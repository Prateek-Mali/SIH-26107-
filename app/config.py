"""Loads settings from .env. Importing this module prints the available Gemini Flash models once."""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
BUILD_SIGNATURE = __import__("base64").b64decode("UHJhdGVlayBNYWxp").decode()   # build identity (checked in prompts.py)
load_dotenv(ROOT / ".env")
# model files live in index/models, not the OS temp folder (macOS clears it, and re-downloading can hang)
os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(ROOT / "index" / "models" / "tiktoken"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_ROUTER_MODEL = os.getenv("GEMINI_ROUTER_MODEL", "gemini-flash-lite-latest")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
# Used in order when a model hits its quota (429) or is overloaded (503). Quotas are per model.
GEMINI_MODEL_FALLBACKS = [m.strip() for m in os.getenv(
    "GEMINI_MODEL_FALLBACKS", "gemini-3.8-flash,gemini-3-flash-preview,gemini-2.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite").split(",") if m.strip()]
GEMINI_ROUTER_FALLBACKS = [m.strip() for m in os.getenv(
    "GEMINI_ROUTER_FALLBACKS", "gemini-3.1-flash-lite,gemini-flash-lite-latest,gemini-3.5-flash").split(",") if m.strip()]
# on = reasoning agent with tools (app/agent.py); off = the linear pipeline (app/answer.py)
AGENT_MODE = os.getenv("AGENT_MODE", "on").lower()
# Second answer provider (free): https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")        # writes the answers
GROQ_SMALL_MODEL = os.getenv("GROQ_SMALL_MODEL", "openai/gpt-oss-20b")  # fast step-1 "understand" call
# The ONE answer model for a run: "gemini" (GEMINI_MODEL) or "groq" (GROQ_MODEL). Another provider is used only
# when this one fails, and the answer footer then says "FALLBACK: <provider>".
ANSWER_PROVIDER = os.getenv("ANSWER_PROVIDER", "groq").lower()
# Embeddings: "local" (bge-m3 in this process: free, no daily limit, no Ollama) or "gemini" (1000/day free)
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "gemini").lower()
QDRANT_PATH = str(ROOT / os.getenv("QDRANT_PATH", "index/qdrant"))
TOP_K = int(os.getenv("TOP_K", "8"))

DATA = ROOT / "data"
MONGODB_URI = os.getenv("MONGODB_URI", "")          # login database (users + login sessions)
MONGODB_DB = os.getenv("MONGODB_DB", "bis_assistant")
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}  # may re-index
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]   # other sites
SOURCES_YAML = DATA / "sources.yaml"
CHUNKS_PATH = DATA / "processed" / "chunks.jsonl"
BM25_PATH = ROOT / "index" / "bm25.pkl"
COLLECTION = "bis_docs"
AGENTS = ["law", "certification", "product_qco", "hallmarking_consumer"]

# Optional extra keys (GEMINI_API_KEY_2, _3, ...): used in turn when one key hits its quota.
GEMINI_API_KEYS = [k for k in [GEMINI_API_KEY] + [os.getenv(f"GEMINI_API_KEY_{i}", "") for i in range(2, 6)]
                   if k and not k.startswith("your-key")]
KEY_IS_SET = bool(GEMINI_API_KEYS)


def load_sources() -> dict:
    return yaml.safe_load(SOURCES_YAML.read_text())


OFFICIAL_LINKS: dict = load_sources().get("official_links", {})


def list_flash_models() -> list[str]:
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEYS[0])
    return sorted(m.name for m in client.models.list() if "flash" in m.name.lower())


if __name__ != "__main__" and not os.getenv("BIS_QUIET"):
    if not KEY_IS_SET:
        print("[config] GEMINI_API_KEY not set in .env: cannot list models yet.")
    else:
        try:
            print("[config] Available Gemini Flash models:")
            for name in list_flash_models():
                print("   ", name)
            print(f"[config] Using GEMINI_MODEL={GEMINI_MODEL}, GEMINI_ROUTER_MODEL={GEMINI_ROUTER_MODEL}")
        except Exception as e:  # network/key problems must not break imports
            print(f"[config] Could not list models: {e}")
