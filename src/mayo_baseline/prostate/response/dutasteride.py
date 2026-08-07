"""Dutasteride chemoprevention — benefit and harm, side by side.

Equation source
---------------
Nguyen CT, Isariyawongse B, Yu C, Kattan MW. Predictive models for men with a
prior negative prostate biopsy considering dutasteride, built on the REDUCE
trial. Coefficients from the deployed calculator's published R source,

    https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/
        ProstateCancerConsideringDutasteride

which is the model hosted at riskcalc.org.

Why this is a *response* model and not another risk model
----------------------------------------------------------
It predicts **nine outcomes under two arms** — on dutasteride and off it — so
the quantity of interest is the difference, not either number. Four of the nine
are harms:

    benefit    high-grade prostate cancer, any prostate cancer, HGPIN, ASAP,
               acute urinary retention, BPH progression
    harm       erectile dysfunction, gynecomastia, urinary tract infection

A chemoprevention decision is exactly this trade, and a model that reported
only the cancer reduction would be answering half the question.

Form
----
Each sub-model is Cox: ``risk = 1 - S0 ** exp(score)``, with its own predictor
subset, restricted cubic spline knots, baseline survival and applicability
bounds. 17 sub-models, 315 coefficients.

Two asymmetries in the published model, reproduced not smoothed
-----------------------------------------------------------------
1. **ASAP has only the dutasteride arm.** There is no off-treatment comparator
   in the source, so no difference can be computed for it. `difference` is None
   there rather than 0.
2. **HGPIN on dutasteride is a CONSTANT 3.838831%** — no predictors at all,
   the same number for everyone in scope. The off-treatment arm is a full
   28-term model. That is what the source says; it is recorded as a constant
   rather than forced into the Cox shape.

Coefficients are machine-extracted
-----------------------------------
315 coefficients is past the point where hand-copying is safe — this project
has already shipped one wrong coefficient (ALBI's -0.0852) from a far smaller
transcription. `tests/parity/reference/dutasteride_extract.py` parses them out
of the R, and the parity test proves the extraction faithful against that same
R. The JSON it writes is committed.

Scope
-----
Men with a **prior negative 6- to 12-core biopsy in the past 6 months**, the
REDUCE trial's population. Every sub-model carries its own applicability bounds
and returns None outside them, exactly as the tool returns "Not Applicable" —
because the bounds differ per outcome, a patient can be in scope for some
outcomes and not others.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

AXIS = "response"
MODEL_ID = "dutasteride"

#: The 315 coefficients ship WITH the package, not from tests/.
#:
#: They lived under `tests/parity/reference/` and were read from there at
#: runtime, which made the library depend on its own test tree -- an installed
#: wheel that excluded tests would import and then fail on first call. It also
#: put product data in the one directory whose contents are most likely to be
#: dropped from a distribution.
_COEFFICIENTS = Path(__file__).resolve().parent / "data" / "dutasteride_coefficients.json"

ARMS = ("dutasteride", "nodutasteride")

#: outcome key -> (human label, is it a harm?)
OUTCOMES = {
    "highgrade": ("high-grade prostate cancer", False),
    "prostate": ("any prostate cancer", False),
    "hgpin": ("high-grade prostatic intraepithelial neoplasia", False),
    "asap": ("atypical small acinar proliferation", False),
    "aur": ("acute urinary retention", False),
    "bph": ("BPH progression", False),
    "erectile": ("erectile dysfunction", True),
    "gynecomastia": ("gynecomastia", True),
    "uti": ("urinary tract infection", True),
}
HARMS = tuple(k for k, (_, harm) in OUTCOMES.items() if harm)

#: R variable name -> our keyword, from the calculator's own input labels.
INPUTS = {
    "AGE": "age",
    "SBSRL": "sexually_active",
    "IMP": "history_of_impotence",
    "LIB": "history_of_libido_problems",
    "HIS_PCA": "family_history_prostate_cancer",
    "B_OPSA": "psa",
    "B_DRE": "dre_abnormal",
    "B_OPFPS": "percent_free_psa",
    "B_BMI": "bmi",
    "B_IPSS": "ipss_score",
    "B_QM": "max_urinary_flow_ml_s",
    "B_NOCOR": "biopsy_cores",
    "B_PV": "prostate_volume_ml",
    "B_RSD": "residual_urine_ml",
}

MODEL_CITATION = (
    "Nguyen CT, Isariyawongse B, Yu C, Kattan MW — predictive models for men "
    "with a prior negative prostate biopsy considering dutasteride (REDUCE). "
    "Coefficients from the deployed model's published R source at riskcalc.org."
)


@lru_cache(maxsize=1)
def _models() -> dict:
    return json.loads(_COEFFICIENTS.read_text())["models"]


def _used_variables(spec: dict) -> set[str]:
    return (set(spec["linear"])
            | {s["var"] for s in spec["splines"]}
            | {i["var"] for i in spec["indicators"]})


def _applicable(spec: dict, values: dict) -> bool:
    """In scope only if every value the sub-model reads is present and inside
    its declared bounds.

    The bounds and the `!= "Unknown"` checks come from the source, but they do
    not cover every predictor — a variable can be used with no bound declared.
    In R a missing value there would propagate NA silently; here it must be an
    honest None, so every USED variable is required, not just the bounded ones.
    """
    for var in _used_variables(spec):
        if values.get(var) is None:
            return False
    for var, (lo, hi) in spec["bounds"].items():
        v = values.get(var)
        if v is None or not lo <= float(v) <= hi:
            return False
    for var in spec["requires_known"]:
        if values.get(var) is None:
            return False
    return True


def _score(spec: dict, values: dict) -> float:
    total = spec["intercept"]
    for var, coef in spec["linear"].items():
        total += coef * float(values[var])
    for s in spec["splines"]:
        x = float(values[s["var"]]) - s["knot"]
        total += s["coef"] * (x**3 if x > 0 else 0.0)
    for ind in spec["indicators"]:
        got = values.get(ind["var"])
        if isinstance(got, bool):
            got = "Yes" if got else "No"
        if got == ind["level"]:
            total += ind["coef"]
    return total


def _risk(spec: dict, values: dict) -> float | None:
    if not _applicable(spec, values):
        return None
    if spec.get("constant_risk") is not None:
        return float(spec["constant_risk"])
    return 1.0 - spec["baseline_survival"] ** math.exp(_score(spec, values))


def dutasteride_predict(
    *,
    age: float,
    psa: float,
    dre_abnormal: bool | None = None,
    sexually_active: bool | None = None,
    history_of_impotence: bool | None = None,
    history_of_libido_problems: bool | None = None,
    family_history_prostate_cancer: bool | None = None,
    percent_free_psa: float | None = None,
    bmi: float | None = None,
    ipss_score: float | None = None,
    max_urinary_flow_ml_s: float | None = None,
    biopsy_cores: float | None = None,
    prostate_volume_ml: float | None = None,
    residual_urine_ml: float | None = None,
) -> dict:
    """
    Risk of nine outcomes on and off dutasteride, and the difference.

    Only `age` and `psa` are always needed; the rest are optional because the
    sub-models use different subsets. An outcome whose predictors are missing,
    or whose values fall outside its own bounds, comes back None rather than
    guessed — the hosted tool shows "Not Applicable" in the same situations,
    and the bounds differ per outcome, so a patient can be answerable for some
    and not others.

    `risk` is the reduction in HIGH-GRADE prostate cancer, the outcome the
    chemoprevention decision is usually framed around. All nine are in
    `outcomes`, each with its own `difference` (dutasteride minus not) so a
    negative number is a benefit and a positive one is a harm.
    """
    local = locals()
    values = {rvar: local[kw] for rvar, kw in INPUTS.items()}

    outcomes: dict[str, dict] = {}
    for key, (label, is_harm) in OUTCOMES.items():
        spec = _models()[key]
        on = _risk(spec["dutasteride"], values) if "dutasteride" in spec else None
        off = _risk(spec["nodutasteride"], values) if "nodutasteride" in spec else None
        outcomes[key] = {
            "label": label,
            "is_harm": is_harm,
            "dutasteride": on,
            "no_dutasteride": off,
            "difference": (on - off) if (on is not None and off is not None) else None,
        }

    hg = outcomes["highgrade"]["difference"]
    return {
        "risk": hg,
        "outcomes": outcomes,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "prostate",
        "citation": MODEL_CITATION,
        "notes": "nine outcomes under two arms; `difference` is dutasteride "
        "minus no dutasteride, so negative is benefit and positive is harm. "
        "ASAP has no off-treatment arm in the source and HGPIN on dutasteride "
        "is a constant, both reproduced rather than smoothed.",
    }
