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

ROMAN = r"(?:X|IX|VIII|VII|VI|V|IV|III|II|I)"

# Top-level containers: the whole line must be the heading (optionally with a short note in brackets).
TOP = re.compile(
    r"^\s*((?:THE\s+)?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH)\s+SCHEDULE"
    r"|(?:SCHEDULE|Schedule)[\s\-–—]*(?:" + ROMAN + r"|\d+)"
    r"|(?:CHAPTER|Chapter)\s+(?:[IVXLC]+|\d+)"
    r"|(?:ANNEX(?:URE)?|Annex(?:ure)?)[\s\-–—]*(?:[IVX]+|\d+|[A-Z])?"
    r"|(?:FORM|Form)[\s\-–—]*(?:[IVX]+|\d+|[A-Z])"
    r")\s*[.:\-–—]?\s*(\([^)]{0,80}\))?\s*$")
SCHEME = re.compile(r"^\s*(?:SCHEME|Scheme)[\s\-–—]*(" + ROMAN + r"|10|\d)\b\s*[.:\-–—]?\s*([A-Z][^,;]{0,80})?\s*$")
NUMBERED = re.compile(r"^\s*(\d{1,3}[A-Z]?)\.\s+(.+)$")
MARKDOWN = re.compile(r"^\s*(#{1,4})\s+(.+?)\s*#*\s*$")
FAQ_Q = re.compile(r"^\s*\*\*\s*(?:Q(?:uestion)?\s*)?\d*[.:)]?\s*(.+?)\*\*\s*$")
ARABIC = {"10": "X", **{str(i): r for i, r in enumerate(["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]) if i}}


def numbered_title(num: str, rest: str) -> str | None:
    """'17. Prohibition to manufacture ... Mark. (1) No person' -> '17. Prohibition to ... Mark'.
    Returns None for lines that are not headings (form fields ending in ':', lowercase continuations)."""
    rest = rest.strip()
    if not rest or not (rest[0].isupper() or rest[0] in "(\"'“" or "ऀ" <= rest[0] <= "ॿ"):
        return None
    if rest.startswith("("):  # "33. (1) Notwithstanding ..." -> no title of its own
        return f"{num}."
    if rest.endswith("?") and len(rest) < 200:  # FAQ question
        return f"{num}. {rest}"
    m = re.match(r"(.{3,120}?)(?:\.(?=\s|$)|\s[–—-]\s|:-|\.–|\.—)", rest)
    title = m.group(1).strip() if m else rest.strip()
    if rest.rstrip().endswith(":") and not m:  # form field such as "1. Name of Applicant:"
        return None
    if len(title) > 120 or title.endswith((",", ":", ";", "—", "-")) or re.search(r"\b(in|of|the|and|to)$", title):
        return f"{num}."  # a real numbered item, but the line is a sentence, not a title
    return f"{num}. {title}"


try:
    import tiktoken

    _enc = tiktoken.get_encoding("cl100k_base")

    def n_tokens(text: str) -> int:
        return len(_enc.encode(text, disallowed_special=()))
except Exception:  # offline fallback: rough estimate
    def n_tokens(text: str) -> int:
        return len(text) // 4


def split_structure(lines: list[tuple[int | None, str]], doc_type: str = "") -> list[dict]:
    """Group (page, line) pairs into segments that start at headings, tracking the heading path
    (top container > scheme > numbered item). Each segment gets 'section' (the path) and 'scheme'."""
    word = {"act": "Section", "rule": "Rule", "regulation": "Regulation"}.get(doc_type, "")
    top = scheme = item = ""
    segs, cur = [], None

    def path() -> str:
        label = item
        # Act sections / Rules / Regulations are numbered through the whole text, even inside chapters
        if item and word and not scheme and (not top or top.lower().startswith("chapter")) and item[0].isdigit():
            label = f"{word} {item}"
        return " > ".join(x for x in (top, scheme, label) if x)[:200]

    for page, line in lines:
        heading = False
        m_top, m_scheme, m_num = TOP.match(line), SCHEME.match(line), NUMBERED.match(line)
        m_md, m_faq = MARKDOWN.match(line), FAQ_Q.match(line)
        if m_top:
            top = " ".join(line.split())[:80]
            item = ""
            if not re.match(r"(?i)\s*(annex|form)", line):
                scheme = ""
            heading = True
        elif m_scheme:
            roman = ARABIC.get(m_scheme.group(1), m_scheme.group(1))
            scheme = f"Scheme-{roman}" + (f" {m_scheme.group(2).strip()}" if m_scheme.group(2) else "")
            item = ""
            heading = True
        elif m_md and not m_md.group(2).rstrip("*").rstrip().endswith((":", ",")):
            item = re.sub(r"\*\*|\[|\]\([^)]*\)", "", m_md.group(2)).strip()[:150]
            heading = True
        elif m_faq and not m_faq.group(1).rstrip().endswith((":", ",")):
            item = m_faq.group(1).strip()[:150]
            heading = True
        elif m_num:
            title = numbered_title(m_num.group(1), m_num.group(2))
            if title:
                item = title[:150]
                heading = True
        if cur is None or (heading and cur["lines"]):
            if cur and cur["lines"]:
                segs.append(cur)
            cur = {"section": path(), "scheme_heading": scheme, "page": page, "page_end": page, "lines": []}
        cur["lines"].append(line)
        cur["page_end"] = page
    if cur and cur["lines"]:
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
                prev["section"], prev["scheme_heading"] = s["section"], s.get("scheme_heading", "")
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
    segs = [c for s in merge_small(split_structure(lines, doc["doc_type"])) for c in cap(s)]
    first_pages = "\n".join(p["text"] for p in doc["pages"][:4])
    base_scheme = doc.get("scheme") or scheme_for_source(doc["source_id"], doc.get("url", ""))
    title = better_title(doc, first_pages)
    doc_date = find_date(first_pages) if doc["pages"][0]["page"] is not None else ""
    if not doc_date:  # fall back to the year in the title ("... Regulations, 2018")
        years = re.findall(r"\b(19[5-9]\d|20[0-3]\d)\b", title)
        doc_date = years[-1] if years else ""
    page_lang = {p["page"]: p["lang"] for p in doc["pages"]}
    # drop fragments with almost no words (e.g. numbering left over after garbled Hindi lines are removed)
    segs = [s for s in segs if len(re.findall(r"[A-Za-z\u0900-\u097F]", s["text"])) >= 40]
    chunks = []
    for i, s in enumerate(segs):
        chunks.append({
            "chunk_id": f"{doc['source_id']}::{i:04d}",
            "source_id": doc["source_id"],
            "title": title,
            "url": doc["url"],
            "agent": doc["agent"],
            "doc_type": doc["doc_type"],
            "scheme": scheme_from_heading(s.get("scheme_heading", "")) or base_scheme,
            "doc_date": doc_date,
            "page": s["page"],
            "page_end": s["page_end"],
            "section": s["section"],
            "lang": page_lang.get(s["page"]) or doc["pages"][0]["lang"],
            "text": s["text"],
            "date_downloaded": doc.get("date_downloaded", ""),
        })
    return chunks


MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
DATE_PATTERNS = [
    re.compile(r"(\d{1,2})(?:st|nd|rd|th)?\s*(?:day of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s*,?\s*(\d{4})", re.I),
    re.compile(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})", re.I),
    re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b"),
]


def find_date(text: str) -> str:
    """First plausible date in a document's opening pages (the notification date), as YYYY-MM-DD."""
    best = None
    for i, pat in enumerate(DATE_PATTERNS):
        for m in pat.finditer(text[:6000]):
            g = m.groups()
            try:
                if i == 0:
                    d, mo, y = int(g[0]), MONTHS[g[1][:3].lower()], int(g[2])
                elif i == 1:
                    mo, d, y = MONTHS[g[0][:3].lower()], int(g[1]), int(g[2])
                else:
                    d, mo, y = int(g[0]), int(g[1]), int(g[2])
            except (KeyError, ValueError):
                continue
            if 1950 <= y <= 2030 and 1 <= mo <= 12 and 1 <= d <= 31 and (best is None or m.start() < best[0]):
                best = (m.start(), f"{y:04d}-{mo:02d}-{d:02d}")
            break
    return best[1] if best else ""


SOURCE_SCHEMES = [  # source_id prefix -> scheme
    ("guide_grant_coc", "IV"), ("guide_renewal_coc", "IV"), ("guide_coc_", "IV"), ("guide_", "I"),
    ("fmcs_", "FMCS"), ("crs_", "II"), ("marking_requirements", "II"), ("scheme2_page", "II"),
    ("hm_", "Hallmarking"), ("scheme1_products_table", "I"), ("cert_", "I"), ("simplified_procedure", "I"),
    ("application_checklist", "I"), ("operating_manual", "I"), ("scheme4_page", "IV"),
    ("schemeX_page", "X"), ("scheme_x_process", "X"), ("upcoming_qcos", "I"),
]
TABLE_SCHEME = {"products_scheme1": "I", "products_scheme2": "II", "products_scheme4": "IV",
                "products_schemeX": "X", "products_fmcs": "FMCS", "upcoming_qcos": "I"}
_pdf_scheme: dict[str, str] = {}


def _load_pdf_schemes():
    """QCO PDF url -> scheme of the product table that links it."""
    if _pdf_scheme:
        return
    for f in (DATA / "structured").glob("*.csv"):
        sch = TABLE_SCHEME.get(f.stem, "I")
        for row in csv.DictReader(f.open(encoding="utf-8")):
            for link in filter(None, (row.get("qco_pdf_url") or "").split(" | ")):
                _pdf_scheme.setdefault(link.replace("://bis.gov.in", "://www.bis.gov.in"), sch)


def scheme_for_source(source_id: str, url: str = "") -> str:
    if source_id.startswith("qco_"):
        _load_pdf_schemes()
        return _pdf_scheme.get(url.replace("://bis.gov.in", "://www.bis.gov.in"), "I")
    for prefix, sch in SOURCE_SCHEMES:
        if source_id.startswith(prefix):
            return sch
    return "general"


def scheme_from_heading(heading: str) -> str:
    m = re.match(r"Scheme-(" + ROMAN + r")\b", heading or "")
    return m.group(1) if m else ""


def better_title(doc: dict, first_pages: str) -> str:
    """QCO PDFs are named after file names like 'S.O 1081 (E)': use the order's own title if found."""
    title = doc["title"]
    if not doc["source_id"].startswith("qco_") or len(re.sub(r"[^A-Za-z]", "", title)) > 25:
        return title
    m = re.search(r"([A-Z][A-Za-z ,&()\-/]{5,120}?\((?:Quality Control|Compulsory Registration)\)[A-Za-z ()]*Order,?\s*\d{4})",
                  " ".join(first_pages.split()))
    if not m:
        m = re.search(r"([A-Z][A-Za-z ,&()\-/]{5,80}? Rules,?\s*\d{4})", " ".join(first_pages.split()))
    return f"{m.group(1).strip()} ({title})" if m else title


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
                "scheme": TABLE_SCHEME.get(f.stem, "I"),
                "doc_date": "",
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
