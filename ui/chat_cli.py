"""Chat with the BIS Assistant in the terminal.

    .venv/bin/python ui/chat_cli.py

Uses the running API (http://localhost:8000) if it is up, so the vector index is shared;
otherwise runs the RAG graph directly in this process.
Commands: /trace (toggle "How I answered"), /new (new conversation), /quit
"""
import json
import os
import sys
import uuid
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("BIS_QUIET", "1")

API = os.getenv("BIS_API_URL", "http://localhost:8000")
DIM, BOLD, CYAN, GREEN, YELLOW, RESET = "\033[2m", "\033[1m", "\033[36m", "\033[32m", "\033[33m", "\033[0m"


def api_up() -> bool:
    try:
        return httpx.get(f"{API}/health", timeout=3).status_code == 200
    except httpx.HTTPError:
        return False


def ask_api(message: str, session: str):
    """Yields (event, data) from the API's SSE stream."""
    with httpx.stream("POST", f"{API}/chat", json={"message": message, "session_id": session}, timeout=300) as r:
        event = None
        for line in r.iter_lines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:") and event:
                yield event, json.loads(line[5:].strip())
                event = None


def ask_local(message: str, history: list):
    from app.graph import answer

    r = answer(message, history)
    yield "token", {"text": r["final_answer"]}
    yield "trace", r["trace"]
    yield "done", {"refused": r.get("refused"), "intents": r.get("intents", []), "latency_ms": r["latency_ms"]}


def print_trace(trace: list):
    print(f"{DIM}── How I answered ──")
    for t in trace:
        ms = f" {t['ms'] / 1000:.1f}s" if t.get("ms") is not None else ""
        if t["step"] == "router":
            flags = [f for f in ("is_greeting", "out_of_scope") if t.get(f)]
            print(f"  router{ms}: intents={t['intents']} lang={t['language']} {' '.join(flags)}")
            print(f"    search query: {t.get('search_query', '')}")
        elif "retrieved" in t:
            print(f"  {t['step']} agent{ms}: {'answered' if t.get('found') else 'NOT_FOUND'}, "
                  f"retrieved {len(t['retrieved'])}, cited {len(t.get('used', []))}")
            for r in t["retrieved"]:
                mark = "✓" if r["chunk_id"] in t.get("used", []) else " "
                page = f" p.{r['page']}" if r.get("page") else ""
                print(f"    {mark} {r['chunk_id']}{page}  ({r['score']})")
        else:
            print(f"  {t['step']}{ms}: {t.get('note', '')}")
            for s in t.get("removed", []):
                print(f"    removed: {s}")
    print(RESET, end="")


def main():
    use_api = api_up()
    print(f"{BOLD}BIS Assistant{RESET} — ask about BIS law, certification, QCOs, hallmarking (English or हिन्दी).")
    print(f"{DIM}Mode: {'API at ' + API if use_api else 'local (API not running)'} · "
          f"commands: /trace  /new  /quit{RESET}\n")
    show_trace, session, history = False, str(uuid.uuid4()), []
    while True:
        try:
            q = input(f"{CYAN}{BOLD}You › {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q in ("/quit", "/exit", "exit", "quit"):
            break
        if q == "/trace":
            show_trace = not show_trace
            print(f"{DIM}trace {'on' if show_trace else 'off'}{RESET}")
            continue
        if q == "/new":
            session, history = str(uuid.uuid4()), []
            print(f"{DIM}new conversation{RESET}")
            continue
        print(f"{GREEN}{BOLD}BIS › {RESET}", end="", flush=True)
        answer_text, trace, done = "", [], {}
        try:
            stream = ask_api(q, session) if use_api else ask_local(q, history)
            for event, data in stream:
                if event == "status":
                    print(f"\r{DIM}{GREEN}BIS › {data['message']}…{RESET}\033[K", end="", flush=True)
                elif event == "token":
                    if not answer_text:
                        print(f"\r{GREEN}{BOLD}BIS › {RESET}\033[K", end="")
                    answer_text += data["text"]
                    print(data["text"], end="", flush=True)
                elif event == "trace":
                    trace = data
                elif event == "error":
                    print(f"\n{YELLOW}{data['message']}{RESET}")
                elif event == "done":
                    done = data
        except httpx.HTTPError as e:
            print(f"\n{YELLOW}API error: {e}{RESET}")
            continue
        except KeyboardInterrupt:
            print(f"\n{DIM}(stopped){RESET}")
            continue
        print()
        if done:
            print(f"{DIM}[{done.get('latency_ms', 0) / 1000:.1f}s · agents: {', '.join(done.get('intents') or []) or '—'}"
                  f"{' · refused' if done.get('refused') else ''}]{RESET}")
        if show_trace and trace:
            print_trace(trace)
        if not use_api:
            history += [{"role": "user", "content": q}, {"role": "assistant", "content": answer_text[:1500]}]
        print()


if __name__ == "__main__":
    main()
