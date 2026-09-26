"""certification specialist agent."""
from app.agents.specialist import run_specialist
from app.agents.state import State


def certification_node(state: State) -> dict:
    return run_specialist("certification", state)
