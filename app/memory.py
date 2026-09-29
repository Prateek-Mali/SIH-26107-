"""Local conversation memory (SQLite, data/memory.sqlite): no cloud, no API key.

    chat(message, session_id=None) -> the ask() result + session_id; stores both turns, updates the profile.

Short-term: the last 6 turns (answers trimmed to 600 chars) go to the understand step, which rewrites a follow-up
into a standalone question before searching. Long-term: a per-session profile (role, product, IS number, scheme,
place, maker location, language) taken from the user's own words only, and a rolling summary after 12 turns.
Memory only helps understanding: facts still come from retrieved documents with [n] citations.
"""
import json
import re
import sqlite3
import time
import uuid

from app import config

DB = config.DATA / "memory.sqlite"
KEEP_TURNS, SUMMARY_AFTER, TRIM, MAX_AGE_DAYS = 6, 12, 600, 30
PROFILE_KEYS = ("role", "product", "is_number", "scheme", "location", "maker_location", "language")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, created_at REAL, updated_at REAL, title TEXT);
CREATE TABLE IF NOT EXISTS turns (session_id TEXT, turn_no INTEGER, role TEXT, text TEXT, citations_json TEXT,
                                  intent TEXT, created_at REAL, PRIMARY KEY (session_id, turn_no));
CREATE TABLE IF NOT EXISTS profile (session_id TEXT, key TEXT, value TEXT, updated_at REAL, PRIMARY KEY (session_id, key));
CREATE TABLE IF NOT EXISTS summary (session_id TEXT PRIMARY KEY, text TEXT, upto_turn INTEGER);
"""


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    if "owner" not in [r[1] for r in con.execute("PRAGMA table_info(sessions)")]:  # the logged-in user (web); '' = CLI
        con.execute("ALTER TABLE sessions ADD COLUMN owner TEXT DEFAULT ''")
    return con


# ---------------------------------------------------------------- privacy
PERSONAL = [(re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[email]"),
            (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[id number]"),          # Aadhaar
            (re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)"), "[phone]")]


def redact(text: str) -> str:
    for pat, rep in PERSONAL:
        text = pat.sub(rep, text)
    return text


# ---------------------------------------------------------------- sessions and turns
def new_session(owner: str = "") -> str:
    sid = uuid.uuid4().hex[:12]
    with db() as con:
        con.execute("INSERT INTO sessions (session_id, created_at, updated_at, title, owner) VALUES (?,?,?,?,?)",
                    (sid, time.time(), time.time(), "", owner))
    return sid


def owns(sid: str, owner: str) -> bool:
    with db() as con:
        row = con.execute("SELECT owner FROM sessions WHERE session_id=?", (sid,)).fetchone()
    return bool(row) and (row[0] or "") == owner


def ensure(session_id: str | None, owner: str = "") -> str:
    """The session to use: the given one if it exists and belongs to this owner, else a new one."""
    purge_old()
    if session_id:
        with db() as con:
            row = con.execute("SELECT owner FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if row:
            return session_id if (row[0] or "") == owner else new_session(owner)
        with db() as con:
            con.execute("INSERT INTO sessions (session_id, created_at, updated_at, title, owner) VALUES (?,?,?,?,?)",
                        (session_id, time.time(), time.time(), "", owner))
        return session_id
    return new_session(owner)


def add_turn(sid: str, role: str, text: str, citations=None, intent=None):
    with db() as con:
        n = con.execute("SELECT COALESCE(MAX(turn_no), 0) FROM turns WHERE session_id=?", (sid,)).fetchone()[0] + 1
        con.execute("INSERT INTO turns VALUES (?,?,?,?,?,?,?)",
                    (sid, n, role, redact(text), json.dumps(citations or [], ensure_ascii=False), intent, time.time()))
        con.execute("UPDATE sessions SET updated_at=?, title=CASE WHEN title='' AND ?='user' THEN ? ELSE title END "
                    "WHERE session_id=?", (time.time(), role, redact(text)[:60], sid))


def turns(sid: str, last: int | None = None) -> list[dict]:
    with db() as con:
        rows = con.execute("SELECT turn_no, role, text, citations_json, intent FROM turns WHERE session_id=? "
                           "ORDER BY turn_no DESC" + (f" LIMIT {int(last)}" if last else ""), (sid,)).fetchall()
    return [{"turn_no": n, "role": r, "content": t, "citations": json.loads(c or "[]"), "intent": i}
            for n, r, t, c, i in reversed(rows)]


def sessions(limit: int = 20, owner: str | None = None) -> list[dict]:
    """owner None = all (CLI /sessions); else only that user's."""
    with db() as con:
        rows = con.execute("SELECT s.session_id, s.title, s.updated_at, COUNT(t.turn_no) FROM sessions s LEFT JOIN "
                           "turns t USING (session_id) WHERE ? IS NULL OR s.owner = ? GROUP BY s.session_id "
                           "ORDER BY s.updated_at DESC LIMIT ?", (owner, owner, limit)).fetchall()
    return [{"session_id": s, "title": t, "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(u)), "turns": n}
            for s, t, u, n in rows]


def forget(sid: str):
    with db() as con:
        for table in ("turns", "profile", "summary", "sessions"):
            con.execute(f"DELETE FROM {table} WHERE session_id=?", (sid,))


def purge_old(days: int = MAX_AGE_DAYS):
    cutoff = time.time() - days * 86400
    with db() as con:
        old = [r[0] for r in con.execute("SELECT session_id FROM sessions WHERE updated_at < ?", (cutoff,))]
    for sid in old:
        forget(sid)


# ---------------------------------------------------------------- profile (from the user's words only)
STATES = ("andhra pradesh|arunachal pradesh|assam|bihar|chhattisgarh|goa|gujarat|haryana|himachal pradesh|jharkhand|"
          "karnataka|kerala|madhya pradesh|maharashtra|manipur|meghalaya|mizoram|nagaland|odisha|punjab|rajasthan|"
          "sikkim|tamil nadu|telangana|tripura|uttar pradesh|uttarakhand|west bengal|delhi")


def profile(sid: str) -> dict:
    with db() as con:
        return dict(con.execute("SELECT key, value FROM profile WHERE session_id=?", (sid,)).fetchall())


def set_profile(sid: str, updates: dict):
    with db() as con:
        for k, v in updates.items():
            if k in PROFILE_KEYS and v:
                con.execute("INSERT OR REPLACE INTO profile VALUES (?,?,?,?)", (sid, k, str(v)[:80], time.time()))


def profile_from(message: str, u: dict | None) -> dict:
    """Profile facts the user stated in THIS message (rules; the understand step's reading is used only when the
    words are in the message). Never invents: a missing fact is simply not updated."""
    m, ml, u = message, message.lower(), u or {}
    out = {}
    role = u.get("user_role")
    if role and role != "unknown" and re.search(r"\b(i|we|my|our)\b|मैं|हम", ml):
        out["role"] = role
    product = (u.get("product_attrs") or {}).get("product_type") or ""
    if product and all(w in ml for w in re.findall(r"[a-z]{3,}", product.lower())[:3]):
        out["product"] = product
    if is_no := re.search(r"\bIS\s*[:\-]?\s*(\d{2,5})(\s*\(\s*part\s*\d+\s*\))?", m, re.I):
        out["is_number"] = f"IS {is_no.group(1)}{is_no.group(2) or ''}".strip()
    if sch := re.search(r"\b(scheme[\s-]*(?:x|iv|ii|i|1|2|4|10)\b|crs|fmcs|hallmarking)", ml):
        out["scheme"] = sch.group(1).upper() if len(sch.group(1)) <= 5 else sch.group(1).title()
    if loc := re.search(rf"\b({STATES})\b", ml):
        out["location"] = loc.group(1).title()
    elif loc := re.search(r"\b(?:in|at|from)\s+([A-Z][a-z]{3,})\b(?!\s+(?:Standard|Act|Rules))", m):
        if loc.group(1) not in ("India", "Hindi", "English", "Scheme"):
            out["location"] = loc.group(1)
    if re.search(r"\b(in india|indian (maker|manufacturer|company))\b", ml) or out.get("location"):
        out["maker_location"] = "india"
    if re.search(r"\b(abroad|overseas|foreign|made in (?!india)\w+|from china)\b", ml):
        out["maker_location"] = "foreign"
    if re.search(r"\b(in|into) hindi\b|हिंदी में|हिन्दी में", ml) or re.search(r"[ऀ-ॿ]", m):
        out["language"] = "hi"
    elif re.search(r"\b(in|into) english\b", ml):
        out["language"] = "en"
    return out


# ---------------------------------------------------------------- history for the prompts
def history(sid: str) -> list[dict]:
    """summary of older turns (if any) + the last 6 turns, answers trimmed; each assistant turn keeps its citations."""
    with db() as con:
        row = con.execute("SELECT text FROM summary WHERE session_id=?", (sid,)).fetchone()
    out = [{"role": "summary", "content": row[0]}] if row and row[0] else []
    for t in turns(sid, KEEP_TURNS):
        body = re.split(r"\n\n\*\*(?:Sources|स्रोत):\*\*", t["content"])[0]
        out.append({"role": t["role"], "content": body[:TRIM], "full": body, "citations": t["citations"]})
    return out


def maybe_summarize(sid: str):
    """After 12 turns: older turns -> a short rolling summary (one small model call), kept with the last 6 turns."""
    all_turns = turns(sid)
    if len(all_turns) <= SUMMARY_AFTER:
        return
    with db() as con:
        row = con.execute("SELECT text, upto_turn FROM summary WHERE session_id=?", (sid,)).fetchone()
    old_text, upto = (row or ("", 0))
    older = [t for t in all_turns[:-KEEP_TURNS] if t["turn_no"] > upto]
    if not older:
        return
    from app import llm
    convo = "\n".join(f"{t['role']}: {t['content'][:400]}" for t in older)
    try:
        text, _ = llm.generate_with_provider(
            f"Earlier summary: {old_text or '(none)'}\n\nNew turns:\n{convo}\n\nWrite an updated summary in at most "
            "5 short lines: what the user asked about and what they told about themselves (role, product, place). "
            "No facts about BIS rules.", temperature=0.0, max_tokens=300,
            model=config.GEMINI_ROUTER_MODEL, groq_model=config.GROQ_SMALL_MODEL)
    except Exception as e:  # keep the old summary; the last 6 turns are still there
        print(f"[memory] summary skipped ({type(e).__name__})")
        return
    with db() as con:
        con.execute("INSERT OR REPLACE INTO summary VALUES (?,?,?)", (sid, text.strip()[:1500], older[-1]["turn_no"]))


# ---------------------------------------------------------------- one chat turn
RECALL = re.compile(r"\b(what (did|have) i (ask|asked|say|said)|what were we (talking|discussing)|"
                    r"my (first|previous|earlier|last) questions?|what did we (discuss|talk about)|"
                    r"what was my (first|last|previous) question)\b", re.I)


def recall_answer(sid: str, message: str = "") -> str:
    """'What did I ask about before?' is answered from memory (not a BIS fact, so no citation needed)."""
    asked = [t["content"] for t in turns(sid) if t["role"] == "user" and not RECALL.search(t["content"])]
    p = profile(sid)
    if not asked:
        return "We have not talked about anything yet in this conversation."
    if re.search(r"\bfirst\b", message, re.I):
        return f"Your first question was: \"{asked[0]}\""
    if re.search(r"\b(last|previous)\b", message, re.I):
        return f"Your last question was: \"{asked[-1]}\""
    lines = ["Here is what you asked earlier in this conversation:"] + [f"{i}. {q}" for i, q in enumerate(asked[-10:], 1)]
    if p:
        lines.append("\nWhat I remember about you: " + ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in p.items()) + ".")
    return "\n".join(lines)


def chat(message: str, session_id: str | None = None, use_cache: bool = True, owner: str = "") -> dict:
    from app.agent import ask

    sid = ensure(session_id, owner)
    if RECALL.search(message):
        res = {"answer": recall_answer(sid, message), "citations": [], "sources_used": 0, "provider": "memory",
               "fallback": None, "latency_ms": 0, "refused": False, "cached": False,
               "trace": {"stages": {"mode": "memory recall"}}}
    else:
        prof = profile(sid)
        res = ask(message, history(sid), use_cache=use_cache, profile=prof)
        u = (res.get("trace") or {}).get("understand") or {}
        set_profile(sid, profile_from(message, u))
    add_turn(sid, "user", message)
    add_turn(sid, "assistant", res["answer"], [c["chunk_id"] for c in res.get("citations", [])],
             ((res.get("trace") or {}).get("stages") or {}).get("intent"))
    maybe_summarize(sid)
    res["session_id"] = sid
    return res
