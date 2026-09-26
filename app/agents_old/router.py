"""Router: picks the specialist agents (Flash-Lite, JSON output)."""
import re
import time

from app import config, llm, prompts
from app.agents.state import State

GREETING = re.compile(r"^\s*(hi+|hello|hey|namaste|namaskar|नमस्ते|नमस्कार|good (morning|afternoon|evening)|"
                      r"thanks?( you)?|thank you|धन्यवाद|shukriya|ok(ay)?|bye)[\s!.?]*$", re.I)

# Used only when the router model fails or returns bad JSON.
KEYWORDS = {
    "law": r"\b(act|section|rule|regulation|penalt|offence|offense|punish|fine|imprison|legal|law)\w*",
    "certification": r"\b(licen[cs]e|certif|isi|crs|fmcs|scheme|fee|apply|application|registration|renew|lab|test)\w*",
    "product_qco": r"\b(qco|quality control order|compulsory|mandatory|product|is\s*\d+|s\.?o\.?\s*\d+)\w*",
    "hallmarking_consumer": r"\b(hallmark|huid|gold|silver|jewel|assay|complaint|consumer|bis care|carat|karat)\w*",
}


BIS_TERMS = re.compile(
    r"\b(bis|isi|crs|fmcs|qco|huid|hallmark\w*|indian standards?|(?-i:IS)\s*[:/\-]?\s*\d{2,5}|s\.o\.\s*\d+|"
    r"quality control order|standard mark|manak|bureau of indian standards)\b|बीआईएस|हॉलमार्क|मानक", re.I)


def heuristic_route(question: str) -> dict:
    intents = [a for a, pat in KEYWORDS.items() if re.search(pat, question, re.I)]
    hindi = bool(re.search(r"[ऀ-ॿ]", question))
    return {"intents": intents or ["certification", "product_qco"], "language": "hi" if hindi else "en",
            "is_greeting": bool(GREETING.match(question)), "out_of_scope": False, "search_query": question}


ALIASES = [
    (re.compile(r"\b(ibs|bsi|b\.\s*i\.\s*s\.?|bureau of indian standards?|bureau of indian standard)\b", re.I), "BIS"),
    (re.compile(r"भारतीय मानक ब्यूरो"), "BIS"),
]


def normalize(question: str) -> str:
    """Common misspellings of BIS (IBS, BSI, B.I.S) become BIS so search and routing find it."""
    for pat, rep in ALIASES:
        question = pat.sub(rep, question)
    return question


def route(question: str, history: list[dict] | None = None) -> dict:
    question = normalize(question)
    if GREETING.match(question):
        hindi = bool(re.search(r"[ऀ-ॿ]", question))
        return {"intents": [], "language": "hi" if hindi else "en", "is_greeting": True,
                "out_of_scope": False, "search_query": question}
    context = ""
    if history:
        last = "\n".join(f"{t['role']}: {t['content'][:300]}" for t in history[-4:])
        context = f"Earlier conversation (use it to make the search_query standalone):\n{last}\n\n"
    try:
        out = llm.generate_json(f"{context}Question: {question}", system=prompts.ROUTER,
                                model=config.GEMINI_ROUTER_MODEL)
    except Exception as e:
        print(f"[router] falling back to keywords: {e}")
        return heuristic_route(question)
    intents = [i for i in out.get("intents", []) if i in config.AGENTS]
    hindi = bool(re.search(r"[\u0900-\u097F]", question))
    bis_terms = bool(BIS_TERMS.search(question))
    result = {
        "intents": list(dict.fromkeys(intents)),
        # Devanagari script is a reliable signal; Hinglish in Latin script is left to the model.
        "language": "hi" if hindi or (out.get("language") == "hi" and not question.isascii()) else "en",
        "is_greeting": bool(out.get("is_greeting")) and not bis_terms,
        # a question naming BIS things is in scope even if the model says otherwise
        "out_of_scope": bool(out.get("out_of_scope")) and not bis_terms,
        "search_query": normalize(out.get("search_query") or question).strip(),
    }
    if not result["intents"] and not (result["is_greeting"] or result["out_of_scope"]):
        result["intents"] = heuristic_route(question)["intents"]
    return result


def router_node(state: State) -> dict:
    t0 = time.time()
    r = route(state["question"], state.get("history"))
    return {**r, "question": normalize(state["question"]), "trace": [{"step": "router", **r, "ms": int((time.time() - t0) * 1000)}]}
