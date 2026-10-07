"""The answer pipeline: one knowledge base, deterministic retrieval, one answer model per run.

    ask(question, history=None) -> {answer, citations, sources_used, provider, fallback, latency_ms, trace}

question -> understand (JSON + schema, or rules) -> retrieve (concept expansion, hybrid, rerank, neighbours)
         -> refuse only if search_empty -> generate -> citation check -> answer + sources
Second chances (each at most once): the model says NOT_COVERED although the excerpts score high -> ask again;
the citation check would remove > 40% of the sentences -> regenerate from only the supporting excerpts.
trace["stages"] shows every step (the CLI's /trace).
"""
import hashlib
import json
import re
import sqlite3
import time

from app import config, llm, prompts
from app.expand import detect_lang, normalize
from app.retrieval import retrieve
from app.understand import understand

GREETING = re.compile(r"^\s*(hi+|hello|hey|namaste|namaskar|नमस्ते|नमस्कार|good (morning|afternoon|evening))[\s!.?]*$", re.I)
SMALLTALK = [  # (pattern, key in prompts.SMALLTALK): fixed replies, no search, never a refusal
    (re.compile(r"^\s*(thanks?( you)?( so much)?|thank you|thx|ty|धन्यवाद|शुक्रिया|ok(ay)?( thanks?)?)[\s!.?]*$", re.I), "thanks"),
    (re.compile(r"^\s*(bye|goodbye|see you|अलविदा)[\s!.?]*$", re.I), "bye"),
    (re.compile(r"^\s*(who (made|built|created|are) you|are you (chat ?gpt|gpt|a bot|an ai|human)|what are you|"
                r"तुम कौन हो|आप कौन हैं)\W*(\s*/\s*(who (made|built|created|are) you|are you (chat ?gpt|gpt|a bot))\W*)*$", re.I), "who"),
    # who made / owns this assistant or project (only about the assistant itself, never "who owns the licence?")
    (re.compile(r"\b(who|whom)\b[^?]*\b(made|built|created|developed|designed|owns?|owner|creator|author|developer|"
                r"maker|behind)\b[^?]*\b(you|this (project|app|bot|assistant|chatbot|tool|website|system)|"
                r"the (bis )?assistant)\b|\byour (owner|creator|developer|maker|author)\b|"
                r"किसने बनाया|kis\s*ne\s+banaya|(project|app|bot|assistant) (ka|ki) (owner|malik|maalik)", re.I), "who"),
    (re.compile(r"^\s*(what can you do|how can you help( me)?|what do you do|help|आप क्या कर सकते हैं)[\s!.?]*$", re.I), "can"),
]


def smalltalk(q: str, lang: str) -> str | None:
    """Greetings and small talk get a fixed reply (no search, no model)."""
    if GREETING.match(q):
        return prompts.GREETING_HI if lang == "hi" else prompts.GREETING_EN
    for pat, key in SMALLTALK:
        if (pat.search(q) if key == "who" else pat.match(q)):
            return prompts.SMALLTALK[key][lang == "hi"]
    return None
SUPPORT_THRESHOLD = 0.3   # reranker probability that a cited excerpt supports a sentence
RELEVANT_SCORE = 0.1      # a NOT_COVERED reply is re-asked once when the best excerpt scores at least this
                          # (off-topic questions score ~0.0003; answerable ones 0.02-0.99)
MAX_REMOVED = 0.4         # the citation check removing more than this share of sentences -> regenerate once
MIN_CHUNKS = 6            # never send fewer excerpts than this to the model (when retrieval found any)
CACHE_PATH = config.ROOT / "index" / "answer_cache.sqlite"


# ---------------------------------------------------------------- cache
def _index_version() -> str:
    paths = [config.BM25_PATH, config.ROOT / config.QDRANT_PATH]
    return "-".join(str(int(p.stat().st_mtime)) for p in paths if p.exists())


def _cache_key(q: str) -> str:
    """question + index version + the answer model of this run."""
    return hashlib.sha256(f"{q.lower().strip()}|{_index_version()}|{llm.primary_label()}".encode()).hexdigest()


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


PRODUCT_Q = re.compile(r"which (indian )?standard|which IS (no|number)|is (it |bis |isi )?(certification )?(compulsory|mandatory)|"
                       r"do i need|which scheme|want to (make|manufacture|import|sell|start)|\b(make|making|manufactur\w*|"
                       r"import\w*|sell\w*)\b.*\b(in india|bis|isi|crs)|made in|imported from|\bIS \d{2,5}\b", re.I)


def is_product_question(q: str, u: dict) -> bool:
    """'Which standard / is it compulsory / which scheme / I want to make, import or sell X' questions."""
    if PRODUCT_Q.search(q):
        return True
    return u.get("intent") in ("check_requirement", "advice") and bool((u.get("product_attrs") or {}).get("product_type"))


def fit_budget(chunks: list[dict], question: str, budget: int = CONTEXT_CHARS, min_chunks: int = MIN_CHUNKS) -> list[dict]:
    """Keep excerpts in rank order until the context budget is used; long excerpts are cut to the
    part most similar to the question (best_window). Never fewer than min_chunks: if they do not fit,
    every excerpt is cut shorter."""
    size = EXCERPT_CHARS
    while True:
        out, used = [], 0
        for c in chunks:
            text = c["text"] if len(c["text"]) <= size else best_window(question, c["text"], size)
            if out and used + len(text) > budget:
                break
            out.append({**c, "text": text})
            used += len(text)
        if len(out) >= min(min_chunks, len(chunks)) or size <= 300:
            return out
        size = max(300, budget // min(min_chunks, len(chunks)))


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
        elif line.strip() and not line.startswith((" ", "\t")) and not re.match(r"\s*([-*•]|[a-z][.)])\s", line):
            n = 0  # a new paragraph or heading ends the list (indented sub-points do not)
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


UNIT = r"(days?|months?|years?|weeks?|working days?|lakh|crore|%|per cent)"


def _quantities(text: str) -> set[str]:
    """'3 months', 'three months', '90 days' -> {'3 month', '90 day'}: a number together with its unit."""
    t = re.sub(r"\[\d+\]", " ", text.lower())
    for w, d in NUMBER_WORDS.items():
        t = re.sub(rf"\b{w}\b", d, t)
    return {f"{n.replace(',', '')} {u.rstrip('s').replace('working day', 'day')}"
            for n, u in re.findall(r"(\d[\d,]*)\s*(?:\(\s*\d+\s*\)\s*)?" + UNIT, t)}


def numbers_ok(claim: str, passage: str) -> bool:
    """Every number the claim states must appear in the passage (catches 'ten years' vs 'two years'), and
    every quantity with a unit ('3 months') must appear with the same unit."""
    return _numbers(claim) <= _numbers(passage) and _quantities(claim) <= _quantities(passage)


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


ADVICE_START = re.compile(
    r"^(visit|download|create|register|gather|keep|file|check|submit|apply|contact|open|use|read|study|prepare|"
    r"ensure|make sure|do not|don't|avoid|consider|plan|start|talk|call|log in|sign up|pay|upload|go to|note|"
    r"here's what|next step|not covered|this part is not covered|see|refer|look|search|save|ask|write|list|"
    r"compare|decide|choose|follow)\b", re.I)


def needs_citation(unit: str, claim: str) -> bool:
    """Does an uncited line state a fact that must be backed by the documents?
    Headings, links, "Next step:" and plain advice without numbers do not need a citation."""
    raw = unit.strip()
    if len(claim) < 25 or re.match(r"^\s*\|?\s*:?-{3,}", raw):
        return False
    if re.fullmatch(r"(#+\s.*|\*\*[^*]+\*\*:?|\d+\.\s+\*\*[^*]+\*\*:?)", raw) or (raw.endswith(":") and len(raw) < 80):
        return False  # headings
    body = re.sub(r"^\s*([-*•]|\d+[.)]|[a-z][.)])\s*", "", raw)
    body = re.sub(r"^\*\*[^*]{1,60}\*\*\s*[:–-]?\s*", "", body)  # "**Label**: ..."
    if ADVICE_START.match(body) and not re.search(r"\d", body):
        return False  # plain advice ("Visit Manak Online and create an account")
    if re.search(r"https?://", body) and len(re.sub(r"https?://\S+", "", body).split()) < 12:
        return False  # a link line
    return True


def drop_empty_tables(text: str) -> str:
    """A markdown table left with a header but no rows (e.g. after the citation check) is removed."""
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            block = lines[i:j]
            rows = [l for l in block[1:] if not re.match(r"^\s*\|?\s*:?-{3,}", l)]
            has_data = any(re.sub(r"[|\s\-–—:]|\[\d+\]|n/?a", "", r, flags=re.I) for r in rows)
            if has_data:
                out += block
            i = j
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def tidy(text: str) -> str:
    """After removals: drop empty tables, headings with nothing under them, stray markers like [8.1], renumber lists."""
    text = drop_empty_tables(text)
    text = re.sub(r"\s*\[\d+\.\d+\]", "", text)
    text = re.sub(r"(\[\d+\])\s*\((?:[ivx]+|[a-z])\)", r"\1", text)  # "[3] (d)" clause leftovers
    lines = text.split("\n")
    is_heading = lambda l: bool(re.fullmatch(r"\s*(#+\s.*|\*\*[^*]+\*\*:?|\d+\.\s+\*\*[^*]+\*\*:?)\s*", l))
    out = []
    for i, line in enumerate(lines):
        if is_heading(line):
            nxt = next((l for l in lines[i + 1:] if l.strip()), None)
            if nxt is None or is_heading(nxt):
                continue
        out.append(line)
    return renumber_lists(re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip())


def evidence(c: dict) -> str:
    """What a citation of this excerpt may rely on: the whole stored chunk (the prompt may hold only a window of it)
    plus its neighbouring chunks, so a rule split across a chunk boundary still counts as supported."""
    from app.retrieval import _store, neighbours
    try:
        full = _store()[0].get(c["chunk_id"])
    except Exception:  # no index (tests): the excerpt itself
        full = None
    if not full or " ".join(c["text"].split())[:200] not in " ".join(full["text"].split()):
        return c["text"]  # unknown id, or the id does not hold this excerpt
    nb = neighbours(full)
    return " ".join([n["text"] for n in nb[:1] if n["chunk_id"] < full["chunk_id"]] + [full["text"]]
                    + [n["text"] for n in nb if n["chunk_id"] > full["chunk_id"]])


def verify_citations(text: str, chunks: list[dict], language: str) -> tuple[str, list[dict]]:
    """Check each cited sentence against its excerpt(s) with the local reranker (two batched calls).
    Keep supported citations; re-cite to a better excerpt if one supports it; else remove the sentence."""
    if language != "en":
        return text, [], 0  # the local reranker is English-only; Hindi answers are not checked
    from app import rerank

    lines = text.split("\n")
    table_header = {i for i in range(len(lines) - 1) if re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1])}
    def splittable(line: str) -> bool:  # prose lines are checked sentence by sentence (never headings/tables):
        raw = line.strip()               # two sentences on one line may cite different excerpts
        return not raw.startswith(("|", "#"))
    units = [(li, SENTENCE_SPLIT.split(line) if splittable(line) else [line]) for li, line in enumerate(lines)]
    claims = []  # (line index, unit index, claim text, cited numbers); cited = [] for an uncited fact
    for li, parts in units:
        for ui, unit in enumerate(parts):
            nums = [int(x) for x in re.findall(r"\[(\d+)\]", unit)]
            claim = re.sub(r"\[\d+\]|\*\*|^\s*[-*\d.)]+\s*|\|", " ", unit)
            claim = " ".join(claim.split())
            cited = [n for n in dict.fromkeys(nums) if 1 <= n <= len(chunks)]
            if cited and len(claim) >= 25:
                claims.append((li, ui, claim, cited))
            elif not cited and li not in table_header and needs_citation(unit, claim):
                claims.append((li, ui, claim, []))
    is_row = {c: lines[li].lstrip().startswith("|") for li, _, c, _ in claims}
    # pass 1: each claim against the excerpts it cites
    ev = [evidence(c) for c in chunks]

    def full(n: int) -> str:  # title and section count too ("BIS Act, 2016", "Section 29(3)")
        c = chunks[n - 1]
        return f"{c['title']} {c.get('section', '')} {ev[n - 1]}"

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
        if is_row.get(claim) and words_covered(claim, n) >= 0.6:  # table rows read badly to a cross-encoder
            return max(score, 0.5)
        return score

    pairs = [(c, best_window(c, ev[n - 1])) for _, _, c, cited in claims for n in cited]
    it = iter(rerank.pair_scores(pairs))
    first = [[(n, support(c, cited, n, next(it))) for n in cited] for _, _, c, cited in claims]
    # pass 2: unsupported claims against every other excerpt
    failing = [i for i, sc in enumerate(first) if not any(s >= SUPPORT_THRESHOLD for _, s in sc)]
    # only excerpts that contain the claim's numbers are worth scoring (keeps the CPU cost low)
    def overlap(claim: str, n: int) -> int:
        return len(set(_WORD.findall(claim.lower())) & set(_WORD.findall(ev[n - 1].lower())))

    candidates = {i: sorted((n for n in range(1, len(chunks) + 1)
                             if n not in claims[i][3] and numbers_ok(claims[i][2], full(n))),
                            key=lambda n, c=claims[i][2]: -overlap(c, n))[:6]  # the 6 most similar excerpts
                  for i in failing}
    alt_pairs = [(claims[i][2], best_window(claims[i][2], ev[n - 1])) for i in failing for n in candidates[i]]
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
            n = best_alt[i][1]
            if cited:
                unit = re.sub(r"(?:\[\d+\])+", f"[{n}]", unit, count=1)
                unit = re.sub(r"(?<=\])(?:\[\d+\])+", "", unit)
                removed.append({"sentence": claim, "action": f"re-cited to [{n}]", "score": round(best_alt[i][0], 3)})
            else:  # an uncited fact that an excerpt does support: add the citation
                unit = (re.sub(r"\s*\|\s*$", f" [{n}] |", unit.rstrip()) if unit.lstrip().startswith("|")
                        else unit.rstrip() + f" [{n}]")
                removed.append({"sentence": claim, "action": f"uncited: cited to [{n}]", "score": round(best_alt[i][0], 3)})
        else:
            unit = None
            removed.append({"sentence": claim, "action": "removed" if cited else "removed (uncited, not in documents)",
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


# ---------------------------------------------------------------- model-output cleanup and refusal log
REFUSAL_LOG = config.ROOT / "data" / "refusals.jsonl"


def clean_model_output(raw) -> str:
    """Reasoning models (qwen3, gpt-oss) may return None, <think> blocks or odd citation styles.
    Turn every citation style into [n] so a good answer is never thrown away as 'no citations'."""
    text = raw or ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    text = re.sub(r"^.*?</think>", "", text, flags=re.S | re.I)          # unclosed think at the start
    text = re.sub(r"【\s*(\d+)[^】]*】", r"[\1]", text)                   # 【3†L1-L4】 -> [3]
    text = re.sub(r"\[\^(\d+)\]", r"[\1]", text)                          # [^3] -> [3]
    text = re.sub(r"\[(?:Excerpt|Source|Ref|excerpt|source)\s*#?\s*(\d+)\]", r"[\1]", text)  # [Excerpt 3]
    return text.strip()


def log_refusal(question, provider, reason, raw, chunks, removed=None):
    """Every refusal is written to data/refusals.jsonl with the raw model output, so we can see WHY."""
    try:
        with open(REFUSAL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "question": question,
                                "provider": provider, "reason": reason, "raw_output": (raw or "")[:4000],
                                "chunks": [c["chunk_id"] for c in chunks],
                                "removed": removed or []}, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[refusal-log] {e}")


# ---------------------------------------------------------------- main entry
def _result(answer, citations, provider, t0, trace, refused=False, cached=False, fallback=None):
    u = trace.get("understand") or {}
    profile = {k: u[k] for k in ("user_role", "product_or_topic", "user_goal") if k in u}
    return {"answer": answer, "citations": citations, "sources_used": len({c["source_id"] for c in citations}),
            "provider": provider, "fallback": fallback, "latency_ms": int((time.time() - t0) * 1000),
            "refused": refused, "cached": cached, "trace": trace, "profile": profile}  # profile kept even on "not covered"


RETRY_RELEVANT = ("\n\nThe excerpts are relevant: answer from them. Reply NOT_COVERED only if the question is not "
                  "about BIS at all.")
ONLY_SUPPORTING = ("\n\nWrite the answer again using ONLY these excerpts. State only what they say, each fact with its "
                   "[n]; for anything they do not cover write \"Not covered in my documents: <that part>\".")


def known_line(known: dict | None) -> str:
    known = {k: v for k, v in (known or {}).items() if v and k != "language"}
    return ("KNOWN ABOUT THE USER (from this conversation; use it to personalise, e.g. \"For your steel bottles under "
            f"IS 17803...\"; it is NOT a source): {json.dumps(known, ensure_ascii=False)}\n" if known else "")


def answer_prompt(q: str, chunks: list[dict], lang: str, u: dict | None = None, search_q: str = "",
                  tools_block: str = "", known: dict | None = None) -> str:
    u = u or {}
    return (f"CONTEXT:\n{format_context(chunks)}\n\n" + known_line(known)
            + (f"USER: role = {u.get('user_role', 'unknown')}; goal = {u.get('user_goal') or 'not stated'}; "
               f"product/topic = {u.get('product_or_topic') or 'not stated'}\nINTENT: {u.get('intent')}\n" if u else "")
            + (f"\n{tools_block}\nANSWER LAYOUT: product\n\n" if tools_block else "")
            + f"QUESTION ({'Hindi' if lang == 'hi' else 'English'}): {q}"
            + (f"\n(Meaning, with the earlier conversation: {search_q})" if search_q and search_q.lower() != q.lower() else ""))


def generate(prompt: str) -> tuple[str, str]:
    """One answer-model call (temperature 0: the same excerpts give the same answer)."""
    return llm.generate_with_provider(prompt, system=prompts.ANSWER, temperature=0.0, max_tokens=4096)


def said_not_covered(body: str) -> bool:
    return body.strip().upper().startswith("NOT_COVERED") or not re.search(r"\[\d+\]", body)


def ground(question: str, q: str, lang: str, chunks: list[dict], raw: str, provider: str, regen, stages: dict,
           max_rerank: float, u: dict | None, t0: float, trace: dict) -> dict:
    """Shared by the pipeline and the agent: model reply -> (retry once if NOT_COVERED on relevant excerpts)
    -> citation check -> (regenerate once from the supporting excerpts if > 40% removed) -> answer or refusal.
    regen(chunks, extra_instruction) -> (raw, provider) makes one more answer-model call."""
    providers = [provider]
    not_covered = prompts.NOT_COVERED_HI if lang == "hi" else prompts.NOT_COVERED_EN

    def refuse(reason: str, removed=None):
        stages["refusal_reason"] = reason
        trace["note"] = reason
        trace["raw_output"] = (raw or "")[:3000]
        log_refusal(question, providers[-1], reason, raw, chunks, removed)
        return _result(not_covered, [], providers[-1], t0, trace, refused=True, fallback=_fallback(providers))

    body = normalize_markers(split_body_and_sources(clean_model_output(raw)))
    stages["model_not_covered"] = said_not_covered(body)
    stages["retried_not_covered"] = False
    if stages["model_not_covered"] and max_rerank >= RELEVANT_SCORE:
        raw, prov = regen(chunks, RETRY_RELEVANT)
        providers.append(prov)
        body = normalize_markers(split_body_and_sources(clean_model_output(raw)))
        stages["retried_not_covered"] = True
        stages["model_not_covered_after_retry"] = said_not_covered(body)
    if said_not_covered(body):
        return refuse("model_not_covered")

    body = merge_duplicate_citations(body, chunks)
    t_ver = time.time()
    body, removed, n_checked = _check(body, chunks, lang)
    n_removed = sum(x["action"].startswith("removed") for x in removed)
    stages["regenerated"] = False
    if n_checked and n_removed / n_checked > MAX_REMOVED:
        keep = sorted({int(n) for n in re.findall(r"\[(\d+)\]", body) if 1 <= int(n) <= len(chunks)})
        if keep:
            sub = [chunks[n - 1] for n in keep]
            raw2, prov = regen(sub, ONLY_SUPPORTING)
            providers.append(prov)
            body2 = normalize_markers(split_body_and_sources(clean_model_output(raw2)))
            stages["regenerated"] = {"why": f"citation check removed {n_removed}/{n_checked} sentences",
                                     "kept_chunks": [c["chunk_id"] for c in sub]}
            if not said_not_covered(body2):
                body2, removed2, n2 = _check(merge_duplicate_citations(body2, sub), sub, lang)
                if re.search(r"\[\d+\]", body2):
                    raw, body, chunks, n_checked = raw2, body2, sub, n2
                    removed = removed + [{**x, "action": "after regenerate: " + x["action"]} for x in removed2]
    stages["removed"] = [x["sentence"] for x in removed if x["action"].split(": ")[-1].startswith("removed")]
    trace.update(citation_check=removed, claims_checked=n_checked, verify_ms=int((time.time() - t_ver) * 1000))
    body = tidy(merge_duplicate_citations(body, chunks))
    if not re.search(r"\[\d+\]", body):
        return refuse("check_removed_all", removed)
    answer, citations = finalize(body, chunks, lang)
    stages["refusal_reason"] = None
    return _result(answer, citations, providers[-1], t0, trace, fallback=_fallback(providers))


def _check(body: str, chunks: list[dict], lang: str):
    try:
        return verify_citations(body, chunks, lang)
    except Exception as e:  # never lose an answer because the checker failed; say so in the trace
        return body, [{"sentence": "", "action": f"citation check skipped: {type(e).__name__}: {e}"}], 0


def _fallback(providers: list[str]) -> str | None:
    """The provider label to show as 'FALLBACK: ...' if any call of this answer did not use the pinned model."""
    return next((f for f in (llm.fallback_of(p) for p in providers) if f), None)


def retrieval_stages(ret_trace: dict, sent: list[dict]) -> dict:
    return {"sub_queries": ret_trace.get("queries", []), "filters": ret_trace.get("filters", {}),
            "concept_terms": ret_trace.get("concept_terms", []), "per_query": ret_trace.get("per_query", []),
            "max_rerank": ret_trace.get("max_rerank"), "search_empty": ret_trace.get("search_empty", False),
            "sent_to_llm": [c["chunk_id"] for c in sent]}


REFERS_BACK = re.compile(r"\b((earlier|previous|above|last|your) (answer|reply|point|step|list)|step \d+|"
                         r"(that|this|those|the same) (document|standard|rule|step|one|answer|time|deadline)|"
                         r"the (first|second|third|last|\d+(st|nd|rd|th)) (standard|one|step|document|point)|"
                         r"you (mentioned|said|told)|the same|same in)\b", re.I)


def answer_language(question: str, q: str, profile: dict | None) -> str:
    """Asked for in this message ('in Hindi please') > written in Devanagari > English. One request = one answer."""
    ql = question.lower()
    if re.search(r"\b(in|into) hindi\b|हिंदी में|हिन्दी में", ql):
        return "hi"
    if re.search(r"\b(in|into) english\b", ql):
        return "en"
    return "hi" if detect_lang(q) == "hi" else "en"


def earlier_chunks(question: str, history: list[dict] | None) -> list[dict]:
    """'step 2 of your earlier answer', 'that document': the excerpts the last answer cited go back into the context."""
    if not history or not REFERS_BACK.search(question):
        return []
    from app.retrieval import _store
    by_id = _store()[0]
    last = next((t for t in reversed(history) if t["role"] == "assistant" and t.get("citations")), None)
    return [by_id[c] for c in (last or {}).get("citations", [])[:6] if c in by_id]


def ask(question: str, history: list[dict] | None = None, use_cache: bool = True, profile: dict | None = None) -> dict:
    """history: earlier turns [{role, content, citations?}] (app/memory.py); profile: what the session knows."""
    t0 = time.time()
    q = normalize(question)
    lang = answer_language(question, q, profile)
    if reply := smalltalk(q, lang):
        return _result(reply, [], "none", t0, {"step": "smalltalk", "stages": {"mode": "smalltalk"}})

    # step 1: understand the user (small model, JSON + schema; rules if it fails twice); a follow-up is rewritten
    # into a standalone question from the conversation and profile BEFORE searching
    prev = profile or next((t["profile"] for t in reversed(history or []) if t.get("profile")), {})
    t_u = time.time()
    u = understand(question, history, prev)
    profile = {k: u[k] for k in ("user_role", "product_or_topic", "user_goal")}
    search_q = u["standalone_question"]
    key = _cache_key(f"{search_q}|{u['intent']}|{u['user_role']}|{lang}")
    if use_cache and (hit := _cache("get", key)):
        hit["cached"], hit["latency_ms"] = True, int((time.time() - t0) * 1000)
        return hit

    # retrieval searches the user's own words (deterministic); with a conversation, the standalone rewrite
    retrieval_q = search_q if history else q
    ret = retrieve(retrieval_q, intent=u["intent"])
    back = earlier_chunks(question, history)
    if back:
        have = {c["chunk_id"] for c in back}
        ret["chunks"] = back + [c for c in ret["chunks"] if c["chunk_id"] not in have]
    tools_block, tool_trace = "", None
    if is_product_question(q, u):  # even when the search found nothing: "no product row" has its own cited rule
        # Standard Recommender + Scheme Selector: their evidence (product rows, rule proofs) comes first in the context
        from app.recommender import recommend_standards, select_scheme, tool_context
        t_tools = time.time()
        desc = f"{u['product_or_topic']} ({q})" if u.get("product_or_topic") else q
        rec = recommend_standards(desc, attrs=u.get("product_attrs") or {})
        sch = select_scheme({"role": u.get("user_role") if u.get("user_role") in ("importer", "jeweller") else "unknown"},
                            rec["candidates"], f"{q} {search_q}")
        tool_chunks, tools_block = tool_context(rec, sch)
        have = {c["chunk_id"] for c in tool_chunks}
        chunks = tool_chunks + fit_budget([c for c in ret["chunks"] if c["chunk_id"] not in have], search_q,
                                          budget=CONTEXT_CHARS // 2)
        tool_trace = {"candidates": [f"{c['is_number']} | {c['product_name'][:40]} | {c['compulsory']} | {c['scheme']}"
                                     for c in rec["candidates"]],
                      "schemes": [r["key"] for r in sch["results"]], "notes": len(sch["notes"]),
                      "profile": sch["profile"], "ms": int((time.time() - t_tools) * 1000)}
    else:
        chunks = fit_budget(ret["chunks"], search_q)
    stages = {"mode": "pipeline", "understand_ok": u.get("understand_ok"), "understand_attempts": u.get("attempts"),
              "intent": u["intent"], "rewritten_question": search_q if history else None,
              "reused_earlier_chunks": [c["chunk_id"] for c in back], "language": lang, **retrieval_stages(ret["trace"], chunks), "provider": None, "fallback": None}
    trace = {"stages": stages, "understand": {**u, "ms": int((time.time() - t_u) * 1000) - ret["trace"]["ms"]},
             "retrieval": ret["trace"], "tools": tool_trace,
             "chunks": [{"n": n, "chunk_id": c["chunk_id"], "title": c["title"], "section": c.get("section", "")[:80],
                         "scheme": c.get("scheme"), "page": c.get("page"), "rerank": c.get("rerank"),
                         "neighbour_of": c.get("neighbour_of")} for n, c in enumerate(chunks, start=1)]}
    if not chunks:  # the ONLY refusal before the model: retrieval found nothing about the question
        stages["refusal_reason"] = "search_empty"
        trace["note"] = "search_empty"
        not_covered = prompts.NOT_COVERED_HI if lang == "hi" else prompts.NOT_COVERED_EN
        res = _result(not_covered, [], "none", t0, trace, refused=True)
        _cache("put", key, res)
        return res

    def regen(sub: list[dict], extra: str):
        return generate(answer_prompt(q, sub, lang, u, search_q, tools_block if sub is chunks else "", prev) + extra)

    t_gen = time.time()
    raw, provider = generate(answer_prompt(q, chunks, lang, u, search_q, tools_block, prev))
    trace["generate_ms"] = int((time.time() - t_gen) * 1000)
    res = ground(question, q, lang, chunks, raw, provider, regen, stages, ret["trace"].get("max_rerank", 0.0),
                 u, t0, trace)
    stages["provider"], stages["fallback"] = res["provider"], res["fallback"]
    if not res["refused"]:
        res["profile"] = profile
    if not res["fallback"]:  # an answer from a fallback model is not cached (the next run should use the pinned one)
        _cache("put", key, res)
    return res
