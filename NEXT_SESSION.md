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

## To do (in this order)
1. Wrong refusals: D4 timelines, D5 objections (worked in Task 9: regression, likely the new short-answer
   prompt), B6 organic honey (should say voluntary, no QCO), F5 fake ISI complaint.
2. Citation check removes everything on long BIS Act answers: E1 penalty, E3 "what is the BIS Act".
3. Too-short product answers: "which standard" must also give compulsory + QCO + scheme (B1-B3), C2 AIR role,
   C4 "only the foreign manufacturer can register".
4. Re-run: `eval/run_test_paper.py F6 F7 G H I J`, `eval/chat_feel.py`, then the full paper once (25-min cap).
5. `scripts/embedding_map.py` search box still calls Ollama in the browser; update or drop it.
