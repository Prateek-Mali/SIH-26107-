"""Gemini client with model + key fallback, and Groq as the second answer provider.

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
from functools import lru_cache
import random
import threading
import time
from typing import Callable, Iterator

import httpx
from google import genai
from google.genai import errors, types

from app import config

EMBED_DIM = 768
SEED = 7  # fixed sampling seed on every call: with temperature 0, the same prompt should give the same reply
SKIP_MODEL = {429, 503}          # quota / overloaded: go to the next key or model now
RETRY_LATER = {500, 502, 504}    # transient server errors: next option, then back off
COOLDOWN_S = 60
MAX_WAIT_S = 10  # never keep a user waiting long for a busy model; the next round tries every model again

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
            # without a timeout a stalled request blocks forever; 30 s then the next model/provider takes over
            _clients.extend(genai.Client(api_key=k, http_options=types.HttpOptions(timeout=30_000))
                            for k in config.GEMINI_API_KEYS)
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
    return isinstance(e, (httpx.HTTPError, ConnectionError, TimeoutError)) or "timed out" in str(e).lower()


def _is_fallback_error(e: Exception) -> bool:
    """Quota, overload or network problems: the next provider may still answer."""
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
                        # a used-up daily quota will not come back in a minute: bench that model for an hour
                        daily = "PerDay" in str(e) or "per day" in str(e).lower()
                        _cooldown[(k, model)] = time.time() + (3600 if daily else COOLDOWN_S)
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
            time.sleep(min(max(min(waits, default=5), 2), MAX_WAIT_S) + random.random())
    raise AllModelsBusy(f"all Gemini models/keys unavailable: {last}")


def _gen_config(system, json_mode, temperature, max_tokens: int | None = None):
    return types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        max_output_tokens=max_tokens,
        response_mime_type="application/json" if json_mode else None,
        seed=SEED,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # no AFC warning
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
        raise


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
        raise


def generate_json(prompt: str, system: str | None = None, model: str | None = None) -> dict:
    text = generate(prompt, system, model, json_mode=True, temperature=0.0)
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def embed_model_id() -> str:
    """Identifies the embedding space; vectors from different models must never be mixed.
    "local" is bge-m3 run in-process; it gives the same vectors as the old Ollama bge-m3 (cosine 1.0), so it keeps
    that id and every cached vector stays valid."""
    if config.EMBED_PROVIDER in ("local", "ollama"):
        return "ollama:bge-m3"
    return f"{config.GEMINI_EMBED_MODEL}:{EMBED_DIM}"


@lru_cache(maxsize=1)
def _local_embedder():
    """bge-m3 (BAAI's ONNX export) in this process: no Ollama app, no API quota. ~2.2 GB in index/models."""
    from fastembed import TextEmbedding
    from fastembed.common.model_description import ModelSource, PoolingType
    try:
        TextEmbedding.add_custom_model(model="BAAI/bge-m3", pooling=PoolingType.CLS, normalization=True,
                                       sources=ModelSource(hf="BAAI/bge-m3"), dim=1024, model_file="onnx/model.onnx",
                                       additional_files=["onnx/model.onnx_data"])
    except ValueError:  # already registered
        pass
    return TextEmbedding("BAAI/bge-m3", cache_dir=str(config.ROOT / "index" / "models"))


def embed(texts: list[str], task: str = "RETRIEVAL_DOCUMENT", rounds: int = 2) -> list[list[float]]:
    """Embed a batch. task: RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY. Same model always; keys rotate."""
    if config.EMBED_PROVIDER in ("local", "ollama"):  # in-process bge-m3: no quota, no cost, no Ollama
        with _lock:
            return [v.tolist() for v in _local_embedder().embed(texts, batch_size=8)]
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
        config=_gen_config(None, False, 0.0)), model_chain(config.GEMINI_MODEL), rounds=4)
    return resp.text or ""



# ---------------------------------------------------------------- answer generation with providers
class ProviderError(RuntimeError):
    pass


def groq_generate(prompt: str, system: str | None, temperature: float, max_tokens: int,
                  model: str | None = None, json_mode: bool = False) -> str:
    model = model or config.GROQ_MODEL
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    body = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "seed": SEED}
    if "gpt-oss" in model:
        body["reasoning_effort"] = "low"  # fewer hidden reasoning tokens: faster, cheaper
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                   headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"}, json=body, timeout=CALL_TIMEOUT_S)
    r.raise_for_status()
    return clean_text(r.json()["choices"][0]["message"]["content"] or "")


def clean_text(text: str) -> str:
    """Models sometimes use narrow/no-break spaces ('IS\u202f16102'): make them normal spaces."""
    return text.replace("\u202f", " ").replace("\u00a0", " ").replace("\u2009", " ")


CALL_TIMEOUT_S = 30  # per LLM call, every provider


def _gemini_once(prompt: str, system: str | None, temperature: float, max_tokens: int,
                 model: str | None, schema: dict | None = None) -> tuple[str, str]:
    """Exactly ONE Gemini call: the first (model, key) not cooling down. A 429/503 benches that
    model+key (an hour for a used-up daily quota) and raises, so the caller moves to the next provider."""
    for m in model_chain(model or config.GEMINI_MODEL):
        for k, c in enumerate(clients()):
            if _cooldown.get((k, m), 0) > time.time():
                continue
            try:
                cfg = _gen_config(system, bool(schema), temperature, max_tokens)
                if schema:
                    cfg.response_json_schema = schema  # the reply must match the schema
                resp = c.models.generate_content(model=m, contents=prompt, config=cfg)
                return resp.text or "", m
            except errors.APIError as e:
                if e.code == 404:
                    _cooldown[(k, m)] = float("inf")
                elif e.code in SKIP_MODEL:
                    daily = "PerDay" in str(e) or "per day" in str(e).lower()
                    _cooldown[(k, m)] = time.time() + (3600 if daily else COOLDOWN_S)
                raise
    raise AllModelsBusy("every Gemini model/key is cooling down after a 429")


def primary_label(small: bool = False) -> str:
    """The ONE model used for answers in this run (ANSWER_PROVIDER); anything else is a visible fallback."""
    if (config.ANSWER_PROVIDER == "gemini" or not config.GROQ_API_KEY) and config.KEY_IS_SET:
        return f"gemini:{config.GEMINI_ROUTER_MODEL if small else config.GEMINI_MODEL}"
    if config.GROQ_API_KEY:
        return f"groq:{config.GROQ_SMALL_MODEL if small else config.GROQ_MODEL}"
    raise ProviderError("no LLM key set: add GEMINI_API_KEY or GROQ_API_KEY to .env")


def fallback_of(provider: str, small: bool = False) -> str | None:
    """The provider label if it is not this run's pinned model (shown as 'FALLBACK: <provider>'), else None."""
    return None if provider in (primary_label(small), "none", "") else provider


def _provider_order() -> list[str]:
    first = primary_label().split(":")[0]
    return [first] + [p for p in ("groq", "gemini") if p != first]


def generate_with_provider(prompt: str, system: str | None = None, temperature: float = 0.1,
                           max_tokens: int = 4096, model: str | None = None,
                           groq_model: str | None = None, schema: dict | None = None) -> tuple[str, str]:
    """The pinned provider (ANSWER_PROVIDER) first, then the other one. One attempt per
    provider, 30 s timeout, no retries: a 429 / timeout / network error moves straight to the next provider.
    schema: ask for JSON (Gemini response schema / Groq json_object). Returns (text, provider label).
    Other errors (bad request, bad key) are raised, never hidden."""
    errors_seen = []
    groq_wait = None  # seconds until Groq's per-minute token budget resets (from its 429 reply)
    for name in _provider_order():
        if name == "groq":
            if not config.GROQ_API_KEY:
                errors_seen.append("groq: GROQ_API_KEY missing (free key at https://console.groq.com/keys)")
                continue
            try:
                return (groq_generate(prompt, system, temperature, max_tokens, groq_model, json_mode=bool(schema)),
                        f"groq:{groq_model or config.GROQ_MODEL}")
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    raise ProviderError(f"Groq rejected GROQ_API_KEY ({e.response.status_code}): check the key in .env")
                if e.response.status_code == 429:
                    try:
                        groq_wait = float(e.response.headers.get("retry-after", "") or "nan")
                    except ValueError:
                        groq_wait = None
                elif e.response.status_code == 400 and schema:
                    errors_seen.append("groq: HTTP 400 (invalid JSON)")
                    continue
                errors_seen.append(f"groq: HTTP {e.response.status_code}")
            except httpx.HTTPError as e:
                errors_seen.append(f"groq: {type(e).__name__}")
        else:
            if not config.KEY_IS_SET:
                errors_seen.append("gemini: GEMINI_API_KEY missing (https://aistudio.google.com/apikey)")
                continue
            try:
                text, m = _gemini_once(prompt, system, temperature, max_tokens, model, schema)
                if text:
                    return clean_text(text), f"gemini:{m}"
                errors_seen.append("gemini: empty response")
            except Exception as e:
                if not _is_fallback_error(e):
                    raise
                errors_seen.append(f"gemini: {str(e)[:80]}")
    # last resort only (every provider failed): if Groq's token budget resets within 10 s, wait once
    if groq_wait is not None and groq_wait == groq_wait and groq_wait <= 10:
        print(f"[llm] all providers failed; waiting {groq_wait:.0f} s for Groq's per-minute limit to reset")
        time.sleep(groq_wait + 0.5)
        try:
            return (groq_generate(prompt, system, temperature, max_tokens, groq_model, json_mode=bool(schema)),
                    f"groq:{groq_model or config.GROQ_MODEL}")
        except httpx.HTTPError as e:
            errors_seen.append(f"groq (after wait): {type(e).__name__}")
    raise ProviderError("No LLM provider could answer: " + " | ".join(errors_seen))
