"""Parity: CRC-PRO vs. the vendor's own deployed R, and one live defect in it.

Wells BJ, Kattan MW, Cooper GS, Jackson L, Koroukian S. J Am Board Fam Med. 2014;27(1):42-55.

Route 1. `crc_pro_reference.R` copies the model expression **verbatim** from
riskcalc.org's `ColorectalCancer/server.R` and runs it under R 4.6.1, so the
comparison is against their arithmetic rather than our reading of it.

    12 patients, worst absolute difference 4.5e-11 percentage points

The cases hit both ends of every validated bound (age 45/85, weight 75/350 lb,
height 60/80 in, pack-years 0/50, alcohol 0/12, education 6/20, meat 0/5,
activity 0/4), all five ethnicities including the Black reference level, and
every level of estrogen, NSAID and aspirin, because the model is splined in
five variables per sex and a knot error only shows on one side of the knot.

THE DEFECT
----------
The hosted calculator cannot apply its own previous-estrogen coefficient. Its
UI offers `'No'`, `'Yes, but not currently'`, `'Yes-currently'`; the expression
tests `(Estrogen == "Yes-currently")` and `(Estrogen == "Yes-previously")`, and
nothing the UI can produce equals the latter. The −0.044320489 term is dead, so
a woman reporting **previous** estrogen use is scored exactly like one reporting
**none**.

The paper is unambiguous that this is a three-level variable: "currently,
previously, or no", so this module implements the paper, and
`emulate_deployed_defect=True` reproduces the tool. Both are tested:

  * with the flag on, we match the vendor on all 12 cases;
  * with it off, exactly the two previous-estrogen women differ, and the
    deployed tool over-estimates their risk by about 4.2%.

That split is the point. Matching a reference implementation is not the goal;
matching it *and knowing precisely where it departs from the paper* is.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cancerverse_baseline.colorectal.detection import crc_pro_predict
from cancerverse_baseline.colorectal.detection.crc_pro import (
    ASPIRIN_BETA,
    ESTROGEN_BETA,
    ETHNICITY_BETA,
    NSAID_BETA,
    RANGES,
)

CASES_FILE = Path(__file__).parent / "reference" / "crc_pro_cases.json"

NSAID = {
    "No": "no",
    "Yes, but not currently": "previously",
    "Yes, currently": "currently",
}
ESTROGEN = {
    "No": "no",
    "Yes, but not currently": "previously",
    "Yes-currently": "currently",
}
ASPIRIN = {"No": "no", "Yes - Not Currently": "previously", "Yes": "currently"}

TOLERANCE_PCT = 1e-8


def _cases():
    return json.loads(CASES_FILE.read_text())["cases"]


def _kwargs(c: dict) -> dict:
    return dict(
        male=c["male"],
        age=c["age"],
        ethnicity=c["ethnicity"],
        weight_lb=c["weight_lb"],
        height_in=c["height_in"],
        years_education=c["years_education"],
        pack_years=c["pack_years"],
        alcohol_drinks_per_day=c["alcohol"],
        family_history=c["family_history"],
        multivitamin=c["multivitamin"],
        diabetes=c["diabetes"],
        estrogen=ESTROGEN[c["estrogen"]],
        nsaid=NSAID[c["nsaid"]],
        aspirin=ASPIRIN[c["aspirin"]],
        red_meat_oz_per_day=c["red_meat"],
        activity_hours_per_day=c["activity"],
    )


def _id(c):
    return f"{'M' if c['male'] else 'F'}{c['age']}-{c['ethnicity']}"


@pytest.mark.parametrize("case", _cases(), ids=_id)
def test_matches_the_vendor_r_when_emulating_its_defect(case):
    ours = crc_pro_predict(**_kwargs(case), emulate_deployed_defect=True)["risk"] * 100
    assert ours == pytest.approx(case["risk_pct"], abs=TOLERANCE_PCT)


def test_the_defect_changes_exactly_the_previous_estrogen_women():
    """Paper-faithful vs deployed. Nothing else may move."""
    moved = []
    for c in _cases():
        paper = crc_pro_predict(**_kwargs(c))["risk"]
        deployed = crc_pro_predict(**_kwargs(c), emulate_deployed_defect=True)["risk"]
        if abs(paper - deployed) > 1e-15:
            moved.append(c)
    assert moved, "expected the defect to bite somewhere"
    assert all(not c["male"] for c in moved), "men have no estrogen term"
    assert all(ESTROGEN[c["estrogen"]] == "previously" for c in moved), (
        f"only previous-estrogen women should move, got {[c['estrogen'] for c in moved]}"
    )
    assert len(moved) == 2


def test_the_deployed_tool_over_estimates_those_women():
    """The dead coefficient is protective (-0.0443), so failing to apply it
    inflates risk. Around 4% relative, which is not nothing at a screening
    threshold."""
    for c in _cases():
        if c["male"] or ESTROGEN[c["estrogen"]] != "previously":
            continue
        paper = crc_pro_predict(**_kwargs(c))["risk"]
        deployed = crc_pro_predict(**_kwargs(c), emulate_deployed_defect=True)["risk"]
        assert deployed > paper
        assert 0.03 < (deployed - paper) / paper < 0.06


def test_previous_estrogen_is_scored_as_no_estrogen_by_the_deployed_tool():
    """State the defect directly, not only via its effect size."""
    base = dict(
        male=False,
        age=65,
        ethnicity="white",
        weight_lb=160,
        height_in=65,
        years_education=14,
        pack_years=5,
        alcohol_drinks_per_day=1.0,
        family_history=False,
        multivitamin=False,
        diabetes=False,
        nsaid="no",
    )
    none_ = crc_pro_predict(**base, estrogen="no", emulate_deployed_defect=True)["risk"]
    prev = crc_pro_predict(**base, estrogen="previously", emulate_deployed_defect=True)[
        "risk"
    ]
    assert prev == pytest.approx(none_), "the deployed tool cannot tell them apart"
    # while the paper's model can.
    prev_paper = crc_pro_predict(**base, estrogen="previously")["risk"]
    assert prev_paper < none_


def test_men_and_women_are_different_models_not_one_with_a_sex_term():
    """The paper: NSAIDs matter for women only; red meat and activity for men
    only. So the sex-specific arguments must be inert for the other sex."""
    common = dict(
        age=65,
        ethnicity="white",
        weight_lb=170,
        height_in=68,
        years_education=14,
        pack_years=10,
        alcohol_drinks_per_day=1.0,
        family_history=False,
        multivitamin=False,
        diabetes=False,
    )
    m1 = crc_pro_predict(male=True, **common, estrogen="currently", nsaid="currently")[
        "risk"
    ]
    m2 = crc_pro_predict(male=True, **common, estrogen="no", nsaid="no")["risk"]
    assert m1 == pytest.approx(m2), "estrogen and NSAIDs must not enter the men's model"

    f1 = crc_pro_predict(
        male=False,
        **common,
        aspirin="currently",
        red_meat_oz_per_day=4.0,
        activity_hours_per_day=3.0,
    )["risk"]
    f2 = crc_pro_predict(
        male=False,
        **common,
        aspirin="no",
        red_meat_oz_per_day=0.0,
        activity_hours_per_day=0.0,
    )["risk"]
    assert f1 == pytest.approx(f2), (
        "aspirin, meat and activity must not enter the women's model"
    )


def test_the_fixture_covers_every_categorical_level_and_both_bound_ends():
    cases = _cases()
    assert {c["ethnicity"].lower() for c in cases} == set(ETHNICITY_BETA["male"])
    assert {ESTROGEN[c["estrogen"]] for c in cases if not c["male"]} == set(
        ESTROGEN_BETA
    )
    assert {NSAID[c["nsaid"]] for c in cases if not c["male"]} == set(NSAID_BETA)
    assert {ASPIRIN[c["aspirin"]] for c in cases if c["male"]} == set(ASPIRIN_BETA)
    for field, key in (
        ("age", "age"),
        ("weight_lb", "weight_lb"),
        ("height_in", "height_in"),
        ("pack_years", "pack_years"),
        ("alcohol_drinks_per_day", "alcohol"),
        ("years_education", "years_education"),
    ):
        lo, hi = RANGES[field]
        values = {c[key] for c in cases}
        assert min(values) == lo and max(values) == hi, f"{field} not straddled"


def test_bmi_is_derived_from_pounds_and_inches():
    """The spline knots assume the app's own conversion. Passing kilograms and
    metres instead would land the BMI off by a factor of about 703, which is
    silent, every knot would simply saturate."""
    from cancerverse_baseline.colorectal.detection.crc_pro import bmi_from_imperial

    # 25 kg/m^2 at 1.75 m is 76.5625 kg = 168.8 lb, 68.898 in.
    kg, m = 25.0 * 1.75**2, 1.75
    lb, inches = kg / 0.45359237, m / 0.0254
    assert bmi_from_imperial(weight_lb=lb, height_in=inches) == pytest.approx(25.0)

    out = crc_pro_predict(
        male=True,
        age=60,
        ethnicity="white",
        weight_lb=lb,
        height_in=inches,
        years_education=14,
        pack_years=0,
        alcohol_drinks_per_day=0.0,
        family_history=False,
        multivitamin=False,
        diabetes=False,
    )
    assert out["bmi"] == pytest.approx(25.0)


def test_out_of_scope_inputs_are_refused():
    ok = dict(
        male=True,
        age=60,
        ethnicity="white",
        weight_lb=170,
        height_in=68,
        years_education=14,
        pack_years=5,
        alcohol_drinks_per_day=1.0,
        family_history=False,
        multivitamin=False,
        diabetes=False,
    )
    for field, bad in (
        ("age", 40),
        ("age", 90),
        ("weight_lb", 60),
        ("height_in", 55),
        ("pack_years", 60),
        ("alcohol_drinks_per_day", 15),
        ("years_education", 3),
    ):
        with pytest.raises(ValueError, match=field):
            crc_pro_predict(**{**ok, field: bad})
    with pytest.raises(ValueError, match="ethnicity"):
        crc_pro_predict(**{**ok, "ethnicity": "bogus"})


def test_metadata():
    out = crc_pro_predict(
        male=False,
        age=60,
        ethnicity="black",
        weight_lb=150,
        height_in=64,
        years_education=12,
        pack_years=0,
        alcohol_drinks_per_day=0.0,
        family_history=False,
        multivitamin=False,
        diabetes=False,
    )
    assert out["model_id"] == "crc_pro"
    assert out["axis"] == "detection"
    assert out["disease"] == "colorectal"
    assert out["horizon_years"] == 10
    assert 0.0 < out["risk"] < 1.0
