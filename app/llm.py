"""Gemini client with model + key fallback, and Ollama as the last resort.

Quotas are per model, so when a model hits its limit (429) or is overloaded (503) we move to the
next model in its fallback chain (GEMINI_MODEL_FALLBACKS / GEMINI_ROUTER_FALLBACKS), trying every
API key for a model before dropping to a lower one. A model that hit its limit is skipped for 60 s.
Embeddings never switch model (vectors from different models are not comparable); they only rotate keys.

Public functions:
    generate(prompt, system=None, model=None, json_mode=False, temperature=0.1) -> str
    generate_stream(prompt, system=None, model=None) -> Iterator[str]
    generate_json(prompt, system=None, model=None) -> dict
    embed(texts, task="RETRIEVAL_DOCUMENT") -> list[list[float]]
    gemini_ocr(png_bytes) -> str
"""
import json
import random
import threading
import time
from typing import Callable, Iterator

import httpx
from google import genai
from google.genai import errors, types

from app import config

EMBED_DIM = 768
SKIP_MODEL = {429, 503}          # quota / overloaded: go to the next key or model now
RETRY_LATER = {500, 502, 504}    # transient server errors: next option, then back off
COOLDOWN_S = 60

_clients: list[genai.Client] = []
_cooldown: dict[tuple[int, str], float] = {}   # (key index, model) -> skip until
_lock = threading.Lock()                       # agents run in parallel threads


class AllModelsBusy(RuntimeError):
    pass


def clients() -> list[genai.Client]:
    with _lock:
        if not _clients:
            if not config.KEY_IS_SET:
                raise RuntimeError("GEMINI_API_KEY is not set in .env")
            _clients.extend(genai.Client(api_key=k) for k in config.GEMINI_API_KEYS)
    return _clients


def client() -> genai.Client:
    return clients()[0]


def model_chain(model: str) -> list[str]:
    """The requested model first, then its fallbacks (router models fall back to router fallbacks)."""
    if model in [config.GEMINI_ROUTER_MODEL, *config.GEMINI_ROUTER_FALLBACKS]:
        rest = config.GEMINI_ROUTER_FALLBACKS
    else:
        rest = config.GEMINI_MODEL_FALLBACKS
    return list(dict.fromkeys([model, *rest]))


def _is_network_error(e: Exception) -> bool:
    return isinstance(e, (httpx.HTTPError, ConnectionError, TimeoutError))


def _is_fallback_error(e: Exception) -> bool:
    """Quota, overload or network problems: Ollama may still answer."""
    if isinstance(e, errors.APIError):
        return e.code in SKIP_MODEL | RETRY_LATER
    return _is_network_error(e) or isinstance(e, AllModelsBusy)


def _call(fn: Callable[[genai.Client, str], object], models: list[str], rounds: int = 3):
    """Try fn(client, model) over models (outer) x keys (inner); back off between rounds."""
    last: Exception | None = None
    for r in range(rounds):
        for model in models:
            for k, c in enumerate(clients()):
                if _cooldown.get((k, model), 0) > time.time():
                    continue
                try:
                    return fn(c, model)
                except errors.APIError as e:
                    last = e
                    if e.code == 404:          # model not available for this key
                        _cooldown[(k, model)] = float("inf")
                    elif e.code in SKIP_MODEL:
                        _cooldown[(k, model)] = time.time() + COOLDOWN_S
                        print(f"[llm] {model} (key {k + 1}): {e.code}, trying the next key/model")
                    elif e.code not in RETRY_LATER:
                        raise
                except Exception as e:
                    if not _is_network_error(e):
                        raise
                    last = e
        if r < rounds - 1:
            # everything is cooling down or failing: wait for the earliest model to come back
            waits = [t - time.time() for t in _cooldown.values() if t != float("inf")]
            time.sleep(min(max(min(waits, default=5), 2), COOLDOWN_S) + random.random())
    raise AllModelsBusy(f"all Gemini models/keys unavailable: {last}")


def _gen_config(system, json_mode, temperature):
    return types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        response_mime_type="application/json" if json_mode else None,
    )


def generate(prompt: str, system: str | None = None, model: str | None = None,
             json_mode: bool = False, temperature: float = 0.1) -> str:
    try:
        resp = _call(lambda c, m: c.models.generate_content(
            model=m, contents=prompt, config=_gen_config(system, json_mode, temperature)),
            model_chain(model or config.GEMINI_MODEL))
        return resp.text or ""
    except Exception as e:
        if not _is_fallback_error(e) and config.KEY_IS_SET:
            raise
        print(f"[llm] Gemini unavailable ({e}); falling back to Ollama {config.OLLAMA_MODEL}")
        return ollama_generate(prompt, system, json_mode, temperature)


def generate_stream(prompt: str, system: str | None = None, model: str | None = None,
                    temperature: float = 0.1) -> Iterator[str]:
    try:
        # the first chunk is fetched inside _call so quota errors still trigger the fallback
        def start(c, m):
            it = iter(c.models.generate_content_stream(model=m, contents=prompt,
                                                       config=_gen_config(system, False, temperature)))
            return it, next(it, None)

        it, first = _call(start, model_chain(model or config.GEMINI_MODEL))
        if first is not None and first.text:
            yield first.text
        for chunk in it:
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


def embed(texts: list[str], task: str = "RETRIEVAL_DOCUMENT", rounds: int = 2) -> list[list[float]]:
    """Embed a batch. task: RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY. Same model always; keys rotate."""
    resp = _call(lambda c, m: c.models.embed_content(
        model=m, contents=texts,
        config=types.EmbedContentConfig(task_type=task, output_dimensionality=EMBED_DIM)),
        [config.GEMINI_EMBED_MODEL], rounds=rounds)
    return [e.values for e in resp.embeddings]


OCR_PROMPT = (
    "Extract all text from this scanned page of an official Government of India / BIS document. "
    "Keep the original language (Hindi in Devanagari, English as is). Keep section, rule and "
    "S.O. numbers exactly. Render tables as plain rows separated by ' | '. Output only the text."
)


def gemini_ocr(png: bytes) -> str:
    resp = _call(lambda c, m: c.models.generate_content(
        model=m, contents=[types.Part.from_bytes(data=png, mime_type="image/png"), OCR_PROMPT],
        config=types.GenerateContentConfig(temperature=0.0)), model_chain(config.GEMINI_MODEL), rounds=4)
    return resp.text or ""
