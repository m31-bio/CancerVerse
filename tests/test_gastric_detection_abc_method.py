"""Tests for the ABC method (Watabe et al., Gut 2005)."""

import pytest

from mayo_baseline.gastric.detection import abc_group, abc_method_predict


@pytest.mark.parametrize(
    "hp,pg1,ratio,expected_group,expected_rate",
    [
        (False, 54.3, 5.4, "A", 0.0004),   # Hp-, PG- (not atrophic)
        (True, 73.7, 3.6, "B", 0.0006),    # Hp+, PG- (PG I above 70 cutoff)
        (True, 41.9, 2.1, "C", 0.0035),    # Hp+, PG+ (atrophic)
        (False, 35.7, 2.0, "D", 0.0060),   # Hp-, PG+ (atrophic, seroreverted)
    ],
)
def test_group_and_rate_match_watabe_table_2(hp, pg1, ratio, expected_group, expected_rate):
    out = abc_method_predict(
        h_pylori_antibody_positive=hp, pepsinogen_i=pg1, pepsinogen_i_ii_ratio=ratio,
    )
    assert out["group"] == expected_group
    assert out["risk"] == pytest.approx(expected_rate, abs=1e-12)


def test_atrophic_requires_both_criteria():
    # PG I at the cutoff but ratio above 3.0: NOT atrophic (both must hold).
    assert abc_group(
        h_pylori_antibody_positive=False, pepsinogen_i=70.0,
        pepsinogen_i_ii_ratio=3.1,
    ) == "A"
    # Both criteria satisfied (boundary inclusive): atrophic.
    assert abc_group(
        h_pylori_antibody_positive=False, pepsinogen_i=70.0,
        pepsinogen_i_ii_ratio=3.0,
    ) == "D"


def test_group_d_is_highest_risk_despite_seronegative():
    a = abc_method_predict(h_pylori_antibody_positive=False, pepsinogen_i=100, pepsinogen_i_ii_ratio=5.0)
    d = abc_method_predict(h_pylori_antibody_positive=False, pepsinogen_i=50, pepsinogen_i_ii_ratio=2.0)
    assert d["risk"] > a["risk"]


def test_prior_eradication_flags_invalidity():
    out = abc_method_predict(
        h_pylori_antibody_positive=False, pepsinogen_i=54.3,
        pepsinogen_i_ii_ratio=5.4, prior_eradication=True,
    )
    assert "eradication" in out["notes"]


def test_metadata():
    out = abc_method_predict(h_pylori_antibody_positive=False, pepsinogen_i=54.3, pepsinogen_i_ii_ratio=5.4)
    assert out["model_id"] == "abc_method"
    assert out["axis"] == "detection"
    assert out["disease"] == "gastric"
    assert out["horizon_years"] == 1
