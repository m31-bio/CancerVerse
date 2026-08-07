"""Tests for SCORE2 detection model."""

import pytest

from mayo_baseline.cvd.detection import score2_predict
from mayo_baseline.cvd.detection.score2 import (
    linear_predictor,
    recalibrate,
    uncalibrated_risk,
)


def test_score2_paper_example_ordering():
    # Male smoker age 50, SBP 140, TC 6, HDL ~1.0–1.3: low region < very_high region
    common = dict(
        sex="male",
        age=50,
        sbp=140,
        total_chol_mmol=6.0,
        hdl_mmol=1.0,
        smoker=True,
    )
    low = score2_predict(**common, region="low")["risk"]
    very = score2_predict(**common, region="very_high")["risk"]
    assert 0.0 < low < very < 1.0


def test_score2_rejects_diabetes():
    with pytest.raises(ValueError, match="diabetes"):
        score2_predict(
            sex="female",
            age=55,
            sbp=130,
            total_chol_mmol=5.5,
            hdl_mmol=1.4,
            smoker=False,
            diabetes=True,
        )


def test_score2_hand_lp_male():
    # age 60 → cage=0; non-smoker; sbp 120; tc 6; hdl 1.3 → all centered zeros → lp=0
    lp = linear_predictor(
        sex="male",
        age=60,
        sbp=120,
        total_chol_mmol=6.0,
        hdl_mmol=1.3,
        smoker=False,
    )
    assert lp == pytest.approx(0.0)
    uncal = uncalibrated_risk(sex="male", lp=lp)
    assert uncal == pytest.approx(1.0 - 0.9605)
    cal = recalibrate(uncal, sex="male", region="moderate")
    assert 0.0 < cal < 1.0


def test_score2_metadata():
    out = score2_predict(
        sex="female",
        age=55,
        sbp=130,
        total_chol_mmol=5.5,
        hdl_mmol=1.4,
        smoker=False,
        region="low",
    )
    assert out["model_id"] == "score2"
    assert out["axis"] == "detection"
    assert out["region"] == "low"
