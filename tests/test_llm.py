"""Model and key fallback order, with fake clients (no network)."""
import pytest
from google.genai import errors

from app import config, llm


def api_error(code):
    return errors.APIError(code, {"error": {"code": code, "message": "x", "status": "x"}})


@pytest.fixture
def fake(monkeypatch):
    monkeypatch.setattr(llm, "_clients", ["key1", "key2"])
    monkeypatch.setattr(llm, "_cooldown", {})
    monkeypatch.setattr(config, "GEMINI_MODEL_FALLBACKS", ["m2", "m3"])
    monkeypatch.setattr(config, "GEMINI_ROUTER_FALLBACKS", ["r2"])
    monkeypatch.setattr(config, "GEMINI_ROUTER_MODEL", "r1")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)


def test_quota_tries_other_key_then_next_model(fake):
    calls = []

    def fn(c, m):
        calls.append((c, m))
        if m == "m1" or (m == "m2" and c == "key1"):
            raise api_error(429)
        return f"{c}:{m}"

    assert llm._call(fn, llm.model_chain("m1")) == "key2:m2"
    assert calls == [("key1", "m1"), ("key2", "m1"), ("key1", "m2"), ("key2", "m2")]
    # m1 (both keys) and key1:m2 are cooling down: the next call goes straight to key2:m2
    calls.clear()
    llm._call(fn, llm.model_chain("m1"))
    assert calls == [("key2", "m2")]


def test_unknown_model_is_skipped_for_good_and_bad_request_raises(fake):
    assert llm._call(lambda c, m: (_ for _ in ()).throw(api_error(404)) if m == "m1" else m,
                     llm.model_chain("m1")) == "m2"
    with pytest.raises(errors.APIError):
        llm._call(lambda c, m: (_ for _ in ()).throw(api_error(400)), ["m2"])


def test_router_chain_and_all_busy(fake):
    assert llm.model_chain("r1") == ["r1", "r2"]
    assert llm.model_chain("m1") == ["m1", "m2", "m3"]
    with pytest.raises(llm.AllModelsBusy):
        llm._call(lambda c, m: (_ for _ in ()).throw(api_error(503)), ["m1"], rounds=2)
