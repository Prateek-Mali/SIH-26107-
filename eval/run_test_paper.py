"""Run eval/test_paper.jsonl (TEST_PAPER.md A-J) in agent mode, no cache; each question in a fresh session,
except I3, which follows I1 in the same session (it is a follow-up).

    python -u eval/run_test_paper.py [A B ...]      -> eval/test_paper_answers.md
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")
from app import memory  # noqa: E402

sections = set(sys.argv[1:])
qs = [json.loads(l) for l in (ROOT / "eval" / "test_paper.jsonl").open(encoding="utf-8")]
qs = [q for q in qs if not sections or q["id"] in sections or q["id"].rstrip("0123456789") in sections]
out = (ROOT / "eval" / "test_paper_answers.md").open("w", encoding="utf-8")
sid_for = {}
for q in qs:
    sid = sid_for.get("I1") if q["id"] == "I3" else None
    r = memory.chat(q["question"], sid, use_cache=False)
    sid_for[q["id"]] = r["session_id"]
    st = r["trace"].get("stages") or {}
    out.write(f"## {q['id']}: {q['question']}\n_{r['latency_ms'] / 1000:.1f} s | refused={r['refused']} "
              f"({st.get('refusal_reason')}) | rewritten: {st.get('rewritten_question')} | provider {r['provider']}"
              f"{' FALLBACK ' + r['fallback'] if r.get('fallback') else ''}_\n\n{r['answer']}\n\n")
    out.flush()
    print(q["id"], "done", flush=True)
