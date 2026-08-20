"""BCRAT (Gail model), absolute risk of invasive breast cancer.

Model shape
-----------
Unlike the other flagships in this repo, BCRAT is not a single regression.
It is a competing-risk absolute-risk model with two separable pieces:

1. A **relative risk** on five categorised factors (biopsies, age at
   menarche, age at first birth, affected first-degree relatives, and biopsy
   histology), fitted in the BCDDP case-control study.
2. **Baseline hazards** — SEER breast-cancer incidence and NCHS all-cause
   mortality, by race/ethnicity and five-year attained-age band, which    already contain the population's average relative risk, so they are
   scaled by ``1 - attributable risk`` to get a risk-factor-free baseline.

Absolute risk between ages T1 and T2 integrates the two, one year at a
time, exactly as ``absolute.risk.R`` does it (see the loop in
``_integrate`` below):

    h1(a) = (1 - AR) * RR(a) * lambda1(a)      # cause-specific hazard
    h2(a) = lambda2(a)                          # competing-mortality hazard
    Pr(T1, T2) = sum_a  [h1(a) / (h1(a)+h2(a))] * exp(-Lambda(a)) *
                          [1 - exp(-(h1(a)+h2(a)))]

Why this is the breast flagship
--------------------------------
BCRAT is the model behind the NCI's public Breast Cancer Risk Assessment
Tool, NCCN/USPSTF chemoprevention pathways, and NSABP P-1/STAR eligibility
(5-year risk >= 1.66%). Discrimination is modest (pooled AUC ~0.60) but
calibration in US populations is good, exactly the property a
population-level screening/chemoprevention policy needs.

Scope note
----------
The published algorithm distinguishes six Asian-American subgroups
(Chinese/Japanese/Filipino/Hawaiian/other-Pacific-Islander/other-Asian),
each with its own SEER hazard vector but one shared relative-risk model.
This port collapses them to a single ``"asian"`` stratum using the Chinese
rates as a proxy, to keep the coefficient surface manageable. Anyone using
this for a specific Asian subgroup should confirm whether that
approximation matters for their case, or pull the subgroup-specific vectors
from ``absolute.risk.R`` directly.
"""

from __future__ import annotations

import math

from . import coefficients as C

AXIS = "detection"
MODEL_ID = "bcrat"


def _band(age: float) -> int:
    """Index into the 14 five-year hazard bands for an attained age."""
    return min(13, max(0, int((age - C.AGE_MIN) // 5)))


def categorise(
    *,
    age: float,
    race: str,
    n_biopsies: float,
    atypical_hyperplasia: str,
    age_menarche: float,
    age_first_birth: float,
    n_relatives: float,
) -> dict:
    """Reproduce ``recode.check`` from the BCRA package: raw inputs -> the
    five categorised covariates the relative-risk model actually uses."""
    if race not in C.RACE_GROUPS:
        raise ValueError(f"race must be one of {C.RACE_GROUPS}, got {race!r}")
    if atypical_hyperplasia not in C.R_HYPERPLASIA:
        raise ValueError(
            f"atypical_hyperplasia must be one of {tuple(C.R_HYPERPLASIA)}, "
            f"got {atypical_hyperplasia!r}"
        )

    # number of biopsies
    if n_biopsies in (0.0, C.UNKNOWN):
        nb = 0
    elif n_biopsies == 1.0:
        nb = 1
    else:
        nb = 2
    if race in C._HISPANIC and nb == 2:
        nb = 1  # Hispanic strata pool 2+ biopsies with 1 biopsy
    r_hyp = 1.0 if nb == 0 else C.R_HYPERPLASIA[atypical_hyperplasia]

    # age at menarche
    if age_menarche == C.UNKNOWN or age_menarche >= 14.0:
        am = 0
    elif age_menarche >= 12.0:
        am = 1
    else:
        am = 2
    if race == "black" and am == 2:
        am = 1  # CARE model pools menarche <12 with 12-13
    if race == "hispanic_us_born":
        am = 0  # SFBCS US-born model drops age at menarche

    # age at first live birth
    if age_first_birth == C.UNKNOWN or age_first_birth < 20.0:
        af = 0
    elif age_first_birth < 25.0:
        af = 1
    elif age_first_birth < 30.0 or age_first_birth == C.NULLIPAROUS:
        af = 2
    else:
        af = 3
    if race == "black":
        af = 0  # CARE model drops age at first birth
    elif race in C._HISPANIC:
        if age_first_birth != C.NULLIPAROUS and af == 2:
            af = 1
        elif af == 3:
            af = 2

    # first-degree relatives with breast cancer
    if n_relatives in (0.0, C.UNKNOWN):
        nr = 0
    elif n_relatives == 1.0:
        nr = 1
    else:
        nr = 2
    if nr == 2 and race in ("asian",) + C._HISPANIC:
        nr = 1  # 2+ relatives pooled with 1 in these strata

    return {
        "nb": float(nb),
        "am": float(am),
        "af": float(af),
        "nr": float(nr),
        "r_hyp": r_hyp,
    }


def relative_risk(cats: dict, race: str) -> tuple[float, float]:
    """(RR before age 50, RR at/after age 50), per ``relative.risk.R``."""
    beta = C.BETA[race]
    lp1 = (
        beta[0] * cats["nb"]
        + beta[1] * cats["am"]
        + beta[2] * cats["af"]
        + beta[3] * cats["nr"]
        + beta[5] * cats["af"] * cats["nr"]
        + math.log(cats["r_hyp"])
    )
    rr_under_50 = math.exp(lp1)
    rr_50_plus = math.exp(lp1 + beta[4] * cats["nb"])
    return rr_under_50, rr_50_plus


def _integrate(
    *,
    start_age: float,
    end_age: float,
    lambda1: tuple,
    lambda2: tuple,
    one_ar_rr: list,
) -> float:
    """Discrete competing-risk integral, per ``absolute.risk.R``.

    ``one_ar_rr[i]`` is ``(1-AR)*RR`` for attained age ``AGE_MIN + i``
    (70 one-year slices covering ages 20-89).
    """
    n_slices = math.ceil(end_age) - math.floor(start_age)
    first = int(math.floor(start_age) - C.AGE_MIN)
    risk = 0.0
    cumulative = 0.0
    for j in range(n_slices):
        index = first + j
        if n_slices == 1:
            length = end_age - start_age
        elif j == 0:
            length = 1.0 - (start_age - math.floor(start_age))
        elif j == n_slices - 1:
            frac = end_age - math.floor(end_age)
            length = frac if frac > 0 else 1.0
        else:
            length = 1.0
        h1 = lambda1[index // 5] * one_ar_rr[index]
        h2 = lambda2[index // 5]
        total = h1 + h2
        risk += (h1 / total) * math.exp(-cumulative) * (1.0 - math.exp(-total * length))
        cumulative += total * length
    return risk


def bcrat_predict(
    *,
    start_age: float,
    end_age: float,
    race: str = "white",
    n_biopsies: float,
    atypical_hyperplasia: str = "unknown",
    age_menarche: float,
    age_first_birth: float,
    n_relatives: float,
) -> dict:
    """
    Absolute risk of a first invasive breast cancer between ``start_age``
    and ``end_age``, accounting for competing all-cause mortality.

    Notes
    -----
    Population: women aged 35-85 without a personal history of invasive
    breast cancer, DCIS or LCIS, and without a known BRCA1/2 (or other
    high-penetrance) pathogenic variant. The hazard tables are defined from
    age 20, but the public NCI tool refuses to project below age 35.
    ``n_biopsies=99`` / ``age_menarche=99`` / ``age_first_birth=99`` are the
    algorithm's own "unknown" sentinel; ``age_first_birth=98`` means
    nulliparous.
    """
    if end_age <= start_age:
        raise ValueError("end_age must be greater than start_age")
    if start_age < C.AGE_MIN or end_age > C.AGE_MAX:
        raise ValueError(f"ages must fall within [{C.AGE_MIN}, {C.AGE_MAX}]")

    cats = categorise(
        age=start_age,
        race=race,
        n_biopsies=n_biopsies,
        atypical_hyperplasia=atypical_hyperplasia,
        age_menarche=age_menarche,
        age_first_birth=age_first_birth,
        n_relatives=n_relatives,
    )
    rr_under_50, rr_50_plus = relative_risk(cats, race)
    one_ar = C.ONE_MINUS_AR[race]
    one_ar_rr = [one_ar[0] * rr_under_50] * 30 + [one_ar[1] * rr_50_plus] * 40

    risk = _integrate(
        start_age=start_age,
        end_age=end_age,
        lambda1=C.LAMBDA1[race],
        lambda2=C.LAMBDA2[race],
        one_ar_rr=one_ar_rr,
    )

    if race in ("white", "other"):
        avg_l1, avg_l2 = C.AVG_LAMBDA1_WHITE, C.AVG_LAMBDA2_WHITE
    else:
        avg_l1, avg_l2 = C.LAMBDA1[race], C.LAMBDA2[race]
    average_risk = _integrate(
        start_age=start_age,
        end_age=end_age,
        lambda1=avg_l1,
        lambda2=avg_l2,
        one_ar_rr=[1.0] * 70,
    )

    years = end_age - start_age
    five_year_flag = (
        risk >= C.CHEMOPREVENTION_THRESHOLD_5Y if abs(years - 5.0) < 1e-9 else None
    )

    return {
        "risk": risk,
        "average_risk_same_age": average_risk,
        "relative_risk": {"under_50": rr_under_50, "at_or_over_50": rr_50_plus},
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "breast",
        "start_age": start_age,
        "end_age": end_age,
        "meets_star_p1_threshold": five_year_flag,
        "citation": C.MODEL_CITATION,
        "notes": (
            "Absolute invasive-breast-cancer risk, start_age to end_age, "
            "with competing all-cause mortality; formula verified line-by-line "
            "against CRAN BCRA relative.risk.R / absolute.risk.R (2026-08-05), "
            "not yet cross-checked by executing the R package itself"
        ),
    }
