"""One session, in order, no cache: the chat-feel test (Task 12). -> eval/chat_feel.md"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")
from app import memory  # noqa: E402

Q = ["what is ibs", "is it government?", "i make steel water bottles, which standard", "is it compulsory",
     "and fee?", "how do i apply — steps only", "explain step 3", "difference between isi and crs",
     "what did i ask about first?", "capital of france"]
sid = memory.new_session()
out = (ROOT / "eval" / "chat_feel.md").open("w", encoding="utf-8")
for i, q in enumerate(Q, 1):
    r = memory.chat(q, sid, use_cache=False)
    st = r["trace"].get("stages") or {}
    out.write(f"## {i}. {q}\n_rewritten: {st.get('rewritten_question')} | refused={r['refused']} "
              f"({st.get('refusal_reason')}) | {r['latency_ms'] / 1000:.1f} s_\n\n{r['answer']}\n\n")
    out.flush()
    print(i, "done", flush=True)
