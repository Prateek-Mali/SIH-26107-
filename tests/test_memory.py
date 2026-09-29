"""Local conversation memory: storage, profile rules, privacy, recall (no models)."""
import pytest

from app import memory as M


@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(M, "DB", tmp_path / "memory.sqlite")


def test_profile_comes_only_from_the_users_words():
    u = {"user_role": "manufacturer", "product_attrs": {"product_type": "stainless steel water bottle"}}
    p = M.profile_from("I make stainless-steel water bottles in Udaipur. Which standard?", u)
    assert p == {"role": "manufacturer", "product": "stainless steel water bottle", "location": "Udaipur",
                 "maker_location": "india"}
    assert M.profile_from("Is it compulsory?", {"user_role": "manufacturer"}) == {}   # nothing new stated
    assert M.profile_from("Now tell me the same in Hindi", {})["language"] == "hi"
    assert M.profile_from("What about IS 17803 under Scheme I?", {}) == {"is_number": "IS 17803", "scheme": "Scheme I"}


def test_personal_data_is_not_stored():
    sid = M.new_session()
    M.add_turn(sid, "user", "call me on 9876543210 or a@b.com, aadhaar 1234 5678 9012")
    assert M.turns(sid)[0]["content"] == "call me on [phone] or [email], aadhaar [id number]"


def test_history_keeps_last_turns_trimmed_with_citations_and_recall():
    sid = M.new_session()
    for i in range(5):
        M.add_turn(sid, "user", f"question {i}")
        M.add_turn(sid, "assistant", "x" * 900 + "\n\n**Sources:**\n[1] doc", ["c::0001"])
    h = M.history(sid)
    assert len(h) == 6 and h[-1]["citations"] == ["c::0001"] and len(h[-1]["content"]) == 600
    assert "Sources" not in h[-1]["full"]
    assert "4. question 3" in M.recall_answer(sid)


def test_forget_and_purge():
    sid = M.new_session()
    M.add_turn(sid, "user", "hello there")
    M.set_profile(sid, {"role": "importer", "phone": "x"})       # unknown keys are never stored
    assert M.profile(sid) == {"role": "importer"}
    M.forget(sid)
    assert M.turns(sid) == [] and M.profile(sid) == {}
    old = M.new_session()
    with M.db() as con:
        con.execute("UPDATE sessions SET updated_at=0 WHERE session_id=?", (old,))
    M.purge_old()
    assert old not in [s["session_id"] for s in M.sessions()]
