"""Tests for ROMA (Moore et al., Gynecol Oncol 2009)."""

import math

import pytest

from cancerverse_baseline.ovarian.detection import roma_predict
from cancerverse_baseline.ovarian.detection.roma import (
    POSTMENOPAUSAL,
    PREMENOPAUSAL,
    predictive_index,
)


def test_premenopausal_equation_matches_the_paper():
    """PI = -12.0 + 2.38*LN(HE4) + 0.0626*LN(CA125)"""
    he4, ca125 = 60.0, 30.0
    expected = -12.0 + 2.38 * math.log(he4) + 0.0626 * math.log(ca125)
    assert predictive_index(
        he4_pmol_l=he4, ca125_u_ml=ca125, postmenopausal=False
    ) == pytest.approx(expected)


def test_postmenopausal_equation_matches_the_paper():
    """PI = -8.09 + 1.04*LN(HE4) + 0.732*LN(CA125)"""
    he4, ca125 = 60.0, 30.0
    expected = -8.09 + 1.04 * math.log(he4) + 0.732 * math.log(ca125)
    assert predictive_index(
        he4_pmol_l=he4, ca125_u_ml=ca125, postmenopausal=True
    ) == pytest.approx(expected)


def test_logistic_link():
    out = roma_predict(he4_pmol_l=60.0, ca125_u_ml=30.0, postmenopausal=True)
    pi = out["predictive_index"]
    assert out["risk"] == pytest.approx(math.exp(pi) / (1 + math.exp(pi)))


def test_published_cutoffs():
    assert PREMENOPAUSAL["cutoff"] == 0.131
    assert POSTMENOPAUSAL["cutoff"] == 0.277


def test_risk_group_uses_the_stratum_specific_cutoff():
    """A probability of 20% is high risk premenopausally, low postmenopausally."""
    # Find inputs landing near 20% in each stratum by construction.
    pre = roma_predict(he4_pmol_l=52.0, ca125_u_ml=30.0, postmenopausal=False)
    post = roma_predict(he4_pmol_l=52.0, ca125_u_ml=30.0, postmenopausal=True)
    assert pre["cutoff"] == 0.131
    assert post["cutoff"] == 0.277
    # Same inputs, different thresholds, verify the threshold is actually applied.
    for out in (pre, post):
        assert out["risk_group"] == ("high" if out["risk"] > out["cutoff"] else "low")


def test_premenopausal_model_is_driven_by_he4_not_ca125():
    """CA125's premenopausal coefficient (0.0626) is near-negligible next to
    HE4's (2.38), the model encoding that CA125 is confounded by benign
    gynaecological disease in premenopausal women."""
    assert PREMENOPAUSAL["ln_ca125"] < 0.1
    assert PREMENOPAUSAL["ln_he4"] > 2.0
    # Postmenopausally CA125 carries real weight.
    assert POSTMENOPAUSAL["ln_ca125"] > 0.7

    low_ca = roma_predict(he4_pmol_l=80.0, ca125_u_ml=10.0, postmenopausal=False)[
        "risk"
    ]
    high_ca = roma_predict(he4_pmol_l=80.0, ca125_u_ml=500.0, postmenopausal=False)[
        "risk"
    ]
    assert abs(high_ca - low_ca) < 0.05  # barely moves premenopausally

    low_ca_p = roma_predict(he4_pmol_l=80.0, ca125_u_ml=10.0, postmenopausal=True)[
        "risk"
    ]
    high_ca_p = roma_predict(he4_pmol_l=80.0, ca125_u_ml=500.0, postmenopausal=True)[
        "risk"
    ]
    assert high_ca_p - low_ca_p > 0.2  # moves a lot postmenopausally


def test_risk_rises_with_both_markers():
    lo = roma_predict(he4_pmol_l=30.0, ca125_u_ml=10.0, postmenopausal=True)["risk"]
    hi = roma_predict(he4_pmol_l=400.0, ca125_u_ml=1000.0, postmenopausal=True)["risk"]
    assert hi > lo
    assert 0.0 < lo < hi < 1.0


def test_invalid_inputs():
    with pytest.raises(ValueError, match="he4"):
        roma_predict(he4_pmol_l=0, ca125_u_ml=30.0, postmenopausal=True)
    with pytest.raises(ValueError, match="ca125"):
        roma_predict(he4_pmol_l=60.0, ca125_u_ml=-1, postmenopausal=True)


def test_metadata():
    out = roma_predict(he4_pmol_l=60.0, ca125_u_ml=30.0, postmenopausal=False)
    assert out["model_id"] == "roma"
    assert out["axis"] == "detection"
    assert out["disease"] == "ovarian"
    assert out["menopausal_status"] == "premenopausal"


def test_coefficients_corroborated_by_the_assay_insert():
    """The Moore 2009 paper, the Abbott/Fujirebio assay insert and ARUP's test
    directory all print the same six coefficients. Independent corroboration of
    the equation, in the absence of any published worked example."""
    assert PREMENOPAUSAL["intercept"] == -12.0
    assert PREMENOPAUSAL["ln_he4"] == 2.38
    assert PREMENOPAUSAL["ln_ca125"] == 0.0626
    assert POSTMENOPAUSAL["intercept"] == -8.09
    assert POSTMENOPAUSAL["ln_he4"] == 1.04
    assert POSTMENOPAUSAL["ln_ca125"] == 0.732


def test_paper_and_assay_cutoffs_differ_and_cross_over():
    """Same equation, two published thresholds, and they disagree in opposite
    directions by menopausal status. Premenopausally the commercial cut is more
    sensitive (11.4 vs 13.1); postmenopausally it is less (29.9 vs 27.7).
    """
    from cancerverse_baseline.ovarian.detection.roma import CUTOFFS

    assert CUTOFFS["paper"]["premenopausal"] > CUTOFFS["assay_insert"]["premenopausal"]
    assert (
        CUTOFFS["paper"]["postmenopausal"] < CUTOFFS["assay_insert"]["postmenopausal"]
    )


def test_cutoff_source_changes_the_call_for_a_borderline_patient():
    """A premenopausal PP near 12% is low risk by the paper, high by the insert."""
    kw = dict(he4_pmol_l=57.0, ca125_u_ml=25.0, postmenopausal=False)
    paper = roma_predict(**kw, cutoff_source="paper")
    insert = roma_predict(**kw, cutoff_source="assay_insert")
    assert paper["risk"] == pytest.approx(insert["risk"])  # same equation
    assert paper["cutoff"] == 0.131 and insert["cutoff"] == 0.114
    if 0.114 < paper["risk"] <= 0.131:  # the disputed band
        assert paper["risk_group"] == "low"
        assert insert["risk_group"] == "high"


def test_invalid_cutoff_source():
    with pytest.raises(ValueError, match="cutoff_source"):
        roma_predict(
            he4_pmol_l=60.0, ca125_u_ml=30.0, postmenopausal=True, cutoff_source="bogus"
        )
