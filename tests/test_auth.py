"""Login: signup/login/logout, protected endpoints, per-user conversations (in-memory fake of MongoDB)."""
import pytest
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

from app import auth, memory


class FakeCollection:
    def __init__(self, unique=None):
        self.docs, self.unique = [], unique

    def create_index(self, *a, **k):
        pass

    def insert_one(self, doc):
        if self.unique and any(d[self.unique] == doc[self.unique] for d in self.docs):
            raise DuplicateKeyError("dup")
        self.docs.append(dict(doc))

    def find_one(self, q):
        return next((d for d in self.docs if all(d.get(k) == v for k, v in q.items())), None)

    def delete_one(self, q):
        self.docs = [d for d in self.docs if not all(d.get(k) == v for k, v in q.items())]


class FakeDB:
    def __init__(self):
        self.users, self.login_sessions = FakeCollection("email"), FakeCollection()


@pytest.fixture
def client(monkeypatch, tmp_path):
    db = FakeDB()
    monkeypatch.setattr(auth, "_db", lambda: db)
    monkeypatch.setattr(memory, "DB", tmp_path / "memory.sqlite")
    monkeypatch.setattr(memory, "chat", lambda m, sid=None, use_cache=True, owner="": {
        "answer": "ok", "session_id": memory.ensure(sid, owner)})
    from app import api
    monkeypatch.setattr(api, "FAILED", {})
    return TestClient(api.app), db


def test_signup_login_logout_and_protection(client):
    c, db = client
    assert c.get("/sessions").status_code == 401                                   # not signed in
    assert c.post("/auth/signup", json={"email": "a@x.in", "password": "short"}).status_code == 400
    assert c.post("/auth/signup", json={"email": "A@x.in", "password": "longenough1"}).status_code == 200
    assert db.users.docs[0]["email"] == "a@x.in" and "longenough1" not in str(db.users.docs[0])  # hash only
    assert c.get("/auth/me").json() == {"email": "a@x.in"}
    assert c.post("/auth/signup", json={"email": "a@x.in", "password": "longenough1"}).status_code == 400  # duplicate
    c.post("/auth/logout")
    assert c.get("/auth/me").status_code == 401
    assert c.post("/auth/login", json={"email": "a@x.in", "password": "wrongpass1"}).status_code == 401
    assert c.post("/auth/login", json={"email": "a@x.in", "password": "longenough1"}).status_code == 200


def test_users_see_only_their_own_conversations(client):
    c, _ = client
    c.post("/auth/signup", json={"email": "a@x.in", "password": "longenough1"})
    sid = c.post("/chat", json={"message": "hi"}).json()["session_id"]
    memory.add_turn(sid, "user", "hi")
    assert [s["session_id"] for s in c.get("/sessions").json()] == [sid]
    c.post("/auth/logout")
    c.post("/auth/signup", json={"email": "b@x.in", "password": "longenough2"})
    assert c.get("/sessions").json() == []
    assert c.get(f"/session/{sid}").status_code == 404 and c.delete(f"/session/{sid}").status_code == 404
    other = c.post("/chat", json={"message": "hi", "session_id": sid}).json()["session_id"]
    assert other != sid                                                              # cannot write into a's chat


def test_login_attempts_are_limited_and_reindex_is_admin_only(client, monkeypatch):
    c, _ = client
    for _ in range(10):
        assert c.post("/auth/login", json={"email": "x@x.in", "password": "wrongpass1"}).status_code == 401
    assert c.post("/auth/login", json={"email": "x@x.in", "password": "wrongpass1"}).status_code == 429
    from app import api, config
    monkeypatch.setattr(api, "FAILED", {})
    monkeypatch.setattr(config, "ADMIN_EMAILS", {"boss@x.in"})
    c.post("/auth/signup", json={"email": "a@x.in", "password": "longenough1"})
    assert c.post("/admin/reindex").status_code == 403


def test_errors_do_not_leak_internals(client, monkeypatch):
    c, _ = client
    c.post("/auth/signup", json={"email": "a@x.in", "password": "longenough1"})
    monkeypatch.setattr(memory, "chat", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("secret path /Users/x")))
    r = c.post("/chat", json={"message": "hi"}).json()
    assert "secret" not in r["error"] and r["error"].startswith("Something went wrong")
