"""ARRM, the annual recurrence risk model for cervical cancer (Cibula 2021).

Equation source
---------------
Cibula D, Dostalek L, Jarkovsky J, et al. "The annual recurrence risk model for
tailored surveillance strategy in patients with cervical cancer."
Eur J Cancer. 2021;158:111-122. doi:10.1016/j.ejca.2021.09.008 (PMC9406128).

SCCAN consortium: 4,343 early-stage patients treated 2007-2016 at 20 centres on
four continents. Harrell's C 0.735 (95% CI 0.713; 0.757); ten-fold
cross-validated AUC 0.732. Endorsed by ESGO, deployed at calculators.esgo.org,
and externally validated in IJGC 2025.

Why this model closes a cell four nomogram papers could not
-----------------------------------------------------------
Every previous cervical prognosis candidate was an `rms::cph` nomogram, and
none printed a baseline survival S0(t). Without it you can rank patients and
cannot state a probability, and the probability is the output. ARRM does not
need S0(t), because it is not a nomogram: it converts its betas into an integer
points score, bands the score into five groups, and reports the *observed*
Kaplan-Meier outcome per band. There is no baseline hazard anywhere in it.

The model has two halves, and they come from two different artifacts
--------------------------------------------------------------------
**Patient -> points** is Table 2 of the paper: fourteen levels with a beta and
an integer "Risk points (max. 100)" column, every reference level named.

**Points band -> outcome** is only partly printed. The text gives the 26-50
band at years 1/3/5, the 51-75 band at years 1 and 5, and the 76-100 band at
years 1 and 2; the two lowest bands are described qualitatively. The full grid
is Fig. 3, a graphic. It is recovered here by re-running the deployed
calculator's own estimator over the 4,343-row cohort that calculator ships
client-side, see `tests/parity/reference/cibula_arrm_derive.py`, which does
the derivation, and the parity test, which checks the result against the twelve
numbers the paper does print.

Both halves live in the generated data file beside this module rather than
being typed here, so neither exists in two places. The points schedule is
verified two independent ways: `POINTS_DIVISOR` re-derives all thirteen point
values from the betas alone, and the deployed calculator's own
`<option value>` attributes are compared at zero tolerance.

The reference levels are the trap
---------------------------------
Two of the five predictors pool "not assessed" with "negative":

    Positive pelvic LN      reference is "0 / NOT ASSESSED"
    LVSI                    reference is "No / NOT ASSESSED"

A patient who never had a pelvic lymphadenectomy therefore scores exactly like
a node-negative one, and a specimen never examined for lymphovascular invasion
scores like a clean one. That is the model as published, it was built to be
usable where the work-up is incomplete, but it means a missing field is
silently optimistic, and a caller reading `positive_pelvic_nodes=None` as "we
don't know" will get an answer that reads as "we know it's fine". Passing
`None` here is allowed and does exactly what the paper does; the returned
`notes` say so every time it happens.

**Grade does not work this way.** Its levels are 1, 2 and 3, and Table 2 prints
no "not assessed" level for it. Missing grade was multiply imputed during
fitting, which is not something this module can reproduce for one patient, so
grade is required and an unknown grade raises rather than defaulting to 1.

Scope
-----
Early-stage cervical cancer treated by **primary surgery**, and all five inputs
are surgical pathology. It is not a model for patients treated with definitive
chemoradiation, who never produce a specimen, and it is not a pre-operative
model, the tumour diameter is the pathologic one, not the imaged one. The
outcome is disease-free survival counted from surgery, and the annual
recurrence risk is *conditional*: the year-3 figure is the risk for a patient
who has already been recurrence-free for two years, not a cumulative risk.

The 76-100 band holds thirteen patients, twelve of whom recurred. The paper
runs its landmark analysis for that band only to year three and says why; years
four and five are reported here as None rather than as the 0.0% the arithmetic
gives, because there is nobody left in the band rather than no risk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

AXIS = "prognosis"
MODEL_ID = "cibula_arrm"
DISEASE = "cervical"

_DATA = Path(__file__).resolve().parent / "data" / "cibula_arrm_2021.json"
_MODEL: dict[str, Any] = json.loads(_DATA.read_text())

#: Table 2 in full: predictor -> {reference, levels -> {label, beta, points}}.
#: The beta column is carried for provenance and is NOT used to compute
#: anything, the integer points are the model, but a reader checking our
#: transcription against the paper needs the betas beside them.
PREDICTORS: dict[str, dict[str, Any]] = _MODEL["predictors"]

#: predictor -> level key -> integer points. What actually gets summed.
POINTS: dict[str, dict[str, int]] = {
    name: {key: lv["points"] for key, lv in pred["levels"].items()}
    for name, pred in PREDICTORS.items()
}

#: predictor -> level key -> beta, reference levels omitted. Provenance only.
TABLE_2_COEFFICIENTS: dict[str, dict[str, float]] = {
    name: {key: lv["beta"] for key, lv in pred["levels"].items()
           if lv["beta"] is not None}
    for name, pred in PREDICTORS.items()
}

#: 100 divided by the sum of the largest beta in each predictor. The paper
#: states the construction ("weighted to the maximum sum of 100 points") and
#: never states the number; this is that sentence taken literally, and all
#: thirteen published point values reproduce from it under round(beta * d).
POINTS_DIVISOR: float = _MODEL["points_divisor"]

#: 25-point intervals except the first, which is the absence of every risk
#: predictor: 0, 1-25, 26-50, 51-75, 76-100.
BANDS: list[dict[str, Any]] = _MODEL["bands"]

#: One row per band: n, recurrences, disease-free survival at years 1-5 with
#: the calculator's own 95% intervals, and the conditional annual recurrence
#: risk at years 1-5.
OUTCOME: list[dict[str, Any]] = _MODEL["outcome"]

MAX_SCORE = 100
COHORT = _MODEL["cohort"]

MODEL_CITATION = (
    "Cibula D, Dostalek L, Jarkovsky J, et al. The annual recurrence risk "
    "model for tailored surveillance strategy in patients with cervical "
    "cancer. Eur J Cancer. 2021;158:111-122. doi:10.1016/j.ejca.2021.09.008 "
    "(points schedule from Table 2; outcome grid re-derived from the ESGO "
    "calculator's own 4,343-row cohort)"
)

SCOPE = (
    "Early-stage cervical cancer treated by primary surgery: SCCAN "
    "consortium, 4,343 patients at 20 centres, 2007-2016. All five inputs are "
    "surgical pathology, so the model cannot be run before surgery and does "
    "not apply to patients treated with definitive chemoradiation. Outcome is "
    "disease-free survival from the date of surgery. Harrell's C 0.735 "
    "(95% CI 0.713; 0.757)."
)

# Aliases accepted for histotype. Deliberately short: "adeno" is NOT accepted,
# because it is equally close to adenocarcinoma and adenosquamous, and a
# silently wrong guess between the two is a 4-point error.
_HISTOTYPE_ALIASES = {
    "squamous": "squamous",
    "squamous cell": "squamous",
    "squamous cell carcinoma": "squamous",
    "scc": "squamous",
    "adenocarcinoma": "adenocarcinoma",
    "adenosquamous": "adenosquamous",
    "adenosquamous carcinoma": "adenosquamous",
    "neuroendocrine": "neuroendocrine",
    "other": "other",
}

_BAND_BY_INDEX = {b["index"]: b for b in BANDS}

assert len(BANDS) == 5 and len(OUTCOME) == 5, "the outcome grid is not 5 bands"
assert sum(max(v.values()) for v in POINTS.values()) == MAX_SCORE, (
    "the worst patient no longer scores 100"
)


def _normalise_histotype(histotype: str) -> str:
    key = str(histotype).strip().lower().replace("_", " ")
    if key not in _HISTOTYPE_ALIASES:
        raise ValueError(
            f"histotype must be one of {sorted(POINTS['histotype'])}, "
            f"got {histotype!r}"
        )
    return _HISTOTYPE_ALIASES[key]


def diameter_level(tumour_diameter_cm: float) -> str:
    """Table 2's four diameter bands, in centimetres.

    The paper bands in cm (< 0.5, 0.5-1.99, 2-3.99, >= 4) and the deployed
    calculator labels the same four levels in mm (< 5, 5-19, 20-39, >= 40).
    They are the same cut-points; this takes cm, as the paper does.

    The measurement is the **maximal pathologic** diameter from the resection
    specimen, not a pre-operative imaging measurement.
    """
    size = float(tumour_diameter_cm)
    if size < 0:
        raise ValueError(f"tumour_diameter_cm must be >= 0, got {size}")
    if size < 0.5:
        return "<0.5cm"
    if size < 2:
        return "0.5-1.99cm"
    if size < 4:
        return "2-3.99cm"
    return ">=4cm"


def node_level(positive_pelvic_nodes: int | None) -> str:
    """Table 2's node levels. `None` means not assessed and scores zero.

    "0 / not assessed" is one level in the published model, so a patient with
    no pelvic lymphadenectomy is scored as node-negative. That is the paper's
    choice, not ours.
    """
    if positive_pelvic_nodes is None:
        return "0_or_not_assessed"
    count = int(positive_pelvic_nodes)
    if count != float(positive_pelvic_nodes) or count < 0:
        raise ValueError(
            "positive_pelvic_nodes must be a non-negative whole number or "
            f"None for 'not assessed', got {positive_pelvic_nodes!r}"
        )
    if count == 0:
        return "0_or_not_assessed"
    if count == 1:
        return "1"
    if count == 2:
        return "2"
    return ">=3"


def grade_level(grade: int | str) -> str:
    """Table 2's grade levels: 1, 2 or 3, and nothing else.

    Unlike the node and LVSI rows, grade has no "not assessed" level. The
    authors multiply imputed missing grade when fitting, which cannot be
    reproduced for a single patient, so an unknown grade is refused rather
    than quietly scored as grade 1.
    """
    key = str(grade).strip()
    if key not in POINTS["grade"]:
        raise ValueError(
            f"grade must be one of {sorted(POINTS['grade'])}; Table 2 has no "
            f"'not assessed' level for grade, unlike positive_pelvic_nodes "
            f"and lvsi. Got {grade!r}"
        )
    return key


def band_for(score: int) -> dict[str, Any]:
    """The risk band a points total falls in."""
    for band in BANDS:
        if band["low"] <= score <= band["high"]:
            return band
    raise ValueError(f"score {score} falls outside 0-{MAX_SCORE}")


def arrm_points(
    *,
    histotype: str,
    tumour_diameter_cm: float,
    grade: int | str,
    positive_pelvic_nodes: int | None,
    lvsi: bool | None,
) -> dict[str, Any]:
    """The five point assignments and their sum (0-100)."""
    levels = {
        "histotype": _normalise_histotype(histotype),
        "tumour_diameter": diameter_level(tumour_diameter_cm),
        "grade": grade_level(grade),
        "positive_pelvic_nodes": node_level(positive_pelvic_nodes),
        "lvsi": "yes" if lvsi else "no_or_not_assessed",
    }
    earned = {name: POINTS[name][key] for name, key in levels.items()}
    return {"levels": levels, "points": earned, "score": sum(earned.values())}


def cibula_arrm_predict(
    *,
    histotype: str,
    tumour_diameter_cm: float,
    grade: int | str,
    positive_pelvic_nodes: int | None = None,
    lvsi: bool | None = None,
) -> dict[str, Any]:
    """ARRM risk points (0-100), the risk band, and that band's outcome.

    `histotype` is one of squamous / adenocarcinoma / adenosquamous /
    neuroendocrine / other. `tumour_diameter_cm` is the maximal **pathologic**
    diameter. `grade` is 1, 2 or 3 and is required.

    `positive_pelvic_nodes` and `lvsi` both default to None, which the
    published model treats as identical to negative, see the module docstring.
    That default is the paper's pooling and not a convenience; the returned
    `notes` flag it whenever it is used.

    The outcome figures are Kaplan-Meier estimates over the derivation cohort's
    own band, not predictions for an individual, and are named accordingly.
    `annual_recurrence_risk_in_derivation` is *conditional*: year 3 is the risk
    for someone already two years recurrence-free.
    """
    scored = arrm_points(
        histotype=histotype,
        tumour_diameter_cm=tumour_diameter_cm,
        grade=grade,
        positive_pelvic_nodes=positive_pelvic_nodes,
        lvsi=lvsi,
    )
    score = scored["score"]
    band = band_for(score)
    row = OUTCOME[band["index"]]

    reliable = row["arrm_reliable_through_year"]
    arrm = [v if year <= reliable else None
            for year, v in enumerate(row["arrm_percent"], start=1)]

    notes = [
        "points from Table 2; outcome is the derivation cohort's observed "
        "Kaplan-Meier result for this band, not an individual prediction",
        "annual recurrence risk is conditional on being recurrence-free at "
        "the start of the year",
    ]
    if positive_pelvic_nodes is None:
        notes.append(
            "pelvic nodes not assessed, the published model pools that with "
            "node-negative, so this scored 0 points for nodes"
        )
    if lvsi is None:
        notes.append(
            "LVSI not assessed, the published model pools that with "
            "LVSI-negative, so this scored 0 points for LVSI"
        )
    if reliable < 5:
        notes.append(
            f"the paper stops the landmark analysis for this band at year "
            f"{reliable} ({row['n']} patients, {row['n_recurrences']} "
            f"recurrences); later years are reported as None"
        )

    return {
        "score": score,
        "max_score": MAX_SCORE,
        "points": scored["points"],
        "levels": scored["levels"],
        "band": band["index"],
        "band_label": band["label"],
        "band_n_in_derivation": row["n"],
        "band_recurrences_in_derivation": row["n_recurrences"],
        "observed_dfs_in_derivation": row["dfs_percent"],
        # strict=True: the two CI lists and dfs_percent must stay the same
        # length. Without it a data file edited to five survival values and
        # four lower bounds would silently return four intervals for five
        # estimates, fewer numbers, no error, and nothing downstream to
        # notice.
        "observed_dfs_ci_in_derivation": [
            [lo, hi] for lo, hi in zip(row["dfs_ci_low_percent"],
                                       row["dfs_ci_high_percent"], strict=True)
        ],
        "annual_recurrence_risk_in_derivation": arrm,
        "arrm_reliable_through_year": reliable,
        "risk": None,  # a points score with a band lookup, not a probability
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": DISEASE,
        "interpretation": (
            f"{score}/100 points, {band['label']}. Five-year disease-free "
            f"survival in this band was {row['dfs_percent'][4]}% among "
            f"{row['n']} patients ({row['n_recurrences']} recurrences). "
            "Annual recurrence risk: "
            + ", ".join(
                f"year {y} {v}%" for y, v in enumerate(arrm, start=1)
                if v is not None
            )
            + ". The paper sets no action threshold: it concludes that "
            "\"surveillance strategy can be consequently adopted individually "
            "using the preferred threshold for an acceptable annual risk\". "
            "It uses 1% descriptively, the lowest group stays under it "
            "throughout, and the middle groups fall under it at years three "
            "and four, but 1% is not a recommendation the authors make."
        ),
        "citation": MODEL_CITATION,
        "scope": SCOPE,
        "notes": "; ".join(notes),
    }
