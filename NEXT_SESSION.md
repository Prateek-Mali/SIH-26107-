# Next session (after Task 12, 2026-09-29)

## State
- Chat: `.venv/bin/python ui/chat_cli.py` (agent mode, local memory in `data/memory.sqlite`, resumes the last session).
- No Ollama: embeddings are bge-m3 in-process (`EMBED_PROVIDER=local`, `index/models`, same vectors as before).
  Answers: Gemini (`ANSWER_PROVIDER=gemini`), Groq only as a visible `FALLBACK:`.
- Index: 5103 chunks; vectors for 2123 (every core document); 1985 QCO-PDF chunks + 898 product rows are
  keyword-only. To embed them: `.venv/bin/python scripts/build_index.py` (~0.5 chunk/s on this CPU, ~95 min).
- Tests: 58 pass (`.venv/bin/python -m pytest tests -q`).

## Scores (Task 12, strict grading)
- Test paper (`eval/test_paper.jsonl`, runner `eval/run_test_paper.py`): 66/92 on A1-F5 (46 questions); F6-J4 not
  run (Gemini + Groq free quota ran out). Answers: `eval/test_paper_answers_part1.md`.
- Held-out test, agent: answered 91%, wrong refusal 9%, off-topic refused 100%, citation validity 90%,
  source hit read 74% / cited 65%.
- Chat-feel test (`eval/chat_feel.py`): only 2/10 ran (quota).

## Fixed after Task 12 (not yet re-scored on Gemini: its free quota was used up until ~12:30 IST)
- E3: the citation check now checks every prose sentence separately (two sentences on one line may cite
  different excerpts); the logged E3 answer now survives the check.
- E1: "ISI mark" -> "ISI mark (Standard Mark)" (official term); retrieval follows legal cross-references
  (Section 17 -> Section 29(3) "contravenes section 17 ... punishable").
- D4/D5: the "not covered" line may no longer be the whole answer when an excerpt is relevant; a NOT_COVERED
  reply is retried when the best excerpt scores >= 0.1 (was 0.5; off-topic ~0.0003).
- F5: keyword search maps verbs to the documents' nouns (complain -> complaint, renew -> renewal, ...);
  the complaint page now ranks #2.
- B6: product questions reach the product tools even when the search finds nothing; lookup_product with no
  match returns the cited "voluntary unless notified" rule (cert_overview::0000).
- B1-B3: "which standard" answers also give compulsory + QCO + scheme (B1 verified on Groq: 2/2).

## To do (in this order)
1. With Gemini back: `eval/run_test_paper.py D4 D5 B6 F5 E1 E3 B2 B3 C2 C4`, then F6 F7 G H I J, then
   `eval/chat_feel.py` (25-min cap). C2 on Groq still missed the AIR; check it on Gemini.
2. Recommender: with no product type, "organic honey" matched unrelated de-notified food rows.
3. Done: Ollama leftovers, old multi-agent code and the Streamlit app removed.
