"""Tests for the UK Biobank head and neck cancer risk model (McCarthy 2020)."""

import math

import pytest

from cancerverse_baseline.head_neck.detection import (
    ukb_hnc_linear_predictor,
    ukb_hnc_predict,
)

#: Reference category on every categorical, so each term can be switched on
#: one at a time and read off against Table III.
BASE = dict(
    age=60.0,
    male=False,
    smoking_status="never",
    townsend_quintile=1,
    bmi=25.0,
    alcohol_status="never",
    exercise_days="none",
    fruit_veg="under_5",
)


def test_all_reference_categories_leave_only_intercept_age_and_bmi():
    lp = ukb_hnc_linear_predictor(**BASE)
    expected = -9.54 + math.log(1.04) * 60.0 + math.log(0.96) * 25.0
    assert lp == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("field,value,odds_ratio", [
    ("male", True, 1.81),
    ("smoking_status", "previous", 1.59),
    ("smoking_status", "current", 3.10),
    ("townsend_quintile", 2, 1.30),
    ("townsend_quintile", 3, 1.14),
    ("townsend_quintile", 4, 1.81),
    ("townsend_quintile", 5, 1.66),
    ("alcohol_status", "previous", 3.26),
    ("alcohol_status", "current", 1.42),
    ("exercise_days", "1-4_days", 0.68),
    ("exercise_days", "5_or_more_days", 0.66),
    ("fruit_veg", "5_or_more", 0.71),
])
def test_each_term_moves_the_log_odds_by_ln_of_its_published_odds_ratio(
        field, value, odds_ratio):
    """Switching one category off its reference must move the linear predictor
    by exactly ln(OR) from Table III, and nothing else."""
    base_lp = ukb_hnc_linear_predictor(**BASE)
    lp = ukb_hnc_linear_predictor(**{**BASE, field: value})
    assert lp - base_lp == pytest.approx(math.log(odds_ratio), abs=1e-12)


def test_age_and_bmi_are_per_unit_and_not_centred():
    a = ukb_hnc_linear_predictor(**{**BASE, "age": 61.0})
    b = ukb_hnc_linear_predictor(**BASE)
    assert a - b == pytest.approx(math.log(1.04), abs=1e-12)

    c = ukb_hnc_linear_predictor(**{**BASE, "bmi": 26.0})
    assert c - b == pytest.approx(math.log(0.96), abs=1e-12)


def test_bmi_is_protective_and_the_sign_is_not_a_bug():
    """Higher BMI carried LOWER risk in this cohort (OR 0.96). Asserted so a
    future 'fix' to the sign fails here rather than silently shipping."""
    lean = ukb_hnc_predict(**{**BASE, "bmi": 20.0})["risk"]
    heavy = ukb_hnc_predict(**{**BASE, "bmi": 35.0})["risk"]
    assert heavy < lean


def test_previous_drinking_outranks_current_drinking():
    """The sick-quitter pattern in Table III: previous 3.26 vs current 1.42.
    Non-monotonic on purpose."""
    prev = ukb_hnc_predict(**{**BASE, "alcohol_status": "previous"})["risk"]
    curr = ukb_hnc_predict(**{**BASE, "alcohol_status": "current"})["risk"]
    never = ukb_hnc_predict(**BASE)["risk"]
    assert prev > curr > never


def test_deprivation_quintile_4_outranks_quintile_5():
    """Also non-monotonic in Table III: 1.81 at Q4 against 1.66 at Q5."""
    q4 = ukb_hnc_predict(**{**BASE, "townsend_quintile": 4})["risk"]
    q5 = ukb_hnc_predict(**{**BASE, "townsend_quintile": 5})["risk"]
    assert q4 > q5


def test_risk_brackets_the_cohort_base_rate():
    """232 incident cases in 397,179 observations is 0.058% over 7 years. The
    lowest- and highest-risk profiles the model can express must sit either
    side of that, or the intercept has been misread."""
    base_rate = 232 / 397179

    lowest = ukb_hnc_predict(
        age=40, male=False, smoking_status="never", townsend_quintile=1,
        bmi=40.0, alcohol_status="never", exercise_days="5_or_more_days",
        fruit_veg="5_or_more")["risk"]
    highest = ukb_hnc_predict(
        age=70, male=True, smoking_status="current", townsend_quintile=4,
        bmi=18.0, alcohol_status="previous", exercise_days="none",
        fruit_veg="under_5")["risk"]

    assert lowest < base_rate < highest
    assert lowest > 0 and highest < 0.5


def test_predict_shape():
    out = ukb_hnc_predict(**BASE)
    assert 0.0 < out["risk"] < 1.0
    assert out["horizon_years"] == 7
    assert out["model_id"] == "ukb_hnc"
    assert out["disease"] == "head_neck"
    assert out["axis"] == "detection"
    assert "C32" in out["notes"], "the laryngeal exclusion must be stated"


@pytest.mark.parametrize("field,bad", [
    ("smoking_status", "ex-smoker"),
    ("alcohol_status", "occasional"),
    ("townsend_quintile", 0),
    ("townsend_quintile", 6),
    ("exercise_days", "daily"),
    ("fruit_veg", "lots"),
])
def test_unknown_categories_are_rejected_rather_than_treated_as_reference(
        field, bad):
    """A typo must not silently score as the reference category."""
    with pytest.raises(ValueError):
        ukb_hnc_predict(**{**BASE, field: bad})


@pytest.mark.parametrize("field,bad", [("age", 0), ("age", 130), ("bmi", 2), ("bmi", 200)])
def test_implausible_continuous_values_are_rejected(field, bad):
    with pytest.raises(ValueError):
        ukb_hnc_predict(**{**BASE, field: bad})
