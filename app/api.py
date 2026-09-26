"""FastAPI server.

    uvicorn app.api:app --port 8000

POST /chat {message, session_id} -> Server-Sent Events:
    status    {"step", "message"}          as each graph step finishes
    token     {"text"}                     the answer, in small pieces
    citations [{n, title, section, page, url, ...}]
    trace     [{step, ...}]                "How I answered"
    done      {"refused", "language", "intents", "latency_ms"}
GET /health, GET /sources
"""
import json
import re
import time
from collections import defaultdict, deque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from starlette.concurrency import iterate_in_threadpool

from app import config
from app.graph import stream

app = FastAPI(title="BIS Assistant API", version="0.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Short in-memory history per session, only so follow-up questions work. Never written to disk.
HISTORY: dict[str, deque] = defaultdict(lambda: deque(maxlen=6))

STATUS = {
    "router": "Understanding the question",
    "law": "Searched BIS Act, Rules and Regulations",
    "certification": "Searched certification procedures and fees",
    "product_qco": "Searched product lists and Quality Control Orders",
    "hallmarking_consumer": "Searched hallmarking and consumer documents",
    "composer": "Writing the answer",
    "guard": "Checking every sentence against the sources",
    "direct": "Replying",
}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field("default", max_length=100)


def sse(event: str, data) -> dict:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


def pieces(text: str):
    """Split the checked answer into small word groups for streaming."""
    for m in re.finditer(r"\S+\s*", text):
        yield m.group(0)


def chat_events(message: str, session_id: str):
    t0 = time.time()
    state: dict = {"trace": []}
    try:
        for node, update in stream(message, list(HISTORY[session_id])):
            trace = update.pop("trace", [])
            state.update(update)
            state["trace"] += trace
            yield sse("status", {"step": node, "message": STATUS.get(node, node)})
    except Exception as e:
        yield sse("error", {"message": f"Sorry, something went wrong: {type(e).__name__}"})
        print(f"[api] error: {e!r}")
        return
    answer = state.get("final_answer", "")
    for p in pieces(answer):
        yield sse("token", {"text": p})
    yield sse("citations", state.get("citations", []))
    yield sse("trace", state["trace"])
    yield sse("done", {"refused": state.get("refused", False), "language": state.get("language", "en"),
                       "intents": state.get("intents", []), "latency_ms": int((time.time() - t0) * 1000)})
    short = answer.split("\n\n**Sources:**")[0].split("\n\n**स्रोत:**")[0]
    HISTORY[session_id].extend([{"role": "user", "content": message}, {"role": "assistant", "content": short}])


@app.post("/chat")
async def chat(req: ChatRequest):
    return EventSourceResponse(iterate_in_threadpool(chat_events(req.message, req.session_id)))


@app.get("/")
def root():
    return {"name": "BIS Assistant API", "chat": "POST /chat {message, session_id} (Server-Sent Events)",
            "docs": "/docs", "health": "/health", "sources": "/sources",
            "ui": "run: streamlit run ui/streamlit_app.py  (then open http://localhost:8501)"}


@app.get("/health")
def health():
    return {"status": "ok", "gemini_key_set": config.KEY_IS_SET, "model": config.GEMINI_MODEL,
            "router_model": config.GEMINI_ROUTER_MODEL, "embed_model": config.GEMINI_EMBED_MODEL,
            "bm25_index": config.BM25_PATH.exists(), "vector_index": (config.ROOT / config.QDRANT_PATH).exists()}


@app.get("/sources")
def sources():
    docs: dict[str, dict] = {}
    if config.CHUNKS_PATH.exists():
        for line in config.CHUNKS_PATH.open(encoding="utf-8"):
            c = json.loads(line)
            d = docs.setdefault(c["source_id"], {
                "source_id": c["source_id"], "title": c["title"], "url": c["url"], "agent": c["agent"],
                "doc_type": c["doc_type"], "date_downloaded": c["date_downloaded"], "chunks": 0})
            d["chunks"] += 1
    return {"count": len(docs), "documents": sorted(docs.values(), key=lambda d: (d["agent"], d["title"]))}
