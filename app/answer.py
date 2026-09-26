"""The answer pipeline: one knowledge base, at most one LLM call per question.

    ask(question, history=None) -> {answer, citations, sources_used, provider, latency_ms, trace}

question -> normalize -> retrieve (rule expansions, hybrid, scheme filter, rerank, neighbours)
         -> generate (1 LLM call) -> citation cleanup -> local citation check -> answer + sources
"""
import hashlib
import json
import re
import sqlite3
import time

from app import config, llm, prompts
from app.expand import detect_lang, normalize
from app.retrieval import retrieve

GREETING = re.compile(r"^\s*(hi+|hello|hey|namaste|namaskar|नमस्ते|नमस्कार|good (morning|afternoon|evening)|"
                      r"thanks?( you)?|thank you|धन्यवाद|ok(ay)?|bye)[\s!.?]*$", re.I)
SUPPORT_THRESHOLD = 0.3   # reranker probability that a cited excerpt supports a sentence
CACHE_PATH = config.ROOT / "index" / "answer_cache.sqlite"


# ---------------------------------------------------------------- cache
def _index_version() -> str:
    paths = [config.BM25_PATH, config.ROOT / config.QDRANT_PATH]
    return "-".join(str(int(p.stat().st_mtime)) for p in paths if p.exists())


def _cache_key(q: str) -> str:
    return hashlib.sha256(f"{q.lower().strip()}|{_index_version()}|{config.GEMINI_MODEL}".encode()).hexdigest()


def _cache(op: str, key: str, value: dict | None = None):
    try:
        con = sqlite3.connect(CACHE_PATH)
        con.execute("CREATE TABLE IF NOT EXISTS answers (key TEXT PRIMARY KEY, value TEXT, created REAL)")
        if op == "get":
            row = con.execute("SELECT value FROM answers WHERE key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else None
        con.execute("INSERT OR REPLACE INTO answers VALUES (?,?,?)", (key, json.dumps(value, ensure_ascii=False), time.time()))
        con.commit()
    except sqlite3.Error as e:
        print(f"[cache] {e}")
    finally:
        try:
            con.close()
        except Exception:
            pass


# ---------------------------------------------------------------- context and citations
def label(n: int, c: dict) -> str:
    parts = [c["title"], f"scheme: {c.get('scheme') or 'general'}"]
    if c.get("section"):
        parts.append(c["section"][:120])
    if c.get("page"):
        parts.append(f"page {c['page']}")
    parts.append(f"date: {c.get('doc_date') or 'n/a'}")
    if "operating_manual" in c["source_id"]:
        parts.append("OLDER document: the Regulations win on conflict")
    return f"[{n}] " + " | ".join(parts)


def format_context(chunks: list[dict]) -> str:
    return "\n\n".join(f"{label(n, c)}\n{c['text']}" for n, c in enumerate(chunks, start=1))


def split_body_and_sources(text: str) -> str:
    """Drop any source list the model wrote anyway; we add our own."""
    return re.split(r"\n\s*(?:\*\*)?(?:Sources|स्रोत)(?:\*\*)?\s*:?\s*(?:\*\*)?\s*\n", text)[0].strip()


def merge_duplicate_citations(text: str, chunks: list[dict]) -> str:
    """[5][6][7] pointing to the same document page become one number."""
    first_for_key: dict[tuple, int] = {}
    mapping = {}
    for n, c in enumerate(chunks, start=1):
        key = (c["source_id"], c.get("page")) if "::row" not in c["chunk_id"] else (c["chunk_id"],)
        mapping[n] = first_for_key.setdefault(key, n)

    def fix(group: str) -> str:
        nums = [int(x) for x in re.findall(r"\[(\d+)\]", group)]
        kept = list(dict.fromkeys(mapping.get(n, n) for n in nums if 1 <= n <= len(chunks)))
        return "".join(f"[{n}]" for n in kept)

    return re.sub(r"(?:\[\d+\])+", lambda m: fix(m.group(0)), text)


SENTENCE_SPLIT = re.compile(r"(?<=[.!?।])\s+(?=[A-Z0-9\"'(*ऀ-ॿ])")


def _units(text: str) -> list[str]:
    """Lines, then sentences within lines (keeps markdown list items whole)."""
    out = []
    for line in text.split("\n"):
        out += SENTENCE_SPLIT.split(line) if len(line) > 200 else [line]
    return out


def verify_citations(text: str, chunks: list[dict], language: str) -> tuple[str, list[dict]]:
    """Check each cited sentence against its excerpt with the local reranker. Re-cite to a better
    excerpt if one supports it; remove the sentence if none does. Returns (text, removed)."""
    if language != "en":
        return text, []  # the local reranker is English-only; Hindi answers are not checked
    from app import rerank

    removed, out_lines = [], []
    for line in text.split("\n"):
        new_parts = []
        for unit in (SENTENCE_SPLIT.split(line) if line.strip() else [line]):
            nums = [int(x) for x in re.findall(r"\[(\d+)\]", unit)]
            claim = re.sub(r"\[\d+\]|\*\*|^\s*[-*\d.)]+\s*", "", unit).strip()
            if not nums or len(claim) < 25:
                new_parts.append(unit)
                continue
            cited = [n for n in dict.fromkeys(nums) if 1 <= n <= len(chunks)]
            sc = rerank.pair_scores([(claim, chunks[n - 1]["text"]) for n in cited]) if cited else []
            good = [n for n, s in zip(cited, sc) if s >= SUPPORT_THRESHOLD]
            if good:
                if len(good) < len(cited):
                    unit = re.sub(r"(?:\[\d+\])+", "".join(f"[{n}]" for n in good), unit, count=1)
                    unit = re.sub(r"(?<=\])(?:\[\d+\])+", "", unit)
                new_parts.append(unit)
                continue
            # none of the cited excerpts supports it: is there another excerpt that does?
            others = [n for n in range(1, len(chunks) + 1) if n not in cited]
            alt = rerank.scores(claim, [chunks[n - 1]["text"] for n in others]) if others else []
            best = max(zip(alt, others), default=(0, None))
            if best[0] >= SUPPORT_THRESHOLD:
                unit = re.sub(r"(?:\[\d+\])+", f"[{best[1]}]", unit, count=1)
                unit = re.sub(r"(?<=\])(?:\[\d+\])+", "", unit)
                new_parts.append(unit)
                removed.append({"sentence": claim, "action": f"re-cited to [{best[1]}]", "score": round(best[0], 3)})
            else:
                removed.append({"sentence": claim, "action": "removed", "score": round(max(sc, default=0), 3)})
        joined = " ".join(p for p in new_parts if p is not None).rstrip()
        if line.strip() and not joined.strip():
            continue  # the whole line was removed
        if re.fullmatch(r"\s*([-*•]|\d+[.)])\s*", joined):
            continue
        out_lines.append(joined)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines)).strip(), removed


def finalize(text: str, chunks: list[dict], language: str) -> tuple[str, list[dict]]:
    """Renumber citations 1..N in order of first use, drop unused, append the source list."""
    order = []
    for m in re.findall(r"\[(\d+)\]", text):
        n = int(m)
        if 1 <= n <= len(chunks) and n not in order:
            order.append(n)
    new = {old: i for i, old in enumerate(order, start=1)}
    text = re.sub(r"\[(\d+)\]", lambda m: f"[{new[int(m.group(1))]}]" if int(m.group(1)) in new else "", text)
    citations = []
    for old in order:
        c = chunks[old - 1]
        url = c.get("url", "")
        if c.get("page") and url.lower().split("#")[0].endswith(".pdf"):
            url = f"{url.split('#')[0]}#page={c['page']}"
        citations.append({"n": new[old], "chunk_id": c["chunk_id"], "source_id": c["source_id"], "title": c["title"],
                          "section": c.get("section", ""), "page": c.get("page"), "url": url,
                          "scheme": c.get("scheme", ""), "doc_date": c.get("doc_date", ""),
                          "snippet": " ".join(c["text"].split())[:300]})
    if citations:
        lines = []
        for c in citations:
            where = ", ".join(x for x in (c["section"][:90], f"p. {c['page']}" if c["page"] else "",
                                          f"dated {c['doc_date']}" if c["doc_date"] else "") if x)
            lines.append(f"[{c['n']}] {c['title']}" + (f": {where}" if where else "") + f" | {c['url']}")
        text += f"\n\n**{'स्रोत' if language == 'hi' else 'Sources'}:**\n" + "\n".join(lines)
    return text, citations


# ---------------------------------------------------------------- main entry
def _result(answer, citations, provider, t0, trace, refused=False, cached=False):
    return {"answer": answer, "citations": citations, "sources_used": len({c["source_id"] for c in citations}),
            "provider": provider, "latency_ms": int((time.time() - t0) * 1000), "refused": refused,
            "cached": cached, "trace": trace}


def with_history(q: str, history: list[dict] | None) -> str:
    """Short follow-ups ("and the fee?", "what about renewal?") get the previous question as context."""
    if not history or len(q.split()) > 8:
        return q
    last_user = next((t["content"] for t in reversed(history) if t["role"] == "user"), "")
    return f"{last_user} {q}" if last_user else q


def ask(question: str, history: list[dict] | None = None, use_cache: bool = True) -> dict:
    t0 = time.time()
    q = normalize(question)
    lang = detect_lang(q)
    if GREETING.match(q):
        return _result(prompts.GREETING_HI if lang == "hi" else prompts.GREETING_EN, [], "none", t0, {"step": "greeting"})
    search_q = with_history(q, history)
    key = _cache_key(search_q)
    if use_cache and (hit := _cache("get", key)):
        hit["cached"], hit["latency_ms"] = True, int((time.time() - t0) * 1000)
        return hit

    ret = retrieve(search_q)
    chunks = ret["chunks"]
    trace = {"retrieval": ret["trace"],
             "chunks": [{"n": n, "chunk_id": c["chunk_id"], "title": c["title"], "section": c.get("section", "")[:80],
                         "scheme": c.get("scheme"), "page": c.get("page"), "rerank": c.get("rerank"),
                         "neighbour_of": c.get("neighbour_of")} for n, c in enumerate(chunks, start=1)]}
    not_covered = prompts.NOT_COVERED_HI if lang == "hi" else prompts.NOT_COVERED_EN
    if not chunks:
        return _result(not_covered, [], "none", t0, trace, refused=True)

    prompt = (f"CONTEXT:\n{format_context(chunks)}\n\n"
              f"QUESTION ({'Hindi' if lang == 'hi' else 'English'}): {q}"
              + (f"\n(Earlier question in this conversation: {search_q[:-len(q)].strip()})" if search_q != q else ""))
    t_gen = time.time()
    raw, provider = llm.generate_with_provider(prompt, system=prompts.ANSWER, temperature=0.1, max_tokens=4096)
    trace["generate_ms"] = int((time.time() - t_gen) * 1000)
    body = split_body_and_sources(raw)
    if body.strip().upper().startswith("NOT_COVERED") or not re.search(r"\[\d+\]", body):
        trace["note"] = "model found nothing relevant in the context"
        res = _result(not_covered, [], provider, t0, trace, refused=True)
        _cache("put", key, res)
        return res

    body = merge_duplicate_citations(body, chunks)
    t_ver = time.time()
    try:
        body, removed = verify_citations(body, chunks, lang)
    except Exception as e:  # never lose an answer because the checker failed; say so in the trace
        removed = [{"sentence": "", "action": f"citation check skipped: {type(e).__name__}: {e}"}]
    trace["verify_ms"] = int((time.time() - t_ver) * 1000)
    trace["citation_check"] = removed
    if not re.search(r"\[\d+\]", body):
        res = _result(not_covered, [], provider, t0, trace, refused=True)
        return res
    answer, citations = finalize(body, chunks, lang)
    res = _result(answer, citations, provider, t0, trace)
    _cache("put", key, res)
    return res
