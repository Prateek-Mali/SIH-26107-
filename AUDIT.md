# BIS Assistant: Phase 0 audit

Audit date: 2026-09-26. Read-only: no code was changed for this report. A copy of the vector index was used, so the audit did not touch the live one.

## 1. Code status

26 of 26 unit tests pass (`pytest tests`).

| File | What it does | Status |
|---|---|---|
| `app/config.py` | Loads `.env` (keys, model names, fallback chains, paths); prints the available Flash models on import | working |
| `app/llm.py` | Gemini client. On 429/503 it tries the other key, then the next model in the chain (60 s cooldown). Also embeddings, OCR, and Ollama as a last resort | working. **Ollama fallback is broken**: `OLLAMA_MODEL=qwen2.5:3b` is not installed (only `llama3.2:1b`) |
| `app/retrieval.py` | Hybrid search: Qdrant vectors top-20 + BM25 top-20 → RRF → top-k; optional `agent` filter; normalises IS/S.O./G.S.R. numbers; pauses vector search for 10 min if the query embedding fails | working |
| `app/prompts.py` | The 12 chatbot rules, router, agent, composer and guard prompts, greeting and refusal texts | working |
| `app/tools.py` | `lookup_product()` over the product CSVs (IS number or name); `official_link()` | working. **Bug**: IS numbers written `IS/IEC 62368` are not recognised (all of Scheme II) |
| `app/agents/state.py` | LangGraph state | working |
| `app/agents/router.py` | Flash-Lite router → intents, language, greeting, out_of_scope, standalone search query | working (to be removed in Phase 2: single knowledge base, no router refusals) |
| `app/agents/specialist.py` | Shared agent logic: search filtered by agent → answer only from excerpts → `NOT_FOUND` | working (to be replaced in Phase 2) |
| `app/agents/{law,certification,product_qco,hallmarking_consumer}_agent.py` | The four specialists (product_qco also calls `lookup_product`) | working (to be moved to `agents_old/`) |
| `app/agents/composer.py` | Merges agent answers, one global citation numbering | working (to be replaced) |
| `app/agents/guard.py` | Sentence-level grounding check with Flash-Lite; removes unsupported sentences; renumbers citations; appends source list | working (logic reused in Phase 2) |
| `app/graph.py` | LangGraph: router → specialists in parallel → composer → guard | working (to be replaced by the linear pipeline) |
| `app/api.py` | FastAPI: `POST /chat` (SSE only), `GET /health`, `GET /sources`, `GET /` | working. **Missing**: non-streaming `/chat` JSON, `/chat/stream`, `/search`, `/admin/reindex` |
| `ui/chat_cli.py` | Terminal chat (via API, or in-process if the API is down); `/trace`, `/new` | working. Errors are shown in yellow, not red |
| `ui/streamlit_app.py` | Streamlit test UI | working, **unused** (backend-only now) |
| `scripts/download.py` | Downloads `sources.yaml`: PDFs (checks `%PDF`), HTML main content → markdown, table scrape with rowspans → CSV + linked QCO PDFs, robots.txt, 2 s delay, retries, log | working. `follow_links_same_section` not yet exercised live (hallmarking FAQ not reached yet) |
| `scripts/parse.py` | PDF → per-page text (side-margin section titles folded in, Gazette boilerplate removed, garbled legacy-font Hindi dropped when English exists); HTML markdown; OCR hook | working. **OCR never run** (key was missing at parse time) |
| `scripts/chunk.py` | Structure-first chunking (Chapter/Section/Rule/Regulation/Schedule/numbered items) → ≤800 tokens with 100 overlap; one chunk per product row | working |
| `scripts/build_index.py` | BM25 pickle + Gemini embeddings (cached, 20 per batch) → Qdrant `bis_docs`; survives the daily quota with a partial index | working |
| `scripts/refresh.sh` | download → parse → chunk → index | untested end to end |
| `eval/run_eval.py` | Runs the question set; refusal/router/citation validity/latency; RAGAS or Gemini judge → `eval/report.md` | working (smoke-tested on 5 questions). **Missing**: retrieval hit@5 |
| `eval/draft_questions.py` | Drafts eval questions from chunks with Gemini | untested |
| `eval/questions.jsonl` | 5 out-of-scope questions only | incomplete |
| `tests/test_download.py` | Table scrape (rowspan, category rows, mobile copy), markdown cleanup, sub-page links, guards, slugs | working |
| `tests/test_chunking.py` | Structure splits, page tracking, caps and overlap, cleaning, doc types, product rows | working |
| `tests/test_retrieval.py` | ID normalisation, RRF, IS 12330 → cement first, penalty → BIS Act, agent filter, product lookup | working |
| `tests/test_graph.py` | Routing with a fake LLM: multi-intent, out of scope, greeting, not found, guard removal, citation renumbering | working |
| `tests/test_llm.py` | Model/key fallback order with fake clients | working |

## 2. LLM status

Provider: **Gemini** (`google-genai` SDK). Two API keys are configured (`GEMINI_API_KEY`, `GEMINI_API_KEY_2`). Fallback: Ollama at `http://localhost:11434`.

| Setting | Value |
|---|---|
| `GEMINI_MODEL` | `gemini-3.6-flash`, then fallbacks `gemini-3.8-flash, gemini-3-flash-preview, gemini-2.5-flash, gemini-3.5-flash-lite, gemini-3.1-flash-lite` |
| `GEMINI_ROUTER_MODEL` | `gemini-3.5-flash-lite`, then fallbacks `gemini-3.1-flash-lite, gemini-flash-lite-latest, gemini-3.5-flash` |
| `GEMINI_EMBED_MODEL` | `gemini-embedding-001` (768 dims) |
| `OLLAMA_MODEL` | `qwen2.5:3b`: **not installed**. Installed models: `llama3.2:1b` |

Live test calls:
```
key1 LLM gemini-3.6-flash:      OK -> 'OK'
key1 LLM gemini-3.5-flash-lite: OK -> 'OK'
key1 EMBED:                     ERROR -> 429 RESOURCE_EXHAUSTED ... Quota exceeded for metric:
        generativelanguage.googleapis.com/embed_content_free_tier_requests, limit: 1000 (per day, per project, per model)
key2 LLM gemini-3.6-flash:      OK -> 'OK'
key2 LLM gemini-3.5-flash-lite: OK -> 'OK'
key2 EMBED gemini-embedding-001: OK -> dim 768
```
Both keys are valid. Key 1 has used its **1000 embeddings/day** free quota. Key 2 still has quota today.

## 3. Data inventory

Status meanings:
- **OK**: file present with a text layer.
- **FAILED**: a download was attempted and failed.
- **MISSING (pending)**: priority 1, not reached yet. The priority-1 download is still running; it is on the product tables now, and hallmarking comes last.
- **MISSING (not attempted)**: priority 2, not run yet.
- **EMPTY-TEXT**: no usable text layer (scanned), needs OCR.

| id | title | expected file | exists? | size | pages | text chars | scanned pages (<50 chars) | status |
|---|---|---|---|---|---|---|---|---|
| bis_act_2016 | Bureau of Indian Standards Act, 2016 | data/raw/pdf/law/bis_act_2016.pdf | yes | 133 KB | 17 | 54955 | 0 | OK |
| bis_act_2016_indiacode | BIS Act, 2016 (India Code copy, fallback) | data/raw/pdf/law/bis_act_2016_indiacode.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| bis_act_removal_of_difficulty_2019 | BIS Act 2016 with Removal of Difficulty Order, 2019 | data/raw/pdf/law/bis_act_removal_of_difficulty_2019.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| bis_act_enforcement | Enforcement of BIS Act, 2016 | data/raw/pdf/law/bis_act_enforcement.pdf | no | - | - | - | - | FAILED (HTTP 403) |
| bis_rules_2018 | BIS Rules, 2018 (with all amendments) | data/raw/pdf/law/bis_rules_2018.pdf | yes | 846 KB | 57 | 123415 | 0 | OK |
| ca_regulations_2018 | BIS (Conformity Assessment) Regulations, 2018 | data/raw/pdf/law/ca_regulations_2018.pdf | yes | 7141 KB | 412 | 715150 | 11 | OK (some scanned pages) |
| ca_amdt_2020 | CA Amendment Regulations, 2020 | data/raw/pdf/law/ca_amdt_2020.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2021_1 | CA First Amendment Regulations, 2021 | data/raw/pdf/law/ca_amdt_2021_1.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2021_2 | CA Second Amendment Regulations, 2021 | data/raw/pdf/law/ca_amdt_2021_2.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2021_3 | CA Third Amendment Regulations, 2021 | data/raw/pdf/law/ca_amdt_2021_3.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2021_4 | CA Fourth Amendment Regulations, 2021 | data/raw/pdf/law/ca_amdt_2021_4.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2021_5 | CA Fifth Amendment Regulations, 2021 | data/raw/pdf/law/ca_amdt_2021_5.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2021_6 | CA Sixth Amendment Regulations, 2021 | data/raw/pdf/law/ca_amdt_2021_6.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2022 | CA Amendment Regulations, 2022 (Scheme X) | data/raw/pdf/law/ca_amdt_2022.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2023 | CA Amendment Regulations, 2023 | data/raw/pdf/law/ca_amdt_2023.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2024_mar | CA Amendment Regulations, March 2024 | data/raw/pdf/law/ca_amdt_2024_mar.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2024_sep | CA Regulations amendment, Sep 2024 | data/raw/pdf/law/ca_amdt_2024_sep.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| ca_amdt_2026 | CA Amendment Regulations, 2026 | data/raw/pdf/law/ca_amdt_2026.pdf | yes | 1666 KB | 71 | 151429 | 0 | OK |
| ca_amdt_2026_corrigendum | Corrigendum to CA Amendment, 2026 | data/raw/pdf/law/ca_amdt_2026_corrigendum.pdf | yes | 680 KB | 2 | 3000 | 0 | OK |
| advisory_committees_regs | BIS Advisory Committees Regulations, 2018 (amended to J | data/raw/pdf/law/advisory_committees_regs.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| dg_powers_regs | BIS Powers and Duties of Director General Regulations,  | data/raw/pdf/law/dg_powers_regs.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| marking_requirements | Marking requirement as per BIS (CA) Regulations | data/raw/pdf/law/marking_requirements.pdf | yes | 84 KB | 1 | 1552 | 0 | OK |
| law_page | BIS Act, Rules & Regulations index page | data/raw/html/law/law_page.md | yes | 14 KB | - | 14450 | - | OK |
| cert_overview | Product Certification Overview | data/raw/html/certification/cert_overview.md | yes | 4 KB | - | 3924 | - | OK |
| cert_process | Product Certification Process | data/raw/html/certification/cert_process.md | yes | 3 KB | - | 2884 | - | OK |
| cert_fee | Product Certification Fee | data/raw/html/certification/cert_fee.md | yes | 5 KB | - | 5107 | - | OK |
| cert_faq | Product Certification FAQ | data/raw/html/certification/cert_faq.md | yes | 13 KB | - | 13402 | - | OK |
| cert_apply_online | Apply Online | data/raw/html/certification/cert_apply_online.md | yes | 0 KB | - | 212 | - | EMPTY-TEXT |
| simplified_procedure_list | List of Products under Simplified Procedure | data/raw/pdf/certification/simplified_procedure_list.pdf | yes | 306 KB | 31 | 84257 | 0 | OK |
| scheme_x_process | Scheme-X Certification Process | data/raw/html/certification/scheme_x_process.md | no | - | - | - | - | MISSING (not attempted, priority 2) |
| fmcs_overview | FMCS (Foreign Manufacturers) Overview | data/raw/html/certification/fmcs_overview.md | yes | 2 KB | - | 1598 | - | OK |
| fmcs_how_to_apply | FMCS How to Apply | data/raw/html/certification/fmcs_how_to_apply.md | yes | 2 KB | - | 1988 | - | OK |
| fmcs_fee | FMCS Fee | data/raw/html/certification/fmcs_fee.md | yes | 0 KB | - | 365 | - | OK |
| fmcs_faq | FMCS FAQs | data/raw/html/certification/fmcs_faq.md | yes | 6 KB | - | 6299 | - | OK |
| crs_order_2021 | Electronics & IT Goods (Requirement of Compulsory Regis | data/raw/pdf/certification/crs_order_2021.pdf | yes | 6231 KB | 14 | 0 | 14 | EMPTY-TEXT |
| crs_amdt_mar_2026 | CRS Order amendment S.O.1246(E), 10 Mar 2026 | data/raw/pdf/certification/crs_amdt_mar_2026.pdf | yes | 701 KB | 2 | 4928 | 0 | OK |
| crs_amdt_may_2026_hdd | CRS Order amendment S.O.2204(E), 5 May 2026 (Hard Disk  | data/raw/pdf/certification/crs_amdt_may_2026_hdd.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| crs_cctv_requirements | CCTV Essential Requirements S.O.1652(E), Apr 2024 | data/raw/pdf/certification/crs_cctv_requirements.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| crs_standard_mark_guidelines | CRS Standard Mark Guidelines | data/raw/pdf/certification/crs_standard_mark_guidelines.pdf | yes | 864 KB | 6 | 8417 | 0 | OK |
| lab_recognition_scheme | Lab Recognition Scheme 2020 | data/raw/pdf/certification/lab_recognition_scheme.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| scheme1_products_table | Scheme I (ISI mark): products under compulsory certific | data/structured/products_scheme1.csv | yes | 1656 KB | - | 803 rows | - | OK |
| scheme2_page | Scheme II (CRS registration) page | data/structured/products_scheme2.csv | yes | 94 KB | - | 75 rows | - | OK |
| scheme4_page | Scheme IV (Certificate of Conformity) products | data/structured/products_scheme4.csv | no | - | - | - | - | MISSING (not attempted, priority 2) |
| schemeX_page | Scheme X products | data/structured/products_schemeX.csv | no | - | - | - | - | MISSING (not attempted, priority 2) |
| fmcs_products | Products under FMCS | data/structured/products_fmcs.csv | no | - | - | - | - | MISSING (not attempted, priority 2) |
| upcoming_qcos | Upcoming QCOs notified and due for implementation | data/structured/upcoming_qcos.csv | no | - | - | - | - | MISSING (pending) |
| qco_guidance | Guidance Document on Quality Control Orders | data/raw/pdf/product_qco/qco_guidance.pdf | no | - | - | - | - | MISSING (pending) |
| product_specific_info | Product-specific information | data/raw/html/product_qco/product_specific_info.md | no | - | - | - | - | MISSING (not attempted, priority 2) |
| pib_qco_2025 | PIB release: 187 QCOs covering 769 products (Mar 2025) | data/raw/html/product_qco/pib_qco_2025.md | no | - | - | - | - | MISSING (not attempted, priority 2) |
| hm_regulations_2018 | BIS (Hallmarking) Regulations, 2018 (incl. Amdt 1) | data/raw/pdf/hallmarking_consumer/hm_regulations_2018.pdf | no | - | - | - | - | MISSING (pending) |
| hm_regs_amdt_2021 | Hallmarking Amendment Regulations, 2021 | data/raw/pdf/hallmarking_consumer/hm_regs_amdt_2021.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| hm_regs_amdt_2022 | Hallmarking Amendment Regulations, 2022 | data/raw/pdf/hallmarking_consumer/hm_regs_amdt_2022.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| hm_regs_amdt_2026 | Hallmarking Amendment Regulations, 2026 | data/raw/pdf/hallmarking_consumer/hm_regs_amdt_2026.pdf | no | - | - | - | - | MISSING (pending) |
| hm_order_2020 | Hallmarking of Gold Jewellery and Gold Artefacts Order, | data/raw/pdf/hallmarking_consumer/hm_order_2020.pdf | no | - | - | - | - | MISSING (pending) |
| hm_order_amdt_2020 | Hallmarking Order Amendment, 2020 | data/raw/pdf/hallmarking_consumer/hm_order_amdt_2020.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| hm_order_june_2021 | Hallmarking Order, June 2021 | data/raw/pdf/hallmarking_consumer/hm_order_june_2021.pdf | no | - | - | - | - | MISSING (pending) |
| hm_order_amdt_2022 | Hallmarking Order Amendment, 2022 | data/raw/pdf/hallmarking_consumer/hm_order_amdt_2022.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| hm_doca_notification | DoCA notification on precious metal articles | data/raw/pdf/hallmarking_consumer/hm_doca_notification.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| hm_overview | Hallmarking overview | data/raw/html/hallmarking_consumer/hm_overview.md | no | - | - | - | - | MISSING (pending) |
| hm_mandatory_order_page | Mandatory Hallmarking Order page | data/raw/html/hallmarking_consumer/hm_mandatory_order_page.md | no | - | - | - | - | MISSING (pending) |
| hm_faq_general | Hallmarking FAQ (general) | data/raw/html/hallmarking_consumer/hm_faq_general.md | no | - | - | - | - | MISSING (pending) |
| hm_jewellers_guidelines | Guidelines for Jewellers (Jul 2026) | data/raw/pdf/hallmarking_consumer/hm_jewellers_guidelines.pdf | no | - | - | - | - | MISSING (pending) |
| hm_ahc_guidelines | Guidelines for AHCs (Jul 2026) | data/raw/pdf/hallmarking_consumer/hm_ahc_guidelines.pdf | no | - | - | - | - | MISSING (not attempted, priority 2) |
| hm_marking_fee | Hallmarking marking fee | data/raw/html/hallmarking_consumer/hm_marking_fee.md | no | - | - | - | - | MISSING (not attempted, priority 2) |
| consumer_complaint | Online complaint registration | data/raw/html/hallmarking_consumer/consumer_complaint.md | no | - | - | - | - | MISSING (pending) |
| consumer_protection | Consumer protection | data/raw/html/hallmarking_consumer/consumer_protection.md | no | - | - | - | - | MISSING (pending) |
| bis_care_app_page | BIS apps (BIS CARE) | data/raw/html/hallmarking_consumer/bis_care_app_page.md | no | - | - | - | - | MISSING (pending) |

### Counts per agent and priority

| agent | priority | OK | FAILED | MISSING | other |
|---|---|---|---|---|---|
| law | 1 | 7 | 1 | 0 | 0 |
| law | 2 | 0 | 0 | 15 | 0 |
| certification | 1 | 11 | 0 | 0 | 2 |
| certification | 2 | 0 | 0 | 4 | 0 |
| product_qco | 1 | 2 | 0 | 2 | 0 |
| product_qco | 2 | 0 | 0 | 5 | 0 |
| hallmarking_consumer | 1 | 0 | 0 | 11 | 0 |
| hallmarking_consumer | 2 | 0 | 0 | 7 | 0 |

### Product / QCO tables

**products_scheme1.csv**: 803 rows; columns: s_no, category, is_number, product, qco_title, qco_pdf_url, source_id, source_url, date_downloaded

- IS 12330 | Sulphate Resisting Portland Cement | 1. Cement (Quality Control)Order, 2003 S.O. No. 191(E) Dt. 17 Feb 2003 | https://www.bis.gov.in/MandatoryProducts/QCOrder/SO-No-191(E).pdf
- IS 12600 | Low heat Portland Cement | 1. Cement (Quality Control)Order, 2003 S.O. No. 191(E) Dt. 17 Feb 2003 | https://www.bis.gov.in/MandatoryProducts/QCOrder/SO-No-191(E).pdf
- IS 1489 (Part 1) | Portland Pozzolana Cement-Part1 Fly-ash based | 1. Cement (Quality Control)Order, 2003 S.O. No. 191(E) Dt. 17 Feb 2003 | https://www.bis.gov.in/MandatoryProducts/QCOrder/SO-No-191(E).pdf

**products_scheme2.csv**: 75 rows; columns: s_no, category, is_number, product, qco_title, qco_pdf_url, title, source_id, source_url, date_downloaded

- IS/IEC 62368: Part 1: 2023 | Electronic Games (Video) | Electronics & Information Technology Goods (Requirements for Compulsory Registration) Orde | http://crsbis.in/BIS/app_srv/tdc/gl/docs/gazette_notification_2012_10_03.pdf | h
- IS/IEC 62368: Part 1: 2023 | Laptop/Notebook/Tablets | Electronics & Information Technology Goods (Requirements for Compulsory Registration) Orde | http://crsbis.in/BIS/app_srv/tdc/gl/docs/gazette_notification_2012_10_03.pdf | h
- IS/IEC 62368: Part 1: 2023 | Plasma/ LCD/LED Televisions of screen size 32″ & above | Electronics & Information Technology Goods (Requirements for Compulsory Registration) Orde | http://crsbis.in/BIS/app_srv/tdc/gl/docs/gazette_notification_2012_10_03.pdf | h

**products_scheme4.csv**: not created yet

**products_schemeX.csv**: not created yet

**products_fmcs.csv**: not created yet

**upcoming_qcos.csv**: not created yet

### QCO PDFs from product tables

516 files, 570 MB, 2282 pages, of which 211 pages have <50 chars (scanned); 49 files are fully scanned (no text layer).
Unique PDF links in the tables: 573. Failed QCO downloads so far: 9: qco_199241 (HTTP 504), qco_199241 (HTTP 504), qco_egazette_malleable_iron_shots_and_grits (ReadTimeout: The read operatio), qco_aniline_amendment_order_00c61e (RemoteProtocolError: peer clos), qco_flame_producing_lighters_qco_2023_1 (RemoteProtocolError: peer clos), qco_aluminum_and_aluminum_alloy_products_quality_control_order_2025 (RemoteProtocolError: peer clos), qco_hinges_qco_pdf_26_july (ReadTimeout: The read operatio), qco_rubber_gaskets_for_pressure_cookers (RemoteProtocolError: peer clos), qco_indutech_qco_2024 (RemoteProtocolError: peer clos)

Followed sub-pages saved: 0

## 4. Index status

- chunks.jsonl: **1696** chunks from **76** documents/tables (built 2026-09-26 13:57)
- Qdrant collection `bis_docs`: **1115** points (embedding model `gemini-embedding-001`, 768 dims)
- BM25 index `index/bm25.pkl`: exists, **1696** chunks
- Chunk count vs point count: **MISMATCH (581 chunks have no vector: daily embedding quota)**
- Files on disk not yet in the index: **462** of 537 (PDF+HTML); index is stale vs downloads
- Chunks by agent: {'certification': 68, 'law': 403, 'product_qco': 1225}
- Chunks by doc_type: {'page': 18, 'faq': 13, 'order': 1, 'guideline': 42, 'act': 37, 'rule': 28, 'regulation': 332, 'qco': 1225}
- Chunks by lang: {'en': 1696}


## 5. Retrieval smoke test

Hybrid `search(query, k=5)` = vector top-20 + BM25 top-20 → RRF, no agent filter. `v`=found by vector, `b`=found by BM25.

**IS 12330** (hybrid)

| # | source_id | page | via | first 150 chars |
|---|---|---|---|---|
| 1 | scheme1_products_table | - | vb | Product: Sulphate Resisting Portland Cement / IS 12330 / Scheme I (ISI mark) / Category: Cement (any variety of cement manufactured or sold in India)  |
| 2 | qco_qco_on_144_steel_steel_products_1 | 63 | v | 31st December, 2020. Made from BIS standard marked Grain Oriented Electrical Steel Sheet and Strip conforming to IS 3024:2015 or Cold rolled nonorient |
| 3 | ca_regulations_2018 | 250 | b | 1 piece ₹ 46,000.00 ₹ 37,000.00 ₹ 2.70 All ₹ 0.00 ₹ 0.00 IS 12225:1997 1 piece ₹ 58,000.00 ₹ 47,000.00 ₹ 8.70 All ₹ 0.00 ₹ 0.00 IS 12227:2002 1000 pie |
| 4 | qco_qco_on_144_steel_steel_products_1 | 63 | v | 130. IS 12313: 1988 Specification For HotDip Terne Coated Carbon Steel Sheets [6 months from date of publication of this order.] 131. 6 months from da |
| 5 | ca_regulations_2018 | 2 | b | ₹ 48,000.00 ₹ 1.00 ₹ 0.00 ₹ 0.00 ₹ 79,000.00 ₹ 64,000.00 ₹ 0.95 ₹ 0.00 ₹ 0.00 12234:1988 ₹ 64,000.00 ₹ 52,000.00 ₹ 0.55 ₹ 0.00 ₹ 0.00 12254:1993 ₹ 69, |

**penalty for improper use of standard mark** (hybrid)

| # | source_id | page | via | first 150 chars |
|---|---|---|---|---|
| 1 | qco_145_qco_order | 35 | vb | 3. Compulsory use of Standard Mark. – Every steel and steel products specified in column (3) of Table 1 shall bear the Standard Mark under a licence f |
| 2 | qco_qco_on_144_steel_steel_products_1 | 41 | vb | 3. Compulsory use of Standard Mark: - Every steel and steel products specified in column (3) of Table 1 shall bear the Standard Mark under a licence f |
| 3 | qco_steel_qco_14022020_1 | 12 | vb | 3. Compulsory use of Standard Mark.- Every steel and steel products specified in column (3) of Table 1 shall bear the Standard Mark under a license fr |
| 4 | qco_steel_qco_2020_dated_27th_may_2020 | 20 | vb | 3. Compulsory use of Standard Mark.- Every steel and steel products specified in column (3) of Table 1 shall bear the Standard Mark under a license fr |
| 5 | bis_act_2016 | 13 | vb | 29. Penalty for contravention. (1) Any person who contravenes the provisions of section 11 or sub-section (1) of section 26 shall be punishable with f |

**documents required for grant of licence** (hybrid)

| # | source_id | page | via | first 150 chars |
|---|---|---|---|---|
| 1 | qco_s_o_1081_e | 95 | vb | 6. Particulars of NOC issued by District Authority where applicable 7. Particulars of CNG Dispensers/ Cascade & Compressors ….….  (In case of Form ‘G’ |
| 2 | ca_regulations_2018 | 309 | vb | 8. This application is being made for grant of licence of: (a) Indian Standard: (b) Product Category: (c) Product Name: Model Number(s) Brand Name 9.  |
| 3 | qco_s_o_1081_e | 94 | vb | 4. Name of the sea port/airport where cylinders/valves/LPG regulators are proposed to be imported: [5. Remarks:]  Signature of Applicant [Date of appl |
| 4 | ca_amdt_2026 | 50 | vb | 8. This application is being made for grant of licence of: (a) Indian Standard or essential requirements notified for the product or both: (b) Product |
| 5 | ca_regulations_2018 | 243 | vb | the factory or in a third party laboratory; (g) the manufacturer may apply for grant of licence in Form –V annexed to this Scheme and the Bureau shall |

**HUID hallmarking** (hybrid)

| # | source_id | page | via | first 150 chars |
|---|---|---|---|---|
| 1 | bis_act_2016 | 8 | vb | 14. Certification of Standard Mark of jewellers and sellers of certain specified goods or articles. (1) The Central Government, after consulting the B |
| 2 | bis_act_2016 | 1 | vb | 2. Definitions. In this Act, unless the context otherwise requires,— (1) "article" means any substance, artificial or natural, or partly artificial or |
| 3 | law_page | - | vb | / 7 / The Bureau of Indian Standards (Hallmarking) Regulations, 2018 / 2.5 MB / Pdf / [View](https://www.bis.gov.in/wp-content/uploads/2019/02/BIS-Hal |
| 4 | marking_requirements | 1 | v | BUREAU OF INDIAN STANDARDS (Registration Department) Our Ref: Registration/CRS E&IT & Solar Goods 06.09.2019 Subject: Marking requirement as per self- |
| 5 | law_page | - | b | / 18 / BIS (Conformity Assessment) Fourth Amendment Regulations, 2021 / 1 MB / Pdf / [View](https://www.bis.gov.in/wp-content/uploads/2021/08/BIS-CA-4 |

**CRS registration electronics** (hybrid)

| # | source_id | page | via | first 150 chars |
|---|---|---|---|---|
| 1 | crs_standard_mark_guidelines | 1 | vb | BUREAU OF INDIAN STANDARDS (Registration Department) Our Ref: Registration/CRS E&IT & Solar Goods 06.09.2019 Subject: Marking requirement as per self- |
| 2 | crs_amdt_mar_2026 | 1 | vb | No. 1194] NEW DELHI, TUESDAY, MARCH 10, 2026/PHALGUNA 19, 1947 1723 GI/2026 (1) MINISTRY OF ELECTRONICS AND INFORMATION TECHNOLOGY ORDER New Delhi, th |
| 3 | fmcs_overview | - | vb | # FMCS Overview  * Bureau of Indian Standards (BIS) has been operating a Foreign Manufacturers Certification Scheme (FMCS) since the year 2000 under [ |
| 4 | crs_standard_mark_guidelines | 6 | vb | 1. Devices utilizing e-labels shall have a physical label on the packaging of the product at the time of import, storage for sale and sale or distribu |
| 5 | crs_standard_mark_guidelines | 4 | vb | Annexure-II The IS number and licence number given above are examples only. Please also refer Gazette Notification S. O. 3240(E) dated 01 December 201 |


**Reading the smoke test:**
- **IS 12330:** row 1 is correct. Rows 2–5 are noise: fee-table rows and steel QCO lines that only share digits.
- **Penalty:** BIS Act Section 29 is only #5. It sits below four copies of the same "Compulsory use of Standard Mark" clause from different steel QCOs.
- **Documents for grant of licence:** #1 and #3 are Gas Cylinder Rules forms, which are wrong. #2 and #4 (the CA Regulations Form V application) are relevant but only partly answer it. The knowledge base has no "documents checklist" document.
- **HUID:** no hallmarking document is in the index yet, so the results are generic BIS Act sections.
- **CRS:** reasonable, but the main CRS Order 2021 is a scanned PDF with 0 extracted text.

## 6. What is wrong (cause → planned fix)

1. **No hallmarking or consumer documents (0 of 18).** Cause: `sources.yaml` order puts them last, and the priority-1 run is still on the QCO PDFs, which take hours because of slow and timing-out government servers. → Fix: let the run finish, then run priority 2. Retry failures 3×, and list anything left in `MISSING_DOCS.md`.
2. **24 priority-2 sources not attempted**, including all CA amendment regulations (2020–2024), Scheme IV/X/FMCS product tables, the Hallmarking amendments and the Lab Recognition Scheme. → Fix: `download.py --priority 2`.
3. **Dead links on bis.gov.in.** `bis_act_enforcement` returns HTTP 403, and `dg_powers_regs` and `hm_doca_notification` are in the same `/PDF/bs/` folder, so they will fail the same way. BIS's own page links to these dead URLs. → Fix: `MISSING_DOCS.md` plus `data/manual/`; ask you.
4. **Scanned pages are not OCR'd.** Affected: the CRS Order 2021 (14 of 14 pages, 0 chars), 49 fully scanned QCO PDFs (211 pages under 50 chars) and 11 pages of the CA Regulations. Cause: `parse.py` ran before the key existed. Tesseract has only `eng` installed (no `hin`), and ocrmypdf is not installed. → Fix: Gemini OCR through the model fallback chain (about 230 pages, cached per page). Tesseract `eng` is the offline backup.
5. **Index is stale:** 462 of 537 files on disk are not indexed yet. Only about 110 of 516 QCO PDFs and none of the new Scheme II rows are in it. Cause: the index was built mid-download. → Fix: re-parse, re-chunk and re-index after downloads.
6. **Vectors are missing: 581 of 1696 chunks.** Cause: the free-tier embedding limit is 1000 requests/day per project, and every chunk and every query costs one. The full knowledge base will be about 6000–8000 chunks (the CA Regulations alone are 412 pages; the QCO PDFs are 2282 pages). → **Decision needed** (see end).
7. **Query embeddings use the same daily quota.** Once it's used up, vector search pauses and answers fall back to BM25 only. → Fixed by the same decision as #6.
8. **Near-duplicate chunks crowd out the right source.** Dozens of QCOs repeat the same "Compulsory use of Standard Mark" and penalty clauses, which push BIS Act Section 29 down. → Fix: collapse near-duplicates (same normalised text) before reranking, plus a cross-encoder reranker (Phase 2).
9. **Numeric noise in vector results for IS numbers.** → Fix: exact CSV lookup first (already there), reranker, and keeping the BM25 exact match on top.
10. **Knowledge gap: "documents required / step-by-step grant of licence".** The official *Guidelines for Grant of Licence*, *Renewal*, *Change in scope*, *Factory/Market surveillance* and similar PDFs are linked from the Product Certification Process page but are **not in `sources.yaml`**. → Fix: propose them in `MISSING_DOCS.md` under "Suggested extra documents" (Phase 1c).
11. **`cert_apply_online` page is almost empty** (212 chars; the page is mostly links or JavaScript). → Fix: follow its links to the Manak Online manuals if they're public, or mark it as a gap.
12. **Scheme II rows can't be looked up by IS number.** `_norm_is()` misses `IS/IEC 62368` style numbers. The Scheme II CSV also has an extra junk `title` column. → Fix: extend the IS regex (IS/IEC, IS/ISO, "Part 1" forms) and normalise columns.
13. **Agent filters hide relevant chunks, and the router can refuse.** For example, CA Regulations Scheme II text lives under `law` but answers certification questions. → Fix (Phase 2, per brief): a single knowledge base `bis_kb`, no agent filters and no router refusals. Move the multi-agent code to `app/agents_old/`.
14. **Some QCO documents have weak titles and types.** For example, `qco_s_o_1081_e` is the Gas Cylinder Rules but is titled "S.O 1081 (E)" and typed `qco`. → Fix: take the title from the PDF's first page (order title plus S.O./G.S.R. number and date), and give each chunk an explicit `doc_date` so "newest wins" works.
15. **No document dates on chunks.** Only `date_downloaded` exists, so the "newest wins" rule can't compare the original regulation with its amendment. → Fix: extract the notification date from the first page or the S.O. line into `doc_date`.
16. **Ollama fallback does not work.** The configured model isn't installed. The brief asks for `qwen2.5:7b` (about 4.7 GB) → question for you.
17. **API is missing endpoints the brief asks for:** non-streaming JSON `/chat`, `/chat/stream`, `/search` and `/admin/reindex`, plus `provider` and `sources_used` fields. Also, embedded Qdrant allows only one process, so `/admin/reindex` must run inside the API process and reopen its client. → Fix in Phase 2.
18. **Latency is 7–15 s normally and 40–70 s when Gemini is overloaded (503)** and the chain falls to a slower model. The multi-agent flow makes 4–5 LLM calls per question. → Fix: the linear pipeline makes 3 calls (expansion with Flash-Lite, generation, check with Flash-Lite), and the model chain is ordered by speed.
19. **The eval set has only 5 questions and no hit@5 metric.** → Fix: Phase 3.
20. **Garbled Hindi text layer in Gazette PDFs.** The Hindi half uses legacy fonts and extracts as garbage. We keep the English half (same law), so `lang` is always `en` for PDFs. Hindi questions are answered from English chunks via multilingual embeddings. → Keep this. Only Hindi-only scanned pages get OCR'd.
21. **CLI shows errors in yellow and turns some failures into refusals.** For example, the agent JSON parse failure → `NOT_FOUND`. → Fix: surface real errors in red; never hide an error behind a refusal.

## Decisions needed before Phase 1/2

1. **Embeddings (affects #6 and #7).** The free Gemini tier allows 1000 embeddings per day per key. The full knowledge base needs about 6000–8000, plus one per question. Options:
   - **(a) Enable billing on one Google AI Studio project.** Embedding everything should cost well under US$1, and there are no daily limits.
   - **(b) Local `bge-m3` via Ollama.** Free, offline, multilingual (Hindi). A 1.2 GB download. On this Intel i7 CPU, embedding about 7000 chunks takes roughly 30–60 minutes once, and each query about 0.2 s.
   - **(c) Stay on the free tier.** About a week until the index is complete.

   My recommendation is **(b)**: it removes quota risk during the demo, and a reindex costs nothing.
2. **Reranker.** `bge-reranker-v2-m3` (a 2.3 GB download, plus PyTorch) on this Intel CPU with no GPU will take several seconds per question for 60 candidates. `bge-reranker-base` (1.1 GB) is about 3× faster. The brief lets me choose. I plan v2-m3 with a 30-candidate cap and will switch to base if p50 latency goes over 3 s.
3. **Ollama fallback model.** Pull `qwen2.5:7b` (about 4.7 GB; slow on CPU, 30–90 s per answer), or use `qwen2.5:3b` (about 2 GB, faster, weaker)? My recommendation is `qwen2.5:3b`.
4. **Architecture change vs `CLAUDE.md`.** The brief replaces the multi-agent graph (router, 4 agents, composer, guard) with a single-knowledge-base linear pipeline. `CLAUDE.md` says "do not swap without asking" for the agents part of the stack, so this brief is taken as your approval. I'll also update `CLAUDE.md` so the two stay consistent.
