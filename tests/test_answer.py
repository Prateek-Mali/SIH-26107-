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
    monkeypatch.setattr(A, "retrieve", lambda q, **k: {"chunks": CHUNKS, "trace": {"queries": [q], "ms": 1}})
    monkeypatch.setattr(A, "understand", lambda q, h=None, p=None: {
        "intent": "process", "user_role": "manufacturer", "user_goal": "", "product_or_topic": "",
        "standalone_question": q, "sub_questions": [], "language": "en", "provider": "fake"})
    monkeypatch.setattr(llm, "generate_with_provider", lambda *a, **k: (state["reply"], "gemini:fake"))

    def fake_scores(q, passages):  # "supported" when the claim shares a key word with the passage
        return [0.9 if any(w in p.lower() for w in ("form-v", "rs 1000") if w in q.lower()) else 0.05 for p in passages]

    monkeypatch.setattr(rerank, "scores", fake_scores)
    monkeypatch.setattr(rerank, "pair_scores", lambda pairs: [fake_scores(q, [p])[0] for q, p in pairs])
    monkeypatch.setattr(A, "_cache", lambda *a, **k: None)
    monkeypatch.setattr(A, "log_refusal", lambda *a, **k: None)  # tests must not write to data/refusals.jsonl
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
    # hand-written boosts/expansions were removed in Task 8 (they were tuned to test questions)
    assert expand.source_boosts("penalty for fake ISI mark") == [] and expand.expansions("fees") == []
    assert expand.normalize("register under IBS for is1293") == "register under BIS for IS 1293"
    assert expand.detect_scheme("I import toys, what licence?") == "FMCS"
    assert expand.detect_scheme("documents for ISI licence") == "I"
    assert expand.detect_scheme("compare Scheme I and Scheme II") is None
    assert expand.detect_scheme("CRS registration for mobile chargers") == "II"


def test_provider_fallback(monkeypatch):
    from app import config
    monkeypatch.setattr(config, "KEY_IS_SET", True)
    monkeypatch.setattr(config, "GROQ_API_KEY", "k")
    monkeypatch.setattr(llm, "_call", lambda *a, **k: (_ for _ in ()).throw(llm.AllModelsBusy("429")))
    monkeypatch.setattr(llm, "groq_generate", lambda *a, **k: "from groq")
    assert llm.generate_with_provider("q") == ("from groq", f"groq:{config.GROQ_MODEL}")


def test_marker_formats_are_normalised():
    assert A.normalize_markers("Fee is Rs 1000 [1, 2, 6]. Steps [3-5].") == "Fee is Rs 1000 [1][2][6]. Steps [3][4][5]."


def test_splitter_and_list_renumbering():
    assert A.SENTENCE_SPLIT.split("Inspection fee is Rs. 7,000 per man day [1]. Next.") == ["Inspection fee is Rs. 7,000 per man day [1].", "Next."]
    assert A.renumber_lists("1. a\n2. b\n4. c\n\ntext\n3. d") == "1. a\n2. b\n3. c\n\ntext\n1. d"


def test_understand_rules_and_profile_memory(monkeypatch):
    from app import understand as U
    monkeypatch.setattr(llm, "generate_with_provider", lambda *a, **k: (_ for _ in ()).throw(llm.ProviderError("x")))
    u = U.understand("Difference between ISI mark and CRS?")
    assert u["intent"] == "compare"
    u = U.understand("and how much does it cost?", [], {"user_role": "importer", "product_or_topic": "LED bulbs"})
    assert u["user_role"] == "importer" and u["product_or_topic"] == "LED bulbs"


def test_uncited_facts_need_support_but_advice_does_not():
    assert A.needs_citation("Present the HUID to customs for clearance of LED bulbs.", "Present the HUID to customs for clearance of LED bulbs.")
    assert not A.needs_citation("Visit Manak Online and create an account today.", "Visit Manak Online and create an account today.")
    assert not A.needs_citation("**3. Which scheme**", "3. Which scheme")
    assert A.tidy("**A**\n\n**B**\ntext [8.1]\n1. x\n   - sub\n3. y") == "**B**\ntext\n1. x\n   - sub\n2. y"


def test_followup_detection():
    from app.understand import is_followup
    assert is_followup("and how much does it cost?") and is_followup("what about renewal?")
    assert not is_followup("Difference between ISI mark and CRS for electronic goods sold in India?")
    assert not is_followup("Difference between ISI mark and CRS?")


def test_quantities_must_match_with_units():
    assert not A.numbers_ok("Apply 3 months before expiry.", "apply preferably two months prior; see clause 3")
    assert A.numbers_ok("Apply two months before expiry.", "preferably two months prior to the validity date")
