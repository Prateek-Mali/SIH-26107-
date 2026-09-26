"""Download every source in data/sources.yaml.

Usage:
    python scripts/download.py --priority 1        # sources with priority <= 1
    python scripts/download.py --priority 2
    python scripts/download.py --only scheme1_products_table

Obeys download_rules: polite delay, robots.txt, retries, skip existing files.
Every attempt is written to data/download_log.csv.
"""
import argparse
import csv
import hashlib
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import yaml
from bs4 import BeautifulSoup
from markdownify import markdownify

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW_PDF = DATA / "raw" / "pdf"
RAW_HTML = DATA / "raw" / "html"
LOG_PATH = DATA / "download_log.csv"
LOG_FIELDS = ["id", "url", "status", "bytes", "sha256", "date", "path", "note"]
TODAY = date.today().isoformat()

# Content we must never fetch: paid standards stores, login/CAPTCHA pages.
BLOCKED_URL = re.compile(r"bsbedge\.com|/login|captcha|signin|sign-in", re.I)
PAID_STANDARD = re.compile(r"\bIS\s*/\s*(ISO|IEC)\b|\bISO\s*/\s*IEC\s+\d", re.I)


class Downloader:
    def __init__(self, rules: dict):
        self.ua = rules.get("user_agent", "BIS-Assistant")
        self.delay = float(rules.get("delay_seconds", 2))
        self.retries = int(rules.get("retries", 3))
        self.skip_existing = bool(rules.get("skip_if_exists", True))
        self.respect_robots = bool(rules.get("respect_robots_txt", True))
        self.client = httpx.Client(
            headers={"User-Agent": self.ua}, follow_redirects=True, timeout=httpx.Timeout(120, connect=20)
        )
        self.robots: dict[str, RobotFileParser | None] = {}
        self.last_request = 0.0
        self.counts = {"downloaded": 0, "skipped": 0, "failed": 0}
        new_log = not LOG_PATH.exists()
        self.log_file = LOG_PATH.open("a", newline="")
        self.log = csv.DictWriter(self.log_file, fieldnames=LOG_FIELDS)
        if new_log:
            self.log.writeheader()

    # ---------- helpers ----------
    def record(self, sid, url, status, data=b"", path="", note=""):
        self.counts[status] += 1
        self.log.writerow({
            "id": sid, "url": url, "status": status, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest() if data else "",
            "date": TODAY, "path": str(path.relative_to(ROOT)) if path else "", "note": note,
        })
        self.log_file.flush()
        print(f"  [{status}] {sid}: {note or (path.name if path else url)}")

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        host = urlparse(url)._replace(path="", query="", fragment="").geturl()
        if host not in self.robots:
            rp = RobotFileParser()
            try:
                r = self.client.get(host + "/robots.txt", timeout=30)
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except httpx.HTTPError:
                rp.parse([])  # robots.txt unreachable: treat as no rules
            self.robots[host] = rp
        return self.robots[host].can_fetch(self.ua, url)

    def fetch(self, url: str) -> httpx.Response:
        if BLOCKED_URL.search(url):
            raise RuntimeError("blocked URL (login/CAPTCHA/paid store)")
        if not self.allowed(url):
            raise RuntimeError("disallowed by robots.txt")
        err = None
        for attempt in range(1, self.retries + 1):
            wait = self.delay - (time.time() - self.last_request)
            if wait > 0:
                time.sleep(wait)
            self.last_request = time.time()
            try:
                r = self.client.get(url)
                if BLOCKED_URL.search(str(r.url)):
                    raise RuntimeError(f"redirected to login/CAPTCHA page: {r.url}")
                if r.status_code == 200:
                    return r
                err = f"HTTP {r.status_code}"
                if r.status_code in (403, 404, 410):
                    break  # retrying will not help
            except httpx.HTTPError as e:
                err = f"{type(e).__name__}: {e}"
            time.sleep(self.delay * attempt)
        raise RuntimeError(err or "unknown error")

    # ---------- source types ----------
    def pdf(self, sid: str, url: str, out: Path):
        if self.skip_existing and out.exists() and out.stat().st_size > 0:
            return self.record(sid, url, "skipped", path=out, note="already downloaded")
        try:
            r = self.fetch(url)
            if not r.content.lstrip()[:4] == b"%PDF":
                raise RuntimeError(f"not a PDF (content-type {r.headers.get('content-type')})")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(r.content)
            self.record(sid, url, "downloaded", r.content, out)
        except Exception as e:
            self.record(sid, url, "failed", note=str(e))

    def html(self, src: dict):
        sid, url, agent = src["id"], src["url"], src["agent"]
        out = RAW_HTML / agent / f"{sid}.md"
        if self.skip_existing and out.exists() and out.stat().st_size > 0:
            self.record(sid, url, "skipped", path=out, note="already downloaded")
            if not src.get("follow_links_same_section"):
                return
            soup = None
        else:
            soup = self.save_page(sid, url, src["title"], out)
        if src.get("follow_links_same_section"):
            if soup is None:  # need the page again to find sub-pages
                try:
                    soup = parse_html(self.fetch(url).text)
                except Exception as e:
                    return self.record(sid, url, "failed", note=f"sub-page discovery: {e}")
            for sub_url, sub_title in same_section_links(soup, url):
                slug = slugify(urlparse(sub_url).path.rstrip("/").rsplit("/", 1)[-1])
                sub_out = RAW_HTML / agent / f"{sid}__{slug}.md"
                if self.skip_existing and sub_out.exists() and sub_out.stat().st_size > 0:
                    self.record(f"{sid}__{slug}", sub_url, "skipped", path=sub_out, note="already downloaded")
                else:
                    self.save_page(f"{sid}__{slug}", sub_url, sub_title or src["title"], sub_out)

    def save_page(self, sid, url, title, out: Path, drop_tables=False):
        """Fetch a page, keep main content as markdown. Returns the full soup (or None on failure)."""
        try:
            r = self.fetch(url)
            soup = parse_html(r.text)
            md = page_markdown(soup, url, drop_tables)
            if len(md) < 50:
                if drop_tables:  # page is only the table, which is already in the CSV
                    self.record(sid, url, "skipped", note="no text outside the table")
                    return soup
                raise RuntimeError("main content is empty")
            out.parent.mkdir(parents=True, exist_ok=True)
            text = f"# {title}\n\nSource: {url}\nDownloaded: {TODAY}\n\n---\n\n{md}\n"
            out.write_text(text, encoding="utf-8")
            self.record(sid, url, "downloaded", text.encode(), out)
            return soup
        except Exception as e:
            self.record(sid, url, "failed", note=str(e))
            return None

    def table_scrape(self, src: dict):
        sid, url = src["id"], src["url"]
        csv_path = ROOT / src["output_csv"]
        if self.skip_existing and csv_path.exists() and csv_path.stat().st_size > 0:
            self.record(sid, url, "skipped", path=csv_path, note="CSV exists")
            rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        else:
            try:
                r = self.fetch(url)
                soup = parse_html(r.text)
                rows = scrape_tables(soup, url)
                if not rows:
                    raise RuntimeError("no table rows found")
                write_csv(csv_path, rows, sid, url)
                self.record(sid, url, "downloaded", csv_path.read_bytes(), csv_path,
                            note=f"{len(rows)} rows -> {csv_path.name}")
            except Exception as e:
                self.record(sid, url, "failed", note=str(e))
                rows = []
            # Keep the page's prose (notes, dates) too; tables are already in the CSV.
            md_out = RAW_HTML / src["agent"] / f"{sid}.md"
            if not (self.skip_existing and md_out.exists()):
                self.save_page(f"{sid}_page", url, src["title"], md_out, drop_tables=True)

        # Download every PDF linked from the table rows (the QCO notifications).
        links = list(dict.fromkeys(
            normalize_url(l) for row in rows
            for l in (row.get("qco_pdf_url") or "").split(" | ") if is_pdf_link(l)))
        for link, slug in qco_slugs(links).items():
            if PAID_STANDARD.search(unquote(link)):
                self.record(sid, link, "skipped", note="looks like a paid ISO/IEC standard")
                continue
            self.pdf(f"qco_{slug}", link, RAW_PDF / "product_qco" / f"qco_{slug}.pdf")


# ---------- pure functions (tested in tests/test_download.py) ----------
def parse_html(text: str) -> BeautifulSoup:
    # BIS pages have broken markup that lxml gives up on; html5lib parses it like a browser.
    return BeautifulSoup(text, "html5lib")


def main_content(soup: BeautifulSoup):
    for sel in [".who_we_area", "#skip-to-main-content", "main", "article", ".entry-content", "#content"]:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 50:
            return el
    return soup.body or soup


def page_markdown(soup: BeautifulSoup, base_url: str, drop_tables=False) -> str:
    content = main_content(soup)
    content = BeautifulSoup(str(content), "html5lib")  # work on a copy
    junk = "script, style, noscript, nav, header, footer, form, iframe, .about_client, [class*=breadcrumb], .post-modified-info"
    for el in content.select(junk):
        el.decompose()
    for lst in content.select("ol, ul"):  # breadcrumb rendered as a list: Home / Section / Page
        first = lst.find("li")
        if first and first.get_text(strip=True) == "Home":
            lst.decompose()
    if drop_tables:
        for el in content.select("table"):
            el.decompose()
    for a in content.find_all("a", href=True):
        a["href"] = urljoin(base_url, a["href"])
    md = markdownify(str(content), heading_style="ATX", strip=["img"])
    md = re.sub(r"\n\s*\n\s*\n+", "\n\n", md)
    # drop a leading "Home / Section / Page" breadcrumb if it survived as plain text
    md = re.sub(r"^\s*\[?Home\]?[^\n]*(\n\s*/\s*\n[^\n]*)+\n", "", md)
    return md.strip()


def same_section_links(soup: BeautifulSoup, url: str) -> list[tuple[str, str]]:
    """Sibling pages one level deep: links whose path shares this page's parent path."""
    page = urlparse(url)
    parent = page.path.rstrip("/").rsplit("/", 1)[0] + "/"
    found, out = set(), []
    for a in soup.find_all("a", href=True):
        link = urlparse(urljoin(url, a["href"]))
        if link.netloc != page.netloc or not link.path.startswith(parent):
            continue
        rest = link.path[len(parent):].strip("/")
        if not rest or "/" in rest or link.path.rstrip("/") == page.path.rstrip("/"):
            continue  # the section index itself, deeper pages, or this page
        if link.path.lower().endswith((".pdf", ".jpg", ".png", ".zip", ".doc", ".docx")):
            continue
        clean = link._replace(query="lang=en", fragment="").geturl()
        if clean not in found:
            found.add(clean)
            out.append((clean, a.get_text(" ", strip=True)))
    return out


HEADER_MAP = [  # (regex on header text, canonical column)
    (r"^(s\.?\s*no|sr\.?\s*no|sl\.?\s*no|serial)", "s_no"),
    (r"\bis\b.*\bno|is number|indian standard|^standard", "is_number"),
    (r"notification|quality control order|\bqco\b|order|gazette", "qco_title"),
    (r"product|item|goods", "product"),
]


def canonical_header(text: str, used: set) -> str:
    t = text.strip().lower()
    for pattern, name in HEADER_MAP:
        if re.search(pattern, t) and name not in used:
            return name
    base = slugify(t)[:40] or "col"
    name, i = base, 2
    while name in used:
        name, i = f"{base}_{i}", i + 1
    return name


def expand_table(table) -> list[list[tuple[str, list[str], int]]]:
    """Return rows as lists of (text, links, own_cell_count) with rowspan/colspan expanded."""
    grid, pending = [], {}  # pending: col -> [remaining_rows, text, links]
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"], recursive=False)
        row, col = [], 0

        def fill_pending():
            nonlocal col
            while col in pending:
                p = pending[col]
                row.append((p[1], p[2]))
                p[0] -= 1
                if p[0] == 0:
                    del pending[col]
                col += 1

        for c in cells:
            fill_pending()
            text = c.get_text(" ", strip=True)
            links = [a["href"] for a in c.find_all("a", href=True)]
            colspan = int(re.sub(r"\D", "", c.get("colspan", "1")) or 1)
            rowspan = int(re.sub(r"\D", "", c.get("rowspan", "1")) or 1)
            for _ in range(colspan):
                row.append((text, links))
                if rowspan > 1:
                    pending[col] = [rowspan - 1, text, links]
                col += 1
        fill_pending()
        while pending and col <= max(pending):  # spans hanging past the last own cell
            if col in pending:
                fill_pending()
            else:
                row.append(("", []))
                col += 1
        grid.append([(t, l, len(cells)) for t, l in row])
    return grid


def scrape_tables(soup: BeautifulSoup, base_url: str) -> list[dict]:
    content = main_content(soup)
    tables = [t for t in content.find_all("table")
              if not t.find("table") and not t.find_parent(class_="mobile")]
    rows, seen_tables, seen_rows = [], set(), set()
    for table in tables:
        sig = hashlib.md5(table.get_text(" ", strip=True).encode()).hexdigest()
        if sig in seen_tables:  # BIS pages repeat the same table (e.g. per tab)
            continue
        seen_tables.add(sig)
        grid = expand_table(table)
        if len(grid) < 2:
            continue
        header_row = next((r for r in grid if len(r) >= 2), None)
        if header_row is None:
            continue
        used: set = set()
        headers = []
        for text, _, _ in header_row:
            h = canonical_header(text, used)
            used.add(h)
            headers.append(h)
        category = ""
        for r in grid[grid.index(header_row) + 1:]:
            texts = [t for t, _, _ in r]
            # Group heading: first cell spans 2+ columns (it may share the row with the first cell
            # of a new rowspan QCO column). Footnotes like "* Since revised as ..." are skipped.
            if len(texts) >= 2 and texts[0] and texts[0] == texts[1] and not re.match(r"^\d+\.?$", texts[0]):
                if not texts[0].startswith("*"):
                    category = texts[0]
                continue
            if not any(texts):
                continue
            rec = {"category": category}
            links = []
            for i, (text, cell_links, _) in enumerate(r[: len(headers)]):
                rec[headers[i]] = text
                links += [urljoin(base_url, l) for l in cell_links]
            rec["qco_pdf_url"] = " | ".join(dict.fromkeys(l for l in links if not l.startswith(("mailto:", "javascript:"))))
            # BIS pages repeat the table (desktop, older copy, mobile); the first copy is the most current.
            key = (rec.get("is_number", ""), rec.get("product", ""), rec.get("s_no", "")) if (rec.get("is_number") or rec.get("product")) else tuple(sorted(rec.items()))
            if key not in seen_rows:
                seen_rows.add(key)
                rows.append(rec)
    return rows


def write_csv(path: Path, rows: list[dict], sid: str, url: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    preferred = ["s_no", "category", "is_number", "product", "qco_title", "qco_pdf_url"]
    extra = sorted({k for r in rows for k in r} - set(preferred))
    fields = [f for f in preferred if any(f in r for r in rows)] + extra + ["source_id", "source_url", "date_downloaded"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({**r, "source_id": sid, "source_url": url, "date_downloaded": TODAY})


def normalize_url(url: str) -> str:
    """bis.gov.in and www.bis.gov.in serve the same files."""
    u = urlparse(url)
    return u._replace(netloc="www.bis.gov.in").geturl() if u.netloc == "bis.gov.in" else url


def qco_slugs(links: list[str]) -> dict[str, str]:
    """File slug per link; different files with the same name get a short hash suffix."""
    stems = {l: slugify(Path(unquote(urlparse(l).path)).stem) for l in links}
    counts: dict[str, int] = {}
    for st in stems.values():
        counts[st] = counts.get(st, 0) + 1
    return {l: st if counts[st] == 1 else f"{st}_{hashlib.md5(l.encode()).hexdigest()[:6]}"
            for l, st in stems.items()}


def is_pdf_link(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".pdf")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--priority", type=int, default=1, help="download sources with priority <= this")
    ap.add_argument("--only", nargs="*", help="only these source ids")
    args = ap.parse_args()

    cfg = yaml.safe_load((DATA / "sources.yaml").read_text())
    d = Downloader(cfg.get("download_rules", {}))
    sources = [s for s in cfg["sources"] if s.get("priority", 1) <= args.priority]
    if args.only:
        sources = [s for s in sources if s["id"] in args.only]
    print(f"Downloading {len(sources)} sources (priority <= {args.priority})")
    for s in sources:
        print(f"- {s['id']} ({s['type']})")
        try:
            if s["type"] == "pdf":
                d.pdf(s["id"], s["url"], RAW_PDF / s["agent"] / f"{s['id']}.pdf")
            elif s["type"] == "html":
                d.html(s)
            elif s["type"] == "table_scrape":
                d.table_scrape(s)
            else:
                d.record(s["id"], s["url"], "failed", note=f"unknown type {s['type']}")
        except Exception as e:  # on_failure: log and continue
            d.record(s["id"], s["url"], "failed", note=f"unexpected: {e}")
    d.log_file.close()
    c = d.counts
    print(f"\nSummary: downloaded={c['downloaded']} skipped={c['skipped']} failed={c['failed']}")
    print(f"Log: {LOG_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
