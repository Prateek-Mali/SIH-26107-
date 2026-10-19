"""Run one question N times (no cache) and show the traces side by side, naming the first stage that differs.

    python -u eval/trace_compare.py [--mode agent|pipeline] [--n 3] ["question"]

Writes eval/trace_compare_<mode>.md.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

OBJECTION = ("I already applied for a BIS licence and BIS has raised objections. How much time do I get to respond, "
             "and what happens if I don't?")
ap = argparse.ArgumentParser()
ap.add_argument("question", nargs="?", default=OBJECTION)
ap.add_argument("--mode", default="agent", choices=["agent", "pipeline"])
ap.add_argument("--n", type=int, default=3)
args = ap.parse_args()

from app import agent, answer  # noqa: E402

ask = agent.ask if args.mode == "agent" else answer.ask
STAGES = [  # (label, how to read it from a result)
    ("understand_ok", lambda r, s: s.get("understand_ok")),
    ("intent", lambda r, s: s.get("intent")),
    ("tools", lambda r, s: " -> ".join(s.get("tools") or []) or "-"),
    ("sub-queries", lambda r, s: " || ".join(s.get("sub_queries") or [])),
    ("concept terms", lambda r, s: ", ".join(s.get("concept_terms") or []) or "-"),
    ("retrieved per sub-query (count: top 3)", lambda r, s: " || ".join(
        f"{p['count']}: {', '.join(c for c, _ in p['top3'])}" for p in s.get("per_query") or [])),
    ("chunks sent to the LLM", lambda r, s: ", ".join(s.get("sent_to_llm") or [])),
    ("provider", lambda r, s: s.get("provider")),
    ("fallback", lambda r, s: s.get("fallback") or "-"),
    ("model said NOT_COVERED", lambda r, s: s.get("model_not_covered")),
    ("retried after NOT_COVERED", lambda r, s: s.get("retried_not_covered")),
    ("regenerated (>40% removed)", lambda r, s: bool(s.get("regenerated"))),
    ("sentences removed by the check", lambda r, s: len(s.get("removed") or [])),
    ("refusal reason", lambda r, s: s.get("refusal_reason") or "-"),
    ("cited sources", lambda r, s: ", ".join(dict.fromkeys(c["chunk_id"] for c in r["citations"])) or "-"),
    ("answer (first line)", lambda r, s: r["answer"].strip().split("\n")[0][:160]),
]

runs = []
for i in range(args.n):
    r = ask(args.question, use_cache=False)
    runs.append(r)
    print(f"run {i + 1}/{args.n} done ({r['latency_ms'] / 1000:.1f} s)", flush=True)

rows, first_diff = [], None
for label, get in STAGES:
    vals = [str(get(r, r["trace"].get("stages") or {})) for r in runs]
    same = len(set(vals)) == 1
    if not same and first_diff is None and label not in ("answer (first line)",):
        first_diff = label
    rows.append((label, same, vals))

md = [f"# Same question, {args.n} runs ({args.mode}, no cache)\n", f"**Question:** {args.question}\n",
      "| stage | same? | " + " | ".join(f"run {i + 1}" for i in range(args.n)) + " |",
      "|---|---|" + "---|" * args.n]
for label, same, vals in rows:
    cells = [v.replace("|", "/").replace("\n", " ") for v in vals]
    md.append(f"| {label} | {'yes' if same else '**NO**'} | " + " | ".join(cells) + " |")
md.append(f"\n**First stage that differs:** {first_diff or 'none (all stages identical)'}\n")
md.append("## Full answers\n")
for i, r in enumerate(runs, 1):
    md.append(f"### Run {i}\n\n{r['answer']}\n")
out = ROOT / "eval" / f"trace_compare_{args.mode}.md"
out.write_text("\n".join(md), encoding="utf-8")
for label, same, vals in rows:
    print(f"{'  ' if same else '≠ '}{label}:")
    for i, v in enumerate(vals, 1):
        print(f"      run {i}: {v[:230]}")
print(f"\nFIRST STAGE THAT DIFFERS: {first_diff or 'none (all stages identical)'}\n-> {out.relative_to(ROOT)}")
