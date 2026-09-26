"""product_qco specialist agent: looks the product up in the BIS product tables first."""
from app.agents.specialist import run_specialist
from app.agents.state import State
from app.tools import lookup_product


def product_qco_node(state: State) -> dict:
    query = state.get("search_query") or state["question"]
    rows = lookup_product(query)
    if not rows and query != state["question"]:
        rows = lookup_product(state["question"])
    return run_specialist("product_qco", state, extra_chunks=rows)
