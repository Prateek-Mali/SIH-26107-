"""Hybrid search: Qdrant vectors + BM25 keywords, fused with Reciprocal Rank Fusion.

    search(query, agent=None, k=8) -> list[chunk dict with 'score']
"""
import pickle
import re
import time
from functools import lru_cache

from app import config

CANDIDATES = 20
RRF_K = 60

STOPWORDS = set("""a an and are as at be by can do does for from has have how i if in is it its of on or
that the this to was what when where which who why will with my me we you your our under shall""".split())


def embed_text(chunk: dict) -> str:
    """Text used for both embeddings and BM25: title and section give context to short chunks."""
    head = " | ".join(x for x in (chunk.get("title"), chunk.get("section")) if x)
    return f"{head}\n{chunk['text']}" if head else chunk["text"]


def normalize_ids(text: str) -> str:
    """Make official numbers match however they are typed: IS 12330 / IS:12330 / IS12330 -> is12330,
    S.O. 191(E) / SO 191 (E) -> so191e, G.S.R. 1081(E) -> gsr1081e."""
    t = text.lower()
    t = re.sub(r"\bis\s*[:\-]?\s*(\d{1,5})", r" is\1 \1 ", t)
    t = re.sub(r"\bs\.?\s*o\.?\s*(?:no\.?\s*)?(\d{1,5})\s*\(\s*e\s*\)", r" so\1e ", t)
    t = re.sub(r"\bg\.?\s*s\.?\s*r\.?\s*(?:no\.?\s*)?(\d{1,5})\s*\(\s*e\s*\)", r" gsr\1e ", t)
    return t


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+|[ऀ-ॿ]+", normalize_ids(text))
    return [t for t in tokens if t not in STOPWORDS]


@lru_cache(maxsize=1)
def _bm25():
    with config.BM25_PATH.open("rb") as f:
        data = pickle.load(f)
    return data["bm25"], data["chunks"]


@lru_cache(maxsize=1)
def _qdrant():
    import atexit

    from qdrant_client import QdrantClient

    client = QdrantClient(path=config.QDRANT_PATH)
    atexit.register(client.close)  # close cleanly (avoids a noisy warning at interpreter exit)
    return client


def bm25_search(query: str, agent: str | None = None, n: int = CANDIDATES) -> list[dict]:
    bm25, chunks = _bm25()
    scores = bm25.get_scores(tokenize(query))
    order = sorted(range(len(chunks)), key=lambda i: -scores[i])
    out = []
    for i in order:
        if scores[i] <= 0:
            break
        if agent and chunks[i]["agent"] != agent:
            continue
        out.append({**chunks[i], "bm25_score": float(scores[i])})
        if len(out) == n:
            break
    return out


def vector_search(query: str, agent: str | None = None, n: int = CANDIDATES) -> list[dict]:
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    from app.llm import embed

    vec = embed([query], task="RETRIEVAL_QUERY", rounds=1)[0]  # fail fast: BM25 is the fallback
    flt = Filter(must=[FieldCondition(key="agent", match=MatchValue(value=agent))]) if agent else None
    hits = _qdrant().query_points(config.COLLECTION, query=vec, query_filter=flt, limit=n).points
    return [{**h.payload, "vector_score": h.score} for h in hits]


def rrf(*ranked_lists: list[dict], k: int = RRF_K) -> list[dict]:
    scores, items = {}, {}
    for lst in ranked_lists:
        for rank, item in enumerate(lst):
            cid = item["chunk_id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
            items[cid] = {**items.get(cid, {}), **item}
    return [{**items[cid], "score": s} for cid, s in sorted(scores.items(), key=lambda x: -x[1])]


_vector_paused_until = 0.0


def search(query: str, agent: str | None = None, k: int | None = None) -> list[dict]:
    global _vector_paused_until
    k = k or config.TOP_K
    keyword = bm25_search(query, agent)
    vector = []
    if time.time() >= _vector_paused_until:
        try:
            vector = vector_search(query, agent)
        except Exception as e:  # no key / quota / no vector index / network: keyword search still works
            _vector_paused_until = time.time() + 600  # do not slow down every question; retry in 10 min
            print(f"[retrieval] vector search paused for 10 min ({type(e).__name__}: {str(e)[:120]}); BM25 only")
    return rrf(vector, keyword)[:k]
