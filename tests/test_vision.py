"""Photo check without network: format rules, image preparation, answer assembly, API upload (mocked vision)."""
import base64
import io

import pytest
from PIL import Image

from app import memory, vision
from app.vision_check import check, check_cml, check_huid, check_purity, check_r_number


def test_format_rules_come_from_the_documents():
    assert check_huid("AB12C3")["valid_format"] and not check_huid("XY7Q2")["valid_format"]
    assert check_r_number("R-41012345")["valid_format"] and not check_r_number("R-4101234")["valid_format"]
    assert check_r_number("R41012345")["valid_format"]                     # missing dash is normalised
    assert check_cml("CM/L-7600012345")["valid_format"] and not check_cml("7600012345")["valid_format"]
    assert check_purity("22K916")["valid_format"] and not check_purity("22K999")["valid_format"]
    assert all(c["source"] for c in check({"huid": "AB12C3", "r_number": "R-41012345", "cml_number": None,
                                            "purity": "unclear"})) and len(check({"huid": "AB12C3"})) == 1


def png(w=3200, h=2000) -> bytes:
    b = io.BytesIO()
    Image.new("RGB", (w, h), "white").save(b, "PNG")
    return b.getvalue()


def test_prepare_resizes_and_rejects_bad_files():
    data, mime = vision.prepare(png(), "label.png")
    assert mime == "image/jpeg" and max(Image.open(io.BytesIO(data)).size) == 1600
    assert vision.prepare(b"heic-bytes", "photo.HEIC") == (b"heic-bytes", "image/heic")
    with pytest.raises(ValueError, match="jpg, png"):
        vision.prepare(png(), "notes.pdf")
    with pytest.raises(ValueError, match="10 MB"):
        vision.prepare(b"0" * (vision.MAX_BYTES + 1), "big.jpg")


V_BOTTLE = {"product_type": "steel water bottle", "product_description": "stainless steel water bottle",
            "marks": [], "cml_number": None, "r_number": None, "huid": None, "purity": None,
            "is_number_on_label": None, "brand": None, "other_text": None, "image_quality": "good", "notes": None,
            "_model": "fake", "_ms": 1}


@pytest.fixture
def fake(monkeypatch, tmp_path):
    monkeypatch.setattr(memory, "DB", tmp_path / "m.sqlite")
    state = {"v": dict(V_BOTTLE), "asked": []}
    monkeypatch.setattr(vision, "read_image", lambda data, name: dict(state["v"]))
    import app.recommender as R
    monkeypatch.setattr(R, "recommend_standards", lambda d, attrs=None: {"candidates": [
        {"is_number": "IS 17803", "compulsory": "yes", "scheme": "I", "source": {"row_chunk_id": "row::1"}}]})
    monkeypatch.setattr(R, "select_scheme", lambda p, c, t="": {"results": [{"key": "scheme1"}]})

    def chat(q, sid=None, use_cache=True, owner=""):
        state["asked"].append(q)
        return {"answer": "IS 17803 applies [1].\n\n**Sources:**\n[1] list | url", "refused": False,
                "citations": [{"n": 1, "chunk_id": "row::1"}], "session_id": memory.ensure(sid, owner),
                "trace": {"stages": {}}, "latency_ms": 1}
    monkeypatch.setattr(memory, "chat", chat)
    return state


def test_missing_required_mark_is_reported_and_product_remembered(fake):
    r = vision.photo_chat(b"x", "a.jpg", "is this legal?")
    assert r["answer"].startswith("**What I see in your photo:** steel water bottle; no certification mark visible")
    assert "**No ISI mark visible; this product requires one** [1]" in r["answer"]
    assert "Product in my photo: stainless steel water bottle" in fake["asked"][0]
    assert memory.profile(r["session_id"])["product"] == "steel water bottle"
    assert r["answer"].endswith("[1] list | url")                       # sources stay last


def test_numbers_get_format_check_and_bis_care_never_genuine(fake):
    fake["v"].update(marks=[{"type": "ISI", "confidence": 0.9}], cml_number="CM/L-7600012345")
    r = vision.photo_chat(b"x", "a.jpg")
    assert "format looks right" in r["answer"] and "BIS CARE app" in r["answer"]
    assert "genuine" not in r["answer"].replace("does not prove the number is genuine", "")
    assert "The ISI mark this product needs is visible" in r["answer"]


def test_non_product_photo_is_answered_honestly(fake):
    fake["v"].update(product_type=None, product_description="a landscape with hills and a tree")
    r = vision.photo_chat(b"x", "a.jpg")
    assert "can't see a product" in r["answer"] and not r["citations"] and not fake["asked"]


def test_blurry_numbers_are_dropped(monkeypatch):
    class Resp:
        text = ('{"product_type": "bottle", "product_description": "d", "marks": [], "cml_number": "CM/L-7800912345", '
                '"r_number": null, "huid": null, "purity": null, "is_number_on_label": "IS 17763", "brand": null, '
                '"other_text": null, "image_quality": "blurry", "notes": null}')
        model_version = "fake"
    monkeypatch.setattr(vision.llm, "_call", lambda fn, models, rounds=1: Resp())
    monkeypatch.setattr(vision, "vision_model", lambda: "fake")
    v = vision.read_image(png(100, 100), "a.png")
    assert v["cml_number"] is None and v["is_number_on_label"] is None and "too blurry" in v["notes"]


def test_api_accepts_multipart_and_base64(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from app import api
    api.app.dependency_overrides[api.current_user] = lambda: {"email": "a@x.in"}
    seen = []
    monkeypatch.setattr(vision, "photo_chat", lambda data, name, q, sid, owner="": seen.append((len(data), name, q))
                        or {"answer": "ok", "vision": {"marks": []}, "format_checks": []})
    try:
        c = TestClient(api.app)
        r = c.post("/chat", data={"message": "legal?"}, files={"image": ("h.png", png(10, 10), "image/png")})
        assert r.status_code == 200 and r.json()["vision"] == {"marks": []} and seen[-1][1:] == ("h.png", "legal?")
        b64 = base64.b64encode(png(10, 10)).decode()
        assert c.post("/chat", json={"message": "", "image_base64": b64, "image_name": "h.png"}).status_code == 200
        assert c.post("/chat", json={"message": ""}).status_code == 422          # neither text nor photo
        assert c.post("/chat", json={"image_base64": "%%%"}).status_code == 400    # not base64
    finally:
        api.app.dependency_overrides.clear()
