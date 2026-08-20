"""Tests for the Risk of Malignancy Index (Jacobs 1990 + variants)."""

import pytest

from cancerverse_baseline.ovarian.detection import rmi_predict


def test_rmi1_worked_example():
    # U=3 (score>=2), M=3 (postmenopausal), CA-125=35 -> 3*3*35 = 315
    out = rmi_predict(ultrasound_score=3, postmenopausal=True, ca125=35.0, variant="rmi1")
    assert out["index"] == pytest.approx(315.0)
    assert out["above_cutoff"] is True  # 315 >= 200


def test_rmi1_zero_ultrasound_score_forces_index_to_zero():
    # Published structural quirk: U=0 zeroes the index regardless of CA-125.
    out = rmi_predict(ultrasound_score=0, postmenopausal=True, ca125=1000.0, variant="rmi1")
    assert out["index"] == pytest.approx(0.0)
    assert out["above_cutoff"] is False


def test_rmi3_removes_the_zero():
    # Same inputs as above, RMI 3: U=1 (score 0-1), M=3 -> 1*3*1000 = 3000
    out = rmi_predict(ultrasound_score=0, postmenopausal=True, ca125=1000.0, variant="rmi3")
    assert out["index"] == pytest.approx(3000.0)
    assert out["above_cutoff"] is True


def test_rmi4_worked_example_with_size_score():
    # U=4 (score>=2), M=4, S=2 (>=7cm), CA-125=100 -> 4*4*2*100 = 3200
    out = rmi_predict(
        ultrasound_score=2, postmenopausal=True, ca125=100.0,
        variant="rmi4", max_diameter_cm=8.0,
    )
    assert out["index"] == pytest.approx(3200.0)
    assert out["above_cutoff"] is True  # cutoff 450


def test_rmi4_requires_max_diameter():
    with pytest.raises(ValueError, match="max_diameter_cm"):
        rmi_predict(ultrasound_score=2, postmenopausal=True, ca125=100.0, variant="rmi4")


def test_diameter_ignored_outside_rmi4():
    out = rmi_predict(
        ultrasound_score=2, postmenopausal=True, ca125=100.0,
        variant="rmi1", max_diameter_cm=8.0,
    )
    assert "ignored" in out["notes"]


def test_premenopausal_scores_lower_than_postmenopausal():
    pre = rmi_predict(ultrasound_score=3, postmenopausal=False, ca125=50.0, variant="rmi1")
    post = rmi_predict(ultrasound_score=3, postmenopausal=True, ca125=50.0, variant="rmi1")
    assert pre["index"] < post["index"]


def test_output_is_index_not_probability():
    out = rmi_predict(ultrasound_score=3, postmenopausal=True, ca125=50.0)
    assert out["risk"] is None


def test_unknown_variant_rejected():
    with pytest.raises(ValueError, match="variant"):
        rmi_predict(ultrasound_score=3, postmenopausal=True, ca125=50.0, variant="rmi5")


def test_metadata():
    out = rmi_predict(ultrasound_score=3, postmenopausal=True, ca125=50.0)
    assert out["model_id"] == "rmi"
    assert out["axis"] == "detection"
    assert out["disease"] == "ovarian"
