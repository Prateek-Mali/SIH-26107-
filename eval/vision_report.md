# Photo check evaluation

Generated 2026-09-30 23:12.

**10/10 synthetic images passed** (target 8/10). Real photos tested: 0.

| image | marks read | extracted JSON | format check | answer + cited | latency | result |
|---|---|---|---|---|---|---|
| 01_isi_bottle.png | ISI | yes | yes | yes (1 sources) | 23.3 s | PASS |
| 02_isi_cement.png | ISI | yes | yes | yes (1 sources) | 13.0 s | PASS |
| 03_crs_led.png | CRS | yes | yes | yes (1 sources) | 13.1 s | PASS |
| 04_crs_charger_invalid.png | CRS | yes | yes | yes (3 sources) | 13.1 s | PASS |
| 05_gold_hallmark.png | HALLMARK | yes | yes | yes (3 sources) | 10.6 s | PASS |
| 06_gold_invalid_huid.png | HALLMARK | yes | yes | yes (3 sources) | 11.4 s | PASS |
| 07_isi_helmet.png | ISI | yes | yes | yes (1 sources) | 14.3 s | PASS |
| 08_blurry.png | ISI | yes | yes | yes (1 sources) | 14.1 s | PASS |
| 09_no_mark_bottle.png | - | yes | yes | yes (1 sources) | 11.9 s | PASS |
| 10_landscape.png | - | yes | yes | yes (0 sources) | 1.6 s | PASS |

## 01_isi_bottle.png
`{"product_type": "stainless steel water bottle", "product_description": "An AquaSteel stainless steel potable water bottle of 750 ml capacity made of food grade SS 304.", "marks": [{"type": "ISI", "confidence": 1.0}], "cml_number": "CM/L-7600012345", "r_number": null, "huid": null, "purity": null, "is_number_on_label": "IS 17803", "brand": "AquaSteel", "other_text": "750 ml, food grade SS 304, Made in India", "image_quality": "good", "notes": null}`

**What I see in your photo:** stainless steel water bottle; ISI mark.
Numbers on the label: IS number IS 17803, licence CM/L-7600012345.
- cml number **CM/L-7600012345**: format looks right: CM/L-7600012345 starts with CM/L- and is followed by digits: the licence number is written CM/L-<number>; the documents do not state how many digits it has, so only the CM/L- prefix and digits are checked.

The ISI mark this product needs is visible in the photo.

The applicable Indian Standard is IS 17803: 2022 for Potable Water Bottles (Copper, Stainless Steel, Aluminum), BIS certification is compulsory, and it falls under Scheme I (ISI mark) [1].

**How to verify:** check CM/L-7600012345 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 17803: 2022: Potable Water Bottles (Copper, Stainless Steel, Aluminum) | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 02_isi_cement.png
`{"product_type": "cement bag", "product_description": "SuperStrong Cement Sulphate Resisting Portland Cement in a 50 kg bag.", "marks": [{"type": "ISI", "confidence": 1.0}], "cml_number": "CM/L-4100098765", "r_number": null, "huid": null, "purity": null, "is_number_on_label": "IS 12330", "brand": "SuperStrong Cement", "other_text": "Sulphate Resisting Portland Cement 50 kg bag Batch 2026-09", "image_quality": "good", "notes": null}`

**What I see in your photo:** cement bag; ISI mark.
Numbers on the label: IS number IS 12330, licence CM/L-4100098765.
- cml number **CM/L-4100098765**: format looks right: CM/L-4100098765 starts with CM/L- and is followed by digits: the licence number is written CM/L-<number>; the documents do not state how many digits it has, so only the CM/L- prefix and digits are checked.

The ISI mark this product needs is visible in the photo.

IS 12330 applies to Sulphate Resisting Portland Cement, BIS certification is compulsory, and it comes under Scheme I (ISI mark) [1].

**How to verify:** check CM/L-4100098765 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 12330: Sulphate Resisting Portland Cement | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 03_crs_led.png
`{"product_type": "LED lamp", "product_description": "BrightLite LED Lamp 9W, self-ballasted LED lamp for general lighting use.", "marks": [{"type": "CRS", "confidence": 1.0}], "cml_number": null, "r_number": "R-41012345", "huid": null, "purity": null, "is_number_on_label": "IS 16102(Part 1)", "brand": "BrightLite", "other_text": "Self-ballasted LED lamp 220-240 V AC, B22 base www.crsbis.in", "image_quality": "good", "notes": null}`

**What I see in your photo:** LED lamp; CRS mark.
Numbers on the label: IS number IS 16102(Part 1), registration R-41012345.
- r number **R-41012345**: format looks right: R-41012345 is R- followed by 8 digits: the CRS licence number is written R-XXXXXXXX (R- followed by 8 characters).

The CRS mark this product needs is visible in the photo.

IS 16102(Part 1) applies, BIS certification is compulsory under Scheme II (Compulsory Registration Scheme), governed by the Electronics & Information Technology Goods (Requirements for Compulsory Registration) Order, 2012 (Notification No. S.O. 2905(E) dated 13th November 2012) [1].

**How to verify:** check R-41012345 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme II (CRS registration) page: IS 16102(Part 1): Self-Ballasted LED Lamps for General Lighting Services | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-ii-registration-scheme/?lang=en

## 04_crs_charger_invalid.png
`{"product_type": "USB Adapter", "product_description": "FastCharge USB Adapter mobile phone charger 5V 2A with input 100-240 V.", "marks": [{"type": "CRS", "confidence": 0.99}], "cml_number": null, "r_number": "R-4101234", "huid": null, "purity": null, "is_number_on_label": "IS 13252(Part 1)", "brand": "FastCharge", "other_text": "www.crsbis.in", "image_quality": "good", "notes": null}`

**What I see in your photo:** USB Adapter; CRS mark.
Numbers on the label: IS number IS 13252(Part 1), registration R-4101234.
- r number **R-4101234**: format does NOT match: R-4101234 has 7 digits after R-: the CRS licence number is written R-XXXXXXXX (R- followed by 8 characters).

The CRS mark this product needs is visible in the photo.

IS 13252 (Part 1) applies, BIS certification is compulsory under Scheme II (CRS registration), governed by the Electronics and Information Technology Goods (Requirement of Compulsory Registration) Order, 2021 [1][2][3].

**How to verify:** check R-4101234 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme II (CRS registration) page: IS/IEC 62368: Part 1: 2023: Power Adaptors for IT Equipments | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-ii-registration-scheme/?lang=en
[2] Scheme II (CRS registration) page: IS 302 (Part 1): 2008: Adapters for household and similar electrical appliances | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-ii-registration-scheme/?lang=en
[3] Electronics & IT Goods (Requirement of Compulsory Registration) Order, 2021: 5., p. 6, dated 2021-03-18 | https://www.bis.gov.in/wp-content/uploads/2021/11/Electronics-and-Information-Technology-Goods-Requirement-of-Compulsory-Registration-Order-2021-1.pdf#page=6

## 05_gold_hallmark.png
`{"product_type": "gold ring", "product_description": "22 Carat gold ring shown with its hallmark details.", "marks": [{"type": "HALLMARK", "confidence": 1.0}], "cml_number": null, "r_number": null, "huid": "AB12C3", "purity": "22K916", "is_number_on_label": null, "brand": null, "other_text": "22 Carat Gold Ring Close-up of hallmark on the inner side BIS", "image_quality": "good", "notes": "The image shows a 22 carat gold ring hallmark containing the BIS logo, purity 22K916, and HUID AB12C3."}`

**What I see in your photo:** gold ring; HALLMARK mark.
Numbers on the label: HUID AB12C3, purity 22K916.
- huid **AB12C3**: format looks right: AB12C3 has 6 letters/digits: a HUID is a six-digit alphanumeric number, unique for each hallmarked item.
- purity **22K916**: format looks right: 22K916 is a listed grade: gold purity grades are 14K(585), 18K(750), 20K(833), 22K(916), 23K(958) and 24K(995).
(Photo good: The image shows a 22 carat gold ring hallmark containing the BIS logo, purity 22K916, and HUID AB12C3. I do not guess numbers I cannot read clearly.)

The HALLMARK mark this product needs is visible in the photo.

| IS no. | Title | When it applies | Compulsory |
|---|---|---|---|
| IS 1417 | Gold and gold Alloys, Jewellery/Artefacts- Fineness and marking | Gold jewellery and artefacts [1] | Yes, under the Mandatory Hallmarking Order [2] |

Scheme: Hallmarking [3].

**How to verify:** check AB12C3 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] BIS (Hallmarking) Regulations, 2018 (incl. Amdt 1): Schedule-III, p. 68, dated 2018 | https://www.bis.gov.in/wp-content/uploads/2019/02/BIS-Hallmarking-Regulations-2018-Incorp.-Amdt-1.pdf#page=68
[2] Mandatory Hallmarking Order page: Mandatory Hallmarking Order | https://www.bis.gov.in/hallmarking-overview/mandatory-hallmarking-order/?lang=en
[3] Hallmarking FAQ (general): BIS Act and Regulation: BIS Act and Regulation | https://www.bis.gov.in/hallmarking-overview/hallmarking-faqs/bis-act-and-regulation-faq/?lang=en

## 06_gold_invalid_huid.png
`{"product_type": "Gold Chain", "product_description": "An 18 carat gold chain with a hallmark stamp on the clasp.", "marks": [{"type": "HALLMARK", "confidence": 1.0}], "cml_number": null, "r_number": null, "huid": "XY7Q2", "purity": "18K750", "is_number_on_label": null, "brand": null, "other_text": "Gold Chain 18 Carat Hallmark stamp on the clasp BIS", "image_quality": "good", "notes": null}`

**What I see in your photo:** Gold Chain; HALLMARK mark.
Numbers on the label: HUID XY7Q2, purity 18K750.
- huid **XY7Q2**: format does NOT match: XY7Q2 has 5 characters or other symbols: a HUID is a six-digit alphanumeric number, unique for each hallmarked item.
- purity **18K750**: format looks right: 18K750 is a listed grade: gold purity grades are 14K(585), 18K(750), 20K(833), 22K(916), 23K(958) and 24K(995).

The HALLMARK mark this product needs is visible in the photo.

IS 1417 applies to gold and gold alloys, jewellery and artefacts [1]. BIS hallmarking is compulsory under the Mandatory Hallmarking Order [2], operated under the Hallmarking scheme [3].

**How to verify:** check XY7Q2 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] BIS (Hallmarking) Regulations, 2018 (incl. Amdt 1): Schedule-III, p. 68, dated 2018 | https://www.bis.gov.in/wp-content/uploads/2019/02/BIS-Hallmarking-Regulations-2018-Incorp.-Amdt-1.pdf#page=68
[2] Hallmarking overview: Hallmarking overview | https://www.bis.gov.in/hallmarking-overview/?lang=en
[3] Hallmarking FAQ (general): 8. What is HUID in the hallmarked gold jewellery? | https://www.bis.gov.in/hallmarking-overview/hallmarking-faqs/hallmarking-faq/?lang=en

## 07_isi_helmet.png
`{"product_type": "protective helmet", "product_description": "Protective helmet for two-wheeler riders used for head safety.", "marks": [{"type": "ISI", "confidence": 1.0}], "cml_number": "CM/L-8300054321", "r_number": null, "huid": null, "purity": null, "is_number_on_label": "IS 4151", "brand": "RoadSafe", "other_text": "RoadSafe Helmet, Protective helmet for two-wheeler riders, Size: L (58-60 cm)", "image_quality": "good", "notes": null}`

**What I see in your photo:** protective helmet; ISI mark.
Numbers on the label: IS number IS 4151, licence CM/L-8300054321.
- cml number **CM/L-8300054321**: format looks right: CM/L-8300054321 starts with CM/L- and is followed by digits: the licence number is written CM/L-<number>; the documents do not state how many digits it has, so only the CM/L- prefix and digits are checked.

The ISI mark this product needs is visible in the photo.

The applicable Indian Standard is IS 4151: 2015 for Helmet for riders of Two Wheeler Motor Vehicles, BIS certification is compulsory under Scheme I (ISI mark), and it is governed by the Helmet for riders of Two Wheeler Motor Vehicles (Quality Control) Order, 2020 (S.O. No. 4252 (E) dated 26/11/2020) [1].

**How to verify:** check CM/L-8300054321 in the BIS CARE app (https://play.google.com/store/apps/details?id=com.bis.bisapp). A correct format does not prove the number is genuine; only BIS CARE can confirm it.

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 4151: 2015: Helmet for riders of Two Wheeler Motor Vehicles | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 08_blurry.png
`{"product_type": "stainless steel water bottle", "product_description": "An AquaSteel stainless steel portable water bottle with a 1 litre capacity.", "marks": [{"type": "ISI", "confidence": 0.95}], "cml_number": null, "r_number": null, "huid": null, "purity": null, "is_number_on_label": null, "brand": "AquaSteel", "other_text": "1 litre", "image_quality": "blurry", "notes": "The image is blurry but the brand, IS number, and CM/L number are legible. The photo is too blurry to read the numbers reliably (cml number, is number on label); please send a sharper photo of the label."}`

**What I see in your photo:** stainless steel water bottle; ISI mark.
(Photo blurry: The image is blurry but the brand, IS number, and CM/L number are legible. The photo is too blurry to read the numbers reliably (cml number, is number on label); please send a sharper photo of the label. I do not guess numbers I cannot read clearly.)

The ISI mark this product needs is visible in the photo.

IS 17803: 2022 applies to your stainless steel potable water bottle, BIS certification is compulsory under Scheme I (ISI mark), and it is governed by the Potable Water Bottles (Quality Control) Order, 2023 S.O. 2988(E), dated 5th July 2023 [1].

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 17803: 2022: Potable Water Bottles (Copper, Stainless Steel, Aluminum) | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 09_no_mark_bottle.png
`{"product_type": "stainless steel water bottle", "product_description": "A stainless steel water bottle.", "marks": [], "cml_number": null, "r_number": null, "huid": null, "purity": null, "is_number_on_label": null, "brand": "CoolSip", "other_text": "CoolSip Steel Bottle, Stainless steel water bottle, Keep away from fire, Made in India", "image_quality": "good", "notes": "No standard compliance marks or numbers are present on the label."}`

**What I see in your photo:** stainless steel water bottle; no certification mark visible.
(Photo good: No standard compliance marks or numbers are present on the label. I do not guess numbers I cannot read clearly.)

**No ISI mark visible; this product requires one** [1].

IS 17803: 2022 applies to Potable Water Bottles (Copper, Stainless Steel, Aluminum), and BIS certification is compulsory under Scheme I (ISI mark) governed by the Potable Water Bottles (Quality Control) Order, 2023 S.O. 2988(E), dated 5th July 2023 (along with subsequent orders of 2024 and 2026) [1].

**Sources:**
[1] Scheme I (ISI mark): products under compulsory certification: IS 17803: 2022: Potable Water Bottles (Copper, Stainless Steel, Aluminum) | https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-1/?lang=en

## 10_landscape.png
`{"product_type": null, "product_description": "Digital illustration of a landscape containing mountains, a tree, a sun, and grass.", "marks": [], "cml_number": null, "r_number": null, "huid": null, "purity": null, "is_number_on_label": null, "brand": null, "other_text": null, "image_quality": "good", "notes": "The image is a landscape drawing, not a commercial product or a label with BIS marks."}`

**What I see in your photo:** Digital illustration of a landscape containing mountains, a tree, a sun, and grass.. I can't see a product or a BIS mark, so there is nothing to check. Send a photo of the product and its label or mark.
