"""Tests for the Kunzmann esophageal adenocarcinoma points model."""

import pytest

from cancerverse_baseline.esophageal.detection import kunzmann_predict
from cancerverse_baseline.esophageal.detection.kunzmann import (
    MAX_POINTS,
    REFERRAL_THRESHOLD,
    age_points,
    bmi_points,
)

LOWEST = dict(age=52, male=False, bmi=22, smoking="never", esophageal_condition=False)


def test_lowest_and_highest_risk_profiles_span_the_published_range():
    assert kunzmann_predict(**LOWEST)["score"] == 0.0
    highest = kunzmann_predict(
        age=70, male=True, bmi=40, smoking="current", esophageal_condition=True
    )
    assert highest["score"] == MAX_POINTS == 15.0


def test_age_bands_from_table_2():
    assert age_points(50) == 0.0
    assert age_points(54.9) == 0.0
    assert age_points(55) == 1.5
    assert age_points(59.9) == 1.5
    assert age_points(60) == 2.5
    assert age_points(64.9) == 2.5
    assert age_points(65) == 3.5
    assert age_points(90) == 3.5


def test_bmi_bands_from_table_2():
    assert bmi_points(24.9) == 0.0
    assert bmi_points(25) == 1.0
    assert bmi_points(29.9) == 1.0
    assert bmi_points(30) == 1.5
    assert bmi_points(34.9) == 1.5
    assert bmi_points(35) == 2.5


def test_male_sex_is_the_single_largest_factor():
    """4.0 of 15 points — half the referral threshold, from sex alone."""
    male_only = kunzmann_predict(**{**LOWEST, "male": True})
    assert male_only["score"] == 4.0
    assert male_only["components"]["sex"] == 4.0
    # Larger than any other single component's maximum.
    assert max(age_points(90), bmi_points(40), 3.5, 1.5) < 4.0


def test_smoking_bands():
    for status, expected in (("never", 0.0), ("former", 2.0), ("current", 3.5)):
        out = kunzmann_predict(**{**LOWEST, "smoking": status})
        assert out["components"]["smoking"] == expected, status


def test_esophageal_condition_adds_1_5():
    out = kunzmann_predict(**{**LOWEST, "esophageal_condition": True})
    assert out["score"] == 1.5


def test_referral_threshold_is_8_points():
    assert REFERRAL_THRESHOLD == 8.0
    # 65yo male, obese, never smoker: 3.5 + 4.0 + 1.5 + 0 + 0 = 9.0
    refer = kunzmann_predict(
        age=65, male=True, bmi=32, smoking="never", esophageal_condition=False
    )
    assert refer["score"] == 9.0
    assert refer["refer_for_screening"] is True

    # 60yo male, normal BMI, never smoker: 2.5 + 4.0 = 6.5
    no_refer = kunzmann_predict(
        age=60, male=True, bmi=22, smoking="never", esophageal_condition=False
    )
    assert no_refer["score"] == 6.5
    assert no_refer["refer_for_screening"] is False


def test_components_sum_to_score():
    out = kunzmann_predict(
        age=67, male=True, bmi=31, smoking="former", esophageal_condition=True
    )
    assert sum(out["components"].values()) == out["score"]
    assert out["score"] == 3.5 + 4.0 + 1.5 + 2.0 + 1.5


def test_model_refuses_ages_below_its_development_range():
    with pytest.raises(ValueError, match="50"):
        kunzmann_predict(**{**LOWEST, "age": 45})


def test_invalid_inputs():
    with pytest.raises(ValueError, match="smoking"):
        kunzmann_predict(**{**LOWEST, "smoking": "sometimes"})
    with pytest.raises(ValueError, match="bmi"):
        kunzmann_predict(**{**LOWEST, "bmi": 0})


def test_metadata():
    out = kunzmann_predict(**LOWEST)
    assert out["model_id"] == "kunzmann"
    assert out["axis"] == "detection"
    assert out["disease"] == "esophageal"
    assert out["risk"] is None
