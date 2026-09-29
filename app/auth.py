"""Login: users and login sessions in MongoDB (MONGODB_URI).

    signup(email, password) / login(email, password) -> session token (sent as an HttpOnly cookie)
    user_for(token) -> {"email": ...} or None;  logout(token)

Only the email and a password hash are stored (no name, no phone). Passwords: scrypt with a random salt
(Python standard library). Login sessions expire after 30 days (MongoDB TTL index).
"""
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from app import config

COOKIE = "bis_session"
SESSION_DAYS = 30
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[A-Za-z]{2,}$")


class AuthError(ValueError):
    pass


@lru_cache(maxsize=1)
def _db():
    from pymongo import ASCENDING, MongoClient
    if not config.MONGODB_URI:
        raise AuthError("MONGODB_URI is not set in .env")
    db = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=10000)[config.MONGODB_DB]
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.login_sessions.create_index("expires_at", expireAfterSeconds=0)  # MongoDB deletes expired sessions
    return db


def _hash(password: str, salt: bytes) -> str:
    return hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32).hex()


def _clean(email: str, password: str) -> tuple[str, str]:
    email = (email or "").strip().lower()
    if not EMAIL.match(email):
        raise AuthError("Enter a valid email address.")
    if not 8 <= len(password or "") <= 128:
        raise AuthError("The password must be 8 to 128 characters.")
    return email, password


def _new_session(email: str) -> str:
    token = secrets.token_urlsafe(32)
    _db().login_sessions.insert_one({"token_hash": hashlib.sha256(token.encode()).hexdigest(), "email": email,
                                     "expires_at": datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)})
    return token


def signup(email: str, password: str) -> str:
    from pymongo.errors import DuplicateKeyError
    email, password = _clean(email, password)
    salt = secrets.token_bytes(16)
    try:
        _db().users.insert_one({"email": email, "salt": salt.hex(), "password_hash": _hash(password, salt),
                                "created_at": datetime.now(timezone.utc)})
    except DuplicateKeyError:
        raise AuthError("An account with this email already exists. Sign in instead.")
    return _new_session(email)


def login(email: str, password: str) -> str:
    email = (email or "").strip().lower()
    user = _db().users.find_one({"email": email})
    ok = bool(user) and hmac.compare_digest(_hash(password or "", bytes.fromhex(user["salt"])), user["password_hash"])
    if not ok:  # same message either way: do not reveal which emails have accounts
        raise AuthError("Wrong email or password.")
    return _new_session(email)


def user_for(token: str | None) -> dict | None:
    if not token:
        return None
    s = _db().login_sessions.find_one({"token_hash": hashlib.sha256(token.encode()).hexdigest()})
    if not s or s["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None
    return {"email": s["email"]}


def logout(token: str | None):
    if token:
        _db().login_sessions.delete_one({"token_hash": hashlib.sha256(token.encode()).hexdigest()})
