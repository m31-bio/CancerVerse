"""Parity: our ARRM implementation vs. what Cibula et al actually printed.

Why this test is shaped differently from every other parity test here
---------------------------------------------------------------------
ARRM has two halves that come from two different artifacts, and they carry
very different evidential weight. The test treats them differently on purpose.

**Patient -> points** is Table 2 of the paper, and it is checked twice over,
both times against something outside our own transcription:

  1. `POINTS_DIVISOR` re-derives all thirteen published point values from the
     thirteen published betas alone. The paper states the construction
     ("weighted to the maximum sum of 100 points") and never states the
     divisor; taking that sentence literally gives 100/5.231 = 19.1168, and
     every point value falls out of `round(beta * divisor)` with no exceptions
     and no fudge. Thirteen independent agreements from one derived constant is
     not something a transcription error survives.
  2. The deployed ESGO calculator's own `<option value>` attributes are a
     second published statement of the same schedule, by the same authors,
     through a different medium. Compared at zero tolerance, in order.

**Points band -> outcome** is the weak half and is labelled as such. The paper
prints the full grid only as Fig. 3, a graphic. The numbers here were recovered
by re-running the calculator's estimator over the 4,343-row cohort the
calculator ships client-side, so the parity target has to be the twelve values
the paper states *in prose*, those are the only outcome numbers that exist as
text anywhere. Twelve of twelve reproduce, ten of them exactly.

The two that differ by 0.1 are the interesting ones and are pinned individually
below rather than being swallowed by a blanket tolerance, because "0.1 off" and
"0.1 off in the direction plain rounding predicts" are different findings.

Everything here is offline. reference/cibula_arrm_derive.py regenerates the
fixture and is where the estimator lives.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cancerverse_baseline.cervical.prognosis.arrm import (
    BANDS,
    MAX_SCORE,
    OUTCOME,
    POINTS,
    POINTS_DIVISOR,
    PREDICTORS,
    TABLE_2_COEFFICIENTS,
    cibula_arrm_predict,
)

REFERENCE = Path(__file__).parent / "reference"
CASES_FILE = REFERENCE / "cibula_arrm_cases.json"

#: The paper prints its outcome percentages to one decimal, so a half-unit in
#: the last place is 0.05 and any honest re-derivation can land 0.1 away when
#: the underlying value sits near a rounding boundary. Two of the twelve do.
ROUNDING = 0.1

#: The calculator's <option value> attributes, in page order, mapped to our
#: predictor names. Order is asserted, not just membership: histotype runs
#: 0, 7, 11, 33, 22. NOT ascending, so a test that sorted before comparing
#: would pass even if neuroendocrine and "other" were swapped, and swapping
#: those two is an 11-point error on the single largest coefficient in the
#: model.
_OPTION_KEYS = {
    "histotype": "histotype",
    "max-diameter": "tumour_diameter",
    "grade": "grade",
    "positive-lymph-nodes": "positive_pelvic_nodes",
    "space-invasion": "lvsi",
}


def _fixture() -> dict:
    return json.loads(CASES_FILE.read_text())


# --------------------------------------------------------------------------
# Half one: the points schedule. Checked against the betas, and against the
# authors' own deployment.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "predictor,level",
    [(p, lv) for p, pred in json.loads(
        (Path(__file__).resolve().parents[2] / "src" / "cancerverse_baseline" /
         "cervical" / "prognosis" / "data" / "cibula_arrm_2021.json").read_text()
     )["predictors"].items() for lv, d in pred["levels"].items()
     if d["beta"] is not None],
    ids=lambda x: str(x),
)
def test_every_published_point_value_falls_out_of_the_betas(predictor, level):
    """round(beta * 100/5.231) reproduces Table 2's points column, 13 for 13.

    This is the check that makes the points schedule trustworthy without
    anyone re-reading the PDF. The divisor is derived from the betas, so if a
    single beta or a single point value were mistranscribed, that row would
    disagree, and if the divisor itself were wrong, all thirteen would.
    """
    beta = TABLE_2_COEFFICIENTS[predictor][level]
    printed = POINTS[predictor][level]
    assert round(beta * POINTS_DIVISOR) == printed, (
        f"{predictor}/{level}: beta {beta} * {POINTS_DIVISOR:.4f} = "
        f"{beta * POINTS_DIVISOR:.3f}, which rounds to "
        f"{round(beta * POINTS_DIVISOR)}, but Table 2 prints {printed}"
    )


def test_the_divisor_is_what_the_papers_own_sentence_implies():
    """100 / (sum of the largest beta in each predictor).

    The paper says the score is "weighted to the maximum sum of 100 points"
    and never prints the constant. The worst patient is neuroendocrine (1.741)
    + >=4 cm (1.556) + grade 3 (0.457) + >=3 nodes (0.939) + LVSI (0.538) =
    5.231, so the divisor is 100/5.231. Pinned so nobody "tidies" it to 19.12
    and quietly breaks two of the thirteen point values.
    """
    worst = sum(max(v.values()) for v in TABLE_2_COEFFICIENTS.values())
    assert worst == pytest.approx(5.231, abs=1e-9)
    assert pytest.approx(100 / 5.231, rel=1e-12) == POINTS_DIVISOR


def test_the_worst_possible_patient_scores_exactly_100():
    assert sum(max(v.values()) for v in POINTS.values()) == MAX_SCORE == 100


@pytest.mark.parametrize("option_key", sorted(_OPTION_KEYS))
def test_the_deployed_calculator_states_the_same_points_in_the_same_order(option_key):
    """A second published statement of Table 2, by the same authors.

    The ESGO page's <option value> attributes are the points it adds up. They
    agree with Table 2 at zero tolerance, which rules out a transcription error
    in the half of the model that does all the arithmetic.
    """
    deployed = _fixture()["calculator_options"][option_key]
    ours = list(POINTS[_OPTION_KEYS[option_key]].values())
    assert ours == deployed


def test_the_reference_level_of_every_predictor_scores_zero():
    """Two predictors pool "not assessed" with negative, and that is the single
    most consequential thing about running this model on real records. Pinned
    here so the pooling stays visible: if someone later splits "not assessed"
    into its own level, this fails and they have to justify it against Table 2.
    """
    for name, pred in PREDICTORS.items():
        ref = pred["reference"]
        assert pred["levels"][ref]["beta"] is None, name
        assert POINTS[name][ref] == 0, name
    assert PREDICTORS["positive_pelvic_nodes"]["reference"] == "0_or_not_assessed"
    assert PREDICTORS["lvsi"]["reference"] == "no_or_not_assessed"
    # ...and grade does NOT get that treatment. Table 2 has no "not assessed"
    # level for it, so the module refuses an unknown grade rather than
    # defaulting it to 1.
    assert set(POINTS["grade"]) == {"1", "2", "3"}


# --------------------------------------------------------------------------
# Half two: the outcome grid. The parity target is the paper's prose, because
# that is the only place these numbers exist as text.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value", _fixture()["paper_values"],
    ids=lambda v: f"{v['quantity']}-band{v['band']}-yr{v['year']}",
)
def test_every_outcome_number_the_paper_prints_is_reproduced(value):
    key = "dfs_percent" if value["quantity"] == "dfs" else "arrm_percent"
    ours = OUTCOME[value["band"]][key][value["year"] - 1]
    # Both sides are decimals printed to one place, so the difference is
    # rounded to one place before comparing. `pytest.approx(3.2, abs=0.1)`
    # rejects 3.1: in binary the gap is 0.10000000000000009, and a tolerance
    # meant to permit "one in the last printed place" must not be decided by
    # the ninth binary digit.
    assert round(abs(ours - value["printed"]), 6) <= ROUNDING, (
        f"{value['locus']}: paper says {value['printed']}% "
        f"({value['quote']}), we derive {ours}%"
    )


def test_ten_of_the_twelve_printed_values_reproduce_exactly():
    """Not "within tolerance", exactly, to the digit the paper printed.

    A blanket 0.1 tolerance over twelve values would also pass if every one of
    them were 0.1 off, which would mean a systematic error in the estimator.
    Pinning the exact count separates "two rounding boundaries" from "a bias".
    """
    exact = [v for v in _fixture()["paper_values"] if v["abs_diff"] == 0.0]
    assert len(exact) == 10
    assert max(v["abs_diff"] for v in _fixture()["paper_values"]) == 0.1


def test_the_two_inexact_values_are_the_two_rounding_boundaries():
    """Named individually, because "which two" is the whole finding.

    Both are one-in-the-last-place low, both sit where the paper's own value
    would round up and ours rounds down, and neither is in the same band or the
    same quantity as the other, so this is rounding, not a band being wrong.
    """
    off = {(v["quantity"], v["band"], v["year"]): v
           for v in _fixture()["paper_values"] if v["abs_diff"] != 0.0}
    assert set(off) == {("dfs", 3, 5), ("arrm", 2, 3)}
    assert off[("dfs", 3, 5)]["printed"] == 63.3
    assert off[("dfs", 3, 5)]["computed"] == 63.2
    assert off[("arrm", 2, 3)]["printed"] == 3.2
    assert off[("arrm", 2, 3)]["computed"] == 3.1


@pytest.mark.parametrize("name", sorted(_fixture()["paper_cohort_counts"]))
def test_the_cohort_the_calculator_ships_is_the_cohort_the_paper_describes(name):
    """Six counts the paper states about its own data, reproduced exactly from
    the shipped rows. This is what ties the derived grid to the publication: if
    the deployment had been refitted on different data, these would drift.
    """
    stated = _fixture()["paper_cohort_counts"][name]
    assert stated["computed"] == stated["value"], stated["quote"]


def test_the_shipped_grid_and_the_fixture_grid_are_the_same_numbers():
    """The module's data file and the parity fixture are generated by the same
    script but committed separately, so they can drift apart. They must not.
    """
    assert _fixture()["grid"] == OUTCOME
    assert _fixture()["points_divisor"] == POINTS_DIVISOR


def test_band_totals_account_for_every_patient_and_every_recurrence():
    assert sum(row["n"] for row in OUTCOME) == 4343
    assert sum(row["n_recurrences"] for row in OUTCOME) == 528


def test_the_top_band_is_thirteen_patients_and_is_reported_as_such():
    """The highest-risk band holds 13 people, 12 of whom recurred. The paper
    stops its landmark analysis there at year three and says why; the module
    reports years four and five as None rather than as the 0.0% the arithmetic
    returns, because an empty band is not a risk-free one.
    """
    top = OUTCOME[4]
    assert (top["n"], top["n_recurrences"]) == (13, 12)
    assert top["arrm_reliable_through_year"] == 3
    out = cibula_arrm_predict(
        histotype="neuroendocrine", tumour_diameter_cm=5.0, grade=3,
        positive_pelvic_nodes=4, lvsi=True,
    )
    assert out["score"] == 100
    assert out["annual_recurrence_risk_in_derivation"][3:] == [None, None]
    assert "13 patients, 12 recurrences" in out["notes"]


# --------------------------------------------------------------------------
# End to end: the paper's own worked example.
# --------------------------------------------------------------------------


def test_bands_tile_zero_to_one_hundred_without_gap_or_overlap():
    """Zero is its own band, it is the absence of every risk predictor, not
    the bottom of a 25-point interval, and it is the band the surveillance
    recommendation actually turns on.
    """
    assert [(b["low"], b["high"]) for b in BANDS] == [
        (0, 0), (1, 25), (26, 50), (51, 75), (76, 100)
    ]
    for score in range(0, 101):
        matches = [b for b in BANDS if b["low"] <= score <= b["high"]]
        assert len(matches) == 1, f"score {score} matched {len(matches)} bands"


def test_a_patient_with_no_risk_factors_lands_in_the_zero_band():
    out = cibula_arrm_predict(
        histotype="squamous", tumour_diameter_cm=0.3, grade=1,
        positive_pelvic_nodes=0, lvsi=False,
    )
    assert out["score"] == 0
    assert out["band"] == 0
    assert out["band_n_in_derivation"] == 213
    assert out["observed_dfs_in_derivation"][4] == 97.5
