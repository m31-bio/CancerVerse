"""ESC SCORE2 10-year CVD risk (primary prevention, no diabetes)."""

from __future__ import annotations

import math

from . import coefficients as C

AXIS = "detection"
MODEL_ID = "score2"


def _sex_key(sex: str) -> str:
    s = sex.strip().lower()
    if s in {"m", "male", "man"}:
        return "male"
    if s in {"f", "female", "woman"}:
        return "female"
    raise ValueError(f"sex must be male/female, got {sex!r}")


def linear_predictor(
    *,
    sex: str,
    age: float,
    sbp: float,
    total_chol_mmol: float,
    hdl_mmol: float,
    smoker: bool,
    diabetes: bool = False,
) -> float:
    """Uncalibrated linear predictor (sum of transformed covariates × log HR)."""
    sk = _sex_key(sex)
    c = C.COEFFS[sk]
    cage = (age - 60.0) / 5.0
    csbp = (sbp - 120.0) / 20.0
    ctchol = total_chol_mmol - 6.0
    chdl = (hdl_mmol - 1.3) / 0.5
    smoke = 1.0 if smoker else 0.0
    dm = 1.0 if diabetes else 0.0
    return (
        c["age"] * cage
        + c["smoking"] * smoke
        + c["sbp"] * csbp
        + c["diabetes"] * dm
        + c["tchol"] * ctchol
        + c["hdl"] * chdl
        + c["smoking_age"] * cage * smoke
        + c["sbp_age"] * cage * csbp
        + c["tchol_age"] * cage * ctchol
        + c["hdl_age"] * cage * chdl
        + c["diabetes_age"] * cage * dm
    )


def uncalibrated_risk(*, sex: str, lp: float | None = None, **kwargs) -> float:
    sk = _sex_key(sex)
    if lp is None:
        lp = linear_predictor(sex=sex, **kwargs)
    s0 = C.COEFFS[sk]["baseline_survival"]
    return 1.0 - s0 ** math.exp(lp)


def recalibrate(uncal: float, *, sex: str, region: str) -> float:
    sk = _sex_key(sex)
    region = region.strip().lower().replace("-", "_").replace(" ", "_")
    if region not in C.RECALIBRATION[sk]:
        raise ValueError(f"region must be one of {C.REGIONS}, got {region!r}")
    if not (0.0 < uncal < 1.0):
        # boundary handling for numerical edge cases
        uncal = min(max(uncal, 1e-15), 1.0 - 1e-15)
    scale1, scale2 = C.RECALIBRATION[sk][region]
    return 1.0 - math.exp(-math.exp(scale1 + scale2 * math.log(-math.log(1.0 - uncal))))


def score2_predict(
    *,
    sex: str,
    age: float,
    sbp: float,
    total_chol_mmol: float,
    hdl_mmol: float,
    smoker: bool,
    region: str = "moderate",
    diabetes: bool = False,
) -> dict:
    """
    10-year SCORE2 CVD risk (probability in [0,1]).

    Notes
    -----
    Official SCORE2 target population excludes diabetes; keep diabetes=False.
    Use SCORE2-Diabetes extension (not yet implemented) for patients with DM.
    """
    if diabetes:
        raise ValueError(
            "SCORE2 is not intended for diabetes; use SCORE2-Diabetes (not implemented). "
            "Pass diabetes=False for the primary-prevention algorithm."
        )
    lp = linear_predictor(
        sex=sex,
        age=age,
        sbp=sbp,
        total_chol_mmol=total_chol_mmol,
        hdl_mmol=hdl_mmol,
        smoker=smoker,
        diabetes=False,
    )
    uncal = uncalibrated_risk(sex=sex, lp=lp)
    risk = recalibrate(uncal, sex=sex, region=region)
    return {
        "risk": risk,
        "risk_uncalibrated": uncal,
        "linear_predictor": lp,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "cvd",
        "region": region.strip().lower().replace("-", "_").replace(" ", "_"),
        "citation": C.MODEL_CITATION,
        "notes": "Calibrated 10y CVD risk; not checked yet vs Cambridge score2risk",
    }
