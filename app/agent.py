"""Reasoning agent: plan -> call tools -> read -> reflect -> grounded answer (native function calling).

    ask(question, history=None, use_cache=True) -> same dict as app.answer.ask (answer, citations, trace, ...)

Tools return small JSON; every chunk a tool returns gets a number n (a registry shared by all tools), and the model
cites [n]. The final answer goes through the same citation check as the pipeline (app/answer.py).
Providers: the pinned ANSWER_PROVIDER first (Groq: OpenAI-style tools; Gemini: function declarations), temperature 0.
If it fails mid-loop, the work so far is handed to the other one as text and the answer says "FALLBACK: <provider>".
search_documents uses the same deterministic retrieve() as the pipeline (concept expansion, rerank, filters).
Limits: 6 tool calls, 45 s, older tool results trimmed to their best 3.
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
Intent: a simple "what is X / what does X mean / difference between X and Y" question is intent basic.

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
    from app.retrieval import retrieve
    q = normalize(query)
    ret = retrieve(q, top_k=max(6, min(int(k or 8), 10)), with_neighbours=False,
                   filters={"scheme": scheme, "doc_type": doc_type, "source": source})
    t = ret["trace"]
    return {"results": [_brief(reg, c, q) for c in ret["chunks"]],
            "_stats": {"query": q, "filters": t["filters"], "concept_terms": t["concept_terms"],
                       "count": len(ret["chunks"]), "max_rerank": t["max_rerank"], "search_empty": t["search_empty"],
                       "top3": [[c["chunk_id"], c.get("rerank")] for c in ret["chunks"][:3]]}}


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
                    **({"when_it_applies": c["when_it_applies"]} if c.get("when_it_applies") else {}),
                    **({"deciding_factor": c["deciding_factor"]} if c.get("deciding_factor") else {})})
    if out:
        return {"products": out, "note": ""}
    # no product row: the cited rule for that case (compulsory only when notified, else voluntary)
    return {"products": [], "note": "no matching product in the BIS compulsory-certification lists",
            "rule": t_select_scheme(reg, text)["results"]}


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
    body = {"model": config.GROQ_MODEL, "messages": messages, "temperature": 0.0, "max_tokens": 3000, "seed": llm.SEED}
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
        system_instruction=messages[0]["content"], temperature=0.0, max_output_tokens=3000, seed=llm.SEED,
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


def _providers() -> list:
    """The pinned answer provider first; the other one only as a (visible) fallback."""
    first = llm.primary_label().split(":")[0]
    return sorted([p for p in PROVIDERS if p[2]()], key=lambda p: p[0] != first)


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
def run_agent(question: str, history: list[dict] | None = None, known: dict | None = None, lang: str = "en",
              earlier: list[dict] | None = None) -> dict:
    t0 = time.time()
    reg, steps = Registry(), []
    convo = "\n".join(f"{t['role']}: {t['content'][:600]}" for t in (history or [])[-7:])
    back = [_brief(reg, c, question, 900) for c in (earlier or [])]
    # every run starts from the same evidence: one deterministic search of the user's own words
    first = t_search_documents(reg, question)
    stats = first.pop("_stats")
    steps.append({"step": "tool", "tool": "search_documents", "args": {"query": question}, "provider": "fixed first search",
                  "returned": len(first["results"]), "error": None, "ms": 0, "search": stats})
    from app.answer import known_line
    user = ((f"Earlier conversation (for understanding only, never a source):\n{convo}\n\n" if convo else "")
            + known_line(known)
            + (f"Excerpts your earlier answer cited: {json.dumps(back, ensure_ascii=False)}\n\n" if back else "")
            + f"Question: {question}\n" + ("Answer in Hindi.\n" if lang == "hi" else "") + "\n"
            + ("Search results for the question as written (excerpts numbered n; search again only for parts they "
               f"do not cover):\n{json.dumps(first, ensure_ascii=False)}" if first["results"]
               else "A search for the question as written found nothing relevant in the BIS documents."))
    messages = [{"role": "system", "content": system_prompt()}, {"role": "user", "content": user}]
    providers = _providers()
    calls, final, provider, used = 0, None, "none", []
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
        used.append(provider)
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
            stats = result.pop("_stats", None)
            calls += c["name"] in TOOL_FUNCS
            messages.append({"role": "tool", "tool_call_id": c["id"], "name": c["name"],
                             "content": json.dumps(result, ensure_ascii=False)})
            steps.append({"step": "tool", "tool": c["name"], "args": c["args"], "provider": provider,
                          "returned": len(result.get("results") or result.get("products") or []),
                          "error": result.get("error"), "ms": int((time.time() - t1) * 1000),
                          **({"search": stats} if stats else {})})
        _trim(messages)
    if final is None:
        raise llm.ProviderError("no provider could finish the agent loop: " + "; ".join(s.get("error") or "" for s in steps))
    return {"text": final, "registry": reg, "steps": steps, "tool_calls": calls, "provider": provider,
            "providers_used": used, "ms": int((time.time() - t0) * 1000)}


def ask(question: str, history: list[dict] | None = None, use_cache: bool = True, profile: dict | None = None) -> dict:
    from app import answer as A
    from app.retrieval import retrieve

    if config.AGENT_MODE != "on":
        return A.ask(question, history, use_cache, profile)
    t0 = time.time()
    q = normalize(question)
    lang = A.answer_language(question, q, profile)
    if reply := A.smalltalk(q, lang):
        return A._result(reply, [], "none", t0, {"step": "smalltalk", "stages": {"mode": "smalltalk"}})
    u, rewritten = None, None
    if history:  # a follow-up becomes a standalone question BEFORE any search
        from app.understand import understand
        u = understand(question, history, profile)
        rewritten = u["standalone_question"]
        q = rewritten
    key = A._cache_key(f"agent|{q}|{lang}")
    if use_cache and (hit := A._cache("get", key)):
        hit["cached"], hit["latency_ms"] = True, int((time.time() - t0) * 1000)
        return hit
    earlier = A.earlier_chunks(question, history)
    try:
        run = run_agent(q, history, profile, lang, earlier)
    except Exception as e:  # the demo never breaks: fall back to the pipeline
        print(f"[agent] falling back to the pipeline ({type(e).__name__}: {str(e)[:120]})")
        res = A.ask(question, history, use_cache, profile)
        res["trace"]["agent_fallback"] = f"{type(e).__name__}: {str(e)[:200]}"
        res["trace"].setdefault("stages", {})["agent_fallback"] = res["trace"]["agent_fallback"]
        return res
    chunks, raw = run["registry"].chunks, run["text"]
    searches = [s["search"] for s in run["steps"] if s.get("search")]
    stages = {"mode": "agent", "understand_ok": (u or {}).get("understand_ok", "n/a (no conversation yet)"),
              "intent": (u or {}).get("intent"), "rewritten_question": rewritten, "language": lang,
              "reused_earlier_chunks": [c["chunk_id"] for c in earlier],
              "sub_queries": [s["query"] for s in searches], "filters": [s["filters"] for s in searches],
              "concept_terms": sorted({t for s in searches for t in s["concept_terms"]}),
              "per_query": [{k: s[k] for k in ("query", "count", "top3")} for s in searches],
              "tools": [s["tool"] for s in run["steps"] if s["step"] == "tool"],
              "provider": None, "fallback": None}
    if not chunks:
        # the agent found or read nothing: decide from one deterministic search, never from the model alone
        ret = retrieve(q)
        stages["own_search"] = True
        stages["per_query"] += [{k: v for k, v in pq.items()} for pq in ret["trace"]["per_query"]]
        chunks = A.fit_budget(ret["chunks"], q)
        max_rerank = ret["trace"]["max_rerank"]
        raw = "NOT_COVERED"  # an answer written without excerpts cannot be grounded
    else:
        max_rerank = max((c.get("rerank") or 0.0 for c in chunks), default=0.0)
        if max_rerank < A.RELEVANT_SCORE and not all("rerank" in c for c in chunks):
            from app import rerank
            max_rerank = max([max_rerank] + rerank.scores(q, [c["text"][:800] for c in chunks]))
    stages.update(sent_to_llm=[c["chunk_id"] for c in chunks], max_rerank=round(max_rerank, 4),
                  search_empty=not chunks)
    trace = {"stages": stages, "understand": u, "agent": {"steps": run["steps"], "tool_calls": run["tool_calls"], "ms": run["ms"]},
             "chunks": [{"n": n, "chunk_id": c["chunk_id"], "title": c["title"], "section": (c.get("section") or "")[:80],
                         "page": c.get("page"), "scheme": c.get("scheme"), "rerank": c.get("rerank")}
                        for n, c in enumerate(chunks, start=1)]}
    if not chunks:
        stages["refusal_reason"] = "search_empty"
        trace["note"] = "search_empty"
        res = A._result(prompts.NOT_COVERED_HI if lang == "hi" else prompts.NOT_COVERED_EN, [], run["provider"], t0,
                        trace, refused=True, fallback=A._fallback(run["providers_used"]))
        stages["provider"], stages["fallback"] = res["provider"], res["fallback"]
        A._cache("put", key, res)
        return res

    def regen(sub: list[dict], extra: str):
        return A.generate(A.answer_prompt(q, sub, lang, known=profile) + extra)

    res = A.ground(question, q, lang, chunks, raw, run["provider"], regen, stages, max_rerank, None, t0, trace)
    res["fallback"] = res["fallback"] or A._fallback(run["providers_used"])
    stages["provider"], stages["fallback"] = res["provider"], res["fallback"]
    if not res["fallback"]:
        A._cache("put", key, res)
    return res
