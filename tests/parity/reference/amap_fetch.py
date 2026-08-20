"""Capture reference outputs from CUHK's aMAP calculator.

Verification route 3 (POST to a server-side endpoint). aMAP publishes no worked
example, so the custodial calculator is the only external check available.

The tool is hosted by CUHK's Medical Data Analytics Centre, an aMAP
collaborating site:  https://mdac.cuhk.edu.hk/calculators/amap/
It is a WordPress form posting to admin-ajax.php with action
`get_calculator_result`; the response is a JSON array
`[score, risk_group, label, incidence]`. The score is an INTEGER.

Field map (opaque names, recovered from the form markup):
    field_0 age (years)          field_1 gender ("Male"/"Female")
    field_2 total bilirubin      field_2_unit "µmol/L" | "mg/dL"
    field_3 albumin              field_3_unit "g/L" | "g/dL"
    field_4 platelets            field_4_unit "x10<sup>9</sup>/L" | ...

HISTORICAL NOTE — READ THIS BEFORE TRUSTING OLD DOCS
-----------------------------------------------------
An earlier probe of this calculator recorded scores 2-3 points ABOVE the
published formula, and that discrepancy was documented in this repo as an
unresolved conflict requiring the authors to adjudicate. It no longer
reproduces: the same three inputs now return exactly what the published formula
gives. Whatever the cause (a fixed tool, or an error in the original probe), the
conflict is closed empirically and the published formula stands.

This script is NOT run by the test suite. It writes amap_cases.json, and
tests/parity/test_amap_parity.py asserts against that file so CI stays offline.

    python tests/parity/reference/amap_fetch.py
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

AJAX = "https://mdac.cuhk.edu.hk/wp-admin/admin-ajax.php"
PAGE = "https://mdac.cuhk.edu.hk/calculators/amap/"
POST_ID = "58"
OUT = Path(__file__).with_name("amap_cases.json")

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

UNIT_BILI_SI = "µmol/L"
UNIT_ALB_SI = "g/L"
UNIT_PLT_SI = "x10<sup>9</sup>/L"

# Spans age, both sexes, and each analyte across its clinical range, and
# straddles both band cut-offs (50 and 60). The three cases marked `historic`
# are the exact inputs that produced the previously recorded 56/44/68.
CASES = [
    dict(age=50, male=True, bili=15, alb=42, plt=200, historic=56),
    dict(age=30, male=True, bili=10, alb=45, plt=250, historic=44),
    dict(age=65, male=True, bili=25, alb=38, plt=150, historic=68),
    dict(age=50, male=False, bili=15, alb=42, plt=200),  # sex is the only change
    dict(age=30, male=False, bili=10, alb=45, plt=250),
    dict(age=65, male=False, bili=25, alb=38, plt=150),
    dict(age=18, male=True, bili=5, alb=50, plt=400),  # low extreme
    dict(age=85, male=True, bili=60, alb=28, plt=60),  # high extreme
    dict(age=45, male=False, bili=20, alb=40, plt=180),
    dict(age=70, male=True, bili=12, alb=35, plt=120),
    dict(age=55, male=False, bili=30, alb=44, plt=300),
    dict(age=60, male=True, bili=18, alb=41, plt=220),
    dict(age=40, male=True, bili=8, alb=47, plt=280),
    dict(age=75, male=False, bili=35, alb=33, plt=100),
    dict(age=62, male=True, bili=22, alb=39, plt=160),
]


def probe(case: dict) -> list:
    fields = {
        "action": "get_calculator_result",
        "post_id": POST_ID,
        "field_0": str(case["age"]),
        "field_1": "Male" if case["male"] else "Female",
        "field_2": str(case["bili"]),
        "field_2_unit": UNIT_BILI_SI,
        "field_3": str(case["alb"]),
        "field_3_unit": UNIT_ALB_SI,
        "field_4": str(case["plt"]),
        "field_4_unit": UNIT_PLT_SI,
    }
    req = urllib.request.Request(
        AJAX,
        data=urllib.parse.urlencode(fields).encode(),
        headers={
            "User-Agent": UA,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": PAGE,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
    )
    raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    return json.loads(raw)


def main() -> None:
    rows = []
    for k, c in enumerate(CASES):
        score, group, _label, incidence = probe(c)
        rows.append(
            {
                **{key: c[key] for key in ("age", "male", "bili", "alb", "plt")},
                "historic": c.get("historic"),
                "score": score,
                "risk_group": group,
                "incidence": incidence,
            }
        )
        print(f"[{k + 1:2d}/{len(CASES)}] {c} -> {score} {group} {incidence}")
        time.sleep(1.0)

    OUT.write_text(
        json.dumps(
            {
                "source": AJAX,
                "tool": "CUHK MDAC aMAP calculator",
                "page": PAGE,
                "units": {
                    "bilirubin": "umol/L",
                    "albumin": "g/L",
                    "platelets": "x10^9/L",
                },
                "resolution": "integer score, as returned by the tool",
                "cases": rows,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"\nwrote {OUT} ({len(rows)} cases)")


if __name__ == "__main__":
    main()
