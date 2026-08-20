"""Extract published formulas / point tables from MDCalc calculators.

Run:  python tests/parity/reference/mdcalc_extract.py

Why this exists
---------------
Eleven models in this project publish no per-patient worked example, so the
usual parity check is unavailable. That does NOT mean they are unverifiable: an
**independent reimplementation that publishes its own formula** can be compared
coefficient-by-coefficient, which covers the whole input space rather than one
point.

MDCalc is a Next.js app that ships each calculator's input schema, including
every option's point value, in the page's `__NEXT_DATA__` blob, and its prose
"formula" field for continuous models. Both are extractable without running the
calculator.

This route already paid for itself: it exposed that our ALBI module carried
`-0.0852` where the primary paper prints `-0.085` (see docs/VERIFICATION.md).

Caveat on what this proves
--------------------------
Agreement with MDCalc is *corroboration*, not proof. MDCalc is a secondary
source. It is strong evidence when MDCalc's value is independently traceable to
the same primary paper, and it is decisive when the two disagree, because then
at least one of us is wrong and the primary must be consulted.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request

CALCULATORS = {
    "albi": "https://www.mdcalc.com/calc/10070/albi-albumin-bilirubin-grade-hepatocellular-carcinoma-hcc",
    "capra": "https://www.mdcalc.com/calc/2046/ucsf-capra-score-prostate-cancer-risk",
    "cha2ds2_vasc": "https://www.mdcalc.com/calc/801/cha2ds2-vasc-score-atrial-fibrillation-stroke-risk",
}


def fetch_calc(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as fh:
        html = fh.read().decode("utf-8", errors="ignore")
    blob = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not blob:
        raise ValueError(f"no __NEXT_DATA__ at {url}")
    return json.loads(blob.group(1))["props"]["pageProps"]["calc"]


def describe(name: str, calc: dict) -> None:
    print(f"\n=== {name} ===")
    for field in calc.get("input_schema", []):
        opts = field.get("options")
        if opts:
            rendered = ", ".join(
                f"{o.get('label') or o.get('label_en')}={o['value']}" for o in opts
            )
            print(f"  {field['name']:26} {rendered}")
    formula = (calc.get("content", {}).get("about", {}) or {}).get("formula_en", "")
    if formula:
        text = re.sub(r"<[^>]+>", "", formula)
        text = text.replace("&times;", "x").replace("&mu;", "u").replace("&minus;", "-")
        print(f"  formula: {' '.join(text.split())[:220]}")


def main() -> int:
    for name, url in CALCULATORS.items():
        try:
            describe(name, fetch_calc(url))
        except Exception as exc:  # network / layout change
            print(f"\n=== {name} ===\n  FAILED: {type(exc).__name__}: {exc}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
