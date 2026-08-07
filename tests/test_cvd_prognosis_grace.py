"""Tests for the GRACE in-hospital mortality score (Granger et al., 2003)."""

import pytest

from mayo_baseline.cvd.prognosis import grace_predict
from mayo_baseline.cvd.prognosis.grace import (
    age_points,
    creatinine_points,
    heart_rate_points,
    risk_from_points,
    sbp_points,
)


def test_worked_example_1_component_by_component():
    """Figure 4, first example. Killip II, SBP 100, HR 100, age 65, creat 1.0,
    no arrest, ST deviation, elevated enzymes.

    The paper lists components 20 + 53 + 15 + 58 + 7 + 0 + 28 + 14 and states
    the total is 196. Those components actually sum to 195 — the published
    total carries an arithmetic slip. We assert against the COMPONENTS, which
    are the model, not against the misprinted total.
    """
    out = grace_predict(
        killip_class=2,
        sbp=100,
        heart_rate=100,
        age=65,
        creatinine_mg_dl=1.0,
        cardiac_arrest_at_admission=False,
        st_segment_deviation=True,
        elevated_cardiac_enzymes=True,
    )
    assert out["components"] == {
        "killip": 20,
        "sbp": 53,
        "heart_rate": 15,
        "age": 58,
        "creatinine": 7,
        "cardiac_arrest": 0,
        "st_deviation": 28,
        "elevated_enzymes": 14,
    }
    assert out["score"] == 195
    assert sum(out["components"].values()) == out["score"]
    # Paper: "about a 16% risk".
    assert out["risk"] == pytest.approx(0.155, abs=0.01)


def test_worked_example_2_matches_exactly():
    """Figure 4, second example: Killip I, SBP 80, HR 60, age 55, creat 0.4,
    no other risk factors -> 0 + 58 + 3 + 41 + 1 = 103, ~0.9% risk."""
    out = grace_predict(
        killip_class=1, sbp=80, heart_rate=60, age=55, creatinine_mg_dl=0.4
    )
    assert out["score"] == 103
    assert out["risk"] == pytest.approx(0.009, abs=0.001)


def test_band_boundaries_follow_the_worked_examples_not_the_printed_labels():
    """The printed bands read '80-99' then '100-119', but the paper's own
    examples put SBP 100 in the lower band. Boundary values go DOWN."""
    assert sbp_points(80) == 58     # "<=80"
    assert sbp_points(100) == 53    # printed "80-99" — the disambiguating case
    assert sbp_points(101) == 43
    assert sbp_points(120) == 43
    assert sbp_points(121) == 34

    assert creatinine_points(0.40) == 1   # printed "0-0.39"
    assert creatinine_points(0.41) == 4
    assert creatinine_points(1.0) == 7

    assert age_points(60) == 41
    assert age_points(61) == 58
    assert heart_rate_points(70) == 3
    assert heart_rate_points(71) == 9


def test_end_bands_honour_their_printed_signs():
    assert sbp_points(200) == 0          # ">=200"
    assert sbp_points(250) == 0
    assert heart_rate_points(200) == 46  # ">=200"
    assert age_points(90) == 100         # ">=90"
    assert creatinine_points(4.0) == 21
    assert creatinine_points(4.1) == 28  # ">4.0"


def test_sbp_scale_runs_backward():
    """Low blood pressure scores highest — it encodes shock, not hypertension."""
    assert sbp_points(70) > sbp_points(130) > sbp_points(210)


def test_risk_increases_monotonically_with_points():
    risks = [risk_from_points(p) for p in range(60, 260, 10)]
    assert risks == sorted(risks)
    assert risk_from_points(50) == pytest.approx(0.002)   # clamped low
    assert risk_from_points(300) == pytest.approx(0.52)   # clamped high


def test_killip_class_and_binary_factors():
    base = dict(sbp=140, heart_rate=80, age=60, creatinine_mg_dl=1.0)
    scores = [grace_predict(killip_class=k, **base)["score"] for k in (1, 2, 3, 4)]
    assert scores == sorted(scores)
    with_arrest = grace_predict(
        killip_class=1, cardiac_arrest_at_admission=True, **base
    )["score"]
    assert with_arrest - scores[0] == 39


def test_invalid_inputs():
    base = dict(sbp=120, heart_rate=80, age=60, creatinine_mg_dl=1.0)
    with pytest.raises(ValueError, match="killip_class"):
        grace_predict(killip_class=5, **base)
    with pytest.raises(ValueError, match="sbp"):
        grace_predict(killip_class=1, **{**base, "sbp": 0})
    with pytest.raises(ValueError, match="creatinine"):
        grace_predict(killip_class=1, **{**base, "creatinine_mg_dl": -1})


def test_metadata():
    out = grace_predict(
        killip_class=1, sbp=120, heart_rate=80, age=60, creatinine_mg_dl=1.0
    )
    assert out["model_id"] == "grace"
    assert out["axis"] == "prognosis"
    assert out["disease"] == "cvd"
    assert 0.0 < out["risk"] < 1.0
