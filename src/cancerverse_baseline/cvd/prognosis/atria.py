"""ATRIA stroke risk score (Singer et al., J Am Heart Assoc 2013).

Equation source
----------------
Singer DE, Chang Y, Borowsky LH, et al. "A New Risk Scheme to Predict
Ischemic Stroke and Other Thromboembolism in Atrial Fibrillation: The ATRIA
Study Stroke Risk Score." J Am Heart Assoc. 2013;2(3):e000250. Table 3
(point table) and Table 4 (rate-by-score band), PMC3698792, CC BY-NC.

Table 3, transcribed exactly (age enters through an age x prior-stroke
interaction, not one age term plus a stroke flag):

                          no prior stroke   prior stroke
    Age >= 85                    6               9
    Age 75-84                    5               7
    Age 65-74                    3               7
    Age < 65                     0               8
    Female                       1               1
    Diabetes                     1               1
    CHF                          1               1
    Hypertension                 1               1
    Proteinuria                  1               1
    eGFR < 45 or ESRD            1               1

Two disjoint ranges result: 0-12 with no prior stroke, 7-15 with one.

Risk banding is Table 4's own category boundaries (<=5 low / 1%/yr, 6
moderate / 1-2%/yr, >=7 high / 2%/yr), not a value we chose. As with
CHA2DS2-VASc in this package, no raw per-point annual rate is shipped: Table 4
gives event counts and person-years per point, which is a finer claim than the
three-way banding, and different external validations of ATRIA have not
agreed on point-level rates the way they agree on the three bands.

Proteinuria and eGFR are both routine-chemistry findings, not a send-out
biomarker panel, what separates this from ABC-stroke (Hijazi et al. 2016),
which needs GDF-15, high-sensitivity troponin and NT-proBNP and was set aside
for exactly that reason (see registry `atria_stroke_2013.tier_note`).
"""

from __future__ import annotations

AXIS = "prognosis"
MODEL_ID = "atria_stroke_2013"

#: (age >= this) -> (points without prior stroke, points with prior stroke).
#: Checked from the top: the first band an age qualifies for is the one used.
_AGE_BANDS = (
    (85, 6, 9),
    (75, 5, 7),
    (65, 3, 7),
)
#: Age < 65: 0 points without prior stroke, 8 points with one.
_AGE_UNDER_65 = (0, 8)

MODEL_CITATION = (
    "Singer DE et al. J Am Heart Assoc. 2013;2(3):e000250 (ATRIA stroke risk score)."
)


def _age_points(age: float, *, prior_stroke: bool) -> int:
    if age < 0:
        raise ValueError(f"age must be >= 0, got {age}")
    for threshold, no_stroke_pts, stroke_pts in _AGE_BANDS:
        if age >= threshold:
            return stroke_pts if prior_stroke else no_stroke_pts
    return _AGE_UNDER_65[1 if prior_stroke else 0]


def atria_score(
    *,
    age: float,
    prior_stroke: bool,
    female: bool,
    diabetes: bool,
    heart_failure: bool,
    hypertension: bool,
    proteinuria: bool,
    egfr_under_45_or_esrd: bool,
) -> int:
    """Total ATRIA points. 0-12 with no prior stroke, 7-15 with one."""
    return (
        _age_points(age, prior_stroke=prior_stroke)
        + (1 if female else 0)
        + (1 if diabetes else 0)
        + (1 if heart_failure else 0)
        + (1 if hypertension else 0)
        + (1 if proteinuria else 0)
        + (1 if egfr_under_45_or_esrd else 0)
    )


def risk_category(score: int) -> str:
    """Table 4's own three-way band: <=5 low, 6 moderate, >=7 high."""
    if score <= 5:
        return "low"
    if score == 6:
        return "moderate"
    return "high"


def atria_predict(
    *,
    age: float,
    prior_stroke: bool,
    female: bool,
    diabetes: bool,
    heart_failure: bool,
    hypertension: bool,
    proteinuria: bool,
    egfr_under_45_or_esrd: bool,
) -> dict:
    """ATRIA score and risk band for stroke in atrial fibrillation."""
    score = atria_score(
        age=age,
        prior_stroke=prior_stroke,
        female=female,
        diabetes=diabetes,
        heart_failure=heart_failure,
        hypertension=hypertension,
        proteinuria=proteinuria,
        egfr_under_45_or_esrd=egfr_under_45_or_esrd,
    )
    return {
        "score": score,
        "risk_category": risk_category(score),
        "risk": None,  # banded by Table 4, not a per-point rate; see module docstring
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "cvd",
        "citation": MODEL_CITATION,
        "notes": ("0-12 points with no prior stroke, 7-15 with one; "
                 "bands: <=5 low, 6 moderate, >=7 high (Table 4)"),
    }
