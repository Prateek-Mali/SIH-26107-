"""Read-only interactive graph of the knowledge base (pyvis): eval/knowledge_graph.html

    python scripts/knowledge_graph.py

Big dots = documents, small dots = chunks (linked to their document), extra lines between chunks of
different documents whose stored bge-m3 vectors have cosine >= 0.80. QCO PDFs and product rows = one grey dot.
"""
import html
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from pyvis.network import Network

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

from app import config  # noqa: E402
from app.retrieval import _qdrant  # noqa: E402  (snapshot copy if the chat holds the index)

MIN_SIM = 0.80
COLOUR = {"law": "#E24B4A", "certification": "#378ADD", "hallmarking": "#EF9F27", "consumer": "#639922", "qco": "#888780"}


def category(sid: str, doc_type: str) -> str:
    if sid.startswith(("qco_", "scheme", "upcoming_qcos", "product_specific", "pib_qco")):
        return "qco"
    if sid.startswith("hm_"):
        return "hallmarking"
    if sid.startswith(("consumer_", "bis_care")):
        return "consumer"
    if doc_type in ("act", "rule", "regulation") or sid.startswith(("bis_act", "bis_rules", "ca_", "law_", "advisory", "dg_")):
        return "law"
    return "certification"


chunks = [json.loads(l) for l in config.CHUNKS_PATH.open(encoding="utf-8")]
vec, offset = {}, None
while True:
    batch, offset = _qdrant().scroll(config.COLLECTION, limit=512, offset=offset, with_vectors=True, with_payload=["chunk_id"])
    vec.update({p.payload["chunk_id"]: p.vector for p in batch})
    if offset is None:
        break

keep = [c for c in chunks if category(c["source_id"], c["doc_type"]) != "qco" and c["chunk_id"] in vec]
by_src = defaultdict(list)
for c in keep:
    by_src[c["source_id"]].append(c)

net = Network(height="95vh", width="100%", bgcolor="#111111", font_color="#e8e8e8", cdn_resources="in_line")
net.barnes_hut(gravity=-6000, central_gravity=0.2, spring_length=90, spring_strength=0.02)

for sid, cs in by_src.items():
    cat = category(sid, cs[0]["doc_type"])
    net.add_node(sid, label=cs[0]["title"][:45], title=f"{cs[0]['title']}\n{len(cs)} chunks · {cat}",
                 color=COLOUR[cat], size=18 + min(len(cs), 150) ** 0.5 * 2, shape="dot", font={"size": 16})
n_qco = sum(1 for c in chunks if category(c["source_id"], c["doc_type"]) == "qco")
net.add_node("QCO products", label="QCO products", color=COLOUR["qco"], size=30, shape="dot",
             title=f"{n_qco} QCO-PDF chunks and product-table rows (not drawn)", font={"size": 16})

for c in keep:
    cat = category(c["source_id"], c["doc_type"])
    tip = f"{c['title']}\n{c.get('section') or ''} · p.{c.get('page') or '-'}\n\n{' '.join(c['text'].split())[:300]}"
    net.add_node(c["chunk_id"], label=" ", title=html.escape(tip), color=COLOUR[cat], size=4, shape="dot")
    net.add_edge(c["chunk_id"], c["source_id"], color="#444444", width=0.5)

V = np.array([vec[c["chunk_id"]] for c in keep], dtype=np.float32)
V /= np.linalg.norm(V, axis=1, keepdims=True)
S = np.triu(V @ V.T, k=1)
src = np.array([c["source_id"] for c in keep])
n_sim = 0
for i, j in zip(*np.where(S >= MIN_SIM)):
    if src[i] != src[j]:
        net.add_edge(keep[i]["chunk_id"], keep[j]["chunk_id"], color="#bbbbbb", width=0.4)
        n_sim += 1

out = ROOT / "eval" / "knowledge_graph.html"
net.write_html(str(out), notebook=False)
print(f"{len(by_src)} documents + 1 QCO hub, {len(keep)} chunks, {n_sim} similarity lines (>= {MIN_SIM}) "
      f"-> {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB)")
assert len(by_src) and len(keep) == sum(len(v) for v in by_src.values())
