# BIS Assistant: build instructions for Claude Code

Project: SIH26107, an AI-powered intelligent assistant for Indian Standards and BIS services.
Owner: Prateek (AI/ML lead). Claude Code writes all code. It downloads all data itself from `data/sources.yaml`; the owner downloads nothing by hand.

## Goal of Phase 1 (build this first)
A **text-only, multi-agent RAG chatbot**. It answers questions about BIS law, certification, product rules (QCOs) and hallmarking, and **every answer has citations to official BIS documents**. Images come in Phase 2. Do not start them now.

Why RAG, not fine-tuning: rules change often (new QCOs and amendments every month). With RAG we re-download and re-index, with no retraining. Every answer can point to the exact document and page. Fine-tuning cannot cite, and it goes stale.

---

## Fixed tech stack (do not swap without asking)
| Part | Choice |
|---|---|
| Language | Python 3.11+ |
| LLM | Google Gemini via `google-genai` SDK. `GEMINI_MODEL` then `GEMINI_MODEL_FALLBACKS` (quota is per model; each model is tried on every key in `GEMINI_API_KEY`, `GEMINI_API_KEY_2`). Flash-Lite (`GEMINI_ROUTER_MODEL`) for cheap calls (Hindi→English query, eval judge). On import, `app/config.py` prints the available Flash models. |
| Fallback LLM | Groq (`GROQ_API_KEY`, `GROQ_MODEL`), then local Ollama (`OLLAMA_MODEL=qwen2.5:7b`). No waiting on 429: move to the next provider. |
| Pipeline | Single knowledge base, linear pipeline in `app/answer.py` (the old LangGraph multi-agent graph is in `app/agents_old/`, not used; owner approved in Task 1/2) |
| Embeddings | Local `bge-m3` via Ollama (`EMBED_PROVIDER=ollama`), 1024 dims; Gemini embeddings still supported (`EMBED_PROVIDER=gemini`, 1000/day free) |
| Reranker | Local ONNX cross-encoder via `fastembed` (`RERANK_MODEL`, default `Xenova/ms-marco-MiniLM-L-12-v2`; Intel Mac, no PyTorch) |
| Vector DB | Qdrant in **local embedded mode** (`QdrantClient(path="index/qdrant")`), no server needed |
| Keyword search | `rank_bm25` (exact IS numbers such as "IS 1293" must match) |
| Fusion | Reciprocal Rank Fusion of vector + BM25 results |
| PDF parsing | PyMuPDF (`pymupdf`). If a page has no text layer (scanned or Hindi Gazette), send that page to Gemini for text extraction. |
| HTML parsing | `httpx` + `beautifulsoup4` (+ `pandas.read_html` for tables) |
| API | FastAPI with streaming (SSE) |
| Test UI (Phase 1) | Streamlit chat. The web teammate builds the real Next.js UI against the same API later. |
| Evaluation | RAGAS + a hand-checked question set |

---

## Folder structure (create exactly this)
```
bis-assistant/
├── CLAUDE.md                  # this file
├── .env.example               # keys and model names (copy to .env)
├── requirements.txt
├── data/
│   ├── sources.yaml           # download list (given)
│   ├── raw/pdf/<agent>/       # downloaded PDFs, named <id>.pdf
│   ├── raw/html/<agent>/      # saved page text, named <id>.md
│   ├── structured/            # CSVs from table_scrape (products, QCOs)
│   ├── processed/chunks.jsonl # all chunks with metadata
│   └── download_log.csv       # id, url, status, bytes, sha256, date
├── index/qdrant/              # vector index (git-ignored)
├── scripts/
│   ├── download.py            # reads sources.yaml and downloads everything
│   ├── parse.py               # PDF/HTML → clean text, with page numbers
│   ├── chunk.py               # text → chunks.jsonl
│   ├── build_index.py         # chunks → Qdrant + BM25 pickle
│   └── refresh.sh             # download → parse → chunk → build_index
├── app/
│   ├── config.py              # loads .env
│   ├── llm.py                 # Gemini client + Ollama fallback + retry
│   ├── retrieval.py           # hybrid search (vector + BM25 + RRF), filter by agent
│   ├── prompts.py             # all system prompts (rules below)
│   ├── agents/
│   │   ├── state.py           # the shared graph state
│   │   ├── router.py
│   │   ├── law_agent.py
│   │   ├── certification_agent.py
│   │   ├── product_qco_agent.py
│   │   ├── hallmarking_consumer_agent.py
│   │   ├── composer.py        # merges answers, adds citations
│   │   └── guard.py           # checks grounding; refuses if unsupported
│   ├── graph.py               # builds the LangGraph
│   ├── tools.py               # product lookup in CSVs, official-link lookup
│   └── api.py                 # FastAPI: POST /chat (SSE), GET /health, GET /sources
├── ui/streamlit_app.py
├── eval/
│   ├── questions.jsonl        # question, expected_answer, expected_source_ids, type
│   └── run_eval.py            # RAGAS + citation checks → eval/report.md
└── tests/                     # pytest: download, chunking, retrieval, graph routing
```

---

## Step 1: Download (scripts/download.py)
- Read `data/sources.yaml` and obey `download_rules`: 2 s delay, robots.txt, retries, and skip files already downloaded.
- `pdf` → save to `data/raw/pdf/<agent>/<id>.pdf`. Check the file really is a PDF (it starts with `%PDF`).
- `html` → take the main content only (remove nav, header and footer). Save it as markdown in `data/raw/html/<agent>/<id>.md`, with the source URL and date at the top.
- `table_scrape` → read the table(s) into `output_csv`. Keep every link found in a row (column `qco_pdf_url`). Then download **each linked QCO PDF** to `data/raw/pdf/product_qco/qco_<slug>.pdf`.
- `follow_links_same_section: true` → also save the sub-pages under the same URL path (one level deep only).
- Never log in, never solve a CAPTCHA, and never download ISO/IEC-adopted paid standards.
- Write every attempt to `data/download_log.csv`. At the end, print a summary: downloaded / skipped / failed.
- Command: `python scripts/download.py --priority 1` (then run it again with `--priority 2`).

## Step 2: Parse and chunk
- Keep **page numbers** for PDFs (citations need them).
- Clean the text: repeated headers and footers, hyphenated line breaks, Gazette boilerplate. Keep Hindi text if present. Mark `lang` as `hi` or `en`.
- Chunk by **structure first**: split on "Section", "Rule", "Regulation", "Clause", "Schedule" headings and numbered items. Then cap each chunk at ~800 tokens with ~100 tokens of overlap.
- Each chunk in `chunks.jsonl`:
  `{chunk_id, source_id, title, url, agent, doc_type(act|rule|regulation|order|qco|faq|guideline|page), page, section, lang, text, date_downloaded}`
- Also turn each row of the product CSVs into a small text chunk, e.g. "Product: Sulphate Resisting Portland Cement | IS 12330 | Scheme I | QCO: Cement (Quality Control) Order 2003, S.O. 191(E) | PDF: <url>".

## Step 3: Index
- Embed every chunk (in batches; retry on rate limits). Store it in Qdrant with the full metadata as payload, one collection called `bis_docs`.
- Build a BM25 index over the same chunks and save it to `index/bm25.pkl`.
- Retrieval function: `search(query, agent=None, k=8)` → vector top-20 + BM25 top-20 → RRF → top-k, with an optional filter on `agent`.

---

## Step 4: The answer pipeline (current; replaces the agent graph below)

```
question → normalize (IBS/BSI→BIS, IS numbers) → [Hindi: 1 Flash-Lite call → English query]
 → rule-based expansions (app/expand.py) → vector (bge-m3) + BM25 for each query → RRF
 → exact product/IS rows from the CSVs → scheme filter/boost + topic boosts → collapse duplicates
 → local reranker vote → top 12 + neighbour chunks → ONE LLM call (answer template, [n] citations)
 → citation cleanup (merge same page, renumber) → local citation check (re-cite or remove sentence)
 → answer + sources, or exactly "not covered in the official BIS documents" + official links
```
- Never answer from model knowledge (no "general answers"). Off-topic → the "not covered" reply.
- Chunks carry `scheme` (I, II, IV, X, FMCS, Hallmarking, general) and `doc_date`; newer documents win.
- Debug retrieval: `python scripts/debug_search.py "question"` or `POST /search`.
- Terminal chat: `python ui/chat_cli.py` (`/trace` shows the chunks and the citation check).

## Step 4 (original design, superseded): The agent graph (LangGraph)

```
            user question (text)
                    │
             ┌──────▼──────┐
             │   ROUTER    │  Flash-Lite, JSON output:
             │             │  {intents:[...], language, is_greeting, out_of_scope}
             └──────┬──────┘
   ┌──────────┬─────┴──────┬───────────────┐     (runs 1 or more in parallel)
   ▼          ▼            ▼               ▼
 LAW       CERTIFICATION  PRODUCT_QCO    HALLMARKING_CONSUMER
 Act,      ISI/CRS/FMCS/  product → IS   HUID, hallmark rules,
 Rules,    Scheme X steps, no. → scheme → complaints, verify
 Regs,     fees, simplified QCO + date   guidance, BIS CARE
 penalties procedure, labs (uses CSV tool)
   └──────────┴─────┬──────┴───────────────┘
             ┌──────▼──────┐
             │  COMPOSER   │  one answer; numbered citations [1][2]
             └──────┬──────┘
             ┌──────▼──────┐
             │   GUARD     │  every claim supported by a retrieved chunk?
             └──────┬──────┘  no → rewrite or refuse honestly
                    ▼
         answer + citations + official links
```

**State** (`state.py`): `question, language, intents, agent_outputs{agent: {answer, chunks}}, final_answer, citations[], refused(bool), trace[]`.

**Each specialist agent:**
1. Calls `search(question, agent=<its own name>)`. The product_qco agent also calls the `lookup_product(name_or_is_number)` tool on the CSVs first.
2. Answers **only from the retrieved chunks**. Returns `{answer, used_chunk_ids}`.
3. If the chunks don't contain the answer, returns `NOT_FOUND`.

**Router rules:**
- It may pick several intents. Example: "I make LED bulbs, is ISI compulsory and what is the fee?" → product_qco + certification.
- Greeting → reply briefly without retrieval.
- Out of scope (not BIS or standards) → polite refusal.

**Guard:** a second, cheap Gemini call that asks "Is each sentence supported by these chunks?". Unsupported sentences are removed. If nothing is left → refuse.

**Trace:** record which agents ran and which chunks they used, and return it in the API. The UI shows it as "How I answered". Judges like this.

---

## Chatbot rules (put these in `prompts.py`; every agent must follow them)
1. **Answer only from retrieved official BIS documents.** Never from memory. If not found, say: "I could not find this in official BIS documents I have. Please check <official link> or contact BIS." and give the relevant link from `official_links`.
2. **Always cite.** Every factual sentence ends with [n]. At the end, list each source as: title, section/clause if known, page, and URL.
3. **Law first, precision always.** Quote section, regulation and QCO numbers exactly (e.g. "Section 17 of the BIS Act, 2016", "S.O. 191(E)"). Never invent numbers, dates, fees or penalties.
4. **Say the date.** For QCOs, fees and deadlines, state the date of the document used and add: "Rules change often; confirm the latest on bis.gov.in."
5. **Not legal advice.** When a question is about penalties, disputes or legal liability, add one line: "This is information, not legal advice."
6. **Never verify a licence, HUID or R-number yourself.** Check the format only, then send the user to the BIS CARE app or the official portal link.
7. **Don't copy standards' full text** (BIS copyright). Summarise and link to the free download site or Know Your Standard.
8. **Answer in the user's language** (Hindi or English). Keep IS numbers, S.O. numbers and official terms exactly as written.
9. **Simple words, short answers.** Start with the direct answer (yes/no/number), then steps as a list, then the sources.
10. **Stay in scope:** BIS, Indian Standards, certification, hallmarking, and consumer questions about BIS marks. Politely refuse anything else.
11. **No personal data.** Don't ask for or store names, phone numbers or Aadhaar.
12. **Admit conflicts.** If two documents disagree (e.g. an old QCO and its amendment), say so and prefer the newer one, citing both.

---

## Step 5: API and test UI
- `POST /chat` `{message, session_id}` → SSE stream: `token` events, then `citations`, `trace` and `done` events.
- `GET /sources` → the list of indexed documents with dates (for the "Knowledge base" panel).
- Streamlit UI: chat box, streamed answer, citation cards (title, page, link) and an expandable "How I answered" trace.

## Step 6: Evaluation (before any demo)
- `eval/questions.jsonl`: at least 60 questions to start (target 150).
  - 15 law
  - 15 certification
  - 15 product/QCO
  - 10 hallmarking/consumer
  - 5 trick or out-of-scope questions that **must be refused**
  - 10 in Hindi
- Draft the questions with Gemini from the chunks, then **the team checks every answer by hand**.
- `run_eval.py` reports: faithfulness, answer relevancy and context recall (RAGAS); citation validity (does the cited chunk exist and support the claim?); refusal accuracy; router accuracy; p50/p95 latency.
- Write the results to `eval/report.md`. Aim for: faithfulness ≥ 0.85, refusal accuracy ≥ 90%, citation validity ≥ 90%.

---

## Build order and "done" checks
| # | Task | Done when |
|---|---|---|
| 1 | Set up the project, requirements, .env, config | `python -c "import app.config"` works; the model list is printed |
| 2 | download.py | priority 1 downloads; log has 0 unexpected failures; products_scheme1.csv has rows with IS numbers |
| 3 | parse + chunk | chunks.jsonl exists; a sample chunk shows the right page and section |
| 4 | build_index + retrieval | `search("IS 12330")` returns the cement row first; `search("penalty for misuse of standard mark")` returns BIS Act chunks |
| 5 | Single-agent RAG (no router yet) | answers with correct citations for 10 sample questions |
| 6 | Full LangGraph (router + 4 agents + composer + guard) | multi-intent question routes to 2 agents; out-of-scope question is refused |
| 7 | FastAPI + Streamlit | streaming chat works end to end on localhost |
| 8 | Eval | eval/report.md generated; fix the weakest area |
| 9 | Priority-2 sources + refresh.sh | one command re-downloads and re-indexes |

Work one step at a time. After each step, run its "done" check, commit, and show the owner a short result.

## Phase 2 (later, do not build now)
Image input: Gemini vision reads a product photo → mark type (ISI/CRS/Hallmark), CM/L / R-number / HUID, product type → added to the graph as a new **VISION** agent that feeds `product_qco` and `hallmarking_consumer`. Then Hindi voice, then the Next.js UI.

## Git
Ignore `.env`, `data/raw/`, `index/`. Commit `data/sources.yaml`, `data/structured/*.csv` and the code.
