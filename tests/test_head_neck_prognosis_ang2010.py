"""Tests for the Ang 2010 RTOG 0129 recursive-partitioning risk groups."""

import pytest

from mayo_baseline.head_neck.prognosis import ang2010_rpa_predict


def test_hpv_positive_light_smoker_any_n_stage_is_low_risk():
    out = ang2010_rpa_predict(hpv_positive=True, pack_years=5, n_stage="N3", t_stage="T2")
    assert out["risk_group"] == "low"


def test_hpv_positive_heavy_smoker_low_n_stage_is_low_risk():
    out = ang2010_rpa_predict(hpv_positive=True, pack_years=20, n_stage="N2a", t_stage="T3")
    assert out["risk_group"] == "low"


def test_hpv_positive_heavy_smoker_high_n_stage_is_intermediate():
    for n in ("N2b", "N2c", "N3"):
        out = ang2010_rpa_predict(hpv_positive=True, pack_years=20, n_stage=n, t_stage="T2")
        assert out["risk_group"] == "intermediate", n


def test_hpv_negative_light_smoker_t2_or_t3_is_intermediate():
    for t in ("T2", "T3"):
        out = ang2010_rpa_predict(hpv_positive=False, pack_years=0, n_stage="N0", t_stage=t)
        assert out["risk_group"] == "intermediate", t


def test_hpv_negative_heavy_smoker_is_high_regardless_of_t_stage():
    out = ang2010_rpa_predict(hpv_positive=False, pack_years=15, n_stage="N0", t_stage="T2")
    assert out["risk_group"] == "high"


def test_hpv_negative_light_smoker_t1_or_t4_is_high():
    """The exception is 'T2 or T3' only — T1 and T4 are not covered by it."""
    for t in ("T1", "T4"):
        out = ang2010_rpa_predict(hpv_positive=False, pack_years=0, n_stage="N0", t_stage=t)
        assert out["risk_group"] == "high", t


def test_pack_years_boundary_is_at_10():
    common = dict(hpv_positive=True, n_stage="N2b", t_stage="T2")
    assert ang2010_rpa_predict(pack_years=10, **common)["risk_group"] == "low"
    assert ang2010_rpa_predict(pack_years=10.01, **common)["risk_group"] == "intermediate"


def test_stage_normalization_accepts_clinical_prefix_and_case():
    a = ang2010_rpa_predict(hpv_positive=True, pack_years=20, n_stage="cN2b", t_stage="T2")
    b = ang2010_rpa_predict(hpv_positive=True, pack_years=20, n_stage="n2b", t_stage="t2")
    assert a["risk_group"] == b["risk_group"] == "intermediate"


def test_published_survival_and_hazard_ratios_attached():
    low = ang2010_rpa_predict(hpv_positive=True, pack_years=0, n_stage="N0", t_stage="T2")
    inter = ang2010_rpa_predict(hpv_positive=True, pack_years=20, n_stage="N2b", t_stage="T2")
    high = ang2010_rpa_predict(hpv_positive=False, pack_years=20, n_stage="N0", t_stage="T2")
    assert low["three_year_os"] == pytest.approx(0.930)
    assert inter["three_year_os"] == pytest.approx(0.708)
    assert high["three_year_os"] == pytest.approx(0.462)
    assert low["hazard_ratio_vs_low"] is None
    assert inter["hazard_ratio_vs_low"] == pytest.approx(3.54)
    assert high["hazard_ratio_vs_low"] == pytest.approx(7.16)
    assert low["three_year_os"] > inter["three_year_os"] > high["three_year_os"]


def test_invalid_inputs():
    with pytest.raises(ValueError, match="pack_years"):
        ang2010_rpa_predict(hpv_positive=True, pack_years=-1, n_stage="N0", t_stage="T2")
    with pytest.raises(ValueError, match="n_stage"):
        ang2010_rpa_predict(hpv_positive=True, pack_years=5, n_stage="bogus", t_stage="T2")
    with pytest.raises(ValueError, match="t_stage"):
        ang2010_rpa_predict(hpv_positive=True, pack_years=5, n_stage="N0", t_stage="bogus")


def test_metadata():
    out = ang2010_rpa_predict(hpv_positive=True, pack_years=5, n_stage="N0", t_stage="T2")
    assert out["model_id"] == "ang2010_rpa"
    assert out["axis"] == "prognosis"
    assert out["disease"] == "head_neck"
    assert out["risk"] is None


def test_the_two_operationalizations_differ_only_for_hpv_negative_t1():
    """Ang's text names "T2 or T3"; Fakhry's validation says "<T4", which adds
    T1. Everything else agrees, so the divergence is exactly one cell."""
    diffs = []
    for hpv in (True, False):
        for py in (0, 5, 20):
            for n in ("N0", "N2a", "N2b", "N3"):
                for t in ("T1", "T2", "T3", "T4"):
                    a = ang2010_rpa_predict(hpv_positive=hpv, pack_years=py,
                                            n_stage=n, t_stage=t,
                                            definition="ang2010")["risk_group"]
                    fk = ang2010_rpa_predict(hpv_positive=hpv, pack_years=py,
                                             n_stage=n, t_stage=t,
                                             definition="fakhry")["risk_group"]
                    if a != fk:
                        diffs.append((hpv, py, n, t, a, fk))
    assert diffs, "the two definitions should differ somewhere"
    assert all(hpv is False and py <= 10 and t == "T1" for hpv, py, _, t, _, _ in diffs)
    assert all((a, fk) == ("high", "intermediate") for *_, a, fk in diffs)


def test_default_definition_is_the_literal_primary_reading():
    out = ang2010_rpa_predict(hpv_positive=False, pack_years=0,
                              n_stage="N0", t_stage="T1")
    assert out["definition"] == "ang2010"
    assert out["risk_group"] == "high"


def test_invalid_definition():
    with pytest.raises(ValueError, match="definition"):
        ang2010_rpa_predict(hpv_positive=True, pack_years=5, n_stage="N0",
                            t_stage="T2", definition="bogus")
