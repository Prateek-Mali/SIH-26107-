# BIS Assistant (SIH26107)

An AI assistant for **Indian Standards and BIS services**. It answers questions about the BIS Act, Rules and
Regulations, product certification (ISI / Scheme I, CRS / Scheme II, FMCS, Scheme IV / X), Quality Control Orders
(QCOs), hallmarking and consumer matters. **Every answer cites official BIS documents**, with page links.

It is built on retrieval-augmented generation (RAG): documents are downloaded from bis.gov.in, split into cited
chunks and searched at question time. When the rules change (new QCOs, amendments), you re-download and
re-index. No retraining is needed.

## What it can do

- **Answer with citations:** every fact ends with `[n]`, and a source list gives the title, section, page and URL.
  A local checker removes any sentence its source does not support.
- **Advise:** it works out who you are (manufacturer, importer, jeweller, consumer) and what you want, then answers
  as an action plan, steps, a comparison table or a problem-solving guide.
- **Recommend standards:** describe a product ("stainless steel water bottle") and it returns the Indian Standard(s),
  whether certification is compulsory, the QCO (S.O. number, date) and the scheme.
- **Select the scheme:** Scheme I, FMCS, CRS or Hallmarking, with the rule that decides it and next steps, each
  backed by a document.
- **Reasoning agent:** plans, calls tools (search, product lookup, scheme selection, read neighbouring text),
  checks for gaps, then answers.
- **Honest refusals:** if the documents do not cover something, it says so and gives official links. It never
  answers from model memory.
- English and Hindi.

## How it works

```
question
  └─ agent (Groq gpt-oss-120b → Gemini → local Ollama)
       ├─ search_documents   hybrid search: bge-m3 vectors (Qdrant) + BM25, reciprocal rank fusion
       ├─ lookup_product     product index: IS number, QCO, scheme, compulsory status
       ├─ select_scheme      rule table (app/scheme_rules.yaml), every rule cites its source chunk
       └─ get_chunk_neighbours
  └─ citation check (local reranker + number check) → answer + sources
```

The knowledge base holds **3,600+ chunks** from about 550 official documents (BIS Act 2016, BIS Rules 2018, Conformity
Assessment Regulations and amendments, grant/renewal/surveillance guidelines, FAQs, hallmarking regulations and
orders, about 500 QCO PDFs), plus **995 products** from the BIS compulsory-certification lists.

| Part | Choice |
|---|---|
| LLM | Groq (`gpt-oss-120b`, `gpt-oss-20b`) → Google Gemini (model fallback chain) → local Ollama (`qwen2.5:3b`) |
| Embeddings | `bge-m3` via Ollama (local, free, Hindi + English) |
| Vector DB | Qdrant, embedded mode (no server) |
| Keyword search | `rank_bm25` (exact IS / S.O. numbers) |
| Reranker | `BAAI/bge-reranker-base` (ONNX via `fastembed`, CPU) |
| PDF / HTML | PyMuPDF, httpx + BeautifulSoup |
| API | FastAPI (JSON and SSE streaming) |

## Setup

Needs Python 3.11+ and [Ollama](https://ollama.com).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
ollama pull bge-m3
ollama pull qwen2.5:3b          # offline fallback model
cp .env.example .env            # then add your keys
```

Keys in `.env`:
- `GROQ_API_KEY`: free at https://console.groq.com/keys
- `GEMINI_API_KEY` (optional `GEMINI_API_KEY_2`): free at https://aistudio.google.com/apikey

## Build the knowledge base

```bash
.venv/bin/python scripts/download.py --priority 1   # official sources from data/sources.yaml (polite: 2 s delay, robots.txt)
.venv/bin/python scripts/parse.py                   # PDF/HTML -> text with page numbers
.venv/bin/python scripts/chunk.py                   # structure-aware chunks -> data/processed/chunks.jsonl
.venv/bin/python scripts/build_index.py             # bge-m3 vectors + BM25
.venv/bin/python scripts/build_product_index.py     # product index for the recommender
```

To re-download and re-index everything later, run `bash scripts/refresh.sh`.
Documents that could not be downloaded (BIS server returns 403) are listed in `data/MISSING_DOCS.md`. Put them in
`data/manual/` and re-index.

## Run

Terminal chat (`/trace` shows how it answered):
```bash
.venv/bin/python ui/chat_cli.py
```

API server:
```bash
.venv/bin/uvicorn app.api:app --port 8000
```

| Endpoint | What it does |
|---|---|
| `POST /chat` | `{message, session_id}` → answer, citations, sources, provider, latency |
| `POST /chat/stream` | same, as Server-Sent Events |
| `POST /recommend` | `{description}` → candidate Indian Standards (IS, compulsory, QCO, scheme) |
| `POST /scheme` | `{profile}` → scheme, why, next steps, sources |
| `POST /search` | raw retrieval results (for debugging) |
| `GET /health`, `GET /sources` | status, and the list of indexed documents |
| `POST /admin/reindex` | re-parse, re-chunk and re-index in the background |

Set `AGENT_MODE=off` in `.env` to use the simpler linear pipeline instead of the agent. The agent also falls back
to it automatically if it fails, so the demo never breaks.

## Test and evaluate

```bash
.venv/bin/python -m pytest tests          # unit tests + recommender cases (these need Ollama)
.venv/bin/python eval/quick_eval.py       # 10 questions, local scoring, one line each
.venv/bin/python eval/run_eval.py         # full question set -> eval/report.md
```

Tools for inspecting the knowledge base:
- `scripts/chunk_report.py` writes the chunk statistics report.
- `scripts/embedding_map.py` builds an interactive 2D map of the vectors with a search box.
- `scripts/knowledge_graph.py` builds an interactive graph of documents and chunks.
- `scripts/export_obsidian.py` exports the knowledge base as an Obsidian vault.
- `scripts/debug_search.py "question"` shows what retrieval returns for a question.

## Project layout

```
app/        agent, answer pipeline, retrieval, recommender, scheme rules, prompts, LLM providers, API
scripts/    download, parse, chunk, index, product index, inspection tools
data/       sources.yaml, product tables (structured/), download log, manual uploads
eval/       question sets, eval runners, reports
tests/      pytest suite
ui/         terminal chat, Streamlit test UI
```

## Limits

- Answers are information, not legal advice. Rules change often, so confirm the latest on https://www.bis.gov.in.
- Some official PDFs are scanned and still need OCR; some BIS links return 403 (see `data/MISSING_DOCS.md`).
- The assistant never verifies a licence, HUID or R-number itself. It points to the BIS CARE app.

Built for Smart India Hackathon, problem statement SIH26107.
