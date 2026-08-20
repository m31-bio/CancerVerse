"""MSK pancreatic nomogram — disease-specific survival after resection.

Equation source
---------------
Brennan MF, Kattan MW, Klimstra D, Conlon K. "Prognostic nomogram for patients
undergoing resection for adenocarcinoma of the pancreas." Ann Surg.
2004;240(2). Coefficients from the deployed calculator's published R source,

    https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/
        PancreaticCancer1YrSurvivalAfterResectionforAdenocarcinoma

which is the model hosted at riskcalc.org. (Its directory name says "1Yr"; the
tool actually reports 12, 24 and 36 months.)

Until 2026-08-06 this repository recorded pancreatic prognosis as a cell with
no published equation. That was wrong.

Form
----
    S(t) = S0(t) ** exp(Xb)
    S0 = 0.6775 at 12 months, 0.3457804 at 24, 0.1976732 at 36

    Xb = -1.1733872
       - 0.0018564703 age              + 0.052203014 [male]
       + 0.14916275   [portal vein resected]
       + 0.90746165   [splenectomy]
       + 0.06340785   [resection margin positive]
       - 0.75934357   [resection NOT in the head]
       + 0.31532231   [poorly differentiated] - 0.20496646 [well differentiated]
       + 0.3177352    [posterior margin positive]
       + 0.23051721   posLN - 0.014400166 (posLN)^3+
         + 0.018000207 (posLN-1)^3+ - 0.0036000415 (posLN-5)^3+
       - 0.0017790967 negLN
       + 0.22200163   [back pain]
       - 0.53691787   [T2] - 0.38735092 [T3] + 0.3867342 [T4]
       + 0.04259022   [weight loss]
       + 0.43940983   size - 0.039121714 (size-2)^3+
         + 0.059533043 (size-3.2)^3+ - 0.020411329 (size-5.5)^3+

Three things that will look like errors and are not
---------------------------------------------------
1. **T stage is not monotone.** Against a T1 reference, T2 is -0.537 and T3 is
   -0.387 — both *better* than T1 — while T4 is +0.387. Reproduced as
   published; do not "fix" the ordering.
2. **Splenectomy is the largest single term** (+0.907), larger than any nodal
   or margin effect. It is a marker of extended resection for locally advanced
   disease, not a treatment effect.
3. **Non-head tumours score better** (-0.759 for "other"). Head is the
   reference.

A labelling defect in the hosted tool
-------------------------------------
Its size input is labelled "Maximum Path Axis (**mm**)", but the validated
range is 0.1-16 and the spline knots sit at 2, 3.2 and 5.5. Those are
**centimetres** — a 16 mm ceiling on resected pancreatic adenocarcinoma is not
credible. This module takes centimetres and says so. The range check partly
masks the problem in practice, since most millimetre entries fall outside
0.1-16 and are rejected, but a user entering "8" meaning 8 mm would silently
be scored as an 8 cm tumour.

Scope
-----
After **resection for adenocarcinoma of the pancreas**. Validated ranges
enforced: age 33-89, positive nodes 0-39, negative nodes 0-83, size 0.1-16 cm.
"""

from __future__ import annotations

import math

AXIS = "prognosis"
MODEL_ID = "msk_pancreatic"

BASELINE_SURVIVAL = {12: 0.6775, 24: 0.3457804, 36: 0.1976732}
SUPPORTED_MONTHS = tuple(BASELINE_SURVIVAL)
INTERCEPT = -1.1733872

DIFFERENTIATION_BETA = {"poor": 0.31532231, "moderate": 0.0, "well": -0.20496646}
T_STAGE_BETA = {"1": 0.0, "2": -0.53691787, "3": -0.38735092, "4": 0.3867342}
LOCATION_BETA = {"head": 0.0, "other": -0.75934357}

AGE_RANGE = (33.0, 89.0)
POSITIVE_NODES_RANGE = (0, 39)
NEGATIVE_NODES_RANGE = (0, 83)
SIZE_CM_RANGE = (0.1, 16.0)

MODEL_CITATION = (
    "Brennan MF, Kattan MW, Klimstra D, Conlon K. Ann Surg. 2004;240(2). "
    "Coefficients from the deployed model's published R source at riskcalc.org."
)


def _plus3(x: float) -> float:
    return x**3 if x > 0 else 0.0


def _check(name: str, value: float, bounds: tuple) -> float:
    lo, hi = bounds
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be within [{lo}, {hi}], got {value}")
    return float(value)


def _level(value: str, table: dict, name: str) -> str:
    key = str(value).strip().lower()
    if key not in table:
        raise ValueError(f"{name} must be one of {sorted(table)}, got {value!r}")
    return key


def linear_predictor(
    *,
    age: float,
    male: bool,
    portal_vein_resected: bool,
    splenectomy: bool,
    resection_margin_positive: bool,
    location: str,
    differentiation: str,
    posterior_margin_positive: bool,
    positive_nodes: int,
    negative_nodes: int,
    back_pain: bool,
    t_stage: str,
    weight_loss: bool,
    size_cm: float,
) -> float:
    a = _check("age", age, AGE_RANGE)
    p = _check("positive_nodes", positive_nodes, POSITIVE_NODES_RANGE)
    n = _check("negative_nodes", negative_nodes, NEGATIVE_NODES_RANGE)
    s = _check("size_cm", size_cm, SIZE_CM_RANGE)
    loc = _level(location, LOCATION_BETA, "location")
    diff = _level(differentiation, DIFFERENTIATION_BETA, "differentiation")
    t = str(t_stage).strip().lower().removeprefix("t")
    if t not in T_STAGE_BETA:
        raise ValueError(f"t_stage must be one of 1-4, got {t_stage!r}")

    lp = INTERCEPT
    lp += -0.0018564703 * a
    lp += 0.052203014 * (1.0 if male else 0.0)
    lp += 0.14916275 * (1.0 if portal_vein_resected else 0.0)
    lp += 0.90746165 * (1.0 if splenectomy else 0.0)
    lp += 0.06340785 * (1.0 if resection_margin_positive else 0.0)
    lp += LOCATION_BETA[loc]
    lp += DIFFERENTIATION_BETA[diff]
    lp += 0.3177352 * (1.0 if posterior_margin_positive else 0.0)
    lp += (
        0.23051721 * p
        - 0.014400166 * _plus3(p)
        + 0.018000207 * _plus3(p - 1.0)
        - 0.0036000415 * _plus3(p - 5.0)
    )
    lp += -0.0017790967 * n
    lp += 0.22200163 * (1.0 if back_pain else 0.0)
    lp += T_STAGE_BETA[t]
    lp += 0.04259022 * (1.0 if weight_loss else 0.0)
    lp += (
        0.43940983 * s
        - 0.039121714 * _plus3(s - 2.0)
        + 0.059533043 * _plus3(s - 3.2)
        - 0.020411329 * _plus3(s - 5.5)
    )
    return lp


def msk_pancreatic_predict(
    *,
    age: float,
    male: bool,
    portal_vein_resected: bool = False,
    splenectomy: bool = False,
    resection_margin_positive: bool = False,
    location: str = "head",
    differentiation: str = "moderate",
    posterior_margin_positive: bool = False,
    positive_nodes: int = 0,
    negative_nodes: int = 0,
    back_pain: bool = False,
    t_stage: str = "1",
    weight_loss: bool = False,
    size_cm: float = 3.0,
    months: int = 12,
) -> dict:
    """
    Disease-specific survival at 12, 24 or 36 months after resection.

    `size_cm` is the maximum pathological axis in **centimetres**, despite the
    hosted tool labelling the same field "mm" — see the module docstring.
    """
    if months not in BASELINE_SURVIVAL:
        raise ValueError(
            f"months must be one of {SUPPORTED_MONTHS} (the published "
            f"horizons), got {months}"
        )
    lp = linear_predictor(
        age=age, male=male, portal_vein_resected=portal_vein_resected,
        splenectomy=splenectomy,
        resection_margin_positive=resection_margin_positive, location=location,
        differentiation=differentiation,
        posterior_margin_positive=posterior_margin_positive,
        positive_nodes=positive_nodes, negative_nodes=negative_nodes,
        back_pain=back_pain, t_stage=t_stage, weight_loss=weight_loss,
        size_cm=size_cm,
    )
    s0 = BASELINE_SURVIVAL[months]
    survival = s0 ** math.exp(lp)
    return {
        "survival": survival,
        "risk": 1.0 - survival,
        "linear_predictor": lp,
        "baseline_survival": s0,
        "months": months,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "pancreatic",
        "citation": MODEL_CITATION,
        "notes": "disease-specific survival after resection; T stage is "
        "non-monotone as published, and size is in cm despite the hosted "
        "tool's mm label",
    }
