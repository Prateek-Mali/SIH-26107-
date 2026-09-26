"""Draft evaluation questions with Gemini from the indexed chunks. THE TEAM MUST CHECK EVERY ONE.

    python eval/draft_questions.py            # appends drafts to eval/questions.jsonl

Drafts get "reviewed": false. After checking a question and its expected answer against the
source document, set "reviewed": true (or delete the line). run_eval.py reports reviewed and
unreviewed questions separately.

Target mix (CLAUDE.md): 15 law, 15 certification, 15 product_qco, 10 hallmarking_consumer,
5 out-of-scope (hand-written, already in questions.jsonl), 10 Hindi.
"""
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

from app import config, llm  # noqa: E402

QUESTIONS = ROOT / "eval" / "questions.jsonl"
PLAN = [("law", 15, "en"), ("certification", 15, "en"), ("product_qco", 15, "en"),
        ("hallmarking_consumer", 10, "en"), ("law", 3, "hi"), ("certification", 3, "hi"),
        ("product_qco", 2, "hi"), ("hallmarking_consumer", 2, "hi")]

PROMPT = """You write test questions for a chatbot about the Bureau of Indian Standards (BIS).
From the EXCERPT below (an official BIS document), write ONE question a real user
(a manufacturer, importer, jeweller or consumer) might ask, which the excerpt answers clearly.
Write the question in {language}. The expected answer must be short (1-2 sentences), in English, and
use only facts from the excerpt (keep section, IS, S.O. numbers and amounts exactly).
If the excerpt has nothing a user would ask about, reply {{"skip": true}}.
Reply with JSON only: {{"question": "...", "expected_answer": "..."}}

EXCERPT ({title}, {where}):
{text}"""


def main():
    if not config.KEY_IS_SET:
        sys.exit("Set GEMINI_API_KEY in .env first.")
    chunks = [json.loads(l) for l in config.CHUNKS_PATH.open(encoding="utf-8")]
    existing = [json.loads(l) for l in QUESTIONS.open(encoding="utf-8")] if QUESTIONS.exists() else []
    used = {s for q in existing for s in q.get("expected_chunk_ids", [])}
    rng = random.Random(42)
    n = len(existing)
    with QUESTIONS.open("a", encoding="utf-8") as out:
        for agent, count, lang in PLAN:
            pool = [c for c in chunks if c["agent"] == agent and c["chunk_id"] not in used and len(c["text"]) > 300]
            rng.shuffle(pool)
            made = 0
            for c in pool:
                if made == count:
                    break
                where = ", ".join(x for x in (c.get("section", "")[:80], f"page {c['page']}" if c.get("page") else "") if x)
                try:
                    q = llm.generate_json(PROMPT.format(language="Hindi" if lang == "hi" else "English",
                                                        title=c["title"], where=where, text=c["text"][:3000]))
                except Exception as e:
                    print(f"  skip {c['chunk_id']}: {e}")
                    continue
                if q.get("skip") or not q.get("question"):
                    continue
                n += 1
                row = {"id": f"q{n:03d}", "question": q["question"], "expected_answer": q["expected_answer"],
                       "expected_source_ids": [c["source_id"]], "expected_chunk_ids": [c["chunk_id"]],
                       "type": "hindi" if lang == "hi" else agent, "expected_intents": [agent],
                       "language": lang, "reviewed": False}
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                used.add(c["chunk_id"])
                made += 1
                print(f"{row['id']} [{agent}/{lang}] {row['question']}")
    print(f"\nDrafted questions appended to {QUESTIONS.relative_to(ROOT)}. Review each one and set reviewed=true.")


if __name__ == "__main__":
    main()
