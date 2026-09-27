"""FastAPI server:  uvicorn app.api:app --port 8000

POST /chat           {message, session_id} -> {answer, citations, sources_used, latency_ms, provider, trace}
POST /chat/stream    same, as Server-Sent Events: status, token..., citations, trace, done
POST /search         {query} -> the raw retrieval result (for checking accuracy)
GET  /health         providers, embeddings, index counts
GET  /sources        every indexed document with date and page count
POST /admin/reindex  re-parse, re-chunk, re-index (including data/manual/) in the background
"""
import json
import re
import subprocess
import sys
import threading
import time
from collections import defaultdict, deque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from starlette.concurrency import iterate_in_threadpool

from app import config
from app.answer import ask
from app.retrieval import reload, retrieve

app = FastAPI(title="BIS Assistant API", version="0.2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# short in-memory history per session, only so follow-up questions work (never written to disk)
HISTORY: dict[str, deque] = defaultdict(lambda: deque(maxlen=12))  # last 6 turns
REINDEX = {"running": False, "started": None, "finished": None, "log": ""}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field("default", max_length=100)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class RecommendRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=2000)


class SchemeRequest(BaseModel):
    profile: dict = Field(default_factory=dict)  # maker_location, role, product, is_electronics_it, is_precious_metal


def _remember(session_id: str, message: str, result: dict):
    short = re.split(r"\n\n\*\*(?:Sources|स्रोत):\*\*", result["answer"])[0][:1500]
    HISTORY[session_id].extend([{"role": "user", "content": message},
                                {"role": "assistant", "content": short, "profile": result.get("profile")}])


def _chat(req: ChatRequest) -> dict:
    result = ask(req.message, list(HISTORY[req.session_id]))
    _remember(req.session_id, req.message, result)
    return result


@app.get("/")
def root():
    return {"name": "BIS Assistant API", "docs": "/docs",
            "endpoints": ["POST /chat", "POST /chat/stream", "POST /search", "POST /recommend", "POST /scheme", "GET /health", "GET /sources",
                          "POST /admin/reindex"]}


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        return _chat(req)
    except Exception as e:  # show the real error, never a fake refusal
        return {"error": f"{type(e).__name__}: {e}"}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    def events():
        yield {"event": "status", "data": json.dumps({"message": "Searching official BIS documents"})}
        try:
            result = _chat(req)
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"message": f"{type(e).__name__}: {e}"})}
            return
        for m in re.finditer(r"\S+\s*", result["answer"]):
            yield {"event": "token", "data": json.dumps({"text": m.group(0)}, ensure_ascii=False)}
        yield {"event": "citations", "data": json.dumps(result["citations"], ensure_ascii=False)}
        yield {"event": "trace", "data": json.dumps(result["trace"], ensure_ascii=False)}
        yield {"event": "done", "data": json.dumps({k: result[k] for k in ("provider", "latency_ms", "sources_used",
                                                                            "refused", "cached")})}
    return EventSourceResponse(iterate_in_threadpool(events()))


@app.post("/recommend")
def recommend(req: RecommendRequest):
    """Standard Recommender: candidate Indian Standards for a product description (JSON for the web UI)."""
    from app.recommender import recommend_standards
    return recommend_standards(req.description)


@app.post("/scheme")
def scheme(req: SchemeRequest):
    """Scheme Selector: which BIS scheme applies, why, next steps and sources, for a profile."""
    from app.recommender import recommend_standards, select_scheme
    p = req.profile
    product = str(p.get("product") or "")
    rec = recommend_standards(product, attrs={"precious_metal": p.get("is_precious_metal", False)}) if product else {"candidates": []}
    return {"candidates": rec["candidates"], **select_scheme(p, rec["candidates"], product)}


@app.post("/search")
def search(req: SearchRequest):
    r = retrieve(req.query)
    return {"question": r["question"], "trace": r["trace"],
            "chunks": [{k: c.get(k) for k in ("chunk_id", "title", "section", "scheme", "page", "doc_date", "url",
                                              "adj_score", "rerank", "final_score", "neighbour_of")}
                       | {"text": c["text"][:600]} for c in r["chunks"]]}


def _count_points() -> int | None:
    try:
        from app.retrieval import _qdrant
        return _qdrant().count(config.COLLECTION).count
    except Exception:
        return None


@app.get("/health")
def health():
    n_chunks = sum(1 for _ in config.CHUNKS_PATH.open()) if config.CHUNKS_PATH.exists() else 0
    docs = {json.loads(l)["source_id"] for l in config.CHUNKS_PATH.open()} if n_chunks else set()
    return {"status": "ok",
            "llm": {"order": ["gemini", "groq", "ollama"], "gemini_model": config.GEMINI_MODEL,
                    "gemini_keys": len(config.GEMINI_API_KEYS), "groq": bool(config.GROQ_API_KEY),
                    "groq_model": config.GROQ_MODEL, "ollama_model": config.OLLAMA_MODEL},
            "embeddings": config.EMBED_PROVIDER + ":" + (config.OLLAMA_EMBED_MODEL if config.EMBED_PROVIDER == "ollama"
                                                         else config.GEMINI_EMBED_MODEL),
            "index": {"chunks": n_chunks, "vectors": _count_points(), "documents": len(docs),
                      "bm25": config.BM25_PATH.exists()},
            "reindex": REINDEX}


@app.get("/sources")
def sources():
    parsed = config.DATA / "processed" / "parsed.jsonl"
    pages = {}
    if parsed.exists():
        for line in parsed.open(encoding="utf-8"):
            d = json.loads(line)
            pages[d["source_id"]] = len(d["pages"])
    docs: dict[str, dict] = {}
    for line in config.CHUNKS_PATH.open(encoding="utf-8"):
        c = json.loads(line)
        d = docs.setdefault(c["source_id"], {
            "source_id": c["source_id"], "title": c["title"], "url": c["url"], "category": c["agent"],
            "doc_type": c["doc_type"], "scheme": c.get("scheme"), "doc_date": c.get("doc_date"),
            "date_downloaded": c["date_downloaded"], "pages": pages.get(c["source_id"]), "chunks": 0})
        d["chunks"] += 1
    return {"count": len(docs), "documents": sorted(docs.values(), key=lambda d: (d["category"], d["title"]))}


def _reindex_job():
    REINDEX.update(running=True, started=time.strftime("%H:%M:%S"), finished=None, log="")
    log = []
    try:
        for cmd in (["scripts/parse.py"], ["scripts/chunk.py"], ["scripts/build_index.py"]):
            p = subprocess.run([sys.executable, *cmd], cwd=config.ROOT, capture_output=True, text=True)
            log.append(f"$ {' '.join(cmd)}\n{p.stdout[-1500:]}{p.stderr[-800:]}")
            if p.returncode != 0:
                break
        reload()
    finally:
        REINDEX.update(running=False, finished=time.strftime("%H:%M:%S"), log="\n".join(log))


@app.post("/admin/reindex")
def admin_reindex():
    if REINDEX["running"]:
        return {"status": "already running", "started": REINDEX["started"]}
    threading.Thread(target=_reindex_job, daemon=True).start()
    return {"status": "started", "check": "GET /health -> reindex"}
