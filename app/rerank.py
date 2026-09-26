"""Local cross-encoder (ONNX, CPU): relevance scores for (query, passage) pairs.

Model: RERANK_MODEL (default Xenova/ms-marco-MiniLM-L-12-v2, ~120 MB, fast on an Intel CPU).
Used (1) as one vote when ranking retrieved chunks and (2) to check that a cited sentence is
supported by its chunk. Scores are probabilities in [0, 1] (sigmoid of the model's logit).
"""
import math
import os
import threading
import time
from functools import lru_cache

MODEL = os.getenv("RERANK_MODEL", "Xenova/ms-marco-MiniLM-L-12-v2")
MAX_CHARS = 1200
_lock = threading.Lock()


@lru_cache(maxsize=1)
def _model():
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    return TextCrossEncoder(MODEL)


def available() -> bool:
    try:
        _model()
        return True
    except Exception as e:  # model download failed / onnxruntime missing: ranking still works without it
        print(f"[rerank] cross-encoder unavailable: {e}")
        return False


def scores(query: str, passages: list[str]) -> list[float]:
    if not passages:
        return []
    with _lock:  # onnxruntime session is not re-entrant across our threads
        raw = list(_model().rerank(query, [p[:MAX_CHARS] for p in passages], batch_size=16))
    return [1 / (1 + math.exp(-float(x))) for x in raw]


def pair_scores(pairs: list[tuple[str, str]]) -> list[float]:
    """Score (sentence, passage) pairs that have different queries."""
    out = []
    for q, p in pairs:
        out += scores(q, [p])
    return out


def timed_scores(query: str, passages: list[str]) -> tuple[list[float], float]:
    t0 = time.time()
    s = scores(query, passages)
    return s, time.time() - t0
