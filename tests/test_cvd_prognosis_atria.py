"""Tests for the ATRIA stroke risk score (Singer et al., JAHA 2013)."""

import pytest

from cancerverse_baseline.cvd.prognosis import (
    atria_predict,
    atria_risk_category,
    atria_score,
)

NONE_NO_STROKE = dict(
    age=50,
    prior_stroke=False,
    female=False,
    diabetes=False,
    heart_failure=False,
    hypertension=False,
    proteinuria=False,
    egfr_under_45_or_esrd=False,
)


def test_zero_score_for_no_risk_factors_under_65():
    assert atria_score(**NONE_NO_STROKE) == 0


def test_age_bands_no_prior_stroke():
    assert atria_score(**{**NONE_NO_STROKE, "age": 64}) == 0
    assert atria_score(**{**NONE_NO_STROKE, "age": 65}) == 3
    assert atria_score(**{**NONE_NO_STROKE, "age": 74}) == 3
    assert atria_score(**{**NONE_NO_STROKE, "age": 75}) == 5
    assert atria_score(**{**NONE_NO_STROKE, "age": 84}) == 5
    assert atria_score(**{**NONE_NO_STROKE, "age": 85}) == 6
    assert atria_score(**{**NONE_NO_STROKE, "age": 95}) == 6


def test_age_bands_with_prior_stroke_are_not_the_no_stroke_bands_plus_two():
    # The interaction table, not one age term plus a flat stroke addend --
    # under-65-with-stroke (8) is worth MORE than 65-74-with-stroke (7).
    base = {**NONE_NO_STROKE, "prior_stroke": True}
    assert atria_score(**{**base, "age": 50}) == 8
    assert atria_score(**{**base, "age": 65}) == 7
    assert atria_score(**{**base, "age": 74}) == 7
    assert atria_score(**{**base, "age": 75}) == 7
    assert atria_score(**{**base, "age": 85}) == 9


def test_max_score_with_prior_stroke_is_fifteen():
    out = atria_score(
        age=90,
        prior_stroke=True,
        female=True,
        diabetes=True,
        heart_failure=True,
        hypertension=True,
        proteinuria=True,
        egfr_under_45_or_esrd=True,
    )
    assert out == 9 + 1 + 1 + 1 + 1 + 1 + 1 == 15


def test_max_score_with_no_prior_stroke_is_twelve():
    out = atria_score(
        age=90,
        prior_stroke=False,
        female=True,
        diabetes=True,
        heart_failure=True,
        hypertension=True,
        proteinuria=True,
        egfr_under_45_or_esrd=True,
    )
    assert out == 6 + 1 + 1 + 1 + 1 + 1 + 1 == 12


def test_risk_bands_match_table_4():
    assert atria_risk_category(0) == "low"
    assert atria_risk_category(5) == "low"
    assert atria_risk_category(6) == "moderate"
    assert atria_risk_category(7) == "high"
    assert atria_risk_category(15) == "high"


def test_predict_shape_and_no_raw_rate_shipped():
    out = atria_predict(**NONE_NO_STROKE)
    assert out["score"] == 0
    assert out["risk_category"] == "low"
    assert out["risk"] is None
    assert out["model_id"] == "atria_stroke_2013"
    assert out["disease"] == "cvd"
    assert out["axis"] == "prognosis"


def test_negative_age_rejected():
    with pytest.raises(ValueError):
        atria_score(**{**NONE_NO_STROKE, "age": -1})
