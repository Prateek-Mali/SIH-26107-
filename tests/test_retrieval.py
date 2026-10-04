import os

os.environ["BIS_QUIET"] = "1"

import pytest  # noqa: E402

from app import config  # noqa: E402
from app.retrieval import bm25_search, normalize_ids, rrf, search, tokenize  # noqa: E402
from app.tools import lookup_product  # noqa: E402


def test_id_normalisation():
    assert "is12330" in tokenize("IS 12330") and "is12330" in tokenize("IS:12330") and "is12330" in tokenize("is12330")
    assert "so191e" in normalize_ids("S.O. 191(E)") and "so191e" in normalize_ids("SO 191 (E)")
    assert "gsr1081e" in normalize_ids("G.S.R. No. 1081(E)")


def test_rrf_merges_rankings():
    a = [{"chunk_id": "x"}, {"chunk_id": "y"}]
    b = [{"chunk_id": "y"}, {"chunk_id": "z"}]
    assert [r["chunk_id"] for r in rrf(a, b)][0] == "y"


needs_index = pytest.mark.skipif(not config.BM25_PATH.exists(), reason="run scripts/build_index.py first")


@needs_index
def test_is_number_finds_cement_row_first():
    assert "IS 12330" in search("IS 12330")[0]["text"]
    assert "Sulphate Resisting Portland Cement" in bm25_search("IS 12330")[0]["text"]


@needs_index
def test_penalty_question_finds_bis_act():
    top = search("penalty for misuse of standard mark", k=5)
    assert any(c["source_id"] == "bis_act_2016" for c in top)


@needs_index
def test_agent_filter():
    assert all(c["agent"] == "law" for c in search("standard mark", agent="law"))


def test_lookup_product():
    if not list((config.DATA / "structured").glob("*.csv")):
        pytest.skip("no product CSVs yet")
    hit = lookup_product("IS 12330")[0]
    assert "IS 12330" in hit["text"] and hit["chunk_id"].startswith("scheme1_products_table::row")
    assert any("Portland" in r["text"] for r in lookup_product("portland pozzolana cement"))
