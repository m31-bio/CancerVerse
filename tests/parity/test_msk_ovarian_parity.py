"""Parity: MSK ovarian nomogram vs. the vendor's own deployed R.

Abu-Rustum NR, Awtrey CS, Huh J, Eisenhauer EL, Barakat RR, Kattan MW.
Gynecol Oncol. 2008;108(1).

Route 1. `msk_ovarian_reference.R` copies the model expression **verbatim**
from riskcalc.org's server.R and runs it under R 4.6.1.

    8 patients, worst absolute difference 4.4e-11 percentage points

**This cell was recorded as having no published equation until 2026-08-06.**
That verdict was a claim about the literature made without looking at who
deploys these models, and it was wrong.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cancerverse_baseline.ovarian.prognosis import msk_ovarian_predict
from cancerverse_baseline.ovarian.prognosis.msk_ovarian import RESIDUAL_BETA

CASES_FILE = Path(__file__).parent / "reference" / "msk_ovarian_cases.json"

RESIDUAL = {"No Gross Residual": "no_gross_residual", "<0.5 cm": "lt_0.5_cm",
            "0.5-1 cm": "0.5_1_cm", "1-2 cm": "1_2_cm", ">2 cm": "gt_2_cm"}


def _cases():
    return json.loads(CASES_FILE.read_text())["cases"]


def _kwargs(c):
    return dict(age=c["age"], grade=c["grade"], histology_yes=c["histology_yes"],
                platelets=c["platelets"], ascites=c["ascites"],
                residual_disease=RESIDUAL[c["residual"]])


@pytest.mark.parametrize("case", _cases(), ids=lambda c: f"{c['age']}-G{c['grade']}")
def test_matches_the_vendor_r(case):
    ours = msk_ovarian_predict(**_kwargs(case))["survival"] * 100
    assert ours == pytest.approx(case["surv_5yr_pct"], abs=1e-8)


def test_the_residual_disease_reference_is_the_middle_category():
    """0.5-1 cm carries no term — not 'no gross residual', which a reader will
    assume. Two levels are therefore protective and two are harmful."""
    assert RESIDUAL_BETA["0.5_1_cm"] == 0.0
    assert RESIDUAL_BETA["no_gross_residual"] < 0
    assert RESIDUAL_BETA["lt_0.5_cm"] < 0
    assert RESIDUAL_BETA["1_2_cm"] > 0
    assert RESIDUAL_BETA["gt_2_cm"] > 0


def test_residual_disease_is_monotone_and_dominant():
    """Monotone despite the odd reference, and the largest effect in the model
    — which is the clinical argument for maximal cytoreduction."""
    order = ["no_gross_residual", "lt_0.5_cm", "0.5_1_cm", "1_2_cm", "gt_2_cm"]
    common = dict(age=60, grade="3", histology_yes=False, platelets=400,
                  ascites=True)
    survivals = [msk_ovarian_predict(**common, residual_disease=r)["survival"]
                 for r in order]
    assert survivals == sorted(survivals, reverse=True)
    spread = survivals[0] - survivals[-1]
    grade = abs(msk_ovarian_predict(**{**common, "grade": "1-2"},
                                    residual_disease="0.5_1_cm")["survival"]
                - msk_ovarian_predict(**common,
                                      residual_disease="0.5_1_cm")["survival"])
    assert spread > grade * 5


def test_the_fixture_covers_every_residual_level_and_both_age_bounds():
    cases = _cases()
    assert {RESIDUAL[c["residual"]] for c in cases} == set(RESIDUAL_BETA)
    assert min(c["age"] for c in cases) == 22
    assert max(c["age"] for c in cases) == 87
    assert min(c["platelets"] for c in cases) == 113
    assert max(c["platelets"] for c in cases) == 1078


def test_out_of_scope_inputs_are_refused():
    ok = dict(age=60, grade="3", histology_yes=False, platelets=400,
              ascites=False, residual_disease="0.5_1_cm")
    with pytest.raises(ValueError, match="age"):
        msk_ovarian_predict(**{**ok, "age": 15})
    with pytest.raises(ValueError, match="platelets"):
        msk_ovarian_predict(**{**ok, "platelets": 50})
    with pytest.raises(ValueError, match="grade"):
        msk_ovarian_predict(**{**ok, "grade": "4"})
    with pytest.raises(ValueError, match="residual_disease"):
        msk_ovarian_predict(**{**ok, "residual_disease": "bogus"})


def test_metadata():
    out = msk_ovarian_predict(age=60, grade="3", histology_yes=True,
                              platelets=400, ascites=False,
                              residual_disease="no_gross_residual")
    assert out["model_id"] == "msk_ovarian"
    assert out["axis"] == "prognosis"
    assert out["disease"] == "ovarian"
    assert out["horizon_years"] == 5
