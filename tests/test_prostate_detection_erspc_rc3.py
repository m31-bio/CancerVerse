"""Tests for prostate detection (ERSPC RC3)."""

import math

import pytest

from mayo_baseline.base import logit_risk
from mayo_baseline.prostate.detection import (
    erspc_rc3_predict,
    linear_predictor_rc3,
    volume_class,
)


def test_volume_class_bins():
    assert volume_class(29.9) == 25.0
    assert volume_class(30.0) == 40.0
    assert volume_class(49.9) == 40.0
    assert volume_class(50.0) == 60.0


def test_rc3_monotonic_in_psa():
    low = erspc_rc3_predict(psa=2.0, volume_ml=40.0, dre_positive=False)["risk"]
    high = erspc_rc3_predict(psa=20.0, volume_ml=40.0, dre_positive=False)["risk"]
    assert 0.0 < low < high < 1.0


def test_rc3_dre_increases_risk():
    neg = erspc_rc3_predict(psa=5.0, volume_ml=40.0, dre_positive=False)["risk"]
    pos = erspc_rc3_predict(psa=5.0, volume_ml=40.0, dre_positive=True)["risk"]
    assert pos > neg


def test_rc3_hand_calculation():
    psa, vc = 4.0, 40.0
    lp = -1.826 + 1.024 * (math.log(psa, 2) - 2.0) - 1.50 * (math.log(vc, 2) - 5.4)
    out = erspc_rc3_predict(psa=psa, volume_ml=35.0, dre_positive=False)
    assert linear_predictor_rc3(psa=psa, volume_ml=35.0, dre_positive=False) == pytest.approx(lp)
    assert out["risk"] == pytest.approx(logit_risk(lp))
    assert out["axis"] == "detection"
    assert out["model_id"] == "erspc_rc3"
