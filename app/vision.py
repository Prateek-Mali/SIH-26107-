"""Product photo -> what is on it -> the normal cited answer.

    read_image(data, filename) -> vision JSON (Gemini vision, JSON schema; reads only what is visible)
    photo_chat(data, filename, question, session_id, owner) -> the chat result + "vision" and "format_checks"

Steps: (1) Gemini reads the photo into a fixed JSON (numbers it cannot clearly read are null, never guessed);
(2) app/vision_check.py checks the number formats against the BIS documents (plain code); (3) the product
description goes through the usual chat (recommender, scheme selector, RAG, citations, memory). The reply starts
with "What I see in your photo:". It never says a licence or HUID is genuine: only BIS CARE can confirm that.
"""
import hashlib
import io
import json
import re
import time

from app import config, llm
from app.vision_check import check

MAX_BYTES = 10 * 1024 * 1024
MAX_SIDE = 1024   # enough for label text; smaller = faster upload and vision call
MIME = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "heic": "image/heic",
        "heif": "image/heic"}
MARK_TYPES = ["ISI", "CRS", "HALLMARK", "OTHER"]

SCHEMA = {
    "type": "object",
    "properties": {
        "product_type": {"type": ["string", "null"], "description": "e.g. 'stainless steel water bottle'; null if no product"},
        "product_description": {"type": "string", "description": "what the product is, material, use (for finding its standard)"},
        "marks": {"type": "array", "items": {"type": "object", "properties": {
            "type": {"type": "string", "enum": MARK_TYPES}, "confidence": {"type": "number"}},
            "required": ["type", "confidence"]}},
        "cml_number": {"type": ["string", "null"]}, "r_number": {"type": ["string", "null"]},
        "huid": {"type": ["string", "null"]}, "purity": {"type": ["string", "null"]},
        "is_number_on_label": {"type": ["string", "null"]}, "brand": {"type": ["string", "null"]},
        "other_text": {"type": ["string", "null"]},
        "image_quality": {"type": "string", "enum": ["good", "blurry", "partial"]},
        "notes": {"type": ["string", "null"]},
    },
    "required": ["product_type", "product_description", "marks", "cml_number", "r_number", "huid", "purity",
                 "is_number_on_label", "brand", "other_text", "image_quality", "notes"],
}

PROMPT = """Read this product/label photo for a BIS (Bureau of Indian Standards) assistant. Report ONLY what is visible.
marks: ISI (Standard Mark box, IS number above, CM/L number below), CRS (R- number with IS number), HALLMARK (BIS logo,
purity like 22K916, 6-character HUID), OTHER; [] if none. Copy numbers exactly as printed, WITH their prefix
(cml_number "CM/L-...", r_number "R-...", is_number_on_label "IS ..."); if a number is not clearly readable
return null and say so in notes. NEVER guess a number. product_type: null if no product (landscape, animal...).
product_description: one sentence (product, material, use)."""


def prepare(data: bytes, filename: str) -> tuple[bytes, str]:
    """Checks type and size; resizes jpg/png/webp to at most 1600 px (HEIC is sent as is: Gemini reads it)."""
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext not in MIME:
        raise ValueError("Please send a jpg, png, webp or heic photo.")
    if len(data) > MAX_BYTES:
        raise ValueError("The photo is larger than 10 MB. Please send a smaller one.")
    if MIME[ext] == "image/heic":
        return data, MIME[ext]
    from PIL import Image, ImageOps
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.save(out, format="JPEG", quality=90)
    return out.getvalue(), "image/jpeg"


_VISION_CACHE: dict[str, dict] = {}   # sha256 of the photo -> vision JSON


def read_image(data: bytes, filename: str) -> dict:
    """Photo -> vision JSON (+ model, ms). The same photo twice is read once. Raises ValueError for a bad file."""
    key = hashlib.sha256(data).hexdigest()
    if key in _VISION_CACHE:
        return {**_VISION_CACHE[key], "_ms": 0, "_cached": True}
    out = _read_image(data, filename)
    if len(_VISION_CACHE) > 256:  # ponytail: in-process FIFO cache; move to SQLite if photos repeat across restarts
        _VISION_CACHE.pop(next(iter(_VISION_CACHE)))
    _VISION_CACHE[key] = out
    return out


def _read_image(data: bytes, filename: str) -> dict:
    from google.genai import types
    body, mime = prepare(data, filename)
    t0 = time.time()
    cfg = types.GenerateContentConfig(temperature=0.0, seed=llm.SEED, response_mime_type="application/json",
                                      response_json_schema=SCHEMA, max_output_tokens=1500)
    contents = [types.Part.from_bytes(data=body, mime_type=mime), PROMPT]
    models = llm.model_chain(config.GEMINI_MODEL)  # the pinned Flash(-Lite) model first: fast; fallbacks after
    resp = llm._call(lambda c, m: c.models.generate_content(model=m, contents=contents, config=cfg), models, rounds=1)
    out = json.loads(resp.text)
    out["marks"] = [m for m in out.get("marks") or [] if m.get("type") in MARK_TYPES]
    numbers = ("cml_number", "r_number", "huid", "purity", "is_number_on_label")
    for k in numbers:  # "unclear" means not read
        if isinstance(out.get(k), str) and (not out[k].strip() or "unclear" in out[k].lower()):
            out[k] = None
    if out.get("image_quality") == "blurry" and any(out.get(k) for k in numbers):
        # a model reading a blurry label fills in plausible digits (tested: 7600012345 read as 7800912345):
        # numbers from a blurry photo are never used
        dropped = [k for k in numbers if out.get(k)]
        for k in dropped:
            out[k] = None
        out["notes"] = ((out.get("notes") or "").rstrip(". ") + ". " if out.get("notes") else "") + \
            "The photo is too blurry to read the numbers reliably (" + ", ".join(dropped).replace("_", " ") + \
            "); please send a sharper photo of the label."
    out["_model"], out["_ms"] = resp.model_version or models[0], int((time.time() - t0) * 1000)
    return out


# ---------------------------------------------------------------- answer
EXPECTED_MARK = {"I": "ISI", "II": "CRS", "hallmarking": "HALLMARK"}


def seen_block(v: dict, checks: list[dict]) -> str:
    """'What I see in your photo:' from the vision JSON (observations, not document facts)."""
    marks = ", ".join(f"{m['type']} mark" for m in v["marks"]) or "no certification mark visible"
    lines = [f"**What I see in your photo:** {v.get('product_type') or 'no product'}; {marks}."]
    nums = [f"{label} {v[k]}" for k, label in (("is_number_on_label", "IS number"), ("cml_number", "licence"),
                                                 ("r_number", "registration"), ("huid", "HUID"),
                                                 ("purity", "purity")) if v.get(k)]
    if nums:
        lines.append("Numbers on the label: " + ", ".join(nums) + ".")
    for c in checks:
        lines.append(f"- {c['field'].replace('_', ' ')} **{c['value']}**: format "
                     f"{'looks right' if c['valid_format'] else 'does NOT match'}: {c['reason']}")
    if v.get("image_quality") != "good" or v.get("notes"):
        lines.append(f"(Photo {v.get('image_quality')}{': ' + v['notes'].rstrip('. ') if v.get('notes') else ''}. "
                     "I do not guess numbers I cannot read clearly.)")
    return "\n".join(lines)


def mark_line(v: dict, rec: dict, sch: dict, citations: list[dict]) -> str:
    """Whether the required mark is visible; the 'required' part cites the product row the answer cited."""
    top = (rec.get("candidates") or [None])[0]
    key = "hallmarking" if any(r["key"] == "hallmarking" for r in sch.get("results", [])) else (top or {}).get("scheme")
    need = EXPECTED_MARK.get("II" if str(key).startswith("II") else key)  # product lists say "II-CRS"
    if not need:
        return ""
    have = {m["type"] for m in v["marks"]}
    row = (top or {}).get("source", {}).get("row_chunk_id")
    n = next((c["n"] for c in citations if c["chunk_id"] == row), None)
    compulsory = key == "hallmarking" or (top or {}).get("compulsory") == "yes"
    if need in have:
        return f"The {need} mark this product needs is visible in the photo."
    if compulsory and n:
        return f"**No {need} mark visible; this product requires one** [{n}]."
    return f"No {need} mark is visible in the photo; see below whether this product requires one."


def verify_line(v: dict) -> str:
    nums = [v[k] for k in ("cml_number", "r_number", "huid") if v.get(k)]
    if not nums:
        return ""
    return ("**How to verify:** check " + " and ".join(nums) + " in the BIS CARE app "
            "(https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the "
            "number is genuine; only BIS CARE can confirm it.")


def _answer(v: dict, question: str, sid: str, precious: bool, t0: float):
    """Fast photo path (no agent loop): product tools and document search in parallel -> ONE answer call with the
    tool evidence + the top 8 excerpts -> the usual citation check (app/answer.ground)."""
    from concurrent.futures import ThreadPoolExecutor

    from app import answer as A, memory
    from app.expand import detect_lang
    from app.recommender import recommend_standards, select_scheme, tool_context
    from app.retrieval import retrieve

    desc, marks = v["product_description"], ", ".join(m["type"] for m in v["marks"]) or "none"
    is_no = v.get("is_number_on_label") or ""  # printed on the label: exact evidence for the product lookup
    ask = question.strip() or "Which Indian Standard applies, is BIS certification compulsory, and which scheme?"
    q = (f"{ask} (Product in my photo: {desc}. Marks visible: {marks}"
         + (f"; IS number on label: {v['is_number_on_label']}" if v.get("is_number_on_label") else "") + ".)")
    with ThreadPoolExecutor(2) as pool:
        f_ret = pool.submit(retrieve, f"{ask} {desc} {is_no}", top_k=8, with_neighbours=False)
        rec = recommend_standards(f"{desc} {is_no}".strip(), attrs={"product_type": v.get("product_type") or "", "precious_metal": precious})
        sch = select_scheme({"is_precious_metal": precious}, rec["candidates"], desc)
        ret = f_ret.result()
    tool_chunks, tools_block = tool_context(rec, sch)
    have = {c["chunk_id"] for c in tool_chunks}
    chunks = tool_chunks + A.fit_budget([c for c in ret["chunks"] if c["chunk_id"] not in have][:8], q,
                                        budget=A.CONTEXT_CHARS // 2)
    lang = "hi" if detect_lang(question) == "hi" else "en"
    known = memory.profile(sid)
    stages = {"mode": "photo", "sent_to_llm": [c["chunk_id"] for c in chunks], "product": v.get("product_type")}
    trace = {"stages": stages, "chunks": [{"n": n, "chunk_id": c["chunk_id"], "title": c["title"]}
                                          for n, c in enumerate(chunks, start=1)]}
    prompt = A.answer_prompt(q, chunks, lang, tools_block=tools_block, known=known)
    raw, provider = A.generate(prompt)

    def regen(sub, extra):
        return A.generate(A.answer_prompt(q, sub, lang, tools_block=tools_block if sub is chunks else "", known=known) + extra)

    res = A.ground(q, q, lang, chunks, raw, provider, regen, stages, ret["trace"].get("max_rerank", 0.0), None, t0, trace)
    return res, rec, sch


def photo_chat(data: bytes, filename: str, question: str = "", session_id: str | None = None,
               owner: str = "", use_cache: bool = True) -> dict:
    from app import memory

    t0 = time.time()
    v = read_image(data, filename) if use_cache else _read_image(data, filename)
    checks = check(v)
    sid = memory.ensure(session_id, owner)
    if not v.get("product_type") and not v["marks"]:  # not a product: say what it is, nothing invented
        answer = (f"**What I see in your photo:** {v.get('product_description') or 'no product'}. I can't see a product "
                  "or a BIS mark, so there is nothing to check. Send a photo of the product and its label or mark.")
        memory.add_turn(sid, "user", f"[photo] {question}".strip())
        memory.add_turn(sid, "assistant", answer)
        return {"answer": answer, "citations": [], "sources_used": 0, "provider": v["_model"], "fallback": None,
                "latency_ms": int((time.time() - t0) * 1000), "refused": False, "cached": False, "session_id": sid,
                "trace": {"stages": {"mode": "photo"}}, "vision": v, "format_checks": checks}

    precious = any(m["type"] == "HALLMARK" for m in v["marks"]) or bool(re.search(r"\b(gold|silver)\b",
                                                                                   v["product_description"], re.I))
    res, rec, sch = _answer(v, question, sid, precious, t0)
    memory.add_turn(sid, "user", f"[photo: {v.get('product_type')}] {question}".strip())
    memory.add_turn(sid, "assistant", res["answer"], [c["chunk_id"] for c in res.get("citations", [])])
    memory.set_profile(sid, {"product": v.get("product_type"), "is_number": v.get("is_number_on_label")})
    res["session_id"] = sid
    if not res.get("refused"):
        body, sep, sources = res["answer"].partition("\n\n**Sources:**")
        parts = [seen_block(v, checks), mark_line(v, rec, sch, res.get("citations", [])), body.strip(), verify_line(v)]
        res["answer"] = "\n\n".join(p for p in parts if p) + (sep + sources if sep else "")
    else:
        res["answer"] = seen_block(v, checks) + "\n\n" + res["answer"] + ("\n\n" + verify_line(v) if verify_line(v) else "")
    res.update(vision=v, format_checks=checks, latency_ms=int((time.time() - t0) * 1000))
    return res
