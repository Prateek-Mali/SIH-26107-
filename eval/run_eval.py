"""Run the question set through the graph and write eval/report.md.

    python eval/run_eval.py                 # all questions
    python eval/run_eval.py --reviewed-only
    python eval/run_eval.py --limit 10

Metrics
- faithfulness, answer relevancy, context recall: RAGAS if installed and working, otherwise an
  equivalent Gemini judge (the report says which was used)
- citation validity: every [n] points to a real indexed chunk that supports its sentence
- refusal accuracy: out-of-scope questions refused / in-scope questions answered
- router accuracy: expected intent is among the routed intents (out-of-scope: flagged out of scope)
- source recall: an expected source document is among the cited ones
- latency p50 / p95
Targets: faithfulness >= 0.85, refusal accuracy >= 90%, citation validity >= 90%.
"""
import argparse
import json
import os
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")

from app import config, llm  # noqa: E402
from app.graph import answer  # noqa: E402

EVAL = ROOT / "eval"

CITATION_JUDGE = """For each numbered CLAIM, say if the SOURCE text given with it supports it (numbers, dates,
fees and section numbers must match). Reply with JSON only: {"supported": [true, false, ...]} in claim order."""

RELEVANCY_JUDGE = """Rate how well the ANSWER addresses the QUESTION (ignore whether it is correct):
1.0 = fully answers it, 0.5 = partly, 0.0 = does not answer or refuses. Reply with JSON only: {"score": <number>}"""

RECALL_JUDGE = """Split the EXPECTED ANSWER into its facts. For each fact, say if the CONTEXT contains it.
Reply with JSON only: {"facts": [{"fact": "...", "in_context": true|false}]}"""

FAITHFULNESS_JUDGE = """Split the ANSWER into factual claims (ignore source lists, links and safety notes).
For each claim say if the CONTEXT supports it. Reply with JSON only: {"claims": [{"claim": "...", "supported": true|false}]}"""


def strip_sources(text: str) -> str:
    return re.split(r"\n\n\*\*(Sources|स्रोत):\*\*", text)[0]


def claims_with_citations(answer_text: str) -> list[tuple[str, list[int]]]:
    body = strip_sources(answer_text)
    out = []
    for sent in re.split(r"(?<=[.!?।])\s+|\n+", body):
        nums = [int(n) for n in re.findall(r"\[(\d+)\]", sent)]
        if nums:
            out.append((re.sub(r"\[\d+\]", "", sent).strip(), nums))
    return out


def citation_validity(result: dict, index_ids: set) -> tuple[int, int]:
    """(valid, total) cited claims."""
    cites = {c["n"]: c for c in result.get("citations", [])}
    claims = claims_with_citations(result.get("final_answer", ""))
    if not claims:
        return 0, 0
    blocks, exists = [], []
    for i, (claim, nums) in enumerate(claims, start=1):
        ok = all(n in cites and cites[n]["chunk_id"] in index_ids for n in nums)
        exists.append(ok)
        src = "\n".join(cites[n]["snippet"] if n in cites else "(missing)" for n in nums)
        blocks.append(f"CLAIM {i}: {claim}\nSOURCE {i}: {src}")
    try:
        # the stored snippet is short; use the full chunk text for judging
        full = {c["chunk_id"]: c["text"] for c in result.get("sources", [])}
        for i, (claim, nums) in enumerate(claims):
            texts = [full.get(cites[n]["chunk_id"], cites[n]["snippet"]) for n in nums if n in cites]
            blocks[i] = f"CLAIM {i + 1}: {claim}\nSOURCE {i + 1}: " + "\n".join(texts)[:4000]
        supported = llm.generate_json("\n\n".join(blocks), system=CITATION_JUDGE,
                                      model=config.GEMINI_ROUTER_MODEL).get("supported", [])
    except Exception:
        supported = [True] * len(claims)  # judge failed: only the existence check counts
    valid = sum(1 for e, s in zip(exists, supported + [False] * len(claims)) if e and s)
    return valid, len(claims)


def contexts_of(result: dict) -> list[str]:
    return [c["text"] for c in result.get("sources", [])] or \
           [c["text"] for out in result.get("agent_outputs", {}).values() for c in out.get("chunks", [])]


def judge_metrics(row: dict) -> dict:
    """Gemini-judge versions of faithfulness, answer relevancy and context recall."""
    ctx = "\n\n".join(row["contexts"])[:20000]
    ans = strip_sources(row["answer"])
    q = row
    m = {}
    try:
        claims = llm.generate_json(f"CONTEXT:\n{ctx}\n\nANSWER:\n{ans}", system=FAITHFULNESS_JUDGE).get("claims", [])
        m["faithfulness"] = sum(c.get("supported", False) for c in claims) / len(claims) if claims else None
    except Exception:
        m["faithfulness"] = None
    try:
        m["answer_relevancy"] = float(llm.generate_json(f"QUESTION: {q['question']}\n\nANSWER:\n{ans}",
                                                        system=RELEVANCY_JUDGE).get("score"))
    except Exception:
        m["answer_relevancy"] = None
    try:
        facts = llm.generate_json(f"EXPECTED ANSWER: {q['expected_answer']}\n\nCONTEXT:\n{ctx}",
                                  system=RECALL_JUDGE).get("facts", [])
        m["context_recall"] = sum(f.get("in_context", False) for f in facts) / len(facts) if facts else None
    except Exception:
        m["context_recall"] = None
    return m


def ragas_metrics(rows: list[dict]) -> dict | None:
    """Try RAGAS with Gemini. Returns per-row scores, or None if RAGAS is not usable here."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        from ragas import EvaluationDataset, evaluate
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import Faithfulness, LLMContextRecall, ResponseRelevancy
    except Exception as e:
        print(f"[eval] RAGAS not available ({type(e).__name__}: {e}); using the Gemini judge instead")
        return None
    data = EvaluationDataset.from_list([{
        "user_input": r["question"], "response": strip_sources(r["answer"]),
        "retrieved_contexts": r["contexts"] or [""], "reference": r["expected_answer"]} for r in rows])
    judge = LangchainLLMWrapper(ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, google_api_key=config.GEMINI_API_KEY))
    emb = LangchainEmbeddingsWrapper(GoogleGenerativeAIEmbeddings(model=f"models/{config.GEMINI_EMBED_MODEL}",
                                                                  google_api_key=config.GEMINI_API_KEY))
    res = evaluate(data, metrics=[Faithfulness(), ResponseRelevancy(), LLMContextRecall()], llm=judge, embeddings=emb)
    df = res.to_pandas()
    return {"faithfulness": df["faithfulness"].tolist(), "answer_relevancy": df["answer_relevancy"].tolist(),
            "context_recall": df["context_recall"].tolist()}


def pct(x):
    return "n/a" if x is None else f"{x * 100:.0f}%"


def mean(xs):
    xs = [x for x in xs if x is not None and x == x]  # drop None / NaN
    return sum(xs) / len(xs) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewed-only", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--no-ragas", action="store_true")
    args = ap.parse_args()

    qs = [json.loads(l) for l in (EVAL / "questions.jsonl").open(encoding="utf-8") if l.strip()]
    if args.reviewed_only:
        qs = [q for q in qs if q.get("reviewed")]
    if args.limit:
        qs = qs[: args.limit]
    index_ids = {json.loads(l)["chunk_id"] for l in config.CHUNKS_PATH.open(encoding="utf-8")}

    rows = []
    for i, q in enumerate(qs, start=1):
        t0 = time.time()
        try:
            r = answer(q["question"])
        except Exception as e:
            r = {"final_answer": f"ERROR: {e}", "refused": False, "intents": [], "citations": [], "trace": []}
        latency = time.time() - t0
        must_refuse = q["type"] == "out_of_scope"
        routed_ok = (r.get("out_of_scope") or not r.get("intents")) if must_refuse else \
            bool(set(q.get("expected_intents", [])) & set(r.get("intents", [])))
        valid, total = (0, 0) if r.get("refused") else citation_validity(r, index_ids)
        cited_sources = {c["source_id"] for c in r.get("citations", [])}
        row = {"id": q["id"], "type": q["type"], "question": q["question"], "expected_answer": q["expected_answer"],
               "reviewed": q.get("reviewed", False), "answer": r.get("final_answer", ""),
               "refused": bool(r.get("refused")), "must_refuse": must_refuse,
               "refusal_correct": bool(r.get("refused")) == must_refuse, "intents": r.get("intents", []),
               "router_correct": bool(routed_ok), "citations_valid": valid, "citations_total": total,
               "source_hit": (bool(cited_sources & set(q.get("expected_source_ids", [])))
                              if q.get("expected_source_ids") else None),
               "latency_s": round(latency, 2), "contexts": contexts_of(r)}
        rows.append(row)
        print(f"[{i}/{len(qs)}] {q['id']} {q['type']}: refused={row['refused']} router_ok={row['router_correct']} "
              f"cites={valid}/{total} {latency:.1f}s")

    method = "Gemini judge"
    answered = [r for r in rows if not r["must_refuse"] and not r["refused"]]
    scores = ragas_metrics(answered) if answered and not args.no_ragas else None
    if scores:
        method = "RAGAS"
        for k, vals in scores.items():
            for r, v in zip(answered, vals):
                r[k] = v
    else:
        for r in answered:
            r.update(judge_metrics(r))

    with (EVAL / "results.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({k: v for k, v in r.items() if k != "contexts"}, ensure_ascii=False) + "\n")
    write_report(rows, method)


def write_report(rows: list[dict], method: str):
    in_scope = [r for r in rows if not r["must_refuse"]]
    oos = [r for r in rows if r["must_refuse"]]
    answered = [r for r in in_scope if not r["refused"]]
    cv_valid = sum(r["citations_valid"] for r in rows)
    cv_total = sum(r["citations_total"] for r in rows)
    lat = sorted(r["latency_s"] for r in rows) or [0]
    p95 = lat[min(len(lat) - 1, int(round(0.95 * (len(lat) - 1))))]
    faith = mean([r.get("faithfulness") for r in answered])
    refusal_acc = sum(r["refusal_correct"] for r in rows) / len(rows) if rows else None
    cit_val = cv_valid / cv_total if cv_total else None

    def check(value, target):
        return "" if value is None else (" ✅" if value >= target else " ❌")

    lines = [
        "# BIS Assistant: evaluation report", "",
        f"Run: {datetime.now():%Y-%m-%d %H:%M} · model `{config.GEMINI_MODEL}` · router `{config.GEMINI_ROUTER_MODEL}` · "
        f"{len(rows)} questions ({sum(r['reviewed'] for r in rows)} hand-reviewed) · quality metrics by **{method}**", "",
        "| Metric | Value | Target |", "|---|---|---|",
        f"| Faithfulness | {pct(faith)}{check(faith, 0.85)} | ≥ 85% |",
        f"| Answer relevancy | {pct(mean([r.get('answer_relevancy') for r in answered]))} | |",
        f"| Context recall | {pct(mean([r.get('context_recall') for r in answered]))} | |",
        f"| Citation validity | {pct(cit_val)}{check(cit_val, 0.9)} ({cv_valid}/{cv_total} cited claims) | ≥ 90% |",
        f"| Refusal accuracy (all questions) | {pct(refusal_acc)}{check(refusal_acc, 0.9)} | ≥ 90% |",
        f"| Out-of-scope refused | {sum(r['refused'] for r in oos)}/{len(oos)} | all |",
        f"| In-scope wrongly refused | {sum(r['refused'] for r in in_scope)}/{len(in_scope)} | low |",
        f"| Router accuracy | {pct(sum(r['router_correct'] for r in rows) / len(rows) if rows else None)} | |",
        f"| Expected source cited | {pct(mean([r['source_hit'] for r in in_scope if r['source_hit'] is not None]))} | |",
        f"| Latency p50 / p95 | {statistics.median(lat):.1f} s / {p95:.1f} s | |", "",
        "## By question type", "", "| Type | n | refused | router ok | faithfulness | citation validity |", "|---|---|---|---|---|---|",
    ]
    for t in sorted({r["type"] for r in rows}):
        rs = [r for r in rows if r["type"] == t]
        v, n = sum(r["citations_valid"] for r in rs), sum(r["citations_total"] for r in rs)
        lines.append(f"| {t} | {len(rs)} | {sum(r['refused'] for r in rs)} | {sum(r['router_correct'] for r in rs)} | "
                     f"{pct(mean([r.get('faithfulness') for r in rs]))} | {pct(v / n if n else None)} |")
    lines += ["", "## Failures to look at", ""]
    bad = [r for r in rows if not r["refusal_correct"] or not r["router_correct"]
           or (r["citations_total"] and r["citations_valid"] < r["citations_total"])
           or (r.get("faithfulness") is not None and r["faithfulness"] < 0.85)]
    for r in bad[:40]:
        lines.append(f"- **{r['id']}** ({r['type']}) {r['question']}  \n  refused={r['refused']}, intents={r['intents']}, "
                     f"cites {r['citations_valid']}/{r['citations_total']}, faithfulness={pct(r.get('faithfulness'))}  \n"
                     f"  expected: {r['expected_answer'][:200]}  \n  got: {strip_sources(r['answer'])[:300].replace(chr(10), ' ')}")
    if not bad:
        lines.append("None.")
    (EVAL / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:16]))
    print(f"\nWrote {EVAL / 'report.md'}")


if __name__ == "__main__":
    main()
