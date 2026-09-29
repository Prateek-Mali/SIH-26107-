"""Step 1: understand the user (one small, fast LLM call; JSON out).

    understand(question, history, profile) -> {intent, user_role, user_goal, product_or_topic, sub_questions,
                                               standalone_question, language}

The profile (role, product, goal) is carried across turns of a session, so "and how much does it cost?"
becomes a standalone question about the same product and scheme.
Deterministic: JSON mode with a schema (Gemini response schema / Groq json_object), temperature 0, and the reply
is validated. If two attempts fail, a rule-based understanding is used and logged (data/understand_failures.jsonl).
"""
import json
import re
import time

from app import config, llm
from app.expand import detect_lang, normalize

INTENTS = ["basic", "advice", "process", "explain", "check_requirement", "compare", "problem_solving", "quick_fact"]
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
Intent guide: basic = a simple "what is X / what does X mean / difference between X and Y / who are you";
advice = "what should I do / guide me"; process = "how to / steps"; explain = "what is";
check_requirement = "is it compulsory / do I need"; compare = "difference / vs"; problem_solving = something went
wrong (objection, rejection, no HUID, fake mark); quick_fact = one number or name.
Role guide: makes goods in India = manufacturer; imports goods = importer; makes goods abroad = foreign_manufacturer;
buyer with a problem = consumer. Keep IS numbers and official terms exactly."""


SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": INTENTS},
        "user_role": {"type": "string", "enum": ROLES},
        "user_goal": {"type": "string"},
        "product_or_topic": {"type": "string"},
        "standalone_question": {"type": "string"},
        "sub_questions": {"type": "array", "items": {"type": "string"}},
        "product_attrs": {"type": "object", "properties": {
            "product_type": {"type": "string"}, "material": {"type": "string"}, "use": {"type": "string"},
            "electrical": {"type": "boolean"}, "electronics_it": {"type": "boolean"},
            "precious_metal": {"type": "boolean"}, "maker_location": {"type": "string"}, "role": {"type": "string"}}},
    },
    "required": ["intent", "user_role", "user_goal", "product_or_topic", "standalone_question", "sub_questions"],
}
FAIL_LOG = config.ROOT / "data" / "understand_failures.jsonl"


def validate(out) -> str | None:
    """None if the reply matches SCHEMA, else what is wrong."""
    if not isinstance(out, dict):
        return "not a JSON object"
    for k in SCHEMA["required"]:
        if k not in out:
            return f"missing {k}"
    if out["intent"] not in INTENTS:
        return f"bad intent {out['intent']!r}"
    if out["user_role"] not in ROLES:
        return f"bad user_role {out['user_role']!r}"
    if not isinstance(out["standalone_question"], str) or not out["standalone_question"].strip():
        return "empty standalone_question"
    if not isinstance(out["sub_questions"], list) or not all(isinstance(x, str) for x in out["sub_questions"]):
        return "sub_questions is not a list of strings"
    if "product_attrs" in out and not isinstance(out["product_attrs"], dict):
        return "product_attrs is not an object"
    return None


def _call_json(prompt: str) -> tuple[dict | None, str, str]:
    """(parsed reply or None, provider, error)."""
    try:
        text, provider = llm.generate_with_provider(prompt, system=SYSTEM, temperature=0.0, max_tokens=1200,
                                                    model=config.GEMINI_ROUTER_MODEL, groq_model=config.GROQ_SMALL_MODEL,
                                                    schema=SCHEMA)
    except Exception as e:
        return None, "none", f"{type(e).__name__}: {str(e)[:120]}"
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        out = json.loads(text[text.find("{"): text.rfind("}") + 1])
    except ValueError as e:
        return None, provider, f"invalid JSON: {e}"
    err = validate(out)
    return (None, provider, err) if err else (out, provider, "")


def is_followup(q: str) -> bool:
    """'and how much does it cost?', 'what about renewal?', 'fees?' continue the previous topic."""
    return (len(q.split()) <= 3 or bool(re.match(r"^\s*(and|also|what about|how about|how much|then|so|same)\b", q, re.I))
            or bool(re.search(r"\b(it|this|that|them|those)\b", q, re.I) and len(q.split()) <= 10))


def _rules(q: str, profile: dict) -> dict:
    """Fallback when the model is unavailable."""
    ql = q.lower()
    from app.expand import is_basic
    intent = ("basic" if is_basic(q) else "compare" if re.search(r"difference|compare|vs\b|versus", ql) else
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
    if profile.get("role"):  # session memory keys (app/memory.py) -> the keys used here
        profile.setdefault("user_role", profile["role"])
    if profile.get("product"):
        profile.setdefault("product_or_topic", profile["product"])
    followup = is_followup(q)
    hist = [t for t in (history or []) if t.get("content")][-7:]
    last_answer = next((t for t in reversed(hist) if t["role"] == "assistant"), None)
    convo = "\n".join(f"{t['role']}: " + ((t.get("full") or t["content"])[:2500] if t is last_answer else t["content"][:600])
                      for t in hist)
    known = {k: v for k, v in profile.items() if v and k not in ("user_goal",)}
    prompt = (f"Known profile of this user: {json.dumps(known, ensure_ascii=False)}\n"
              + (f"Earlier conversation:\n{convo}\n" if convo else "") + f"\nMessage: {q}\n"
              + ("Rewrite rule: if the message depends on the conversation (it, that, same, 'step 2', 'and the fee?', "
                 "'in Hindi'), standalone_question must name the product, IS number and scheme from the conversation "
                 "or profile. 'step N' means item N of the NUMBERED list in the assistant's last answer (not a bullet): "
                 "name that item. 'the same' / 'that' / 'it' means the whole topic of the last answer. "
                 "Keep a general question general: 'and the fee?' -> 'What is the BIS licence fee (application, "
                 "annual, marking fee) under Scheme I for <product>?'. If it is a new self-contained question, "
                 "keep it as it is." if convo else ""))
    out, provider, errors = None, "rules", []
    for attempt in range(2):
        out, provider, err = _call_json(prompt)
        if out is not None:
            break
        errors.append(err)
    if out is None:  # two failures: deterministic rules, logged
        out, provider = {}, "rules"
        print(f"[understand] using rules ({'; '.join(errors)[:160]})")
        try:
            with FAIL_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "question": q, "errors": errors},
                                   ensure_ascii=False) + "\n")
        except OSError:
            pass
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
    res["understand_ok"] = "rules-fallback" if provider == "rules" else "json"
    res["attempts"] = len(errors) + (provider != "rules")
    res["errors"] = errors
    return res
