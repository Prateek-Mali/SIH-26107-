"""Show what the retriever gives the LLM for a question.

    python scripts/debug_search.py "What documents are needed for an ISI licence?"
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("BIS_QUIET", "1")

from app.retrieval import retrieve  # noqa: E402

q = " ".join(sys.argv[1:]) or "What documents are required for grant of licence?"
r = retrieve(q)
t = r["trace"]
print(f"question : {r['question']}")
print(f"queries  : {t['queries']}")
print(f"scheme   : {t['scheme']}   boosts: {t['boosts']}")
print(f"vector   : {t['vector']}   candidates: {t['candidates']} -> {t['after_dedupe']} after dedupe")
print(f"timing   : retrieval {t['ms']} ms (reranker {t['rerank_ms']} ms)\n")
for n, c in enumerate(r["chunks"], 1):
    tag = f"  (neighbour of {c['neighbour_of']})" if c.get("neighbour_of") else ""
    print(f"[{n:2}] {c['chunk_id']}  scheme={c.get('scheme')}  page={c.get('page')}  "
          f"rerank={c.get('rerank', '-')}  final={c.get('final_score', c.get('adj_score', '-'))}{tag}")
    print(f"     {c['title'][:80]} > {c.get('section', '')[:80]}")
    print(f"     {' '.join(c['text'].split())[:220]}\n")
