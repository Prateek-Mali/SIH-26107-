"""Standard Recommender + Scheme Selector: the 10 Task-6 cases (live: needs Ollama bge-m3 and the product index).

    pytest tests/test_recommender.py      # pass/fail
    python tests/test_recommender.py      # table: pass/fail, top IS numbers, scheme, latency
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("BIS_QUIET", "1")

import httpx  # noqa: E402
import pytest  # noqa: E402

from app import config  # noqa: E402


def ollama_up() -> bool:
    try:
        return httpx.get(f"{config.OLLAMA_URL}/api/tags", timeout=3).status_code == 200
    except httpx.HTTPError:
        return False


def has(cands, digits):
    return any(digits in c["is_number"].replace(" ", "") for c in cands)


def scheme_keys(s):
    return [r["key"] for r in s["results"]]


CASES = [  # (description, check(candidates, scheme_result) -> bool, what is expected)
    ("Sulphate resisting cement",
     lambda c, s: has(c[:1], "12330") and c[0]["compulsory"] == "yes" and c[0]["qco"]["so_number"] == "S.O. 191(E)"
     and "scheme1" in scheme_keys(s), "IS 12330, compulsory, S.O. 191(E), Scheme I"),
    ("stainless steel water bottle for drinking water",
     lambda c, s: has(c, "17803") and has(c, "17526") and any(x.get("deciding_factor") for x in c),
     "IS 17803 + IS 17526 with a deciding_factor"),
    ("electric geyser for home",
     lambda c, s: any("water heater" in x["product_name"].lower() for x in c[:3]) and c[0]["compulsory"] == "yes"
     and "scheme1" in scheme_keys(s), "water-heater IS, compulsory, Scheme I"),
    ("LED bulb made in China",
     lambda c, s: scheme_keys(s) == ["crs"] and has(c, "16102"), "CRS Scheme II (IS 16102)"),
    ("Mobile phone charger / power adapter",
     lambda c, s: scheme_keys(s) == ["crs"], "CRS Scheme II"),
    ("Gold necklace sold by my shop",
     lambda c, s: scheme_keys(s) == ["hallmarking"], "Hallmarking"),
    ("Steel TMT bars imported from Vietnam",
     lambda c, s: scheme_keys(s) == ["fmcs"] and has(c, "1786") and s["notes"], "FMCS + IS 1786 + importer note"),
    ("Handmade wooden toy",
     lambda c, s: bool(c) and "9873" in c[0]["is_number"] and "toy" in c[0]["product_name"].lower(),
     "toys QCO row (IS 9873) from the data"),
    ("Organic honey",
     lambda c, s: not c and scheme_keys(s) == ["voluntary"], "no QCO -> voluntary"),
    ("IS 1293",
     lambda c, s: has(c[:1], "1293") and "plug" in c[0]["product_name"].lower() and c[0]["compulsory"] == "yes",
     "plug/socket row, compulsory"),
]


def run_case(desc):
    from app.recommender import recommend_standards, select_scheme
    t0 = time.time()
    rec = recommend_standards(desc)
    sch = select_scheme({}, rec["candidates"], desc)
    return rec, sch, time.time() - t0


@pytest.mark.skipif(not ollama_up() or not (config.DATA / "structured" / "product_index.csv").exists(),
                    reason="needs Ollama (bge-m3) and scripts/build_product_index.py")
@pytest.mark.parametrize("desc,check,expected", CASES, ids=[c[0][:30] for c in CASES])
def test_case(desc, check, expected):
    rec, sch, _ = run_case(desc)
    assert check(rec["candidates"], sch), f"expected {expected}; got {[c['is_number'] for c in rec['candidates']]} {scheme_keys(sch)}"


def test_no_invented_is_numbers():
    """Every IS number the recommender returns exists in the product index."""
    import csv
    from app.recommender import INDEX_CSV
    known = {r["is_number"] for r in csv.DictReader(INDEX_CSV.open(encoding="utf-8"))}
    if not ollama_up():
        pytest.skip("needs Ollama")
    rec, _, _ = run_case("stainless steel water bottle for drinking water")
    assert all(c["is_number"] in known for c in rec["candidates"])


if __name__ == "__main__":
    print(f"{'#':>2} {'case':38} {'pass':5} {'top IS numbers':52} {'scheme':22} {'secs':>5}")
    for n, (desc, check, expected) in enumerate(CASES, 1):
        rec, sch, dt = run_case(desc)
        ok = check(rec["candidates"], sch)
        top = ", ".join(dict.fromkeys(c["is_number"] for c in rec["candidates"][:4])) or "(none)"
        schemes = " + ".join(r["key"] for r in sch["results"]) + (" +note" if sch["notes"] else "")
        print(f"{n:>2} {desc[:38]:38} {'PASS' if ok else 'FAIL':5} {top[:52]:52} {schemes:22} {dt:5.1f}", flush=True)
        if not ok:
            print(f"     expected: {expected} | got: " + "; ".join(
                f"{c['is_number']} {c['product_name'][:35]} ({c['compulsory']}, {c['scheme']}, {c['score']}, {c['match_reason'][:40]})"
                for c in rec["candidates"][:5]))
