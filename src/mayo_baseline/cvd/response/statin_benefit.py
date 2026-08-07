"""Absolute benefit of LDL lowering — a COMPOSITION, not a published model.

Read this before using it. Every other model in this repository is a published
equation reimplemented and checked against an external source. This one is not.
It is the standard guideline arithmetic for turning a risk estimate and a trial
effect size into an absolute benefit, and it has no calculator or reference
implementation to be checked against, because nobody published it as a model.

    ARR(t) = baseline_risk(t) x (1 - RR ** delta_ldl_mmol)
    NNT    = 1 / ARR

Both inputs are published and both were read:

  baseline_risk   from any verified risk model in this library — PREVENT or
                  SCORE2 for cardiovascular events. Supplied by the caller
                  rather than computed here, so the choice of risk model, its
                  horizon and its scope stay visible.

  RR              Cholesterol Treatment Trialists' Collaboration. "Efficacy and
                  safety of more intensive lowering of LDL cholesterol: a
                  meta-analysis of data from 170,000 participants in 26
                  randomised trials." Lancet. 2010;376(9753):1670-1681.
                  PMID 21067804. Verbatim from the abstract:

                    major vascular events   RR 0.78 (95% CI 0.76-0.80) per
                                            1.0 mmol/L LDL reduction
                    all-cause mortality     RR 0.90 (95% CI 0.87-0.93)

What the composition assumes, and where it strains
---------------------------------------------------
1. **Constant proportional effect.** CTT reports "similar proportional
   reductions in major vascular events per 1.0 mmol/L LDL cholesterol reduction
   ... in all types of patient studied", which is what licenses multiplying it
   onto an individual's baseline risk. It is still an assumption when carried
   to a patient unlike those in the trials.
2. **Horizon mismatch.** CTT's trials ran a median 4.8-5.1 years. PREVENT and
   SCORE2 report 10-year risk. Applying a 5-year proportional effect across 10
   years assumes the effect persists, which the CTT legacy analyses support but
   do not prove for an individual.
3. **Outcome mismatch.** CTT's endpoint is major vascular events (coronary
   death, MI, revascularisation, ischaemic stroke). PREVENT's `total_cvd` and
   SCORE2's endpoint are close but not identical. Use `outcome="mortality"`
   with an all-cause-mortality baseline if that is what you mean.
4. **The CI is on the trial effect only.** `arr_ci` propagates CTT's interval;
   it says nothing about uncertainty in the baseline risk estimate, which is
   usually the larger source.

None of that makes the calculation wrong — it is what NICE, USPSTF and the AHA
do — but it is why this module reports its assumptions in the result and why
its registry row is marked `derived_not_published` rather than verified.
"""

from __future__ import annotations

AXIS = "response"
MODEL_ID = "cvd_statin_benefit"

#: Rate ratio per 1.0 mmol/L LDL-C reduction, with 95% CI. CTT 2010.
RATE_RATIO = {
    "major_vascular_events": (0.78, 0.76, 0.80),
    "all_cause_mortality": (0.90, 0.87, 0.93),
}
OUTCOMES = tuple(RATE_RATIO)

#: 1 mmol/L of LDL-C is 38.67 mg/dL.
MMOL_PER_MG_DL = 1.0 / 38.67

MODEL_CITATION = (
    "Cholesterol Treatment Trialists' Collaboration. Lancet. "
    "2010;376(9753):1670-1681. PMID 21067804 — rate ratio per 1.0 mmol/L "
    "LDL-C reduction, applied to a baseline risk from a separate model."
)


def ldl_reduction_mmol(
    *,
    mmol_l: float | None = None,
    mg_dl: float | None = None,
) -> float:
    """LDL-C reduction in mmol/L, from either unit. Exactly one is required."""
    if (mmol_l is None) == (mg_dl is None):
        raise ValueError("give the LDL reduction in exactly one of mmol_l or mg_dl")
    value = mmol_l if mmol_l is not None else mg_dl * MMOL_PER_MG_DL
    if value < 0:
        raise ValueError(f"ldl reduction must be >= 0, got {value}")
    return value


def cvd_statin_benefit_predict(
    *,
    baseline_risk: float,
    ldl_reduction_mmol_l: float | None = None,
    ldl_reduction_mg_dl: float | None = None,
    outcome: str = "major_vascular_events",
    baseline_risk_source: str = "unspecified",
) -> dict:
    """
    Absolute risk reduction and NNT from lowering LDL-C.

    `baseline_risk` is an untreated absolute risk in [0, 1] — take it from
    `predict("prevent", ...)` or `predict("score2", ...)`, whose horizon and
    scope then govern the answer. It is not computed here on purpose: this
    function must not hide which risk model it was applied to.

    `baseline_risk_source` is recorded verbatim in the result. Passing the
    model id you used makes the output self-describing, which matters because
    the answer means something different on a 10-year PREVENT total-CVD risk
    than on a 5-year one.
    """
    if not 0.0 <= baseline_risk <= 1.0:
        raise ValueError(
            f"baseline_risk must be a probability in [0, 1], got {baseline_risk}"
        )
    if outcome not in RATE_RATIO:
        raise ValueError(f"outcome must be one of {OUTCOMES}, got {outcome!r}")

    delta = ldl_reduction_mmol(
        mmol_l=ldl_reduction_mmol_l, mg_dl=ldl_reduction_mg_dl
    )
    rr, rr_lo, rr_hi = RATE_RATIO[outcome]

    def _arr(ratio: float) -> float:
        return baseline_risk * (1.0 - ratio**delta)

    arr = _arr(rr)
    # a smaller rate ratio is a larger benefit, so the CI inverts
    arr_hi, arr_lo = _arr(rr_lo), _arr(rr_hi)

    return {
        "risk": None,  # this is a benefit, not a risk — see notes
        "absolute_risk_reduction": arr,
        "arr_ci": (arr_lo, arr_hi),
        "relative_risk_reduction": 1.0 - rr**delta,
        "treated_risk": baseline_risk - arr,
        "number_needed_to_treat": (1.0 / arr) if arr > 0 else None,
        "baseline_risk": baseline_risk,
        "baseline_risk_source": baseline_risk_source,
        "ldl_reduction_mmol_l": delta,
        "outcome": outcome,
        "rate_ratio_per_mmol": rr,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "cvd",
        "citation": MODEL_CITATION,
        "notes": "DERIVED, not a published prediction model: a published trial "
        "effect applied to a baseline risk from a separate model. The horizon "
        "and outcome are whatever the baseline risk model's were; CTT's trials "
        "ran a median 4.8-5.1 years for major vascular events.",
        "assumptions": (
            "constant proportional effect across baseline risk (CTT)",
            "trial effect over ~5 years carried to the baseline model's horizon",
            "CTT's major-vascular-events endpoint approximates the baseline "
            "model's endpoint",
            "arr_ci propagates the trial effect only, not baseline uncertainty",
        ),
    }
