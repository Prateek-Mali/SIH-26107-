"""Consistency: run the dev questions of eval/heldout.jsonl twice (no cache) and compare the two runs.

    python -u eval/consistency.py [--modes pipeline agent] [--runs 2]

Consistent = same outcome (answered / refused) AND the same top source (first cited document) in every run.
Also reported: same cited documents, same answer text, fallbacks. Writes eval/consistency_report.md.
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

ap = argparse.ArgumentParser()
ap.add_argument("--modes", nargs="+", default=["pipeline", "agent"], choices=["pipeline", "agent"])
ap.add_argument("--runs", type=int, default=2)
args = ap.parse_args()

from app import agent, answer  # noqa: E402

qs = [json.loads(l) for l in (ROOT / "eval" / "heldout.jsonl").open(encoding="utf-8") if l.strip()]
dev = [q for q in qs if q["split"] == "dev"]


def outcome(r: dict) -> dict:
    return {"refused": r["refused"], "top": r["citations"][0]["source_id"] if r["citations"] else None,
            "sources": sorted({c["source_id"] for c in r["citations"]}), "answer": r["answer"],
            "fallback": r.get("fallback"), "reason": (r["trace"].get("stages") or {}).get("refusal_reason"),
            "secs": round(r["latency_ms"] / 1000, 1)}


report = ["# Consistency on the 20 dev questions\n", f"Generated {time.strftime('%Y-%m-%d %H:%M')}; "
          f"{args.runs} full passes per mode, no cache. Consistent = same answered/refused outcome and same top "
          "source (first cited document) in every pass.\n"]
summary = {}
for mode in args.modes:
    ask = agent.ask if mode == "agent" else answer.ask
    passes = []
    for p in range(args.runs):
        res = []
        for i, q in enumerate(dev, 1):
            try:
                res.append(outcome(ask(q["question"], use_cache=False)))
            except Exception as e:
                res.append({"refused": None, "top": f"ERROR {type(e).__name__}", "sources": [], "answer": str(e),
                            "fallback": None, "reason": "error", "secs": 0})
            print(f"  {mode} pass {p + 1}: {i}/{len(dev)}", flush=True)
        passes.append(res)
    rows, same, same_src, same_text, fb = [], 0, 0, 0, 0
    for i, q in enumerate(dev):
        runs = [ps[i] for ps in passes]
        ok = len({(r["refused"], r["top"]) for r in runs}) == 1
        same += ok
        same_src += len({tuple(r["sources"]) for r in runs}) == 1
        same_text += len({r["answer"] for r in runs}) == 1
        fb += any(r["fallback"] for r in runs)
        rows.append(f"| {q['id']} | {q['type']} | {'yes' if ok else '**NO**'} | "
                    + " | ".join(("refused (" + str(r["reason"]) + ")" if r["refused"] else str(r["top"]))
                                 + (f" FALLBACK {r['fallback']}" if r["fallback"] else "") for r in runs) + " |")
    n = len(dev)
    summary[mode] = {"consistent (outcome + top source)": f"{same}/{n} = {100 * same / n:.0f}%",
                     "same cited documents": f"{same_src}/{n}", "identical answer text": f"{same_text}/{n}",
                     "questions with a fallback": str(fb),
                     "answered (pass 1)": f"{sum(not r['refused'] for r in passes[0])}/{n}"}
    report += [f"\n## {mode}\n", "| id | type | consistent | " + " | ".join(f"pass {p + 1}" for p in range(args.runs)) + " |",
               "|---|---|---|" + "---|" * args.runs, *rows]
    with (ROOT / "eval" / f"consistency_{mode}.jsonl").open("w", encoding="utf-8") as f:
        for i, q in enumerate(dev):
            f.write(json.dumps({"id": q["id"], "runs": [ps[i] for ps in passes]}, ensure_ascii=False) + "\n")

table = ["| metric | " + " | ".join(summary) + " |", "|---|" + "---|" * len(summary)]
for k in next(iter(summary.values())):
    table.append(f"| {k} | " + " | ".join(summary[m][k] for m in summary) + " |")
report.insert(2, "\n".join(table) + "\n")
(ROOT / "eval" / "consistency_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
print("\n" + "\n".join(table))
