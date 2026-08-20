"""Tests for PREDICT Breast v2.2 (Pharoah; Winton Centre reference impl)."""

import pytest

from cancerverse_baseline.breast.prognosis import predict_breast
from cancerverse_baseline.breast.prognosis.predict import (
    CHEMO_BETA,
    ER_NEG,
    ER_POS,
    GRADE_UNKNOWN,
    HORMONE_EXTENDED_BETA,
    SCREEN_UNKNOWN,
)

# A typical ER-positive, node-positive case.
CASE = dict(age=57, size_mm=29, nodes=5, grade=2, er_positive=True, her2=1, ki67=1)


def test_survival_is_a_probability_and_decreases_with_time():
    survivals = [
        predict_breast(**CASE, years=y)["survival_no_treatment"] for y in (1, 5, 10, 15)
    ]
    assert all(0.0 < s < 1.0 for s in survivals)
    assert survivals == sorted(survivals, reverse=True)


def test_treatment_always_helps_or_is_neutral():
    """Every treatment log-HR in the model is <= 0, so benefit cannot be negative."""
    out = predict_breast(
        **CASE,
        chemo_generation=3,
        hormone=True,
        trastuzumab=True,
        bisphosphonate=True,
        years=10,
    )
    assert out["benefit"] > 0
    assert out["survival_with_treatment"] > out["survival_no_treatment"]

    none = predict_breast(**CASE, years=10)
    assert none["benefit"] == pytest.approx(0.0, abs=1e-12)


def test_third_generation_chemo_beats_second():
    g2 = predict_breast(**CASE, chemo_generation=2, years=10)["benefit"]
    g3 = predict_breast(**CASE, chemo_generation=3, years=10)["benefit"]
    assert g3 > g2 > 0
    assert CHEMO_BETA[3] < CHEMO_BETA[2] < CHEMO_BETA[0]


def test_hormone_therapy_only_helps_er_positive_disease():
    er_pos = predict_breast(**{**CASE, "er_positive": True}, hormone=True, years=10)
    er_neg = predict_breast(
        **{**CASE, "er_positive": False, "ki67": 9}, hormone=True, years=10
    )
    assert er_pos["benefit"] > 0
    assert er_neg["benefit"] == pytest.approx(0.0, abs=1e-12)


def test_extended_endocrine_effect_only_appears_after_year_10():
    """The extra -0.26 log-HR applies to years 11-15 only (ATLAS/aTTom)."""
    b10 = predict_breast(**CASE, hormone=True, years=10)["benefit"]
    b15 = predict_breast(**CASE, hormone=True, years=15)["benefit"]
    assert b15 > b10
    assert HORMONE_EXTENDED_BETA < 0


def test_trastuzumab_requires_her2_positive():
    her2_pos = predict_breast(**{**CASE, "her2": 1}, trastuzumab=True, years=10)
    her2_neg = predict_breast(**{**CASE, "her2": 0}, trastuzumab=True, years=10)
    assert her2_pos["benefit"] > 0
    assert her2_neg["benefit"] == pytest.approx(0.0, abs=1e-12)


def test_worse_tumour_features_lower_survival():
    base = predict_breast(**CASE, years=10)["survival_no_treatment"]
    for field, worse_value in (("size_mm", 60), ("nodes", 15), ("grade", 3)):
        worse = predict_breast(**{**CASE, field: worse_value}, years=10)[
            "survival_no_treatment"
        ]
        assert worse < base, field


def test_er_negative_uses_different_fractional_polynomials_not_just_betas():
    """The ER strata differ in transform, not only in coefficient value."""
    assert "age_mfp2_center" in ER_POS  # ER+ has a second age FP term
    assert "age_mfp2_center" not in ER_NEG  # ER- has a plain linear age term
    assert ER_POS["size_beta"] != ER_NEG["size_beta"]
    assert ER_NEG["screen_beta"] == 0.0  # screen detection unused when ER-


def test_er_negative_collapses_grade_to_binary():
    """Grade 2 and 3 score identically when ER-negative; grade 1 differs."""
    kwargs = dict(age=57, size_mm=29, nodes=5, er_positive=False, her2=0, years=10)
    g1 = predict_breast(**kwargs, grade=1)["prognostic_index"]
    g2 = predict_breast(**kwargs, grade=2)["prognostic_index"]
    g3 = predict_breast(**kwargs, grade=3)["prognostic_index"]
    assert g2 == pytest.approx(g3)
    assert g1 < g2


def test_unknown_inputs_use_the_published_imputation_constants():
    assert GRADE_UNKNOWN == 2.13
    assert SCREEN_UNKNOWN == 0.204
    # grade=9 must land between grade 2 and grade 3 for ER-positive disease.
    g2 = predict_breast(**{**CASE, "grade": 2}, years=10)["prognostic_index"]
    g3 = predict_breast(**{**CASE, "grade": 3}, years=10)["prognostic_index"]
    g9 = predict_breast(**{**CASE, "grade": 9}, years=10)["prognostic_index"]
    assert g2 < g9 < g3


def test_ki67_ignored_when_er_negative():
    a = predict_breast(**{**CASE, "er_positive": False, "ki67": 1}, years=10)
    b = predict_breast(**{**CASE, "er_positive": False, "ki67": 0}, years=10)
    assert a["prognostic_index"] == pytest.approx(b["prognostic_index"])


def test_invalid_inputs():
    with pytest.raises(ValueError, match="years"):
        predict_breast(**CASE, years=20)
    with pytest.raises(ValueError, match="grade"):
        predict_breast(**{**CASE, "grade": 4}, years=10)
    with pytest.raises(ValueError, match="her2"):
        predict_breast(**{**CASE, "her2": 2}, years=10)
    with pytest.raises(ValueError, match="chemo_generation"):
        predict_breast(**CASE, chemo_generation=1, years=10)
    with pytest.raises(ValueError, match="nodes"):
        predict_breast(**{**CASE, "nodes": -1}, years=10)


def test_metadata_and_dual_axis_export():
    out = predict_breast(**CASE, years=10)
    assert out["model_id"] == "predict_breast"
    assert out["disease"] == "breast"
    assert out["axis"] == "prognosis"
    # The same model backs the response cell.
    from cancerverse_baseline.breast.response import predict_breast as response_export

    assert response_export is predict_breast
