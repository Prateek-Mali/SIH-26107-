"""Ask the questions that were wrongly refused and show, for each one, WHY it was refused.
Run:  .venv/bin/python scripts/check_refusals.py
Reads nothing from the cache (use_cache=False). Full details go to data/refusals.jsonl."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.answer import ask  # noqa: E402

QUESTIONS = [
    "Is BIS certification compulsory for Sulphate Resisting Portland Cement?",
    "Is BIS certification compulsory for LED lamps? Which IS number and which QCO?",
    "Explain the relationship between an Indian Standard, a BIS licence, a Quality Control Order and the Standard Mark.",
    "How do I decide whether my product falls under Scheme I, Scheme II (CRS) or FMCS?",
    "After I apply for a BIS licence, if BIS raises objections, how much time do I get to respond and what happens if I don't?",
    "What is the capital of France?",  # must be refused
]

for q in QUESTIONS:
    r = ask(q, use_cache=False)
    tr = r.get("trace", {})
    status = "REFUSED" if r.get("refused") else "ANSWERED"
    print(f"\n{'=' * 100}\n{status} | {r.get('provider')} | {r.get('latency_ms')} ms | {q}")
    if r.get("refused"):
        print("  reason :", tr.get("note"))
        print("  chunks :", [c["chunk_id"] for c in tr.get("chunks", [])][:8])
        print("  raw    :", (tr.get("raw_output") or "")[:400].replace("\n", " "))
    else:
        print("  sources:", len(r.get("citations", [])), "| sentences removed by check:",
              sum(1 for x in tr.get("citation_check", []) if x.get("action") == "removed"))
        print(r["answer"][:700])
