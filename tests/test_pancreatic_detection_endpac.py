"""Tests for the END-PAC score (Sharma et al., Gastroenterology 2018, Table 1)."""

import pytest

from cancerverse_baseline.pancreatic.detection import endpac as E
from cancerverse_baseline.pancreatic.detection import endpac_predict


def test_worked_contrast_between_pc_related_and_ordinary_diabetes():
    """The model's whole purpose: separate diabetes caused by a tumour from
    ordinary type 2. A big glucose jump with weight LOSS in an older patient is
    the pancreatic-cancer picture; a small rise with weight GAIN in a younger
    one is type 2."""
    pc_like = endpac_predict(
        glucose_at_diabetes_mg_dl=180,
        glucose_one_year_before_mg_dl=95,
        weight_change_kg=-7.0,
        age_at_diabetes_onset=72,
    )
    t2_like = endpac_predict(
        glucose_at_diabetes_mg_dl=130,
        glucose_one_year_before_mg_dl=118,
        weight_change_kg=5.0,
        age_at_diabetes_onset=52,
    )
    # PC-like: glucose +3 (cat 1->4... here 1->5), weight +6, age +1 = 11 (max)
    assert pc_like["score"] == 11 and pc_like["risk_band"] == "high"
    # T2-like: glucose 4-3=1, weight -4 (gain 4.0-5.9), age -1 = -4
    assert t2_like["score"] == -4 and t2_like["risk_band"] == "very_low"
    assert t2_like["components"] == {"glucose": 1, "weight": -4, "age": -1}


def test_weight_loss_scores_positive_not_negative():
    """Sign trap: losing weight raises the score, gaining lowers it."""
    assert E.weight_score(-7.0) == 6
    assert E.weight_score(0.0) == 0
    assert E.weight_score(7.0) == -6


def test_glucose_term_is_a_category_difference_not_mg_dl():
    """A rise 95 -> 130 mg/dL is category 1 -> 4, i.e. A = 3 (not 35)."""
    out = endpac_predict(
        glucose_at_diabetes_mg_dl=130,
        glucose_one_year_before_mg_dl=95,
        weight_change_kg=0.0,
        age_at_diabetes_onset=65,
    )
    assert out["bg_category_before"] == 1
    assert out["bg_category_now"] == 4
    assert out["components"]["glucose"] == 3


def test_risk_bands():
    assert E.HIGH_RISK_THRESHOLD == 3
    kw = dict(glucose_one_year_before_mg_dl=95, age_at_diabetes_onset=65)
    assert (
        endpac_predict(glucose_at_diabetes_mg_dl=130, weight_change_kg=0.0, **kw)[
            "risk_band"
        ]
        == "high"
    )  # score 3
    assert (
        endpac_predict(glucose_at_diabetes_mg_dl=130, weight_change_kg=5.0, **kw)[
            "risk_band"
        ]
        == "very_low"
    )  # score -1


def test_metadata():
    out = endpac_predict(
        glucose_at_diabetes_mg_dl=150,
        glucose_one_year_before_mg_dl=100,
        weight_change_kg=-3.0,
        age_at_diabetes_onset=65,
    )
    assert out["model_id"] == "endpac"
    assert out["axis"] == "detection"
    assert out["disease"] == "pancreatic"
    assert out["risk"] is None


def test_out_of_scope_glucose_pairs_are_rejected():
    """Found by the randomized invariant sweep: an unconstrained glucose pair
    yields scores outside the published range (a fall from diabetic to normal
    gave -9, against a stated glucose-term range of 1-4).

    Table 1 assigns BG categories 1-3 to the -1 year reading and 4-5 to the
    reading at diagnosis, so the model is defined only for someone who actually
    crossed into diabetes. Out-of-scope pairs now raise instead of returning a
    meaningless number.
    """
    ok = dict(
        glucose_at_diabetes_mg_dl=150,
        glucose_one_year_before_mg_dl=100,
        weight_change_kg=-3.0,
        age_at_diabetes_onset=65,
    )
    endpac_predict(**ok)  # in scope

    with pytest.raises(ValueError, match="new-onset diabetes"):
        endpac_predict(**{**ok, "glucose_at_diabetes_mg_dl": 110})
    with pytest.raises(ValueError, match="already have been diabetic"):
        endpac_predict(**{**ok, "glucose_one_year_before_mg_dl": 140})


def test_glucose_term_stays_within_the_published_1_to_4_range():
    for before in (95, 105, 120):
        for at in (130, 200):
            out = endpac_predict(
                glucose_at_diabetes_mg_dl=at,
                glucose_one_year_before_mg_dl=before,
                weight_change_kg=0.0,
                age_at_diabetes_onset=65,
            )
            assert 1 <= out["components"]["glucose"] <= 4
