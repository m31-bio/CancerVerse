"""Tests for the ALBI grade (Johnson et al., JCO 2015)."""

import math

import pytest

from mayo_baseline.liver.prognosis import albi as A
from mayo_baseline.liver.prognosis import albi_grade, albi_predict, albi_score


def test_formula_matches_published_coefficients():
    """Johnson 2015 (PMC4322258) prints, verbatim:
        "linear predictor = (log10 bilirubin x 0.66) + (albumin x -0.085)"
    This module previously shipped -0.0852, taken from a search summary rather
    than the paper. Corrected 2026-08-05; see the module docstring.
    """
    bili, alb = 20.0, 40.0
    expected = 0.66 * math.log10(bili) - 0.085 * alb
    assert albi_score(bilirubin_umol_l=bili, albumin_g_l=alb) == pytest.approx(expected)


def test_grade_boundaries_are_inclusive_at_the_published_cutoffs():
    # Grade 1 extends up to and including -2.60; grade 2 up to and including -1.39.
    assert albi_grade(-3.0) == 1
    assert albi_grade(A.GRADE_1_MAX) == 1
    assert albi_grade(A.GRADE_1_MAX + 1e-9) == 2
    assert albi_grade(A.GRADE_2_MAX) == 2
    assert albi_grade(A.GRADE_2_MAX + 1e-9) == 3


def test_worse_liver_function_raises_score_and_grade():
    healthy = albi_predict(bilirubin_umol_l=10.0, albumin_g_l=45.0)
    sick = albi_predict(bilirubin_umol_l=60.0, albumin_g_l=28.0)
    assert sick["score"] > healthy["score"]
    assert sick["grade"] >= healthy["grade"]


def test_us_units_convert_to_si():
    si = albi_predict(bilirubin_umol_l=1.0 * A.BILIRUBIN_MG_DL_TO_UMOL_L, albumin_g_l=40.0)
    us = albi_predict(bilirubin_mg_dl=1.0, albumin_g_dl=4.0)
    assert us["score"] == pytest.approx(si["score"])
    assert us["bilirubin_umol_l"] == pytest.approx(17.1)
    assert us["albumin_g_l"] == pytest.approx(40.0)


def test_rejects_ambiguous_or_invalid_units():
    with pytest.raises(ValueError, match="one unit only"):
        albi_predict(bilirubin_umol_l=20.0, bilirubin_mg_dl=1.2, albumin_g_l=40.0)
    with pytest.raises(ValueError, match="albumin"):
        albi_predict(bilirubin_umol_l=20.0)
    with pytest.raises(ValueError, match="bilirubin"):
        albi_score(bilirubin_umol_l=0.0, albumin_g_l=40.0)


def test_metadata():
    out = albi_predict(bilirubin_umol_l=20.0, albumin_g_l=40.0)
    assert out["model_id"] == "albi"
    assert out["axis"] == "prognosis"
    assert out["disease"] == "liver"
    # ALBI is a graded stratifier, not a probability model.
    assert out["risk"] is None


def test_albumin_coefficient_is_the_published_minus_0_085():
    """Regression guard. -0.0852 circulates in secondary sources and was once
    shipped here; the primary paper, MDCalc and the aMAP paper all print
    -0.085. A wrong value here shifts scores ~0.008, enough to flip a grade at
    the -2.60 / -1.39 boundaries."""
    assert A.ALBUMIN_COEF == -0.085
    assert A.BILIRUBIN_COEF == 0.66
