"""Read-only export of the knowledge base as an Obsidian vault: kb_graph/

    python scripts/export_obsidian.py

One note per document (docs/), one per chunk (chunks/) linked to its document and to its 3 most similar
chunks from OTHER documents (cosine of the stored bge-m3 vectors >= 0.75). QCO PDFs and product-table rows
are summarised in one hub note ("QCO products") instead of thousands of notes.
"""
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

from app import config  # noqa: E402
from app.retrieval import _qdrant  # noqa: E402  (snapshot copy if the chat holds the index)

VAULT = ROOT / "kb_graph"
MIN_SIM, TOP = 0.75, 3
COLOURS = {"law": 0xE24B4A, "certification": 0x378ADD, "hallmarking": 0xEF9F27, "consumer": 0x639922, "qco": 0x888780}


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


def note(cid: str) -> str:
    return cid.replace("::", "__")  # ':' is not allowed in Obsidian note names


def scheme_tag(s: str) -> str:
    return {"I": "#scheme-I", "II": "#scheme-II", "FMCS": "#fmcs"}.get(s or "", "")


# all chunks (metadata) + vectors of the ones we export
chunks = [json.loads(l) for l in config.CHUNKS_PATH.open(encoding="utf-8")]
keep = lambda c: category(c["source_id"], c["doc_type"]) != "qco"
vec = {}
offset = None
while True:
    batch, offset = _qdrant().scroll(config.COLLECTION, limit=512, offset=offset, with_vectors=True, with_payload=["chunk_id"])
    vec.update({p.payload["chunk_id"]: p.vector for p in batch})
    if offset is None:
        break
exp = [c for c in chunks if keep(c)]
with_vec = [c for c in exp if c["chunk_id"] in vec]
V = np.array([vec[c["chunk_id"]] for c in with_vec], dtype=np.float32)
V /= np.linalg.norm(V, axis=1, keepdims=True)
S = V @ V.T
src = np.array([c["source_id"] for c in with_vec])
S[src[:, None] == src[None, :]] = -1  # only links to OTHER documents
similar = {}
for i, c in enumerate(with_vec):
    top = np.argsort(-S[i])[:TOP]
    similar[c["chunk_id"]] = [(with_vec[j]["chunk_id"], float(S[i, j])) for j in top if S[i, j] >= MIN_SIM]

if VAULT.exists():
    shutil.rmtree(VAULT)  # the vault is generated: rebuild it from scratch every time
(VAULT / "docs").mkdir(parents=True)
(VAULT / "chunks").mkdir()
(VAULT / ".obsidian").mkdir()

by_src = defaultdict(list)
for c in chunks:
    by_src[c["source_id"]].append(c)

# document notes
for sid, cs in by_src.items():
    c0 = cs[0]
    cat = category(sid, c0["doc_type"])
    if cat == "qco":
        continue
    tags = " ".join(t for t in (f"#{cat}", scheme_tag(c0.get("scheme"))) if t)
    fm = {"title": c0["title"], "url": c0["url"], "scheme": c0.get("scheme"), "doc_type": c0["doc_type"],
          "date": c0.get("doc_date") or c0.get("date_downloaded"), "chunk_count": len(cs)}
    (VAULT / "docs" / f"{sid}.md").write_text(
        "---\n" + "".join(f"{k}: {json.dumps(v, ensure_ascii=False)}\n" for k, v in fm.items()) + "---\n"
        f"# {c0['title']}\n\n{tags}\n\n[Official document]({c0['url']}) · {len(cs)} chunks\n", encoding="utf-8")

# chunk notes
n_links = 0
for c in exp:
    cat = category(c["source_id"], c["doc_type"])
    tags = " ".join(t for t in (f"#{cat}", scheme_tag(c.get("scheme"))) if t)
    sims = similar.get(c["chunk_id"], [])
    n_links += len(sims)
    text = " ".join(c["text"].split())[:400]
    body = (f"# {c['title']}\n\n{tags}\n\n**Section:** {c.get('section') or '-'} · **Page:** {c.get('page') or '-'}\n\n"
            f"> {text}\n\nDocument: [[{c['source_id']}]]\n")
    if sims:
        body += "\nSimilar (other documents):\n" + "".join(f"- [[{note(o)}]] ({s:.2f})\n" for o, s in sims)
    (VAULT / "chunks" / f"{note(c['chunk_id'])}.md").write_text(body, encoding="utf-8")

# one hub for all QCO PDFs and product rows
rows = [c for c in chunks if "::row" in c["chunk_id"]]
qco_titles = Counter(c["title"] for c in chunks if c["source_id"].startswith("qco_"))
cats = Counter((c["source_id"], c.get("section", "").split(":")[0]) for c in rows)
hub = ["# QCO products", "", "#qco", "",
       f"{len(rows)} product rows from the BIS product tables and {len(qco_titles)} QCO / notification PDFs "
       "(not exported as notes, to keep the graph readable).", "", "## Product tables", ""]
for sid in sorted({c["source_id"] for c in rows}):
    n = sum(1 for c in rows if c["source_id"] == sid)
    hub.append(f"- {sid}: {n} products" + (f" → [[{sid}]]" if (VAULT / 'docs' / f'{sid}.md').exists() else ""))
hub += ["", "## QCO / notification PDFs", ""] + [f"- {t}" for t in sorted(qco_titles)]
(VAULT / "QCO products.md").write_text("\n".join(hub) + "\n", encoding="utf-8")

(VAULT / ".obsidian" / "graph.json").write_text(json.dumps({
    "colorGroups": [{"query": f"tag:#{k}", "color": {"a": 1, "rgb": v}} for k, v in COLOURS.items()],
    "showTags": False, "showAttachments": False, "hideUnresolved": True}, indent=1), encoding="utf-8")

n_notes = sum(1 for _ in VAULT.rglob("*.md"))
print(f"{n_notes} notes ({len(list((VAULT / 'docs').glob('*.md')))} documents, {len(exp)} chunks, 1 hub), "
      f"{n_links} similarity links (>= {MIN_SIM}), {len(exp) - len(with_vec)} chunks without vectors -> {VAULT.relative_to(ROOT)}/")
assert n_notes < 1500, "graph too big for readability"
