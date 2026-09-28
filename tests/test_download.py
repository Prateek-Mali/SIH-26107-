import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from download import (  # noqa: E402
    BLOCKED_URL, PAID_STANDARD, is_pdf_link, page_markdown, parse_html,
    same_section_links, scrape_tables, slugify,
)

TABLE_PAGE = """
<html><body><div class="who_we_area"><table>
<tr><td>Sr No.</td><td>IS No.</td><td>Product</td><td>For Notification Details</td></tr>
<tr><td colspan="4">Cement (any variety) such as</td></tr>
<tr><td>1.</td><td>IS 12330</td><td>Sulphate Resisting Portland Cement</td>
    <td rowspan="2"><a href="/QCOrder/SO-No-191(E).pdf">Cement (Quality Control) Order, 2003 S.O. 191(E)</a>
    <a href="/QCOrder/SO-No-2(E).pdf">Amendment</a></td></tr>
<tr><td>2.</td><td>IS 12600</td><td>Low heat Portland Cement</td></tr>
</table>
<div class="mobile"><table><tr><td>Sr No.</td><td>IS No.</td></tr><tr><td>9.</td><td>IS 999</td></tr></table></div>
</div></body></html>
"""


def test_table_scrape_expands_rowspan_and_keeps_links():
    rows = scrape_tables(parse_html(TABLE_PAGE), "https://www.bis.gov.in/scheme-1/")
    assert [r["is_number"] for r in rows] == ["IS 12330", "IS 12600"]  # mobile copy skipped
    assert rows[1]["qco_title"].startswith("Cement (Quality Control) Order")  # from rowspan
    assert rows[0]["category"] == "Cement (any variety) such as"
    assert rows[1]["qco_pdf_url"] == (
        "https://www.bis.gov.in/QCOrder/SO-No-191(E).pdf | https://www.bis.gov.in/QCOrder/SO-No-2(E).pdf")


def test_page_markdown_drops_menu_and_breadcrumb():
    html = """<html><body><header>TOP</header><div id="skip-to-main-content">
    <div class="about_client"><a href="/a">Left menu</a></div>
    <div class="who_we_area"><ul><li>Home</li><li>/</li><li>Page</li></ul>
    <h1>Fee</h1><p>Application fee is Rs 1000. <a href="/fee.pdf">Fee PDF</a></p></div></div>
    <footer>BOTTOM</footer></body></html>"""
    md = page_markdown(parse_html(html), "https://www.bis.gov.in/x/")
    assert "# Fee" in md and "Rs 1000" in md
    assert "https://www.bis.gov.in/fee.pdf" in md
    for junk in ("TOP", "BOTTOM", "Left menu", "Home"):
        assert junk not in md


def test_same_section_links_one_level():
    html = """<a href="/hm/faqs/general/">g</a><a href="/hm/faqs/huid/?lang=en">h</a>
    <a href="/hm/faqs/huid/deeper/">deep</a><a href="/other/x/">o</a><a href="/hm/faqs/">idx</a>
    <a href="/hm/faqs/doc.pdf">pdf</a>"""
    links = [u for u, _ in same_section_links(parse_html(html), "https://www.bis.gov.in/hm/faqs/general/?lang=en")]
    assert links == ["https://www.bis.gov.in/hm/faqs/huid/?lang=en"]


def test_guards_and_helpers():
    assert BLOCKED_URL.search("https://www.manakonline.in/login.do")
    assert BLOCKED_URL.search("https://standardsbis.bsbedge.com/x")
    assert PAID_STANDARD.search("IS/ISO 9001 : 2015.pdf")
    assert not PAID_STANDARD.search("SO-No-191(E).pdf")
    assert is_pdf_link("https://x/a/B.PDF") and not is_pdf_link("https://x/a/page/")
    assert slugify("SO-No-191(E)") == "so_no_191_e"


def test_qco_slugs_handle_duplicate_names():
    from download import normalize_url, qco_slugs
    assert normalize_url("https://bis.gov.in/a.pdf") == "https://www.bis.gov.in/a.pdf"
    s = qco_slugs(["https://www.bis.gov.in/2023/Gazette-Notification.pdf",
                   "https://www.bis.gov.in/2024/Gazette-Notification.pdf",
                   "https://www.bis.gov.in/SO-No-191(E).pdf"])
    assert len(set(s.values())) == 3
    assert s["https://www.bis.gov.in/SO-No-191(E).pdf"] == "so_no_191_e"


def test_category_row_sharing_a_rowspan_cell():
    html = """<div class="who_we_area"><table>
    <tr><td>Sr No.</td><td>IS No.</td><td>Product</td><td>Notification</td></tr>
    <tr><td colspan="3">Feeding Bottles</td><td rowspan="3">Feeding Bottles QCO S.O. 1(E)</td></tr>
    <tr><td>1.</td><td>IS 14625</td><td>Plastic feeding bottles</td></tr>
    <tr><td colspan="3">* Since revised as IS/IEC 60898</td></tr>
    <tr><td>2.</td><td>IS 11111</td><td>Teats</td><td>Other QCO</td></tr>
    </table></div>"""
    rows = scrape_tables(parse_html(html), "https://x/")
    assert [(r["category"], r["qco_title"]) for r in rows] == [
        ("Feeding Bottles", "Feeding Bottles QCO S.O. 1(E)"), ("Feeding Bottles", "Other QCO")]
