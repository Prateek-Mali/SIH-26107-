"""Turn parsed documents and product CSVs into chunks.

Usage:
    python scripts/chunk.py        # data/processed/parsed.jsonl + data/structured/*.csv -> chunks.jsonl

Structure first (Chapter / Section / Rule / Regulation / Clause / Schedule headings and numbered
items), then each chunk is capped at ~800 tokens with ~100 tokens of overlap.
"""
import csv
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PARSED = DATA / "processed" / "parsed.jsonl"
OUT = DATA / "processed" / "chunks.jsonl"

MAX_TOKENS = 800
OVERLAP_TOKENS = 100
MIN_TOKENS = 120  # merge tiny structural pieces into the next one

HEADING = re.compile(
    r"""^\s*(
        \#{1,4}\s+\S.*                                             # markdown heading
      | (CHAPTER|Chapter|अध्याय)\s+[IVXLC\d]+\b.*                     # CHAPTER IV
      | (SECTION|Section|RULE|Rule|REGULATION|Regulation|CLAUSE|Clause
         |SCHEDULE|Schedule|ANNEX|Annex|ANNEXURE|Annexure|SCHEME|Scheme|PART|Part)
        [\s\-–—]+[IVXLC\d]+[A-Z]?\b.*                              # Section 17, Schedule II
      | (FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH)\s+SCHEDULE\b.*
      | \d{1,3}[A-Z]?\.\s+(\(\d+\)\s*)?[A-Z(ऀ-ॿ].{0,200}   # 17. Prohibition of improper use...
      | \*\*Q(uestion)?\s*\d*[.:)].*                               # FAQ question
    )\s*$""",
    re.X,
)

try:
    import tiktoken

    _enc = tiktoken.get_encoding("cl100k_base")

    def n_tokens(text: str) -> int:
        return len(_enc.encode(text, disallowed_special=()))
except Exception:  # offline fallback: rough estimate
    def n_tokens(text: str) -> int:
        return len(text) // 4


def split_structure(lines: list[tuple[int | None, str]]) -> list[dict]:
    """Group (page, line) pairs into segments that start at headings."""
    segs, cur = [], {"section": "", "page": None, "page_end": None, "lines": []}
    for page, line in lines:
        if HEADING.match(line) and cur["lines"]:
            segs.append(cur)
            cur = {"section": "", "page": None, "page_end": None, "lines": []}
        if not cur["lines"]:
            cur["section"] = re.sub(r"^#+\s*|\*\*", "", line.strip())[:150] if HEADING.match(line) else ""
            cur["page"] = page
        cur["lines"].append(line)
        cur["page_end"] = page
    if cur["lines"]:
        segs.append(cur)
    for s in segs:
        s["text"] = "\n".join(s.pop("lines")).strip()
    return [s for s in segs if s["text"]]


def merge_small(segs: list[dict]) -> list[dict]:
    out = []
    for s in segs:
        if out and n_tokens(out[-1]["text"]) < MIN_TOKENS and n_tokens(out[-1]["text"] + s["text"]) <= MAX_TOKENS:
            prev = out[-1]
            prev["text"] += "\n" + s["text"]
            prev["page_end"] = s["page_end"]
            if not prev["section"]:
                prev["section"] = s["section"]
        else:
            out.append(dict(s))
    return out


def cap(seg: dict) -> list[dict]:
    """Split a segment longer than MAX_TOKENS into overlapping windows (on line/sentence bounds)."""
    if n_tokens(seg["text"]) <= MAX_TOKENS:
        return [seg]
    units = [u for u in re.split(r"(?<=\n)|(?<=[.;])\s+", seg["text"]) if u and u.strip()]
    pieces, cur = [], []
    for u in units:
        if cur and n_tokens("".join(cur) + u) > MAX_TOKENS:
            pieces.append("".join(cur))
            tail, size = [], 0
            for prev in reversed(cur):  # carry ~OVERLAP_TOKENS into the next piece
                size += n_tokens(prev)
                if size > OVERLAP_TOKENS:
                    break
                tail.insert(0, prev)
            cur = tail
        cur.append(u if u.endswith("\n") else u + " ")
    if cur:
        pieces.append("".join(cur))
    out = []
    for p in pieces:  # hard split for long runs without sentence breaks (tables)
        words = p.split(" ")
        while n_tokens(" ".join(words)) > MAX_TOKENS:
            cut = len(words) * MAX_TOKENS // n_tokens(" ".join(words)) - 5
            out.append(" ".join(words[:cut]))
            words = words[max(cut - OVERLAP_TOKENS // 2, 1):]
        out.append(" ".join(words))
    return [{**seg, "text": p.strip()} for p in out if p.strip()]


def chunk_document(doc: dict) -> list[dict]:
    lines = [(p["page"], line) for p in doc["pages"] for line in p["text"].splitlines()]
    segs = [c for s in merge_small(split_structure(lines)) for c in cap(s)]
    page_lang = {p["page"]: p["lang"] for p in doc["pages"]}
    chunks = []
    for i, s in enumerate(segs):
        chunks.append({
            "chunk_id": f"{doc['source_id']}::{i:04d}",
            "source_id": doc["source_id"],
            "title": doc["title"],
            "url": doc["url"],
            "agent": doc["agent"],
            "doc_type": doc["doc_type"],
            "page": s["page"],
            "page_end": s["page_end"],
            "section": s["section"],
            "lang": page_lang.get(s["page"]) or doc["pages"][0]["lang"],
            "text": s["text"],
            "date_downloaded": doc.get("date_downloaded", ""),
        })
    return chunks


SCHEME_NAMES = {
    "scheme1_products_table": "Scheme I (ISI mark)",
    "scheme2_page": "Scheme II (CRS registration)",
    "scheme4_page": "Scheme IV (Certificate of Conformity)",
    "schemeX_page": "Scheme X",
    "fmcs_products": "FMCS (Foreign Manufacturers Certification Scheme)",
    "upcoming_qcos": "Upcoming QCO (notified, due for implementation)",
}
ROW_KEYS = {"s_no", "category", "is_number", "product", "qco_title", "qco_pdf_url",
            "source_id", "source_url", "date_downloaded"}


def row_text(row: dict, scheme: str) -> str:
    parts = []
    if row.get("product"):
        parts.append(f"Product: {row['product']}")
    if row.get("is_number"):
        parts.append(row["is_number"])
    parts.append(scheme)
    if row.get("category"):
        parts.append(f"Category: {row['category']}")
    if row.get("qco_title"):
        parts.append("QCO: " + re.sub(r"^\d+\.\s*", "", row["qco_title"]))
    for k, v in row.items():  # other columns (dates, remarks) as "Key: value"
        if k not in ROW_KEYS and v and v.strip():
            parts.append(f"{k.replace('_', ' ').title()}: {v.strip()}")
    if row.get("qco_pdf_url"):
        links = row["qco_pdf_url"].split(" | ")
        if len(links) > 4:  # original order + latest amendments keep the chunk small
            links = links[:1] + links[-3:] + [f"({len(links) - 4} more on the product page)"]
        parts.append("PDF: " + " | ".join(links))
    return " | ".join(parts)


def row_label(row: dict) -> str:
    """Citation label for a product row, e.g. 'IS 269: Ordinary Portland Cement'."""
    label = ": ".join(x for x in (row.get("is_number", "").strip(), row.get("product", "").strip()) if x)
    return (label or row.get("category", ""))[:120]


def chunk_csvs(sources: dict) -> list[dict]:
    chunks = []
    for f in sorted((DATA / "structured").glob("*.csv")):
        rows = list(csv.DictReader(f.open(encoding="utf-8")))
        if not rows:
            continue
        sid = rows[0].get("source_id") or f.stem
        src = sources.get(sid, {})
        scheme = SCHEME_NAMES.get(sid, src.get("title", f.stem))
        for i, row in enumerate(rows):
            if not (row.get("product") or row.get("is_number") or row.get("qco_title")):
                continue
            chunks.append({
                "chunk_id": f"{sid}::row{i:04d}",
                "source_id": sid,
                "title": src.get("title", f.stem),
                "url": row.get("source_url") or src.get("url", ""),
                "agent": src.get("agent", "product_qco"),
                "doc_type": "qco",
                "page": None,
                "page_end": None,
                "section": row_label(row),
                "lang": "en",
                "text": row_text(row, scheme),
                "date_downloaded": row.get("date_downloaded", ""),
            })
    return chunks


def main():
    sources = {s["id"]: s for s in yaml.safe_load((DATA / "sources.yaml").read_text())["sources"]}
    n_docs = 0
    all_chunks = []
    for line in PARSED.open(encoding="utf-8"):
        doc = json.loads(line)
        if doc["pages"]:
            all_chunks += chunk_document(doc)
            n_docs += 1
    rows = chunk_csvs(sources)
    all_chunks += rows
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as out:
        for c in all_chunks:
            out.write(json.dumps(c, ensure_ascii=False) + "\n")
    sizes = sorted(n_tokens(c["text"]) for c in all_chunks) or [0]
    print(f"{len(all_chunks)} chunks ({len(all_chunks) - len(rows)} from {n_docs} documents, "
          f"{len(rows)} product rows) -> {OUT.relative_to(ROOT)}")
    print(f"tokens per chunk: median {sizes[len(sizes) // 2]}, max {sizes[-1]}")


if __name__ == "__main__":
    main()
