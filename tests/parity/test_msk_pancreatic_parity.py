"""Parity: MSK pancreatic nomogram vs. the vendor's own deployed R.

Brennan MF, Kattan MW, Klimstra D, Conlon K. Ann Surg. 2004;240(2).

Route 1. `msk_pancreatic_reference.R` copies the model expression **verbatim**
from riskcalc.org's server.R and runs it under R 4.6.1.

    8 patients x 3 horizons = 24 probabilities
    worst absolute difference 5.0e-11 percentage points

**This cell was recorded as having no published equation until 2026-08-06.**
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mayo_baseline.pancreatic.prognosis import msk_pancreatic_predict
from mayo_baseline.pancreatic.prognosis.msk_pancreatic import (
    DIFFERENTIATION_BETA,
    LOCATION_BETA,
    T_STAGE_BETA,
)

CASES_FILE = Path(__file__).parent / "reference" / "msk_pancreatic_cases.json"


def _cases():
    return json.loads(CASES_FILE.read_text())["cases"]


def _kwargs(c):
    return dict(age=c["age"], male=c["male"],
                portal_vein_resected=c["portal_vein"],
                splenectomy=c["splenectomy"],
                resection_margin_positive=c["margin_positive"],
                location=c["location"].lower(),
                differentiation=c["differentiation"].lower(),
                posterior_margin_positive=c["posterior_margin_positive"],
                positive_nodes=c["positive_nodes"],
                negative_nodes=c["negative_nodes"], back_pain=c["back_pain"],
                t_stage=c["t_stage"], weight_loss=c["weight_loss"],
                size_cm=c["size_cm"])


@pytest.mark.parametrize("months,key", [(12, "surv_12mo_pct"),
                                        (24, "surv_24mo_pct"),
                                        (36, "surv_36mo_pct")])
@pytest.mark.parametrize("case", _cases(), ids=lambda c: f"{c['age']}-T{c['t_stage']}")
def test_matches_the_vendor_r(case, months, key):
    ours = msk_pancreatic_predict(**_kwargs(case), months=months)["survival"] * 100
    assert ours == pytest.approx(case[key], abs=1e-8)


def test_t_stage_is_not_monotone_as_published():
    """T2 and T3 both score BETTER than the T1 reference; only T4 is worse.
    Reproduced, not corrected — pinned so nobody "fixes" the ordering."""
    assert T_STAGE_BETA["1"] == 0.0
    assert T_STAGE_BETA["2"] < T_STAGE_BETA["3"] < 0 < T_STAGE_BETA["4"]


def test_splenectomy_is_the_largest_single_term():
    """+0.907, larger than any nodal or margin effect. It marks extended
    resection for locally advanced disease, not a treatment effect."""
    common = dict(age=62, male=True, location="head", differentiation="moderate",
                  positive_nodes=3, negative_nodes=12, t_stage="3", size_cm=3.0)
    base = msk_pancreatic_predict(**common)["survival"]
    spleen = msk_pancreatic_predict(**common, splenectomy=True)["survival"]
    margin = msk_pancreatic_predict(**common, resection_margin_positive=True)["survival"]
    posterior = msk_pancreatic_predict(**common, posterior_margin_positive=True)["survival"]
    assert (base - spleen) > (base - margin)
    assert (base - spleen) > (base - posterior)


def test_non_head_tumours_score_better():
    """-0.759 for 'other'. Counterintuitive, and published."""
    assert LOCATION_BETA["other"] < LOCATION_BETA["head"] == 0.0
    common = dict(age=62, male=True, differentiation="moderate",
                  positive_nodes=2, negative_nodes=10, t_stage="2", size_cm=3.0)
    assert (msk_pancreatic_predict(**common, location="other")["survival"]
            > msk_pancreatic_predict(**common, location="head")["survival"])


def test_differentiation_is_ordered_around_a_moderate_reference():
    assert DIFFERENTIATION_BETA["well"] < DIFFERENTIATION_BETA["moderate"] == 0.0
    assert DIFFERENTIATION_BETA["poor"] > 0


def test_the_fixture_covers_every_level_and_both_bound_ends():
    cases = _cases()
    assert {c["t_stage"] for c in cases} == set(T_STAGE_BETA)
    assert {c["differentiation"].lower() for c in cases} == set(DIFFERENTIATION_BETA)
    assert {c["location"].lower() for c in cases} == set(LOCATION_BETA)
    assert (min(c["age"] for c in cases), max(c["age"] for c in cases)) == (33, 89)
    assert max(c["positive_nodes"] for c in cases) == 39
    assert max(c["negative_nodes"] for c in cases) == 83
    assert (min(c["size_cm"] for c in cases), max(c["size_cm"] for c in cases)) == (0.1, 16)


def test_size_is_centimetres_despite_the_tools_mm_label():
    """The hosted tool labels this field "mm" while validating 0.1-16 with
    knots at 2, 3.2 and 5.5. A 16 mm ceiling on resected pancreatic
    adenocarcinoma is not credible; these are centimetres."""
    from mayo_baseline.pancreatic.prognosis.msk_pancreatic import SIZE_CM_RANGE

    assert SIZE_CM_RANGE == (0.1, 16.0)
    with pytest.raises(ValueError, match="size_cm"):
        msk_pancreatic_predict(age=62, male=True, size_cm=30.0)   # 30 mm entered raw


def test_out_of_scope_inputs_are_refused():
    ok = dict(age=62, male=True)
    for field, bad in (("age", 25), ("age", 95), ("positive_nodes", 40),
                       ("negative_nodes", 90), ("size_cm", 20.0)):
        with pytest.raises(ValueError, match=field):
            msk_pancreatic_predict(**{**ok, field: bad})
    with pytest.raises(ValueError, match="months"):
        msk_pancreatic_predict(**ok, months=60)
    with pytest.raises(ValueError, match="t_stage"):
        msk_pancreatic_predict(**ok, t_stage="5")


def test_metadata():
    out = msk_pancreatic_predict(age=62, male=True)
    assert out["model_id"] == "msk_pancreatic"
    assert out["axis"] == "prognosis"
    assert out["disease"] == "pancreatic"
    assert out["months"] == 12
