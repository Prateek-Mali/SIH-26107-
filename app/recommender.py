"""Standard Recommender and Scheme Selector.

    recommend_standards(description, attrs=None) -> {"candidates": [...], "attrs": {...}, "ms": ...}
    select_scheme(profile, candidates) -> {"results": [...], "notes": [...], "profile": {...}}

Every IS number comes from data/structured/product_index.csv; every scheme rule cites its proof chunk
(app/scheme_rules.yaml). One cheap LLM call extracts product attributes, and only when the caller
(the chat's understand step) has not already done it.
"""
import csv
import json
import re
import time
from functools import lru_cache

import yaml

from app import config, llm
from app.expand import normalize

INDEX_CSV = config.DATA / "structured" / "product_index.csv"
QDRANT_PATH, COLLECTION = str(config.ROOT / "index" / "qdrant_products"), "bis_product_index"
RULES = config.ROOT / "app" / "scheme_rules.yaml"
KEEP = 0.30          # reranker probability to keep a candidate (tuned on tests/test_recommender.py)
CLOSE = 0.15         # candidates within this of the best one get a deciding_factor
STOP = {"for", "of", "the", "and", "with", "use", "in", "to", "a", "an", "or", "by", "on", "part", "specification",
        "general", "requirements", "type", "types", "made", "my", "sold", "shop", "home", "india", "from"}

EXTRACT = """Extract product facts from a user's description for a BIS (Bureau of Indian Standards) lookup.
Reply with JSON only: {"product_type": "the product in plain English (singular)", "material": "", "use": "domestic |
industrial | ''", "electrical": true|false, "electronics_it": true|false, "precious_metal": true|false,
"maker_location": "india | foreign | unknown", "role": "manufacturer | importer | trader | jeweller | consumer | unknown",
"key_specs": ""}"""


@lru_cache(maxsize=1)
def _rows() -> list[dict]:
    rows = list(csv.DictReader(INDEX_CSV.open(encoding="utf-8")))
    for r in rows:
        r["syn"] = [s for s in (r.get("synonyms") or "").split(" | ") if s]
    return rows


@lru_cache(maxsize=1)
def _vocab() -> set[str]:
    return set().union(*(_words(" ".join([r["product_name"]] + r["syn"])) for r in _rows()))


@lru_cache(maxsize=1)
def _client():
    from app.retrieval import open_local_qdrant
    return open_local_qdrant(QDRANT_PATH)


@lru_cache(maxsize=1)
def rules() -> dict:
    return yaml.safe_load(RULES.read_text(encoding="utf-8"))


def _words(t: str) -> set[str]:
    return {w.rstrip("s") for w in re.findall(r"[a-z0-9]+", (t or "").lower()) if w not in STOP and len(w) > 2}


def _is_set(t: str) -> set[str]:
    from app.tools import _norm_is
    return _norm_is(t)


def extract(description: str) -> dict:
    try:
        text, _ = llm.generate_with_provider(f"Description: {description}", system=EXTRACT, temperature=0.0,
                                             max_tokens=300, model=config.GEMINI_ROUTER_MODEL,
                                             groq_model=config.GROQ_SMALL_MODEL)
        return json.loads(text[text.find("{"): text.rfind("}") + 1])
    except Exception as e:
        print(f"[recommender] attribute extraction skipped ({type(e).__name__})")
        return {}


def compulsory(r: dict) -> str:
    return {"in_force": "yes",
            "upcoming": f"upcoming from {r.get('effective_date') or 'the date in the order'}",
            "withdrawn": "no: the QCO for this product was withdrawn (see the order)",
            "de-notified": "no: de-notified from compulsory BIS certification"}.get(r["status"], r["status"])


def recommend_standards(description: str, attrs: dict | None = None, k: int = 5) -> dict:
    t0 = time.time()
    attrs = attrs if attrs is not None else extract(description)
    q = normalize(description)
    ptype = (attrs.get("product_type") or "").strip()
    text_l = f" {q.lower()} {ptype.lower()} "
    rows = _rows()
    strong, reasons = [], {}

    def note(i, why):
        reasons.setdefault(i, [])
        if why not in reasons[i]:
            reasons[i].append(why)

    want = _is_set(q)
    if want:  # 1. exact IS number
        for i, r in enumerate(rows):
            if _is_set(r["is_number"]) & want:
                strong.append(i)
                note(i, f"IS number {r['is_number']}")
    for i, r in enumerate(rows):  # 2. exact product name or synonym in the description
        for name in [r["product_name"]] + r["syn"]:
            if len(name) >= 4 and re.search(r"(?<![a-z0-9])" + re.escape(name.lower()) + r"(?:s|es)?(?![a-z0-9])", text_l):
                if i not in strong:
                    strong.append(i)
                note(i, f"name/synonym '{name}'")
                break
    if attrs.get("precious_metal") and not strong:
        return {"candidates": [], "attrs": attrs, "ms": int((time.time() - t0) * 1000), "note": "precious metal"}

    query = " ".join(x for x in (ptype, attrs.get("material", ""), attrs.get("use", ""), q) if x)
    vector = []  # 3. vector search on the product index
    try:
        from app.llm import embed
        v = embed([query], task="RETRIEVAL_QUERY", rounds=1)[0]
        key = {(r["row_chunk_id"], r["product_name"]): i for i, r in enumerate(rows)}
        for h in _client().query_points(COLLECTION, query=v, limit=10).points:
            i = key.get((h.payload["row_chunk_id"], h.payload["product_name"]))
            if i is not None:
                vector.append(i)
    except Exception as e:
        print(f"[recommender] vector search skipped ({type(e).__name__}: {str(e)[:80]})")
    # 4. word overlap with name + synonyms; only words that occur in some product name count, so question words
    #    like "make", "which", "applies", "compulsory" do not dilute the coverage
    qw = _words(f"{ptype} {q}") & _vocab()
    overlap = sorted(((len(qw & _words(" ".join([r["product_name"]] + r["syn"]))), i) for i, r in enumerate(rows)),
                     reverse=True)
    keyword = [i for n, i in overlap[:10] if n]
    for i in keyword:
        note(i, "words: " + ", ".join(sorted(qw & _words(" ".join([rows[i]["product_name"]] + rows[i]["syn"])))))
    for i in vector:
        note(i, "meaning (vector) match")

    fused = {}
    for lst in (strong, vector, keyword):
        for rank, i in enumerate(lst):
            fused[i] = fused.get(i, 0) + 1 / (60 + rank + 1)
    cands = sorted(fused, key=lambda i: -fused[i])[:15]
    if not cands:
        return {"candidates": [], "attrs": attrs, "ms": int((time.time() - t0) * 1000)}

    from app import rerank  # 5. local reranker on short product texts
    passages = [f"{rows[i]['product_name']} ({', '.join(rows[i]['syn'])}) {rows[i]['is_number']}" for i in cands]
    scores = rerank.scores(ptype or q, passages)

    head_words = [w.rstrip("s") for w in re.findall(r"[a-z0-9]+", (ptype or q).lower()) if w not in STOP and len(w) > 2]
    head = head_words[-1] if head_words else ""  # the thing itself: "toy" in "wooden toy", "cement" in "... cement"

    def coverage(i: int) -> float:
        """Share of the question's words in the product's name + synonyms, halved when the head noun is missing
        (so 'wooden toy' prefers toys over wooden boards)."""
        pw = _words(" ".join([rows[i]["product_name"]] + rows[i]["syn"]))
        cov = len(qw & pw) / len(qw) if qw else 0.0
        return cov if (not head or head in pw) else cov / 2

    # final = reranker + word coverage: the reranker alone prefers a related product over the named one
    # ("sulphate resisting cement" -> super sulphated cement) and drops plain matches ("wooden toy" -> toys)
    final = {i: s + coverage(i) for i, s in zip(cands, scores)}
    ranked = sorted(cands, key=lambda i: (i not in strong, -final[i]))
    out, seen = [], set()
    for i in ranked:
        r, s = rows[i], final[i]
        key = (r["is_number"], r["product_name"])
        if key in seen or (i not in strong and s < KEEP):
            continue
        seen.add(key)
        out.append({"is_number": r["is_number"], "is_title": r["is_title"], "product_name": r["product_name"],
                    "compulsory": compulsory(r), "status": r["status"], "scheme": r["scheme"],
                    "qco": {"title": r["qco_title"], "so_number": r["qco_so_number"], "date": r["qco_date"]},
                    "match_reason": "; ".join(reasons.get(i, [])) or "reranker",
                    "confidence": "high" if i in strong else ("medium" if s >= 0.6 else "low"),
                    "score": round(float(s), 3), "coverage": round(coverage(i), 2),
                    "source": {"row_chunk_id": r["row_chunk_id"], "url": r["url"]}})
        if len(out) == k:
            break
    # close calls (e.g. plain steel bottle vs vacuum flask): say what tells them apart, from their titles
    if len(out) > 1:
        best = out[0]
        for c in out[1:]:
            # a different standard for the same kind of product (shares half the question's words, or scores close)
            if c["is_number"] != best["is_number"] and (c["coverage"] >= 0.5 or abs(c["score"] - best["score"]) <= CLOSE):
                a, b = _words(best["is_title"]) - _words(c["is_title"]), _words(c["is_title"]) - _words(best["is_title"])
                c["deciding_factor"] = (f"{best['is_number']} is for: {', '.join(sorted(a)) or '-'}; "
                                        f"{c['is_number']} is for: {', '.join(sorted(b)) or '-'}")
    return {"candidates": out, "attrs": attrs, "ms": int((time.time() - t0) * 1000)}


FOREIGN = re.compile(r"\b(made in (?!india)\w+|import\w*|imported|from (?!india)(china|vietnam|japan|korea|taiwan|thailand|"
                     r"germany|usa|us|uk|italy|turkey|malaysia|indonesia|bangladesh|sri lanka|nepal)|foreign|overseas|abroad)\b", re.I)


def fill_profile(profile: dict, text: str = "", attrs: dict | None = None) -> dict:
    """Fill missing profile fields from the question and extracted attributes; unknown stays 'unknown'."""
    p, a, t = dict(profile or {}), attrs or {}, text.lower()
    if not p.get("maker_location") or p["maker_location"] == "unknown":
        loc = a.get("maker_location") if a.get("maker_location") in ("india", "foreign") else None
        p["maker_location"] = loc or ("foreign" if FOREIGN.search(t) else "india" if re.search(r"\b(made in india|in india|udaipur|delhi|mumbai|my factory)\b", t) else "unknown")
    if not p.get("role") or p["role"] == "unknown":
        p["role"] = (a.get("role") if a.get("role") not in (None, "", "unknown") else
                     "importer" if re.search(r"\bimport", t) else
                     "jeweller" if re.search(r"\b(my shop|jeweller)\b", t) and re.search(r"gold|silver|jewel", t) else
                     "manufacturer" if re.search(r"\b(make|making|manufactur|produce|factory)", t) else
                     "trader" if re.search(r"\b(sell|trader|shop)\b", t) else "unknown")
    if "is_precious_metal" not in p:
        p["is_precious_metal"] = bool(a.get("precious_metal")) or bool(re.search(r"\b(gold|silver|jewel\w*|artefact)", t))
    if "is_electronics_it" not in p:
        p["is_electronics_it"] = bool(a.get("electronics_it"))
    return p


def _scheme(key: str) -> dict:
    s = rules()["schemes"][key]
    return {"scheme": s["name"], "key": key, "why": s["why"], "why_sources": s["proof"],
            "next_steps": s["steps"], "portal": s["portal"]}


@lru_cache(maxsize=1)
def _simplified_text() -> str:
    from app.retrieval import _store
    by_id, order = _store()
    return " ".join(by_id[c]["text"] for c in order.get("simplified_procedure_list", []))


def select_scheme(profile: dict, candidates: list[dict] | None = None, text: str = "") -> dict:
    p = fill_profile(profile, text)
    cands = candidates or []
    top = next((c for c in cands if c["status"] in ("in_force", "upcoming")), None)
    results, notes = [], []
    if p["is_precious_metal"] and not (top and top["scheme"] == "II-CRS"):
        r = _scheme("hallmarking")
        r["compulsory"] = "yes, for articles covered by the Mandatory Hallmarking Order (see the order and its amendments)"
        r["compulsory_source"] = rules()["schemes"]["hallmarking"]["compulsory_proof"]
        results.append(r)
    elif top and top["scheme"] == "II-CRS":
        results.append({**_scheme("crs"), "compulsory": top["compulsory"], "compulsory_source": top["source"]["row_chunk_id"]})
    elif top:
        keys = {"india": ["scheme1"], "foreign": ["fmcs"]}.get(p["maker_location"], ["scheme1", "fmcs"])
        for key in keys:  # unknown maker location -> show both cases
            r = {**_scheme(key), "compulsory": top["compulsory"], "compulsory_source": top["source"]["row_chunk_id"]}
            if len(keys) > 1:
                r["case"] = "if the maker is in India" if key == "scheme1" else "if the maker is outside India"
            results.append(r)
        num = re.sub(r"\D", "", top["is_number"].split(":")[0])
        if "scheme1" in keys and num and re.search(rf"\b{num}\b", _simplified_text()):
            notes.append(rules()["notes"]["simplified"])
    else:
        results.append({**_scheme("voluntary"), "compulsory": "no QCO found in my documents"})
    if p["role"] in ("importer", "trader") and not p["is_precious_metal"]:
        notes.append(rules()["notes"]["importer"])
    return {"results": results, "notes": notes, "profile": p}


def tool_context(rec: dict, sch: dict) -> tuple[list[dict], str]:
    """Excerpts (real chunks: product rows + rule proofs) to put first in the answer context, and a summary
    that refers to them as [n]. The caller renumbers when it merges them with the RAG chunks."""
    from app.retrieval import _store
    by_id, _ = _store()
    ids = [c["source"]["row_chunk_id"] for c in rec["candidates"]]
    for r in sch["results"]:
        ids += r["why_sources"] + [s["proof"] for s in r["next_steps"]] + ([r["compulsory_source"]] if r.get("compulsory_source") else [])
    ids += [n["proof"] for n in sch["notes"]]
    ids = [i for i in dict.fromkeys(ids) if i in by_id]
    n = {cid: k for k, cid in enumerate(ids, start=1)}
    # long proof chunks: keep the window that matches the step/reason they prove (keeps the prompt small)
    claim = {}
    for r in sch["results"]:
        for x in r["why_sources"]:
            claim.setdefault(x, r["why"])
        for st in r["next_steps"]:
            claim[st["proof"]] = claim.get(st["proof"], "") + " " + st["text"]
    for x in sch["notes"]:
        claim.setdefault(x["proof"], x["text"])
    from app.answer import best_window
    chunks = [{**by_id[i], "text": best_window(claim[i], by_id[i]["text"], 1500)} if i in claim else by_id[i] for i in ids]
    lines = ["PRODUCT CHECK (computed from the excerpts; cite the excerpt numbers shown):"]
    for c in rec["candidates"]:
        ref = f"[{n[c['source']['row_chunk_id']]}]" if c["source"]["row_chunk_id"] in n else ""
        lines.append(f"- {c['is_number']} | {c['product_name']} | compulsory: {c['compulsory']} | scheme {c['scheme']} | "
                     f"QCO: {c['qco']['title'][:160]} {ref}" + (f" | deciding factor: {c['deciding_factor']}" if c.get("deciding_factor") else ""))
    if not rec["candidates"]:
        lines.append("- No matching product row in the BIS compulsory-certification lists I have.")
    for r in sch["results"]:
        refs = "".join(f"[{n[x]}]" for x in r["why_sources"] if x in n)
        lines.append(f"SCHEME{(' (' + r['case'] + ')') if r.get('case') else ''}: {r['scheme']}: {r['why']} {refs} | "
                     f"compulsory: {r['compulsory']} | portal: {r['portal']['name']} {r['portal']['url']}")
        for s in r["next_steps"]:
            lines.append(f"  step: {s['text']} [{n[s['proof']]}]" if s["proof"] in n else f"  step: {s['text']}")
    for x in sch["notes"]:
        lines.append(f"NOTE: {x['text']} [{n[x['proof']]}]" if x["proof"] in n else f"NOTE: {x['text']}")
    return chunks, "\n".join(lines)


if __name__ == "__main__":
    import sys
    d = " ".join(sys.argv[1:]) or "stainless steel water bottle for drinking water"
    rec = recommend_standards(d)
    print(json.dumps({k: v for k, v in rec.items()}, indent=1, ensure_ascii=False)[:3000])
    print(json.dumps(select_scheme({}, rec["candidates"], d), indent=1, ensure_ascii=False)[:2000])
