"""Draw 10 synthetic test photos for the photo check -> data/test_images/synthetic/ (+ expected.json).

    python scripts/make_test_images.py

Made-up numbers in the valid formats, plus 2 deliberately invalid ones (a 7-digit R-number, a 5-character HUID).
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "data" / "test_images" / "synthetic"


def font(size: int):
    for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/Library/Fonts/Arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(title: str, lines: list[str], bg="#f4f1ea"):
    img = Image.new("RGB", (1000, 700), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 980, 680], outline="#333", width=4)
    d.text((60, 50), title, fill="#111", font=font(56))
    for i, t in enumerate(lines):
        d.text((60, 140 + i * 50), t, fill="#222", font=font(34))
    return img, d


def isi_mark(d, x, y, is_no: str, cml: str):
    """ISI-style Standard Mark: IS number above, the ISI monogram box, licence number below."""
    d.text((x + 10, y), is_no, fill="#000", font=font(34))
    d.rectangle([x, y + 50, x + 240, y + 170], outline="#000", width=6)
    d.text((x + 55, y + 70), "ISI", fill="#000", font=font(72))
    d.text((x, y + 185), cml, fill="#000", font=font(34))


def crs_mark(d, x, y, is_no: str, r_no: str):
    """CRS Standard Mark: a box with the IS number and the R-number."""
    d.rounded_rectangle([x, y, x + 330, y + 170], radius=18, outline="#000", width=6)
    d.text((x + 25, y + 20), is_no, fill="#000", font=font(34))
    d.text((x + 25, y + 90), r_no, fill="#000", font=font(40))
    d.text((x, y + 185), "www.crsbis.in", fill="#000", font=font(26))


def hallmark(d, x, y, purity: str, huid: str):
    d.polygon([(x, y + 110), (x + 60, y), (x + 120, y + 110)], outline="#000", width=5)   # BIS logo (triangle)
    d.text((x + 38, y + 50), "BIS", fill="#000", font=font(26))
    d.text((x + 150, y + 30), purity, fill="#000", font=font(56))
    d.text((x + 380, y + 30), huid, fill="#000", font=font(56))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    expected = {}

    img, d = label("AquaSteel Water Bottle", ["Stainless steel potable water bottle", "750 ml, food grade SS 304",
                                              "Made in India"])
    isi_mark(d, 620, 330, "IS 17803", "CM/L-7600012345"); img.save(OUT / "01_isi_bottle.png")
    expected["01_isi_bottle.png"] = {"marks": ["ISI"], "cml_number": "CM/L-7600012345", "is_number_on_label": "IS 17803",
                                     "valid": {"cml_number": True}, "kind": "product"}

    img, d = label("SuperStrong Cement", ["Sulphate Resisting Portland Cement", "50 kg bag", "Batch 2026-09"])
    isi_mark(d, 620, 330, "IS 12330", "CM/L-4100098765"); img.save(OUT / "02_isi_cement.png")
    expected["02_isi_cement.png"] = {"marks": ["ISI"], "cml_number": "CM/L-4100098765", "is_number_on_label": "IS 12330",
                                     "valid": {"cml_number": True}, "kind": "product"}

    img, d = label("BrightLite LED Lamp 9W", ["Self-ballasted LED lamp", "220-240 V AC, B22 base"])
    crs_mark(d, 600, 330, "IS 16102(Part 1)", "R-41012345"); img.save(OUT / "03_crs_led.png")
    expected["03_crs_led.png"] = {"marks": ["CRS"], "r_number": "R-41012345", "valid": {"r_number": True}, "kind": "product"}

    img, d = label("FastCharge USB Adapter", ["Mobile phone charger 5V 2A", "Input 100-240 V"])
    crs_mark(d, 600, 330, "IS 13252(Part 1)", "R-4101234"); img.save(OUT / "04_crs_charger_invalid.png")
    expected["04_crs_charger_invalid.png"] = {"marks": ["CRS"], "r_number": "R-4101234", "valid": {"r_number": False},
                                              "kind": "product"}

    img, d = label("22 Carat Gold Ring", ["Close-up of hallmark on the inner side"], bg="#f6e7b8")
    hallmark(d, 80, 330, "22K916", "AB12C3"); img.save(OUT / "05_gold_hallmark.png")
    expected["05_gold_hallmark.png"] = {"marks": ["HALLMARK"], "huid": "AB12C3", "purity": "22K916",
                                        "valid": {"huid": True, "purity": True}, "kind": "product"}

    img, d = label("Gold Chain 18 Carat", ["Hallmark stamp on the clasp"], bg="#f6e7b8")
    hallmark(d, 80, 330, "18K750", "XY7Q2"); img.save(OUT / "06_gold_invalid_huid.png")
    expected["06_gold_invalid_huid.png"] = {"marks": ["HALLMARK"], "huid": "XY7Q2", "purity": "18K750",
                                            "valid": {"huid": False, "purity": True}, "kind": "product"}

    img, d = label("RoadSafe Helmet", ["Protective helmet for two-wheeler riders", "Size: L (58-60 cm)"])
    isi_mark(d, 620, 330, "IS 4151", "CM/L-8300054321"); img.save(OUT / "07_isi_helmet.png")
    expected["07_isi_helmet.png"] = {"marks": ["ISI"], "cml_number": "CM/L-8300054321", "is_number_on_label": "IS 4151",
                                     "valid": {"cml_number": True}, "kind": "product"}

    img, d = label("AquaSteel Water Bottle", ["Stainless steel potable water bottle", "1 litre"])
    isi_mark(d, 620, 330, "IS 17803", "CM/L-7600012345")
    img.filter(ImageFilter.GaussianBlur(9)).save(OUT / "08_blurry.png")
    expected["08_blurry.png"] = {"kind": "blurry", "no_invented_numbers": True}

    img, d = label("CoolSip Steel Bottle", ["Stainless steel water bottle", "Keep away from fire", "Made in India"])
    img.save(OUT / "09_no_mark_bottle.png")
    expected["09_no_mark_bottle.png"] = {"marks": [], "kind": "no_mark", "must_say": "No ISI mark visible"}

    img = Image.new("RGB", (1000, 700), "#8ecae6")   # a landscape: sky, sun, hills, a tree
    d = ImageDraw.Draw(img)
    d.ellipse([760, 60, 900, 200], fill="#ffb703")
    d.polygon([(0, 520), (300, 300), (620, 520)], fill="#2a9d8f")
    d.polygon([(380, 520), (700, 260), (1000, 520)], fill="#264653")
    d.rectangle([0, 520, 1000, 700], fill="#52b788")
    d.rectangle([150, 430, 175, 560], fill="#6f4518"); d.ellipse([100, 340, 225, 460], fill="#1b4332")
    img.save(OUT / "10_landscape.png")
    expected["10_landscape.png"] = {"kind": "not_product", "marks": []}

    (OUT / "expected.json").write_text(json.dumps(expected, indent=1), encoding="utf-8")
    print(f"{len(expected)} images -> {OUT}")


if __name__ == "__main__":
    main()
