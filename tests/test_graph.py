"""Graph routing tests with a fake LLM and fake search (no network, no API key)."""
import json
import os

os.environ["BIS_QUIET"] = "1"

import pytest  # noqa: E402

from app import llm  # noqa: E402
from app.agents import guard as guard_mod  # noqa: E402
from app.agents import product_qco_agent, specialist  # noqa: E402
from app.graph import answer  # noqa: E402

CHUNKS = {
    "product_qco": [{"chunk_id": "scheme1::row0000", "source_id": "scheme1", "agent": "product_qco",
                     "title": "Scheme I products", "url": "https://www.bis.gov.in/scheme-1/", "page": None,
                     "section": "Cement", "doc_type": "qco", "date_downloaded": "2026-09-26",
                     "text": "Product: LED lamps | IS 16102 | Scheme I | QCO: LED Lamps Order S.O. 1(E)"}],
    "certification": [{"chunk_id": "cert_fee::0000", "source_id": "cert_fee", "agent": "certification",
                       "title": "Product Certification Fee", "url": "https://www.bis.gov.in/fee/", "page": None,
                       "section": "Fee", "doc_type": "page", "date_downloaded": "2026-09-26",
                       "text": "Application fee is Rs 1000."}],
}


@pytest.fixture
def fake(monkeypatch):
    calls = []

    def fake_json(prompt, system=None, model=None):
        calls.append(system)
        if system.startswith("You route"):
            q = prompt.lower()
            if "cricket" in q:
                return {"intents": [], "language": "en", "is_greeting": False, "out_of_scope": True, "search_query": q}
            return {"intents": ["product_qco", "certification"], "language": "en", "is_greeting": False,
                    "out_of_scope": False, "search_query": "LED bulb ISI compulsory fee"}
        if system.startswith("You check"):
            answer_text = prompt.split("ANSWER:\n", 1)[1]
            sents = [{"text": s, "supported": "moon" not in s} for s in answer_text.split("\n") if s.strip()]
            return {"sentences": sents}
        if "PRODUCT & QCO" in system:
            return {"answer": "Yes, LED lamps need ISI under IS 16102 [1].", "used": [1]}
        return {"answer": "The application fee is Rs 1000 [1].\nThe moon is made of cheese [1].", "used": [1]}

    monkeypatch.setattr(llm, "generate_json", fake_json)
    monkeypatch.setattr(llm, "generate", lambda prompt, system=None, **k:
                        "Yes, LED lamps need ISI under IS 16102 [1].\nThe application fee is Rs 1000 [2].\nThe moon is made of cheese [2].")
    monkeypatch.setattr(specialist, "search", lambda q, agent=None, k=None: CHUNKS.get(agent, []))
    monkeypatch.setattr(product_qco_agent, "lookup_product", lambda q: [])
    return calls


def test_multi_intent_routes_to_two_agents_and_guard_removes_unsupported(fake):
    r = answer("I make LED bulbs, is ISI compulsory and what is the fee?")
    steps = [t["step"] for t in r["trace"]]
    assert set(steps) >= {"router", "product_qco", "certification", "composer", "guard"}
    assert r["intents"] == ["product_qco", "certification"]
    assert "moon" not in r["final_answer"]
    assert "IS 16102 [1]" in r["final_answer"] and "Rs 1000 [2]" in r["final_answer"]
    assert [c["chunk_id"] for c in r["citations"]] == ["scheme1::row0000", "cert_fee::0000"]
    assert "**Sources:**" in r["final_answer"] and not r["refused"]


def test_out_of_scope_is_refused_without_retrieval(fake):
    r = answer("Who won the cricket world cup?")
    assert r["refused"] is True
    assert "only help with BIS" in r["final_answer"]
    assert [t["step"] for t in r["trace"]] == ["router", "direct"]


def test_greeting_skips_the_llm(fake):
    r = answer("namaste")
    assert not r["refused"] and "BIS" in r["final_answer"]
    assert fake == []  # no model call at all


def test_not_found_gives_official_link(fake, monkeypatch):
    monkeypatch.setattr(specialist, "search", lambda q, agent=None, k=None: [])
    r = answer("I make LED bulbs, is ISI compulsory and what is the fee?")
    assert r["refused"] and "could not find this in official BIS documents" in r["final_answer"]
    assert "https://" in r["final_answer"]


def test_finalize_renumbers_by_first_use():
    src = [{"chunk_id": f"c{i}", "source_id": "s", "title": f"T{i}", "url": "https://x/a.pdf", "page": i,
            "section": "", "text": "t"} for i in range(1, 4)]
    text, cites = guard_mod.finalize("A [3]. B [1][3].", src, "en")
    assert text.startswith("A [1]. B [2][1].")
    assert [c["chunk_id"] for c in cites] == ["c3", "c1"]
    assert cites[0]["url"] == "https://x/a.pdf#page=3"
    json.dumps(cites)  # API-serialisable


def test_notes_lose_their_citation_markers():
    src = [{"chunk_id": "c1", "source_id": "s", "title": "T", "url": "https://x/", "page": None, "section": "", "text": "t"}]
    text, cites = guard_mod.finalize("Fee is Rs 1000 [1]. Rules change often; confirm the latest on bis.gov.in [1].", src, "en")
    assert "bis.gov.in." in text and "bis.gov.in [1]" not in text and len(cites) == 1
