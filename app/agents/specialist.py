"""Shared logic for the four specialist agents: retrieve, answer only from excerpts, cite."""
import re
import time

from app import llm, prompts
from app.agents.state import State
from app.retrieval import search


def format_excerpts(chunks: list[dict]) -> str:
    parts = []
    for n, c in enumerate(chunks, start=1):
        meta = [c.get("title", "")]
        if c.get("section"):
            meta.append(f"section: {c['section'][:100]}")
        if c.get("page"):
            meta.append(f"page {c['page']}")
        if c.get("date_downloaded"):
            meta.append(f"downloaded {c['date_downloaded']}")
        parts.append(f"[{n}] {' | '.join(meta)}\n{c['text']}")
    return "\n\n".join(parts)


def dedupe(chunks: list[dict]) -> list[dict]:
    seen, out = set(), []
    for c in chunks:
        if c["chunk_id"] not in seen:
            seen.add(c["chunk_id"])
            out.append(c)
    return out


def answer_from_chunks(agent: str, question: str, chunks: list[dict], language: str) -> tuple[str, list[int]]:
    if not chunks:
        return "NOT_FOUND", []
    system = prompts.AGENT.format(rules=prompts.RULES, focus=prompts.AGENT_FOCUS[agent])
    lang = "Hindi" if language == "hi" else "English"
    prompt = f"EXCERPTS:\n{format_excerpts(chunks)}\n\nQUESTION ({lang}): {question}"
    try:
        out = llm.generate_json(prompt, system=system)
        answer = str(out.get("answer", "")).strip()
        used = [int(n) for n in out.get("used", []) if str(n).isdigit() and 1 <= int(n) <= len(chunks)]
    except Exception as e:
        print(f"[{agent}] bad JSON from model: {e}")
        return "NOT_FOUND", []
    if not answer or answer.upper().startswith("NOT_FOUND"):
        return "NOT_FOUND", []
    cited = [int(n) for n in re.findall(r"\[(\d+)\]", answer) if 1 <= int(n) <= len(chunks)]
    used = list(dict.fromkeys(used + cited))
    if not used:  # an answer without any citation is not grounded
        return "NOT_FOUND", []
    return answer, used


def run_specialist(agent: str, state: State, extra_chunks: list[dict] | None = None) -> dict:
    t0 = time.time()
    query = state.get("search_query") or state["question"]
    chunks = dedupe((extra_chunks or []) + search(query, agent=agent))
    question = state["question"]
    if state.get("search_query") and state["search_query"] != question:
        question = f"{question}\n(Search query used: {state['search_query']})"
    answer, used = answer_from_chunks(agent, question, chunks, state.get("language", "en"))
    output = {"answer": answer, "chunks": chunks, "used": used}
    trace = {
        "step": agent,
        "retrieved": [{"chunk_id": c["chunk_id"], "title": c["title"], "page": c.get("page"),
                       "score": round(c.get("score", 0), 4)} for c in chunks],
        "used": [chunks[n - 1]["chunk_id"] for n in used],
        "found": answer != "NOT_FOUND",
        "ms": int((time.time() - t0) * 1000),
    }
    return {"agent_outputs": {agent: output}, "trace": [trace]}
