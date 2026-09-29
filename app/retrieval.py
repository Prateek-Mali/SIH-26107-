"""Hybrid search: Qdrant vectors + BM25 keywords, fused with Reciprocal Rank Fusion.

    search(query, agent=None, k=8) -> list[chunk dict with 'score']
"""
import os
import pickle
import re
import time
from functools import lru_cache
from pathlib import Path

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
    t = re.sub(r"\bis(?:\s*/\s*(?:iec|iso))?\s*[:\-]?\s*(\d{1,5})", r" is\1 \1 ", t)
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
    return open_local_qdrant(config.QDRANT_PATH)


def open_local_qdrant(path: str):
    """Open an embedded Qdrant store; if another process (the chat, the API) holds it, read a snapshot copy."""
    import atexit

    from qdrant_client import QdrantClient

    try:
        client = QdrantClient(path=path)
    except RuntimeError as e:
        if "already accessed" not in str(e):
            raise
        import shutil
        import tempfile

        snap = Path(tempfile.mkdtemp(prefix="bis_qdrant_")) / "qdrant"
        shutil.copytree(path, snap, ignore=shutil.ignore_patterns(".lock"))
        print("[retrieval] index is open in another process; using a read-only snapshot copy")
        client = QdrantClient(path=str(snap))
    atexit.register(client.close)  # close cleanly (avoids a noisy warning at interpreter exit)
    return client


# Words people use -> words the official documents use.
SYNONYMS = [
    (r"\bisi\b", "standard mark"),
    (r"\blicen[cs]e\b", "licence license"),
    (r"\bcrs\b", "compulsory registration"),
    (r"\bhuid\b", "hallmark unique identification"),
    (r"\bregistration\b", "registration licence application"),
    # verbs people type -> the nouns the documents use (keyword search has no stemming)
    (r"\bcomplain(ed|ing|s)?\b", "complaint"), (r"\brenew(ed|ing|s)?\b", "renewal"),
    (r"\bapply(ing)?\b|\bapplied\b", "application"), (r"\bcancel(l?ed|l?ing|s)?\b", "cancellation"),
    (r"\bsuspend(ed|ing|s)?\b", "suspension"), (r"\binspect(ed|ing|s)?\b", "inspection"),
    (r"\bregister(ed|ing|s)?\b", "registration"), (r"\bcertif(y|ied|ying)\b", "certification"),
    (r"\btest(ed|ing)?\b", "testing test report"), (r"\bfake|counterfeit|misuse\b", "misuse"),
]


def expand_query(query: str) -> str:
    extra = [rep for pat, rep in SYNONYMS if re.search(pat, query, re.I)]
    return query + (" " + " ".join(extra) if extra else "")


def bm25_search(query: str, agent: str | None = None, n: int = CANDIDATES) -> list[dict]:
    bm25, chunks = _bm25()
    scores = bm25.get_scores(tokenize(expand_query(query)))
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
_vector_error = ""


def vector_search_many(queries: list[str], n: int) -> list[list[dict]]:
    """One embedding call for all queries, then one Qdrant query each. Empty lists if unavailable."""
    global _vector_paused_until, _vector_error
    if time.time() < _vector_paused_until:
        return [[] for _ in queries]
    try:
        from app.llm import embed

        vecs = embed(queries, task="RETRIEVAL_QUERY", rounds=1)
        client = _qdrant()
        return [[{**h.payload, "vector_score": h.score}
                 for h in client.query_points(config.COLLECTION, query=v, limit=n).points] for v in vecs]
    except Exception as e:  # embedding server down / index missing: keyword search still works
        _vector_paused_until = time.time() + 120
        _vector_error = f"{type(e).__name__}: {str(e)[:160]}"
        print(f"[retrieval] vector search unavailable ({_vector_error}); using BM25 only for 2 min")
        return [[] for _ in queries]


def search(query: str, agent: str | None = None, k: int | None = None) -> list[dict]:
    """Plain hybrid search for one query (used by tests and debugging)."""
    keyword = bm25_search(query, agent)
    vector = [c for c in vector_search_many([query], CANDIDATES)[0] if not agent or c["agent"] == agent]
    return rrf(vector, keyword)[:k or config.TOP_K]


# ---------------------------------------------------------------- the full retrieval pipeline
@lru_cache(maxsize=1)
def _store():
    """chunk_id -> chunk, and (source_id, position) for neighbour lookup."""
    _, chunks = _bm25()
    by_id = {c["chunk_id"]: c for c in chunks}
    order: dict[str, list[str]] = {}
    for c in chunks:
        order.setdefault(c["source_id"], []).append(c["chunk_id"])
    return by_id, order


def _dedupe_key(c: dict) -> str:
    """Near-duplicates (the same QCO clause repeated in dozens of orders) share this key."""
    return re.sub(r"[^a-z]", "", c["text"].lower())[:220]


def cross_references(chunk: dict, query: str = "", limit: int = 2) -> list[dict]:
    """Law points to law: for 'Section 17' of the Act, the chunks of the same document that cite 'section 17'
    (e.g. Section 29(3): 'contravenes the provisions of section 17 shall be punishable ...')."""
    m = re.search(r"\b(Section|Regulation|Rule)\s+(\d+)", chunk.get("section") or "")
    if not m or chunk.get("doc_type") not in ("act", "rule", "regulation"):
        return []
    by_id, order = _store()
    ref = re.compile(rf"\b{m.group(1)}\s+{m.group(2)}\b(?!\s*\()", re.I)
    own = re.compile(rf"\b{m.group(1)}\s+{m.group(2)}\b", re.I)
    refs = [by_id[cid] for cid in order.get(chunk["source_id"], []) if cid != chunk["chunk_id"]
            and ref.search(by_id[cid]["text"]) and not own.search(by_id[cid].get("section") or "")]
    q = set(tokenize(query))  # the referring chunks most about the question first (title + text)
    return sorted(refs, key=lambda c: -len(q & set(tokenize(embed_text(c)))))[:limit]


def neighbours(chunk: dict) -> list[dict]:
    by_id, order = _store()
    ids = order.get(chunk["source_id"], [])
    try:
        i = ids.index(chunk["chunk_id"])
    except ValueError:
        return []
    return [by_id[ids[j]] for j in (i - 1, i + 1) if 0 <= j < len(ids)]


MIN_RERANK = 0.003  # below this for EVERY candidate, the search found nothing about the question (search_empty)


def question_parts(q: str) -> list[str]:
    """A multi-part question -> its parts, each searched on its own (deterministic; one long query mixes the
    topics and finds neither). 'What is X? Additionally, what is Y?' -> ['What is X?', 'what is Y?']"""
    parts = [re.sub(r"^(additionally|also|and|further(more)?|moreover)[,\s]+", "", p.strip(), flags=re.I)
             for p in re.split(r"(?<=[?.!])\s+", q)]
    parts = [p for p in parts if len(p.split()) >= 5]
    return parts if len(parts) >= 2 else []


def _passes(c: dict, filters: dict) -> bool:
    if filters.get("scheme") and c.get("scheme") not in (filters["scheme"], "general"):
        return False
    if filters.get("doc_type") and c.get("doc_type") != filters["doc_type"]:
        return False
    return not filters.get("source") or c["source_id"].startswith(filters["source"])


def retrieve(question: str, top_k: int = 12, candidates: int = 30, use_reranker: bool = True,
             extra_queries: list[str] | None = None, intent: str | None = None, filters: dict | None = None,
             with_neighbours: bool = True) -> dict:
    """question -> {"chunks": final context (top_k + neighbours), "trace": {...}}.

    normalize -> concept expansion (term graph) -> vector + BM25 for each query -> RRF -> exact product rows
    -> filters, scheme boost -> collapse duplicates -> rerank vote -> top_k -> neighbours.
    Deterministic: the same question always gives the same chunks (no LLM inside)."""
    from app import expand, tools

    t0 = time.time()
    filters = {k: v for k, v in (filters or {}).items() if v}
    q = expand.normalize(question)
    en = expand.to_english(q) if expand.detect_lang(q) == "hi" else ""
    rule_q = expand.normalize(en) if en else q          # rules are written for English
    extra = [expand.normalize(x) for x in (extra_queries or []) if x and x.strip()] + question_parts(rule_q)
    concepts = expand.concept_terms(" ".join([rule_q] + extra[:3]))
    queries = list(dict.fromkeys([q] + ([rule_q] if en else []) + extra[:3]
                                 + ([f"{rule_q} {' '.join(concepts)}"] if concepts else [])))[:7]
    scheme = expand.detect_scheme(rule_q)
    basic = intent == "basic" or expand.is_basic(rule_q)

    bm = [bm25_search(x, None, candidates) for x in queries]
    vec = vector_search_many(queries, candidates)
    fused = rrf(*bm, *vec)
    per_query = []
    for x, b, v in zip(queries, bm, vec):
        f = rrf(b, v)
        per_query.append({"query": x, "count": len(f), "top3": [[c["chunk_id"], round(c["score"], 4)] for c in f[:3]]})

    # exact product / IS-number rows from the scraped tables always come first
    has_is = bool(tools._norm_is(rule_q))
    product_question = intent in (None, "check_requirement", "quick_fact", "advice")
    rows = [r for r in tools.lookup_product(rule_q, limit=6)
            if has_is or r.get("full_match") or (product_question and r.get("match_words", 0) >= 2)]
    row_ids = {r["chunk_id"] for r in rows}
    by_id, _ = _store()
    fused_ids = {c["chunk_id"] for c in fused}
    for r in rows:
        if r["chunk_id"] not in fused_ids and r["chunk_id"] in by_id:
            fused.append({**by_id[r["chunk_id"]], "score": 0.0})

    if filters:
        fused = [c for c in fused if _passes(c, filters)]

    def adjusted(c: dict) -> float:
        score = c.get("score", 0.0)
        if basic and (c.get("agent") == "general" or c.get("doc_type") == "faq"
                      or (c["source_id"] == "bis_act_2016" and "Definitions" in (c.get("section") or ""))):
            score *= 1.6  # definition questions: About-BIS pages, the Act's definitions and FAQs first
        if c["chunk_id"] in row_ids:
            score += 0.05 if has_is else 0.01
        cs = c.get("scheme", "general")
        if scheme:
            if cs == scheme:
                score *= 1.4
            elif cs not in ("general",) and not c["source_id"].endswith(("_products_table", "_page")):
                score *= 0.25  # another scheme's procedure: almost never the right source
        return score

    ranked = sorted(fused, key=adjusted, reverse=True)
    seen, pool = set(), []
    for c in ranked:  # collapse near-duplicates, keep the best-ranked copy
        key = _dedupe_key(c)
        if key in seen:
            continue
        seen.add(key)
        pool.append({**c, "adj_score": round(adjusted(c), 5)})
        if len(pool) >= candidates:
            break

    rerank_ms, final = 0, pool
    if use_reranker and pool:
        from app import rerank

        try:
            texts = [embed_text(c) for c in pool]
            rs, dt = rerank.timed_scores(rule_q, texts)  # the reranker is English-only
            rerank_ms = int(dt * 1000)
            for c, r in zip(pool, rs):
                c["rerank"] = round(r, 4)
            # the reranker is one vote next to the retrieval ranking (it is not domain-trained)
            by_rerank = sorted(pool, key=lambda c: -c["rerank"])
            final = rrf(pool, by_rerank)
            for c in final:
                c["final_score"] = round(c.pop("score"), 5)
        except Exception as e:
            print(f"[retrieval] reranker skipped: {e}")
    # product-table rows must not crowd out the documents that explain the rules (max 4 unless an IS number was asked)
    top, n_rows = [], 0
    for c in final:
        is_row = "::row" in c["chunk_id"]
        if is_row and not has_is and n_rows >= 4:
            continue
        n_rows += is_row
        top.append(c)
        if len(top) == top_k:
            break

    # add the chunk before/after each of the top 5 so a rule is not cut in half
    # ranked hits first, neighbours after: the context budget keeps every hit before any neighbour
    have = {c["chunk_id"] for c in top}
    context = list(top)
    for i, c in enumerate(top):
        if with_neighbours and i < 5 and "::row" not in c["chunk_id"]:  # a table row's neighbours are unrelated products
            for nb in neighbours(c) + cross_references(c, rule_q):
                if nb["chunk_id"] not in have:
                    have.add(nb["chunk_id"])
                    context.append({**nb, "neighbour_of": c["chunk_id"]})
    max_rerank = max((c.get("rerank", 0.0) for c in pool), default=0.0)
    empty = not pool or (rerank_ms > 0 and max_rerank < MIN_RERANK)
    return {
        "question": q, "chunks": [] if empty else context,
        "trace": {"queries": queries, "translated": en, "scheme": scheme, "concept_terms": concepts,
                  "filters": {**filters, **({"scheme_boost": scheme} if scheme else {}), **({"basic": True} if basic else {}),
                              "product_rows": len(rows)},
                  "per_query": per_query, "max_rerank": round(max_rerank, 4), "search_empty": empty,
                  "vector": _vector_error if time.time() < _vector_paused_until else "ok",
                  "candidates": len(fused), "after_dedupe": len(pool), "rerank_ms": rerank_ms,
                  "ms": int((time.time() - t0) * 1000)},
    }


def reload():
    """Drop cached indexes so the next query loads the rebuilt ones (used after /admin/reindex)."""
    from app import tools

    if _qdrant.cache_info().currsize:
        try:
            _qdrant().close()
        except Exception:
            pass
    from app import expand
    for f in (_bm25, _qdrant, _store, tools.product_rows, expand._term_graph):
        f.cache_clear()
