"""Build the Qdrant vector index and the BM25 keyword index from chunks.jsonl.

Usage:
    python scripts/build_index.py              # embeddings (Gemini) + BM25
    python scripts/build_index.py --bm25-only  # no API key needed

Embeddings are cached in index/embed_cache.jsonl (keyed by text hash + model), so a refresh
only embeds new or changed chunks.
"""
import argparse
import hashlib
import json
import os
import pickle
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

from rank_bm25 import BM25Okapi  # noqa: E402

from app import config  # noqa: E402
from app.retrieval import embed_text, tokenize  # noqa: E402

CACHE = ROOT / "index" / "embed_cache.jsonl"
BATCH = 20  # small batches stay under the free tier's tokens-per-minute limit


def load_chunks() -> list[dict]:
    return [json.loads(l) for l in config.CHUNKS_PATH.open(encoding="utf-8")]


def build_bm25(chunks: list[dict]):
    corpus = [tokenize(embed_text(c)) for c in chunks]
    bm25 = BM25Okapi(corpus)
    config.BM25_PATH.parent.mkdir(parents=True, exist_ok=True)
    with config.BM25_PATH.open("wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)
    print(f"BM25: {len(chunks)} chunks -> {config.BM25_PATH.relative_to(ROOT)}")


def embed_with_wait(texts: list[str], tries: int = 10) -> list[list[float]]:
    """On a quota error wait for the per-minute window to reset, then retry the same batch."""
    import httpx

    from app.llm import AllModelsBusy, embed

    for attempt in range(tries):
        try:
            return embed(texts, task="RETRIEVAL_DOCUMENT")
        except httpx.HTTPError as e:  # local Ollama restarting or overloaded
            if attempt == tries - 1:
                raise
            print(f"  embedding server error ({type(e).__name__}); retrying in 15 s")
            time.sleep(15)
            continue
        except AllModelsBusy:
            if attempt == tries - 1 or "PerDay" in str(sys.exc_info()[1]):
                raise
            print("  rate limited: waiting 65 s")
            time.sleep(65)


def embed_all(chunks: list[dict], cached_only: bool = False, core_only: bool = False) -> list[list[float] | None]:
    from app.llm import embed_model_id

    cache = {}
    if CACHE.exists():
        for line in CACHE.open(encoding="utf-8"):
            row = json.loads(line)
            cache[row["key"]] = row["vector"]
    keys = [hashlib.sha256(f"{embed_model_id()}:{embed_text(c)}".encode()).hexdigest()
            for c in chunks]
    todo = [] if cached_only else [i for i, k in enumerate(keys) if k not in cache
                                   and not (core_only and chunks[i]["source_id"].startswith("qco_"))]
    # Most useful first: core documents and product rows, then the bulk of individual QCO PDFs.
    todo.sort(key=lambda i: chunks[i]["source_id"].startswith("qco_"))
    print(f"Embeddings: {len(chunks) - len(todo)} cached, {len(todo)} to embed with {embed_model_id()}")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("a", encoding="utf-8") as out:
        size = 8 if config.EMBED_PROVIDER == "ollama" else BATCH  # small batches keep local Ollama stable
        for start in range(0, len(todo), size):
            batch = todo[start:start + size]
            try:
                vectors = embed_with_wait([embed_text(chunks[i]) for i in batch])
            except Exception as e:
                if "PerDay" not in str(e):
                    raise
                left = len(todo) - start
                print(f"  Daily embedding quota reached: {left} chunks left without vectors (BM25 still covers "
                      f"them). Run build_index.py again tomorrow; cached vectors are reused.")
                break
            for i, v in zip(batch, vectors):
                cache[keys[i]] = v
                out.write(json.dumps({"key": keys[i], "vector": v}) + "\n")
            out.flush()
            print(f"  embedded {min(start + size, len(todo))}/{len(todo)}")
            if config.EMBED_PROVIDER != "ollama":
                time.sleep(1)  # stay under free-tier rate limits
    return [cache.get(k) for k in keys]


def build_qdrant(chunks: list[dict], vectors: list[list[float] | None]):
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    points = [PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])), vector=v, payload=c)
              for c, v in zip(chunks, vectors) if v is not None]
    if not points:
        print("Qdrant: no embeddings yet; keeping the previous vector index")
        return
    # Build into a fresh folder, then swap it in: a running API/chat keeps its (old) index open
    # without blocking the build, and picks up the new one on restart.
    import shutil

    final, tmp = Path(config.QDRANT_PATH), Path(config.QDRANT_PATH + ".new")
    shutil.rmtree(tmp, ignore_errors=True)
    client = QdrantClient(path=str(tmp))
    client.create_collection(config.COLLECTION,
                             vectors_config=VectorParams(size=len(points[0].vector), distance=Distance.COSINE))
    for start in range(0, len(points), 256):
        client.upsert(config.COLLECTION, points=points[start:start + 256])
    print(f"Qdrant: {client.count(config.COLLECTION).count} of {len(chunks)} chunks have vectors in '{config.COLLECTION}'")
    client.close()
    old = Path(config.QDRANT_PATH + ".old")
    shutil.rmtree(old, ignore_errors=True)
    if final.exists():
        final.rename(old)
    tmp.rename(final)
    shutil.rmtree(old, ignore_errors=True)
    print("Qdrant: new index swapped in (restart the API/chat to use it)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bm25-only", action="store_true")
    ap.add_argument("--cached-only", action="store_true",
                    help="build the vector index from already-cached embeddings only (no new embedding)")
    ap.add_argument("--core-only", action="store_true",
                    help="embed only non-QCO-PDF chunks now (the bulk QCO PDFs can be embedded later)")
    args = ap.parse_args()
    chunks = load_chunks()
    build_bm25(chunks)
    if args.bm25_only:
        return
    if config.EMBED_PROVIDER == "gemini" and not config.KEY_IS_SET:
        sys.exit("GEMINI_API_KEY is not set in .env: cannot build Gemini embeddings (set EMBED_PROVIDER=ollama "
                 "or use --bm25-only).")
    build_qdrant(chunks, embed_all(chunks, cached_only=args.cached_only, core_only=args.core_only))


if __name__ == "__main__":
    main()
