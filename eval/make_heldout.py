"""Build eval/heldout.jsonl: 60 NEW questions written by a DIFFERENT model (Groq qwen) from randomly sampled chunks.

    python eval/make_heldout.py

Mix: simple, multi-part, vague, Hindi, scenario-style (from chunks) and off-topic (no chunk). Each question stores
its expected source chunk_ids. Split: 20 dev / 40 test (fixed seed). Prints only counts, never the questions.
"""
import json
import os
import random
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")
from app import config  # noqa: E402

WRITER = "qwen/qwen3.8-27b"  # not the answer models (gpt-oss-120b / Gemini Flash-Lite)
OUT = ROOT / "eval" / "heldout.jsonl"
PLAN = {"simple": 16, "multi_part": 8, "vague": 7, "hindi": 8, "scenario": 13, "off_topic": 8}  # = 60
STYLE = {
    "simple": "a direct, simple question a user might ask",
    "multi_part": "ONE question with two or three parts that needs BOTH excerpts to answer fully",
    "vague": "a short, vague, informally worded question (like a real chat message, maybe with a typo) whose answer is in the excerpt",
    "hindi": "a question written in Hindi (Devanagari script)",
    "scenario": "a question where the user first describes their own situation (business, product, problem) and then asks what to do",
}


def ask_writer(prompt: str) -> dict:
    import time
    for _ in range(6):
        r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                       headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
                       json={"model": WRITER, "temperature": 0.7, "max_tokens": 600,
                             "messages": [{"role": "user", "content": prompt}]}, timeout=60)
        if r.status_code != 429:
            break
        time.sleep(min(float(r.headers.get("retry-after") or 10), 30) + 1)  # per-minute token limit: wait, not fail
    r.raise_for_status()
    t = r.json()["choices"][0]["message"]["content"]
    t = re.sub(r"<think>.*?</think>", "", t, flags=re.S)
    return json.loads(t[t.find("{"): t.rfind("}") + 1])


def main():
    rng = random.Random(20260927)
    chunks = [json.loads(l) for l in config.CHUNKS_PATH.open(encoding="utf-8")]
    usable = [c for c in chunks if len(c["text"]) >= 400 and len(re.findall(r"[A-Za-z]", c["text"])) > 250]
    by_doc = {}
    for c in usable:
        doc = "qco_pdfs" if c["source_id"].startswith("qco_") else ("product_rows" if "::row" in c["chunk_id"] else c["source_id"])
        by_doc.setdefault(doc, []).append(c)
    docs = sorted(by_doc)
    rng.shuffle(docs)
    pick = lambda: rng.choice(by_doc[docs[pick.i % len(docs)]]) if not setattr(pick, "i", pick.i + 1) else None
    pick.i = 0
    rows, failed = [], 0
    for kind, n in PLAN.items():
        made = 0
        while made < n and failed < 30:
            try:
                if kind == "off_topic":
                    q = ask_writer("Write ONE question a person might type into a chatbot that has NOTHING to do with "
                                   "Indian standards, BIS, certification, hallmarking or product quality (e.g. sports, "
                                   "cooking, coding, travel, maths). Vary the topic. "
                                   f"Seed {rng.random():.4f}. Reply with JSON only: {{\"question\": \"...\"}}")
                    ctx = []
                else:
                    ctx = [pick()] + ([pick()] if kind == "multi_part" else [])
                    ex = "\n\n".join(f"EXCERPT {i + 1} ({c['title']}):\n{c['text'][:1200]}" for i, c in enumerate(ctx))
                    q = ask_writer(f"You write test questions for a chatbot about the Bureau of Indian Standards (BIS).\n"
                                   f"Write {STYLE[kind]}. It must be answerable from the excerpt(s) below, without "
                                   f"copying their wording. Keep IS / S.O. numbers exact if you use them.\n"
                                   f"Reply with JSON only: {{\"question\": \"...\", \"answer_facts\": \"one line: the key facts from the excerpt(s)\"}}\n\n{ex}")
            except Exception as e:
                failed += 1
                print(f"  writer error ({type(e).__name__}); retrying")
                continue
            if not q.get("question"):
                failed += 1
                continue
            rows.append({"question": q["question"].strip(), "type": kind,
                         "language": "hi" if kind == "hindi" else "en", "answerable": kind != "off_topic",
                         "expected_chunk_ids": [c["chunk_id"] for c in ctx],
                         "expected_source_ids": list(dict.fromkeys(c["source_id"] for c in ctx)),
                         "reference": q.get("answer_facts", "")})
            made += 1
    rng.shuffle(rows)
    for i, r in enumerate(rows):
        r["id"] = f"h{i + 1:03d}"
        r["split"] = "dev" if i < 20 else "test"
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    from collections import Counter
    print(f"{len(rows)} questions -> {OUT.relative_to(ROOT)} | dev {sum(r['split'] == 'dev' for r in rows)}, "
          f"test {sum(r['split'] == 'test' for r in rows)} | types {dict(Counter(r['type'] for r in rows))} | "
          f"documents covered {len({s for r in rows for s in r['expected_source_ids']})}")


if __name__ == "__main__":
    main()
