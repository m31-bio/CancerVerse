"""Tests for PLCOm2012 lung detection model."""

import math

import pytest

from mayo_baseline.lung.detection import coefficients as C
from mayo_baseline.lung.detection import plcom2012_predict
from mayo_baseline.lung.detection.plcom2012 import (
    linear_predictor,
    smoking_intensity_term,
)

# Reference profile: every continuous term sits on its centering value and every
# binary term is absent, so the logit reduces to intercept + smoking-intensity term.
CENTERED = dict(
    age=62,
    race="white",
    education_level=4,
    bmi=27,
    copd=False,
    personal_cancer_history=False,
    family_history_lung_cancer=False,
    current_smoker=False,
    smoking_duration_years=27,
    quit_years=10,
)


def test_centered_profile_reduces_to_intercept_plus_intensity():
    lp = linear_predictor(**CENTERED, cigarettes_per_day=10)
    # cpd=10 → (10/10)**-1 = 1 → term = 1 - 0.4021541613
    assert lp == pytest.approx(
        C.INTERCEPT + C.SMOKING_INTENSITY * (1.0 - C.SMOKING_INTENSITY_CENTER)
    )


def test_smoking_intensity_transform():
    assert smoking_intensity_term(80) == pytest.approx(0.125 - C.SMOKING_INTENSITY_CENTER)
    # Non-linear and decreasing in cigarettes/day: the transform is (cpd/10)**-1.
    assert smoking_intensity_term(20) > smoking_intensity_term(40)


def test_risk_monotonic_in_established_risk_factors():
    base = plcom2012_predict(**CENTERED, cigarettes_per_day=20)["risk"]
    for factor in ("copd", "personal_cancer_history", "family_history_lung_cancer"):
        worse = plcom2012_predict(
            **{**CENTERED, factor: True}, cigarettes_per_day=20
        )["risk"]
        assert worse > base, factor
    older = plcom2012_predict(**{**CENTERED, "age": 70}, cigarettes_per_day=20)["risk"]
    assert older > base
    longer = plcom2012_predict(
        **{**CENTERED, "smoking_duration_years": 40}, cigarettes_per_day=20
    )["risk"]
    assert longer > base


def test_longer_quit_time_lowers_risk():
    recent = plcom2012_predict(**{**CENTERED, "quit_years": 2}, cigarettes_per_day=20)
    distant = plcom2012_predict(**{**CENTERED, "quit_years": 20}, cigarettes_per_day=20)
    assert distant["risk"] < recent["risk"]


def test_current_smoker_term_matches_table2():
    former = linear_predictor(**{**CENTERED, "quit_years": 0}, cigarettes_per_day=20)
    current = linear_predictor(
        **{**CENTERED, "current_smoker": True, "quit_years": 0}, cigarettes_per_day=20
    )
    assert current - former == pytest.approx(C.SMOKING_STATUS_CURRENT)


def test_race_offsets_match_table2():
    white = linear_predictor(**CENTERED, cigarettes_per_day=20)
    for race, beta in C.RACE.items():
        lp = linear_predictor(**{**CENTERED, "race": race}, cigarettes_per_day=20)
        assert lp - white == pytest.approx(beta), race


def test_race_aliases_and_normalisation():
    canonical = plcom2012_predict(
        **{**CENTERED, "race": "native_hawaiian_pacific_islander"}, cigarettes_per_day=20
    )
    alias = plcom2012_predict(
        **{**CENTERED, "race": "Native Hawaiian / Pacific Islander"}, cigarettes_per_day=20
    )
    assert alias["risk"] == pytest.approx(canonical["risk"])
    assert alias["race_group"] == "native_hawaiian_pacific_islander"


def test_never_smoker_and_invalid_inputs_rejected():
    with pytest.raises(ValueError, match="ever-smokers"):
        plcom2012_predict(**CENTERED, cigarettes_per_day=0)
    with pytest.raises(ValueError, match="ever-smokers"):
        plcom2012_predict(
            **{**CENTERED, "smoking_duration_years": 0}, cigarettes_per_day=20
        )
    with pytest.raises(ValueError, match="education_level"):
        plcom2012_predict(**{**CENTERED, "education_level": 7}, cigarettes_per_day=20)
    with pytest.raises(ValueError, match="race"):
        plcom2012_predict(**{**CENTERED, "race": "unknown"}, cigarettes_per_day=20)
    with pytest.raises(ValueError, match="quit_years"):
        plcom2012_predict(**{**CENTERED, "quit_years": -1}, cigarettes_per_day=20)
    with pytest.raises(ValueError, match="current smokers"):
        plcom2012_predict(
            **{**CENTERED, "current_smoker": True, "quit_years": 5}, cigarettes_per_day=20
        )


def test_logit_and_risk_are_consistent():
    out = plcom2012_predict(**CENTERED, cigarettes_per_day=20)
    lp = out["linear_predictor"]
    assert out["risk"] == pytest.approx(math.exp(lp) / (1.0 + math.exp(lp)))


def test_metadata():
    out = plcom2012_predict(**CENTERED, cigarettes_per_day=20)
    assert out["model_id"] == "plcom2012"
    assert out["axis"] == "detection"
    assert out["disease"] == "lung"
    assert out["horizon_years"] == 6
