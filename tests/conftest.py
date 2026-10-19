import pytest


@pytest.fixture(autouse=True)
def _no_writes_to_data(monkeypatch, tmp_path):
    """Tests never append to the real logs in data/."""
    from app import answer, understand
    monkeypatch.setattr(understand, "FAIL_LOG", tmp_path / "understand_failures.jsonl")
    monkeypatch.setattr(answer, "REFUSAL_LOG", tmp_path / "refusals.jsonl")
