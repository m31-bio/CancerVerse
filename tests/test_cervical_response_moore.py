"""Moore criteria, the contract, not the arithmetic.

Table 4's numbers are checked in tests/parity/test_moore_criteria_parity.py.
This file checks how the module behaves at its edges: the two inputs that
collapse a wider clinical variable (performance status, disease site), the
race factor's visibility, and the caller-facing guarantee that this returns a
band lookup and never a fitted probability.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.cervical.response.moore import (
    AXIS,
    DISEASE,
    MODEL_ID,
    RECURRENCE_INTERVAL_CUTOFF_MONTHS,
    moore_criteria_predict,
    moore_risk_factors,
)

BASELINE = dict(
    black_race=False, performance_status=0, disease_site="distant",
    prior_radiosensitizer=False, months_diagnosis_to_first_recurrence=24,
)


def test_the_result_identifies_itself_to_the_registry():
    out = moore_criteria_predict(**BASELINE)
    assert (out["model_id"], out["axis"], out["disease"]) == (
        MODEL_ID, AXIS, DISEASE) == ("moore_criteria", "response", "cervical")


def test_risk_is_none_because_this_model_produces_a_band_not_a_probability():
    assert moore_criteria_predict(**BASELINE)["risk"] is None


def test_zero_risk_factors_is_the_low_band():
    out = moore_criteria_predict(**BASELINE)
    assert out["risk_factor_count"] == 0
    assert out["band"] == 0
    assert out["band_label"] == "low risk (0-1 factors)"


def test_all_five_risk_factors_is_the_high_band():
    out = moore_criteria_predict(
        black_race=True, performance_status=2, disease_site="pelvic",
        prior_radiosensitizer=True, months_diagnosis_to_first_recurrence=3,
    )
    assert out["risk_factor_count"] == 5
    assert out["band"] == 2
    assert out["band_label"] == "high risk (4-5 factors)"


@pytest.mark.parametrize("count,band", [(0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2)])
def test_band_boundaries_match_the_papers_own_grouping(count, band):
    """Low 0-1, mid 2-3, high 4-5, the paper's own words, not a convention
    this module invented."""
    factors = ["black_race", "performance_status", "disease_site",
               "prior_radiosensitizer", "months_diagnosis_to_first_recurrence"]
    case = dict(BASELINE)
    for name in factors[:count]:
        if name == "black_race":
            case["black_race"] = True
        elif name == "performance_status":
            case["performance_status"] = 1
        elif name == "disease_site":
            case["disease_site"] = "pelvic"
        elif name == "prior_radiosensitizer":
            case["prior_radiosensitizer"] = True
        elif name == "months_diagnosis_to_first_recurrence":
            case["months_diagnosis_to_first_recurrence"] = 6
    out = moore_criteria_predict(**case)
    assert out["risk_factor_count"] == count
    assert out["band"] == band


# ---------------------------------------------------------------------------
# Performance status: a raw GOG/ECOG score, dichotomised internally at 0.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ps", [0])
def test_performance_status_zero_is_not_a_risk_factor(ps):
    out = moore_risk_factors(**{**BASELINE, "performance_status": ps})
    assert out["factors"]["performance_status_above_0"] is False


@pytest.mark.parametrize("ps", [1, 2, 3, 4])
def test_any_performance_status_above_zero_is_a_risk_factor(ps):
    """The paper's cut is PS > 0, not PS >= some higher grade, a GOG PS of 1
    (symptomatic but fully ambulatory) counts exactly the same as a PS of 4."""
    out = moore_risk_factors(**{**BASELINE, "performance_status": ps})
    assert out["factors"]["performance_status_above_0"] is True


@pytest.mark.parametrize("bad", [-1, 5, 1.5])
def test_performance_status_outside_0_to_4_is_refused(bad):
    with pytest.raises(ValueError, match="performance_status must be"):
        moore_risk_factors(**{**BASELINE, "performance_status": bad})


# ---------------------------------------------------------------------------
# Disease site: three levels in the source, two in the published factor, and
# the collapsing rule for "combined" is not stated in the paper.
# ---------------------------------------------------------------------------

def test_pelvic_site_is_the_risk_factor():
    out = moore_risk_factors(**{**BASELINE, "disease_site": "pelvic"})
    assert out["factors"]["pelvic_disease"] is True


def test_distant_site_is_not_the_risk_factor():
    out = moore_risk_factors(**{**BASELINE, "disease_site": "distant"})
    assert out["factors"]["pelvic_disease"] is False


def test_combined_site_is_scored_as_non_pelvic_and_the_inference_is_flagged():
    """This is the one place this module makes a call the paper does not
    make in prose. Table 3 tests "Pelvic vs. Non-pelvic" over a variable that
    Table 1/2 record as three levels (pelvic / distant / combined); nothing in
    the text says which side "combined" falls on. The plain reading of the
    binary label puts it on the non-pelvic side, and that is what this module
    does, but the caller is told, not left to assume it was settled.
    """
    out = moore_risk_factors(**{**BASELINE, "disease_site": "combined"})
    assert out["factors"]["pelvic_disease"] is False
    assert out["disease_site_collapsed_from_three_levels"] is True

    predicted = moore_criteria_predict(**{**BASELINE, "disease_site": "combined"})
    assert "never states this collapsing rule in prose" in predicted["notes"]


def test_an_unknown_disease_site_is_refused_rather_than_guessed():
    with pytest.raises(ValueError, match="disease_site must be one of"):
        moore_risk_factors(**{**BASELINE, "disease_site": "pelvic and distant"})


# ---------------------------------------------------------------------------
# Recurrence interval: continuous months, dichotomised at the paper's cutoff.
# ---------------------------------------------------------------------------

def test_the_cutoff_is_twelve_months_and_is_closed_on_the_short_side():
    assert RECURRENCE_INTERVAL_CUTOFF_MONTHS == 12.0
    at_cutoff = moore_risk_factors(
        **{**BASELINE, "months_diagnosis_to_first_recurrence": 12.0})
    just_over = moore_risk_factors(
        **{**BASELINE, "months_diagnosis_to_first_recurrence": 12.01})
    assert at_cutoff["factors"]["recurrence_within_1_year"] is True
    assert just_over["factors"]["recurrence_within_1_year"] is False


def test_recurrence_interval_is_measured_from_original_diagnosis_not_from_treatment():
    """A caller who passes the interval from the START OF THIS CHEMOTHERAPY
    rather than from the original cancer diagnosis would silently score the
    wrong thing, the module cannot detect that mistake, so it is named
    explicitly in the parameter's own docstring rather than left implicit.
    """
    out = moore_criteria_predict(
        **{**BASELINE, "months_diagnosis_to_first_recurrence": 6})
    assert out["risk_factors_present"]["recurrence_within_1_year"] is True


def test_a_negative_interval_is_refused():
    with pytest.raises(ValueError, match="must be >= 0"):
        moore_risk_factors(
            **{**BASELINE, "months_diagnosis_to_first_recurrence": -1})


# ---------------------------------------------------------------------------
# The race factor: present in the count, and always disclosed when it fires.
# ---------------------------------------------------------------------------

def test_black_race_is_counted_exactly_like_every_other_factor():
    with_race = moore_risk_factors(**{**BASELINE, "black_race": True})
    without = moore_risk_factors(**BASELINE)
    assert with_race["count"] - without["count"] == 1


def test_black_race_being_true_is_disclosed_in_notes():
    out = moore_criteria_predict(**{**BASELINE, "black_race": True})
    assert "race counted as a risk factor" in out["notes"]
    assert "not a biological claim" in out["notes"]


def test_black_race_being_false_says_nothing_extra():
    out = moore_criteria_predict(**{**BASELINE, "black_race": False})
    assert "race counted as a risk factor" not in out["notes"]


# ---------------------------------------------------------------------------
# GOG 240 prospective validation is attached only where the paper states a
# number in text, not invented for the band it left to a figure.
# ---------------------------------------------------------------------------

def test_prospective_validation_present_for_low_and_high_bands_only():
    low = moore_criteria_predict(**BASELINE)
    mid = moore_criteria_predict(**{**BASELINE, "performance_status": 1,
                                     "disease_site": "pelvic"})
    high = moore_criteria_predict(
        black_race=True, performance_status=2, disease_site="pelvic",
        prior_radiosensitizer=True, months_diagnosis_to_first_recurrence=3,
    )
    assert low["gog240_prospective_validation"] is not None
    assert mid["gog240_prospective_validation"] is None
    assert high["gog240_prospective_validation"] is not None


def test_the_interpretation_mentions_gog_240_only_when_it_has_a_number():
    low = moore_criteria_predict(**BASELINE)
    mid = moore_criteria_predict(**{**BASELINE, "performance_status": 1,
                                     "disease_site": "pelvic"})
    assert "GOG 240" in low["interpretation"]
    assert "GOG 240" not in mid["interpretation"]


# ---------------------------------------------------------------------------
# Citation and scope travel with the result.
# ---------------------------------------------------------------------------

def test_the_citation_names_both_the_index_paper_and_the_prospective_validation():
    out = moore_criteria_predict(**BASELINE)
    assert "10.1016/j.ygyno.2009.09.006" in out["citation"]
    assert "10.1158/1078-0432.CCR-15-1346" in out["citation"]


def test_scope_states_the_question_this_model_answers_and_the_one_it_does_not():
    out = moore_criteria_predict(**BASELINE)
    assert "cisplatin-based chemotherapy" in out["scope"]
    assert "not whether the patient will survive" in out["scope"]
    assert "not" in out["scope"] and "chemoradiation" in out["scope"]
