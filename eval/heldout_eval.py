"""Held-out eval: old pipeline vs agent on eval/heldout.jsonl. Prints ONLY aggregate scores.

    python -u eval/heldout_eval.py --split test              # both modes, 40 test questions
    python -u eval/heldout_eval.py --split dev --modes agent

Per-question rows go to eval/heldout_results_<split>_<mode>.jsonl (never printed, so the test questions stay unseen).

Metrics:
- answered: answerable questions that got an answer (not "not covered")
- wrong refusal: answerable questions refused
- off-topic refused: off-topic questions correctly refused
- source hit: an expected source document is among the chunks the bot read
- cited hit: an expected source document is among the cited sources
- citation validity: cited sentences the local check kept unchanged / all cited sentences checked
- language match: answer language == question language
- tool calls: average tool calls per question (agent only)
"""
import argparse
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

ap = argparse.ArgumentParser()
ap.add_argument("--split", default="test", choices=["dev", "test", "all"])
ap.add_argument("--modes", nargs="+", default=["pipeline", "agent"], choices=["pipeline", "agent"])
ap.add_argument("--limit", type=int, default=0, help="only the first N questions (smoke test)")
args = ap.parse_args()

qs = [json.loads(l) for l in (ROOT / "eval" / "heldout.jsonl").open(encoding="utf-8") if l.strip()]
qs = [q for q in qs if args.split == "all" or q["split"] == args.split][:args.limit or None]

from app import agent, answer  # noqa: E402  (loads the indexes)
from app.expand import detect_lang  # noqa: E402


def src(chunk_id: str) -> str:
    return chunk_id.split("::")[0]


def run(mode: str) -> list[dict]:
    ask = agent.ask if mode == "agent" else answer.ask
    if mode == "agent":
        agent.config.AGENT_MODE = "on"
    out = ROOT / "eval" / f"heldout_results_{args.split}_{mode}.jsonl"
    rows = []
    with out.open("w", encoding="utf-8") as f:
        for i, q in enumerate(qs, 1):
            t0 = time.time()
            try:
                r = ask(q["question"], use_cache=False)
            except Exception as e:
                r = {"answer": f"ERROR: {type(e).__name__}: {e}", "citations": [], "refused": False,
                     "provider": "error", "trace": {}, "latency_ms": int((time.time() - t0) * 1000)}
            tr = r.get("trace") or {}
            read = {src(c["chunk_id"]) for c in tr.get("chunks", [])}
            cited = {c.get("source_id") or src(c.get("chunk_id", "")) for c in r.get("citations", [])}
            exp = set(q["expected_source_ids"])
            checked, changed = tr.get("claims_checked", 0), len(tr.get("citation_check") or [])
            row = {"id": q["id"], "type": q["type"], "answerable": q["answerable"], "refused": r["refused"],
                   "error": r.get("provider") == "error", "source_hit": bool(exp & read) if exp else None,
                   "cited_hit": bool(exp & cited) if exp else None, "checked": checked, "changed": changed,
                   "lang_ok": r["refused"] or detect_lang(r["answer"]) == q["language"],
                   "tool_calls": (tr.get("agent") or {}).get("tool_calls"), "fallback": "agent_fallback" in tr,
                   "secs": round(r["latency_ms"] / 1000, 1), "provider": r.get("provider"),
                   "question": q["question"], "answer": r["answer"]}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            rows.append(row)
            print(f"  {mode}: {i}/{len(qs)} done", flush=True)
    return rows


def pct(xs) -> str:
    xs = [x for x in xs if x is not None]
    return f"{100 * sum(xs) / len(xs):.0f}%" if xs else "-"


def summary(rows: list[dict]) -> dict:
    ans = [r for r in rows if r["answerable"]]
    off = [r for r in rows if not r["answerable"]]
    checked = sum(r["checked"] for r in rows)
    secs = sorted(r["secs"] for r in rows)
    tools = [r["tool_calls"] for r in rows if r["tool_calls"] is not None]
    return {
        "answered (answerable)": pct(not r["refused"] for r in ans),
        "wrong refusal": pct(r["refused"] for r in ans),
        "off-topic refused": pct(r["refused"] for r in off),
        "source hit (read)": pct(r["source_hit"] for r in ans),
        "source hit (cited)": pct(r["cited_hit"] for r in ans if not r["refused"]),
        "citation validity": f"{100 * (checked - sum(r['changed'] for r in rows)) / checked:.0f}%" if checked else "-",
        "language match": pct(r["lang_ok"] for r in rows),
        "avg tool calls": f"{statistics.mean(tools):.1f}" if tools else "-",
        "fell back to pipeline": str(sum(r["fallback"] for r in rows)),
        "errors": str(sum(r["error"] for r in rows)),
        "latency p50": f"{statistics.median(secs):.1f} s",
        "latency p95": f"{secs[max(0, math.ceil(0.95 * len(secs)) - 1)]:.1f} s",
    }


results = {m: summary(run(m)) for m in args.modes}
table = [f"| metric ({args.split}, {len(qs)} questions) | " + " | ".join(args.modes) + " |",
         "|---|" + "---|" * len(args.modes)]
for k in next(iter(results.values())):
    table.append(f"| {k} | " + " | ".join(results[m][k] for m in args.modes) + " |")
text = "\n".join(table)
print("\n" + text)
(ROOT / "eval" / f"heldout_report_{args.split}.md").write_text(
    f"# Held-out eval ({args.split})\n\nGenerated {time.strftime('%Y-%m-%d %H:%M')}. Aggregate only.\n\n{text}\n",
    encoding="utf-8")
