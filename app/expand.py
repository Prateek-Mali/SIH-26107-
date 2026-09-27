"""Rule-based query understanding: no LLM call.

    normalize(q)       IBS/BSI/B.I.S -> BIS, "is1293"/"IS-1293"/"IS:1293" -> "IS 1293"
    detect_lang(q)     "hi" if Devanagari, else "en"
    expansions(q)      up to 3 extra search queries from a synonym map
    detect_scheme(q)   the certification scheme the question is about, or None
    source_boosts(q)   source_id prefixes / doc types to prefer for this question
"""
import re
import unicodedata
from functools import lru_cache

ALIASES = [
    (re.compile(r"\b(?:ibs|bsi|b\.\s*i\.\s*s\.?|bureau of indian standards?)(?=\W|$)", re.I), "BIS"),
    (re.compile(r"भारतीय\s*मानक\s*ब्यूरो|बीआईएस"), "BIS"),
]


def normalize(q: str) -> str:
    q = unicodedata.normalize("NFC", " ".join(q.split()))
    for pat, rep in ALIASES:
        q = pat.sub(rep, q)
    # "is1293" / "IS-1293" / "IS:1293" -> "IS 1293" (but not "what is 17%")
    q = re.sub(r"\b(?:IS|is)[\-:]?(\d{3,5})\b", r"IS \1", q)
    q = re.sub(r"\bIS\s*[\-:]\s*(\d{2,5})\b", r"IS \1", q)
    return q


def detect_lang(q: str) -> str:
    return "hi" if re.search(r"[ऀ-ॿ]", q) else "en"


def expansions(q: str, limit: int = 3) -> list[str]:
    """No hand-written query expansions any more (they were tuned to test questions); the agent writes its own
    search queries. Kept as a no-op so the fallback pipeline still runs."""
    return []


def detect_scheme(q: str) -> str | None:
    """The scheme a question is about. None = do not filter (law, comparisons, general)."""
    ql = q.lower()
    explicit = re.search(r"scheme[\s\-–]*(x|10|iv|4|iii|3|ii|2|i|1)\b", ql)
    if re.search(r"\b(compare|comparison|difference|differ|versus|vs\.?|types of|all schemes|which scheme)\b", ql):
        return None
    if explicit:
        v = explicit.group(1)
        return {"1": "I", "2": "II", "3": "III", "4": "IV", "10": "X"}.get(v, v.upper())
    if re.search(r"hallmark|huid|jewel|gold|silver|assay|हॉलमार्क|सोना", ql):
        return "Hallmarking"
    if re.search(r"\b(foreign|overseas|fmcs|abroad|import\w*)\b|विदेशी|आयात", ql):
        return "FMCS"
    if re.search(r"\b(crs|electronic\w*|it goods|r-?number|compulsory registration|registration scheme)\b", ql):
        return "II"
    if re.search(r"\b(licen[cs]e|apply|application|get started|new business|manufacturer|isi|documents?|register\w*|"
                 r"fee|renew\w*|surveillance|suspen\w*|cancel\w*|varieties|change in scope|objection|inspection)\b"
                 r"|प्रमाणन|लाइसेंस|पंजीकरण|आवेदन", ql):
        return "I"  # default for Indian manufacturers asking about the licence process
    return None


def source_boosts(q: str) -> list[str]:
    """Removed: a hand-written map from question words to specific documents (tuned to test questions)."""
    return []


# Rule-based Hindi -> English keywords (no LLM call). Enough for the rules above to fire on Hindi questions;
# the bge-m3 embeddings handle the Hindi text itself.
HINDI_WORDS = {
    "सज़ा": "penalty", "सजा": "penalty", "दंड": "penalty", "जुर्माना": "fine penalty", "कारावास": "imprisonment",
    "लाइसेंस": "licence", "अनुज्ञप्ति": "licence", "नवीनीकरण": "renewal", "आवेदन": "application", "शुल्क": "fee",
    "फीस": "fee", "दस्तावेज़": "documents", "दस्तावेज": "documents", "कागजात": "documents", "प्रमाणन": "certification",
    "अनिवार्य": "compulsory", "ज़रूरी": "compulsory", "जरूरी": "compulsory", "पंजीकरण": "registration",
    "हॉलमार्किंग": "hallmarking", "हॉलमार्क": "hallmark", "सोना": "gold", "सोने": "gold", "चांदी": "silver",
    "आभूषण": "jewellery", "गहने": "jewellery", "जौहरी": "jeweller", "शिकायत": "complaint", "उपभोक्ता": "consumer",
    "विदेशी": "foreign", "आयात": "import", "निर्माता": "manufacturer", "प्रक्रिया": "process", "कैसे": "how",
    "क्या है": "what is", "मानक": "standard", "मार्क": "mark", "चेक": "check verify", "सत्यापित": "verify",
    "रद्द": "cancellation", "निलंबन": "suspension", "परीक्षण": "testing", "नमूना": "sample",
}


def to_english(q: str) -> str:
    """Hindi question -> English keywords from HINDI_WORDS (plus any Latin words kept as they are)."""
    words = [en for hi, en in HINDI_WORDS.items() if hi in q]
    latin = re.findall(r"[A-Za-z][A-Za-z0-9.\-/()]*|\d+", q)
    return " ".join(dict.fromkeys(latin + words))
