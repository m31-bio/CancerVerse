"""Extract Table S1 (logistic regression parameters) from the cervical paper's supplement.

Wu Z, Li T, Han Y, et al. "Development of models for cervical cancer screening:
construction in a cross-sectional population and validation in two screening
cohorts in China." BMC Medicine. 2021;19(1):197.
doi:10.1186/s12916-021-02078-2 (open access).

The supplement is a real .xlsx, not a figure, which makes this the strongest
kind of coefficient check available: an independently downloaded, machine-
readable copy of the source table, compared term by term at zero tolerance.

Two access notes worth keeping, because the obvious route fails:

  * PMC's own mirror path (/articles/instance/8414700/bin/...MOESM1_ESM.xlsx)
    returns a "Preparing to download" HTML interstitial, not the workbook.
    `file` reports it as HTML; openpyxl then dies with BadZipFile.
  * Springer's CDN serves the real file:
        https://static-content.springer.com/esm/
            art%3A10.1186%2Fs12916-021-02078-2/MediaObjects/
            12916_2021_2078_MOESM1_ESM.xlsx

Run to refresh the fixture:

    python tests/parity/reference/cervical_s1_extract.py

Writes cervical_table_s1.json, which tests/parity/test_cervical_cin_parity.py
asserts against offline.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

URL = (
    "https://static-content.springer.com/esm/"
    "art%3A10.1186%2Fs12916-021-02078-2/MediaObjects/"
    "12916_2021_2078_MOESM1_ESM.xlsx"
)
OUT = Path(__file__).with_name("cervical_table_s1.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def main() -> None:
    import io

    import openpyxl

    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    blob = urllib.request.urlopen(req, timeout=120).read()
    if not blob.startswith(b"PK"):
        raise SystemExit("got HTML, not a workbook, the download path changed")

    ws = openpyxl.load_workbook(io.BytesIO(blob), data_only=True)["Table S1"]

    blocks: dict[str, dict[str, float]] = {}
    current = None
    for row in ws.iter_rows(min_row=1, values_only=True):
        label, value = row[0], row[1]
        if label is None:
            continue
        label = str(label).strip()
        if value is None:
            if label.lower().startswith("base"):
                current = label
                blocks[current] = {}
            continue
        if current and isinstance(value, (int, float)):
            blocks[current][label] = float(value)

    OUT.write_text(json.dumps(blocks, indent=2) + "\n")
    total = sum(len(v) for v in blocks.values())
    print(f"wrote {OUT} — {len(blocks)} models, {total} coefficients")


if __name__ == "__main__":
    main()
