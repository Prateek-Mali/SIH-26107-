"""Composer: merges specialist answers into one reply with one shared citation numbering."""
import re
import time

from app import llm, prompts
from app.agents.state import State
from app.tools import official_link


def not_found_message(language: str, intent: str | None) -> str:
    template = prompts.NOT_FOUND_HI if language == "hi" else prompts.NOT_FOUND_EN
    return template.format(link=official_link(intent))


def renumber(answer: str, used_chunks: list[dict], sources: list[dict], index: dict) -> str:
    """Map an agent's local [n] markers to global numbers in `sources` (extended in place)."""
    mapping = {}
    for n, chunk in enumerate(used_chunks, start=1):
        if chunk is None:
            continue
        if chunk["chunk_id"] not in index:
            sources.append(chunk)
            index[chunk["chunk_id"]] = len(sources)
        mapping[n] = index[chunk["chunk_id"]]
    return re.sub(r"\[(\d+)\]", lambda m: f"[{mapping[int(m.group(1))]}]" if int(m.group(1)) in mapping else "", answer)


def composer_node(state: State) -> dict:
    t0 = time.time()
    outputs = state.get("agent_outputs", {})
    intents = state.get("intents", [])
    language = state.get("language", "en")
    found = {a: outputs[a] for a in intents if a in outputs and outputs[a]["answer"] != "NOT_FOUND"}
    missing = [a for a in intents if a not in found]

    if not found:
        return {"draft_answer": "", "sources": [], "refused": True,
                "final_answer": not_found_message(language, intents[0] if intents else None),
                "trace": [{"step": "composer", "note": "no specialist found an answer",
                           "ms": int((time.time() - t0) * 1000)}]}

    sources, index, parts = [], {}, {}
    for agent, out in found.items():
        # only cited excerpts become sources; others are left as None so their markers are dropped
        cited = [c if (n + 1) in out["used"] else None for n, c in enumerate(out["chunks"])]
        parts[agent] = renumber(out["answer"], cited, sources, index)

    if len(parts) == 1 and not missing and language == "en":
        draft, mode = next(iter(parts.values())), "single agent, no merge needed"
    else:
        blocks = [f"### {a} specialist\n{t}" for a, t in parts.items()]
        blocks += [f"### {a} specialist\nNOT_FOUND (official link: {official_link(a)})" for a in missing]
        system = prompts.COMPOSER.format(rules=prompts.RULES, links=prompts.OFFICIAL_LINKS_TEXT,
                                         language_name="Hindi" if language == "hi" else "English")
        draft = llm.generate(f"QUESTION: {state['question']}\n\n" + "\n\n".join(blocks), system=system)
        mode = f"merged {len(parts)} answers" + (f", {len(missing)} not found" if missing else "")
    return {"draft_answer": draft.strip(), "sources": sources,
            "trace": [{"step": "composer", "note": mode, "sources": [s["chunk_id"] for s in sources],
                       "ms": int((time.time() - t0) * 1000)}]}
