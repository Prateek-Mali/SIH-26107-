"""FastAPI server:  uvicorn app.api:app --port 8000

POST /chat           {message, session_id} -> {answer, citations, sources_used, latency_ms, provider, fallback, trace}
                     (trace.stages: every step, see app/answer.py)
POST /chat/stream    same, as Server-Sent Events: status, token..., citations, trace, done
POST /search         {query} -> the raw retrieval result (for checking accuracy)
GET  /health         providers, embeddings, index counts
GET  /sources        every indexed document with date and page count
POST /admin/reindex  re-parse, re-chunk, re-index (including data/manual/) in the background
"""
import base64
import binascii
import json
import logging
import re
import subprocess
import sys
import threading
import time

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
from sse_starlette.sse import EventSourceResponse
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from app import auth, config
from app.agent import ask  # AGENT_MODE=off (or any agent failure) -> the old pipeline
from app.retrieval import reload, retrieve

app = FastAPI(title="BIS Assistant API", version="0.2")


@app.middleware("http")
async def build_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Created-By"] = config.BUILD_SIGNATURE
    return response
# the web UI is served from this same server, so no other site needs access; list extra origins in ALLOWED_ORIGINS
if config.ALLOWED_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS, allow_credentials=True,
                       allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type"])
log = logging.getLogger("bis.api")
FRIENDLY_ERROR = "Something went wrong while answering. Please try again in a moment."

REINDEX = {"running": False, "started": None, "finished": None, "log": ""}


class ChatRequest(BaseModel):
    message: str = Field("", max_length=2000)            # may be empty when a photo is sent
    session_id: str | None = Field(None, max_length=100, pattern=r"^[A-Za-z0-9_-]*$")  # none -> a new session
    image_base64: str | None = Field(None, max_length=14_000_000)   # optional product photo (<= 10 MB)
    image_name: str | None = Field(None, max_length=200)            # e.g. "label.jpg" (gives the file type)

    def image(self) -> tuple[bytes, str] | None:
        if not self.image_base64:
            if not self.message.strip():
                raise HTTPException(422, "Send a message or a photo.")
            return None
        try:
            data = base64.b64decode(self.image_base64.split(",")[-1], validate=True)  # plain or data: URL
        except (ValueError, binascii.Error):
            raise HTTPException(400, "The photo is not valid base64.")
        return data, self.image_name or "photo.jpg"


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class RecommendRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=2000)


class SchemeRequest(BaseModel):
    profile: dict = Field(default_factory=dict)  # maker_location, role, product, is_electronics_it, is_precious_metal


# ---------------------------------------------------------------- login (app/auth.py, MongoDB)
class AuthRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., max_length=128)


def current_user(request: Request) -> dict:
    """Every chat / conversation / tool endpoint needs a logged-in user (the session cookie)."""
    try:
        user = auth.user_for(request.cookies.get(auth.COOKIE))
    except Exception as e:  # the login database is down: say so, never let the request through
        raise HTTPException(503, f"login service unavailable ({type(e).__name__})")
    if not user:
        raise HTTPException(401, "Please sign in.")
    return user


FAILED: dict[str, list[float]] = {}   # client address -> times of failed login/signup attempts
MAX_FAILS, FAIL_WINDOW_S = 10, 15 * 60


def _check_attempts(request: Request):
    # ponytail: in-memory, per server process; use MongoDB or Redis when running several servers
    ip = request.client.host if request.client else "?"
    recent = [t for t in FAILED.get(ip, []) if time.time() - t < FAIL_WINDOW_S]
    FAILED[ip] = recent
    if len(recent) >= MAX_FAILS:
        raise HTTPException(429, "Too many attempts. Please wait 15 minutes and try again.")
    return ip


def _set_cookie(response: Response, request: Request, token: str):
    response.set_cookie(auth.COOKIE, token, max_age=auth.SESSION_DAYS * 86400, httponly=True, samesite="lax",
                        secure=request.url.scheme == "https", path="/")


@app.post("/auth/signup")
def signup(req: AuthRequest, request: Request, response: Response):
    ip = _check_attempts(request)
    try:
        _set_cookie(response, request, auth.signup(req.email, req.password))
    except auth.AuthError as e:
        FAILED.setdefault(ip, []).append(time.time())
        raise HTTPException(400, str(e))
    return {"email": req.email.strip().lower()}


@app.post("/auth/login")
def login(req: AuthRequest, request: Request, response: Response):
    ip = _check_attempts(request)
    try:
        _set_cookie(response, request, auth.login(req.email, req.password))
    except auth.AuthError as e:
        FAILED.setdefault(ip, []).append(time.time())
        raise HTTPException(401, str(e))
    return {"email": req.email.strip().lower()}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    auth.logout(request.cookies.get(auth.COOKIE))
    response.delete_cookie(auth.COOKIE, path="/")
    return {"ok": True}


@app.get("/auth/me")
def me(user: dict = Depends(current_user)):
    return user


# ---------------------------------------------------------------- conversations (local SQLite memory, per user)
def _chat(req: ChatRequest, user: dict, image: tuple[bytes, str] | None = None) -> dict:
    from app import memory
    if image:  # Phase 2: product photo -> what is on it -> the normal cited answer (app/vision.py)
        from app.vision import photo_chat
        try:
            return photo_chat(image[0], image[1], req.message, req.session_id or None, owner=user["email"])
        except ValueError as e:  # wrong file type / too large: tell the user exactly that
            raise HTTPException(400, str(e))
    return memory.chat(req.message, req.session_id or None, owner=user["email"])


async def _chat_request(request: Request) -> tuple[ChatRequest, tuple[bytes, str] | None]:
    """POST /chat takes JSON (image as base64) or a multipart form (message, session_id, image file)."""
    if request.headers.get("content-type", "").startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("image")
        req = ChatRequest(message=str(form.get("message") or ""), session_id=form.get("session_id") or None)
        if upload is not None and hasattr(upload, "read"):
            data = await upload.read(vision_max_bytes() + 1)
            return req, (data, upload.filename or "photo.jpg")
        return req, req.image()
    try:
        req = ChatRequest(**await request.json())
    except ValidationError as e:
        raise HTTPException(422, e.errors(include_url=False, include_context=False))
    except ValueError:
        raise HTTPException(400, "Send JSON or a multipart form.")
    return req, req.image()


def vision_max_bytes() -> int:
    from app.vision import MAX_BYTES
    return MAX_BYTES


def _own(session_id: str, user: dict):
    from app import memory
    if not memory.owns(session_id, user["email"]):
        raise HTTPException(404, "No such conversation.")


@app.get("/sessions")
def list_sessions(user: dict = Depends(current_user)):
    from app import memory
    return memory.sessions(50, owner=user["email"])


@app.get("/session/{session_id}")
def get_session(session_id: str, user: dict = Depends(current_user)):
    from app import memory
    _own(session_id, user)
    return {"session_id": session_id, "profile": memory.profile(session_id), "turns": memory.turns(session_id)}


@app.delete("/session/{session_id}")
def delete_session(session_id: str, user: dict = Depends(current_user)):
    from app import memory
    _own(session_id, user)
    memory.forget(session_id)
    return {"deleted": session_id}


app.mount("/app", StaticFiles(directory=config.ROOT / "ui" / "web", html=True), name="web")  # the web chat UI


@app.get("/")
def root():
    return RedirectResponse("/app/")


@app.get("/api")
def api_index():
    return {"name": "BIS Assistant API", "docs": "/docs", "ui": "/app/",
            "endpoints": ["GET /sessions", "GET /session/{id}", "DELETE /session/{id}", "POST /chat", "POST /chat/stream", "POST /search", "POST /recommend", "POST /scheme", "GET /health", "GET /sources",
                          "POST /admin/reindex"]}


@app.post("/chat")
async def chat(request: Request, user: dict = Depends(current_user)):
    req, image = await _chat_request(request)
    try:
        return await run_in_threadpool(_chat, req, user, image)
    except HTTPException:
        raise
    except Exception as e:  # show the real error, never a fake refusal
        log.exception("chat failed")  # the details go to the server log, not to the user
        return {"error": FRIENDLY_ERROR}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, user: dict = Depends(current_user)):
    image = req.image()

    def events():
        yield {"event": "status", "data": json.dumps({"message": "Reading your photo" if image else
                                                      "Searching official BIS documents"})}
        try:
            result = _chat(req, user, image)
        except HTTPException as e:
            yield {"event": "error", "data": json.dumps({"message": e.detail})}
            return
        except Exception as e:
            log.exception("chat failed")
            yield {"event": "error", "data": json.dumps({"message": FRIENDLY_ERROR})}
            return
        for m in re.finditer(r"\S+\s*", result["answer"]):
            yield {"event": "token", "data": json.dumps({"text": m.group(0)}, ensure_ascii=False)}
        yield {"event": "citations", "data": json.dumps(result["citations"], ensure_ascii=False)}
        yield {"event": "trace", "data": json.dumps(result["trace"], ensure_ascii=False)}
        if result.get("vision"):
            yield {"event": "vision", "data": json.dumps({"vision": result["vision"],
                                                          "format_checks": result["format_checks"]}, ensure_ascii=False)}
        yield {"event": "done", "data": json.dumps({k: result.get(k) for k in ("session_id", "provider", "fallback", "latency_ms",
                                                                                "sources_used", "refused", "cached")})}
    return EventSourceResponse(iterate_in_threadpool(events()))


@app.post("/recommend")
def recommend(req: RecommendRequest, user: dict = Depends(current_user)):
    """Standard Recommender: candidate Indian Standards for a product description (JSON for the web UI)."""
    from app.recommender import recommend_standards
    return recommend_standards(req.description)


@app.post("/scheme")
def scheme(req: SchemeRequest, user: dict = Depends(current_user)):
    """Scheme Selector: which BIS scheme applies, why, next steps and sources, for a profile."""
    from app.recommender import recommend_standards, select_scheme
    p = req.profile
    product = str(p.get("product") or "")
    rec = recommend_standards(product, attrs={"precious_metal": p.get("is_precious_metal", False)}) if product else {"candidates": []}
    return {"candidates": rec["candidates"], **select_scheme(p, rec["candidates"], product)}


@app.post("/search")
def search(req: SearchRequest, user: dict = Depends(current_user)):
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
            "llm": {"answer_model": __import__("app.llm", fromlist=["x"]).primary_label(),
                    "gemini_model": config.GEMINI_MODEL,
                    "gemini_keys": len(config.GEMINI_API_KEYS), "groq": bool(config.GROQ_API_KEY),
                    "groq_model": config.GROQ_MODEL},
            "embeddings": config.EMBED_PROVIDER + ":" + __import__("app.llm", fromlist=["x"]).embed_model_id(),
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
        for cmd in (["scripts/parse.py"], ["scripts/chunk.py"], ["scripts/build_index.py"], ["scripts/build_term_graph.py"]):
            p = subprocess.run([sys.executable, *cmd], cwd=config.ROOT, capture_output=True, text=True)
            log.append(f"$ {' '.join(cmd)}\n{p.stdout[-1500:]}{p.stderr[-800:]}")
            if p.returncode != 0:
                break
        reload()
    finally:
        REINDEX.update(running=False, finished=time.strftime("%H:%M:%S"), log="\n".join(log))


@app.post("/admin/reindex")
def admin_reindex(user: dict = Depends(current_user)):
    if user["email"] not in config.ADMIN_EMAILS:
        raise HTTPException(403, "Only an admin can re-index.")
    if REINDEX["running"]:
        return {"status": "already running", "started": REINDEX["started"]}
    threading.Thread(target=_reindex_job, daemon=True).start()
    return {"status": "started", "check": "GET /health -> reindex"}
