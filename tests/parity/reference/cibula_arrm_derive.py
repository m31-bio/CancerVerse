#!/usr/bin/env python
"""Derive the ARRM outcome grid from the ESGO calculator's own shipped cohort.

Run:

    .venv/bin/python tests/parity/reference/cibula_arrm_derive.py

It writes two files and nothing else:

  * ``src/cancerverse_baseline/cervical/prognosis/data/cibula_arrm_2021.json``, the
    committed data file the model imports: Table 2's points schedule, and the
    5 x 5 outcome grid.
  * ``tests/parity/reference/cibula_arrm_cases.json``, the offline parity
    fixture, holding the numbers *the paper prints* next to the numbers this
    script *computes*, plus the deployed calculator's own points schedule.

Why a script and not a typed-in table
-------------------------------------
Cibula et al print the points schedule in full (Table 2) and the outcome grid
only in part. The text gives the 26-50 band at years 1/3/5, the 51-75 band at
years 1 and 5, and the 76-100 band at years 1 and 2; the two lowest bands are
described qualitatively ("close to 0%", "oscillating close to 1%"). The whole
grid exists as Fig. 3, which is a graphic.

The deployed calculator supplies it numerically, and generously. The page is
static and ships **the entire derivation cohort client-side**: a single
``const dataRaw = [...]`` of 4343 rows, which is the paper's own N. Its
``scripts/main.js`` carries the estimator, a plain Kaplan-Meier, then
``arrm[i] = (S(i-1) - S(i)) / S(i-1)`` with year buckets assigned by
``Math.ceil(t)``. So the grid is not read off a figure, it is recomputed from
patient-level data, and the recomputation can be checked against the seven
numbers the paper does print.

`kaplan_meier` and `annual_recurrence_risk` below are deliberate line-by-line
ports of that JavaScript rather than idiomatic survival code. Two details
matter and a tidier implementation would silently change them: event times are
matched by exact float equality (`rfiYears === t_i`), and the landmark bucket
for a KM step at time t is `ceil(t)`, so an event at exactly 2.0 years lands in
year 2 and one at 2.01 lands in year 3.

What this does NOT establish
----------------------------
That the 4343 rows are the paper's 4343 patients is inferred from the row
count, the 528 event rows against the paper's 528 recurrences, the per-band
sizes (213 / 1844 / 1899 / 374 / 13, and the paper states 213 and 13), and the
reproduction of the printed outcome numbers. The rows carry no identifiers and
the cohort is not separately published, so it cannot be checked further.

Licensing
---------
The points schedule is Table 2 of a CC-licensed PMC article, published
scientific fact under `docs/CONVENTIONS.md`. The outcome grid is *derived from
data shipped by the calculator*, whose pages carry "©2023 All rights
reserved". That is a different question and it is NOT resolved here; see
`docs/COMMERCIAL_USE_AUDIT.md`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DATA_OUT = (ROOT / "src" / "cancerverse_baseline" / "cervical" / "prognosis"
            / "data" / "cibula_arrm_2021.json")
FIXTURE_OUT = Path(__file__).resolve().parent / "cibula_arrm_cases.json"

BASE = "https://calculators.esgo.org/cervical-cancer-recurrence-risk-calculator/"
FILES = {
    "index.html": BASE,
    "data/data.min.js": BASE + "data/data.min.js",
    "scripts/main.js": BASE + "scripts/main.js",
}
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")

# ---------------------------------------------------------------------------
# Table 2, transcribed once, here, from the PMC9406128 article HTML.
#
# This is the ONLY transcription of these numbers in the repository: the model
# module reads them back out of the JSON this script writes. Two independent
# checks below make a typo here fail loudly rather than ship:
#
#   * `check_points_reproduce_from_betas` re-derives all thirteen point values
#     from the betas alone, through the paper's own stated construction
#     ("weighted to the maximum sum of 100 points");
#   * `check_calculator_agrees` reads the deployed calculator's own
#     `<option value="...">` attributes and demands an exact match.
#
# The reference levels are the trap. Positive pelvic LN pools "0 / not
# assessed", and LVSI pools "No / not assessed", a patient who never had the
# node dissection scores the same as a node-negative one. Grade has no such
# pooling: its levels are 1, 2 and 3 and nothing else.
# ---------------------------------------------------------------------------
TABLE_2: dict[str, dict[str, Any]] = {
    "histotype": {
        "label": "Histotype",
        "reference": "squamous",
        "reference_label": "Squamous cell",
        "levels": {
            "squamous": {"label": "Squamous cell", "beta": None, "points": 0},
            "adenocarcinoma": {"label": "Adenocarcinoma", "beta": 0.342, "points": 7},
            "adenosquamous": {"label": "Adenosquamous", "beta": 0.598, "points": 11},
            "neuroendocrine": {"label": "Neuroendocrine", "beta": 1.741, "points": 33},
            "other": {"label": "Other", "beta": 1.145, "points": 22},
        },
    },
    "tumour_diameter": {
        "label": "Tumour diameter",
        "reference": "<0.5cm",
        "reference_label": "< 0.5 cm",
        "levels": {
            "<0.5cm": {"label": "< 0.5 cm", "beta": None, "points": 0},
            "0.5-1.99cm": {"label": "0.5-1.99 cm", "beta": 0.501, "points": 10},
            "2-3.99cm": {"label": "2-3.99 cm", "beta": 1.115, "points": 21},
            ">=4cm": {"label": ">= 4 cm", "beta": 1.556, "points": 30},
        },
    },
    "grade": {
        "label": "Grade",
        "reference": "1",
        "reference_label": "1",
        "levels": {
            "1": {"label": "1", "beta": None, "points": 0},
            "2": {"label": "2", "beta": 0.260, "points": 5},
            "3": {"label": "3", "beta": 0.457, "points": 9},
        },
    },
    "positive_pelvic_nodes": {
        "label": "Positive pelvic LN",
        "reference": "0_or_not_assessed",
        "reference_label": "0 / not assessed",
        "levels": {
            "0_or_not_assessed": {"label": "0 / not assessed", "beta": None, "points": 0},
            "1": {"label": "1", "beta": 0.255, "points": 5},
            "2": {"label": "2", "beta": 0.482, "points": 9},
            ">=3": {"label": ">= 3", "beta": 0.939, "points": 18},
        },
    },
    "lvsi": {
        "label": "LVSI",
        "reference": "no_or_not_assessed",
        "reference_label": "No / not assessed",
        "levels": {
            "no_or_not_assessed": {"label": "No / not assessed", "beta": None, "points": 0},
            "yes": {"label": "Yes", "beta": 0.538, "points": 10},
        },
    },
}

#: 25-point intervals except the first, which is the absence of every risk
#: predictor. Methods: "0, 1-25, 26-50, 51-75, 76-100".
BANDS = [
    {"index": 0, "low": 0, "high": 0, "label": "0 points"},
    {"index": 1, "low": 1, "high": 25, "label": "1-25 points"},
    {"index": 2, "low": 26, "high": 50, "label": "26-50 points"},
    {"index": 3, "low": 51, "high": 75, "label": "51-75 points"},
    {"index": 4, "low": 76, "high": 100, "label": "76-100 points"},
]

#: The calculator's `<option value>` order per select, as the page lists them.
OPTION_ORDER = {
    "histotype": ["squamous", "adenocarcinoma", "adenosquamous",
                  "neuroendocrine", "other"],
    "max-diameter": ["<0.5cm", "0.5-1.99cm", "2-3.99cm", ">=4cm"],
    "grade": ["1", "2", "3"],
    "positive-lymph-nodes": ["0_or_not_assessed", "1", "2", ">=3"],
    "space-invasion": ["no_or_not_assessed", "yes"],
}
_SELECT_TO_PREDICTOR = {
    "histotype": "histotype",
    "max-diameter": "tumour_diameter",
    "grade": "grade",
    "positive-lymph-nodes": "positive_pelvic_nodes",
    "space-invasion": "lvsi",
}

# ---------------------------------------------------------------------------
# What the paper itself prints, with the sentence each number came from. These
# are the parity targets: everything else in the fixture is computed.
# ---------------------------------------------------------------------------
PAPER_VALUES = [
    {"quantity": "dfs", "band": 0, "year": 5, "printed": 97.5,
     "locus": "Abstract",
     "quote": "five-year DFS of 97.5%, 94.7%, 85.2%, and 63.3% in increasing "
              "risk groups"},
    {"quantity": "dfs", "band": 1, "year": 5, "printed": 94.7,
     "locus": "Abstract", "quote": "(same sentence)"},
    {"quantity": "dfs", "band": 2, "year": 5, "printed": 85.2,
     "locus": "Abstract", "quote": "(same sentence)"},
    {"quantity": "dfs", "band": 3, "year": 5, "printed": 63.3,
     "locus": "Abstract", "quote": "(same sentence)"},
    {"quantity": "dfs", "band": 4, "year": 2, "printed": 15.4,
     "locus": "Abstract / Discussion",
     "quote": "two-year DFS in the highest risk group equalled 15.4%"},
    {"quantity": "arrm", "band": 2, "year": 1, "printed": 5.2,
     "locus": "Results, ARRM",
     "quote": "the RR for the first year of follow-up was 5.2% "
              "(95% CI: 4.2%; 6.2%)"},
    {"quantity": "arrm", "band": 2, "year": 3, "printed": 3.2,
     "locus": "Results, ARRM",
     "quote": "steadily decreased from year three (3.2% (95% CI: 2.3%; 4.1%)"},
    {"quantity": "arrm", "band": 2, "year": 5, "printed": 1.0,
     "locus": "Results, ARRM", "quote": "to year five (1.0% (95% CI: 0.4%; 1.6%))"},
    {"quantity": "arrm", "band": 3, "year": 1, "printed": 13.7,
     "locus": "Results, ARRM",
     "quote": "recurrence risk equalling 13.7% (95% CI: 10.2%; 17.2%) at year one"},
    {"quantity": "arrm", "band": 3, "year": 5, "printed": 3.9,
     "locus": "Results, ARRM",
     "quote": "significantly decreased by year five, when it reached 3.9% "
              "(95% CI: 0.8%; 7.0%)"},
    {"quantity": "arrm", "band": 4, "year": 1, "printed": 53.8,
     "locus": "Results, ARRM",
     "quote": "The probability of recurrence in years one and two equalled "
              "53.8% (95% CI: 26.7%; 80.9%)"},
    {"quantity": "arrm", "band": 4, "year": 2, "printed": 66.7,
     "locus": "Results, ARRM", "quote": "and 66.7% (95% CI: 28.9%; 100%)"},
]

#: Cohort facts the paper states, checked against the shipped rows.
PAPER_COUNTS = {
    "n_total": {"value": 4343, "quote": "Data of 4,343 early-stage cervical "
                                        "cancer patients (Abstract / Methods)"},
    "n_events": {"value": 528, "quote": "528 recurrence rows; the paper's "
                                        "cohort had 528 recurrences"},
    "band_0_n": {"value": 213, "quote": "the group with zero points represents "
                                        "a cohort of 213 patients"},
    "band_0_events": {"value": 4, "quote": "only four recurrences were observed"},
    "band_4_n": {"value": 13, "quote": "due to the limited number of cases "
                                       "(13 patients)"},
    "band_4_events": {"value": 12, "quote": "high recurrence rate in the first "
                                            "three years (cumulatively, 12 "
                                            "recurrences)"},
}

#: The paper stops the 76-100 landmark analysis at year three and says so:
#: "The landmark analysis for the group with the highest risk (76-100 points)
#: was only performed until year three of follow-up ... The analysis ceased to
#: be reliable after this point." Fig. 3 marks the rest N/A. Two patients are
#: still at risk entering year three and none entering year four, so years four
#: and five compute to a flat 0.0% that means "nobody left", not "no risk".
ARRM_RELIABLE_THROUGH = {0: 5, 1: 5, 2: 5, 3: 5, 4: 3}

#: Row layout, from the `jsonAttributeMap` in scripts/main.js.
KEYS = ["fupYears", "points", "category", "recurrence", "rfiYears", "cat1", "cat2"]


# ---------------------------------------------------------------------------
# The estimator, ported from scripts/main.js
# ---------------------------------------------------------------------------
def kaplan_meier(rows: list[dict]) -> tuple[list[dict], list[float]]:
    """Port of ``kmCurve(data, true)``.

    Returns the KM table (with a synthetic S=1 row prepended at t=0) and the
    Greenwood-style standard errors the calculator uses for its displayed
    confidence intervals.
    """
    event_times = [r["rfiYears"] for r in rows if r.get("recurrence")]
    unique = sorted(set(event_times))

    censored = [r["fupYears"] for r in rows if not r.get("recurrence")]
    max_fup = max(censored) if censored else -math.inf
    if not unique or max_fup > unique[-1]:
        if max_fup > 0:
            unique.append(max_fup)

    table: list[dict] = []
    d_is: list[int] = []
    n_is: list[int] = []
    for t_i in unique:
        # Exact float equality, as the JavaScript does. The times come from the
        # same decimal literals, so both languages parse them to one double.
        d_i = sum(1 for r in rows if r.get("recurrence") and r["rfiYears"] == t_i)
        y_i = sum(
            1 for r in rows
            if (not r.get("recurrence") and r["fupYears"] >= t_i)
            or (r.get("recurrence") and r["rfiYears"] >= t_i)
        )
        d_is.append(d_i)
        n_is.append(y_i)
        table.append({"t": t_i, "d": d_i, "at_risk": y_i,
                      "step": 1 - d_i / y_i if y_i else float("nan")})

    for i, row in enumerate(table):
        row["S"] = (table[i - 1]["S"] if i else 1.0) * row["step"]

    table.insert(0, {"t": 0.0, "d": 0, "at_risk": 0, "step": 0.0, "S": 1.0})

    se = []
    for i in range(len(d_is)):
        total = 0.0
        finite = True
        for j in range(i + 1):
            denom = n_is[j] * (n_is[j] - d_is[j])
            if denom == 0:
                finite = False
                break
            total += d_is[j] / denom
        se.append(math.sqrt(total) if finite else 0.0)
    se.insert(0, 0.0)
    return table, se


def annual_recurrence_risk(rows: list[dict]) -> dict[str, list[float]]:
    """Port of ``calculateArrm(data)``.

    The landmark step is the part worth reading twice. Every KM step at time
    ``t`` is written into bucket ``ceil(t)`` and every later bucket, so a
    bucket holds the survival at the *end* of that year. The annual risk is
    then the conditional drop across the year, ``(S[y-1] - S[y]) / S[y-1]``,
    not the unconditional increment, which is what makes it a *conditional*
    recurrence risk for a patient who has already survived y-1 years.
    """
    table, se = kaplan_meier(rows)
    surv = [1.0] * 6
    surv_se = [0.0] * 6
    for k, row in enumerate(table):
        i = math.ceil(row["t"])
        if i < len(surv):
            for j in range(i, len(surv)):
                surv[j] = row["S"]
                surv_se[j] = se[k]

    arrm: list[float] = []
    for i in range(1, len(surv)):
        arrm.append((surv[i - 1] - surv[i]) / surv[i - 1])
        if surv[i] == 0:
            break
    arrm += [float("nan")] * (5 - len(arrm))

    dfs = surv[1:]
    dfs_se = surv_se[1:]
    return {
        "dfs": dfs,
        "dfs_ci_low": [max(0.0, d - 1.96 * s)
                        for d, s in zip(dfs, dfs_se, strict=True)],
        "dfs_ci_high": [min(1.0, d + 1.96 * s)
                         for d, s in zip(dfs, dfs_se, strict=True)],
        "arrm": arrm,
    }


# ---------------------------------------------------------------------------
# Checks. Each one refuses to write rather than warning.
# ---------------------------------------------------------------------------
def points_divisor() -> float:
    """100 / (sum of the largest beta in each predictor).

    The paper says only that the score "was derived from regression
    coefficients (beta) of the final model, which were weighted to the maximum
    sum of 100 points". It never states the divisor. This is that sentence
    taken literally: the worst possible patient, neuroendocrine, >= 4 cm,
    grade 3, >= 3 positive nodes, LVSI present, must score exactly 100.
    """
    worst = sum(
        max(lv["beta"] or 0.0 for lv in pred["levels"].values())
        for pred in TABLE_2.values()
    )
    return 100.0 / worst


def check_points_reproduce_from_betas() -> dict[str, Any]:
    """Every published point value must be round(beta * divisor).

    This is what proves the two halves of Table 2 are one model rather than two
    independent transcriptions. Thirteen constraints on one unknown; nothing
    but a correct beta column can satisfy them all. Same technique that settled
    the Kunzmann divisor, where it exposed a wrong footnote.
    """
    divisor = points_divisor()
    checked = []
    for name, pred in TABLE_2.items():
        for key, level in pred["levels"].items():
            if level["beta"] is None:
                if level["points"] != 0:
                    raise SystemExit(
                        f"{name}.{key} is a reference level with "
                        f"{level['points']} points")
                continue
            got = round(level["beta"] * divisor)
            if got != level["points"]:
                raise SystemExit(
                    f"beta->points MISMATCH at {name}.{key}: "
                    f"{level['beta']} * {divisor:.6f} = "
                    f"{level['beta'] * divisor:.4f} -> {got}, "
                    f"Table 2 prints {level['points']}")
            checked.append(f"{name}.{key}")
    worst_points = sum(max(lv["points"] for lv in p["levels"].values())
                       for p in TABLE_2.values())
    if worst_points != 100:
        raise SystemExit(f"the worst patient scores {worst_points}, not 100")
    print(f"  beta -> points: all {len(checked)} reproduce at "
          f"divisor {divisor:.10f}; worst patient scores 100")
    return {"divisor": divisor, "n_levels_checked": len(checked)}


def check_calculator_agrees(index_html: str) -> dict[str, list[int]]:
    """The deployed calculator's option values must be the same schedule.

    `docs/EXTRACTION.md` Route C, a second independent statement of the rule.
    Compared at zero tolerance because these are integers: any disagreement is
    a real disagreement, not a rounding difference.
    """
    selects = dict(re.findall(
        r'<select[^>]*\bid="([a-z-]+)"[^>]*>(.*?)</select>', index_html, re.S))
    found: dict[str, list[int]] = {}
    for select_id, level_keys in OPTION_ORDER.items():
        if select_id not in selects:
            raise SystemExit(f"no <select id={select_id!r}> on the page")
        values = [int(v) for v in
                  re.findall(r'<option value="(-?\d+)"', selects[select_id])]
        predictor = _SELECT_TO_PREDICTOR[select_id]
        expected = [TABLE_2[predictor]["levels"][k]["points"] for k in level_keys]
        if values != expected:
            raise SystemExit(
                f"calculator disagrees with Table 2 for {select_id}: "
                f"page says {values}, Table 2 says {expected}")
        found[select_id] = values
    print(f"  calculator option values: exact match on all "
          f"{sum(len(v) for v in found.values())} levels")
    return found


def band_of(points: int) -> int:
    for band in BANDS:
        if band["low"] <= points <= band["high"]:
            return band["index"]
    raise SystemExit(f"points {points} fall outside 0-100")


def check_cohort(rows: list[dict]) -> dict[str, Any]:
    """The shipped rows must look like the paper's cohort before we trust them."""
    lengths = Counter(len(r) for r in RAW)
    n_total = len(rows)
    n_events = sum(1 for r in rows if r.get("recurrence"))
    per_band = Counter(band_of(r["points"]) for r in rows)
    events_band = Counter(band_of(r["points"]) for r in rows if r.get("recurrence"))

    actual = {
        "n_total": n_total, "n_events": n_events,
        "band_0_n": per_band[0], "band_0_events": events_band[0],
        "band_4_n": per_band[4], "band_4_events": events_band[4],
    }
    for key, expected in PAPER_COUNTS.items():
        if actual[key] != expected["value"]:
            raise SystemExit(
                f"cohort check FAILED on {key}: shipped data has "
                f"{actual[key]}, the paper says {expected['value']} "
                f"({expected['quote']})")

    # The `category` column is the calculator's own banding. Re-derive it from
    # the points and demand agreement, so we band by the published rule rather
    # than by trusting a column.
    wrong = [r for r in rows if band_of(r["points"]) != r["category"]]
    if wrong:
        raise SystemExit(f"{len(wrong)} rows band differently from their "
                         "`category` column")

    lo = min(r["points"] for r in rows)
    hi = max(r["points"] for r in rows)
    if (lo, hi) != (0, 100):
        raise SystemExit(f"points span {lo}-{hi}, expected 0-100")

    print(f"  cohort: {n_total} rows ({dict(lengths)} by length), "
          f"{n_events} events, bands "
          f"{[per_band[i] for i in range(5)]}, points {lo}-{hi}")
    return {"n_total": n_total, "n_events": n_events,
            "per_band": [per_band[i] for i in range(5)],
            "events_per_band": [events_band[i] for i in range(5)],
            "row_lengths": {str(k): v for k, v in sorted(lengths.items())}}


# ---------------------------------------------------------------------------
def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return resp.read()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path,
                    help="directory holding already-fetched copies of the "
                         "three files; skips the network")
    args = ap.parse_args()

    print(f"ARRM derivation — {date.today().isoformat()}")
    print(f"source: {BASE}")

    blobs: dict[str, bytes] = {}
    for name, url in FILES.items():
        if args.cache:
            blobs[name] = (args.cache / Path(name).name).read_bytes()
            print(f"  cached  {name}  {len(blobs[name])} bytes")
        else:
            blobs[name] = fetch(url)
            print(f"  fetched {name}  {len(blobs[name])} bytes")

    artifacts = {
        name: {"url": FILES[name],
               "bytes": len(blob),
               "sha256": hashlib.sha256(blob).hexdigest()}
        for name, blob in blobs.items()
    }

    global RAW
    js = blobs["data/data.min.js"].decode("utf-8")
    match = re.search(r"const dataRaw\s*=\s*(\[.*\])\s*;", js, re.S)
    if not match:
        raise SystemExit("no `const dataRaw = [...]` in data.min.js")
    RAW = json.loads(match.group(1))
    # strict=True: if ESGO ever changes the shipped row format, this must
    # fail loudly. Without it a row gaining or losing a column would be
    # silently mis-mapped and the whole derived outcome grid would be wrong
    # in a way nothing downstream could detect.
    rows = [dict(zip(KEYS, r, strict=True)) for r in RAW]

    main_js = blobs["scripts/main.js"].decode("utf-8")
    if "jsonAttributeMap" not in main_js or "calculateArrm" not in main_js:
        raise SystemExit("scripts/main.js is not the estimator we ported")
    shipped_map = re.search(r"jsonAttributeMap\s*=\s*\[([^\]]*)\]", main_js)
    shipped_keys = [k.strip().strip("'\"") for k in shipped_map.group(1).split(",")]
    if shipped_keys != KEYS:
        raise SystemExit(f"row layout changed: page says {shipped_keys}, "
                         f"this script assumes {KEYS}")
    print(f"  row layout confirmed from main.js: {shipped_keys}")

    print("checks")
    divisor_info = check_points_reproduce_from_betas()
    options = check_calculator_agrees(blobs["index.html"].decode("utf-8"))
    cohort = check_cohort(rows)

    print("outcome grid")
    outcome = []
    for band in BANDS:
        sub = [r for r in rows if band_of(r["points"]) == band["index"]]
        est = annual_recurrence_risk(sub)
        outcome.append({
            "band_index": band["index"],
            "band_label": band["label"],
            "points_low": band["low"],
            "points_high": band["high"],
            "n": len(sub),
            "n_recurrences": sum(1 for r in sub if r.get("recurrence")),
            "dfs_percent": [round(100 * v, 1) for v in est["dfs"]],
            "dfs_ci_low_percent": [round(100 * v, 1) for v in est["dfs_ci_low"]],
            "dfs_ci_high_percent": [round(100 * v, 1) for v in est["dfs_ci_high"]],
            "arrm_percent": [round(100 * v, 1) for v in est["arrm"]],
            "arrm_reliable_through_year": ARRM_RELIABLE_THROUGH[band["index"]],
        })
        print(f"  {band['label']:>12}  n={len(sub):>4}  "
              f"DFS {' '.join(f'{v:5.1f}' for v in outcome[-1]['dfs_percent'])}  "
              f"ARRM {' '.join(f'{v:5.1f}' for v in outcome[-1]['arrm_percent'])}")

    print("against the numbers the paper prints")
    comparisons = []
    worst = 0.0
    for target in PAPER_VALUES:
        row = outcome[target["band"]]
        key = "dfs_percent" if target["quantity"] == "dfs" else "arrm_percent"
        computed = row[key][target["year"] - 1]
        delta = abs(computed - target["printed"])
        worst = max(worst, delta)
        comparisons.append({**target, "computed": computed,
                            "abs_diff": round(delta, 4)})
        flag = "" if delta < 1e-9 else f"   <-- differs by {delta:.1f} pp"
        print(f"  {target['quantity']:>4} band {target['band']} "
              f"year {target['year']}: paper {target['printed']:>5}  "
              f"computed {computed:>5}{flag}")
    print(f"  worst disagreement: {worst:.1f} percentage points")
    if worst > 0.15:
        raise SystemExit("a printed value is off by more than one KM step; "
                         "do not ship this grid")

    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUT.write_text(json.dumps({
        "model_id": "cibula_arrm",
        "generated": date.today().isoformat(),
        "generated_by": "tests/parity/reference/cibula_arrm_derive.py",
        "source": {
            "paper": {
                "citation": "Cibula D, Dostalek L, Jarkovsky J, et al. The "
                            "annual recurrence risk model for tailored "
                            "surveillance strategy in patients with cervical "
                            "cancer. Eur J Cancer. 2021;158:111-122",
                "doi": "10.1016/j.ejca.2021.09.008",
                "pmcid": "PMC9406128",
                "points_schedule_from": "Table 2, read from the PMC article HTML",
                "outcome_grid_in_paper": "Fig. 3 (a graphic) plus seven values "
                                         "quoted in the Abstract and Results",
            },
            "calculator": {
                "url": BASE,
                "role": "supplies the outcome grid numerically: the page ships "
                        "the whole 4343-row derivation cohort and the "
                        "estimator",
                "artifacts": artifacts,
                "notice": "The calculator pages carry '©2023 All rights "
                          "reserved'. The points schedule is Table 2 of a "
                          "CC-licensed article and is published scientific "
                          "fact; the outcome grid below is DERIVED FROM DATA "
                          "SHIPPED BY THE CALCULATOR, which is a separate "
                          "question and is not resolved here. See "
                          "docs/COMMERCIAL_USE_AUDIT.md.",
            },
        },
        "cohort": cohort,
        "points_divisor": divisor_info["divisor"],
        "predictors": TABLE_2,
        "bands": BANDS,
        "outcome": outcome,
    }, indent=1) + "\n")
    print(f"wrote {DATA_OUT.relative_to(ROOT)}")

    FIXTURE_OUT.write_text(json.dumps({
        "model_id": "cibula_arrm",
        "generated": date.today().isoformat(),
        "generated_by": "tests/parity/reference/cibula_arrm_derive.py",
        "what_this_fixture_is": (
            "The parity target is the PAPER, not the calculator. "
            "`paper_values` are the twelve outcome numbers Cibula et al print "
            "in prose, each with the sentence it came from; `computed` beside "
            "each is what re-running the calculator's own estimator over the "
            "calculator's own shipped cohort produces. `calculator_options` "
            "are the deployed page's <option value> attributes, an "
            "independent second statement of Table 2's points schedule. "
            "`cohort` are the counts the paper states about its own cohort."),
        "artifacts": artifacts,
        "paper_values": comparisons,
        "paper_cohort_counts": {
            k: {**v, "computed": cohort_value}
            for (k, v), cohort_value in zip(
                PAPER_COUNTS.items(),
                [cohort["n_total"], cohort["n_events"],
                 cohort["per_band"][0], cohort["events_per_band"][0],
                 cohort["per_band"][4], cohort["events_per_band"][4]],
                strict=True)
        },
        "calculator_options": options,
        "points_divisor": divisor_info["divisor"],
        "grid": outcome,
    }, indent=1) + "\n")
    print(f"wrote {FIXTURE_OUT.relative_to(ROOT)}")
    return 0


RAW: list = []

if __name__ == "__main__":
    sys.exit(main())
