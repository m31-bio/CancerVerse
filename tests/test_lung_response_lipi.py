"""Tests for LIPI (Lung Immune Prognostic Index)."""

import pytest

from mayo_baseline.lung.response import derived_nlr, lipi_predict


def test_derived_nlr_uses_non_neutrophil_white_count():
    # neutrophils 6, leukocytes 8 -> 6 / (8 - 6) = 3.0
    assert derived_nlr(neutrophils=6.0, leukocytes=8.0) == pytest.approx(3.0)


def test_three_groups_at_the_published_thresholds():
    good = lipi_predict(dnlr=2.0, ldh=200, ldh_upper_limit_normal=250)
    inter = lipi_predict(dnlr=4.0, ldh=200, ldh_upper_limit_normal=250)
    poor = lipi_predict(dnlr=4.0, ldh=300, ldh_upper_limit_normal=250)
    assert (good["score"], good["group"]) == (0, "good")
    assert (inter["score"], inter["group"]) == (1, "intermediate")
    assert (poor["score"], poor["group"]) == (2, "poor")


def test_thresholds_are_strict_inequalities():
    # dNLR > 3 and LDH > ULN — exactly at the cutoff scores 0.
    at_cutoff = lipi_predict(dnlr=3.0, ldh=250, ldh_upper_limit_normal=250)
    assert at_cutoff["score"] == 0
    just_over = lipi_predict(dnlr=3.01, ldh=250.01, ldh_upper_limit_normal=250)
    assert just_over["score"] == 2


def test_ldh_is_compared_against_the_reporting_lab_uln():
    """Same LDH value, different lab ULN → different point."""
    a = lipi_predict(dnlr=1.0, ldh=240, ldh_upper_limit_normal=250)
    b = lipi_predict(dnlr=1.0, ldh=240, ldh_upper_limit_normal=220)
    assert a["components"]["ldh"] == 0
    assert b["components"]["ldh"] == 1


def test_counts_and_dnlr_agree():
    from_counts = lipi_predict(
        neutrophils=6.0, leukocytes=8.0, ldh=200, ldh_upper_limit_normal=250
    )
    from_dnlr = lipi_predict(dnlr=3.0, ldh=200, ldh_upper_limit_normal=250)
    assert from_counts["dnlr"] == pytest.approx(from_dnlr["dnlr"])


def test_invalid_inputs():
    with pytest.raises(ValueError, match="dnlr"):
        lipi_predict(neutrophils=6.0, ldh=200, ldh_upper_limit_normal=250)
    with pytest.raises(ValueError, match="not both"):
        lipi_predict(dnlr=2.0, neutrophils=6.0, ldh=200, ldh_upper_limit_normal=250)
    with pytest.raises(ValueError, match="must exceed"):
        derived_nlr(neutrophils=8.0, leukocytes=8.0)
    with pytest.raises(ValueError, match="ldh"):
        lipi_predict(dnlr=2.0, ldh=0, ldh_upper_limit_normal=250)


def test_metadata():
    out = lipi_predict(dnlr=2.0, ldh=200, ldh_upper_limit_normal=250)
    assert out["model_id"] == "lipi"
    assert out["axis"] == "response"
    assert out["disease"] == "lung"
    assert out["risk"] is None
