"""Xu 2021 gastric TRG score, checked against the paper's own printed values.

There is no reference implementation and no vendor calculator, so this is a
transcription check, not a parity check. What it can verify is that every
number we ship appears in the paper, that the score behaves the way the paper
says it does, and that the two directions most likely to be implemented
backwards are the paper's directions.
"""

from itertools import combinations

import pytest

from cancerverse_baseline.gastric.response.xu_trg_score import (
    CA19_9_CUTOFF,
    CA72_4_CUTOFF,
    HIGH_SCORE_THRESHOLD,
    LNMAX_CUTOFF,
    MAX_SCORE,
    OBSERVED_TRG0_RATE,
    POINTS,
    TABLE3_COEFFICIENTS,
    xu_gastric_trg_score_predict,
    xu_trg_points,
)

#: A patient scoring every point.
ALL_FOUR = dict(ca19_9_u_ml=5.0, ca72_4_u_ml=2.0, differentiation="well", lnmax_cm=2.0)
#: A patient scoring none.
NONE = dict(ca19_9_u_ml=50.0, ca72_4_u_ml=9.0, differentiation="poor", lnmax_cm=1.0)


def test_the_four_point_values_are_the_ones_table_4_prints():
    """Table 4: CA19-9 5, CA72-4 4, well differentiation 7, LNmax 7."""
    assert POINTS == {"ca19_9": 5, "ca72_4": 4, "differentiation": 7, "lnmax": 7}
    assert sum(POINTS.values()) == MAX_SCORE == 23


def test_the_cutoffs_are_the_ones_the_results_text_prints():
    assert (CA19_9_CUTOFF, CA72_4_CUTOFF, LNMAX_CUTOFF) == (10.90, 3.19, 1.535)
    assert HIGH_SCORE_THRESHOLD == 13


def test_the_range_runs_0_to_23():
    assert xu_trg_points(**NONE)["score"] == 0
    assert xu_trg_points(**ALL_FOUR)["score"] == MAX_SCORE


def test_the_cutoff_falls_in_an_unreachable_gap():
    """Weights 5, 4, 7, 7 cannot sum to 13.

    So "<=13 / >13" is exactly "<=12 / >=14", and the inclusive-or-exclusive
    question that usually haunts a published threshold cannot move anyone.
    """
    weights = list(POINTS.values())
    reachable = {sum(c) for n in range(len(weights) + 1)
                 for c in combinations(weights, n)}
    assert reachable == {0, 4, 5, 7, 9, 11, 12, 14, 16, 18, 19, 23}
    assert HIGH_SCORE_THRESHOLD not in reachable
    assert max(s for s in reachable if s < HIGH_SCORE_THRESHOLD) == 12
    assert min(s for s in reachable if s > HIGH_SCORE_THRESHOLD) == 14


@pytest.mark.parametrize("marker,cutoff,other", [
    ("ca19_9_u_ml", CA19_9_CUTOFF, "ca72_4_u_ml"),
    ("ca72_4_u_ml", CA72_4_CUTOFF, "ca19_9_u_ml"),
])
def test_low_tumour_markers_score_and_the_boundary_is_inclusive(marker, cutoff, other):
    """Table 3 indexes the "<=" level for both markers."""
    base = dict(ALL_FOUR)
    key = "ca19_9" if marker == "ca19_9_u_ml" else "ca72_4"

    at = xu_trg_points(**{**base, marker: cutoff})
    just_over = xu_trg_points(**{**base, marker: cutoff + 0.01})
    assert at["points"][key] == POINTS[key], "the cut-off value itself must score"
    assert just_over["points"][key] == 0
    assert at["score"] > just_over["score"]


def test_a_large_lymph_node_scores_and_that_is_the_papers_direction():
    """The one people will 'fix'.

    Table 3 indexes ">=1.535", Table 4 gives that level the 7 points, and the
    Discussion calls it a novel finding. A larger node scores TOWARD complete
    regression. If this test is ever failing, read the Discussion before
    changing the sign.
    """
    big = xu_trg_points(**{**ALL_FOUR, "lnmax_cm": LNMAX_CUTOFF})
    small = xu_trg_points(**{**ALL_FOUR, "lnmax_cm": LNMAX_CUTOFF - 0.001})
    assert big["points"]["lnmax"] == 7, "the cut-off value itself must score"
    assert small["points"]["lnmax"] == 0
    assert big["score"] > small["score"]


def test_well_differentiation_scores_and_moderate_is_refused():
    assert xu_trg_points(**ALL_FOUR)["points"]["differentiation"] == 7
    assert xu_trg_points(**{**ALL_FOUR, "differentiation": "poor"})[
        "points"]["differentiation"] == 0
    with pytest.raises(ValueError, match="no intermediate level"):
        xu_trg_points(**{**ALL_FOUR, "differentiation": "moderate"})


def test_higher_score_is_the_group_the_paper_calls_more_likely():
    hi = xu_gastric_trg_score_predict(**ALL_FOUR)
    lo = xu_gastric_trg_score_predict(**NONE)
    assert hi["group"] == "high_likelihood"
    assert lo["group"] == "low_likelihood"
    assert hi["observed_trg0_rate_in_derivation"] == 0.2235
    assert lo["observed_trg0_rate_in_derivation"] == 0.0
    assert OBSERVED_TRG0_RATE["high_likelihood"] > OBSERVED_TRG0_RATE["low_likelihood"]


def test_it_never_returns_a_probability():
    """The paper publishes no points-to-probability mapping, so we must not
    appear to have one. `risk` is the key every other model in this library
    uses for a probability; this model must not carry it."""
    out = xu_gastric_trg_score_predict(**ALL_FOUR)
    assert "risk" not in out
    assert "score" in out


def test_the_zero_percent_group_says_it_is_zero_events():
    """0/N is not a probability of zero, and the output has to say so."""
    out = xu_gastric_trg_score_predict(**NONE)
    assert out["observed_trg0_rate_in_derivation"] == 0.0
    assert "0 events" in out["notes"]


def test_table_3_odds_ratios_match_their_betas():
    """Cheap check that the provenance block was transcribed, not invented."""
    from math import exp
    for name, row in TABLE3_COEFFICIENTS.items():
        assert exp(row["beta"]) == pytest.approx(row["odds_ratio"], rel=2e-3), name
        lo, hi = row["ci"]
        assert lo < row["odds_ratio"] < hi, name


def test_the_points_are_re_derivable_from_the_odds_ratios():
    """The paper never states how ORs became points. It is recoverable.

    Same trick as the Kunzmann divisor: each published point p constrains a
    divisor d by p - 0.5 <= or/d < p + 0.5, and intersecting the four
    constraints leaves a narrow non-empty band. The natural anchor, the
    smallest OR over its own points, lies inside it and reproduces all four.

    This test exists because the module docstring originally claimed the
    opposite. It is the check that caught it.
    """
    intervals = [
        (TABLE3_COEFFICIENTS[name]["odds_ratio"] / (pts + 0.5),
         TABLE3_COEFFICIENTS[name]["odds_ratio"] / (pts - 0.5))
        for name, pts in POINTS.items()
    ]
    lower = max(lo for lo, _ in intervals)
    upper = min(hi for _, hi in intervals)
    assert lower < upper, "no consistent divisor, the docstring needs correcting"
    assert (round(lower, 4), round(upper, 4)) == (1.0593, 1.1425)

    anchor = TABLE3_COEFFICIENTS["ca72_4"]["odds_ratio"] / POINTS["ca72_4"]
    assert lower < anchor <= upper, "the smallest-OR anchor should sit in the band"
    for name, pts in POINTS.items():
        odds = TABLE3_COEFFICIENTS[name]["odds_ratio"]
        assert round(odds / anchor) == pts, name
