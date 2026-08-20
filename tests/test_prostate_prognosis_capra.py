"""Tests for the UCSF-CAPRA score (Cooperberg et al., J Urol 2005, Table 1)."""

import pytest

from cancerverse_baseline.prostate.prognosis import capra_predict, capra_score, risk_group
from cancerverse_baseline.prostate.prognosis.capra import (
    gleason_points,
    psa_points,
    t_stage_points,
)

BASE = dict(
    psa=5.0,
    gleason_primary=3,
    gleason_secondary=3,
    t_stage="T1c",
    percent_positive_cores=20.0,
    age=45,
)


def test_psa_point_bands_match_table_1():
    assert psa_points(2.1) == 0
    assert psa_points(6.0) == 0
    assert psa_points(6.1) == 1
    assert psa_points(10.0) == 1
    assert psa_points(10.1) == 2
    assert psa_points(20.0) == 2
    assert psa_points(20.1) == 3
    assert psa_points(30.0) == 3
    assert psa_points(30.1) == 4


def test_gleason_has_no_two_point_level():
    """Table 1 jumps 0 -> 1 -> 3; any primary pattern 4-5 scores 3."""
    assert gleason_points(3, 3) == 0
    assert gleason_points(3, 4) == 1
    assert gleason_points(3, 5) == 1
    assert gleason_points(4, 3) == 3
    assert gleason_points(5, 5) == 3
    assert 2 not in {gleason_points(p, s) for p in range(1, 6) for s in range(1, 6)}


def test_t_stage_points_and_localized_scope():
    for stage in ("T1", "T1c", "T2", "T2b", "cT2a"):
        assert t_stage_points(stage) == 0
    assert t_stage_points("T3a") == 1
    # CAPRA is preoperative and localized — T3b/T4 are out of scope.
    for stage in ("T3b", "T4"):
        with pytest.raises(ValueError, match="localized"):
            t_stage_points(stage)


def test_minimum_and_maximum_reachable_scores():
    lowest = capra_score(**BASE)
    assert lowest == 0
    highest = capra_score(
        psa=50.0,
        gleason_primary=5,
        gleason_secondary=5,
        t_stage="T3a",
        percent_positive_cores=80.0,
        age=65,
    )
    assert highest == 10


def test_risk_group_boundaries():
    assert risk_group(0) == "low"
    assert risk_group(2) == "low"
    assert risk_group(3) == "intermediate"
    assert risk_group(5) == "intermediate"
    assert risk_group(6) == "high"
    assert risk_group(10) == "high"


def test_age_and_core_cutoffs_are_inclusive():
    assert capra_predict(**{**BASE, "age": 49})["components"]["age"] == 0
    assert capra_predict(**{**BASE, "age": 50})["components"]["age"] == 1
    at_33 = capra_predict(**{**BASE, "percent_positive_cores": 33.9})
    at_34 = capra_predict(**{**BASE, "percent_positive_cores": 34.0})
    assert at_33["components"]["percent_positive_cores"] == 0
    assert at_34["components"]["percent_positive_cores"] == 1


def test_components_sum_to_the_total():
    out = capra_predict(
        psa=12.0,
        gleason_primary=4,
        gleason_secondary=3,
        t_stage="T3a",
        percent_positive_cores=50.0,
        age=62,
    )
    assert sum(out["components"].values()) == out["score"]
    assert out["score"] == 2 + 3 + 1 + 1 + 1  # PSA 10.1-20, G4+, T3a, >=34%, >=50
    assert out["risk_group"] == "high"


def test_invalid_inputs():
    with pytest.raises(ValueError, match="psa"):
        capra_predict(**{**BASE, "psa": 0})
    with pytest.raises(ValueError, match="Gleason"):
        capra_predict(**{**BASE, "gleason_primary": 6})
    with pytest.raises(ValueError, match="percent_positive_cores"):
        capra_predict(**{**BASE, "percent_positive_cores": 150.0})


def test_metadata():
    out = capra_predict(**BASE)
    assert out["model_id"] == "capra"
    assert out["axis"] == "prognosis"
    assert out["disease"] == "prostate"
    assert out["risk"] is None
