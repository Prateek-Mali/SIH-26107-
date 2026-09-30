# Photo check evaluation

Generated 2026-09-30 22:33.

**9/10 synthetic images passed** (target 8/10). Real photos tested: 0.

| image | marks read | extracted JSON | format check | answer + cited | latency | result |
|---|---|---|---|---|---|---|
| 01_isi_bottle.png | ISI | yes | yes | yes (1 sources) | 47.0 s | PASS |
| 02_isi_cement.png | ISI | yes | yes | yes (2 sources) | 31.4 s | PASS |
| 03_crs_led.png | CRS | yes | yes | yes (2 sources) | 37.1 s | PASS |
| 04_crs_charger_invalid.png | CRS | yes | yes | yes (3 sources) | 67.2 s | PASS |
| 05_gold_hallmark.png | HALLMARK | yes | yes | yes (2 sources) | 63.4 s | PASS |
| 06_gold_invalid_huid.png | HALLMARK | yes | yes | yes (1 sources) | 28.6 s | PASS |
| 07_isi_helmet.png | ISI | yes | yes | yes (2 sources) | 35.5 s | PASS |
| 08_blurry.png | ISI | **no** | yes | yes (1 sources) | 34.6 s | FAIL |
| 09_no_mark_bottle.png | - | yes | yes | yes (2 sources) | 29.6 s | PASS |
| 10_landscape.png | - | yes | yes | yes (0 sources) | 17.5 s | PASS |

## 01_isi_bottle.png
`{"product_type": "stainless steel water bottle", "product_description": "Stainless steel potable water bottle made from food grade SS 304 with 750 ml capacity.", "marks": [{"type": "ISI", "confidence": 0.99}], "cml_number": "CM/L-7600012345", "r_number": null, "huid": null, "purity": null, "is_number_on_label": "IS 17803", "brand": "AquaSteel", "other_text": "AquaSteel Water Bottle Stainless steel potable water bottle 750 ml, food grade SS 304 Made in India IS 17803 ISI CM/L-7600012345", "image_quality": "good", "notes": null}`

**What I see in your photo:** stainless steel water bottle; ISI mark.
Numbers on the label: IS number IS 17803, licence CM/L-7600012345.
- cml number **CM/L-7600012345**: format looks right: CM/L-7600012345 starts with CM/L- and is followed by digits: the licence number is written CM/L-<number>; the documents do not state how many digits it has, so only the CM/L- prefix and digits are checked.

The ISI mark this product needs is visible in the photo.

The Indian Standard IS 17803: 2022 applies, BIS certification is compulsory, and the applicable scheme is Scheme I (ISI mark) [1].

**How to verify:** check CM/L-7600012345 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 17803: 2022: Potable Water Bottles (Copper, Stainless Steel, Aluminum) | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 02_isi_cement.png
`{"product_type": "cement bag", "product_description": "A 50 kg bag of Sulphate Resisting Portland Cement used for construction.", "marks": [{"type": "ISI", "confidence": 1.0}], "cml_number": "CM/L-4100098765", "r_number": null, "huid": null, "purity": null, "is_number_on_label": "IS 12330", "brand": "SuperStrong", "other_text": "SuperStrong Cement Sulphate Resisting Portland Cement 50 kg bag Batch 2026-09", "image_quality": "good", "notes": null}`

**What I see in your photo:** cement bag; ISI mark.
Numbers on the label: IS number IS 12330, licence CM/L-4100098765.
- cml number **CM/L-4100098765**: format looks right: CM/L-4100098765 starts with CM/L- and is followed by digits: the licence number is written CM/L-<number>; the documents do not state how many digits it has, so only the CM/L- prefix and digits are checked.

The ISI mark this product needs is visible in the photo.

The applicable Indian Standard is IS 12330 for Sulphate Resisting Portland Cement, BIS certification is compulsory under the Cement (Quality Control) Order, 2003 (S.O. No. 191(E) Dt. [1] 17 Feb 2003), and it falls under Scheme I (ISI mark) [2].

**How to verify:** check CM/L-4100098765 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 12600: Low heat Portland Cement | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en
[2] Scheme I (ISI mark): products under compulsory certification: IS 12330: Sulphate Resisting Portland Cement | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 03_crs_led.png
`{"product_type": "LED lamp", "product_description": "BrightLite LED Lamp 9W, self-ballasted LED lamp with 220-240 V AC and B22 base.", "marks": [{"type": "CRS", "confidence": 1.0}], "cml_number": null, "r_number": "R-41012345", "huid": null, "purity": null, "is_number_on_label": "IS 16102(Part 1)", "brand": "BrightLite", "other_text": "www.crsbis.in", "image_quality": "good", "notes": null}`

**What I see in your photo:** LED lamp; CRS mark.
Numbers on the label: IS number IS 16102(Part 1), registration R-41012345.
- r number **R-41012345**: format looks right: R-41012345 is R- followed by 8 digits: the CRS licence number is written R-XXXXXXXX (R- followed by 8 characters).

No ISI mark is visible in the photo; see below whether this product requires one.

IS 16102 (Part 1) applies, BIS certification is compulsory, and the applicable scheme is Scheme II (Compulsory Registration Scheme - CRS) [1]. This product is covered under the Electronics and Information Technology Goods (Requirements for Compulsory Registration) Order pursuant to S.O. 2905(E) dated 13 November 2012 [1][2].

**How to verify:** check R-41012345 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 16102(Part 1) | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en
[2] Scheme II (CRS registration) page: IS 16102(Part 1): Self-Ballasted LED Lamps for General Lighting Services | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-ii-registration-scheme/?lang=en

## 04_crs_charger_invalid.png
`{"product_type": "USB adapter", "product_description": "A FastCharge USB Adapter mobile phone charger 5V 2A input 100-240 V.", "marks": [{"type": "CRS", "confidence": 1.0}], "cml_number": null, "r_number": "R-4101234", "huid": null, "purity": null, "is_number_on_label": "IS 13252(Part 1)", "brand": "FastCharge", "other_text": "www.crsbis.in", "image_quality": "good", "notes": null}`

**What I see in your photo:** USB adapter; CRS mark.
Numbers on the label: IS number IS 13252(Part 1), registration R-4101234.
- r number **R-4101234**: format does NOT match: R-4101234 has 7 digits after R-: the CRS licence number is written R-XXXXXXXX (R- followed by 8 characters).

The applicable Indian Standard is IS 13252 (Part 1):2010 (Information Technology Equipment – Safety General Requirements) [1], BIS certification is compulsory under the Electronics and Information Technology Goods (Requirement of Compulsory Registration) Order, 2021 [2], and the scheme is Scheme II (CRS registration) [3].

**How to verify:** check R-4101234 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Bureau of Indian Standards Rules, 1987 (2742): p. 1, dated 2017-08-23 | https://www.bis.gov.in/MandatoryProducts/QCOrder/2742.pdf#page=1
[2] Electronics & IT Goods (Requirement of Compulsory Registration) Order, 2021: 5., p. 6, dated 2021-03-18 | https://www.bis.gov.in/wp-content/uploads/2021/11/Electronics-and-Information-Technology-Goods-Requirement-of-Compulsory-Registration-Order-2021-1.pdf#page=6
[3] Scheme II (CRS registration) page: IS/IEC 62368: Part 1: 2023: Power Adaptors for IT Equipments | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-ii-registration-scheme/?lang=en

## 05_gold_hallmark.png
`{"product_type": "Gold Ring", "product_description": "22 carat gold ring with hallmark on the inner side.", "marks": [{"type": "HALLMARK", "confidence": 1.0}], "cml_number": null, "r_number": null, "huid": "AB12C3", "purity": "22K916", "is_number_on_label": null, "brand": null, "other_text": "22 Carat Gold Ring Close-up of hallmark on the inner side BIS", "image_quality": "good", "notes": null}`

**What I see in your photo:** Gold Ring; HALLMARK mark.
Numbers on the label: HUID AB12C3, purity 22K916.
- huid **AB12C3**: format looks right: AB12C3 has 6 letters/digits: a HUID is a six-digit alphanumeric number, unique for each hallmarked item.
- purity **22K916**: format looks right: 22K916 is a listed grade: gold purity grades are 14K(585), 18K(750), 20K(833), 22K(916), 23K(958) and 24K(995).

The HALLMARK mark this product needs is visible in the photo.

The Indian Standard that applies to gold jewellery and artefacts is IS 1417 ("Gold and Gold Alloys, Jewellery/Artefacts-Fineness and Marking") [1]. Hallmarking is operated under the Hallmarking scheme [2].

**How to verify:** check AB12C3 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] BIS (Hallmarking) Regulations, 2018 (incl. Amdt 1): Schedule-III, p. 68, dated 2018 | https://www.bis.gov.in/wp-content/uploads/2019/02/BIS-Hallmarking-Regulations-2018-Incorp.-Amdt-1.pdf#page=68
[2] Hallmarking FAQ (general): 10. Who operates the Hallmarking Scheme? | https://www.bis.gov.in/hallmarking-overview/hallmarking-faqs/hallmarking-faq/?lang=en

## 06_gold_invalid_huid.png
`{"product_type": "gold chain", "product_description": "A gold chain made of 18 Carat gold used as jewelry.", "marks": [{"type": "HALLMARK", "confidence": 1.0}], "cml_number": null, "r_number": null, "huid": "XY7Q2", "purity": "18K750", "is_number_on_label": null, "brand": null, "other_text": "Gold Chain 18 Carat Hallmark stamp on the clasp BIS", "image_quality": "good", "notes": null}`

**What I see in your photo:** gold chain; HALLMARK mark.
Numbers on the label: HUID XY7Q2, purity 18K750.
- huid **XY7Q2**: format does NOT match: XY7Q2 has 5 characters or other symbols: a HUID is a six-digit alphanumeric number, unique for each hallmarked item.
- purity **18K750**: format looks right: 18K750 is a listed grade: gold purity grades are 14K(585), 18K(750), 20K(833), 22K(916), 23K(958) and 24K(995).

The HALLMARK mark this product needs is visible in the photo.

The applicable Indian Standard is IS 1417 (“Gold and gold Alloys, Jewellery/Artefacts- Fineness and marking”), BIS certification/registration is compulsory, and the applicable scheme is the Hallmarking Scheme [1].

**How to verify:** check XY7Q2 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Hallmarking overview: Hallmarking overview | https://www.bis.gov.in/hallmarking-overview/?lang=en

## 07_isi_helmet.png
`{"product_type": "protective helmet for two-wheeler riders", "product_description": "A protective helmet for two-wheeler riders, size L.", "marks": [{"type": "ISI", "confidence": 1.0}], "cml_number": "CM/L-8300054321", "r_number": null, "huid": null, "purity": null, "is_number_on_label": "IS 4151", "brand": "RoadSafe", "other_text": "RoadSafe Helmet Size: L (58-60 cm)", "image_quality": "good", "notes": null}`

**What I see in your photo:** protective helmet for two-wheeler riders; ISI mark.
Numbers on the label: IS number IS 4151, licence CM/L-8300054321.
- cml number **CM/L-8300054321**: format looks right: CM/L-8300054321 starts with CM/L- and is followed by digits: the licence number is written CM/L-<number>; the documents do not state how many digits it has, so only the CM/L- prefix and digits are checked.

The ISI mark this product needs is visible in the photo.

The applicable Indian Standard is IS 4151: 2015, BIS certification is compulsory under Scheme I (ISI mark), and it is governed by the Helmet for riders of Two Wheeler Motor Vehicles (Quality Control) Order, 2020 (S.O. No. 4252 (E) dated 26/11/2020) [1][2].

**How to verify:** check CM/L-8300054321 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 4151: 2015: Helmet for riders of Two Wheeler Motor Vehicles | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en
[2] Scheme I (ISI mark): products under compulsory certification: IS 4151: 2015 | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 08_blurry.png
`{"product_type": "stainless steel water bottle", "product_description": "An AquaSteel stainless steel portable water bottle with 1 litre capacity, bearing an ISI certification mark.", "marks": [{"type": "ISI", "confidence": 0.95}], "cml_number": "7800912345", "r_number": null, "huid": null, "purity": null, "is_number_on_label": "17763", "brand": "AquaSteel", "other_text": "AquaSteel Water Bottle Stainless steel portable water bottle 1 litre", "image_quality": "blurry", "notes": "The image is blurry but readable."}`

**What I see in your photo:** stainless steel water bottle; ISI mark.
Numbers on the label: IS number 17763, licence 7800912345.
- cml number **7800912345**: format does NOT match: 7800912345 is not CM/L- followed by digits: the licence number is written CM/L-<number>; the documents do not state how many digits it has, so only the CM/L- prefix and digits are checked.
(Photo blurry: The image is blurry but readable.. I do not guess numbers I cannot read clearly.)

The ISI mark this product needs is visible in the photo.

The Indian Standard that applies to stainless steel portable water bottles is IS 17803: 2022 (Potable Water Bottles (Copper, Stainless Steel, Aluminum)), BIS certification is compulsory under Scheme I (ISI mark), and it is governed by the Potable Water Bottles (Quality Control) Order, 2023 (S.O. 2988(E), dated 5th July 2023) along with subsequent amendments [1].

**How to verify:** check 7800912345 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 17803: 2022: Potable Water Bottles (Copper, Stainless Steel, Aluminum) | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 09_no_mark_bottle.png
`{"product_type": "stainless steel water bottle", "product_description": "A stainless steel water bottle labeled CoolSip Steel Bottle with instructions to keep away from fire and that it is made in India.", "marks": [], "cml_number": null, "r_number": null, "huid": null, "purity": null, "is_number_on_label": null, "brand": "CoolSip", "other_text": "CoolSip Steel Bottle Stainless steel water bottle Keep away from fire Made in India", "image_quality": "good", "notes": "No certification marks or standard numbers are present on the label."}`

**What I see in your photo:** stainless steel water bottle; no certification mark visible.
(Photo good: No certification marks or standard numbers are present on the label.. I do not guess numbers I cannot read clearly.)

**No ISI mark visible; this product requires one** [2].

| Indian Standard (IS No.) | Title | When it applies | Compulsory? |
| --- | --- | --- | --- |
| IS 17526 : 2021 | Domestic Stainless steel vacuum flask/bottle | For domestic stainless steel vacuum flasks/bottles under Scheme I (ISI mark) [1]. | Yes, under the Insulated Flask, Bottles and Containers for Domestic Use (Quality Control) Orders [1]. |
| IS 17803: 2022 | Potable Water Bottles (Copper, Stainless Steel, Aluminum) | For potable water bottles (metallic) under Scheme I (ISI mark) [2]. | Yes, under the Potable Water Bottles (Quality Control) Orders [2]. |

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 17526 : 2021: Domestic Stainless steel vacuum flask/bottle | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en
[2] Scheme I (ISI mark): products under compulsory certification: IS 17803: 2022: Potable Water Bottles (Copper, Stainless Steel, Aluminum) | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 10_landscape.png
`{"product_type": null, "product_description": "A flat graphic illustration of a landscape with mountains, a tree, green ground, and a sun against a blue sky.", "marks": [], "cml_number": null, "r_number": null, "huid": null, "purity": null, "is_number_on_label": null, "brand": null, "other_text": null, "image_quality": "good", "notes": "The image is an illustration and does not show any product or BIS mark."}`

**What I see in your photo:** A flat graphic illustration of a landscape with mountains, a tree, green ground, and a sun against a blue sky.. I can't see a product or a BIS mark, so there is nothing to check. Send a photo of the product and its label or mark.
