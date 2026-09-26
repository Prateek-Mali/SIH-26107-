"""hallmarking_consumer specialist agent."""
from app.agents.specialist import run_specialist
from app.agents.state import State


def hallmarking_consumer_node(state: State) -> dict:
    return run_specialist("hallmarking_consumer", state)
