"""Format checks for numbers read from a product photo (plain code, no AI). Every rule cites the BIS document
it comes from; a rule the documents do not state is not assumed.

    check(vision_json) -> [{"field", "value", "valid_format", "reason", "source"}]

A valid FORMAT never means the number is genuine: only the BIS CARE app can confirm that.
"""
import re

# rule -> (regex for the whole value, what the documents say, chunk_id that says it)
HUID = (re.compile(r"^[A-Z0-9]{6}$"), "a HUID is a six-digit alphanumeric number, unique for each hallmarked item",
        "hm_faq_general::0002")
R_NUMBER = (re.compile(r"^R-\d{8}$"), "the CRS licence number is written R-XXXXXXXX (R- followed by 8 characters)",
            "ca_regulations_2018::0156")
CML = (re.compile(r"^CM/L-\d+$"), "the licence number is written CM/L-<number>; the documents do not state how many "
                                   "digits it has, so only the CM/L- prefix and digits are checked",
       "guide_change_in_scope::0010")
PURITY_GRADES = {"14K585", "18K750", "20K833", "22K916", "23K958", "24K995"}
PURITY = ("gold purity grades are 14K(585), 18K(750), 20K(833), 22K(916), 23K(958) and 24K(995)", "hm_faq_general::0000")


def _norm(value: str) -> str:
    return re.sub(r"\s+", "", str(value)).upper().replace("–", "-").replace("—", "-")


def check_huid(value: str) -> dict:
    v = _norm(value)
    ok = bool(HUID[0].match(v))
    return {"field": "huid", "value": value, "valid_format": ok, "source": HUID[2],
            "reason": (f"{v} has 6 letters/digits" if ok else f"{v} has {len(v)} characters or other symbols")
                      + f": {HUID[1]}."}


def check_r_number(value: str) -> dict:
    v = _norm(value)
    v = re.sub(r"^R(?=\d)", "R-", v)  # "R12345678" -> "R-12345678"
    ok = bool(R_NUMBER[0].match(v))
    digits = re.sub(r"\D", "", v)
    return {"field": "r_number", "value": value, "valid_format": ok, "source": R_NUMBER[2],
            "reason": (f"{v} is R- followed by 8 digits" if ok else f"{v} has {len(digits)} digits after R-")
                      + f": {R_NUMBER[1]}."}


def check_cml(value: str) -> dict:
    v = _norm(value)
    v = re.sub(r"^CM/?L[-:]?(?=\d)", "CM/L-", v)
    ok = bool(CML[0].match(v))
    return {"field": "cml_number", "value": value, "valid_format": ok, "source": CML[2],
            "reason": (f"{v} starts with CM/L- and is followed by digits" if ok
                       else f"{v} is not CM/L- followed by digits") + f": {CML[1]}."}


def check_purity(value: str) -> dict:
    v = re.sub(r"[^0-9K]", "", _norm(value))
    ok = v in PURITY_GRADES
    return {"field": "purity", "value": value, "valid_format": ok, "source": PURITY[1],
            "reason": (f"{v} is a listed grade" if ok else f"{v} is not one of the listed grades") + f": {PURITY[0]}."}


def check(vision: dict) -> list[dict]:
    """Checks every number the photo showed (unreadable / missing numbers are skipped, never guessed)."""
    out = []
    for field, fn in (("huid", check_huid), ("r_number", check_r_number), ("cml_number", check_cml),
                      ("purity", check_purity)):
        value = (vision or {}).get(field)
        if value and str(value).strip().lower() not in ("null", "none", "unclear"):
            out.append(fn(value))
    return out


if __name__ == "__main__":
    assert check_huid("AB12C3")["valid_format"] and not check_huid("AB12C")["valid_format"]
    assert check_r_number("R-41012345")["valid_format"] and not check_r_number("R-4101234")["valid_format"]
    assert check_cml("CM/L-7600012345")["valid_format"] and not check_cml("CML 76A0")["valid_format"]
    assert check_purity("22K916")["valid_format"] and not check_purity("22K999")["valid_format"]
    print("ok")
