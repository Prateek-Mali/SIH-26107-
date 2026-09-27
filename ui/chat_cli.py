"""Chat with the BIS Assistant in the terminal.

    .venv/bin/python ui/chat_cli.py            # runs the pipeline in this process
    .venv/bin/python ui/chat_cli.py --api      # use a running API at http://localhost:8000

Commands: /trace (toggle "How I answered"), /new (new conversation), /nocache, /quit
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
    rt = tr.get("retrieval", {})
    print(f"{DIM}── How I answered ──")
    if rt:
        print(f"  queries: {rt.get('queries')}")
        print(f"  scheme: {rt.get('scheme')}  boosts: {rt.get('boosts')}  vector search: {rt.get('vector')}")
        print(f"  retrieval {rt.get('ms')} ms (reranker {rt.get('rerank_ms')} ms) · generation {tr.get('generate_ms')} ms"
              f" · citation check {tr.get('verify_ms')} ms")
    for c in tr.get("chunks", []):
        nb = f" (neighbour of {c['neighbour_of']})" if c.get("neighbour_of") else ""
        page = f" p.{c['page']}" if c.get("page") else ""
        rr = f"{c['rerank']:.2f}" if isinstance(c.get("rerank"), (int, float)) else "  - "
        print(f"  [{c['n']:2}] rerank {rr}  {c['chunk_id']}{page} [{c.get('scheme')}]{nb}")
    checks = tr.get("citation_check") or []
    if checks:
        print(f"  citation check: {len(checks)} sentence(s) changed")
        for x in checks:
            print(f"    {x['action']} (score {x.get('score')}): {x['sentence'][:110]}")
    u = tr.get("understand")
    if u:
        print(f"  understood: intent={u.get('intent')} role={u.get('user_role')} product={u.get('product_or_topic')!r}")
        print(f"  goal: {u.get('user_goal')}  |  standalone: {u.get('standalone_question')}")
    if tr.get("note"):
        print(f"  note: {tr['note']}")
    print(RESET, end="")


def main():
    use_api = "--api" in sys.argv
    if not use_api:
        from app.agent import ask  # AGENT_MODE=off (or any agent failure) -> the old pipeline
    print(f"{BOLD}BIS Assistant{RESET} — answers from official BIS documents, with sources (English or हिन्दी).")
    print(f"{DIM}{'API ' + API if use_api else 'local pipeline'} · commands: /trace  /new  /nocache  /quit{RESET}\n")
    show_trace, use_cache, session, history = False, True, os.urandom(8).hex(), []
    while True:
        try:
            q = input(f"{CYAN}{BOLD}You › {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q in ("/quit", "/exit"):
            break
        if q in ("/trace", "/new", "/nocache"):
            if q == "/trace":
                show_trace = not show_trace
                print(f"{DIM}trace {'on' if show_trace else 'off'}{RESET}\n")
            elif q == "/nocache":
                use_cache = not use_cache
                print(f"{DIM}answer cache {'on' if use_cache else 'off'}{RESET}\n")
            else:
                session, history = os.urandom(8).hex(), []
                print(f"{DIM}new conversation{RESET}\n")
            continue
        print(f"{DIM}searching official BIS documents…{RESET}", end="", flush=True)
        try:
            res = ask_api(q, session) if use_api else ask(q, history, use_cache=use_cache)
        except KeyboardInterrupt:
            print(f"\r\033[K{DIM}(stopped){RESET}\n")
            continue
        except Exception as e:  # real errors in red, never hidden
            print(f"\r\033[K{RED}ERROR: {type(e).__name__}: {e}{RESET}\n")
            continue
        print("\r\033[K", end="")
        print(f"{GREEN}{BOLD}BIS › {RESET}{res['answer']}")
        footer = [res.get("provider", ""), f"{res['latency_ms'] / 1000:.1f} s",
                  f"{res.get('sources_used', 0)} source document(s)"]
        if res.get("cached"):
            footer.append("from cache")
        print(f"{DIM}[{' · '.join(x for x in footer if x)}]{RESET}")
        if show_trace:
            print_trace(res)
        print()
        history += [{"role": "user", "content": q},
                    {"role": "assistant", "content": res["answer"][:1500], "profile": res.get("profile")}]
        history = history[-12:]  # last 6 turns


if __name__ == "__main__":
    main()
