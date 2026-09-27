"""Reasoning agent: plan -> call tools -> read -> reflect -> grounded answer (native function calling).

    ask(question, history=None, use_cache=True) -> same dict as app.answer.ask (answer, citations, trace, ...)

Tools return small JSON; every chunk a tool returns gets a number n (a registry shared by all tools), and the model
cites [n]. The final answer goes through the same citation check as the pipeline (app/answer.py).
Providers: Groq (OpenAI-style tools) -> Gemini (function declarations). If a provider fails mid-loop, the work so
far is handed to the next one as text. Limits: 6 tool calls, 45 s, older tool results trimmed to their best 3.
Set AGENT_MODE=off to use the old pipeline; any agent failure also falls back to it.
"""
import json
import re
import time
from datetime import date

import httpx
from google.genai import errors as gerrors
from google.genai import types

from app import config, llm, prompts
from app.expand import detect_lang, normalize

MAX_TOOL_CALLS, MAX_SECONDS, MAX_CONTEXT_CHARS = 6, 45, 45_000

TOOLS = [
    {"name": "search_documents",
     "description": "Search the official BIS documents (Act, Rules, Regulations, guidelines, FAQs, QCOs, product lists). "
                    "Write a focused English query. Returns excerpts numbered n; cite them as [n].",
     "parameters": {"type": "object", "properties": {
         "query": {"type": "string"},
         "scheme": {"type": "string", "description": "optional filter: I, II, IV, X, FMCS or Hallmarking"},
         "doc_type": {"type": "string", "description": "optional filter: act, rule, regulation, order, qco, faq, guideline, page"},
         "source": {"type": "string", "description": "optional source_id prefix, e.g. bis_act_2016 or guide_"},
         "k": {"type": "integer", "description": "number of results, default 8"}},
         "required": ["query"]}},
    {"name": "lookup_product",
     "description": "Find the Indian Standard(s) for a product (name, description or IS number) in the BIS product "
                    "lists: IS number, whether certification is compulsory, the QCO (S.O. number, date) and the scheme.",
     "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "select_scheme",
     "description": "Decide which BIS scheme applies (Scheme I ISI licence, FMCS, CRS Scheme II, Hallmarking, or none) "
                    "for a product and the user's situation; returns the rule, next steps and source excerpts.",
     "parameters": {"type": "object", "properties": {
         "product": {"type": "string"},
         "maker_location": {"type": "string", "description": "india, foreign or unknown"},
         "role": {"type": "string", "description": "manufacturer, importer, trader, jeweller, consumer or unknown"},
         "is_electronics_it": {"type": "boolean"}, "is_precious_metal": {"type": "boolean"}},
         "required": ["product"]}},
    {"name": "get_chunk_neighbours",
     "description": "Read the text just before and after an excerpt (by its number n) when a rule seems cut off.",
     "parameters": {"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"]}},
]


def system_prompt() -> str:
    return f"""Today is {date.today():%d %B %Y}. You are the BIS Assistant, an expert advisor on the Bureau of Indian Standards.

HOW YOU WORK
1. Plan: work out who the user is (manufacturer in India, foreign maker, importer, jeweller, consumer...), what they
   want, and which parts the question has. Off-topic questions (not BIS / standards / certification / hallmarking /
   consumer BIS matters): reply exactly NOT_COVERED without calling tools.
2. Use tools to find evidence: search_documents with focused queries (and filters when useful), lookup_product for
   products or IS numbers, select_scheme to decide the scheme, get_chunk_neighbours to finish a cut-off rule.
   When the user asks what to do about a product (certify, import, sell, register), call select_scheme so the
   steps come from the documents.
3. Reflect before answering: which parts of the question are still unanswered? Do the sources match the user's
   situation (Indian vs foreign maker, this product, this scheme)? If a gap can be fixed, search again. If not, say
   "Not covered in my documents: <part>".
4. Answer. You have at most {MAX_TOOL_CALLS} tool calls.

The numbered excerpts in the tool results are your CONTEXT: cite them as [n] using the "n" values.

""" + prompts.ANSWER


# ---------------------------------------------------------------- tools
class Registry:
    """Every chunk any tool returns gets a stable number n (1-based) for citation."""

    def __init__(self):
        self.chunks, self.index = [], {}

    def add(self, chunk: dict) -> int:
        cid = chunk["chunk_id"]
        if cid not in self.index:
            self.chunks.append(chunk)
            self.index[cid] = len(self.chunks)
        return self.index[cid]


def _brief(reg: Registry, c: dict, focus: str, width: int = 600) -> dict:
    from app.answer import best_window
    n = reg.add(c)
    return {"n": n, "title": c["title"][:90], "section": (c.get("section") or "")[:80], "page": c.get("page"),
            "scheme": c.get("scheme"), "date": c.get("doc_date") or "", "text": " ".join(best_window(focus, c["text"], width).split())}


def t_search_documents(reg, query, scheme=None, doc_type=None, source=None, k=8):
    from app.retrieval import _dedupe_key, bm25_search, rrf, vector_search_many
    q = normalize(query)
    fused = rrf(vector_search_many([q], 40)[0], bm25_search(q, None, 40))
    out, seen = [], set()
    for c in fused:
        if scheme and c.get("scheme") not in (scheme, "general"):
            continue
        if doc_type and c.get("doc_type") != doc_type:
            continue
        if source and not c["source_id"].startswith(source):
            continue
        key = _dedupe_key(c)
        if key in seen:
            continue
        seen.add(key)
        out.append(_brief(reg, c, q))
        if len(out) >= min(int(k or 8), 10):
            break
    return {"results": out}


def t_lookup_product(reg, text):
    from app.recommender import recommend_standards
    from app.retrieval import _store
    by_id, _ = _store()
    rec = recommend_standards(text, attrs={})  # attrs given: no extra LLM call
    out = []
    for c in rec["candidates"]:
        row = by_id.get(c["source"]["row_chunk_id"])
        n = reg.add(row) if row else None
        out.append({"n": n, "is_number": c["is_number"], "product": c["product_name"], "compulsory": c["compulsory"],
                    "scheme": c["scheme"], "qco": c["qco"]["title"][:160], "qco_so_number": c["qco"]["so_number"],
                    "qco_date": c["qco"]["date"], "confidence": c["confidence"],
                    **({"deciding_factor": c["deciding_factor"]} if c.get("deciding_factor") else {})})
    return {"products": out, "note": "" if out else "no matching product in the BIS compulsory-certification lists"}


def t_select_scheme(reg, product, maker_location="unknown", role="unknown", is_electronics_it=False, is_precious_metal=False):
    from app.answer import best_window
    from app.recommender import recommend_standards, select_scheme
    from app.retrieval import _store
    by_id, _ = _store()
    cands = recommend_standards(product, attrs={"precious_metal": is_precious_metal})["candidates"] if product else []
    sch = select_scheme({"maker_location": maker_location, "role": role, "is_electronics_it": is_electronics_it,
                         "is_precious_metal": is_precious_metal}, cands, product)

    def ref(cid, focus):
        return reg.add({**by_id[cid], "text": best_window(focus, by_id[cid]["text"], 1500)}) if cid in by_id else None

    results = []
    for r in sch["results"]:
        results.append({"scheme": r["scheme"], **({"case": r["case"]} if r.get("case") else {}), "why": r["why"],
                        "why_sources": [ref(x, r["why"]) for x in r["why_sources"]], "compulsory": r["compulsory"],
                        "steps": [{"text": s["text"], "n": ref(s["proof"], s["text"])} for s in r["next_steps"]],
                        "portal": r["portal"]})
    for c in cands[:3]:
        row = by_id.get(c["source"]["row_chunk_id"])
        if row:
            reg.add(row)
    return {"results": results, "notes": [{"text": x["text"], "n": ref(x["proof"], x["text"])} for x in sch["notes"]],
            "products": [{"is_number": c["is_number"], "product": c["product_name"], "scheme": c["scheme"],
                          "n": reg.index.get(c["source"]["row_chunk_id"])} for c in cands[:3]]}


def t_get_chunk_neighbours(reg, n):
    from app.retrieval import neighbours
    n = int(n)
    if not 1 <= n <= len(reg.chunks):
        return {"error": f"no excerpt {n}"}
    base = reg.chunks[n - 1]
    return {"results": [_brief(reg, c, base["text"][:200], 900) for c in neighbours(base)]}


TOOL_FUNCS = {"search_documents": t_search_documents, "lookup_product": t_lookup_product,
              "select_scheme": t_select_scheme, "get_chunk_neighbours": t_get_chunk_neighbours}


def run_tool(reg: Registry, name: str, args: dict) -> dict:
    fn = TOOL_FUNCS.get(name)
    if not fn:
        return {"error": f"unknown tool {name}"}
    try:
        return fn(reg, **{k: v for k, v in (args or {}).items() if v not in (None, "")})
    except TypeError as e:
        return {"error": f"bad arguments: {e}"}
    except Exception as e:  # a tool failure is reported to the model, never hidden
        return {"error": f"{type(e).__name__}: {str(e)[:150]}"}


# ---------------------------------------------------------------- providers (one step = one model call)
def groq_step(messages: list[dict], allow_tools: bool) -> dict:
    body = {"model": config.GROQ_MODEL, "messages": messages, "temperature": 0.1, "max_tokens": 3000}
    if "gpt-oss" in config.GROQ_MODEL:
        body["reasoning_effort"] = "low"
    if allow_tools:
        body["tools"] = [{"type": "function", "function": t} for t in TOOLS]
        body["tool_choice"] = "auto"
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                   headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"}, json=body, timeout=llm.CALL_TIMEOUT_S)
    r.raise_for_status()
    m = r.json()["choices"][0]["message"]
    calls = [{"id": tc["id"], "name": tc["function"]["name"], "args": json.loads(tc["function"]["arguments"] or "{}")}
             for tc in (m.get("tool_calls") or [])]
    return {"content": llm.clean_text(m.get("content") or ""), "tool_calls": calls, "provider": f"groq:{config.GROQ_MODEL}"}


def _gemini_contents(messages: list[dict]) -> list:
    out = []
    for m in messages[1:]:  # messages[0] is the system prompt
        if m["role"] == "user":
            out.append(types.Content(role="user", parts=[types.Part(text=m["content"])]))
        elif m["role"] == "assistant":
            out.append(m["_gemini"])  # the model's own content, with its thought signatures
        elif m["role"] == "tool":
            out.append(types.Content(role="user", parts=[types.Part.from_function_response(
                name=m["name"], response={"result": json.loads(m["content"])})]))
    return out


def gemini_step(messages: list[dict], allow_tools: bool) -> dict:
    decls = [types.FunctionDeclaration(name=t["name"], description=t["description"], parameters=t["parameters"])
             for t in TOOLS]
    cfg = types.GenerateContentConfig(
        system_instruction=messages[0]["content"], temperature=0.1, max_output_tokens=3000,
        tools=[types.Tool(function_declarations=decls)] if allow_tools else None,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
    used = {}

    def call(c, m):
        resp = c.models.generate_content(model=m, contents=_gemini_contents(messages), config=cfg)
        used["model"] = m
        return resp

    resp = llm._call(call, llm.model_chain(config.GEMINI_MODEL), rounds=1)
    content = resp.candidates[0].content
    calls = [{"id": f"g{i}", "name": p.function_call.name, "args": dict(p.function_call.args or {})}
             for i, p in enumerate(content.parts or []) if p.function_call]
    text = "".join(p.text for p in (content.parts or []) if getattr(p, "text", None) and not getattr(p, "thought", False))
    return {"content": llm.clean_text(text), "tool_calls": calls, "provider": f"gemini:{used['model']}", "_gemini": content}


PROVIDERS = [("groq", groq_step, lambda: bool(config.GROQ_API_KEY)), ("gemini", gemini_step, lambda: config.KEY_IS_SET)]


def _fallback_error(e: Exception) -> bool:
    if isinstance(e, httpx.HTTPStatusError):
        return e.response.status_code in (408, 413, 429, 500, 502, 503, 504)
    return isinstance(e, (httpx.HTTPError, llm.AllModelsBusy, TimeoutError)) or (
        isinstance(e, gerrors.APIError) and e.code in (429, 500, 503, 504)) or "timed out" in str(e).lower()


def _as_text_history(messages: list[dict]) -> list[dict]:
    """Hand the work so far to another provider: tool calls/results become plain text in the user message."""
    parts = [m for m in messages[2:] if m["role"] == "tool"]
    done = "\n".join(f"- {m['name']}: {m['content'][:4000]}" for m in parts)
    user = messages[1]["content"] + (f"\n\nTool results so far (excerpts keep their numbers n):\n{done}" if done else "")
    return [messages[0], {"role": "user", "content": user}]


def _trim(messages: list[dict]):
    """Keep the context small: older tool results keep only their best 3 items."""
    tools = [m for m in messages if m["role"] == "tool"]
    while sum(len(m.get("content") or "") for m in messages) > MAX_CONTEXT_CHARS and len(tools) > 1:
        m = tools.pop(0)
        data = json.loads(m["content"])
        for key in ("results", "products"):
            if isinstance(data.get(key), list):
                data[key] = data[key][:3]
                for x in data[key]:
                    if isinstance(x, dict) and "text" in x:
                        x["text"] = x["text"][:300]
        m["content"] = json.dumps(data, ensure_ascii=False)


# ---------------------------------------------------------------- the loop
def run_agent(question: str, history: list[dict] | None = None) -> dict:
    t0 = time.time()
    reg, steps = Registry(), []
    convo = "\n".join(f"{t['role']}: {t['content'][:400]}" for t in (history or [])[-6:])
    user = (f"Earlier conversation:\n{convo}\n\n" if convo else "") + f"Question: {question}"
    messages = [{"role": "system", "content": system_prompt()}, {"role": "user", "content": user}]
    providers = [p for p in PROVIDERS if p[2]()]
    calls, final, provider = 0, None, "none"
    while providers:
        name, step, _ = providers[0]
        out_of_budget = calls >= MAX_TOOL_CALLS or time.time() - t0 > MAX_SECONDS
        if out_of_budget and messages[-1]["role"] == "tool":
            messages.append({"role": "user", "content": "Tool budget used. Reflect once more and write the final answer "
                                                        "from the excerpts you have; say which parts are not covered."})
        try:
            resp = step(messages, allow_tools=not out_of_budget)
        except Exception as e:
            if not _fallback_error(e):
                raise
            steps.append({"step": "provider_failed", "provider": name, "error": f"{type(e).__name__}: {str(e)[:100]}"})
            providers.pop(0)
            messages = _as_text_history(messages)
            continue
        provider = resp["provider"]
        if not resp["tool_calls"]:
            final = resp["content"]
            break
        messages.append({"role": "assistant", "content": resp["content"] or None,
                         "tool_calls": [{"id": c["id"], "type": "function",
                                         "function": {"name": c["name"], "arguments": json.dumps(c["args"])}}
                                        for c in resp["tool_calls"]], **({"_gemini": resp["_gemini"]} if "_gemini" in resp else {})})
        for c in resp["tool_calls"]:
            t1 = time.time()
            result = run_tool(reg, c["name"], c["args"]) if calls < MAX_TOOL_CALLS else {"error": "tool budget used"}
            calls += c["name"] in TOOL_FUNCS
            messages.append({"role": "tool", "tool_call_id": c["id"], "name": c["name"],
                             "content": json.dumps(result, ensure_ascii=False)})
            steps.append({"step": "tool", "tool": c["name"], "args": c["args"], "provider": provider,
                          "returned": len(result.get("results") or result.get("products") or []),
                          "error": result.get("error"), "ms": int((time.time() - t1) * 1000)})
        _trim(messages)
    if final is None:
        raise llm.ProviderError("no provider could finish the agent loop: " + "; ".join(s.get("error", "") for s in steps))
    return {"text": final, "registry": reg, "steps": steps, "tool_calls": calls, "provider": provider,
            "ms": int((time.time() - t0) * 1000)}


def ask(question: str, history: list[dict] | None = None, use_cache: bool = True) -> dict:
    from app import answer as A

    if config.AGENT_MODE != "on":
        return A.ask(question, history, use_cache)
    t0 = time.time()
    q = normalize(question)
    lang = detect_lang(q)
    if A.GREETING.match(q):
        return A._result(prompts.GREETING_HI if lang == "hi" else prompts.GREETING_EN, [], "none", t0, {"step": "greeting"})
    key = A._cache_key(f"agent|{q}|{len(history or [])}")
    if use_cache and not history and (hit := A._cache("get", key)):
        hit["cached"], hit["latency_ms"] = True, int((time.time() - t0) * 1000)
        return hit
    try:
        run = run_agent(q, history)
    except Exception as e:  # the demo never breaks: fall back to the pipeline
        print(f"[agent] falling back to the pipeline ({type(e).__name__}: {str(e)[:120]})")
        res = A.ask(question, history, use_cache)
        res["trace"]["agent_fallback"] = f"{type(e).__name__}: {str(e)[:200]}"
        return res
    chunks = run["registry"].chunks
    trace = {"agent": {"steps": run["steps"], "tool_calls": run["tool_calls"], "ms": run["ms"]},
             "chunks": [{"n": n, "chunk_id": c["chunk_id"], "title": c["title"], "section": (c.get("section") or "")[:80],
                         "page": c.get("page"), "scheme": c.get("scheme")} for n, c in enumerate(chunks, start=1)]}
    not_covered = prompts.NOT_COVERED_HI if lang == "hi" else prompts.NOT_COVERED_EN
    body = A.normalize_markers(A.split_body_and_sources(A.clean_model_output(run["text"])))
    if not chunks or body.strip().upper().startswith("NOT_COVERED") or not re.search(r"\[\d+\]", body):
        trace["note"] = "model said NOT_COVERED" if body.strip().upper().startswith("NOT_COVERED") else "no cited answer"
        res = A._result(not_covered, [], run["provider"], t0, trace, refused=True)
        A._cache("put", key, res)
        return res
    body = A.merge_duplicate_citations(body, chunks)
    t_ver = time.time()
    try:
        body, removed, n_checked = A.verify_citations(body, chunks, lang)
    except Exception as e:
        removed, n_checked = [{"sentence": "", "action": f"citation check skipped: {type(e).__name__}: {e}"}], 0
    trace.update(citation_check=removed, claims_checked=n_checked, verify_ms=int((time.time() - t_ver) * 1000))
    body = A.tidy(A.merge_duplicate_citations(body, chunks))
    if not re.search(r"\[\d+\]", body):
        trace["note"] = "citation check removed every sentence"
        return A._result(not_covered, [], run["provider"], t0, trace, refused=True)
    if not re.search(r"(?im)^\W*next step\s*:", body):
        body += "\n\n" + A.default_next_step({"standalone_question": q}, lang)
    text, citations = A.finalize(body, chunks, lang)
    res = A._result(text, citations, run["provider"], t0, trace)
    A._cache("put", key, res)
    return res
