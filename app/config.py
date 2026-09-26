"""Loads settings from .env. Importing this module prints the available Gemini Flash models once."""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_ROUTER_MODEL = os.getenv("GEMINI_ROUTER_MODEL", "gemini-flash-lite-latest")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
QDRANT_PATH = str(ROOT / os.getenv("QDRANT_PATH", "index/qdrant"))
TOP_K = int(os.getenv("TOP_K", "8"))

DATA = ROOT / "data"
SOURCES_YAML = DATA / "sources.yaml"
CHUNKS_PATH = DATA / "processed" / "chunks.jsonl"
BM25_PATH = ROOT / "index" / "bm25.pkl"
COLLECTION = "bis_docs"
AGENTS = ["law", "certification", "product_qco", "hallmarking_consumer"]

KEY_IS_SET = bool(GEMINI_API_KEY) and not GEMINI_API_KEY.startswith("your-key")


def load_sources() -> dict:
    return yaml.safe_load(SOURCES_YAML.read_text())


OFFICIAL_LINKS: dict = load_sources().get("official_links", {})


def list_flash_models() -> list[str]:
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)
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
