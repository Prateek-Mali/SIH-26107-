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


CONTEXT_CHARS = 12_000   # ~3,000 tokens: keeps each question well under Groq's free 8,000 tokens/minute
EXCERPT_CHARS = 1_500


def fit_budget(chunks: list[dict], question: str) -> list[dict]:
    """Keep excerpts in rank order until the context budget is used; long excerpts are cut to the
    part most similar to the question (best_window)."""
    out, used = [], 0
    for c in chunks:
        text = c["text"] if len(c["text"]) <= EXCERPT_CHARS else best_window(question, c["text"], EXCERPT_CHARS)
        if out and used + len(text) > CONTEXT_CHARS:
            break
        out.append({**c, "text": text})
        used += len(text)
    return out


def format_context(chunks: list[dict]) -> str:
    return "\n\n".join(f"{label(n, c)}\n{c['text']}" for n, c in enumerate(chunks, start=1))


def split_body_and_sources(text: str) -> str:
    """Drop any source list the model wrote anyway; we add our own."""
    return re.split(r"\n\s*(?:\*\*)?(?:Sources|स्रोत)(?:\*\*)?\s*:?\s*(?:\*\*)?\s*\n", text)[0].strip()


def normalize_markers(text: str) -> str:
    """[1, 2, 6] / [1-3] / [1,2] -> [1][2][6] so every later step sees one number per bracket."""
    def expand(m: re.Match) -> str:
        nums = []
        for part in re.split(r"\s*,\s*", m.group(1)):
            if "-" in part or "–" in part:
                a, b = re.split(r"\s*[-–]\s*", part)[:2]
                if a.isdigit() and b.isdigit() and int(b) - int(a) < 20:
                    nums += list(range(int(a), int(b) + 1))
            elif part.isdigit():
                nums.append(int(part))
        return "".join(f"[{n}]" for n in nums)
    return re.sub(r"\[(\d+(?:\s*[,–-]\s*\d+)+)\]", expand, text)


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


# split after . ! ? । but not after abbreviations such as "Rs." "No." "S.O." "e.g." "i.e." "viz." "Sr."
SENTENCE_SPLIT = re.compile(r"(?<![Rr]s\.)(?<!No\.)(?<!S\.O\.)(?<!e\.g\.)(?<!i\.e\.)(?<!viz\.)(?<!Sr\.)"
                            r"(?<=[.!?।])\s+(?=[A-Z0-9\"'(*ऀ-ॿ])")


def renumber_lists(text: str) -> str:
    """After sentences are removed, numbered steps are renumbered 1, 2, 3 ... within each list."""
    out, n = [], 0
    for line in text.split("\n"):
        m = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if m:
            n += 1
            line = f"{m.group(1)}{n}. {m.group(3)}"
        elif line.strip():
            n = 0
        out.append(line)
    return "\n".join(out)


def _units(text: str) -> list[str]:
    """Lines, then sentences within lines (keeps markdown list items whole)."""
    out = []
    for line in text.split("\n"):
        out += SENTENCE_SPLIT.split(line) if len(line) > 200 else [line]
    return out


NUMBER_WORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
                "nine": "9", "ten": "10", "fifteen": "15", "twenty": "20", "thirty": "30", "ninety": "90"}
_WORD = re.compile(r"[a-z0-9]+")


def _numbers(text: str) -> set[str]:
    """Numbers in a text, as digits: '₹5,000' -> '5000', 'two lakh' -> '2'. Ignores citation markers."""
    t = re.sub(r"\[\d+\]", " ", text.lower())
    nums = {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", t)}
    nums |= {NUMBER_WORDS[w] for w in re.findall(r"[a-z]+", t) if w in NUMBER_WORDS}
    return {n for n in nums if n}


def numbers_ok(claim: str, passage: str) -> bool:
    """Every number the claim states must appear in the passage (catches 'ten years' vs 'two years')."""
    return _numbers(claim) <= _numbers(passage)


def best_window(claim: str, passage: str, size: int = 700) -> str:
    """The part of a long excerpt that shares most words with the claim (the reranker reads ~800 chars)."""
    if len(passage) <= size:
        return passage
    cw = set(_WORD.findall(claim.lower()))
    best, best_score = passage[:size], -1
    for start in range(0, len(passage) - size // 2, size // 3):
        win = passage[start:start + size]
        score = len(cw & set(_WORD.findall(win.lower())))
        if score > best_score:
            best, best_score = win, score
    return best


def verify_citations(text: str, chunks: list[dict], language: str) -> tuple[str, list[dict]]:
    """Check each cited sentence against its excerpt(s) with the local reranker (two batched calls).
    Keep supported citations; re-cite to a better excerpt if one supports it; else remove the sentence."""
    if language != "en":
        return text, [], 0  # the local reranker is English-only; Hindi answers are not checked
    from app import rerank

    lines = text.split("\n")
    units = [(li, SENTENCE_SPLIT.split(line) if line.strip() else [line]) for li, line in enumerate(lines)]
    claims = []  # (line index, unit index, claim text, cited numbers)
    for li, parts in units:
        for ui, unit in enumerate(parts):
            nums = [int(x) for x in re.findall(r"\[(\d+)\]", unit)]
            claim = re.sub(r"\[\d+\]|\*\*|^\s*[-*\d.)]+\s*", "", unit).strip()
            cited = [n for n in dict.fromkeys(nums) if 1 <= n <= len(chunks)]
            if cited and len(claim) >= 25:
                claims.append((li, ui, claim, cited))
    # pass 1: each claim against the excerpts it cites
    def full(n: int) -> str:  # title and section count too ("BIS Act, 2016", "Section 29(3)")
        c = chunks[n - 1]
        return f"{c['title']} {c.get('section', '')} {c['text']}"

    stop = {"the", "a", "an", "of", "to", "and", "or", "in", "on", "for", "with", "is", "are", "be", "by", "from",
            "your", "you", "if", "as", "at", "this", "that", "its", "it", "any", "within", "under"}

    def words_covered(claim: str, n: int) -> float:
        cw = {w for w in _WORD.findall(claim.lower()) if w not in stop}
        return len(cw & set(_WORD.findall(full(n).lower()))) / len(cw) if cw else 0.0

    def support(claim: str, cited: list[int], n: int, score: float) -> float:
        # every number in the sentence must appear in what it cites (all its cited excerpts together)
        if not numbers_ok(claim, " ".join(full(m) for m in cited)):
            return 0.0
        # short summary bullets ("Timeline: within 90 days of validity") are too terse for the cross-encoder:
        # accept them when most of their words are in the cited excerpt
        if len(claim.split()) <= 14 and words_covered(claim, n) >= 0.75:
            return max(score, 0.5)
        return score

    pairs = [(c, best_window(c, chunks[n - 1]["text"])) for _, _, c, cited in claims for n in cited]
    it = iter(rerank.pair_scores(pairs))
    first = [[(n, support(c, cited, n, next(it))) for n in cited] for _, _, c, cited in claims]
    # pass 2: unsupported claims against every other excerpt
    failing = [i for i, sc in enumerate(first) if not any(s >= SUPPORT_THRESHOLD for _, s in sc)]
    # only excerpts that contain the claim's numbers are worth scoring (keeps the CPU cost low)
    def overlap(claim: str, n: int) -> int:
        return len(set(_WORD.findall(claim.lower())) & set(_WORD.findall(chunks[n - 1]["text"].lower())))

    candidates = {i: sorted((n for n in range(1, len(chunks) + 1)
                             if n not in claims[i][3] and numbers_ok(claims[i][2], full(n))),
                            key=lambda n, c=claims[i][2]: -overlap(c, n))[:6]  # the 6 most similar excerpts
                  for i in failing}
    alt_pairs = [(claims[i][2], best_window(claims[i][2], chunks[n - 1]["text"])) for i in failing for n in candidates[i]]
    it2 = iter(rerank.pair_scores(alt_pairs))
    best_alt = {i: max(((support(claims[i][2], [n], n, next(it2)), n) for n in candidates[i]), default=(0.0, None))
                for i in failing}

    removed = []
    parts_by_line = {li: list(parts) for li, parts in units}
    for i, (li, ui, claim, cited) in enumerate(claims):
        unit = parts_by_line[li][ui]
        good = [n for n, s in first[i] if s >= SUPPORT_THRESHOLD]
        if good:
            if len(good) < len(cited):
                unit = re.sub(r"(?:\[\d+\])+", "".join(f"[{n}]" for n in good), unit, count=1)
                unit = re.sub(r"(?<=\])(?:\[\d+\])+", "", unit)
        elif best_alt[i][0] >= SUPPORT_THRESHOLD:
            unit = re.sub(r"(?:\[\d+\])+", f"[{best_alt[i][1]}]", unit, count=1)
            unit = re.sub(r"(?<=\])(?:\[\d+\])+", "", unit)
            removed.append({"sentence": claim, "action": f"re-cited to [{best_alt[i][1]}]", "score": round(best_alt[i][0], 3)})
        else:
            unit = None
            removed.append({"sentence": claim, "action": "removed",
                            "score": round(max((s for _, s in first[i]), default=0), 3)})
        parts_by_line[li][ui] = unit

    out_lines = []
    for li, line in enumerate(lines):
        joined = " ".join(p for p in parts_by_line[li] if p is not None).rstrip()
        if line.strip() and not joined.strip():
            continue  # the whole line was removed
        if re.fullmatch(r"\s*([-*•]|\d+[.)])\s*", joined):
            continue
        out_lines.append(joined)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines)).strip(), removed, len(claims)


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
    chunks = fit_budget(ret["chunks"], search_q)
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

    body = merge_duplicate_citations(normalize_markers(body), chunks)
    t_ver = time.time()
    try:
        body, removed, n_checked = verify_citations(body, chunks, lang)
    except Exception as e:  # never lose an answer because the checker failed; say so in the trace
        removed, n_checked = [{"sentence": "", "action": f"citation check skipped: {type(e).__name__}: {e}"}], 0
    trace["claims_checked"] = n_checked
    body = merge_duplicate_citations(body, chunks)  # re-citing can point two numbers at the same page again
    body = renumber_lists(body)
    trace["verify_ms"] = int((time.time() - t_ver) * 1000)
    trace["citation_check"] = removed
    if not re.search(r"\[\d+\]", body):
        res = _result(not_covered, [], provider, t0, trace, refused=True)
        return res
    answer, citations = finalize(body, chunks, lang)
    res = _result(answer, citations, provider, t0, trace)
    _cache("put", key, res)
    return res
