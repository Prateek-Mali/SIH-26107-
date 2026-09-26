"""Tools for the agents: product lookup in the scraped CSVs, and official links."""
import csv
import re
import sys
from functools import lru_cache

from app import config
from app.retrieval import STOPWORDS

sys.path.insert(0, str(config.ROOT / "scripts"))
from chunk import SCHEME_NAMES, row_label, row_text  # noqa: E402  (same row text and ids as the index)

IS_NUMBER = re.compile(r"\bIS(?:\s*/\s*(?:IEC|ISO))?\s*[:\-]?\s*(\d{1,5})(?:\s*[:(]?\s*part\s*(\d+))?", re.I)


def _norm_is(text: str) -> set[str]:
    """'IS 1489 (Part 1) : 2015' -> {'1489', '1489-1'}"""
    out = set()
    for num, part in IS_NUMBER.findall(text or ""):
        out.add(num)
        if part:
            out.add(f"{num}-{part}")
    return out


def _words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w.rstrip("s") for w in words if w not in STOPWORDS and len(w) > 2}


@lru_cache(maxsize=1)
def product_rows() -> list[dict]:
    """Every product row as a chunk-like dict (same chunk_id as in chunks.jsonl)."""
    rows = []
    for f in sorted((config.DATA / "structured").glob("*.csv")):
        data = list(csv.DictReader(f.open(encoding="utf-8")))
        if not data:
            continue
        sid = data[0].get("source_id") or f.stem
        scheme = SCHEME_NAMES.get(sid, f.stem)
        for i, row in enumerate(data):
            if not (row.get("product") or row.get("is_number") or row.get("qco_title")):
                continue
            rows.append({
                "chunk_id": f"{sid}::row{i:04d}", "source_id": sid, "agent": "product_qco",
                "title": f"BIS list of products: {scheme}", "url": row.get("source_url", ""),
                "doc_type": "qco", "page": None, "section": row_label(row), "lang": "en",
                "text": row_text(row, scheme), "date_downloaded": row.get("date_downloaded", ""),
                "_is": _norm_is(row.get("is_number", "")), "_words": _words(row.get("product", "")),
            })
    return rows


def lookup_product(name_or_is_number: str, limit: int = 5) -> list[dict]:
    """Find product rows by IS number (exact) or by product name (word overlap)."""
    wanted_is = _norm_is(name_or_is_number)
    rows = product_rows()
    if wanted_is:
        hits = [r for r in rows if r["_is"] & wanted_is]
        # prefer exact part matches ("IS 1489 (Part 1)") over the bare number
        hits.sort(key=lambda r: -len(r["_is"] & wanted_is))
        if hits:
            return [_public(r) for r in hits[:limit]]
    q = _words(name_or_is_number)
    if not q:
        return []
    scored = []
    for r in rows:
        overlap = len(q & r["_words"])
        if overlap:
            full = overlap == len(r["_words"])  # every word of the product name is in the question
            scored.append((overlap / (len(r["_words"]) ** 0.5 + 1), {**r, "match_words": overlap, "full_match": full}))
    scored.sort(key=lambda x: -x[0])
    return [_public(r) for _, r in scored[:limit]]


def _public(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_")}


LINK_FOR_INTENT = {
    "law": ("BIS Act, Rules & Regulations", "https://www.bis.gov.in/the-bureau/bis-act-rules-and-regulations/?lang=en"),
    "certification": ("Manak Online", "https://www.manakonline.in/"),
    "product_qco": ("Know Your Standard", "https://www.bis.gov.in/know-your-standard/?lang=en"),
    "hallmarking_consumer": ("BIS CARE app", "https://play.google.com/store/apps/details?id=com.bis.bisapp"),
}


def official_link(intent: str | None = None) -> str:
    """A relevant official link, formatted 'Name (URL)'."""
    name, url = LINK_FOR_INTENT.get(intent or "", ("the BIS website", "https://www.bis.gov.in"))
    return f"{name} ({url})"
