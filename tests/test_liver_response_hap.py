"""Tests for the HAP score (Kadalayil et al., Ann Oncol 2013)."""

import pytest

from mayo_baseline.liver.response import hap as H
from mayo_baseline.liver.response import hap_grade, hap_predict

# A patient scoring 0 on every criterion.
CLEAN = dict(
    albumin_g_l=42.0,
    bilirubin_umol_l=12.0,
    afp_ng_ml=20.0,
    dominant_tumour_size_cm=3.0,
)


def test_all_criteria_absent_is_grade_a():
    out = hap_predict(**CLEAN)
    assert out["score"] == 0
    assert out["grade"] == "A"
    assert out["median_os_months"] == pytest.approx(27.6)


def test_each_criterion_contributes_exactly_one_point():
    for field, bad_value, key in (
        ("albumin_g_l", 30.0, "albumin"),
        ("bilirubin_umol_l", 25.0, "bilirubin"),
        ("afp_ng_ml", 500.0, "afp"),
        ("dominant_tumour_size_cm", 9.0, "tumour_size"),
    ):
        out = hap_predict(**{**CLEAN, field: bad_value})
        assert out["score"] == 1, field
        assert out["components"][key] == 1, field
        assert out["grade"] == "B"


def test_thresholds_are_strict_and_directional():
    """albumin is '< 36' (not <=); the other three are '>' (not >=)."""
    assert hap_predict(**{**CLEAN, "albumin_g_l": 36.0})["components"]["albumin"] == 0
    assert hap_predict(**{**CLEAN, "albumin_g_l": 35.9})["components"]["albumin"] == 1

    assert hap_predict(**{**CLEAN, "bilirubin_umol_l": 17.0})["components"]["bilirubin"] == 0
    assert hap_predict(**{**CLEAN, "bilirubin_umol_l": 17.1})["components"]["bilirubin"] == 1

    assert hap_predict(**{**CLEAN, "afp_ng_ml": 400.0})["components"]["afp"] == 0
    assert hap_predict(**{**CLEAN, "afp_ng_ml": 400.1})["components"]["afp"] == 1

    assert hap_predict(**{**CLEAN, "dominant_tumour_size_cm": 7.0})["components"]["tumour_size"] == 0
    assert hap_predict(**{**CLEAN, "dominant_tumour_size_cm": 7.1})["components"]["tumour_size"] == 1


def test_grade_d_absorbs_both_3_and_4_points():
    """The paper defines D as '>2', so 3 and 4 are the same grade."""
    assert hap_grade(0) == "A"
    assert hap_grade(1) == "B"
    assert hap_grade(2) == "C"
    assert hap_grade(3) == "D"
    assert hap_grade(4) == "D"


def test_worst_case_is_grade_d():
    out = hap_predict(
        albumin_g_l=28.0,
        bilirubin_umol_l=40.0,
        afp_ng_ml=1200.0,
        dominant_tumour_size_cm=10.0,
    )
    assert out["score"] == 4
    assert out["grade"] == "D"
    assert out["median_os_months"] == pytest.approx(3.6)


def test_median_survival_decreases_monotonically_across_grades():
    os_by_grade = [H.MEDIAN_OS_MONTHS[g] for g in ("A", "B", "C", "D")]
    assert os_by_grade == sorted(os_by_grade, reverse=True)


def test_us_units_convert_to_si():
    si = hap_predict(**CLEAN)
    us = hap_predict(
        albumin_g_dl=4.2,
        bilirubin_mg_dl=12.0 / H.BILIRUBIN_MG_DL_TO_UMOL_L,
        afp_ng_ml=20.0,
        dominant_tumour_size_cm=3.0,
    )
    assert us["score"] == si["score"]
    assert us["components"] == si["components"]


def test_rejects_ambiguous_or_invalid_units():
    with pytest.raises(ValueError, match="albumin in one unit only"):
        hap_predict(**CLEAN, albumin_g_dl=4.2)
    with pytest.raises(ValueError, match="bilirubin in one unit only"):
        hap_predict(**CLEAN, bilirubin_mg_dl=0.7)
    with pytest.raises(ValueError, match="albumin_g_l or albumin_g_dl"):
        hap_predict(
            bilirubin_umol_l=12.0, afp_ng_ml=20.0, dominant_tumour_size_cm=3.0
        )
    with pytest.raises(ValueError, match="afp_ng_ml must be > 0"):
        hap_predict(**{**CLEAN, "afp_ng_ml": 0.0})


def test_metadata():
    out = hap_predict(**CLEAN)
    assert out["model_id"] == "hap"
    assert out["axis"] == "response"
    assert out["disease"] == "liver"
    assert out["risk"] is None
