"""Evaluate the BIS Assistant on eval/questions.jsonl and write eval/report.md.

    python eval/run_eval.py --retrieval-only        # hit@5, old retriever vs new (no LLM calls)
    python eval/run_eval.py                         # full run: answers + judge
    python eval/run_eval.py --limit 10 --label after --compare eval/results_before.jsonl
    python eval/run_eval.py --ragas                 # RAGAS faithfulness/relevancy (many LLM calls)

Metrics
- retrieval hit@5: an expected source is among the first 5 retrieved chunks (neighbours excluded)
- key-fact accuracy: share of the question's key facts (exact numbers/terms) present in the answer
- faithfulness / answer relevancy / citation support: one LLM-judge call per answer (or RAGAS)
- refusal accuracy, wrong refusals on BIS questions, "general answers" (answers without citations: must be 0)
- latency p50 / p95
Targets: hit@5 >= 0.90, faithfulness >= 0.90, citation validity >= 0.95, 0 general answers, 0 wrong refusals, p50 < 12 s
"""
import argparse
import json
import os
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

from app import config, llm  # noqa: E402

EVAL = ROOT / "eval"

JUDGE = """You grade a chatbot answer about BIS (Bureau of Indian Standards) against the SOURCES it cited.
1. faithfulness: split the ANSWER (ignore headings, links and the source list) into factual claims; the share
   of claims fully supported by the SOURCES (numbers, dates, section/form numbers must match).
2. relevancy: how completely the ANSWER addresses the QUESTION (1.0 full, 0.5 partial, 0.0 not at all).
3. citations: for each sentence that has a [n] marker, is it supported by source [n]? Give counts.
4. correct: does the ANSWER agree with the REFERENCE answer's key points (1.0 / 0.5 / 0.0)?
Reply with JSON only: {"faithfulness": 0.0-1.0, "relevancy": 0.0-1.0, "cited_sentences": int,
"cited_supported": int, "correct": 0.0-1.0, "problems": "one short line"}"""


WORDS = {"ninety": "90", "thirty": "30", "twenty one": "21", "five thousand": "5000", "two": "2", "five": "5", "ten": "10"}


def norm(s: str) -> str:
    s = s.lower()
    for w, d in WORDS.items():
        s = re.sub(rf"\b{w}\b", d, s)
    return re.sub(r"[\s,.\-]", "", s).replace("₹", "rs").replace("rs.", "rs")


def key_fact_score(answer: str, facts: list[str]) -> float | None:
    if not facts:
        return None
    a = norm(answer)
    return sum(1 for f in facts if norm(f) in a) / len(facts)


def hit_at_5(chunk_ids: list[str], expected: list[str]) -> bool | None:
    if not expected:
        return None
    top = [c.split("::")[0] for c in chunk_ids[:5]]
    return any(any(t == e or t.startswith(e) for t in top) for e in expected)


def judge(q: dict, res: dict) -> dict:
    body = re.split(r"\n\n\*\*(?:Sources|स्रोत):\*\*", res["answer"])[0]
    sources = "\n\n".join(f"[{c['n']}] {c['title']} | {c.get('section', '')}\n{c.get('full_text') or c['snippet']}"
                          for c in res["citations"])
    prompt = (f"QUESTION: {q['question']}\n\nREFERENCE: {q['expected_answer']}\n\nANSWER:\n{body}\n\nSOURCES:\n{sources}")
    try:
        text, _ = llm.generate_with_provider(prompt, system=JUDGE, temperature=0.0, max_tokens=800,
                                             model=config.GEMINI_ROUTER_MODEL)  # cheap judge model
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(text[text.find("{"): text.rfind("}") + 1])
    except Exception as e:
        return {"judge_error": f"{type(e).__name__}: {str(e)[:120]}"}


def retrieval_only(qs: list[dict]):
    from app.retrieval import retrieve, search
    rows = []
    for q in qs:
        if q["must_refuse"]:
            continue
        old = [c["chunk_id"] for c in search(q["question"], k=5)]
        new = [c["chunk_id"] for c in retrieve(q["question"])["chunks"] if not c.get("neighbour_of")]
        rows.append({"id": q["id"], "type": q["type"], "question": q["question"],
                     "old": hit_at_5(old, q["expected_source_ids"]), "new": hit_at_5(new, q["expected_source_ids"]),
                     "new_top": [c.split("::")[0] for c in new[:5]]})
        print(f"{q['id']} old={rows[-1]['old']} new={rows[-1]['new']} | {q['question'][:60]}")
    o = sum(r["old"] for r in rows) / len(rows)
    n = sum(r["new"] for r in rows) / len(rows)
    lines = ["# Retrieval hit@5: old retriever vs new", "",
             f"Run {datetime.now():%Y-%m-%d %H:%M} · {len(rows)} BIS questions", "",
             f"| | hit@5 |\n|---|---|\n| old (hybrid, one query) | {o:.2f} |\n| **new** (expansions, scheme, boosts, dedupe, rerank) | **{n:.2f}** |", "",
             "| id | type | old | new | question | new top-5 sources |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['type']} | {'✅' if r['old'] else '❌'} | {'✅' if r['new'] else '❌'} | "
                     f"{r['question'][:70]} | {', '.join(dict.fromkeys(r['new_top']))[:90]} |")
    (EVAL / "retrieval_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nhit@5 old={o:.2f} new={n:.2f} -> eval/retrieval_report.md")


def pct(x):
    return "n/a" if x is None else f"{x:.2f}"


def mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return sum(xs) / len(xs) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieval-only", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--label", default="run")
    ap.add_argument("--compare", help="an earlier results_*.jsonl for a before/after table")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--resume", action="store_true", help="skip questions already in results_<label>.jsonl")
    ap.add_argument("--ragas", action="store_true", help="also compute RAGAS metrics (many LLM calls)")
    args = ap.parse_args()

    qs = [json.loads(l) for l in (EVAL / "questions.jsonl").open(encoding="utf-8") if l.strip()]
    if args.ids:
        qs = [q for q in qs if q["id"] in args.ids]
    if args.limit:
        qs = qs[: args.limit]
    if args.retrieval_only:
        return retrieval_only(qs)

    from app.answer import ask
    from app.retrieval import _store

    by_id, _ = _store()
    out = EVAL / f"results_{args.label}.jsonl"
    rows = []
    if args.resume and out.exists():
        rows = [json.loads(l) for l in out.open(encoding="utf-8")]
    elif out.exists():
        out.unlink()
    done = {r["id"] for r in rows}
    for i, q in enumerate(qs, 1):
        if q["id"] in done:
            continue
        t0 = time.time()
        try:
            res = ask(q["question"], use_cache=False)
        except Exception as e:
            res = {"answer": f"ERROR: {type(e).__name__}: {e}", "citations": [], "refused": False, "provider": "error",
                   "latency_ms": int((time.time() - t0) * 1000), "trace": {}}
        for c in res["citations"]:
            c["full_text"] = by_id.get(c["chunk_id"], {}).get("text", "")[:3000]
        retrieved = [c["chunk_id"] for c in res.get("trace", {}).get("chunks", []) if not c.get("neighbour_of")]
        general = (not res["refused"]) and not res["citations"] and not res["answer"].startswith("Hello")
        row = {"id": q["id"], "type": q["type"], "question": q["question"], "reviewed": q.get("reviewed", False),
               "must_refuse": q["must_refuse"], "refused": res["refused"], "provider": res.get("provider"),
               "latency_s": round(res["latency_ms"] / 1000, 1), "hit5": hit_at_5(retrieved, q["expected_source_ids"]),
               "key_facts": key_fact_score(res["answer"], q.get("key_facts", [])), "general_answer": general,
               "removed_by_check": len(res.get("trace", {}).get("citation_check", []) or []),
               "n_citations": len(res["citations"]), "answer": res["answer"]}
        if not args.no_judge and not res["refused"] and res["citations"]:
            j = judge(q, res)
            row.update({k: j.get(k) for k in ("faithfulness", "relevancy", "correct", "problems", "judge_error")})
            if isinstance(j.get("cited_sentences"), int) and j["cited_sentences"]:
                row["citation_valid"] = min(1.0, j.get("cited_supported", 0) / j["cited_sentences"])
        rows.append(row)
        with out.open("a", encoding="utf-8") as f:  # saved as we go, so a run can be resumed
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"[{i}/{len(qs)}] {q['id']} {q['type']:20} refused={row['refused']!s:5} hit5={row['hit5']!s:5} "
              f"facts={pct(row['key_facts'])} faith={pct(row.get('faithfulness'))} {row['latency_s']}s {row['provider']}")

    if args.ragas:
        print("[eval] RAGAS: see eval/run_eval.py history; not run in this version to protect the API quota")

    before = {}
    if args.compare and Path(args.compare).exists():
        before = {json.loads(l)["id"]: json.loads(l) for l in open(args.compare, encoding="utf-8")}
    write_report(rows, before, args.label)


def score_of(r: dict) -> float | None:
    """One 0-10 score per answer: correctness, faithfulness, key facts (and a refusal is right or wrong)."""
    if r["must_refuse"]:
        return 10.0 if r["refused"] else 0.0
    if r["refused"] or r.get("general_answer"):
        return 0.0
    parts = [x for x in (r.get("correct"), r.get("faithfulness"), r.get("key_facts")) if isinstance(x, (int, float))]
    return round(10 * sum(parts) / len(parts), 1) if parts else None


def write_report(rows: list[dict], before: dict, label: str):
    bis = [r for r in rows if not r["must_refuse"]]
    answered = [r for r in bis if not r["refused"]]
    lat = sorted(r["latency_s"] for r in rows) or [0]
    p95 = lat[min(len(lat) - 1, int(round(0.95 * (len(lat) - 1))))]
    hit = mean([1.0 if r["hit5"] else 0.0 for r in bis if r["hit5"] is not None])
    faith = mean([r.get("faithfulness") for r in answered])
    cv = mean([r.get("citation_valid") for r in answered])
    refusal = mean([1.0 if r["refused"] == r["must_refuse"] else 0.0 for r in rows])
    scores = [s for s in (score_of(r) for r in rows) if s is not None]

    def ok(v, t, higher=True):
        return "" if v is None else (" ✅" if (v >= t if higher else v <= t) else " ❌")

    lines = [
        "# BIS Assistant: evaluation report", "",
        f"Run `{label}` {datetime.now():%Y-%m-%d %H:%M} · {len(rows)} questions ({sum(r['reviewed'] for r in rows)} hand-reviewed) · "
        f"providers: {', '.join(sorted({r['provider'] or '' for r in rows}))} · judge: one LLM call per answer", "",
        "| Metric | Value | Target |", "|---|---|---|",
        f"| Retrieval hit@5 | {pct(hit)}{ok(hit, 0.9)} | ≥ 0.90 |",
        f"| Faithfulness (judge) | {pct(faith)}{ok(faith, 0.9)} | ≥ 0.90 |",
        f"| Citation validity (judge) | {pct(cv)}{ok(cv, 0.95)} | ≥ 0.95 |",
        f"| Answer correctness vs reference (judge) | {pct(mean([r.get('correct') for r in answered]))} | |",
        f"| Key-fact accuracy (exact values present) | {pct(mean([r['key_facts'] for r in answered]))} | |",
        f"| Answer relevancy (judge) | {pct(mean([r.get('relevancy') for r in answered]))} | |",
        f"| General (uncited) answers | {sum(r['general_answer'] for r in rows)}{ok(sum(r['general_answer'] for r in rows), 0, False)} | 0 |",
        f"| Wrong refusals on BIS questions | {sum(r['refused'] for r in bis)}{ok(sum(r['refused'] for r in bis), 0, False)} | 0 |",
        f"| Refusal accuracy | {pct(refusal)} | |",
        f"| Sentences removed/re-cited by the citation check | {sum(r['removed_by_check'] for r in rows)} | |",
        f"| Latency p50 / p95 | {statistics.median(lat):.1f} s / {p95:.1f} s{ok(-statistics.median(lat), -12)} | p50 < 12 s |",
        f"| **Average answer score (0-10)** | **{mean(scores) or 0:.1f}** | ≥ 9 |", "",
        "## Per question", "",
        "| id | type | question | score" + (" before | score after" if before else "") + " | hit@5 | facts | faith | s |",
        "|---|---|---|---" + ("|---" if before else "") + "|---|---|---|---|",
    ]
    for r in rows:
        b = score_of(before[r["id"]]) if r["id"] in before else None
        lines.append(f"| {r['id']} | {r['type']} | {r['question'][:60]} | "
                     + (f"{b if b is not None else '-'} | " if before else "")
                     + f"{score_of(r) if score_of(r) is not None else '-'} | {'✅' if r['hit5'] else ('-' if r['hit5'] is None else '❌')} | "
                     f"{pct(r['key_facts'])} | {pct(r.get('faithfulness'))} | {r['latency_s']} |")
    lines += ["", "## Answers to look at (score < 9)", ""]
    for r in rows:
        s = score_of(r)
        if s is not None and s < 9:
            lines.append(f"- **{r['id']}** ({r['type']}, score {s}) {r['question']}  \n  judge: {r.get('problems') or r.get('judge_error') or '-'}"
                         f"  \n  answer: {re.split(chr(10) + chr(10) + r'[*][*]Sources', r['answer'])[0][:300].replace(chr(10), ' ')}")
    (EVAL / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:18]))
    print(f"\nWrote {EVAL / 'report.md'}")


if __name__ == "__main__":
    main()
