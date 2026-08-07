"""Tests for the MSK rectal calculator (Weiser et al., JAMA Netw Open 2021)."""

import math

import pytest

from mayo_baseline.colorectal.prognosis import msk_rectal as M
from mayo_baseline.colorectal.prognosis import msk_rectal_predict
from mayo_baseline.colorectal.prognosis.msk_rectal import linear_predictor

# Reference patient: ypT0, node-negative, low tumour, no VI/PNI.
REF = dict(
    ypt="ypT0",
    positive_nodes=0,
    distance_to_anal_verge_cm=2.0,
    venous_invasion=False,
    perineural_invasion=False,
)


def test_rfs_reference_patient_matches_hand_computed_intercept():
    """ypT0, 0 nodes, DTAV<5, no VI/PNI → every term drops out but the intercept."""
    lp = linear_predictor(endpoint="rfs", **REF)
    assert lp == pytest.approx(-0.5425329)


def test_os_reference_patient_intercept_plus_age_only():
    lp = linear_predictor(endpoint="os", age=36.0, **REF)
    # At age 36 every age spline term is (a-knot)_+ = 0 except the linear one.
    assert lp == pytest.approx(-0.9603734 + 0.00535203 * 36.0)


def test_ypt_reference_groups_differ_between_endpoints():
    """RFS references ypT0/T1; OS references ypT0/T1/T2. ypT2 is the tell."""
    rfs_t0 = linear_predictor(endpoint="rfs", **{**REF, "ypt": "ypT0"})
    rfs_t1 = linear_predictor(endpoint="rfs", **{**REF, "ypt": "ypT1"})
    rfs_t2 = linear_predictor(endpoint="rfs", **{**REF, "ypt": "ypT2"})
    assert rfs_t0 == rfs_t1                      # both in the reference group
    assert rfs_t2 - rfs_t0 == pytest.approx(0.3143759)

    os_t0 = linear_predictor(endpoint="os", age=60, **{**REF, "ypt": "ypT0"})
    os_t2 = linear_predictor(endpoint="os", age=60, **{**REF, "ypt": "ypT2"})
    os_t3 = linear_predictor(endpoint="os", age=60, **{**REF, "ypt": "ypT3"})
    assert os_t2 == os_t0                        # ypT2 IS the reference for OS
    assert os_t3 - os_t0 == pytest.approx(0.2726462)


def test_ypt4_is_the_largest_t_effect_for_both_endpoints():
    for endpoint, kwargs in (("rfs", {}), ("os", {"age": 60})):
        lps = [
            linear_predictor(endpoint=endpoint, **{**REF, "ypt": f"ypT{i}"}, **kwargs)
            for i in range(5)
        ]
        assert lps[4] == max(lps)


def test_positive_node_spline_terms():
    """posLN enters linearly plus three (x)_+^3 terms with knots 0/1/3."""
    lp0 = linear_predictor(endpoint="rfs", **REF)
    lp1 = linear_predictor(endpoint="rfs", **{**REF, "positive_nodes": 1})
    expected = lp0 + 0.522283 * 1 - 0.05440106 * 1**3
    assert lp1 == pytest.approx(expected)

    lp4 = linear_predictor(endpoint="rfs", **{**REF, "positive_nodes": 4})
    expected4 = (
        -0.5425329
        + 0.522283 * 4
        - 0.05440106 * 4**3
        + 0.08160159 * 3**3
        - 0.02720053 * 1**3
    )
    assert lp4 == pytest.approx(expected4)


def test_more_positive_nodes_raise_risk_over_the_clinical_range():
    risks = [
        msk_rectal_predict(endpoint="rfs", months=60, **{**REF, "positive_nodes": n})["risk"]
        for n in range(0, 5)
    ]
    assert risks == sorted(risks)


def test_high_tumour_and_invasion_raise_risk():
    base = msk_rectal_predict(endpoint="rfs", months=60, **REF)["risk"]
    for field in ("venous_invasion", "perineural_invasion"):
        worse = msk_rectal_predict(endpoint="rfs", months=60, **{**REF, field: True})["risk"]
        assert worse > base, field
    t4 = msk_rectal_predict(endpoint="rfs", months=60, **{**REF, "ypt": "ypT4"})["risk"]
    assert t4 > base


def test_distal_tumours_are_higher_risk_than_proximal():
    """DTAV >= 5 cm carries a negative coefficient, i.e. protective."""
    distal = msk_rectal_predict(
        endpoint="rfs", months=60, **{**REF, "distance_to_anal_verge_cm": 2.0}
    )["risk"]
    proximal = msk_rectal_predict(
        endpoint="rfs", months=60, **{**REF, "distance_to_anal_verge_cm": 8.0}
    )["risk"]
    assert proximal < distal


def test_survival_form_and_monotonicity_in_time():
    out60 = msk_rectal_predict(endpoint="rfs", months=60, **REF)
    lp = out60["linear_predictor"]
    assert out60["survival"] == pytest.approx(
        M.BASELINE_SURVIVAL["rfs"][60] ** math.exp(lp)
    )
    survivals = [
        msk_rectal_predict(endpoint="rfs", months=m, **REF)["survival"]
        for m in (0, 60, 120, 180)
    ]
    assert survivals == sorted(survivals, reverse=True)
    assert survivals[0] == pytest.approx(1.0)


def test_os_exceeds_rfs_at_the_same_time_point():
    """Published S0 is higher for OS than RFS at every follow-up time."""
    for m in (60, 120, 180):
        assert M.BASELINE_SURVIVAL["os"][m] > M.BASELINE_SURVIVAL["rfs"][m]


def test_unsupported_time_points_are_refused_not_interpolated():
    with pytest.raises(ValueError, match="published S0 grid"):
        msk_rectal_predict(endpoint="rfs", months=90, **REF)


def test_os_requires_age():
    with pytest.raises(ValueError, match="age is required"):
        msk_rectal_predict(endpoint="os", months=60, **REF)


def test_invalid_inputs():
    with pytest.raises(ValueError, match="endpoint"):
        msk_rectal_predict(endpoint="dfs", months=60, **REF)
    with pytest.raises(ValueError, match="ypt"):
        msk_rectal_predict(endpoint="rfs", months=60, **{**REF, "ypt": "ypT9"})
    with pytest.raises(ValueError, match="positive_nodes"):
        msk_rectal_predict(endpoint="rfs", months=60, **{**REF, "positive_nodes": -1})


def test_ypt_normalization_accepts_common_spellings():
    a = linear_predictor(endpoint="rfs", **{**REF, "ypt": "ypT3"})
    b = linear_predictor(endpoint="rfs", **{**REF, "ypt": "T3"})
    c = linear_predictor(endpoint="rfs", **{**REF, "ypt": "t3"})
    assert a == b == c


def test_metadata():
    out = msk_rectal_predict(endpoint="rfs", months=60, **REF)
    assert out["model_id"] == "msk_rectal"
    assert out["axis"] == "prognosis"
    assert out["disease"] == "colorectal"
    assert 0.0 < out["survival"] < 1.0
