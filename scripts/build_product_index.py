"""Build the product index for the Standard Recommender.

    python scripts/build_product_index.py

data/structured/products_scheme1.csv, products_scheme2.csv, upcoming_qcos.csv
  -> data/structured/product_index.csv
  -> data/structured/product_synonyms.json   (LLM, generated ONCE; cached names are never re-asked)
  -> Qdrant collection "bis_product_index" in index/qdrant_products (bge-m3 of name + synonyms + IS)
"""
import csv
import json
import os
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("BIS_QUIET", "1")

from chunk import find_date  # noqa: E402

from app import config, llm  # noqa: E402

S = ROOT / "data" / "structured"
INDEX_CSV, SYN_JSON = S / "product_index.csv", S / "product_synonyms.json"
QDRANT_PATH, COLLECTION = str(ROOT / "index" / "qdrant_products"), "bis_product_index"
FIELDS = ["product_name", "is_number", "is_title", "scheme", "qco_title", "qco_so_number", "qco_date", "effective_date",
          "status", "category", "source_id", "row_chunk_id", "url", "qco_pdf_url"]


def so_number(text: str) -> str:
    m = re.search(r"\b(S\.?\s*O\.?|G\.?\s*S\.?\s*R\.?)\s*(?:No\.?\s*)?(\d{1,5})\s*\(\s*E\s*\)", text or "", re.I)
    if not m:
        return ""
    kind = "S.O." if m.group(1).upper().replace(".", "").replace(" ", "") == "SO" else "G.S.R."
    return f"{kind} {m.group(2)}(E)"


def build_rows() -> list[dict]:
    rows = []
    for f, scheme, sid in [("products_scheme1", "I", "scheme1_products_table"), ("products_scheme2", "II-CRS", "scheme2_page"),
                           ("upcoming_qcos", None, "upcoming_qcos")]:
        path = S / f"{f}.csv"
        if not path.exists():
            continue
        for i, r in enumerate(csv.DictReader(path.open(encoding="utf-8"))):
            name = (r.get("product") or "").strip()
            if not name:
                continue
            qco = re.sub(r"^\d+\.\s*", "", r.get("qco_title") or "").strip()
            upcoming = f == "upcoming_qcos"
            sch = scheme or ("II-CRS" if re.search(r"electronics|information technology", r.get("ministry_department", ""), re.I) else "I")
            if upcoming:
                status = "upcoming"
            elif re.search(r"withdrawal of|withdrawn", qco, re.I):
                status = "withdrawn"  # the row's latest order withdraws the QCO
            elif re.search(r"de-?notified", r.get("category", ""), re.I):
                status = "de-notified"
            else:
                status = "in_force"
            rows.append({
                "product_name": name, "is_number": (r.get("is_number") or "").strip(),
                "is_title": name,  # the BIS product tables list the product, not the standard's own title
                "scheme": sch, "qco_title": qco, "qco_so_number": so_number(qco), "qco_date": find_date(qco) if qco else "",
                "effective_date": (r.get("enforcement_date") or "").strip(), "status": status,
                "category": (r.get("category") or "").strip(), "source_id": r.get("source_id") or sid,
                "row_chunk_id": f"{r.get('source_id') or sid}::row{i:04d}", "url": r.get("source_url", ""),
                "qco_pdf_url": (r.get("qco_pdf_url") or "").split(" | ")[0]})
    return rows


SYN_PROMPT = """For each BIS product name below, give up to 4 common or plain-words names an Indian buyer, trader or
shopkeeper would use (e.g. "Domestic water heater" -> ["geyser", "electric geyser"]; "High strength deformed steel bars"
-> ["TMT bars", "TMT sariya", "rebar"]). No IS numbers, no brand names. Use [] if there is no common name.
Reply with JSON only: {"<exact product name>": ["...", ...], ...}

"""


def synonyms(names: list[str]) -> dict:
    syn = json.loads(SYN_JSON.read_text(encoding="utf-8")) if SYN_JSON.exists() else {}
    # re-ask names whose cached synonyms are broken (e.g. single characters from a string answer)
    todo = [n for n in dict.fromkeys(names) if n not in syn or any(len(x) < 3 for x in syn[n])]
    for start in range(0, len(todo), 40):
        batch = todo[start:start + 40]
        try:
            text, prov = llm.generate_with_provider(SYN_PROMPT + "\n".join(batch), temperature=0.0, max_tokens=3000,
                                                    model=config.GEMINI_ROUTER_MODEL, groq_model=config.GROQ_SMALL_MODEL)
            got = json.loads(text[text.find("{"): text.rfind("}") + 1])
        except Exception as e:
            print(f"  synonyms batch {start // 40 + 1}: skipped ({type(e).__name__}); re-run later to fill it")
            continue
        for n in batch:
            vals = got.get(n, [])
            if not isinstance(vals, list):  # a string instead of a list would be split into characters
                vals = [vals] if isinstance(vals, str) else []
            clean = []
            for v in vals:
                v = v.strip() if isinstance(v, str) else ""
                if len(v) >= 3 and not re.search(r"\bIS\s*\d", v) and v.lower() not in {c.lower() for c in clean}:
                    clean.append(v)
            syn[n] = clean[:4]
        SYN_JSON.write_text(json.dumps(syn, ensure_ascii=False, indent=1), encoding="utf-8")  # saved per batch
        print(f"  synonyms {min(start + 40, len(todo))}/{len(todo)} via {prov}")
    return syn


def embed_text(r: dict, syn: list[str]) -> str:
    return f"{r['product_name']}. Also called: {', '.join(syn) or '-'}. {r['is_number']}"


def main():
    rows = build_rows()
    with INDEX_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS + ["synonyms"])
        w.writeheader()
        syn = synonyms([r["product_name"] for r in rows])
        for r in rows:
            w.writerow({**r, "synonyms": " | ".join(syn.get(r["product_name"], []))})
    print(f"{len(rows)} products -> {INDEX_CSV.relative_to(ROOT)} "
          f"({sum(1 for r in rows if r['status'] == 'in_force')} in force, {sum(1 for r in rows if r['status'] == 'upcoming')} upcoming, "
          f"{sum(1 for r in rows if r['status'] in ('withdrawn', 'de-notified'))} withdrawn/de-notified)")

    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    texts = [embed_text(r, syn.get(r["product_name"], [])) for r in rows]
    vecs = []
    for start in range(0, len(texts), 32):
        vecs += llm.embed(texts[start:start + 32], task="RETRIEVAL_DOCUMENT")
    client = QdrantClient(path=QDRANT_PATH)
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(COLLECTION, vectors_config=VectorParams(size=len(vecs[0]), distance=Distance.COSINE))
    client.upsert(COLLECTION, points=[
        PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{r['row_chunk_id']}|{r['product_name']}")), vector=v,
                    payload={**r, "synonyms": syn.get(r["product_name"], [])}) for r, v in zip(rows, vecs)])
    print(f"Qdrant '{COLLECTION}': {client.count(COLLECTION).count} products at {QDRANT_PATH}")
    client.close()


if __name__ == "__main__":
    main()
