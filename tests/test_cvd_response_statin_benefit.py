"""The derived statin-benefit calculation.

There is no external reference to check this against — that is the point of
its `derived_not_published` marker. What can be tested is everything else: the
trial effect matches the paper, the arithmetic identity holds, the confidence
interval runs the right way, and the assumptions travel with the result.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.cvd.response import (
    cvd_statin_benefit_predict,
    ldl_reduction_mmol,
)
from cancerverse_baseline.cvd.response.statin_benefit import MMOL_PER_MG_DL, RATE_RATIO


def test_rate_ratios_are_the_published_ctt_values():
    """Verbatim from the CTT 2010 abstract, PMID 21067804."""
    assert RATE_RATIO["major_vascular_events"] == (0.78, 0.76, 0.80)
    assert RATE_RATIO["all_cause_mortality"] == (0.90, 0.87, 0.93)


def test_the_arithmetic_identity():
    """ARR = baseline x (1 - RR^delta). Checked by hand at delta = 1, where
    the rate ratio applies once and the answer is legible."""
    out = cvd_statin_benefit_predict(baseline_risk=0.20,
                                     ldl_reduction_mmol_l=1.0)
    assert out["relative_risk_reduction"] == pytest.approx(1 - 0.78)
    assert out["absolute_risk_reduction"] == pytest.approx(0.20 * 0.22)
    assert out["treated_risk"] == pytest.approx(0.20 - 0.20 * 0.22)
    assert out["number_needed_to_treat"] == pytest.approx(1 / (0.20 * 0.22))


def test_the_effect_compounds_with_the_size_of_the_reduction():
    """Two mmol/L is RR^2, not 2 x the one-mmol effect — the difference is the
    whole reason this is exponentiated rather than multiplied."""
    one = cvd_statin_benefit_predict(baseline_risk=0.2, ldl_reduction_mmol_l=1.0)
    two = cvd_statin_benefit_predict(baseline_risk=0.2, ldl_reduction_mmol_l=2.0)
    assert two["relative_risk_reduction"] == pytest.approx(1 - 0.78**2)
    assert two["relative_risk_reduction"] < 2 * one["relative_risk_reduction"]


def test_absolute_benefit_scales_with_baseline_risk():
    """The proportional effect is constant; the absolute one is not. This is
    the entire clinical argument for risk-stratified prevention."""
    low = cvd_statin_benefit_predict(baseline_risk=0.05, ldl_reduction_mmol_l=1.0)
    high = cvd_statin_benefit_predict(baseline_risk=0.30, ldl_reduction_mmol_l=1.0)
    assert low["relative_risk_reduction"] == pytest.approx(
        high["relative_risk_reduction"]
    )
    assert high["absolute_risk_reduction"] > 5 * low["absolute_risk_reduction"] * 0.99
    assert high["number_needed_to_treat"] < low["number_needed_to_treat"]


def test_the_confidence_interval_runs_the_right_way():
    """A SMALLER rate ratio is a LARGER benefit, so CTT's lower RR bound gives
    the upper ARR bound. Getting this backwards is easy and silent."""
    out = cvd_statin_benefit_predict(baseline_risk=0.20,
                                     ldl_reduction_mmol_l=1.0)
    lo, hi = out["arr_ci"]
    assert lo < out["absolute_risk_reduction"] < hi
    assert lo == pytest.approx(0.20 * (1 - 0.80))
    assert hi == pytest.approx(0.20 * (1 - 0.76))


def test_units():
    assert ldl_reduction_mmol(mmol_l=1.0) == 1.0
    assert ldl_reduction_mmol(mg_dl=38.67) == pytest.approx(1.0)
    assert pytest.approx(1 / 38.67) == MMOL_PER_MG_DL
    with pytest.raises(ValueError, match="exactly one"):
        ldl_reduction_mmol(mmol_l=1.0, mg_dl=38.67)
    with pytest.raises(ValueError, match="exactly one"):
        ldl_reduction_mmol()


def test_zero_reduction_is_zero_benefit():
    out = cvd_statin_benefit_predict(baseline_risk=0.2, ldl_reduction_mmol_l=0.0)
    assert out["absolute_risk_reduction"] == 0.0
    assert out["number_needed_to_treat"] is None


def test_it_composes_with_a_verified_risk_model():
    """The intended use: a baseline from PREVENT, which IS checked against a
    reference, then this transformation on top."""
    import cancerverse_baseline as mb

    baseline = mb.predict(
        "prevent", sex="female", age=60, total_chol_mg_dl=240, hdl_mg_dl=45,
        sbp=145, diabetes=False, smoker=True, bmi=29, egfr=85,
        htn_meds=True, statin=False,
    )["risk"]
    out = cvd_statin_benefit_predict(
        baseline_risk=baseline, ldl_reduction_mg_dl=50,
        baseline_risk_source="prevent 10-year total_cvd",
    )
    assert 0 < out["absolute_risk_reduction"] < baseline
    assert out["baseline_risk_source"] == "prevent 10-year total_cvd"


def test_the_result_carries_its_assumptions():
    """A derived number that travels without its caveats is the failure mode
    this module exists to avoid."""
    out = cvd_statin_benefit_predict(baseline_risk=0.2, ldl_reduction_mmol_l=1.0)
    assert len(out["assumptions"]) >= 4
    assert any("proportional" in a for a in out["assumptions"])
    assert any("horizon" in a or "years" in a for a in out["assumptions"])
    assert "DERIVED" in out["notes"]
    assert out["risk"] is None, "this is a benefit, not a risk"


def test_invalid_inputs():
    with pytest.raises(ValueError, match="baseline_risk"):
        cvd_statin_benefit_predict(baseline_risk=1.5, ldl_reduction_mmol_l=1.0)
    with pytest.raises(ValueError, match="outcome"):
        cvd_statin_benefit_predict(baseline_risk=0.2, ldl_reduction_mmol_l=1.0,
                                   outcome="bogus")
    with pytest.raises(ValueError, match=">= 0"):
        cvd_statin_benefit_predict(baseline_risk=0.2, ldl_reduction_mmol_l=-1.0)


def test_metadata():
    out = cvd_statin_benefit_predict(baseline_risk=0.2, ldl_reduction_mmol_l=1.0)
    assert out["model_id"] == "cvd_statin_benefit"
    assert out["axis"] == "response"
    assert out["disease"] == "cvd"
