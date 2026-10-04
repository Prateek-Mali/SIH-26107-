"""Rule-based query understanding: no LLM call.

    normalize(q)       IBS/BSI/B.I.S -> BIS, "is1293"/"IS-1293"/"IS:1293" -> "IS 1293"
    detect_lang(q)     "hi" if Devanagari, else "en"
    expansions(q)      up to 3 extra search queries from a synonym map
    detect_scheme(q)   the certification scheme the question is about, or None
    concept_terms(q)   related terms from the domain vocabulary (data/structured/term_graph.json)
    source_boosts(q)   source_id prefixes / doc types to prefer for this question
"""
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

ALIASES = [
    (re.compile(r"\b(?:ibs|bsi|b\.\s*i\.\s*s\.?|bureau of indian standards?)(?=\W|$)", re.I), "BIS"),
    (re.compile(r"भारतीय\s*मानक\s*ब्यूरो|बीआईएस"), "BIS"),
]


# Hinglish (Hindi in Latin letters) -> English question words
HINGLISH = [(re.compile(p, re.I), r) for p, r in [
    (r"\b(\w[\w ]{0,40}?)\s+kaise\s+(kare|karen|karein|karu|karun|kre|kren|hota hai|hoga)\b", r"how to do \1"),
    (r"\b(\w[\w ]{0,40}?)\s+(kya|kyaa)\s+(hai|hota hai|he|h)\b", r"what is \1"),
    (r"\b(kitna|kitni|kitne)\b", "how much"), (r"\bkaise\b", "how"), (r"\bkya\b", "what"),
    (r"\bkab\b", "when"), (r"\bkahan\b", "where"), (r"\bchahiye\b", "is needed"),
    (r"\s+(hai|he)(?=\s*[?.!]*\s*$)", "")]]


# the words people use -> the official term the documents use (fixed synonyms, like IBS -> BIS)
OFFICIAL = [(re.compile(r"\bISI\s*mark(?!\s*\(Standard Mark\))", re.I), "ISI mark (Standard Mark)")]


def normalize(q: str) -> str:
    q = unicodedata.normalize("NFC", " ".join(q.split()))
    for pat, rep in ALIASES + HINGLISH + OFFICIAL:
        q = pat.sub(rep, q)
    # "is1293" / "IS-1293" / "IS:1293" -> "IS 1293" (but not "what is 17%")
    q = re.sub(r"\b(?:IS|is)[\-:]?(\d{3,5})\b", r"IS \1", q)
    q = re.sub(r"\bIS\s*[\-:]\s*(\d{2,5})\b", r"IS \1", q)
    return q


BASIC = re.compile(r"^\s*(what\s+(is|are|does)\b(?!.*\b(fee|cost|penalty|time|process|procedure|steps?|documents?)\b)|"
                   r"what do(es)? .{1,40} mean|define\b|meaning of|(what is the )?difference between|who (are|made|built) you|"
                   r"are you (chatgpt|gpt|a bot|human))", re.I)


def is_basic(q: str) -> bool:
    """A basic / definition question ('what is a QCO', 'difference between BIS and ISI'): short plain answer."""
    return bool(BASIC.search(q)) and len(q.split()) <= 14


def detect_lang(q: str) -> str:
    return "hi" if re.search(r"[ऀ-ॿ]", q) else "en"


def expansions(q: str, limit: int = 3) -> list[str]:
    """No hand-written query expansions any more (they were tuned to test questions); the agent writes its own
    search queries. Kept as a no-op so the fallback pipeline still runs."""
    return []


TERM_GRAPH = Path(__file__).resolve().parent.parent / "data" / "structured" / "term_graph.json"
CONCEPT_MIN, CONCEPT_PER_TERM, CONCEPT_MAX = 0.6, 3, 6
# everyday English words carry no domain concept: never expand them
PLAIN_WORDS = set("""about above after again against already also always another anyone anything around because
before being below between both could does doing done during each either else enough ever every first from
give given gives going gone good have having here into just keep know last later less like made make many
might more most much must need needs never next only other over please really same should since some
something still such sure take tell than that their them then there these they thing think this those
though through time today under until very want wants what when where whether which while will with within
without would year years yours happen happens happened dont doesnt cant wont""".split())


@lru_cache(maxsize=1)
def _term_graph() -> dict:
    try:
        return json.loads(TERM_GRAPH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}  # not built yet (scripts/build_term_graph.py): no expansion


def concept_terms(q: str) -> list[str]:
    """Related terms by co-occurrence in the documents, for every content word of the query (same for every
    question: no per-question rules). 'objections' -> remove, removal, thirty."""
    import sys
    sys.path.insert(0, str(TERM_GRAPH.parent.parent.parent / "scripts"))
    from build_term_graph import stem

    graph, words, out = _term_graph(), [], []
    for w in re.findall(r"[a-z]{4,}", q.lower()):
        if w in PLAIN_WORDS:
            continue
        w = stem(w)
        if w not in words:
            words.append(w)
    for w in words:
        out += [t for t, s in graph.get(w, [])[:CONCEPT_PER_TERM] if s >= CONCEPT_MIN and t not in words and t not in out]
    return out[:CONCEPT_MAX]


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
