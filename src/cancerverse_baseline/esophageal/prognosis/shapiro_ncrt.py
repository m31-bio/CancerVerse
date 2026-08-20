"""Shapiro nomogram, overall survival after neoadjuvant chemoradiotherapy
plus surgery for oesophageal or junctional cancer.

Equation source
----------------
Shapiro J, van Klaveren D, Lagarde SM, Toxopeus ELA, van der Gaast A,
Hulshof MCCM, Wijnhoven BPL, van Berge Henegouwen MI, Steyerberg EW,
van Lanschot JJB. "Prediction of survival in patients with oesophageal or
junctional cancer receiving neoadjuvant chemoradiotherapy and surgery."
Br J Surg. 2016;103(8):1039-1047. doi:10.1002/bjs.10142, PMID 27115731.

626 patients treated with CROSS-regimen nCRT plus surgery at Erasmus MC
Rotterdam and the AMC Amsterdam (CROSS-I, CROSS-II and post-CROSS 2009-2013).
Transcribed from the article on 2026-08-17.

Note the first author. The registry's earlier candidate note credited this
paper to "Anderegg MCJ et al", that is wrong, and was corrected on
2026-08-17 against Crossref and the PDF itself. Anderegg is a different
Amsterdam group publishing in the same area.

Why this is implementable when four cervical nomogram papers were not
-----------------------------------------------------------------------
Every previous nomogram this project examined printed its points-to-
probability step only as a drawn axis, so `S(t) = S0(t)^exp(Xb)` was missing
its baseline and no probability could be stated. This one prints the axis
NUMERICALLY. Fig. 1's total-points scale carries tick labels and both survival
scales carry a value under every tick:

    total points      0   2   4   6   8  10  12  14  16
    1-year survival  91  88  85  81  75  68  60  51  41
    5-year survival  70  62  53  43  33  23  14   7   3

That is a complete lookup, not a picture to measure with a ruler. Read from
the extracted text and independently confirmed against renders of page 1043
at 300 and 600 dpi, the same two-reading rule used for the MSK rectal
supplement.

The paper's own worked example is reproduced by the parity test: cN1 with a
complete response (ypT0, ypN0) totals 2 points, "corresponding to estimated
1- and 5-year survival rates of 88 and 62 per cent respectively".

FOUR REACHABLE SCORES HAVE NO PUBLISHED SURVIVAL, and this module returns
None for them rather than inventing a number
---------------------------------------------------------------------------
The tick labels are at even totals only. Every point value is even except
ypN2, which is 5, so any patient with ypN2 lands on an odd total, and the
reachable set 0, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16 contains four values
(5, 7, 9, 11) with no printed survival.

That is not a small corner: ypN2 is 3-6 positive nodes, and it was 60 of 626
patients (9.6%) in the derivation cohort. Roughly one patient in ten gets a
band with no published outcome.

It would be easy to fill the gap and wrong to do it. The axis is a genuine Cox
form and it fits well: taking S(p) = S0^exp(k*p) with S0 = 0.91 and 0.70 at
one and five years, a shared k of 0.1411 reproduces all eighteen printed
values with a root-mean-square error of 0.36 percentage points. Interpolating
the four missing totals from that fit would look authoritative and would be
this project generating numbers rather than reading them. So
`survival_available` is False for those scores and both survival figures come
back None, with the reason in `notes`.

(Worth recording because it is a real inconsistency in the source: the Methods
say the points were made by "multiplying the original coefficients of the
multivariable Cox model by ten and rounding the result to the lowest whole
number", which implies k = 0.1. The fitted k is 0.1411, nearer 1/7. The final
model's coefficients are printed nowhere. Table 2 is the FULL model, whose
hazard ratios do not reproduce these points, so the discrepancy cannot be
resolved from the article, and nothing here depends on resolving it.)

What this model is worth, stated plainly
-------------------------------------------
Discrimination is weak: c-index 0.63 at internal validation, 0.62 and 0.63 on
cross-validation between the two centres. The authors are direct about it,
predicted survival showed "only moderate correlation with observed survival,
emphasizing the need for new prognostic factors to improve survival
prediction".

It has nevertheless been externally validated properly, which almost nothing
else in this cell has: Goense L, Merrell KW, Arnett AL, et al. Validation of a
Nomogram Predicting Survival After Trimodality Therapy for Esophageal Cancer.
Ann Thorac Surg. 2018;106(5):1541-1547. PMID 29932887. 975 patients across
three academic centres, C-statistic 0.61 for overall survival (against 0.63
in Shapiro's own cohort) and 0.64 for progression-free survival, with
calibration described as accurate.

**A better model for this cell exists and cannot be used.** The AUGIS Survival
Predictor (Ann Surg Oncol, PMC9831040) was built on 6,399 oesophagectomies in
England and Wales with a 5-year time-dependent AUC of 83.9%, far above this.
It is a random survival forest, a few thousand decision trees, no coefficient
table, nothing to transcribe. This model is therefore the best IMPLEMENTABLE
model for the cell, not the best model, and `registry/models.yaml` says so.

Scope
-----
Oesophageal or junctional carcinoma treated with CROSS-regimen neoadjuvant
chemoradiotherapy FOLLOWED BY RESECTION. Two of the three inputs are
post-resection pathology, so this cannot be run before surgery and says
nothing about whether to operate. Unlike `chau_eg`, squamous histology is
well represented (139 of 626, 22.2%; adenocarcinoma 481, 76.8%).

Staging editions are not interchangeable and the paper mixes them: cN is UICC
TNM **sixth** edition (cN0/cN1 only, a binary, not the modern N0-N3), while
ypT and ypN are **seventh** edition. A pipeline feeding eighth-edition
categories, or a three-level cN, is feeding the model something it was never
fitted on.
"""

from __future__ import annotations

from typing import Any

AXIS = "prognosis"
MODEL_ID = "shapiro_ncrt"
DISEASE = "esophageal"

#: Fig. 1's three predictor scales. UICC TNM 6th edition for cN, 7th for ypT
#: and ypN, see the module docstring; they are not interchangeable.
#: ypT1 and ypT2 share one point value, as the figure's "ypT1/pT2" tick shows.
POINTS: dict[str, dict[str, int]] = {
    "cn": {"cN0": 0, "cN1": 2},
    "ypt": {"ypT0": 0, "ypT1": 2, "ypT2": 2, "ypT3": 4},
    "ypn": {"ypN0": 0, "ypN1": 4, "ypN2": 5, "ypN3": 10},
}

MAX_POINTS = 16

#: Fig. 1's total-points axis and the two survival scales beneath it, read
#: from the figure. Ticks are at EVEN totals only; see SCORES_WITHOUT_SURVIVAL.
SURVIVAL_BY_POINTS: dict[int, dict[str, float]] = {
    0:  {"one_year_pct": 91.0, "five_year_pct": 70.0},
    2:  {"one_year_pct": 88.0, "five_year_pct": 62.0},
    4:  {"one_year_pct": 85.0, "five_year_pct": 53.0},
    6:  {"one_year_pct": 81.0, "five_year_pct": 43.0},
    8:  {"one_year_pct": 75.0, "five_year_pct": 33.0},
    10: {"one_year_pct": 68.0, "five_year_pct": 23.0},
    12: {"one_year_pct": 60.0, "five_year_pct": 14.0},
    14: {"one_year_pct": 51.0, "five_year_pct": 7.0},
    16: {"one_year_pct": 41.0, "five_year_pct": 3.0},
}

#: Reachable totals with no printed survival. All four arise from ypN2 = 5,
#: the only odd point value in the model. 9.6% of the derivation cohort.
SCORES_WITHOUT_SURVIVAL = (5, 7, 9, 11)

DISCRIMINATION = {
    "internal_c_index": 0.63,
    "cross_validation_c_index": (0.62, 0.63),
    "external_c_index_os": 0.61,
    "external_c_index_pfs": 0.64,
    "external_n": 975,
    "external_centres": 3,
}

COHORT = {
    "n": 626, "n_screened": 661,
    "adenocarcinoma": 481, "squamous": 139,
    "cN0": 182, "cN1": 430,
    "ypT0": 187, "ypT1": 89, "ypT2": 106, "ypT3": 240,
    "ypN0": 400, "ypN1": 146, "ypN2": 60, "ypN3": 20,
}

MODEL_CITATION = (
    "Shapiro J, van Klaveren D, Lagarde SM, et al. Prediction of survival in "
    "patients with oesophageal or junctional cancer receiving neoadjuvant "
    "chemoradiotherapy and surgery. Br J Surg. 2016;103(8):1039-1047. "
    "doi:10.1002/bjs.10142 (points and survival axes from Fig. 1); externally "
    "validated in Goense L et al, Ann Thorac Surg 2018;106(5):1541-1547, "
    "PMID 29932887"
)

SCOPE = (
    "Oesophageal or oesophagogastric junctional carcinoma treated with "
    "CROSS-regimen neoadjuvant chemoradiotherapy FOLLOWED BY RESECTION; 626 "
    "patients at Erasmus MC Rotterdam and AMC Amsterdam. Two of three inputs "
    "are post-resection pathology, so this cannot be run pre-operatively and "
    "says nothing about whether to operate. Squamous histology is well "
    "represented (22.2%), unlike chau_eg. Discrimination is WEAK, c-index "
    "0.63 internal, 0.61 on external validation in 975 patients, and the "
    "authors state predicted survival showed 'only moderate correlation with "
    "observed survival'. The AUGIS Survival Predictor is a substantially "
    "better model for this question (5-year AUC 83.9%) and is a random "
    "survival forest with no closed form, so this is the best IMPLEMENTABLE "
    "model rather than the best model. Staging editions differ by variable: "
    "cN is UICC TNM 6th edition (binary cN0/cN1), ypT and ypN are 7th."
)


def _level(kind: str, value: str) -> str:
    key = str(value).strip()
    table = POINTS[kind]
    if key not in table:
        raise ValueError(
            f"{kind} must be one of {sorted(table)}, got {value!r}. Note the "
            f"staging edition: cN is UICC TNM 6th edition and is BINARY "
            f"(cN0/cN1 only), while ypT and ypN are 7th edition."
        )
    return key


def shapiro_points(
    *, cn_category: str, ypt_category: str, ypn_category: str
) -> dict[str, Any]:
    """The three point assignments and their total (0-16)."""
    levels = {
        "cn": _level("cn", cn_category),
        "ypt": _level("ypt", ypt_category),
        "ypn": _level("ypn", ypn_category),
    }
    earned = {k: POINTS[k][v] for k, v in levels.items()}
    return {"levels": levels, "points": earned, "total": sum(earned.values())}


def shapiro_ncrt_predict(
    *, cn_category: str, ypt_category: str, ypn_category: str
) -> dict[str, Any]:
    """One- and five-year overall survival after nCRT plus surgery.

    `cn_category` is ``"cN0"`` or ``"cN1"`` (UICC TNM 6th edition, binary).
    `ypt_category` is ``"ypT0"``-``"ypT3"`` and `ypn_category` is
    ``"ypN0"``-``"ypN3"``, both UICC TNM 7th edition, both scored on the
    resection specimen after neoadjuvant chemoradiotherapy.

    Returns the total points and the published survival at that total. For
    the four reachable totals the figure does not label (5, 7, 9, 11, every
    ypN2 patient, 9.6% of the derivation cohort) both survival figures are
    **None**: the paper prints no value there and this module does not
    interpolate one. `survival_available` says which case you are in.

    `risk` is None throughout, this returns published survival percentages
    for a points total, not a fitted individual probability.
    """
    scored = shapiro_points(
        cn_category=cn_category,
        ypt_category=ypt_category,
        ypn_category=ypn_category,
    )
    total = scored["total"]
    row = SURVIVAL_BY_POINTS.get(total)
    available = row is not None

    notes = [
        "survival read from the Fig. 1 axes, which the paper prints "
        "numerically, not measured off a drawn scale",
        "two of three inputs are post-resection pathology, so this is not a "
        "pre-operative model",
        "staging editions differ: cN is UICC TNM 6th edition and binary, "
        "ypT and ypN are 7th edition",
        "discrimination is weak (c-index 0.63 internal, 0.61 external); the "
        "AUGIS random survival forest is a better model for this question but "
        "has no closed form to transcribe",
    ]
    if not available:
        notes.append(
            f"NO PUBLISHED SURVIVAL AT {total} POINTS. Fig. 1 labels even "
            f"totals only, and ypN2 is the model's one odd point value, so "
            f"every ypN2 patient lands on an unlabelled tick "
            f"({', '.join(str(s) for s in SCORES_WITHOUT_SURVIVAL)} points; "
            f"9.6% of the derivation cohort). Interpolating would mean "
            f"inventing a number the paper does not print, so both survival "
            f"figures are None"
        )

    return {
        "total_points": total,
        "max_points": MAX_POINTS,
        "points": scored["points"],
        "levels": scored["levels"],
        "survival_available": available,
        "one_year_survival_pct": row["one_year_pct"] if available else None,
        "five_year_survival_pct": row["five_year_pct"] if available else None,
        "risk": None,  # published survival for a points total, not a fitted probability
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": DISEASE,
        "interpretation": (
            f"{total}/{MAX_POINTS} points. Published survival after nCRT plus "
            f"surgery: {row['one_year_pct']}% at one year and "
            f"{row['five_year_pct']}% at five years."
            if available else
            f"{total}/{MAX_POINTS} points. The paper publishes no survival at "
            f"this total. Fig. 1 labels even totals only and ypN2 scores 5, "
            f"so every ypN2 patient falls between labelled ticks. No figure "
            f"is returned rather than an interpolated one."
        ),
        "citation": MODEL_CITATION,
        "scope": SCOPE,
        "notes": "; ".join(notes),
    }
