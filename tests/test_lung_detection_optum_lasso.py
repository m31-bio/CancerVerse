"""Unit maths for the Optum EHR LASSO model.

The parity suite compares whole predictions against PatientLevelPrediction.
These tests cover the things parity cannot: that the shipped data file still
carries the numbers the study package published, that the API's two input
shapes agree, and that the decode rule printed in the module docstring actually
holds for every covariate.
"""

from __future__ import annotations

import json
import math

import pytest

from cancerverse_baseline.lung.detection.optum_lung_lasso import (
    _DATA,
    BETAS,
    COEFFICIENTS,
    INTERCEPT,
    SMOKING,
    age_group_covariate_id,
    describe,
    linear_predictor,
    optum_lung_lasso_predict,
)

RAW = json.loads(_DATA.read_text())


def test_the_model_is_the_one_the_paper_describes():
    """The four facts that identify this fitted model, read from the artifact
    rather than from the paper: intercept, coefficient count, development
    database and cohort size. The paper reports 278 covariates; the study
    package's model.json holds 279 non-zero betas, of which one is the
    intercept.
    """
    assert INTERCEPT == -8.8024
    assert len(BETAS) == 278
    assert RAW["n_candidate_covariates"] == 16633
    assert RAW["development_database"] == "cdm_optum_ehr_v1705"
    assert RAW["n_patients"] == 4_777_606


def test_the_candidate_set_accounts_for_every_covariate():
    """16,633 kept + 22,660 dropped as infrequent + 2 dropped as redundant is
    the 39,295 rows of normFactors. If the extraction ever loses a slice, this
    arithmetic stops closing."""
    total = (RAW["n_candidate_covariates"] + RAW["n_removed_infrequent"]
             + RAW["n_removed_redundant"])
    assert total == 39_295
    assert RAW["removed_redundant"] == [10003, 8532001]


def test_every_coefficient_agrees_with_the_unrounded_copy():
    """`model.json` is what PatientLevelPrediction scores with and it stores
    four decimal places; `covariateImportance.csv` in the same directory stores
    the same coefficients unrounded. The data file keeps both, and they must
    still agree, this is the check that would catch a coefficient edited by
    hand in either column.
    """
    for c in RAW["coefficients"]:
        assert round(c["beta_unrounded"], 4) == c["beta"], c["covariate_id"]


def test_the_covariate_id_decode_rule_holds_everywhere():
    """covariateId = conceptId * 1000 + analysisId, with conceptId 0 for the
    two analyses that index a bucket instead of an OMOP concept (age band, and
    the study package's own smoking covariate)."""
    for cid, c in COEFFICIENTS.items():
        assert cid % 1000 == c["analysis_id"]
        if c["concept_id"]:
            assert cid // 1000 == c["concept_id"]
        else:
            assert c["analysis_id"] in {3, 639}


def test_intercept_alone_is_the_floor_of_the_model():
    out = optum_lung_lasso_predict({})
    assert out["linear_predictor"] == pytest.approx(INTERCEPT)
    assert out["risk"] == pytest.approx(1 / (1 + math.exp(-INTERCEPT)))
    assert out["n_covariates_used"] == 0
    assert out["model_id"] == "optum_lung_lasso"
    assert out["disease"] == "lung"
    assert out["axis"] == "detection"
    assert out["horizon_days"] == 1095


def test_a_set_of_ids_and_a_mapping_of_ones_are_the_same_input():
    ids = [3639, 13003, 8527004]
    assert (linear_predictor(ids)
            == pytest.approx(linear_predictor(dict.fromkeys(ids, 1.0))))


def test_the_linear_predictor_is_the_sum_of_the_betas_it_names():
    ids = [3639, 13003, 8527004, 255573210]
    assert linear_predictor(ids) == pytest.approx(
        INTERCEPT + sum(BETAS[i] for i in ids)
    )


def test_unknown_ids_are_ignored_and_counted():
    out = optum_lung_lasso_predict({3639: 1, 987654321987: 1})
    assert out["linear_predictor"] == pytest.approx(INTERCEPT + BETAS[3639])
    assert out["n_covariates_used"] == 1
    assert out["n_covariates_ignored"] == 1


def test_smoking_covariates_are_ordered_the_way_the_study_sql_orders_them():
    """`R/smoking.R` maps never=1, previously/not currently=2, current=3, then
    forms `value * 1000 + 639`. The fitted betas run the same way: never is
    protective, former positive, current the largest coefficient in the model.
    """
    assert SMOKING == {"never": 1639, "former": 2639, "current": 3639}
    assert BETAS[SMOKING["never"]] < 0 < BETAS[SMOKING["former"]] < BETAS[SMOKING["current"]]
    assert max(BETAS.values()) == BETAS[SMOKING["current"]]


def test_age_group_ids_match_the_labels_the_study_package_ships():
    for age, cid in ((45, 9003), (52, 10003), (59, 11003), (60, 12003), (66, 13003)):
        assert age_group_covariate_id(age) == cid
    # 50-54 was dropped before fitting as the redundant reference band, so it
    # has no coefficient. Returning the id and not finding it is correct.
    assert 10003 not in BETAS
    assert describe(9003)["name"].startswith("age group")
    with pytest.raises(ValueError):
        age_group_covariate_id(-1)


def test_describe_returns_none_outside_the_model():
    assert describe(987654321987) is None
    assert describe(3020891702)["concept_id"] == 3020891


def test_risk_stays_a_probability_at_both_extremes():
    positives = [c for c, b in BETAS.items() if b > 0]
    negatives = [c for c, b in BETAS.items() if b < 0]
    high = optum_lung_lasso_predict(positives)["risk"]
    low = optum_lung_lasso_predict(negatives)["risk"]
    assert 0.0 < low < optum_lung_lasso_predict({})["risk"] < high < 1.0


def test_a_string_id_is_refused_rather_than_silently_dropped():
    """An iterable of strings would otherwise iterate to characters or match
    nothing, and score as a healthy patient."""
    with pytest.raises(TypeError):
        optum_lung_lasso_predict(["3639"])
