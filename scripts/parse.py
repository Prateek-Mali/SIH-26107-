"""Parse downloaded PDFs and HTML pages into clean text with page numbers.

Usage:
    python scripts/parse.py            # writes data/processed/parsed.jsonl
    python scripts/parse.py --no-ocr   # skip Gemini OCR of pages without a text layer

One output record per document:
    {source_id, title, url, agent, doc_type, date_downloaded, path,
     pages: [{page, text, lang}], ocr_pages: [...], empty_pages: [...]}
PDF pages are 1-based. HTML pages are one page with page = null.
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlparse

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "processed" / "parsed.jsonl"
OCR_CACHE = DATA / "processed" / "ocr_cache"

# Gazette of India boilerplate (English and Hindi masthead lines, registration numbers, press credits).
GAZETTE_JUNK = [
    r"^\s*(the\s+)?gazette\s+of\s+india\s*[:：]?\s*(extraordinary)?\s*$",
    r"^\s*(extraordinary|published by authority|प्राधिकार से प्रकाशित|असाधारण)\s*$",
    r"^\s*(भारत\s+का\s+राजपत्र).*$",
    r"^\s*\[?\s*part\s+[ivx]+\s*[-—–]\s*sec(tion)?\.?\s*\d.*$",
    r"^\s*\[?\s*भाग\s+[iIvVxX]+.*खण्ड.*$",
    r"^\s*(registered\s+no|regd\.?\s*no)\.?.*$",
    r"^\s*(सी\.\s*जी\.|CG-[A-Z]{2}-E-\d+|xxxGIDExxx|xxxGIDHxxx).*$",
    r"^\s*uploaded by dte\.? of printing.*$",
    r"^\s*digitally signed by.*$",
    r"^\s*(date|signature not verified|reason|location)\s*:.*$",
    r"^\s*no\.\s*\d+\]\s*new delhi,.*$",
    r"^\s*सं\.\s*\d+\]\s*नई\s*दिल्ली.*$",
    r"^\s*sec\.\s*\d+\s*(\(\w+\))*\s*\]?\s*$",  # running head "SEC. 1]"
    r"^\s*\d+\s*$",                      # bare page numbers
    r"^\s*page\s+\d+\s+(of\s+\d+)?\s*$",
]
GAZETTE_RE = re.compile("|".join(GAZETTE_JUNK), re.I)
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
LATIN = re.compile(r"[A-Za-z]")


def detect_lang(text: str) -> str:
    hi, en = len(DEVANAGARI.findall(text)), len(LATIN.findall(text))
    return "hi" if hi > 0.3 * max(hi + en, 1) else "en"


def doc_type_for(source_id: str, title: str, kind: str) -> str:
    t = f"{source_id} {title}".lower()
    if source_id.startswith("qco_") or "quality control" in t:
        return "qco"
    if "faq" in t:
        return "faq"
    if "guideline" in t or "guidance" in t:
        return "guideline"
    if kind == "html":
        return "page"
    if "regulation" in t or source_id.startswith("ca_") or "_regs" in source_id:
        return "regulation"
    if "rules" in t:
        return "rule"
    if re.search(r"\bact\b", t):
        return "act"
    if "order" in t or "s.o." in t or "notification" in t:
        return "order"
    return "guideline"


DEP_VOWEL = re.compile(r"(^|\s)[\u093E-\u094D]")


def is_garbled_hindi(text: str) -> bool:
    """Legacy-font Gazette pages extract as broken Devanagari: words start with vowel signs."""
    words = re.findall(r"\S+", text)
    deva = [w for w in words if DEVANAGARI.search(w)]
    if len(deva) < 20:
        return False
    return len(DEP_VOWEL.findall(text)) / len(deva) > 0.05


def is_margin(b, width: float) -> bool:
    w = b[2] - b[0]
    return w < 0.2 * width and (b[0] > 0.72 * width or b[2] < 0.28 * width) and bool(LATIN.search(b[4]) or DEVANAGARI.search(b[4]))


def page_text(page: pymupdf.Page) -> str:
    """Page text in reading order, with side-margin notes (section titles in Acts/Rules) folded in.

    "15. (1) No person shall..." + margin "Prohibition to import, sell" becomes
    "15. Prohibition to import, sell\n(1) No person shall..."
    """
    width = page.rect.width
    blocks = [list(b) for b in page.get_text("blocks", sort=True) if b[6] == 0 and b[4].strip()]
    main = [b for b in blocks if not is_margin(b, width)]
    margins = [b for b in blocks if is_margin(b, width)]
    if not main:
        return "\n".join(b[4] for b in blocks)
    for m in margins:
        note = " ".join(m[4].split())
        target = min(main, key=lambda b: abs(b[1] - m[1]))
        num = re.match(r"\s*(\d+[A-Z]?)\.\s+", target[4])
        if num and abs(target[1] - m[1]) < 15 and not target[4].startswith(f"{num.group(1)}. {note}"):
            target[4] = f"{num.group(1)}. {note}\n" + target[4][num.end():]
        else:
            target[4] = target[4].rstrip("\n") + f"\n[{note}]\n"
    return "\n".join(b[4].rstrip("\n") for b in main)


def clean_page(text: str) -> str:
    text = text.replace("­", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = re.sub(r"(\w)-\n\s*(\w)", r"\1\2", text)  # hyphenated line breaks
    lines = [l.rstrip() for l in text.splitlines()]
    lines = [l for l in lines if not GAZETTE_RE.match(l)]
    text = "\n".join(lines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_repeated_lines(pages: list[str]) -> list[str]:
    """Drop header/footer lines that repeat on most pages (checked in the first/last 3 lines)."""
    if len(pages) < 3:
        return pages
    counts = Counter()
    for p in pages:
        lines = [l.strip() for l in p.splitlines() if l.strip()]
        for l in set(lines[:3] + lines[-3:]):
            counts[re.sub(r"\d+", "#", l)] += 1
    repeated = {l for l, n in counts.items() if n >= max(3, 0.5 * len(pages)) and len(l) < 150}
    out = []
    for p in pages:
        out.append("\n".join(l for l in p.splitlines() if re.sub(r"\d+", "#", l.strip()) not in repeated))
    return out


def ocr_page(page: pymupdf.Page, cache_key: str) -> str:
    """Send a page image to Gemini for text extraction. Cached on disk."""
    cache = OCR_CACHE / f"{cache_key}.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    sys.path.insert(0, str(ROOT))
    from app.llm import gemini_ocr  # imported lazily: only needed for scanned pages

    png = page.get_pixmap(dpi=150).tobytes("png")
    text = gemini_ocr(png)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return text


def parse_pdf(path: Path, use_ocr: bool) -> tuple[list[dict], list[int], list[int]]:
    doc = pymupdf.open(path)
    raw, ocr_pages, empty = [], [], []
    texts = [page_text(p) for p in doc]
    # Bilingual Gazettes: the Hindi text layer uses legacy fonts and extracts garbled.
    # When the document also has English text, keep only the English lines (same law).
    # Hindi-only documents with a garbled text layer are sent to OCR like scanned pages.
    has_english = any(len(LATIN.findall(t)) > 200 for t in texts)
    for i, (page, text) in enumerate(zip(doc, texts), start=1):
        scanned = len(text.strip()) < 30 and bool(page.get_images() or page.get_drawings())
        garbled = not has_english and is_garbled_hindi(text)
        if has_english:
            text = "\n".join(l for l in text.splitlines()
                              if len(DEVANAGARI.findall(l)) <= len(LATIN.findall(l)))
        if scanned or garbled:
            if use_ocr:
                try:
                    text = ocr_page(page, f"{path.stem}_p{i}")
                    ocr_pages.append(i)
                except Exception as e:
                    print(f"    OCR failed on {path.name} p{i}: {e}")
                    empty.append(i)
            else:
                empty.append(i)
        raw.append(text)
    cleaned = strip_repeated_lines([clean_page(t) for t in raw])
    pages = [{"page": i, "text": t, "lang": detect_lang(t)} for i, t in enumerate(cleaned, start=1) if len(t) > 20]
    return pages, ocr_pages, empty


def parse_html_md(path: Path) -> tuple[str, str, str]:
    """Return (url, date, body) from a saved markdown page."""
    text = path.read_text(encoding="utf-8")
    url = re.search(r"^Source: (\S+)", text, re.M)
    day = re.search(r"^Downloaded: (\S+)", text, re.M)
    body = text.split("\n---\n", 1)[-1].strip()
    return (url.group(1) if url else ""), (day.group(1) if day else ""), body


def load_metadata() -> tuple[dict, dict, dict]:
    cfg = yaml.safe_load((DATA / "sources.yaml").read_text())
    sources = {s["id"]: s for s in cfg["sources"]}
    log = {}  # path -> latest successful log row
    if (DATA / "download_log.csv").exists():
        for row in csv.DictReader((DATA / "download_log.csv").open(encoding="utf-8")):
            if row["status"] == "downloaded" and row.get("path"):
                log[row["path"]] = row
    qco_titles = {}  # QCO PDF url -> order title from the product tables
    for f in (DATA / "structured").glob("*.csv"):
        for row in csv.DictReader(f.open(encoding="utf-8")):
            for link in filter(None, (row.get("qco_pdf_url") or "").split(" | ")):
                qco_titles.setdefault(link, row.get("qco_title") or "")
    return sources, log, qco_titles


def qco_title(url: str, table_title: str) -> str:
    name = Path(unquote(urlparse(url).path)).stem
    pretty = re.sub(r"[-_]+", " ", name).strip()
    table_title = re.sub(r"^\d+\.\s*", "", table_title or "").strip()
    if table_title and len(table_title) < 160:
        return f"{table_title} ({pretty})"
    return pretty


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ocr", action="store_true", help="do not call Gemini for scanned pages")
    args = ap.parse_args()

    use_ocr = not args.no_ocr
    if use_ocr:
        sys.path.insert(0, str(ROOT))
        import os
        os.environ.setdefault("BIS_QUIET", "1")
        from app import config
        if not config.KEY_IS_SET:
            print("GEMINI_API_KEY not set: scanned pages will be skipped (run again later to OCR them).")
            use_ocr = False

    sources, log, qco_titles = load_metadata()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n_docs = n_pages = n_empty = n_ocr = 0
    with OUT.open("w", encoding="utf-8") as out:
        for path in sorted((DATA / "raw").rglob("*")):
            if path.suffix not in (".pdf", ".md"):
                continue
            rel = str(path.relative_to(ROOT))
            agent = path.parent.name
            sid = path.stem
            base_id = sid.split("__")[0]
            src = sources.get(base_id, {})
            logrow = log.get(rel, {})
            record = {"source_id": sid, "agent": agent, "path": rel}
            try:
                if path.suffix == ".pdf":
                    pages, ocr_pages, empty = parse_pdf(path, use_ocr)
                    url = src.get("url") or logrow.get("url", "")
                    title = src.get("title") or qco_title(url, qco_titles.get(url, ""))
                    record.update(url=url, title=title, date_downloaded=logrow.get("date", ""),
                                  doc_type=doc_type_for(sid, title, "pdf"),
                                  pages=pages, ocr_pages=ocr_pages, empty_pages=empty)
                    n_empty += len(empty)
                    n_ocr += len(ocr_pages)
                else:
                    url, day, body = parse_html_md(path)
                    title = src.get("title", sid)
                    heading = re.search(r"^# (.+)$", body, re.M)
                    if sid != base_id and heading:  # followed sub-page: use its own heading
                        title = f"{title}: {heading.group(1).strip()}"
                    record.update(url=url, title=title, date_downloaded=day,
                                  doc_type=doc_type_for(sid, title, "html"),
                                  pages=[{"page": None, "text": body, "lang": detect_lang(body)}],
                                  ocr_pages=[], empty_pages=[])
            except Exception as e:
                print(f"  [failed] {rel}: {e}")
                continue
            if not record["pages"]:
                print(f"  [no text] {rel} (scanned pages: {record['empty_pages'][:5]}...)")
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            n_docs += 1
            n_pages += len(record["pages"])
    print(f"Parsed {n_docs} documents, {n_pages} pages with text, {n_ocr} OCR'd pages, "
          f"{n_empty} pages without text -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
