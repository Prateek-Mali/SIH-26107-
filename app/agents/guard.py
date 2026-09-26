"""Guard: removes sentences not supported by the cited excerpts; refuses if nothing is left.
Then renumbers citations 1..N in order of appearance and appends the source list."""
import re
import time

from app import config, llm, prompts
from app.agents.composer import not_found_message
from app.agents.specialist import format_excerpts
from app.agents.state import State

BARE_LINE = re.compile(r"^\s*([-*•]|\d+[.)])?\s*$")


def remove_sentences(answer: str, sentences: list[str]) -> str:
    for s in sentences:
        s = s.strip()
        if len(s) > 10:
            answer = answer.replace(s, "")
    lines = [l.rstrip() for l in answer.splitlines()]
    lines = [l for l in lines if not BARE_LINE.match(l) or l == ""]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def citation_entry(n: int, chunk: dict) -> dict:
    url = chunk.get("url", "")
    if chunk.get("page") and url.lower().endswith(".pdf"):
        url = f"{url}#page={chunk['page']}"
    return {"n": n, "chunk_id": chunk["chunk_id"], "source_id": chunk["source_id"], "title": chunk["title"],
            "section": chunk.get("section") or "", "page": chunk.get("page"), "url": url,
            "doc_type": chunk.get("doc_type", ""), "date_downloaded": chunk.get("date_downloaded", ""),
            "snippet": chunk["text"][:300]}


NOTE_CITATION = re.compile(r"((?:Rules change often; confirm the latest on bis\.gov\.in|This is information, not legal advice)\.?)"
                           r"((?:\s*\[\d+\])+)")


def finalize(answer: str, sources: list[dict], language: str) -> tuple[str, list[dict]]:
    """Renumber [n] markers 1..N by first appearance; append the source list."""
    answer = NOTE_CITATION.sub(lambda m: m.group(1).rstrip(".") + ".", answer)  # notes are not cited facts
    order = []
    for m in re.findall(r"\[(\d+)\]", answer):
        n = int(m)
        if 1 <= n <= len(sources) and n not in order:
            order.append(n)
    mapping = {old: new for new, old in enumerate(order, start=1)}
    answer = re.sub(r"\[(\d+)\]", lambda m: f"[{mapping[int(m.group(1))]}]" if int(m.group(1)) in mapping else "", answer)
    citations = [citation_entry(mapping[old], sources[old - 1]) for old in order]
    if citations:
        label = "स्रोत" if language == "hi" else "Sources"
        lines = []
        for c in citations:
            where = ", ".join(x for x in (c["section"][:80] if c["section"] else "",
                                          f"p. {c['page']}" if c["page"] else "") if x)
            lines.append(f"[{c['n']}] {c['title']}" + (f", {where}" if where else "") + f": {c['url']}")
        answer = f"{answer}\n\n**{label}:**\n" + "\n".join(lines)
    return answer, citations


def guard_node(state: State) -> dict:
    t0 = time.time()
    language = state.get("language", "en")
    if state.get("final_answer"):  # composer already refused
        return {"citations": [], "trace": [{"step": "guard", "note": "nothing to check", "ms": 0}]}
    draft, sources = state.get("draft_answer", ""), state.get("sources", [])
    removed, note = [], "all sentences supported"
    try:
        out = llm.generate_json(f"EXCERPTS:\n{format_excerpts(sources)}\n\nANSWER:\n{draft}",
                                system=prompts.GUARD, model=config.GEMINI_ROUTER_MODEL)
        removed = [s["text"] for s in out.get("sentences", []) if not s.get("supported", True)]
        answer = remove_sentences(draft, removed)
        if removed:
            note = f"removed {len(removed)} unsupported sentence(s)"
    except Exception as e:  # guard failure must not block an answer that is already cited
        answer, note = draft, f"guard check failed ({type(e).__name__}); answer kept as drafted"
    if not re.search(r"\[\d+\]", answer):
        intent = (state.get("intents") or [None])[0]
        return {"final_answer": not_found_message(language, intent), "citations": [], "refused": True,
                "trace": [{"step": "guard", "note": "no supported, cited sentence left: refused",
                           "removed": removed, "ms": int((time.time() - t0) * 1000)}]}
    final, citations = finalize(answer, sources, language)
    return {"final_answer": final, "citations": citations, "refused": False,
            "trace": [{"step": "guard", "note": note, "removed": removed, "ms": int((time.time() - t0) * 1000)}]}
