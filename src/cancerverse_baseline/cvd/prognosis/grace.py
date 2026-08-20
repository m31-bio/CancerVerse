"""GRACE risk score — in-hospital mortality in acute coronary syndromes.

Equation source
---------------
Granger CB, Goldberg RJ, Dabbous O, et al. "Predictors of Hospital Mortality in
the Global Registry of Acute Coronary Events." Arch Intern Med.
2003;163(19):2345-2353. Figure 4 (nomogram).

Eight predictors, each contributing integer points; the total maps to an
in-hospital death probability through a published lookup.

    Killip class      I 0    II 20   III 39   IV 59
    SBP (mm Hg)       <=80 58, 80-99 53, 100-119 43, 120-139 34,
                      140-159 24, 160-199 10, >=200 0
    Heart rate (bpm)  <=50 0, 50-69 3, 70-89 9, 90-109 15,
                      110-149 24, 150-199 38, >=200 46
    Age (y)           <=30 0, 30-39 8, 40-49 25, 50-59 41, 60-69 58,
                      70-79 75, 80-89 91, >=90 100
    Creatinine mg/dL  0-0.39 1, 0.40-0.79 4, 0.80-1.19 7, 1.20-1.59 10,
                      1.60-1.99 13, 2.00-3.99 21, >4.0 28
    Cardiac arrest at admission   39
    ST-segment deviation          28
    Elevated cardiac enzymes      14

Note the SBP scale runs BACKWARD — low blood pressure scores highest (<=80
mm Hg is 58 points, >=200 is 0). It encodes cardiogenic shock, not
hypertension.

BAND BOUNDARIES ARE AMBIGUOUS AS PRINTED — read this before touching them
---------------------------------------------------------------------------
The nomogram prints bands like "80-99" then "100-119". Taken literally, SBP of
exactly 100 lands in the 100-119 band and scores 43. **The paper's own worked
examples say otherwise**: it assigns SBP 100 -> 53 (the "80-99" band), SBP 80 ->
58 (the "<=80" band), and creatinine 0.40 -> 1 (the "0-0.39" band).

So each printed band's true upper edge is the NEXT band's printed lower label,
inclusive. Coded literally, this model returns the wrong points for boundary
values -- and 100 mm Hg is one of the most common systolic readings there is.
The two published worked examples are the only thing that disambiguates this,
which is exactly why both are pinned as parity tests.

The explicitly-signed end bands (`<=80`, `>=200`, `>4.0`) are unambiguous and
are honoured as printed.

Version
-------
This is the ORIGINAL 2003 points nomogram for **in-hospital** mortality. Two
other things are also called "GRACE" and are NOT this:
  - Fox KAA et al., BMJ 2006 — 6-month post-discharge mortality, different points
  - GRACE 2.0 — replaced the points system with a non-linear continuous model
Using this score where a guideline specifies GRACE 2.0 will give different
numbers. The registry records which version is implemented.

Creatinine is in mg/dL; multiply by 88.4 for umol/L.
"""

from __future__ import annotations

from bisect import bisect_right

AXIS = "prognosis"
MODEL_ID = "grace"

KILLIP_POINTS = {1: 0, 2: 20, 3: 39, 4: 59}
CARDIAC_ARREST_POINTS = 39
ST_DEVIATION_POINTS = 28
ELEVATED_ENZYMES_POINTS = 14

CREATININE_MG_DL_TO_UMOL_L = 88.4

# (upper bound INCLUSIVE, points), per the worked examples — see the docstring.
# The final entry of each tuple set is the open-ended top band.
_SBP_BANDS = ((80.0, 58), (100.0, 53), (120.0, 43), (140.0, 34),
              (160.0, 24), (199.999, 10))
_SBP_TOP = 0            # >= 200
_HR_BANDS = ((50.0, 0), (70.0, 3), (90.0, 9), (110.0, 15),
             (150.0, 24), (199.999, 38))
_HR_TOP = 46            # >= 200
_AGE_BANDS = ((30.0, 0), (40.0, 8), (50.0, 25), (60.0, 41),
              (70.0, 58), (80.0, 75), (89.999, 91))
_AGE_TOP = 100          # >= 90
_CREAT_BANDS = ((0.40, 1), (0.80, 4), (1.20, 7), (1.60, 10),
                (2.00, 13), (4.00, 21))
_CREAT_TOP = 28         # > 4.0

# Published risk lookup: total points -> probability of in-hospital death.
RISK_TABLE = (
    (60, 0.002), (70, 0.003), (80, 0.004), (90, 0.006), (100, 0.008),
    (110, 0.011), (120, 0.016), (130, 0.021), (140, 0.029), (150, 0.039),
    (160, 0.054), (170, 0.073), (180, 0.098), (190, 0.13), (200, 0.18),
    (210, 0.23), (220, 0.29), (230, 0.36), (240, 0.44), (250, 0.52),
)

MODEL_CITATION = (
    "Granger CB, Goldberg RJ, Dabbous O, et al. Arch Intern Med. "
    "2003;163(19):2345-2353, Figure 4 (GRACE in-hospital mortality nomogram)."
)


def _band_points(value: float, bands, top: int) -> int:
    """Upper-inclusive bands, as disambiguated by the paper's worked examples."""
    for upper, points in bands:
        if value <= upper:
            return points
    return top


def sbp_points(sbp: float) -> int:
    return _band_points(sbp, _SBP_BANDS, _SBP_TOP)


def heart_rate_points(heart_rate: float) -> int:
    return _band_points(heart_rate, _HR_BANDS, _HR_TOP)


def age_points(age: float) -> int:
    return _band_points(age, _AGE_BANDS, _AGE_TOP)


def creatinine_points(creatinine_mg_dl: float) -> int:
    return _band_points(creatinine_mg_dl, _CREAT_BANDS, _CREAT_TOP)


def risk_from_points(points: int) -> float:
    """Interpolate the published points -> in-hospital mortality lookup.

    The table is printed at 10-point intervals; values between rows are
    linearly interpolated, and the ends are clamped to the published bounds
    (<=60 -> <=0.2%, >=250 -> >=52%).
    """
    thresholds = [t for t, _ in RISK_TABLE]
    if points <= thresholds[0]:
        return RISK_TABLE[0][1]
    if points >= thresholds[-1]:
        return RISK_TABLE[-1][1]
    i = bisect_right(thresholds, points) - 1
    x0, y0 = RISK_TABLE[i]
    x1, y1 = RISK_TABLE[i + 1]
    return y0 + (y1 - y0) * (points - x0) / (x1 - x0)


def grace_predict(
    *,
    killip_class: int,
    sbp: float,
    heart_rate: float,
    age: float,
    creatinine_mg_dl: float,
    cardiac_arrest_at_admission: bool = False,
    st_segment_deviation: bool = False,
    elevated_cardiac_enzymes: bool = False,
) -> dict:
    """GRACE score and in-hospital mortality risk for an ACS presentation."""
    if killip_class not in KILLIP_POINTS:
        raise ValueError(f"killip_class must be 1-4, got {killip_class}")
    for name, value in (
        ("sbp", sbp),
        ("heart_rate", heart_rate),
        ("age", age),
        ("creatinine_mg_dl", creatinine_mg_dl),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be > 0, got {value}")

    components = {
        "killip": KILLIP_POINTS[killip_class],
        "sbp": sbp_points(sbp),
        "heart_rate": heart_rate_points(heart_rate),
        "age": age_points(age),
        "creatinine": creatinine_points(creatinine_mg_dl),
        "cardiac_arrest": CARDIAC_ARREST_POINTS if cardiac_arrest_at_admission else 0,
        "st_deviation": ST_DEVIATION_POINTS if st_segment_deviation else 0,
        "elevated_enzymes": ELEVATED_ENZYMES_POINTS if elevated_cardiac_enzymes else 0,
    }
    score = sum(components.values())
    return {
        "score": score,
        "risk": risk_from_points(score),
        "components": components,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "cvd",
        "citation": MODEL_CITATION,
        "notes": "GRACE 2003 in-hospital mortality nomogram; not the BMJ 2006 "
        "6-month score and not GRACE 2.0",
    }
