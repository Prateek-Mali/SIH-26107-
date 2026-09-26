"""Rule-based query understanding: no LLM call.

    normalize(q)       IBS/BSI/B.I.S -> BIS, "is1293"/"IS-1293"/"IS:1293" -> "IS 1293"
    detect_lang(q)     "hi" if Devanagari, else "en"
    expansions(q)      up to 3 extra search queries from a synonym map
    detect_scheme(q)   the certification scheme the question is about, or None
    source_boosts(q)   source_id prefixes / doc types to prefer for this question
"""
import re

ALIASES = [
    (re.compile(r"\b(?:ibs|bsi|b\.\s*i\.\s*s\.?|bureau of indian standards?)(?=\W|$)", re.I), "BIS"),
    (re.compile(r"भारतीय\s*मानक\s*ब्यूरो|बीआईएस"), "BIS"),
]


def normalize(q: str) -> str:
    q = " ".join(q.split())
    for pat, rep in ALIASES:
        q = pat.sub(rep, q)
    # "is1293" / "IS-1293" / "IS:1293" -> "IS 1293" (but not "what is 17%")
    q = re.sub(r"\b(?:IS|is)[\-:]?(\d{3,5})\b", r"IS \1", q)
    q = re.sub(r"\bIS\s*[\-:]\s*(\d{2,5})\b", r"IS \1", q)
    return q


def detect_lang(q: str) -> str:
    return "hi" if re.search(r"[ऀ-ॿ]", q) else "en"


# (pattern in the question, extra search queries). Order matters: the first 3 matches are used.
EXPANSIONS = [
    (r"\b(document|papers?|checklist|check-list|what (?:do i|to) submit)\w*|दस्तावेज़|कागजात",
     ["check-list for application documents to be submitted by applicant for BIS licence",
      "documents to be enclosed with application for grant of licence Form"]),
    (r"\b(register|registration|licen[cs]e|apply|application|get started|start|new business)\w*|पंजीकरण|लाइसेंस",
     ["grant of licence procedure application Scheme-I", "application for grant of licence option-1 option-2 simplified procedure"]),
    (r"\b(fee|fees|cost|charges?|payment)\b|शुल्क|फीस",
     ["application fee annual licence fee marking fee inspection fee", "minimum marking fee testing charges"]),
    (r"\b(penalt\w*|punish\w*|fine|offen[cs]e|jail|imprison\w*|misuse|fake|without (?:a )?licen[cs]e)\b|जुर्माना|दंड|सज़ा",
     ["penalty for contravention Section 29 punishable imprisonment fine", "improper use of Standard Mark Section 17 contravention"]),
    (r"\b(change|update|modify|amend)\w*.*\b(detail|name|address|owner\w*|premises|location|licen[cs]e|brand|scope)\w*|change of address|change in name",
     ["change in scope of licence change of name address ownership premises", "inclusion of additional varieties change in licence details"]),
    (r"\b(renew\w*)\b|नवीनीकरण", ["renewal of licence application Form-XII fees validity", "deferment of renewal of licence"]),
    (r"\b(suspen\w*|cancel\w*|revok\w*|non-?conform\w*|stop marking)\b",
     ["suspension of licence cancellation of licence non-conformity", "stop marking unsatisfactory performance action"]),
    (r"\b(reject\w*|objection|deficien\w*|incomplete|not met|not eligible|eligib\w*)\b",
     ["rejection of application deficiencies communicated to applicant time to respond", "application closed if deficiencies not rectified within days"]),
    (r"\b(time|timeline|days|how long|duration|period)\b",
     ["time period days for grant of licence processing", "time limit to respond to deficiencies days"]),
    (r"\b(simplified)\b", ["simplified procedure grant of licence option-2 list of products"]),
    (r"\b(variet\w*|model\w*|additional product)\b", ["inclusion of additional varieties in licence change in scope"]),
    (r"\b(hallmark\w*|huid|jewel\w*|gold|silver|carat|karat)\b|हॉलमार्क|सोना|आभूषण",
     ["hallmarking HUID jeweller registration assaying and hallmarking centre", "how to verify HUID BIS CARE app"]),
    (r"\b(complain\w*|grievance|consumer|fake isi|verify|check (?:a|the) (?:mark|licen[cs]e))\w*|शिकायत",
     ["consumer complaint BIS CARE app online complaint registration", "verify licence number BIS CARE"]),
    (r"\b(foreign|import\w*|overseas|fmcs|abroad)\b|विदेशी|आयात",
     ["Foreign Manufacturers Certification Scheme FMCS application Authorized Indian Representative"]),
    (r"\b(crs|electronic\w*|it goods|mobile|laptop|led|charger|power bank|r-?number|compulsory registration)\b",
     ["Compulsory Registration Scheme Scheme-II electronics and IT goods registration", "Electronics and Information Technology Goods Requirement of Compulsory Registration Order"]),
    (r"\b(scheme|schemes)\b.*\b(compare|comparison|difference|differ|vs|versus|types)\b|\b(compare|difference|types of)\b.*\bschemes?\b",
     ["conformity assessment schemes Scheme-I Scheme-II Scheme-IV Scheme-X Schedule-II"]),
    (r"\b(what is bis|about bis|purpose|role|functions?)\b",
     ["Bureau of Indian Standards national standards body functions of Bureau", "product certification overview BIS"]),
]


def expansions(q: str, limit: int = 3) -> list[str]:
    out = []
    for pat, extra in EXPANSIONS:
        if re.search(pat, q, re.I):
            for e in extra:
                if e not in out:
                    out.append(e)
        if len(out) >= limit:
            break
    return out[:limit]


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
    """source_id prefixes that should rank higher for this question."""
    ql = q.lower()
    boosts = []
    if re.search(r"penalt|punish|offen[cs]e|imprison|fine\b|section \d+|\bact\b|seiz|compound", ql):
        boosts += ["bis_act_2016", "bis_rules_2018"]
    if re.search(r"document|checklist|check-list|submit", ql):
        boosts += ["application_checklist", "guide_grant_of_licence"]
    if re.search(r"renew", ql):
        boosts += ["guide_renewal"]
    if re.search(r"change|variet|scope|address|name|owner", ql):
        boosts += ["guide_change_in_scope"]
    if re.search(r"suspen|cancel|non-?conform|stop marking", ql):
        boosts += ["guide_non_conformity", "guide_unsatisfactory_performance"]
    if re.search(r"grant|apply|application|process|steps|get started|new business|option|objection|deficien|reject", ql):
        boosts += ["guide_grant_of_licence", "cert_faq", "cert_process", "application_checklist"]
    if re.search(r"fee|cost|charge", ql):
        boosts += ["cert_fee", "cert_faq", "fmcs_fee"]
    if re.search(r"surveillance|inspection", ql):
        boosts += ["guide_factory_surveillance", "guide_market_surveillance"]
    if re.search(r"hallmark|huid|jewel|gold|हॉलमार्क", ql):
        boosts += ["hm_faq_general", "hm_overview", "hm_jewellers_guidelines", "hm_regulations"]
    if re.search(r"complain|consumer|verify|care app|शिकायत", ql):
        boosts += ["consumer_complaint", "consumer_protection", "bis_care_app_page"]
    if re.search(r"foreign|import|fmcs", ql):
        boosts += ["fmcs_"]
    return list(dict.fromkeys(boosts))
