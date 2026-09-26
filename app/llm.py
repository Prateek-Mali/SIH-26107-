"""Gemini client with retry, plus Ollama fallback on quota/network errors.

Public functions:
    generate(prompt, system=None, model=None, json_mode=False, temperature=0.1) -> str
    generate_stream(prompt, system=None, model=None) -> Iterator[str]
    embed(texts, task="RETRIEVAL_DOCUMENT") -> list[list[float]]
    gemini_ocr(png_bytes) -> str
"""
import json
import random
import time
from typing import Iterator

import httpx
from google import genai
from google.genai import errors, types

from app import config

EMBED_DIM = 768
RETRY_CODES = {429, 500, 502, 503, 504}

_client: genai.Client | None = None


def client() -> genai.Client:
    global _client
    if _client is None:
        if not config.KEY_IS_SET:
            raise RuntimeError("GEMINI_API_KEY is not set in .env")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _is_fallback_error(e: Exception) -> bool:
    """Quota or network problems: worth retrying, then falling back to Ollama."""
    if isinstance(e, errors.APIError):
        return e.code in RETRY_CODES
    return isinstance(e, (httpx.HTTPError, ConnectionError, TimeoutError))


def _with_retry(fn, attempts: int = 4):
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            if not _is_fallback_error(e) or i == attempts - 1:
                raise
            time.sleep(min(2 ** i * 2, 30) + random.random())


def _gen_config(system, json_mode, temperature):
    return types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        response_mime_type="application/json" if json_mode else None,
    )


def generate(prompt: str, system: str | None = None, model: str | None = None,
             json_mode: bool = False, temperature: float = 0.1) -> str:
    model = model or config.GEMINI_MODEL
    try:
        resp = _with_retry(lambda: client().models.generate_content(
            model=model, contents=prompt, config=_gen_config(system, json_mode, temperature)))
        return resp.text or ""
    except Exception as e:
        if not _is_fallback_error(e) and config.KEY_IS_SET:
            raise
        print(f"[llm] Gemini unavailable ({e}); falling back to Ollama {config.OLLAMA_MODEL}")
        return ollama_generate(prompt, system, json_mode, temperature)


def generate_stream(prompt: str, system: str | None = None, model: str | None = None,
                    temperature: float = 0.1) -> Iterator[str]:
    model = model or config.GEMINI_MODEL
    try:
        stream = _with_retry(lambda: client().models.generate_content_stream(
            model=model, contents=prompt, config=_gen_config(system, False, temperature)))
        for chunk in stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        if not _is_fallback_error(e) and config.KEY_IS_SET:
            raise
        print(f"[llm] Gemini unavailable ({e}); falling back to Ollama {config.OLLAMA_MODEL}")
        yield ollama_generate(prompt, system, False, temperature)


def generate_json(prompt: str, system: str | None = None, model: str | None = None) -> dict:
    text = generate(prompt, system, model, json_mode=True, temperature=0.0)
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def ollama_generate(prompt: str, system: str | None, json_mode: bool, temperature: float) -> str:
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"model": config.OLLAMA_MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature}}
    if json_mode:
        body["format"] = "json"
    r = httpx.post(f"{config.OLLAMA_URL}/api/chat", json=body, timeout=300)
    r.raise_for_status()
    return r.json()["message"]["content"]


def embed(texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Embed a batch (max 100 texts per call). task: RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY."""
    resp = _with_retry(lambda: client().models.embed_content(
        model=config.GEMINI_EMBED_MODEL, contents=texts,
        config=types.EmbedContentConfig(task_type=task, output_dimensionality=EMBED_DIM)), attempts=8)
    return [e.values for e in resp.embeddings]


OCR_PROMPT = (
    "Extract all text from this scanned page of an official Government of India / BIS document. "
    "Keep the original language (Hindi in Devanagari, English as is). Keep section, rule and "
    "S.O. numbers exactly. Render tables as plain rows separated by ' | '. Output only the text."
)


def gemini_ocr(png: bytes) -> str:
    resp = _with_retry(lambda: client().models.generate_content(
        model=config.GEMINI_MODEL,
        contents=[types.Part.from_bytes(data=png, mime_type="image/png"), OCR_PROMPT],
        config=types.GenerateContentConfig(temperature=0.0)), attempts=6)
    return resp.text or ""
