"""The shared LangGraph state."""
import operator
from typing import Annotated, TypedDict


def merge_dicts(a: dict, b: dict) -> dict:
    return {**(a or {}), **(b or {})}


class AgentOutput(TypedDict):
    answer: str          # answer with local [n] markers, or "NOT_FOUND"
    chunks: list[dict]   # excerpts shown to the agent, in [n] order (n = index + 1)
    used: list[int]      # excerpt numbers the agent cited


class State(TypedDict, total=False):
    question: str
    history: list[dict]                 # previous turns [{role, content}] for follow-up questions
    language: str                       # "en" | "hi"
    intents: list[str]
    search_query: str                   # standalone English query from the router
    is_greeting: bool
    out_of_scope: bool
    agent_outputs: Annotated[dict[str, AgentOutput], merge_dicts]  # parallel agents write here
    draft_answer: str                   # composer output with global [n] markers
    sources: list[dict]                 # global source list for the draft ([n] = index + 1)
    final_answer: str
    citations: list[dict]
    refused: bool
    trace: Annotated[list[dict], operator.add]
