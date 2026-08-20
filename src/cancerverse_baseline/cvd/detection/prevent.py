"""AHA PREVENT risk equations (Khan et al., Circulation 2024).

Covers all 5 published variants (base / uacr / hba1c / sdi / full) at both
horizons (10 and 30 years), for all 5 outcomes (total CVD / ASCVD / heart
failure / CHD / stroke) and both sexes — 100 coefficient sets total, see
`prevent_coefficients.py`.
"""

from __future__ import annotations

import math

from ...base import logit_risk
from . import prevent_coefficients as C

# BMI is accepted for every outcome but only *used* by heart_failure. In the
# published equations the bmi_min / bmi_max / age_bmi_max coefficients are
# exactly 0.0 for total_cvd, ascvd, chd and stroke — 40 of the 50 coefficient
# sets per sex. So a caller who supplies BMI expecting it to move their
# 10-year CVD risk gets no change, and that is correct, not a bug. Pinned by
# test_bmi_only_affects_the_heart_failure_outcome.
BMI_ONLY_AFFECTS = ("heart_failure",)

AXIS = "detection"
MODEL_ID = "prevent"


class CoefficientsNotAvailable(NotImplementedError):
    """Retained for API compatibility. No PREVENT variant currently raises this —
    all 100 published coefficient sets are shipped in prevent_coefficients.py.
    """


def _sex_key(sex: str) -> str:
    s = sex.strip().lower()
    if s in {"m", "male", "man"}:
        return "male"
    if s in {"f", "female", "woman"}:
        return "female"
    raise ValueError(f"sex must be male/female, got {sex!r}")


def select_variant(*, uacr: float | None, hba1c: float | None, sdi_decile: int | None) -> str:
    """Auto-select the model variant from which optional labs were supplied.

    Mirrors the reference implementation's rule (preventr::estimate_risk):
    0 optional predictors -> base; exactly 1 -> that single-predictor model;
    2 or 3 -> full (each missing one is scored via its "missing" indicator).
    """
    n = sum(x is not None for x in (uacr, hba1c, sdi_decile))
    if n == 0:
        return "base"
    if n >= 2:
        return "full"
    if uacr is not None:
        return "uacr"
    if hba1c is not None:
        return "hba1c"
    return "sdi"


def _features(
    *,
    age: float,
    total_chol_mg_dl: float,
    hdl_mg_dl: float,
    sbp: float,
    diabetes: bool,
    smoker: bool,
    bmi: float,
    egfr: float,
    htn_meds: bool,
    statin: bool,
    uacr: float | None,
    hba1c: float | None,
    sdi_decile: int | None,
) -> dict[str, float]:
    """Transformed covariates, keyed by the term slugs used in PREVENT_TABLES."""
    k = C.CHOL_MG_DL_TO_MMOL_L
    age_c = (age - C.AGE_CENTER) / C.AGE_SCALE
    non_hdl = k * (total_chol_mg_dl - hdl_mg_dl) - C.NON_HDL_CENTER
    hdl = (k * hdl_mg_dl - C.HDL_CENTER) / C.HDL_SCALE
    sbp_min = (min(sbp, C.SBP_KNOT) - C.SBP_MIN_CENTER) / C.SBP_SCALE
    sbp_max = (max(sbp, C.SBP_KNOT) - C.SBP_MAX_CENTER) / C.SBP_SCALE
    bmi_min = (min(bmi, C.BMI_KNOT) - C.BMI_MIN_CENTER) / C.BMI_SCALE
    bmi_max = (max(bmi, C.BMI_KNOT) - C.BMI_MAX_CENTER) / C.BMI_SCALE
    egfr_min = (min(egfr, C.EGFR_KNOT) - C.EGFR_MIN_CENTER) / C.EGFR_SCALE
    egfr_max = (max(egfr, C.EGFR_KNOT) - C.EGFR_MAX_CENTER) / C.EGFR_SCALE
    dm = 1.0 if diabetes else 0.0
    smoke = 1.0 if smoker else 0.0
    htn = 1.0 if htn_meds else 0.0
    stat = 1.0 if statin else 0.0

    # Extended-model terms: an absent lab contributes 0 to its slope term and
    # 1 to its own "missing" indicator — that is the published design (the
    # reference implementation encodes exactly this), not an imputation choice
    # of ours. Note ln(UACR) is NOT centered in the source equations.
    ln_acr = 0.0 if uacr is None else math.log(uacr)
    acr_missing = 1.0 if uacr is None else 0.0

    hba1c_dm = 0.0 if (hba1c is None or not diabetes) else (hba1c - C.HBA1C_CENTER)
    hba1c_no_dm = 0.0 if (hba1c is None or diabetes) else (hba1c - C.HBA1C_CENTER)
    hba1c_missing = 1.0 if hba1c is None else 0.0

    sdi_4_6 = 1.0 if (sdi_decile is not None and 4 <= sdi_decile <= 6) else 0.0
    sdi_7_10 = 1.0 if (sdi_decile is not None and 7 <= sdi_decile <= 10) else 0.0
    sdi_missing = 1.0 if sdi_decile is None else 0.0

    return {
        "age": age_c,
        "age_sq": age_c * age_c,
        "non_hdl": non_hdl,
        "hdl": hdl,
        "sbp_min": sbp_min,
        "sbp_max": sbp_max,
        "diabetes": dm,
        "smoking": smoke,
        "bmi_min": bmi_min,
        "bmi_max": bmi_max,
        "egfr_min": egfr_min,
        "egfr_max": egfr_max,
        "htn_meds": htn,
        "statin": stat,
        "htn_meds_sbp_max": htn * sbp_max,
        "statin_non_hdl": stat * non_hdl,
        "age_non_hdl": age_c * non_hdl,
        "age_hdl": age_c * hdl,
        "age_sbp_max": age_c * sbp_max,
        "age_diabetes": age_c * dm,
        "age_smoking": age_c * smoke,
        "age_bmi_max": age_c * bmi_max,
        "age_egfr_min": age_c * egfr_min,
        "ln_acr": ln_acr,
        "acr_missing": acr_missing,
        "hba1c_dm": hba1c_dm,
        "hba1c_no_dm": hba1c_no_dm,
        "hba1c_missing": hba1c_missing,
        "sdi_4_6": sdi_4_6,
        "sdi_7_10": sdi_7_10,
        "sdi_missing": sdi_missing,
        "constant": 1.0,
    }


def linear_predictor(
    *,
    sex: str,
    outcome: str,
    variant: str = "base",
    horizon_years: int = 10,
    uacr: float | None = None,
    hba1c: float | None = None,
    sdi_decile: int | None = None,
    **features,
) -> float:
    """Model logit for one sex x outcome x variant x horizon combination."""
    if outcome not in C.OUTCOMES:
        raise ValueError(f"outcome must be one of {C.OUTCOMES}, got {outcome!r}")
    if variant not in C.VARIANTS:
        raise ValueError(f"variant must be one of {C.VARIANTS}, got {variant!r}")
    if horizon_years not in C.HORIZONS:
        raise ValueError(f"horizon_years must be one of {C.HORIZONS}, got {horizon_years}")
    if sdi_decile is not None and not 1 <= sdi_decile <= 10:
        raise ValueError(f"sdi_decile must be 1-10, got {sdi_decile}")
    if uacr is not None and uacr <= 0:
        raise ValueError(f"uacr must be > 0 mg/g, got {uacr}")

    key = f"{_sex_key(sex)}_{outcome}"
    betas = C.PREVENT_TABLES[(variant, horizon_years)][key]
    x = _features(uacr=uacr, hba1c=hba1c, sdi_decile=sdi_decile, **features)
    return sum(beta * x[term] for term, beta in betas.items())


def prevent_predict(
    *,
    sex: str,
    age: float,
    total_chol_mg_dl: float,
    hdl_mg_dl: float,
    sbp: float,
    diabetes: bool,
    smoker: bool,
    bmi: float,
    egfr: float,
    htn_meds: bool = False,
    statin: bool = False,
    outcome: str = "total_cvd",
    horizon_years: int = 10,
    uacr: float | None = None,
    hba1c: float | None = None,
    sdi_decile: int | None = None,
    variant: str | None = None,
) -> dict:
    """
    PREVENT risk (probability in [0,1]) for one outcome, at 10 or 30 years.

    Parameters use US clinical units: cholesterol in mg/dL, SBP in mm Hg,
    eGFR in mL/min/1.73m², UACR in mg/g, HbA1c in %. `outcome` is one of
    total_cvd / ascvd / heart_failure / chd / stroke.

    Supplying `uacr`, `hba1c` and/or `sdi_decile` auto-selects the matching
    extended model variant (uacr / hba1c / sdi / full) unless `variant` is
    passed explicitly. Selection follows the published rule: 0 extra labs ->
    base, exactly 1 -> that single-predictor model, 2 or 3 -> full (each
    missing lab scored via its own "missing" indicator term).

    Notes
    -----
    The 30-year equations are defined for ages 30-59; 10-year for ages 30-79.
    """
    if variant is None:
        variant = select_variant(uacr=uacr, hba1c=hba1c, sdi_decile=sdi_decile)
    if horizon_years not in C.HORIZONS:
        raise ValueError(f"horizon_years must be one of {C.HORIZONS}, got {horizon_years}")

    lo, hi = C.AGE_RANGE[horizon_years]
    if not lo <= age <= hi:
        raise ValueError(
            f"PREVENT {horizon_years}-year equations are defined for ages "
            f"{lo:.0f}-{hi:.0f}, got {age}"
        )
    features = dict(
        age=age,
        total_chol_mg_dl=total_chol_mg_dl,
        hdl_mg_dl=hdl_mg_dl,
        sbp=sbp,
        diabetes=diabetes,
        smoker=smoker,
        bmi=bmi,
        egfr=egfr,
        htn_meds=htn_meds,
        statin=statin,
    )
    lp = linear_predictor(
        sex=sex,
        outcome=outcome,
        variant=variant,
        horizon_years=horizon_years,
        uacr=uacr,
        hba1c=hba1c,
        sdi_decile=sdi_decile,
        **features,
    )
    return {
        "risk": logit_risk(lp),
        "linear_predictor": lp,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "cvd",
        "outcome": outcome,
        "horizon_years": horizon_years,
        "variant": variant,
        "citation": C.PREVENT_CITATION,
        "notes": "PREVENT equations; base 10y parity matched vs supplemental Table S25",
    }


def prevent_predict_all(**kwargs) -> dict[str, float]:
    """Risk for every PREVENT outcome at once, keyed by outcome name."""
    kwargs.pop("outcome", None)
    return {o: prevent_predict(outcome=o, **kwargs)["risk"] for o in C.OUTCOMES}
