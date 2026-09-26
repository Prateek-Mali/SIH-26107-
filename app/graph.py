"""The agent graph: router -> specialists (parallel) -> composer -> guard.

    answer(question, history=None) -> final state dict
    stream(question, history=None)  -> yields (node_name, update) as each node finishes
"""
import time
from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app import prompts
from app.agents.certification_agent import certification_node
from app.agents.composer import composer_node
from app.agents.guard import guard_node
from app.agents.hallmarking_consumer_agent import hallmarking_consumer_node
from app.agents.law_agent import law_node
from app.agents.product_qco_agent import product_qco_node
from app.agents.router import router_node
from app.agents.state import State

SPECIALISTS = {
    "law": law_node,
    "certification": certification_node,
    "product_qco": product_qco_node,
    "hallmarking_consumer": hallmarking_consumer_node,
}


def direct_node(state: State) -> dict:
    """Greetings and out-of-scope questions: reply without retrieval."""
    hi = state.get("language") == "hi"
    if state.get("is_greeting"):
        text, refused = (prompts.GREETING_HI if hi else prompts.GREETING_EN), False
    else:
        text, refused = (prompts.OUT_OF_SCOPE_HI if hi else prompts.OUT_OF_SCOPE_EN), True
    return {"final_answer": text, "citations": [], "refused": refused,
            "trace": [{"step": "direct", "note": "greeting" if state.get("is_greeting") else "out of scope"}]}


def after_router(state: State) -> list[str]:
    if state.get("is_greeting") or state.get("out_of_scope") or not state.get("intents"):
        return ["direct"]
    return state["intents"]  # these run in parallel


@lru_cache(maxsize=1)
def build_graph():
    g = StateGraph(State)
    g.add_node("router", router_node)
    g.add_node("direct", direct_node)
    for name, fn in SPECIALISTS.items():
        g.add_node(name, fn)
        g.add_edge(name, "composer")
    g.add_node("composer", composer_node)
    g.add_node("guard", guard_node)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", after_router, ["direct", *SPECIALISTS])
    g.add_edge("direct", END)
    g.add_edge("composer", "guard")
    g.add_edge("guard", END)
    return g.compile()


def initial_state(question: str, history: list[dict] | None) -> State:
    return {"question": question.strip(), "history": history or [], "agent_outputs": {}, "trace": [],
            "final_answer": "", "citations": [], "refused": False}


def answer(question: str, history: list[dict] | None = None) -> dict:
    t0 = time.time()
    result = build_graph().invoke(initial_state(question, history))
    result["latency_ms"] = int((time.time() - t0) * 1000)
    return result


def stream(question: str, history: list[dict] | None = None):
    for update in build_graph().stream(initial_state(question, history), stream_mode="updates"):
        for node, data in update.items():
            yield node, data or {}


if __name__ == "__main__":
    import json
    import sys

    r = answer(" ".join(sys.argv[1:]) or "Is ISI mark compulsory for cement?")
    print(r["final_answer"])
    print(json.dumps([{k: v for k, v in t.items() if k != "retrieved"} for t in r["trace"]], indent=1, ensure_ascii=False))
