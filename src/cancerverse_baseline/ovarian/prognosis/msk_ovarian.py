"""MSK ovarian nomogram, survival after primary surgery for bulky stage IIIC.

Equation source
---------------
Chi DS, Palayekar MJ, Sonoda Y, Abu-Rustum NR, Awtrey CS, Huh J, Eisenhauer EL, Barakat RR, Kattan MW.
Gynecol Oncol. 2008;108(1). Coefficients from the deployed calculator's
published R source,

    https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/
        OvarianCancerPredictSurvivalAfterSurgforBulkyStageIIICCarc

which is the model hosted at riskcalc.org.

Until 2026-08-06 this repository recorded ovarian prognosis as a cell with no
published equation. That was wrong, and the correction is the point: a survey
that concludes "nobody has published one" is a claim about the literature, and
this one had not looked at who deploys these models.

Form
----
    S(5y) = 0.4284861 ** exp(Xb)

    Xb = -1.7686247
       + 0.014563065 age
         + 2.0997108e-5 (age-44)^3+ - 4.3394022e-5 (age-60)^3+
         + 2.2396915e-5 (age-75)^3+
       - 0.053519323 [grade 3]
       - 0.18814327  [histology yes]
       + 0.00063621499 platelets
       + 0.57912923  [ascites]
       + residual disease term

Residual disease, and its unusual reference
-------------------------------------------
The reference level is **0.5-1 cm**, the middle category, not either end, so two categories carry negative terms and two positive:

    no gross residual  -0.54064543
    < 0.5 cm           -0.3062644
    0.5-1 cm            0            <- reference
    1-2 cm             +0.5518022
    > 2 cm             +0.6219986

Monotone in the right direction, but a reader expecting "no residual disease"
to be the reference will misread every coefficient. It is also the largest
single effect in the model, which is the whole clinical argument for maximal
cytoreduction.

A labelling caveat we cannot resolve from the source
----------------------------------------------------
The hosted tool labels its histology input simply "Tumor Histology" with
choices Yes/No, and the coefficient is on "Yes". What the Yes means, the
paper's series is serous carcinoma, is not recoverable from the code, so this
module names the argument `histology_yes` rather than inventing a meaning it
cannot verify. Read Chi 2008 before using it clinically.

Scope
-----
**Bulky stage IIIC ovarian carcinoma, after primary surgery.** Validated input
ranges enforced: age 22-87, pre-operative platelets 113-1078 x10^3/uL.
"""

from __future__ import annotations

import math

AXIS = "prognosis"
MODEL_ID = "msk_ovarian"

BASELINE_SURVIVAL_5YR = 0.4284861
HORIZON_YEARS = 5
INTERCEPT = -1.7686247

# Reference is the MIDDLE category, 0.5-1 cm.
RESIDUAL_BETA = {
    "no_gross_residual": -0.54064543,
    "lt_0.5_cm": -0.3062644,
    "0.5_1_cm": 0.0,
    "1_2_cm": 0.5518022,
    "gt_2_cm": 0.6219986,
}
GRADE_BETA = {"1-2": 0.0, "3": -0.053519323}

AGE_RANGE = (22.0, 87.0)
PLATELET_RANGE = (113.0, 1078.0)

MODEL_CITATION = (
    "Chi DS, Palayekar MJ, Sonoda Y, Abu-Rustum NR, Awtrey CS, Huh J, Eisenhauer EL, Barakat RR, Kattan MW. "
    "Gynecol Oncol. 2008;108(1). Coefficients from the deployed model's "
    "published R source at riskcalc.org."
)

_RESIDUAL_ALIASES = {
    "none": "no_gross_residual",
    "no": "no_gross_residual",
    "r0": "no_gross_residual",
    "<0.5": "lt_0.5_cm",
    "<0.5_cm": "lt_0.5_cm",
    "0.5-1": "0.5_1_cm",
    "0.5-1_cm": "0.5_1_cm",
    "1-2": "1_2_cm",
    "1-2_cm": "1_2_cm",
    ">2": "gt_2_cm",
    ">2_cm": "gt_2_cm",
}


def _plus3(x: float) -> float:
    return x**3 if x > 0 else 0.0


def _check(name: str, value: float, bounds: tuple) -> float:
    lo, hi = bounds
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be within [{lo}, {hi}], got {value}")
    return float(value)


def linear_predictor(
    *,
    age: float,
    grade: str,
    histology_yes: bool,
    platelets: float,
    ascites: bool,
    residual_disease: str,
) -> float:
    a = _check("age", age, AGE_RANGE)
    plt = _check("platelets", platelets, PLATELET_RANGE)

    g = str(grade).strip()
    if g not in GRADE_BETA:
        raise ValueError(f"grade must be one of {sorted(GRADE_BETA)}, got {grade!r}")

    r = str(residual_disease).strip().lower().replace(" ", "_")
    r = _RESIDUAL_ALIASES.get(r, r)
    if r not in RESIDUAL_BETA:
        raise ValueError(
            f"residual_disease must be one of {sorted(RESIDUAL_BETA)}, "
            f"got {residual_disease!r}"
        )

    lp = INTERCEPT
    lp += (
        0.014563065 * a
        + 2.0997108e-05 * _plus3(a - 44.0)
        - 4.3394022e-05 * _plus3(a - 60.0)
        + 2.2396915e-05 * _plus3(a - 75.0)
    )
    lp += GRADE_BETA[g]
    lp += -0.18814327 * (1.0 if histology_yes else 0.0)
    lp += 0.00063621499 * plt
    lp += 0.57912923 * (1.0 if ascites else 0.0)
    lp += RESIDUAL_BETA[r]
    return lp


def msk_ovarian_predict(
    *,
    age: float,
    grade: str,
    histology_yes: bool,
    platelets: float,
    ascites: bool,
    residual_disease: str,
) -> dict:
    """
    5-year survival after primary surgery for bulky stage IIIC ovarian carcinoma.

    `grade` is "1-2" or "3"; `residual_disease` is one of RESIDUAL_BETA (the
    reference is 0.5-1 cm, not "no gross residual"); `platelets` is the
    pre-operative count in x10^3/uL.
    """
    lp = linear_predictor(
        age=age,
        grade=grade,
        histology_yes=histology_yes,
        platelets=platelets,
        ascites=ascites,
        residual_disease=residual_disease,
    )
    survival = BASELINE_SURVIVAL_5YR ** math.exp(lp)
    return {
        "survival": survival,
        "risk": 1.0 - survival,
        "linear_predictor": lp,
        "baseline_survival": BASELINE_SURVIVAL_5YR,
        "horizon_years": HORIZON_YEARS,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "ovarian",
        "citation": MODEL_CITATION,
        "notes": "bulky stage IIIC after primary surgery; residual-disease "
        "reference is 0.5-1 cm, not no-gross-residual",
    }
