"""Read-only embedding map: Qdrant vectors (bge-m3) -> 2D (UMAP, t-SNE fallback) -> eval/embedding_map.html

    python scripts/embedding_map.py
    open eval/embedding_map.html   # works offline
"""
import json
import os
import sys
from pathlib import Path

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

from app import config  # noqa: E402
from app.retrieval import _qdrant  # noqa: E402  (opens a snapshot copy if the chat holds the index)

PLOTLY = "https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"


def group(p: dict) -> str:
    s, t = p["source_id"], p.get("doc_type", "")
    if "::row" in p["chunk_id"]:
        return "product rows"
    if s.startswith("qco_"):
        return "QCO PDFs"
    if t == "faq":
        return "FAQs"
    if p.get("scheme") == "Hallmarking" or s.startswith(("hm_", "consumer_", "bis_care")):
        return "hallmarking / consumer"
    if t in ("act", "rule", "regulation") or s.startswith(("bis_act", "bis_rules", "ca_", "law_")):
        return "law"
    if s.startswith(("guide_", "application_checklist", "simplified")):
        return "certification guides"
    return "other pages"


points, offset = [], None
while True:
    batch, offset = _qdrant().scroll(config.COLLECTION, limit=512, offset=offset, with_vectors=True, with_payload=True)
    points += batch
    if offset is None:
        break
V = np.array([p.vector for p in points], dtype=np.float32)
V /= np.linalg.norm(V, axis=1, keepdims=True)
print(f"{len(points)} vectors of {V.shape[1]} dims")

try:
    import umap
    xy = umap.UMAP(n_neighbors=15, min_dist=0.1, metric="cosine", random_state=42).fit_transform(V)
    method = "UMAP"
except ImportError:
    from sklearn.manifold import TSNE
    xy = TSNE(n_components=2, metric="cosine", init="pca", random_state=42).fit_transform(V)
    method = "t-SNE"

meta = []
for p in points:
    d = p.payload
    meta.append({"id": d["chunk_id"], "g": group(d), "s": d.get("scheme") or "general", "t": d.get("doc_type", ""),
                 "h": (f"<b>{d['title'][:80]}</b><br>{(d.get('section') or '')[:80]}<br>p.{d.get('page') or '-'} · "
                       f"scheme {d.get('scheme')} · {d.get('doc_type')}<br><i>{' '.join(d['text'].split())[:200]}</i>")})
_r = httpx.get(PLOTLY, timeout=60, follow_redirects=True)
_r.raise_for_status()
plotly_js = _r.text  # inlined: the HTML works offline

html = f"""<!doctype html><html><head><meta charset="utf-8"><title>BIS embedding map</title>
<style>body{{font-family:system-ui,sans-serif;margin:16px}}#hits li{{margin:4px 0;font-size:13px}}
select{{padding:6px}}</style>
<script>{plotly_js}</script></head><body>
<h3>BIS knowledge base: {len(points)} chunks, bge-m3 vectors → 2D ({method})</h3>
Colour by <select id="mode"><option value="g">source group</option><option value="s">scheme</option><option value="t">doc_type</option></select>
<div id="plot" style="height:760px"></div>
<script>
const XY={json.dumps(np.round(xy, 3).tolist())}, M={json.dumps(meta, ensure_ascii=False)};
function draw(){{
  const mode=document.getElementById('mode').value, cats=[...new Set(M.map(m=>m[mode]))].sort();
  const traces=cats.map(c=>{{const i=M.map((m,k)=>m[mode]===c?k:-1).filter(k=>k>=0);
    return {{type:'scattergl',mode:'markers',name:c+' ('+i.length+')',x:i.map(k=>XY[k][0]),y:i.map(k=>XY[k][1]),
      text:i.map(k=>M[k].h),hoverinfo:'text',marker:{{size:5,opacity:0.7}}}};}});
  Plotly.react('plot',traces,{{hovermode:'closest',legend:{{orientation:'h'}},margin:{{t:10}}}});
}}
document.getElementById('mode').onchange=draw;
draw();
</script></body></html>"""
out = ROOT / "eval" / "embedding_map.html"
out.write_text(html, encoding="utf-8")
print(f"{method} map of {len(points)} chunks -> {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB)")

# check: every point got 2D coordinates and a group
assert len(xy) == len(meta) == len(points) and all(m["g"] for m in meta)
