import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from chunk import MAX_TOKENS, chunk_document, n_tokens, row_text  # noqa: E402
from parse import clean_page, detect_lang, doc_type_for, is_garbled_hindi, strip_repeated_lines  # noqa: E402


def doc(pages):
    return {"source_id": "bis_act_2016", "title": "BIS Act, 2016", "url": "https://x/act.pdf",
            "agent": "law", "doc_type": "act", "date_downloaded": "2026-09-26", "pages": pages}


def test_splits_on_sections_and_keeps_pages():
    body1 = "CHAPTER IV\nSTANDARD MARK\n" + "Intro text. " * 150
    body2 = ("17. Prohibition to manufacture, sell, etc.\n(1) No person shall manufacture " + "goods. " * 100
             + "\n29. Penalty for contravention\n(1) Whoever contravenes shall be punishable. " * 1)
    chunks = chunk_document(doc([{"page": 9, "text": body1, "lang": "en"},
                                 {"page": 10, "text": body2, "lang": "en"}]))
    sections = [c["section"] for c in chunks]
    assert any(s.startswith("17. Prohibition") for s in sections)
    c17 = next(c for c in chunks if c["section"].startswith("17."))
    assert c17["page"] == 10
    assert chunks[0]["page"] == 9 and chunks[0]["chunk_id"] == "bis_act_2016::0000"
    assert set(chunks[0]) >= {"chunk_id", "source_id", "title", "url", "agent", "doc_type", "page",
                              "section", "lang", "text", "date_downloaded"}


def test_long_sections_are_capped_with_overlap():
    text = "Rule 5 Grant of licence\n" + " ".join(f"Sentence number {i} about licences." for i in range(900))
    chunks = chunk_document(doc([{"page": 1, "text": text, "lang": "en"}]))
    assert len(chunks) > 1
    assert all(n_tokens(c["text"]) <= MAX_TOKENS + 20 for c in chunks)
    tail = chunks[0]["text"][-60:]
    assert tail.split(".")[-2].strip() in chunks[1]["text"]  # overlap carried over


def test_cleaning():
    assert clean_page("manufac-\nture of goods") == "manufacture of goods"
    assert "GAZETTE" not in clean_page("THE GAZETTE OF INDIA : EXTRAORDINARY\nReal text here")
    pages = [f"BIS Rules header\nBody {i}\nPage footer" for i in range(5)]
    assert all("header" not in p and "footer" not in p for p in strip_repeated_lines(pages))
    assert detect_lang("भारतीय मानक ब्यूरो अधिनियम") == "hi" and detect_lang("Bureau of Indian Standards") == "en"
    assert is_garbled_hindi("िासी पररर्ि का गठि " * 10 + "ि ब्यक पदेन " * 10)
    assert not is_garbled_hindi("भारतीय मानक ब्यूरो अधिनियम के अंतर्गत " * 10)


def test_doc_types():
    assert doc_type_for("bis_act_2016", "Bureau of Indian Standards Act, 2016", "pdf") == "act"
    assert doc_type_for("bis_rules_2018", "BIS Rules, 2018", "pdf") == "rule"
    assert doc_type_for("ca_regulations_2018", "BIS (Conformity Assessment) Regulations, 2018", "pdf") == "regulation"
    assert doc_type_for("qco_so_no_191_e", "Cement (Quality Control) Order", "pdf") == "qco"
    assert doc_type_for("cert_faq", "Product Certification FAQ", "html") == "faq"
    assert doc_type_for("cert_fee", "Product Certification Fee", "html") == "page"


def test_product_row_text():
    row = {"product": "Sulphate Resisting Portland Cement", "is_number": "IS 12330",
           "category": "Cement", "qco_title": "1. Cement (Quality Control)Order, 2003 S.O. No. 191(E)",
           "qco_pdf_url": "https://www.bis.gov.in/SO-No-191(E).pdf"}
    text = row_text(row, "Scheme I (ISI mark)")
    assert text.startswith("Product: Sulphate Resisting Portland Cement | IS 12330 | Scheme I")
    assert "QCO: Cement (Quality Control)Order, 2003 S.O. No. 191(E)" in text
    assert "PDF: https://www.bis.gov.in/SO-No-191(E).pdf" in text
