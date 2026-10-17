"""Read-only chunk inspector: data/processed/chunks.jsonl (+ parsed.jsonl) -> eval/chunk_report.md

    python scripts/chunk_report.py
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import chunk as C  # noqa: E402  (settings are read from the chunker itself, so the report cannot drift)

chunks = [json.loads(l) for l in (ROOT / "data/processed/chunks.jsonl").open(encoding="utf-8")]
parsed = [json.loads(l) for l in (ROOT / "data/processed/parsed.jsonl").open(encoding="utf-8")]
by_src = defaultdict(list)
for c in chunks:
    by_src[c["source_id"]].append(c)
sizes = [len(c["text"]) for c in chunks]


def table(counter: Counter, head: str) -> list[str]:
    return [f"| {head} | chunks |", "|---|---|"] + [f"| {k or '(none)'} | {v} |" for k, v in counter.most_common()]


def one_line(t: str, n: int) -> str:
    return " ".join(t.split())[:n].replace("|", "/")


rows = [c for c in chunks if "::row" in c["chunk_id"]]
qco = [c for c in chunks if c["source_id"].startswith("qco_")]
main_docs = sorted((s for s in by_src if not s.startswith("qco_") and "::row" not in by_src[s][0]["chunk_id"]),
                   key=lambda s: -len(by_src[s]))
L = ["# Chunk report", "",
     f"**{len(chunks)} chunks** from {len(by_src)} sources: {len(rows)} product-table rows, "
     f"{len(qco)} from {len({c['source_id'] for c in qco})} QCO PDFs, "
     f"{len(chunks) - len(rows) - len(qco)} from {len(main_docs)} other documents.", "",
     "## Chunk settings actually used (scripts/chunk.py)", "",
     f"- Split first on structure: top containers (`TOP`: Schedule / Chapter / Annex / Form), `Scheme-I…X` headings, "
     f"numbered items with a real title (`17. Prohibition…`), markdown headings and FAQ questions. "
     f"Acts are also split at every sub-section `(1)`, `(2)`… (`Section 29(3)` is its own chunk).",
     f"- Then cap each chunk at **{C.MAX_TOKENS} tokens** with **{C.OVERLAP_TOKENS} tokens overlap** "
     f"(tiktoken cl100k); pieces under **{C.MIN_TOKENS} tokens** (25 for Acts) are merged into the next one.",
     "- Fragments with fewer than 40 letters are dropped; every product-table row is one chunk.", "",
     "## Size (characters)", "",
     f"min {min(sizes)} · avg {sum(sizes) // len(sizes)} · median {sorted(sizes)[len(sizes) // 2]} · max {max(sizes)}", ""]
small = [c for c in chunks if len(c["text"]) < 100]
big = [c for c in chunks if len(c["text"]) > 3000]
L += [f"### Under 100 characters ({len(small)})", ""] + [f"- `{c['chunk_id']}` ({len(c['text'])}): {one_line(c['text'], 100)}"
                                                       for c in small[:40]]
L += ["", f"### Over 3,000 characters ({len(big)})", ""] + [f"- `{c['chunk_id']}` ({len(c['text'])}) {c.get('section', '')[:70]}"
                                                         for c in big[:40]]
L += ["", "## Chunks per doc_type", ""] + table(Counter(c["doc_type"] for c in chunks), "doc_type")
L += ["", "## Chunks per scheme", ""] + table(Counter(c.get("scheme") for c in chunks), "scheme")
L += ["", "## Chunks per source (all)", "", "| source_id | chunks | title |", "|---|---|---|"]
L += [f"| {s} | {len(v)} | {one_line(v[0]['title'], 70)} |" for s, v in sorted(by_src.items(), key=lambda x: -len(x[1]))]

L += ["", "## 3 sample chunks per main document (first, middle, last)", ""]
for s in main_docs:
    v = by_src[s]
    L.append(f"### {s} ({len(v)} chunks): {v[0]['title']}")
    for c in dict.fromkeys([v[0]["chunk_id"], v[len(v) // 2]["chunk_id"], v[-1]["chunk_id"]]):
        c = next(x for x in v if x["chunk_id"] == c)
        L.append(f"- `{c['chunk_id']}` · p.{c.get('page') or '-'} · {c.get('section') or '(no section)'}  \n"
                 f"  > {one_line(c['text'], 300)}")
    L.append("")

no_chunks = [d for d in parsed if d["source_id"] not in by_src]
L += ["## Documents with 0 chunks", "", f"{len(no_chunks)} documents (scanned without OCR, or only garbled Hindi):", ""]
L += [f"- `{d['source_id']}` ({d['path']}): {len(d.get('empty_pages', []))} pages without text" for d in no_chunks]
empty = [(d["source_id"], d.get("empty_pages", [])) for d in parsed if d.get("empty_pages")]
L += ["", "## Pages with no text layer (need OCR)", "",
      f"{sum(len(p) for _, p in empty)} pages in {len(empty)} documents:", ""]
L += [f"- `{s}`: pages {', '.join(map(str, p[:20]))}{' …' if len(p) > 20 else ''}" for s, p in empty]

out = ROOT / "eval" / "chunk_report.md"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"{len(chunks)} chunks, {len(small)} < 100 chars, {len(big)} > 3000 chars, {len(no_chunks)} docs with 0 chunks -> {out.relative_to(ROOT)}")
