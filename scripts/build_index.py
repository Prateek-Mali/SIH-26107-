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
BATCH = 100


def load_chunks() -> list[dict]:
    return [json.loads(l) for l in config.CHUNKS_PATH.open(encoding="utf-8")]


def build_bm25(chunks: list[dict]):
    corpus = [tokenize(embed_text(c)) for c in chunks]
    bm25 = BM25Okapi(corpus)
    config.BM25_PATH.parent.mkdir(parents=True, exist_ok=True)
    with config.BM25_PATH.open("wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)
    print(f"BM25: {len(chunks)} chunks -> {config.BM25_PATH.relative_to(ROOT)}")


def embed_all(chunks: list[dict]) -> list[list[float]]:
    from app.llm import EMBED_DIM, embed

    cache = {}
    if CACHE.exists():
        for line in CACHE.open(encoding="utf-8"):
            row = json.loads(line)
            cache[row["key"]] = row["vector"]
    keys = [hashlib.sha256(f"{config.GEMINI_EMBED_MODEL}:{EMBED_DIM}:{embed_text(c)}".encode()).hexdigest()
            for c in chunks]
    todo = [i for i, k in enumerate(keys) if k not in cache]
    print(f"Embeddings: {len(chunks) - len(todo)} cached, {len(todo)} to embed with {config.GEMINI_EMBED_MODEL}")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("a", encoding="utf-8") as out:
        for start in range(0, len(todo), BATCH):
            batch = todo[start:start + BATCH]
            vectors = embed([embed_text(chunks[i]) for i in batch], task="RETRIEVAL_DOCUMENT")
            for i, v in zip(batch, vectors):
                cache[keys[i]] = v
                out.write(json.dumps({"key": keys[i], "vector": v}) + "\n")
            out.flush()
            print(f"  embedded {min(start + BATCH, len(todo))}/{len(todo)}")
            time.sleep(1)  # stay under free-tier rate limits
    return [cache[k] for k in keys]


def build_qdrant(chunks: list[dict], vectors: list[list[float]]):
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    client = QdrantClient(path=config.QDRANT_PATH)
    if client.collection_exists(config.COLLECTION):
        client.delete_collection(config.COLLECTION)
    client.create_collection(config.COLLECTION,
                             vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE))
    points = [PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])), vector=v, payload=c)
              for c, v in zip(chunks, vectors)]
    for start in range(0, len(points), 256):
        client.upsert(config.COLLECTION, points=points[start:start + 256])
    print(f"Qdrant: {client.count(config.COLLECTION).count} points in '{config.COLLECTION}' at {config.QDRANT_PATH}")
    client.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bm25-only", action="store_true")
    args = ap.parse_args()
    chunks = load_chunks()
    build_bm25(chunks)
    if args.bm25_only:
        return
    if not config.KEY_IS_SET:
        sys.exit("GEMINI_API_KEY is not set in .env: cannot build embeddings (use --bm25-only).")
    build_qdrant(chunks, embed_all(chunks))


if __name__ == "__main__":
    main()
