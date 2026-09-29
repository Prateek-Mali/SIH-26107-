"""Domain vocabulary: related terms by co-occurrence in the documents (built once, not per question).

    python scripts/build_term_graph.py      # -> data/structured/term_graph.json, prints 10 random entries

Score = mean of (a) first-order co-occurrence: normalised PMI of two terms in the same 25-word window, and
(b) second-order co-occurrence: cosine of the terms' co-occurrence (PPMI) vectors, i.e. used in the same contexts.
E.g. objection -> remove, removal, thirty, opportunity, extend, rejecting. Only the rules/guidelines/FAQ text is
used: product-table rows and the QCO PDFs (hundreds of near-identical Gazette orders) are skipped.
"""
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import config  # noqa: E402
from app.retrieval import STOPWORDS  # noqa: E402

OUT = config.DATA / "structured" / "term_graph.json"
WINDOW = 25          # words
MIN_DF, MAX_DF = 3, 0.08   # a term must appear in >= 3 windows and in <= 8% of them (drops "bis", "shall"...)
TOP, MIN_SCORE = 8, 0.15
EXTRA_STOP = set("""also such other than said into which where there their these those been being were upon
without within after before under above below between shall made make every each only more most very
provided further thereof therein hereby herein thereto clause section rule page date dated order orders
number item items part parts sub including include includes following given like same""".split())


def stem(w: str) -> str:
    """objections -> objection, deficiencies -> deficiency (plural -> singular, nothing fancier)."""
    if len(w) > 5 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 5 and w.endswith(("xes", "ches", "shes", "sses")):
        return w[:-2]
    if len(w) > 4 and w.endswith("s") and not w.endswith(("ss", "us", "is", "as")):
        return w[:-1]
    return w


def windows() -> list[list[str]]:
    seen, out = set(), []
    for line in config.CHUNKS_PATH.open(encoding="utf-8"):
        c = json.loads(line)
        if "::row" in c["chunk_id"] or c.get("lang") == "hi" or c["source_id"].startswith("qco_"):
            continue
        key = re.sub(r"[^a-z]", "", c["text"].lower())[:220]
        if key in seen:
            continue
        seen.add(key)
        words = [stem(w) for w in re.findall(r"[a-z]{4,}", c["text"].lower())
                 if w not in STOPWORDS and w not in EXTRA_STOP]
        out += [words[i:i + WINDOW] for i in range(0, max(len(words), 1), WINDOW)]
    return [w for w in out if len(w) >= 10]


def build():
    import numpy as np

    wins = [set(w) for w in windows()]
    n = len(wins)
    df = Counter(t for w in wins for t in w)
    vocab = sorted(t for t, d in df.items() if MIN_DF <= d <= MAX_DF * n)
    idx = {t: i for i, t in enumerate(vocab)}
    co = np.zeros((len(vocab), len(vocab)), dtype=np.float32)
    for w in wins:
        ids = [idx[t] for t in w if t in idx]
        co[np.ix_(ids, ids)] += 1
    np.fill_diagonal(co, 0)
    d = np.array([df[t] for t in vocab], dtype=np.float32)
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.nan_to_num(np.log(co * n / np.outer(d, d)), neginf=0)
        npmi = np.nan_to_num(pmi / -np.log(np.maximum(co, 1) / n), neginf=0)
    npmi[co < 3] = 0  # fewer than 3 shared windows is noise
    ppmi = np.maximum(pmi, 0)
    ppmi[co < 2] = 0
    ppmi /= np.linalg.norm(ppmi, axis=1, keepdims=True) + 1e-9
    sim = ppmi @ ppmi.T
    np.fill_diagonal(sim, 0)
    score = 0.5 * sim + 0.5 * np.clip(npmi, 0, 1)
    graph = {}
    for i, t in enumerate(vocab):
        top = np.argsort(-score[i])[:TOP]
        rel = [[vocab[j], round(float(score[i, j]), 3)] for j in top if score[i, j] >= MIN_SCORE]
        if rel:
            graph[t] = rel
    return graph, n, len(vocab)


def main():
    graph, n, v = build()
    OUT.write_text(json.dumps(graph, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(graph)} terms (vocabulary {v}, {n} windows) -> {OUT.relative_to(ROOT)}")
    rng = random.Random()
    for t in rng.sample(sorted(graph), 10):
        print(f"  {t}: {', '.join(b for b, _ in graph[t])}")
    for t in ("objection", "deficiency", "discrepancy"):
        if t in graph:
            print(f"  [{t}]: {', '.join(f'{b} ({s})' for b, s in graph[t])}")


if __name__ == "__main__":
    main()
