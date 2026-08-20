"""Parity: PBCG vs. the vendor's own deployed R, across all eight sub-models.

Ankerst DP, Straubinger J, Selig K, et al. Eur Urol. 2018;74(2):197-203.

Route 1. `pbcg_reference.R` copies the `risk` function **verbatim** from
riskcalc.org's published source and runs it under R 4.6.1. It also defines
`risk_raw`, the same function with only the two `round()` calls removed, so the
comparison can be made on unrounded probabilities.

    12 patients x 3 outcomes = 36 probabilities
    worst absolute difference 4.8e-11 percentage points

The cases are chosen so that **all eight coefficient sets are exercised**. PBCG
fits a separate model for every pattern of missing prior-biopsy / DRE /
family-history data, and a test that only used complete records would leave
seven of the eight untouched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cancerverse_baseline.prostate.detection import pbcg_predict, rounded_like_riskcalc
from cancerverse_baseline.prostate.detection.pbcg import COEFFICIENTS

CASES_FILE = Path(__file__).parent / "reference" / "pbcg_cases.json"


def _cases():
    return json.loads(CASES_FILE.read_text())["cases"]


def _kwargs(c):
    return dict(psa=c["psa"], age=c["age"],
                african_ancestry=c["african_ancestry"],
                prior_biopsy=c["prior_biopsy"], dre_abnormal=c["dre_abnormal"],
                family_history=c["family_history"])


def _id(c):
    known = "".join(k for k, f in (("B", "prior_biopsy"), ("D", "dre_abnormal"),
                                   ("F", "family_history")) if c[f] is not None)
    return f"psa{c['psa']}-{known or 'none'}"


@pytest.mark.parametrize("outcome,key", [("no_cancer", "no_cancer_pct"),
                                         ("low_grade", "low_grade_pct"),
                                         ("high_grade", "high_grade_pct")])
@pytest.mark.parametrize("case", _cases(), ids=_id)
def test_matches_the_vendor_r(case, outcome, key):
    ours = pbcg_predict(**_kwargs(case))["probabilities"][outcome] * 100
    assert ours == pytest.approx(case[key], abs=1e-8)


def test_the_fixture_exercises_all_eight_submodels():
    """PBCG's whole point is one fitted model per missing-data pattern. A
    fixture of complete records would test one of eight."""
    seen = {
        (c["prior_biopsy"] is not None, c["dre_abnormal"] is not None,
         c["family_history"] is not None)
        for c in _cases()
    }
    assert seen == set(COEFFICIENTS), f"untested sub-models: {set(COEFFICIENTS) - seen}"
    assert len(COEFFICIENTS) == 8


def test_each_submodel_has_matching_term_counts():
    """intercept + log2(PSA) + age + ancestry, plus one per known optional."""
    for key, betas in COEFFICIENTS.items():
        expected = 4 + sum(key)
        assert len(betas["low"]) == expected, key
        assert len(betas["high"]) == expected, key


def test_probabilities_sum_to_one():
    for c in _cases():
        p = pbcg_predict(**_kwargs(c))["probabilities"]
        assert sum(p.values()) == pytest.approx(1.0)
        assert all(0.0 < v < 1.0 for v in p.values())


def test_risk_is_the_high_grade_probability():
    """A biopsy decision turns on high-grade disease, not any cancer. The
    convenience `risk` key must not quietly mean 'any cancer'."""
    out = pbcg_predict(psa=6.0, age=65, african_ancestry=False)
    assert out["risk"] == out["probabilities"]["high_grade"]
    assert out["risk"] < out["probabilities"]["no_cancer"] + out["probabilities"]["low_grade"]


def test_unknown_predictors_select_a_smaller_model_rather_than_imputing():
    """Dropping DRE must change which coefficient set runs, not set DRE to 0."""
    known = pbcg_predict(psa=6.0, age=65, african_ancestry=False,
                         dre_abnormal=False)
    unknown = pbcg_predict(psa=6.0, age=65, african_ancestry=False)
    assert known["submodel"] == ("dre_abnormal",)
    assert unknown["submodel"] == ()
    assert known["risk"] != unknown["risk"], (
        "a missing predictor must not be equivalent to a negative one"
    )


def test_the_rounding_artefact_is_reproduced_only_on_request():
    """riskcalc.org rounds no-cancer and low-grade, then derives high grade as
    the remainder — so all the rounding error lands on the clinically decisive
    number. We return unrounded; this reproduces the tool."""
    for c in _cases():
        out = pbcg_predict(**_kwargs(c))
        shown = rounded_like_riskcalc(out)
        assert [shown["no_cancer"], shown["low_grade"], shown["high_grade"]] == c["rounded"]
    # and the artefact is real: at least one case is off by a point
    off = [
        c for c in _cases()
        if abs(rounded_like_riskcalc(pbcg_predict(**_kwargs(c)))["high_grade"]
               - c["high_grade_pct"]) > 0.5
    ]
    assert off, "expected the derive-the-remainder rounding to bite somewhere"


def test_invalid_inputs():
    with pytest.raises(ValueError, match="psa"):
        pbcg_predict(psa=0, age=65, african_ancestry=False)
    with pytest.raises(ValueError, match="age"):
        pbcg_predict(psa=5.0, age=0, african_ancestry=False)


def test_metadata():
    out = pbcg_predict(psa=5.0, age=65, african_ancestry=False)
    assert out["model_id"] == "pbcg"
    assert out["axis"] == "detection"
    assert out["disease"] == "prostate"
