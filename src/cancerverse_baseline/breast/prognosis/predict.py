"""PREDICT Breast v2.2, prognosis and adjuvant treatment benefit.

Equation source
---------------
Model by Paul Pharoah (University of Cambridge). Transcribed from the
MIT-licensed reference implementation the Winton Centre publishes as an
OpenCPU package: https://github.com/WintonCentre/predictv30r, `R/benefits22.R`
(v2.2). Model background: Candido dos Reis FJ, et al. "An updated PREDICT
breast cancer prognostication and treatment benefit prediction model with
independent validation." Breast Cancer Res. 2017;19(1):58 (PMC5440946); 2024
radiotherapy update in npj Breast Cancer.

Why this model matters here
---------------------------
It is the only model in this repo that spans TWO axes: it predicts survival
(prognosis) AND the absolute benefit of each adjuvant treatment combination
(response). The NHS uses it ~30,000 times a month to decide adjuvant chemo.

Structure, a competing-risks model, not a single regression:

  1. Two prognostic indices, each a log-hazard:
       mi = other-cause mortality (age only)
       pi = breast-cancer-specific mortality (fractional polynomials in age,
            size and nodes, plus grade / screen-detection / HER2 / Ki67)
     The age and size terms use DIFFERENT fractional-polynomial transforms for
     ER-positive and ER-negative disease, not merely different coefficients.

  2. Two published cumulative baseline hazards, one per cause, each its own
     closed-form function of time in years.

  3. Treatment effects enter `pi` as additive log-hazard-ratios. Hormone
     therapy has a time-varying effect: -0.3857 for years 1-10, then an extra
     -0.26 for years 11-15 (the ATLAS/aTTom extended-endocrine result).

  4. Competing-risk integration year by year, apportioning all-cause mortality
     between the two causes in proportion to their annual hazards.

Radiotherapy is present in the reference source but gated off (`r.enabled = 0`)
in v2.2, so its terms evaluate to zero. We mirror that exactly rather than
silently enabling a pathway the reference disables.
"""

from __future__ import annotations

import math

AXIS = "prognosis"
MODEL_ID = "predict_breast"

MAX_YEARS = 15

# --- other-cause mortality ---
OTHER_AGE_BETA = 0.0698252
OTHER_AGE_CENTER = 34.23391957
OTHER_BASELINE = (-6.052919, 1.079863, 0.3255321)

# --- breast-cancer-specific prognostic index, ER-positive ---
ER_POS = {
    "age_mfp1_center": 0.0287449295,
    "age_beta1": 34.53642,
    "age_mfp2_center": 0.0510121013,
    "age_beta2": -34.20342,
    "size_center": 1.545233938,
    "size_beta": 0.7530729,
    "nodes_center": 1.387566896,
    "nodes_beta": 0.7060723,
    "grade_beta": 0.746655,
    "screen_beta": -0.22763366,
}

# --- breast-cancer-specific prognostic index, ER-negative ---
ER_NEG = {
    "age_center": 56.3254902,
    "age_beta1": 0.0089827,
    "size_center": 0.5090456276,
    "size_beta": 2.093446,
    "nodes_center": 1.086916249,
    "nodes_beta": 0.6260541,
    "grade_beta": 1.129091,
    "screen_beta": 0.0,
}

HER2_BETA = {1: 0.2413, 0: -0.0762, 9: 0.0}
KI67_BETA = {1: 0.14904, 0: -0.11333, 9: 0.0}

# --- treatment log-hazard-ratios ---
CHEMO_BETA = {0: 0.0, 2: -0.248, 3: -0.446}  # generation of regimen
HORMONE_BETA = -0.3857
HORMONE_EXTENDED_BETA = -0.26  # years 11-15, ATLAS/aTTom
TRASTUZUMAB_BETA = -0.3567
#: Reference `benefits22.R:80` carries the caveat "Only applicable to
#: menopausal women." Neither the R nor this module gates on menopausal
#: status, the term applies whenever the flag is set, so the restriction
#: is the CALLER's to honour. Setting bisphosphonate=True for a
#: premenopausal woman produces a benefit the source says does not apply.
BISPHOSPHONATE_BETA = -0.198

# Imputation constants the reference applies for unknown inputs.
SCREEN_UNKNOWN = 0.204
GRADE_UNKNOWN = 2.13

MODEL_CITATION = (
    "PREDICT Breast v2.2 (Pharoah, University of Cambridge). Reference "
    "implementation: WintonCentre/predictv30r R/benefits22.R (MIT). "
    "Candido dos Reis FJ et al. Breast Cancer Res. 2017;19(1):58."
)


def _prognostic_index(
    *,
    age: float,
    screen: float,
    size_mm: float,
    grade: float,
    nodes: int,
    er_positive: bool,
    her2: int,
    ki67: int,
) -> float:
    """Breast-cancer-specific prognostic index (log hazard)."""
    if er_positive:
        c = ER_POS
        age_mfp1 = (age / 10.0) ** -2 - c["age_mfp1_center"]
        age_mfp2 = (age / 10.0) ** -2 * math.log(age / 10.0) - c["age_mfp2_center"]
        age_term = c["age_beta1"] * age_mfp1 + c["age_beta2"] * age_mfp2
        size_term = c["size_beta"] * (math.log(size_mm / 100.0) + c["size_center"])
        grade_val = grade
    else:
        c = ER_NEG
        age_term = c["age_beta1"] * (age - c["age_center"])
        size_term = c["size_beta"] * ((size_mm / 100.0) ** 0.5 - c["size_center"])
        # ER-negative collapses grade to a binary: grade 2/3 = 1, else 0.
        grade_val = 1.0 if grade in (2, 3) else 0.0

    nodes_term = c["nodes_beta"] * (math.log((nodes + 1) / 10.0) + c["nodes_center"])
    return (
        age_term
        + size_term
        + nodes_term
        + c["grade_beta"] * grade_val
        + c["screen_beta"] * screen
        + HER2_BETA[her2]
        + (KI67_BETA[ki67] if er_positive else 0.0)
    )


def _treatment_log_hr(
    *,
    year: int,
    er_positive: bool,
    chemo_generation: int,
    hormone: bool,
    extended_hormone: bool,
    trastuzumab: bool,
    her2: int,
    bisphosphonate: bool,
) -> float:
    """Additive treatment effect on the breast-cancer log hazard, for one year.

    `hormone` is standard adjuvant endocrine therapy. `extended_hormone` is the
    reference implementation's separate `h10` option, continuing beyond 10
    years, which adds a further -0.26 log-HR in years 11-15 only (ATLAS/aTTom).
    They are DISTINCT treatment arms in the source, not one option: its output
    matrix carries both `hctb` and `h10ctb` columns.
    """
    total = CHEMO_BETA[chemo_generation]
    if hormone and er_positive:
        total += HORMONE_BETA
        if extended_hormone and year > 10:
            total += HORMONE_EXTENDED_BETA
    if trastuzumab and her2 == 1:
        total += TRASTUZUMAB_BETA
    if bisphosphonate:
        total += BISPHOSPHONATE_BETA
    return total


def _cumulative_baseline_breast(year: int, *, er_positive: bool) -> float:
    t = float(year)
    if er_positive:
        return math.exp(0.7424402 - 7.527762 / t**0.5 - 1.812513 * math.log(t) / t**0.5)
    return math.exp(-1.156036 + 0.4707332 / t**2 - 3.51355 / t)


def _cumulative_baseline_other(year: int) -> float:
    t = float(year)
    a, b, c = OTHER_BASELINE
    return math.exp(a + b * math.log(t) + c * t**0.5)


def predict_breast(
    *,
    age: float,
    size_mm: float,
    nodes: int,
    grade: int,
    er_positive: bool,
    her2: int = 9,
    ki67: int = 9,
    screen_detected: int = 0,
    chemo_generation: int = 0,
    hormone: bool = False,
    extended_hormone: bool = False,
    trastuzumab: bool = False,
    bisphosphonate: bool = False,
    years: int = 10,
) -> dict:
    """
    Overall survival and adjuvant treatment benefit at `years` after surgery.

    Parameters
    ----------
    age : age at diagnosis, years.
    size_mm : invasive tumour size in mm.
    nodes : number of positive lymph nodes.
    grade : tumour grade 1/2/3, or 9 if unknown (imputed as 2.13).
    er_positive : oestrogen-receptor status.
    her2 : 1 positive, 0 negative, 9 unknown.
    ki67 : 1 positive, 0 negative, 9 unknown. Only used when ER-positive.
    screen_detected : 1 screen-detected, 0 clinically detected, 2 unknown
        (imputed as 0.204).
    chemo_generation : 0 none, 2 second-generation, 3 third-generation.
    hormone : standard adjuvant endocrine therapy.
    extended_hormone : continue endocrine therapy beyond 10 years. A separate
        treatment arm in the reference implementation (its `h10` columns), not
        an automatic consequence of `hormone`; only affects years 11-15.
    years : follow-up horizon, 1-15.

    Returns overall survival with and without treatment, and the absolute
    benefit of the specified regimen in percentage points.
    """
    if not 1 <= years <= MAX_YEARS:
        raise ValueError(f"years must be 1-{MAX_YEARS}, got {years}")
    if age <= 0:
        raise ValueError(f"age must be > 0, got {age}")
    if size_mm <= 0:
        raise ValueError(f"size_mm must be > 0, got {size_mm}")
    if nodes < 0:
        raise ValueError(f"nodes must be >= 0, got {nodes}")
    if grade not in (1, 2, 3, 9):
        raise ValueError(f"grade must be 1/2/3 or 9 (unknown), got {grade}")
    if her2 not in (0, 1, 9):
        raise ValueError(f"her2 must be 0/1/9, got {her2}")
    if ki67 not in (0, 1, 9):
        raise ValueError(f"ki67 must be 0/1/9, got {ki67}")
    if chemo_generation not in CHEMO_BETA:
        raise ValueError(f"chemo_generation must be 0/2/3, got {chemo_generation}")
    if screen_detected not in (0, 1, 2):
        raise ValueError(f"screen_detected must be 0/1/2, got {screen_detected}")

    screen = SCREEN_UNKNOWN if screen_detected == 2 else float(screen_detected)
    grade_v = GRADE_UNKNOWN if grade == 9 else float(grade)

    pi = _prognostic_index(
        age=age,
        screen=screen,
        size_mm=size_mm,
        grade=grade_v,
        nodes=nodes,
        er_positive=er_positive,
        her2=her2,
        ki67=ki67,
    )
    mi = OTHER_AGE_BETA * ((age / 10.0) ** 2 - OTHER_AGE_CENTER)

    def _cumulative_all_cause_mortality(with_treatment: bool) -> float:
        prev_cum_br = prev_cum_oth = 0.0
        prev_base_br = 0.0
        pred_cum_br = pred_cum_oth = 0.0
        prev_m_cum_all = 0.0
        cum_br_hazard = 0.0

        for year in range(1, years + 1):
            rx = (
                _treatment_log_hr(
                    year=year,
                    er_positive=er_positive,
                    chemo_generation=chemo_generation,
                    hormone=hormone,
                    extended_hormone=extended_hormone,
                    trastuzumab=trastuzumab,
                    her2=her2,
                    bisphosphonate=bisphosphonate,
                )
                if with_treatment
                else 0.0
            )

            base_cum_br = _cumulative_baseline_breast(year, er_positive=er_positive)
            annual_base_br = base_cum_br - prev_base_br
            prev_base_br = base_cum_br

            # Annual breast hazard, then accumulate and convert to risk.
            cum_br_hazard += annual_base_br * math.exp(pi + rx)
            s_cum_br = math.exp(-cum_br_hazard)
            m_cum_br = 1.0 - s_cum_br
            annual_m_br = m_cum_br - prev_cum_br
            prev_cum_br = m_cum_br

            s_cum_oth = math.exp(-math.exp(mi) * _cumulative_baseline_other(year))
            m_cum_oth = 1.0 - s_cum_oth
            annual_m_oth = m_cum_oth - prev_cum_oth
            prev_cum_oth = m_cum_oth

            m_cum_all = 1.0 - s_cum_oth * s_cum_br
            annual_m_all = m_cum_all - prev_m_cum_all
            prev_m_cum_all = m_cum_all

            denom = annual_m_br + annual_m_oth
            prop_br = (annual_m_br / denom) if denom > 0 else 0.0
            pred_cum_br += prop_br * annual_m_all
            pred_cum_oth += (1.0 - prop_br) * annual_m_all

        return pred_cum_br + pred_cum_oth

    untreated = _cumulative_all_cause_mortality(with_treatment=False)
    treated = _cumulative_all_cause_mortality(with_treatment=True)

    return {
        "survival_no_treatment": 1.0 - untreated,
        "survival_with_treatment": 1.0 - treated,
        "benefit": untreated - treated,
        "benefit_percentage_points": 100.0 * (untreated - treated),
        "risk": treated,
        "prognostic_index": pi,
        "other_mortality_index": mi,
        "years": years,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "breast",
        "citation": MODEL_CITATION,
        "notes": "PREDICT v2.2; radiotherapy gated off exactly as in the reference",
    }
