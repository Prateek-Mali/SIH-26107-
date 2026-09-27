"""Step 1: understand the user (one small, fast LLM call; JSON out).

    understand(question, history, profile) -> {intent, user_role, user_goal, product_or_topic, sub_questions,
                                               standalone_question, language}

The profile (role, product, goal) is carried across turns of a session, so "and how much does it cost?"
becomes a standalone question about the same product and scheme. If the call fails, rules fill in.
"""
import json
import re

from app import config, llm
from app.expand import detect_lang, normalize

INTENTS = ["advice", "process", "explain", "check_requirement", "compare", "problem_solving", "quick_fact"]
ROLES = ["manufacturer", "importer", "foreign_manufacturer", "consumer", "jeweller", "lab", "student", "unknown"]

SYSTEM = f"""You analyse a user's message to a BIS (Bureau of Indian Standards) assistant. "IBS"/"BSI" means BIS.
Reply with JSON only:
{{"intent": one of {INTENTS},
 "user_role": one of {ROLES},
 "user_goal": "one line: what the user is trying to achieve",
 "product_or_topic": "the product or topic, in English",
 "standalone_question": "the message rewritten in English as a complete question. For a follow-up, ask ONLY the new
     thing, applied to the known product and scheme (e.g. after LED bulbs: 'and the cost?' -> 'What are the fees for
     CRS registration of LED bulbs?'); do not repeat the earlier question",
 "sub_questions": ["2-4 short English search questions that together cover what the user needs"],
 "product_attrs": {{"product_type": "the product in plain English, or ''", "material": "", "use": "domestic | industrial | ''",
     "electrical": true|false, "electronics_it": true|false, "precious_metal": true|false,
     "maker_location": "india | foreign | unknown", "role": "manufacturer | importer | trader | jeweller | consumer | unknown"}}}}
Intent guide: advice = "what should I do / guide me"; process = "how to / steps"; explain = "what is";
check_requirement = "is it compulsory / do I need"; compare = "difference / vs"; problem_solving = something went
wrong (objection, rejection, no HUID, fake mark); quick_fact = one number or name.
Role guide: makes goods in India = manufacturer; imports goods = importer; makes goods abroad = foreign_manufacturer;
buyer with a problem = consumer. Keep IS numbers and official terms exactly."""


def is_followup(q: str) -> bool:
    """'and how much does it cost?', 'what about renewal?', 'fees?' continue the previous topic."""
    return (len(q.split()) <= 3 or bool(re.match(r"^\s*(and|also|what about|how about|how much|then|so|same)\b", q, re.I))
            or bool(re.search(r"\b(it|this|that|them|those)\b", q, re.I) and len(q.split()) <= 10))


def _rules(q: str, profile: dict) -> dict:
    """Fallback when the model is unavailable."""
    ql = q.lower()
    intent = ("compare" if re.search(r"difference|compare|vs\b|versus", ql) else
              "problem_solving" if re.search(r"objection|reject|without huid|fake|complain|problem|sold me", ql) else
              "check_requirement" if re.search(r"\b(is|are|do|does)\b.*\b(compulsory|mandatory|need|required)", ql) else
              "advice" if re.search(r"guide|what should|what do i need|want to (start|sell|make)", ql) else
              "process" if re.search(r"how (to|do|can)|steps|process", ql) else
              "explain" if re.search(r"what is|explain|meaning", ql) else "quick_fact")
    role = ("importer" if re.search(r"import", ql) else "jeweller" if "jeweller" in ql and "my jeweller" not in ql else
            "consumer" if re.search(r"bought|sold me|my jeweller|consumer|complain", ql) else
            "manufacturer" if re.search(r"manufactur|making|make|produce|factory|start", ql) else
            profile.get("user_role", "unknown"))
    return {"intent": intent, "user_role": role, "user_goal": "", "product_or_topic": profile.get("product_or_topic", ""),
            "standalone_question": q, "sub_questions": []}


def understand(question: str, history: list[dict] | None = None, profile: dict | None = None) -> dict:
    q = normalize(question)
    profile = dict(profile or {})
    followup = is_followup(q)
    if not followup:  # a new, self-contained question: keep who the user is, not the old topic or conversation
        profile = {k: v for k, v in profile.items() if k == "user_role"}
        history = []
    convo = "\n".join(f"{t['role']}: {t['content'][:300]}" for t in (history or [])[-6:])
    known = {k: v for k, v in profile.items() if k in ("user_role", "product_or_topic", "user_goal") and v}
    prompt = (f"Known profile of this user: {json.dumps(known, ensure_ascii=False)}\n"
              + (f"Earlier conversation:\n{convo}\n" if convo else "") + f"\nMessage: {q}")
    out, provider = {}, "rules"
    try:
        text, provider = llm.generate_with_provider(prompt, system=SYSTEM, temperature=0.0, max_tokens=1200,
                                                    model=config.GEMINI_ROUTER_MODEL, groq_model=config.GROQ_SMALL_MODEL)
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        out = json.loads(text[text.find("{"): text.rfind("}") + 1])
    except Exception as e:
        print(f"[understand] using rules ({type(e).__name__}: {str(e)[:80]})")
    base = _rules(q, profile)
    res = {k: out.get(k) or base[k] for k in base}
    if res["intent"] not in INTENTS:
        res["intent"] = base["intent"]
    if res["user_role"] not in ROLES:
        res["user_role"] = base["user_role"]
    if res["user_role"] == "unknown" and profile.get("user_role"):
        res["user_role"] = profile["user_role"]  # remember who the user is across turns
    for k in ("product_or_topic", "user_goal"):
        if not res[k] and profile.get(k):
            res[k] = profile[k]
    res["sub_questions"] = [normalize(s) for s in (res["sub_questions"] or []) if isinstance(s, str)][:4]
    res["standalone_question"] = normalize(res["standalone_question"] or q)
    # safety: the rewrite must keep the official terms the user named (ISI, CRS, HUID, IS 1234 ...)
    terms = set(re.findall(r"\b(ISI|CRS|HUID|FMCS|QCO|IS \d{2,5}|Scheme[- ]?[IVX]+)\b", q, re.I))
    if not followup and any(t.lower() not in res["standalone_question"].lower() for t in terms):
        res["standalone_question"] = q
    attrs = out.get("product_attrs")
    res["product_attrs"] = attrs if isinstance(attrs, dict) else {}
    res["language"] = detect_lang(q)
    res["provider"] = provider
    return res
