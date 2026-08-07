"""Parity: MSK gastric nomogram vs. the vendor's own deployed R.

Kattan MW, Karpeh MS, Mazumdar M, Brennan MF. J Clin Oncol. 2003;21(19).

The paper publishes a nomogram FIGURE and no closed-form model, so for a long
time this cell was recorded as unreachable-without-a-validation-paper, and a
paper request was open for one. It turned out no paper was needed: Cleveland
Clinic publishes the deployed calculator's R source, and riskcalc.org's own
page for it cites Kattan 2003.

That makes this a route-1 check, the strongest kind: `msk_gastric_reference.R`
copies the two model expressions **verbatim** from the vendor's `server.R`, so
the comparison is against their arithmetic, not our reading of it. If we had
mis-transcribed a coefficient, a knot, or the depth level order, this fails.

    12 patients x 2 horizons = 24 probabilities
    worst absolute difference: 4.7e-11 percentage points

The cases deliberately hit both ends of every validated input bound (age 25 and
96, positive nodes 0 and 23, negative nodes 0 and 146, size 0.1 and 21 cm), all
seven depth levels, all four primary sites and all three Lauren types — because
the model is splined in four variables and a knot error only shows up on one
side of the knot.

Fixture captured by `Rscript tests/parity/reference/msk_gastric_reference.R`.
This test is offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mayo_baseline.gastric.prognosis import msk_gastric_predict
from mayo_baseline.gastric.prognosis.msk_gastric import (
    DEPTH_LEVELS,
    LAUREN_BETA,
    PRIMARY_SITE_BETA,
)

CASES_FILE = Path(__file__).parent / "reference" / "msk_gastric_cases.json"

# The app's display strings -> our keys.
SITE = {
    "Antrum or Piloric": "antrum_or_pyloric",
    "Body or Middle One Third": "body_or_middle_third",
    "Gastroesophageal Junction": "gastroesophageal_junction",
    "Proximal or Upper One Third": "proximal_or_upper_third",
}

TOLERANCE_PCT = 1e-8


def _cases():
    return json.loads(CASES_FILE.read_text())["cases"]


def _kwargs(c: dict) -> dict:
    return dict(
        age=c["age"], male=c["male"], primary_site=SITE[c["primary_site"]],
        lauren=c["lauren"].lower(), size_cm=c["size_cm"],
        positive_nodes=c["positive_nodes"], negative_nodes=c["negative_nodes"],
        depth=DEPTH_LEVELS[c["depth_code"] - 1],
    )


def _id(c):
    return f"{c['age']}{'M' if c['male'] else 'F'}-d{c['depth_code']}-n{c['positive_nodes']}"


@pytest.mark.parametrize("years,key", [(5, "dss_5yr_pct"), (9, "dss_9yr_pct")])
@pytest.mark.parametrize("case", _cases(), ids=_id)
def test_matches_the_vendor_r(case, years, key):
    ours = msk_gastric_predict(**_kwargs(case), years=years)["survival"] * 100
    assert ours == pytest.approx(case[key], abs=TOLERANCE_PCT)


def test_the_fixture_exercises_every_categorical_level():
    """A splined ordinal and three factors: if the fixture missed a level, a
    wrong coefficient there would pass unnoticed."""
    cases = _cases()
    assert {c["depth_code"] for c in cases} == set(range(1, 8))
    assert {SITE[c["primary_site"]] for c in cases} == set(PRIMARY_SITE_BETA)
    assert {c["lauren"].lower() for c in cases} == set(LAUREN_BETA)
    assert {c["male"] for c in cases} == {True, False}


def test_the_fixture_reaches_both_ends_of_every_validated_bound():
    from mayo_baseline.gastric.prognosis.msk_gastric import (
        AGE_RANGE,
        NEGATIVE_NODES_RANGE,
        POSITIVE_NODES_RANGE,
        SIZE_CM_RANGE,
    )

    cases = _cases()
    for field, bounds in (("age", AGE_RANGE), ("size_cm", SIZE_CM_RANGE),
                          ("positive_nodes", POSITIVE_NODES_RANGE),
                          ("negative_nodes", NEGATIVE_NODES_RANGE)):
        values = {c[field] for c in cases}
        assert min(values) == bounds[0], f"{field}: fixture never reaches {bounds[0]}"
        assert max(values) == bounds[1], f"{field}: fixture never reaches {bounds[1]}"


def test_depth_is_ordinal_and_its_order_is_part_of_the_model():
    """Depth enters as the NUMBER 1-7, then splined. Reordering the levels
    changes every prediction, so the order is pinned here."""
    assert DEPTH_LEVELS[0] == "mucosa"
    assert DEPTH_LEVELS[-1] == "adjacent_organ_involvement"
    assert len(DEPTH_LEVELS) == 7
    common = dict(age=60, male=True, primary_site="antrum_or_pyloric",
                  lauren="intestinal", size_cm=3.0, positive_nodes=2,
                  negative_nodes=15)
    survivals = [msk_gastric_predict(**common, depth=d)["survival"]
                 for d in DEPTH_LEVELS]
    assert survivals == sorted(survivals, reverse=True), (
        "deeper invasion must not improve survival"
    )


def test_negative_nodes_improve_survival():
    """The stage-migration property: a more thorough lymphadenectomy raises the
    prediction. -0.047 per node over a range to 146 makes this one of the
    model's largest effects, which surprises people."""
    common = dict(age=60, male=True, primary_site="antrum_or_pyloric",
                  lauren="intestinal", size_cm=3.0, positive_nodes=3,
                  depth="subserosa")
    few = msk_gastric_predict(**common, negative_nodes=3)["survival"]
    many = msk_gastric_predict(**common, negative_nodes=40)["survival"]
    assert many > few


def test_out_of_scope_inputs_are_refused():
    ok = dict(age=60, male=True, primary_site="antrum_or_pyloric",
              lauren="intestinal", size_cm=3.0, positive_nodes=2,
              negative_nodes=15, depth="subserosa")
    for field, bad in (("age", 20), ("age", 100), ("positive_nodes", 24),
                       ("negative_nodes", 200), ("size_cm", 25.0)):
        with pytest.raises(ValueError, match=field):
            msk_gastric_predict(**{**ok, field: bad})
    with pytest.raises(ValueError, match="years"):
        msk_gastric_predict(**ok, years=10)
    with pytest.raises(ValueError, match="lauren"):
        msk_gastric_predict(**{**ok, "lauren": "bogus"})


def test_metadata():
    out = msk_gastric_predict(age=60, male=True, primary_site="antrum_or_pyloric",
                              lauren="intestinal", size_cm=3.0, positive_nodes=2,
                              negative_nodes=15, depth="subserosa")
    assert out["model_id"] == "msk_gastric"
    assert out["axis"] == "prognosis"
    assert out["disease"] == "gastric"
    assert 0.0 < out["survival"] < 1.0
    assert out["risk"] == pytest.approx(1.0 - out["survival"])
