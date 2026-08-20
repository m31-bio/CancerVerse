"""Tests for the aMAP score (Fan et al., J Hepatol 2020)."""

import math

import pytest

from cancerverse_baseline.liver.detection import amap as A
from cancerverse_baseline.liver.detection import amap_predict
from cancerverse_baseline.liver.prognosis import albi_score

REF = dict(age=50, male=True, platelets=200, bilirubin_umol_l=15.0, albumin_g_l=42.0)


def test_formula_matches_the_published_expression():
    albi = 0.66 * math.log10(15.0) - 0.085 * 42.0
    lp = 0.06 * 50 + 0.89 * 1 + 0.48 * albi - 0.01 * 200
    expected = (lp + 7.4) / 14.77 * 100
    out = amap_predict(**REF)
    assert out["score"] == pytest.approx(expected)
    assert out["albi_component"] == pytest.approx(albi)


def test_score_stays_in_the_published_0_100_range_over_clinical_inputs():
    for age in (20, 50, 80):
        for plt in (50, 150, 400):
            for alb in (25, 35, 50):
                s = amap_predict(
                    age=age,
                    male=True,
                    platelets=plt,
                    bilirubin_umol_l=20.0,
                    albumin_g_l=alb,
                )["score"]
                assert 0.0 <= s <= 100.0, (age, plt, alb)


def test_risk_group_cutoffs_are_50_and_60():
    assert A.LOW_RISK_MAX == 50.0
    assert A.MEDIUM_RISK_MAX == 60.0
    assert A.risk_group(49.9) == "low"
    assert A.risk_group(50.0) == "medium"
    assert A.risk_group(59.9) == "medium"
    assert A.risk_group(60.0) == "high"


def test_each_risk_factor_moves_the_score_in_the_published_direction():
    base = amap_predict(**REF)["score"]
    older = amap_predict(**{**REF, "age": 70})["score"]
    female = amap_predict(**{**REF, "male": False})["score"]
    low_plt = amap_predict(**{**REF, "platelets": 80})["score"]
    low_alb = amap_predict(**{**REF, "albumin_g_l": 30.0})["score"]
    high_bili = amap_predict(**{**REF, "bilirubin_umol_l": 60.0})["score"]
    assert older > base  # age raises risk
    assert female < base  # male sex raises risk
    assert low_plt > base  # thrombocytopenia raises risk
    assert low_alb > base  # via ALBI
    assert high_bili > base  # via ALBI


def test_amap_embeds_albi():
    """aMAP's ALBI term should track our standalone ALBI implementation.

    aMAP rounds ALBI's albumin coefficient to -0.085; Johnson's original is
    -0.0852. We keep each model's own rounding, so these agree closely but
    are not bit-identical, that is deliberate, not drift.
    """
    out = amap_predict(**REF)
    standalone = albi_score(bilirubin_umol_l=15.0, albumin_g_l=42.0)
    assert out["albi_component"] == pytest.approx(standalone, abs=0.02)
    assert A.ALBI_ALBUMIN_BETA == -0.085


def test_us_units_convert():
    si = amap_predict(**REF)
    us = amap_predict(
        age=50,
        male=True,
        platelets=200,
        bilirubin_mg_dl=15.0 / A.BILIRUBIN_MG_DL_TO_UMOL_L,
        albumin_g_dl=4.2,
    )
    assert us["score"] == pytest.approx(si["score"])


def test_rejects_ambiguous_or_invalid_input():
    with pytest.raises(ValueError, match="one unit only"):
        amap_predict(**REF, bilirubin_mg_dl=1.0)
    with pytest.raises(ValueError, match="albumin_g_l or albumin_g_dl"):
        amap_predict(age=50, male=True, platelets=200, bilirubin_umol_l=15.0)
    with pytest.raises(ValueError, match="platelets"):
        amap_predict(**{**REF, "platelets": 0})


def test_metadata():
    out = amap_predict(**REF)
    assert out["model_id"] == "amap"
    assert out["axis"] == "detection"
    assert out["disease"] == "liver"
    assert out["risk"] is None


def test_published_formula_values_are_pinned():
    """Pin the published-formula outputs for the three vectors we probed against
    CUHK's custodial calculator.

    The calculator returns 56 / 44 / 68 for these; the published expression
    gives the values below. That gap is documented in the module docstring and
    is why aMAP is not marked parity-matched. If someone later "fixes" the
    formula to agree with the calculator, this test should fail loudly and the
    change should be a deliberate, documented decision.
    """
    a = amap_predict(
        age=50, male=True, platelets=200, bilirubin_umol_l=15.0, albumin_g_l=42.0
    )
    b = amap_predict(
        age=30, male=True, platelets=250, bilirubin_umol_l=10.0, albumin_g_l=45.0
    )
    c = amap_predict(
        age=65, male=True, platelets=150, bilirubin_umol_l=25.0, albumin_g_l=38.0
    )
    assert a["score"] == pytest.approx(53.82, abs=0.01)
    assert b["score"] == pytest.approx(41.10, abs=0.01)
    assert c["score"] == pytest.approx(64.88, abs=0.01)


def test_banding_is_on_the_raw_score_not_a_rounded_one():
    """We band the float; CUHK rounds to an integer first. Documented divergence."""
    assert A.risk_group(59.84) == "medium"  # CUHK would round to 60 -> High
    assert A.risk_group(60.0) == "high"
