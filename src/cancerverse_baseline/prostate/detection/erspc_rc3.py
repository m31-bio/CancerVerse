"""ERSPC prostate detection models (RC3 flagship + RC4/5 helpers)."""

from __future__ import annotations

from ...base import log2, logit_risk
from . import coefficients as C

AXIS = "detection"
MODEL_ID_RC3 = "erspc_rc3"
MODEL_ID_RC45 = "erspc_rc45"


def volume_class(volume_ml: float) -> float:
    """Map TRUS/DRE volume (mL) to ERSPC volume class (25/40/60)."""
    if volume_ml < 30.0:
        return C.VOLUME_CLASS_SMALL
    if volume_ml < 50.0:
        return C.VOLUME_CLASS_MEDIUM
    return C.VOLUME_CLASS_LARGE


def linear_predictor_rc3(*, psa: float, volume_ml: float, dre_positive: bool) -> float:
    """ERSPC RC3 (biopsy-naïve) DRE-based volume linear predictor."""
    vc = volume_class(volume_ml)
    dre = 1.0 if dre_positive else 0.0
    return (
        C.RC3_INTERCEPT
        + C.RC3_PSA * (log2(psa) - C.RC3_PSA_CENTER)
        + C.RC3_VOL * (log2(vc) - C.RC3_VOL_CENTER)
        + C.RC3_DRE * dre
    )


def erspc_rc3_predict(*, psa: float, volume_ml: float, dre_positive: bool) -> dict:
    """Any-PCa risk on biopsy for biopsy-naïve men (ERSPC RC3)."""
    lp = linear_predictor_rc3(psa=psa, volume_ml=volume_ml, dre_positive=dre_positive)
    return {
        "risk": logit_risk(lp),
        "linear_predictor": lp,
        "model_id": MODEL_ID_RC3,
        "axis": AXIS,
        "disease": "prostate",
        "volume_class": volume_class(volume_ml),
        "citation": C.MODEL_CITATION,
        "notes": "Biopsy-naïve any-PCa risk; spot-check vs prostatecancer-riskcalculator.com",
    }


def linear_predictor_rc45(
    *,
    psa: float,
    volume_ml: float,
    dre_positive: bool,
    prior_biopsy: bool,
) -> float:
    """ERSPC RC4/5 LP for previously screened/biopsied men."""
    vc = volume_class(volume_ml)
    dre = 1.0 if dre_positive else 0.0
    prior = 1.0 if prior_biopsy else 0.0
    return (
        C.RC45_INTERCEPT
        + C.RC45_PRIOR_BX * prior
        + (C.RC45_PSA + C.RC45_PSA_PRIOR_INTERACTION * prior) * (log2(psa) - 2.0)
        + C.RC45_VOL * (log2(vc) - C.RC45_VOL_CENTER)
        + C.RC45_DRE * dre
    )


def erspc_rc45_predict(
    *,
    psa: float,
    volume_ml: float,
    dre_positive: bool,
    prior_biopsy: bool = True,
) -> dict:
    lp = linear_predictor_rc45(
        psa=psa,
        volume_ml=volume_ml,
        dre_positive=dre_positive,
        prior_biopsy=prior_biopsy,
    )
    return {
        "risk": logit_risk(lp),
        "linear_predictor": lp,
        "model_id": MODEL_ID_RC45,
        "axis": AXIS,
        "disease": "prostate",
        "volume_class": volume_class(volume_ml),
        "citation": C.MODEL_CITATION,
        "notes": "Previously screened/biopsied pathway",
    }
