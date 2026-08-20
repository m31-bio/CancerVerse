"""Tests for BCRAT / Gail model (Gail et al. 1989; NCI DCEG BCRA v2.1.2)."""

import math

import pytest

from cancerverse_baseline.breast.detection import (
    bcrat_predict,
    categorise,
    relative_risk,
)
from cancerverse_baseline.breast.detection import coefficients as C


def test_categorise_reference_profile_is_all_zero():
    cats = categorise(
        age=50,
        race="white",
        n_biopsies=0,
        atypical_hyperplasia="unknown",
        age_menarche=14,
        age_first_birth=19,
        n_relatives=0,
    )
    assert cats == {"nb": 0.0, "am": 0.0, "af": 0.0, "nr": 0.0, "r_hyp": 1.0}


def test_relative_risk_reference_profile_is_unity():
    cats = categorise(
        age=50,
        race="white",
        n_biopsies=0,
        atypical_hyperplasia="unknown",
        age_menarche=14,
        age_first_birth=19,
        n_relatives=0,
    )
    rr_u50, rr_50p = relative_risk(cats, "white")
    assert rr_u50 == pytest.approx(1.0)
    assert rr_50p == pytest.approx(1.0)


def test_relative_risk_formula_matches_published_linear_predictor():
    # relative.risk.R: LP1 = NB*B1 + AM*B2 + AF*B3 + NR*B4 + AF*NR*B6 + log(R_Hyp)
    cats = categorise(
        age=45,
        race="white",
        n_biopsies=1,
        atypical_hyperplasia="yes",
        age_menarche=11,
        age_first_birth=32,
        n_relatives=2,
    )
    beta = C.BETA["white"]
    expected_lp1 = (
        beta[0] * cats["nb"]
        + beta[1] * cats["am"]
        + beta[2] * cats["af"]
        + beta[3] * cats["nr"]
        + beta[5] * cats["af"] * cats["nr"]
        + math.log(cats["r_hyp"])
    )
    rr_u50, rr_50p = relative_risk(cats, "white")
    assert rr_u50 == pytest.approx(math.exp(expected_lp1))
    assert rr_50p == pytest.approx(math.exp(expected_lp1 + beta[4] * cats["nb"]))


def test_lowest_risk_profile_10y_risk_is_low_single_digit_percent():
    out = bcrat_predict(
        start_age=50,
        end_age=60,
        race="white",
        n_biopsies=0,
        atypical_hyperplasia="unknown",
        age_menarche=14,
        age_first_birth=19,
        n_relatives=0,
    )
    # Reference-covariate risk should track the unadjusted SEER 10y rate for
    # a 50-year-old white woman, on the order of a couple of percent.
    assert 0.01 < out["risk"] < 0.04


def test_high_risk_profile_exceeds_average_of_same_age():
    high = bcrat_predict(
        start_age=45,
        end_age=55,
        race="white",
        n_biopsies=1,
        atypical_hyperplasia="yes",
        age_menarche=11,
        age_first_birth=32,
        n_relatives=2,
    )
    avg = bcrat_predict(
        start_age=45,
        end_age=55,
        race="white",
        n_biopsies=0,
        atypical_hyperplasia="unknown",
        age_menarche=14,
        age_first_birth=19,
        n_relatives=0,
    )
    assert high["risk"] > avg["risk"]
    assert high["relative_risk"]["under_50"] > 1.0


def test_lifetime_projection_matches_seer_order_of_magnitude():
    out = bcrat_predict(
        start_age=20,
        end_age=90,
        race="white",
        n_biopsies=0,
        atypical_hyperplasia="unknown",
        age_menarche=14,
        age_first_birth=19,
        n_relatives=0,
    )
    # SEER-quoted US lifetime invasive breast cancer risk is ~12-13%; the
    # lowest-risk reference profile should sit below the population average.
    assert out["risk"] < out["average_risk_same_age"]
    assert 0.03 < out["risk"] < 0.13


def test_end_age_must_exceed_start_age():
    with pytest.raises(ValueError, match="end_age"):
        bcrat_predict(
            start_age=55,
            end_age=45,
            race="white",
            n_biopsies=0,
            atypical_hyperplasia="unknown",
            age_menarche=14,
            age_first_birth=19,
            n_relatives=0,
        )


def test_rejects_ages_outside_hazard_table_range():
    with pytest.raises(ValueError, match="20"):
        bcrat_predict(
            start_age=10,
            end_age=20,
            race="white",
            n_biopsies=0,
            atypical_hyperplasia="unknown",
            age_menarche=14,
            age_first_birth=19,
            n_relatives=0,
        )


def test_metadata():
    out = bcrat_predict(
        start_age=50,
        end_age=60,
        race="white",
        n_biopsies=0,
        atypical_hyperplasia="unknown",
        age_menarche=14,
        age_first_birth=19,
        n_relatives=0,
    )
    assert out["model_id"] == "bcrat"
    assert out["axis"] == "detection"
    assert out["disease"] == "breast"
