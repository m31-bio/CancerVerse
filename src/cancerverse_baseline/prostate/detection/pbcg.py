"""PBCG — Prostate Biopsy Collaborative Group risk calculator.

Equation source
---------------
Ankerst DP, Straubinger J, Selig K, et al. "A Contemporary Prostate Biopsy Risk
Calculator Based on Multiple Heterogeneous Cohorts." Eur Urol. 2018;74(2):197-203.
Built on 15,611 men undergoing 16,369 biopsies at eight North American
institutions 2006-2017, validated at three European ones.

Coefficients from the deployed calculator's published R source,

    https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/PBCG

which is the model hosted at riskcalc.org.

Why this sits alongside ERSPC RC3 rather than replacing it
-----------------------------------------------------------
PBCG is the contemporary successor to PCPTRC 2.0 and reports better
discrimination (AUC 75.5% internal, 72.3% external, against roughly 70-73% for
the older calculators). Two properties matter more than recency:

1. **It predicts three outcomes, not one.** No cancer, low-grade
   (Gleason 6), high-grade (Gleason 7+). The clinically actionable question is
   the high-grade one, and a binary any-cancer model cannot answer it.
2. **It degrades gracefully.** Eight coefficient sets cover every pattern of
   missing prior-biopsy / DRE / family-history data, so a record lacking any of
   them still gets the right sub-model rather than an imputed value.

It is NOT strictly better than ERSPC RC3 everywhere. External validation found
PBCG improved calibration in White men but **over-predicted in Black and other
groups** at most thresholds. Both are kept.

Form
----
Multinomial logistic with "no cancer" as the reference outcome:

    S1 = beta_low  . x        (low grade vs no cancer)
    S2 = beta_high . x        (high grade vs no cancer)

    P(no cancer)  = 1 / (1 + e^S1 + e^S2)
    P(low grade)  = e^S1 / (1 + e^S1 + e^S2)
    P(high grade) = e^S2 / (1 + e^S1 + e^S2)

    x = [1, log2(PSA), age, african_ancestry,
         (prior_biopsy), (dre), (family_history)]   -- present terms only

A display quirk of the hosted tool, reproduced only on request
---------------------------------------------------------------
riskcalc.org rounds P(no cancer) and P(low grade) to whole percent and then
computes high grade as ``100 - no - low``, so **all the rounding error lands on
the high-grade estimate**, the one the decision turns on. This module returns
unrounded probabilities; `rounded_like_riskcalc()` reproduces the tool.
"""

from __future__ import annotations

import math

AXIS = "detection"
MODEL_ID = "pbcg"

#: Coefficient vectors keyed by which optional predictors are supplied, in the
#: order (prior_biopsy, dre, family_history). Term order within each vector is
#: intercept, log2(PSA), age, african_ancestry, then the supplied optionals in
#: that same order, which is how the source builds its data vector.
COEFFICIENTS: dict[tuple[bool, bool, bool], dict[str, tuple[float, ...]]] = {
    (True, True, True): {
        "low": (
            -2.44052108,
            0.13617244,
            0.01780617,
            0.78721039,
            -0.83613721,
            0.04612721,
            0.33233636,
        ),
        "high": (
            -6.36851856,
            0.79996510,
            0.05566536,
            0.61596975,
            -1.27437249,
            0.85780143,
            0.61003848,
        ),
    },
    (True, True, False): {
        "low": (
            -2.29687989,
            0.13785591,
            0.01758914,
            0.63876791,
            -0.86200471,
            0.07193350,
        ),
        "high": (
            -6.06621401,
            0.76053930,
            0.05509847,
            0.51701373,
            -1.38390751,
            0.83442202,
        ),
    },
    (True, False, True): {
        "low": (
            -2.64840984,
            0.13125283,
            0.02044166,
            0.81792881,
            -0.98610357,
            0.31447017,
        ),
        "high": (
            -6.70538152,
            0.77635003,
            0.06542705,
            0.52401464,
            -1.43681965,
            0.55443478,
        ),
    },
    (False, True, True): {
        "low": (
            -2.16147411,
            0.07409519,
            0.01322988,
            0.76131045,
            0.05397516,
            0.29246219,
        ),
        "high": (
            -5.99897055,
            0.70727793,
            0.04992968,
            0.56485952,
            0.89154384,
            0.56910873,
        ),
    },
    (True, False, False): {
        "low": (-2.49050385, 0.12961272, 0.02020429, 0.67674970, -0.97275826),
        "high": (-6.41089002, 0.74110558, 0.06476911, 0.42814591, -1.50274350),
    },
    (False, True, False): {
        "low": (-2.01851079, 0.06745424, 0.01263369, 0.63938472, 0.08562844),
        "high": (-5.68203352, 0.65059244, 0.04883786, 0.49214793, 0.87421554),
    },
    (False, False, True): {
        "low": (-2.39161580, 0.06129651, 0.01600515, 0.81132928, 0.27501639),
        "high": (-6.42320154, 0.67779036, 0.06092178, 0.50429130, 0.50805684),
    },
    (False, False, False): {
        "low": (-2.23794923, 0.05343098, 0.01553627, 0.69593716),
        "high": (-6.13292904, 0.62979529, 0.06002002, 0.43816016),
    },
}

MODEL_CITATION = (
    "Ankerst DP, Straubinger J, Selig K, et al. Eur Urol. 2018;74(2):197-203 "
    "(Prostate Biopsy Collaborative Group risk calculator). Coefficients from "
    "the deployed model's published R source at riskcalc.org."
)


def linear_predictors(
    *,
    psa: float,
    age: float,
    african_ancestry: bool,
    prior_biopsy: bool | None = None,
    dre_abnormal: bool | None = None,
    family_history: bool | None = None,
) -> tuple[float, float]:
    """(S1, S2): log-odds of low-grade and high-grade against no cancer."""
    if psa <= 0:
        raise ValueError(f"psa must be > 0 ng/mL, got {psa}")
    if age <= 0:
        raise ValueError(f"age must be > 0, got {age}")

    key = (
        prior_biopsy is not None,
        dre_abnormal is not None,
        family_history is not None,
    )
    betas = COEFFICIENTS[key]

    x = [1.0, math.log2(psa), float(age), 1.0 if african_ancestry else 0.0]
    # Appended in the source's own order: prior biopsy, DRE, family history.
    if prior_biopsy is not None:
        x.append(1.0 if prior_biopsy else 0.0)
    if dre_abnormal is not None:
        x.append(1.0 if dre_abnormal else 0.0)
    if family_history is not None:
        x.append(1.0 if family_history else 0.0)

    assert len(x) == len(betas["low"]) == len(betas["high"]), (
        f"term/coefficient mismatch for {key}: {len(x)} terms"
    )
    # strict=True as well as the assertion above: assertions vanish under -O,
    # and a silently truncated zip here would drop a predictor and still return
    # a plausible probability.
    s1 = sum(b * v for b, v in zip(betas["low"], x, strict=True))
    s2 = sum(b * v for b, v in zip(betas["high"], x, strict=True))
    return s1, s2


def pbcg_predict(
    *,
    psa: float,
    age: float,
    african_ancestry: bool,
    prior_biopsy: bool | None = None,
    dre_abnormal: bool | None = None,
    family_history: bool | None = None,
) -> dict:
    """
    Probability of no cancer, low-grade and high-grade cancer on biopsy.

    `prior_biopsy`, `dre_abnormal` and `family_history` may each be None,
    meaning "not known", the model then uses the coefficient set fitted
    without that predictor rather than imputing a value. PSA, age and ancestry
    are mandatory.

    `risk` is the HIGH-GRADE probability, because that is the one a biopsy
    decision turns on. All three are in `probabilities`.
    """
    s1, s2 = linear_predictors(
        psa=psa,
        age=age,
        african_ancestry=african_ancestry,
        prior_biopsy=prior_biopsy,
        dre_abnormal=dre_abnormal,
        family_history=family_history,
    )
    denom = 1.0 + math.exp(s1) + math.exp(s2)
    p_no = 1.0 / denom
    p_low = math.exp(s1) / denom
    p_high = math.exp(s2) / denom

    known = [
        n
        for n, v in (
            ("prior_biopsy", prior_biopsy),
            ("dre_abnormal", dre_abnormal),
            ("family_history", family_history),
        )
        if v is not None
    ]
    return {
        "risk": p_high,
        "probabilities": {"no_cancer": p_no, "low_grade": p_low, "high_grade": p_high},
        "linear_predictors": {"low_grade": s1, "high_grade": s2},
        "submodel": tuple(known),
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "prostate",
        "citation": MODEL_CITATION,
        "notes": "multinomial: no cancer / Gleason 6 / Gleason 7+; one of eight "
        "coefficient sets by which optional predictors are known",
    }


def rounded_like_riskcalc(result: dict) -> dict[str, int]:
    """Reproduce the hosted tool's display, including its rounding artefact.

    riskcalc.org rounds no-cancer and low-grade to whole percent and derives
    high grade as the remainder, so every rounding error accumulates on the
    high-grade figure, the clinically decisive one. Use this only to compare
    against that tool.
    """
    p = result["probabilities"]
    no = round(p["no_cancer"] * 100)
    low = round(p["low_grade"] * 100)
    return {"no_cancer": no, "low_grade": low, "high_grade": 100 - no - low}
