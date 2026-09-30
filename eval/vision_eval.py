"""Photo check evaluation: synthetic images (+ any real photos in data/test_images/) -> eval/vision_report.md

    python -u eval/vision_eval.py

Per image: extracted JSON correct? | format check correct? | answer correct + cited? | latency.
Blurry / no-mark / non-product images pass only if handled honestly (no invented numbers).
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BIS_QUIET", "1")
from app.vision import photo_chat  # noqa: E402

SYN = ROOT / "data" / "test_images" / "synthetic"
IS_EXPECTED = {"01": "17803", "02": "12330", "03": "16102", "07": "4151", "09": "17803"}


def norm(x) -> str:
    return re.sub(r"[\s\-–]", "", str(x or "")).upper()


def score(name: str, exp: dict, res: dict) -> dict:
    v, checks, ans = res["vision"], res["format_checks"], res["answer"]
    marks = sorted({m["type"] for m in v["marks"]})
    fields = [k for k in ("cml_number", "r_number", "huid", "purity", "is_number_on_label") if k in exp]
    if exp["kind"] == "blurry":   # honest = every number it reports is the true one (or null)
        truth = {"cml_number": "CM/L-7600012345", "is_number_on_label": "IS 17803"}
        extracted_ok = all(not v.get(k) or norm(v[k]) == norm(truth.get(k, "")) for k in
                           ("cml_number", "r_number", "huid", "purity", "is_number_on_label"))
    else:
        extracted_ok = marks == sorted(exp.get("marks", [])) and all(norm(v.get(k)) == norm(exp[k]) for k in fields)
    got = {c["field"]: c["valid_format"] for c in checks}
    format_ok = all(got.get(k) == want for k, want in exp.get("valid", {}).items())
    if exp["kind"] == "not_product":
        answer_ok = not res["citations"] and "can't see a product" in ans
    elif exp["kind"] == "blurry":
        answer_ok = ans.startswith("**What I see in your photo:**") and not any(
            n in ans for n in ("7600012345",) if not v.get("cml_number"))
    else:
        answer_ok = (ans.startswith("**What I see in your photo:**") and not res["refused"] and bool(res["citations"])
                     and (IS_EXPECTED.get(name[:2], "") in ans)
                     and (not any(v.get(k) for k in ("cml_number", "r_number", "huid")) or "BIS CARE" in ans)
                     and (exp["kind"] != "no_mark" or exp["must_say"] in ans))
    return {"image": name, "marks": ",".join(marks) or "-", "extracted_ok": extracted_ok, "format_ok": format_ok,
            "answer_ok": answer_ok, "cited": len(res["citations"]), "secs": round(res["latency_ms"] / 1000, 1),
            "model": v.get("_model"), "pass": extracted_ok and format_ok and answer_ok}


def main():
    expected = json.loads((SYN / "expected.json").read_text())
    rows, out = [], [f"# Photo check evaluation\n\nGenerated {time.strftime('%Y-%m-%d %H:%M')}.\n"]
    for name, exp in expected.items():
        try:
            res = photo_chat((SYN / name).read_bytes(), name, "", owner="eval-vision", use_cache=False)
            row = score(name, exp, res)
        except Exception as e:
            res, row = {"answer": f"ERROR {type(e).__name__}: {e}", "vision": {}}, {
                "image": name, "marks": "-", "extracted_ok": False, "format_ok": False, "answer_ok": False,
                "cited": 0, "secs": 0, "model": "-", "pass": False}
        rows.append(row)
        out.append(f"## {name}\n`{json.dumps({k: v for k, v in res.get('vision', {}).items() if not k.startswith('_')}, ensure_ascii=False)}`\n\n{res['answer']}\n")
        print(f"{name}: {'PASS' if row['pass'] else 'FAIL'} ({row['secs']} s)", flush=True)
    real = [p for p in (ROOT / "data" / "test_images").iterdir()
            if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".heic")]
    for p in real:  # real photos: no expected answers, so they are shown for a human to judge
        res = photo_chat(p.read_bytes(), p.name, "", owner="eval-vision", use_cache=False)
        out.append(f"## (real photo) {p.name}\n`{json.dumps({k: v for k, v in res['vision'].items() if not k.startswith('_')}, ensure_ascii=False)}`\n\n{res['answer']}\n")
    table = ["| image | marks read | extracted JSON | format check | answer + cited | latency | result |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        yn = lambda b: "yes" if b else "**no**"
        table.append(f"| {r['image']} | {r['marks']} | {yn(r['extracted_ok'])} | {yn(r['format_ok'])} | "
                     f"{yn(r['answer_ok'])} ({r['cited']} sources) | {r['secs']} s | {'PASS' if r['pass'] else 'FAIL'} |")
    passed = sum(r["pass"] for r in rows)
    summary = f"**{passed}/{len(rows)} synthetic images passed** (target 8/10). Real photos tested: {len(real)}.\n"
    out.insert(1, summary + "\n" + "\n".join(table) + "\n")
    (ROOT / "eval" / "vision_report.md").write_text("\n".join(out), encoding="utf-8")
    print("\n" + summary + "\n".join(table))


if __name__ == "__main__":
    main()
