"""Quick local eval: 10 questions, no LLM judge, one line per question, hard 10-minute limit.

    python -u eval/quick_eval.py [--ids q001 q011 ...]

Scores (all local):
- hit@5: an expected source is in the first 5 retrieved chunks
- citation validity: share of the model's cited sentences that the local check found supported
  (by the excerpt it cited, reranker score >= 0.3 and all numbers present) before any fix-up
- refused: whether the bot gave the "not covered" reply (must be True only for off-topic)
- facts: share of the question's key facts (exact values) present in the final answer
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

from eval.run_eval import hit_at_5, key_fact_score  # noqa: E402

DEFAULT = ["q001", "q011", "q015", "q019", "q023", "q024", "q032", "q040", "q053", "q056"]
LIMIT_S = 600

ap = argparse.ArgumentParser()
ap.add_argument("--ids", nargs="*", default=DEFAULT)
ap.add_argument("--label", default="quick")
args = ap.parse_args()

qs = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "eval" / "questions.jsonl").open(encoding="utf-8")}
from app.answer import ask  # noqa: E402  (imported after arg parsing: loads indexes)

t_start = time.time()
rows = []
print(f"{'id':5} {'type':20} {'hit@5':5} {'cite_ok':>7} {'refused':7} {'facts':>5} {'secs':>5} {'ret':>5} {'rrk':>5} {'gen':>5} {'chk':>5}  provider", flush=True)
for qid in args.ids:
    if time.time() - t_start > LIMIT_S:
        print(f"STOP: 10-minute limit reached after {len(rows)} questions", flush=True)
        break
    q = qs[qid]
    t0 = time.time()
    try:
        r = ask(q["question"], use_cache=False)
    except Exception as e:
        r = {"answer": f"ERROR: {type(e).__name__}: {e}", "citations": [], "refused": False, "provider": "error",
             "trace": {}, "latency_ms": int((time.time() - t0) * 1000)}
    tr = r.get("trace", {})
    retrieved = [c["chunk_id"] for c in tr.get("chunks", []) if not c.get("neighbour_of")]
    checked, changed = tr.get("claims_checked", 0), len(tr.get("citation_check") or [])
    row = {"id": qid, "type": q["type"], "question": q["question"], "must_refuse": q["must_refuse"],
           "hit5": hit_at_5(retrieved, q["expected_source_ids"]),
           "cite_valid": round((checked - changed) / checked, 2) if checked else None,
           "claims_checked": checked, "changed": tr.get("citation_check") or [],
           "refused": r["refused"], "facts": key_fact_score(r["answer"], q.get("key_facts", [])),
           "secs": round(r["latency_ms"] / 1000, 1), "provider": r.get("provider"), "answer": r["answer"],
           "expected": q["expected_answer"], "top5": retrieved[:5]}
    rows.append(row)
    f = lambda v: "-" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))
    print(f"{qid:5} {q['type']:20} {f(row['hit5']):5} {f(row['cite_valid']):>7} {str(row['refused']):7} "
          f"{f(row['facts']):>5} {row['secs']:5.1f} {tr.get('retrieval', {}).get('ms', 0) / 1000:5.1f} "
          f"{tr.get('retrieval', {}).get('rerank_ms', 0) / 1000:5.1f} {tr.get('generate_ms', 0) / 1000:5.1f} "
          f"{tr.get('verify_ms', 0) / 1000:5.1f}  {row['provider']}", flush=True)

out = ROOT / "eval" / f"results_{args.label}.jsonl"
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
bis = [r for r in rows if not r["must_refuse"]]
cv = [r["cite_valid"] for r in bis if r["cite_valid"] is not None]
print(f"\nhit@5 {sum(1 for r in bis if r['hit5'])}/{len(bis)} · citation validity {sum(cv) / len(cv) if cv else 0:.2f} · "
      f"wrong refusals {sum(1 for r in bis if r['refused'])} · off-topic refused "
      f"{sum(1 for r in rows if r['must_refuse'] and r['refused'])}/{sum(1 for r in rows if r['must_refuse'])} · "
      f"total {time.time() - t_start:.0f} s -> {out.relative_to(ROOT)}", flush=True)
