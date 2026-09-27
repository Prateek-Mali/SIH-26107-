"""Read-only embedding map: Qdrant vectors (bge-m3) -> 2D (UMAP, t-SNE fallback) -> eval/embedding_map.html

    python scripts/embedding_map.py
    python -m http.server 8765 --bind 127.0.0.1 --directory eval   # then open http://localhost:8765/embedding_map.html

Serve it over localhost: the search box calls the local Ollama bge-m3, which refuses file:// pages.
"""
import base64
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
# ponytail: int8 vectors (1 byte/dim) keep the file small; cosine error is tiny for ranking a top 10
q8 = base64.b64encode(np.round(V * 127).astype(np.int8).tobytes()).decode()
_r = httpx.get(PLOTLY, timeout=60, follow_redirects=True)
_r.raise_for_status()
plotly_js = _r.text  # inlined: the HTML works offline except for the search box

html = f"""<!doctype html><html><head><meta charset="utf-8"><title>BIS embedding map</title>
<style>body{{font-family:system-ui,sans-serif;margin:16px}}#hits li{{margin:4px 0;font-size:13px}}
input{{width:420px;padding:6px}}button,select{{padding:6px}}</style>
<script>{plotly_js}</script></head><body>
<h3>BIS knowledge base: {len(points)} chunks, bge-m3 vectors → 2D ({method})</h3>
Colour by <select id="mode"><option value="g">source group</option><option value="s">scheme</option><option value="t">doc_type</option></select>
&nbsp; <input id="q" placeholder="Ask a question, e.g. penalty for using ISI mark without licence">
<button id="go">Search</button> <span id="msg"></span>
<div id="plot" style="height:760px"></div><ol id="hits"></ol>
<script>
const XY={json.dumps(np.round(xy, 3).tolist())}, M={json.dumps(meta, ensure_ascii=False)};
const DIM={V.shape[1]}, Q8=Uint8Array.from(atob("{q8}"), c => c.charCodeAt(0));
const VEC=new Int8Array(Q8.buffer);
let star=null;
function draw(){{
  const mode=document.getElementById('mode').value, cats=[...new Set(M.map(m=>m[mode]))].sort();
  const traces=cats.map(c=>{{const i=M.map((m,k)=>m[mode]===c?k:-1).filter(k=>k>=0);
    return {{type:'scattergl',mode:'markers',name:c+' ('+i.length+')',x:i.map(k=>XY[k][0]),y:i.map(k=>XY[k][1]),
      text:i.map(k=>M[k].h),hoverinfo:'text',marker:{{size:5,opacity:0.7}}}};}});
  if(star){{traces.push(star.hits,star.q);}}
  Plotly.react('plot',traces,{{hovermode:'closest',legend:{{orientation:'h'}},margin:{{t:10}}}});
}}
async function search(){{
  const q=document.getElementById('q').value.trim(), msg=document.getElementById('msg');
  if(!q){{msg.textContent='Type a question first';return;}}
  msg.textContent='embedding with local bge-m3…';
  try{{
    const r=await fetch('{config.OLLAMA_URL}/api/embed',{{method:'POST',body:JSON.stringify({{model:'{config.OLLAMA_EMBED_MODEL}',input:[q]}})}});
    let v=(await r.json()).embeddings[0]; const n=Math.hypot(...v); v=v.map(x=>x/n);
    const s=new Float32Array(M.length);
    for(let k=0;k<M.length;k++){{let d=0;const o=k*DIM;for(let j=0;j<DIM;j++)d+=v[j]*VEC[o+j];s[k]=d/127;}}
    const top=[...s.keys()].sort((a,b)=>s[b]-s[a]).slice(0,10);
    // ponytail: the question has no UMAP coordinates; place its star at the score-weighted mean of its top 10
    const w=top.map(k=>s[k]), W=w.reduce((a,b)=>a+b);
    const qx=top.reduce((a,k,i)=>a+XY[k][0]*w[i],0)/W, qy=top.reduce((a,k,i)=>a+XY[k][1]*w[i],0)/W;
    star={{hits:{{type:'scattergl',mode:'markers',name:'top 10',x:top.map(k=>XY[k][0]),y:top.map(k=>XY[k][1]),
            text:top.map(k=>M[k].h),hoverinfo:'text',marker:{{size:14,color:'rgba(0,0,0,0)',line:{{color:'black',width:2}}}}}},
          q:{{type:'scattergl',mode:'markers',name:'question',x:[qx],y:[qy],text:[q],hoverinfo:'text',
            marker:{{size:22,symbol:'star',color:'gold',line:{{color:'black',width:1}}}}}}}};
    document.getElementById('hits').innerHTML=top.map(k=>'<li>'+s[k].toFixed(3)+' — <code>'+M[k].id+'</code> '+M[k].h.split('<br>')[0]+'</li>').join('');
    msg.textContent='top 10 by vector similarity (vector search only, not the full hybrid pipeline)'; draw();
  }}catch(e){{msg.textContent='search needs Ollama with bge-m3 and this page served from localhost: '+e;}}
}}
document.getElementById('mode').onchange=draw; document.getElementById('go').onclick=search;
document.getElementById('q').onkeydown=e=>{{if(e.key==='Enter')search();}};
draw();
</script></body></html>"""
out = ROOT / "eval" / "embedding_map.html"
out.write_text(html, encoding="utf-8")
print(f"{method} map of {len(points)} chunks -> {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB)")

# check: every point got 2D coordinates and a group
assert len(xy) == len(meta) == len(points) and all(m["g"] for m in meta)
