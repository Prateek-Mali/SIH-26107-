"""Chat with the BIS Assistant in the terminal.

    .venv/bin/python ui/chat_cli.py            # runs the pipeline in this process
    .venv/bin/python ui/chat_cli.py --api      # use a running API at http://localhost:8000

Commands: /trace (toggle "How I answered": every stage), /nocache, /new, /history, /profile, /forget, /sessions,
/resume <id>, /image <path> ["question"] (product photo check), /quit. Memory is local (data/memory.sqlite); the last session is resumed on restart (data/.last_session).
The footer shows the answer model; "FALLBACK: <provider>" means the pinned model (ANSWER_PROVIDER) failed.
"""
import logging
import os
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("BIS_QUIET", "1")
warnings.filterwarnings("ignore")
logging.getLogger("google_genai").setLevel(logging.ERROR)

import httpx  # noqa: E402

API = os.getenv("BIS_API_URL", "http://localhost:8000")
DIM, BOLD, CYAN, GREEN, RED, RESET = "\033[2m", "\033[1m", "\033[36m", "\033[32m", "\033[31m", "\033[0m"


def ask_api(message: str, session: str) -> dict:
    r = httpx.post(f"{API}/chat", json={"message": message, "session_id": session}, timeout=300)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data


def print_trace(res: dict):
    tr = res.get("trace", {})
    st = tr.get("stages") or {}
    print(f"{DIM}── How I answered ({st.get('mode', '?')}) ──")
    if st.get("rewritten_question"):
        print(f"  rewritten question: {st['rewritten_question']}")
    if st.get("reused_earlier_chunks"):
        print(f"  reused from the earlier answer: {st['reused_earlier_chunks']}")
    print(f"  understand: {st.get('understand_ok')}"
          + (f" ({st['understand_attempts']} attempt(s))" if st.get("understand_attempts") else "")
          + f"  |  intent: {st.get('intent')}")
    if st.get("tools"):
        print(f"  tools: {' -> '.join(st['tools'])}")
    print(f"  sub-queries: {st.get('sub_queries')}")
    print(f"  filters: {st.get('filters')}  |  concept terms: {st.get('concept_terms')}")
    for pq in st.get("per_query") or []:
        top = ", ".join(f"{cid} ({sc})" for cid, sc in pq.get("top3", []))
        print(f"    {pq['count']:>3} for {pq['query'][:70]!r}: {top}")
    print(f"  best rerank: {st.get('max_rerank')}  |  search empty: {st.get('search_empty')}")
    sent = st.get("sent_to_llm") or []
    print(f"  sent to the model ({len(sent)}): {', '.join(sent[:12])}{' ...' if len(sent) > 12 else ''}")
    print(f"  provider: {st.get('provider')}  |  fallback: {st.get('fallback')}")
    print(f"  model said NOT_COVERED: {st.get('model_not_covered')}  |  retried: {st.get('retried_not_covered')}"
          + (f" -> still NOT_COVERED: {st['model_not_covered_after_retry']}" if st.get("retried_not_covered") else ""))
    if st.get("regenerated"):
        print(f"  regenerated: {st['regenerated']['why']} -> kept {st['regenerated']['kept_chunks']}")
    for x in st.get("removed") or []:
        print(f"  removed by the citation check: {x[:110]}")
    for x in tr.get("citation_check") or []:
        if not x["action"].split(": ")[-1].startswith("removed"):
            print(f"  {x['action']} (score {x.get('score')}): {x['sentence'][:100]}")
    print(f"  refusal reason: {st.get('refusal_reason')}")
    print(RESET, end="")


LAST = Path(__file__).resolve().parent.parent / "data" / ".last_session"


def session_command(q: str, sid: str) -> str | None:
    """/history /profile /forget /sessions /resume <id> /new: returns the (possibly new) session id, or None."""
    from app import memory
    cmd, _, arg = q.partition(" ")
    if cmd == "/new":
        sid = memory.new_session()
        print(f"{DIM}new conversation ({sid}){RESET}\n")
    elif cmd == "/history":
        for t in memory.turns(sid, 10):
            who = "You" if t["role"] == "user" else "BIS"
            print(f"{DIM}{t['turn_no']:>3} {who}: {' '.join(t['content'].split())[:150]}{RESET}")
        print()
    elif cmd == "/profile":
        p = memory.profile(sid)
        print(f"{DIM}{chr(10).join(f'  {k}: {v}' for k, v in p.items()) or '  (nothing remembered yet)'}{RESET}\n")
    elif cmd == "/forget":
        memory.forget(sid)
        sid = memory.new_session()
        print(f"{DIM}memory of that conversation deleted; new conversation ({sid}){RESET}\n")
    elif cmd == "/sessions":
        for x in memory.sessions():
            print(f"{DIM}  {x['session_id']}  {x['updated']}  {x['turns']:>3} turns  {x['title']}{RESET}")
        print()
    elif cmd == "/resume" and arg:
        sid = memory.ensure(arg.strip())
        print(f"{DIM}resumed {sid} ({len(memory.turns(sid))} turns){RESET}\n")
    else:
        return None
    return sid


def main():
    use_api = "--api" in sys.argv
    if not use_api:
        from app import memory
    print(f"{BOLD}BIS Assistant{RESET} — answers from official BIS documents, with sources (English or हिन्दी).")
    print(f"{DIM}{'API ' + API if use_api else 'local'} · commands: /trace /nocache /new /history /profile /forget "
          f"/sessions /resume <id> /image <path> /quit{RESET}")
    show_trace, use_cache = False, True
    session = LAST.read_text().strip() if LAST.exists() else ""
    if not use_api:
        session = memory.ensure(session or None)
        n = len(memory.turns(session))
        print(f"{DIM}{'resumed conversation ' + session + f' ({n} turns)' if n else 'new conversation ' + session}{RESET}\n")
    session = session or os.urandom(6).hex()
    while True:
        LAST.write_text(session)
        try:
            q = input(f"{CYAN}{BOLD}You › {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q in ("/quit", "/exit"):
            break
        if q == "/trace":
            show_trace = not show_trace
            print(f"{DIM}trace {'on' if show_trace else 'off'}{RESET}\n")
            continue
        if q == "/nocache":
            use_cache = not use_cache
            print(f"{DIM}answer cache {'on' if use_cache else 'off'}{RESET}\n")
            continue
        if q.startswith("/") and not use_api:
            new = session_command(q, session)
            if new:
                session = new
                continue
        image = None
        if q.startswith("/image"):  # /image <path> ["question"]: product photo check (app/vision.py)
            import shlex
            try:
                parts = shlex.split(q)[1:]
            except ValueError:
                parts = q.split()[1:]
            if not parts or not os.path.isfile(os.path.expanduser(parts[0])):
                print(f"{RED}usage: /image <path to a jpg/png/webp/heic photo> [question]{RESET}\n")
                continue
            image, q = os.path.expanduser(parts[0]), " ".join(parts[1:])
        print(f"{DIM}{'reading your photo…' if image else 'searching official BIS documents…'}{RESET}", end="", flush=True)
        try:
            if image and not use_api:
                from app.vision import photo_chat
                with open(image, "rb") as f:
                    res = photo_chat(f.read(), image, q, session, use_cache=use_cache)
            elif image:
                print(f"\r\033[K{RED}/image works in local mode (without --api){RESET}\n")
                continue
            else:
                res = ask_api(q, session) if use_api else memory.chat(q, session, use_cache=use_cache)
        except KeyboardInterrupt:
            print(f"\r\033[K{DIM}(stopped){RESET}\n")
            continue
        except Exception as e:  # real errors in red, never hidden
            print(f"\r\033[K{RED}ERROR: {type(e).__name__}: {e}{RESET}\n")
            continue
        print("\r\033[K", end="")
        print(f"{GREEN}{BOLD}BIS › {RESET}{res['answer']}")
        footer = [(f"{RED}FALLBACK: {res['fallback']}{DIM}" if res.get("fallback") else res.get("provider", "")),
                  f"{res['latency_ms'] / 1000:.1f} s",
                  f"{res.get('sources_used', 0)} source document(s)"]
        if res.get("cached"):
            footer.append("from cache")
        print(f"{DIM}[{' · '.join(x for x in footer if x)}]{RESET}")
        if show_trace:
            print_trace(res)
        print()


if __name__ == "__main__":
    main()
