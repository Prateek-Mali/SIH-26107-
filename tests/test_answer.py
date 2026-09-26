"""Answer pipeline with a fake retriever, fake LLM and fake reranker (no network, no models)."""
import os

os.environ["BIS_QUIET"] = "1"

import pytest  # noqa: E402

from app import answer as A  # noqa: E402
from app import expand, llm, rerank  # noqa: E402


def chunk(i, source="guide_grant_of_licence", page=1, text="The applicant shall apply in Form-V with the fee."):
    return {"chunk_id": f"{source}::{i:04d}", "source_id": source, "title": f"Doc {source}", "section": f"{i}. Heading",
            "page": page, "url": f"https://x/{source}.pdf", "scheme": "I", "doc_date": "2026-02-25", "text": text}


CHUNKS = [chunk(0, page=3), chunk(1, page=3), chunk(2, "cert_fee", None, "Application fee is Rs 1000.")]


@pytest.fixture
def fake(monkeypatch):
    state = {"reply": "**Short answer**: Apply in Form-V [1][2]. The application fee is Rs 1000 [3].\n"
                      "Moon rocks are required with the application form [1]."}
    monkeypatch.setattr(A, "retrieve", lambda q: {"chunks": CHUNKS, "trace": {"queries": [q]}})
    monkeypatch.setattr(llm, "generate_with_provider", lambda *a, **k: (state["reply"], "gemini:fake"))

    def fake_scores(q, passages):  # "supported" when the claim shares a key word with the passage
        return [0.9 if any(w in p.lower() for w in ("form-v", "rs 1000") if w in q.lower()) else 0.05 for p in passages]

    monkeypatch.setattr(rerank, "scores", fake_scores)
    monkeypatch.setattr(rerank, "pair_scores", lambda pairs: [fake_scores(q, [p])[0] for q, p in pairs])
    monkeypatch.setattr(A, "_cache", lambda *a, **k: None)
    return state


def test_answer_is_cited_deduped_verified_and_numbered(fake):
    r = A.ask("How do I apply to IBS and what is the fee?")
    assert r["provider"] == "gemini:fake" and not r["refused"]
    assert "Moon rocks" not in r["answer"]                      # unsupported sentence removed
    assert "Apply in Form-V [1]." in r["answer"]                 # [1][2] = same page -> one number
    assert "Rs 1000 [2]" in r["answer"]                          # renumbered by first use
    assert [c["source_id"] for c in r["citations"]] == ["guide_grant_of_licence", "cert_fee"]
    assert r["citations"][0]["url"].endswith("#page=3")
    assert "**Sources:**" in r["answer"]
    assert r["trace"]["citation_check"][0]["action"] == "removed"


def test_not_covered_is_the_only_fallback(fake):
    fake["reply"] = "NOT_COVERED"
    r = A.ask("What is the capital of France?")
    assert r["refused"] and r["answer"].startswith("This is not covered in the official BIS documents")
    assert r["citations"] == []


def test_uncited_model_answer_is_never_shown(fake):
    fake["reply"] = "Paris is the capital of France."  # no citations = model knowledge
    r = A.ask("What is the capital of France?")
    assert r["refused"] and "Paris" not in r["answer"]


def test_recite_to_better_excerpt(fake):
    fake["reply"] = "The application fee is Rs 1000 [1]."  # wrong excerpt cited
    r = A.ask("fee?")
    assert "Rs 1000 [1]" in r["answer"] and r["citations"][0]["source_id"] == "cert_fee"
    assert r["trace"]["citation_check"][0]["action"].startswith("re-cited")


def test_greeting_needs_no_llm(fake, monkeypatch):
    monkeypatch.setattr(llm, "generate_with_provider", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    assert "BIS Assistant" in A.ask("namaste")["answer"]


def test_expand_rules():
    assert expand.normalize("register under IBS for is1293") == "register under BIS for IS 1293"
    assert expand.detect_scheme("I import toys, what licence?") == "FMCS"
    assert expand.detect_scheme("documents for ISI licence") == "I"
    assert expand.detect_scheme("compare Scheme I and Scheme II") is None
    assert expand.detect_scheme("CRS registration for mobile chargers") == "II"
    assert "bis_act_2016" in expand.source_boosts("penalty for fake ISI mark")
    assert len(expand.expansions("documents and fee for licence renewal")) == 3


def test_provider_fallback(monkeypatch):
    from app import config
    monkeypatch.setattr(config, "KEY_IS_SET", True)
    monkeypatch.setattr(config, "GROQ_API_KEY", "k")
    monkeypatch.setattr(llm, "_call", lambda *a, **k: (_ for _ in ()).throw(llm.AllModelsBusy("429")))
    monkeypatch.setattr(llm, "groq_generate", lambda *a, **k: "from groq")
    assert llm.generate_with_provider("q") == ("from groq", f"groq:{config.GROQ_MODEL}")
