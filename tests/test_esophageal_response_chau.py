"""Chau index, the contract, not the arithmetic.

Every published constant is pinned in tests/parity/test_chau_eg_parity.py.
This file checks the behaviour a parity test cannot: the two inputs that are
dichotomised internally, the boundary cases at the published cut-points, and
whether the scope limits that make this model easy to misapply stay visible to
a caller who never reads the docstring.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.esophageal.response.chau_eg import (
    AXIS,
    DISEASE,
    MODEL_ID,
    chau_eg_predict,
    chau_eg_risk_factors,
)

BASELINE = dict(performance_status=1, liver_metastases=False,
                peritoneal_metastases=False, alkaline_phosphatase_u_l=80.0)


def test_the_result_identifies_itself_to_the_registry():
    out = chau_eg_predict(**BASELINE)
    assert (out["model_id"], out["axis"], out["disease"]) == (
        MODEL_ID, AXIS, DISEASE) == ("chau_eg", "response", "esophageal")


def test_risk_is_none_because_this_is_a_band_lookup():
    assert chau_eg_predict(**BASELINE)["risk"] is None


# ---------------------------------------------------------------------------
# The count, and the bands.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("count,band", [(0, 0), (1, 1), (2, 1), (3, 2), (4, 2)])
def test_band_boundaries_match_the_papers_grouping(count, band):
    """Good 0, moderate 1-2, poor 3-4, the paper's own words."""
    steps = [
        ("performance_status", 2),
        ("liver_metastases", True),
        ("peritoneal_metastases", True),
        ("alkaline_phosphatase_u_l", 150.0),
    ]
    case = dict(BASELINE)
    for name, value in steps[:count]:
        case[name] = value
    out = chau_eg_predict(**case)
    assert out["risk_factor_count"] == count
    assert out["band"] == band


def test_each_factor_moves_the_count_by_exactly_one():
    """The paper declines to weight them: "All four factors have a similar
    order of magnitude, therefore they can be combined into a simple prognostic
    score without loss of relevant information." So a factor with a bigger
    hazard ratio must not count for more.
    """
    base = chau_eg_risk_factors(**BASELINE)["count"]
    for change in ({"performance_status": 2}, {"liver_metastases": True},
                   {"peritoneal_metastases": True},
                   {"alkaline_phosphatase_u_l": 400.0}):
        assert chau_eg_risk_factors(**{**BASELINE, **change})["count"] - base == 1, change


def test_no_risk_factors_gives_the_best_published_survival():
    out = chau_eg_predict(**BASELINE)
    assert out["risk_factor_count"] == 0
    assert out["median_os_months_in_derivation"] == 11.8
    assert out["band_n_in_derivation"] == 239
    assert out["hazard_ratio_vs_good_risk"] == 1.0


def test_all_four_risk_factors_gives_the_worst():
    out = chau_eg_predict(performance_status=4, liver_metastases=True,
                          peritoneal_metastases=True,
                          alkaline_phosphatase_u_l=500.0)
    assert out["risk_factor_count"] == 4
    assert out["median_os_months_in_derivation"] == 4.1
    assert out["hazard_ratio_vs_good_risk"] == 3.59


# ---------------------------------------------------------------------------
# Performance status: a raw 0-4 score, dichotomised at >= 2 internally.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ps", [0, 1])
def test_performance_status_below_two_is_not_a_risk_factor(ps):
    out = chau_eg_risk_factors(**{**BASELINE, "performance_status": ps})
    assert out["factors"]["performance_status"] is False


@pytest.mark.parametrize("ps", [2, 3, 4])
def test_performance_status_two_or_worse_is_a_risk_factor(ps):
    """The paper's own grouping is 0-1 against 2-3. A PS of 4 does not appear
    in the cohort (only six patients were PS 3) but is accepted and scored with
    the poor group rather than refused, since it is unambiguously worse."""
    out = chau_eg_risk_factors(**{**BASELINE, "performance_status": ps})
    assert out["factors"]["performance_status"] is True


@pytest.mark.parametrize("bad", [-1, 5, 1.5])
def test_performance_status_outside_zero_to_four_is_refused(bad):
    with pytest.raises(ValueError, match="performance_status must be"):
        chau_eg_risk_factors(**{**BASELINE, "performance_status": bad})


# ---------------------------------------------------------------------------
# Alkaline phosphatase: a raw value against a cut-point that surprises people.
# ---------------------------------------------------------------------------

def test_the_alp_cut_point_is_closed_on_the_high_side():
    at = chau_eg_risk_factors(**{**BASELINE, "alkaline_phosphatase_u_l": 100.0})
    below = chau_eg_risk_factors(**{**BASELINE, "alkaline_phosphatase_u_l": 99.99})
    assert at["factors"]["alkaline_phosphatase"] is True
    assert below["factors"]["alkaline_phosphatase"] is False


def test_a_normal_alp_can_still_fire_this_factor_and_the_caller_is_told():
    """100 U/L sits at or below many laboratories' upper reference limit, so
    this factor fires for patients whose liver chemistry is entirely normal.
    That is the published cut-point and it is reproduced, but a clinician
    reading "alkaline phosphatase risk factor present" would reasonably assume
    an abnormal result, so the note says otherwise whenever it fires.
    """
    out = chau_eg_predict(**{**BASELINE, "alkaline_phosphatase_u_l": 110.0})
    assert out["risk_factors_present"]["alkaline_phosphatase"] is True
    assert "many laboratories' upper reference limit" in out["notes"]

    quiet = chau_eg_predict(**{**BASELINE, "alkaline_phosphatase_u_l": 60.0})
    assert "many laboratories' upper reference limit" not in quiet["notes"]


def test_a_negative_alp_is_refused():
    with pytest.raises(ValueError, match="must be >= 0"):
        chau_eg_risk_factors(**{**BASELINE, "alkaline_phosphatase_u_l": -1})


# ---------------------------------------------------------------------------
# Scope limits that decide whether this model may be used at all.
# ---------------------------------------------------------------------------

def test_the_squamous_histology_limit_is_stated_on_every_call():
    """4.6% of the derivation cohort was squamous. Running this on ESCC, the
    dominant histology across East Asia, is the same category error as running
    `kunzmann` on squamous disease, and it is not detectable from the inputs,
    so it has to be said in the output rather than only in a docstring.
    """
    out = chau_eg_predict(**BASELINE)
    assert "not a model for esophageal squamous cell carcinoma" in out["notes"]
    assert "88% ADENOCARCINOMA" in out["scope"]


def test_the_treatment_era_is_stated_on_every_call():
    out = chau_eg_predict(**BASELINE)
    assert "predating trastuzumab and checkpoint inhibitors" in out["notes"]


def test_the_scope_records_that_validation_was_never_completed():
    """The authors write that the index "requires validation" and name their
    own then-ongoing REAL-2 study as the intended set. No completed external
    validation is claimed by the paper, so none may be claimed here."""
    out = chau_eg_predict(**BASELINE)
    assert "requires validation" in out["scope"]
    assert "no completed external validation is claimed" in out["scope"].lower()


def test_the_output_is_named_as_the_derivation_cohorts_not_a_prediction():
    """These are the observed survival figures for the band the patient falls
    in, not an individualised forecast. The key names carry `in_derivation` for
    the same reason cibula_arrm's do."""
    out = chau_eg_predict(**BASELINE)
    for key in ("band_n_in_derivation", "median_os_months_in_derivation",
                "one_year_survival_pct_in_derivation"):
        assert key in out
    assert "not a fitted probability" in out["notes"]


def test_the_citation_names_where_each_half_came_from():
    out = chau_eg_predict(**BASELINE)
    assert "10.1200/jco.2004.08.154" in out["citation"]
    assert "Table 3" in out["citation"]
    assert "Results text" in out["citation"]
