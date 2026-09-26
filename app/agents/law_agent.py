"""law specialist agent."""
from app.agents.specialist import run_specialist
from app.agents.state import State


def law_node(state: State) -> dict:
    return run_specialist("law", state)
