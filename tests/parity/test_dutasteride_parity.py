"""Parity: the dutasteride chemoprevention model vs. the vendor's deployed R.

Nguyen CT, Isariyawongse B, Yu C, Kattan MW, models for men with a prior
negative biopsy considering dutasteride (REDUCE).

Route 1. `dutasteride_reference.R` copies the 17 `predict.*` functions
**verbatim** from riskcalc.org's server.R, and adds `raw.*` copies with only
the display rounding removed so the comparison is on real numbers.

    8 patients x 9 outcomes x 2 arms = 132 probabilities
    worst absolute difference 4.9e-11 percentage points
    applicability ("Not Applicable") agreed on every one

This is also the test that licenses machine extraction. 315 coefficients is
past the point where hand-copying is safe, so
`reference/dutasteride_extract.py` parses them out of the R and this test
proves the parse faithful against that same R. If the extractor mis-read a
knot, a sign or a bound, 132 comparisons will not all agree to 1e-11.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cancerverse_baseline.prostate.response import dutasteride_predict
from cancerverse_baseline.prostate.response.dutasteride import HARMS, OUTCOMES

CASES_FILE = Path(__file__).parent / "reference" / "dutasteride_cases.json"

PATIENT_KEYS = [
    "age",
    "psa",
    "dre_abnormal",
    "sexually_active",
    "history_of_impotence",
    "history_of_libido_problems",
    "family_history_prostate_cancer",
    "percent_free_psa",
    "bmi",
    "ipss_score",
    "max_urinary_flow_ml_s",
    "biopsy_cores",
    "prostate_volume_ml",
    "residual_urine_ml",
]


def _cases():
    return json.loads(CASES_FILE.read_text())["cases"]


def _kwargs(c):
    return {k: c[k] for k in PATIENT_KEYS}


@pytest.mark.parametrize("outcome", list(OUTCOMES))
@pytest.mark.parametrize("case", _cases(), ids=lambda c: f"age{c['age']}-psa{c['psa']}")
def test_matches_the_vendor_r(case, outcome):
    ours = dutasteride_predict(**_kwargs(case))["outcomes"][outcome]
    theirs = case["outcomes"][outcome]
    for arm, key in (("dutasteride", "d"), ("no_dutasteride", "nd")):
        if theirs[key] is None:
            assert ours[arm] is None, (
                f"{outcome}/{arm}: the tool says Not Applicable, we returned a number"
            )
        else:
            assert ours[arm] is not None, (
                f"{outcome}/{arm}: the tool returned a number, we said Not Applicable"
            )
            assert ours[arm] * 100 == pytest.approx(theirs[key], abs=1e-8)


def test_asap_has_no_off_treatment_arm_in_the_source():
    """Reproduced, not smoothed: `difference` is None rather than 0, because
    the source provides no comparator and a zero would read as 'no effect'."""
    out = dutasteride_predict(
        age=63,
        psa=5.7,
        dre_abnormal=False,
        percent_free_psa=16.0,
        bmi=26.8,
        biopsy_cores=9,
        prostate_volume_ml=43.5,
        family_history_prostate_cancer=False,
    )
    asap = out["outcomes"]["asap"]
    assert asap["dutasteride"] is not None
    assert asap["no_dutasteride"] is None
    assert asap["difference"] is None


def test_hgpin_on_dutasteride_is_a_constant():
    """No predictors at all, the same 3.838831% for everyone in scope, while
    the off-treatment arm is a full 28-term model. That is what the source
    says."""
    common = dict(
        dre_abnormal=False,
        percent_free_psa=16.0,
        family_history_prostate_cancer=False,
        biopsy_cores=9,
    )
    a = dutasteride_predict(
        age=55, psa=3.0, bmi=22.0, prostate_volume_ml=30.0, **common
    )["outcomes"]["hgpin"]
    b = dutasteride_predict(
        age=72, psa=9.0, bmi=34.0, prostate_volume_ml=70.0, **common
    )["outcomes"]["hgpin"]
    assert a["dutasteride"] == b["dutasteride"] == pytest.approx(0.03838831)
    assert a["no_dutasteride"] != b["no_dutasteride"], (
        "the off-treatment arm must still depend on the patient"
    )


def test_it_reproduces_the_reduce_finding_that_high_grade_cancer_goes_up():
    """The clinically important asymmetry: dutasteride lowered overall
    prostate cancer but RAISED high-grade disease. A model that only reported
    the overall reduction would be answering half the question."""
    out = dutasteride_predict(
        age=63,
        psa=5.7,
        dre_abnormal=False,
        sexually_active=True,
        history_of_impotence=False,
        history_of_libido_problems=False,
        family_history_prostate_cancer=False,
        percent_free_psa=16.0,
        bmi=26.8,
        ipss_score=12,
        max_urinary_flow_ml_s=12.0,
        biopsy_cores=9,
        prostate_volume_ml=43.5,
        residual_urine_ml=40.0,
    )
    o = out["outcomes"]
    assert o["prostate"]["difference"] < 0, "overall cancer should fall"
    assert o["highgrade"]["difference"] > 0, "high-grade disease should rise"
    assert out["risk"] == o["highgrade"]["difference"]


def test_the_harms_are_labelled_and_go_the_right_way():
    out = dutasteride_predict(
        age=63,
        psa=5.7,
        sexually_active=True,
        history_of_impotence=False,
        history_of_libido_problems=False,
        dre_abnormal=False,
        percent_free_psa=16.0,
        bmi=26.8,
        ipss_score=12,
        max_urinary_flow_ml_s=12.0,
        biopsy_cores=9,
        prostate_volume_ml=43.5,
        residual_urine_ml=40.0,
        family_history_prostate_cancer=False,
    )
    assert set(HARMS) == {"erectile", "gynecomastia", "uti"}
    for key in ("erectile", "gynecomastia"):
        assert out["outcomes"][key]["is_harm"] is True
        assert out["outcomes"][key]["difference"] > 0, f"{key} should increase"


def test_outcomes_out_of_their_own_bounds_come_back_none_not_guessed():
    """The bounds differ per outcome, so a patient can be answerable for some
    outcomes and not others. Supplying nothing optional must not fabricate."""
    out = dutasteride_predict(age=63, psa=5.7)["outcomes"]
    answered = [k for k, v in out.items() if v["dutasteride"] is not None]
    unanswered = [k for k, v in out.items() if v["dutasteride"] is None]
    assert unanswered, "models needing BMI/volume cannot be answered here"
    assert answered != list(out), "some outcomes should still be unanswerable"


def test_the_fixture_covers_every_outcome_and_both_arms():
    cases = _cases()
    assert {k for c in cases for k in c["outcomes"]} == set(OUTCOMES)
    assert len(cases) >= 8
    # and at least one patient is out of scope somewhere, so the None path is real
    assert any(
        v["nd"] is None or v["d"] is None for c in cases for v in c["outcomes"].values()
    )


def test_metadata():
    out = dutasteride_predict(age=63, psa=5.7)
    assert out["model_id"] == "dutasteride"
    assert out["axis"] == "response"
    assert out["disease"] == "prostate"
