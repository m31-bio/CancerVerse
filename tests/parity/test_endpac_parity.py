"""Parity: END-PAC checked against Table 1 and the paper's own group proportions.

END-PAC publishes no worked example, and its only public calculator
(endpacscore.com) no longer resolves. Two routes remained, and both were used
on the primary source itself (Sharma A, Kandlakunta H, Nagpal SJS, et al.
Gastroenterology. 2018;155(3):730-739.e3, NIH author manuscript):

  Route 4  — reproduce the published table. Every cell of Table 1 ("END-PDAC
             score parameters") is asserted below against our point functions,
             including the three stated sub-score RANGES.

  Route 5  — re-derive the paper's own statistics. This is what caught a real
             defect. The paper states its three risk groups in two mutually
             exclusive ways:

                 abstract   "An END-PAC score <0 (in 49% of subjects) meant
                             that patients had an extremely low-risk"
                 results    "Fifteen PC-NODs subjects (21%) had an END-PAC
                             score of 1 or 2 ... Two PC-NODs subjects (2%) had
                             an END-PAC score <=0 to 632 T2-NOD subjects (49%)"

             Same 49%, different inequality. The group proportions decide it:
             they sum to exactly 100% in both cohorts, which is only possible
             if the partition is {>=3, 1..2, <=0}. Under the abstract's "<0" a
             score of exactly 0 belongs to no group at all.

                 T2-NOD   19% + 32% + 49% = 100%
                 PC-NOD   77% + 21% +  2% = 100%

             This module implemented the abstract's "<0", so a score of exactly
             0 was reported as intermediate rather than extremely low risk —
             the boundary between "reassure" and "needs follow-up". Fixed.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.pancreatic.detection.endpac import (
    GLUCOSE_SCORE_RANGE,
    HIGH_RISK_THRESHOLD,
    INTERMEDIATE_SCORES,
    LOW_RISK_AT_OR_BELOW,
    age_score,
    bg_category,
    endpac_predict,
    weight_score,
)

# ---------------------------------------------------------------- Table 1 ---

# "Blood Glucose (BG) Categories" — representative mg/dL value -> printed score
TABLE1_BG = [
    (60, 1), (99, 1),            # <100
    (100, 2), (109, 2),          # 100-109
    (110, 3), (125, 3),          # 110-125
    (126, 4), (160, 4),          # 126-160
    (161, 5), (400, 5),          # >160
]

# "Delta Weight Categories" — kg change -> printed score. LOSS is positive.
TABLE1_WEIGHT = [
    (-10.0, 6), (-6.0, 6),       # <= -6.0
    (-5.9, 4), (-4.0, 4),        # -5.9 to -4.0
    (-3.9, 2), (-2.0, 2),        # -3.9 to -2.0
    (-1.9, 0), (0.0, 0), (1.9, 0),   # -1.9 to +1.9
    (2.0, -2), (3.9, -2),        # +2.0 to +3.9
    (4.0, -4), (5.9, -4),        # +4.0 to +5.9
    (6.0, -6), (12.0, -6),       # >= +6.0
]

# "Age (years) at glycemically-defined new-onset diabetes"
TABLE1_AGE = [(40, -1), (59, -1), (60, 0), (69, 0), (70, 1), (90, 1)]


@pytest.mark.parametrize("mg_dl,expected", TABLE1_BG)
def test_table1_blood_glucose_categories(mg_dl, expected):
    assert bg_category(mg_dl) == expected


@pytest.mark.parametrize("kg,expected", TABLE1_WEIGHT)
def test_table1_weight_categories(kg, expected):
    assert weight_score(kg) == expected


@pytest.mark.parametrize("age,expected", TABLE1_AGE)
def test_table1_age_categories(age, expected):
    assert age_score(age) == expected


def test_table1_printed_subscore_ranges():
    """Table 1 prints a "Score Range" column for each block. Reproduce all three."""
    assert GLUCOSE_SCORE_RANGE == (1, 4)                       # printed "1-4"
    weights = [weight_score(k) for k, _ in TABLE1_WEIGHT]
    assert (min(weights), max(weights)) == (-6, 6)             # printed "-6 to +6"
    ages = [age_score(a) for a, _ in TABLE1_AGE]
    assert (min(ages), max(ages)) == (-1, 1)                   # printed "-1 to +1"


# ------------------------------------------------- the banding, via route 5 ---

# The paper's own group proportions, quoted from the Results.
PUBLISHED_GROUP_PROPORTIONS = {
    "T2-NOD": {"high": 19, "intermediate": 32, "very_low": 49},
    "PC-NOD": {"high": 77, "intermediate": 21, "very_low": 2},
}


@pytest.mark.parametrize("cohort", list(PUBLISHED_GROUP_PROPORTIONS))
def test_the_published_group_proportions_sum_to_one_hundred(cohort):
    """The arithmetic that proves the partition. If the three quoted groups did
    not exhaust the score line, these could not sum to 100%."""
    assert sum(PUBLISHED_GROUP_PROPORTIONS[cohort].values()) == 100


def test_the_three_groups_partition_the_whole_score_line():
    """Every attainable total lands in exactly one group, with no gap. This is
    the property the abstract's "<0" breaks."""
    from cancerverse_baseline.pancreatic.detection.endpac import TOTAL_SCORE_RANGE

    lo, hi = TOTAL_SCORE_RANGE
    for total in range(lo, hi + 1):
        in_high = total >= HIGH_RISK_THRESHOLD
        in_mid = total in INTERMEDIATE_SCORES
        in_low = total <= LOW_RISK_AT_OR_BELOW
        assert sum((in_high, in_mid, in_low)) == 1, f"score {total} is not in exactly one group"


def test_score_of_exactly_zero_is_extremely_low_risk_not_intermediate():
    """The regression. The paper's intermediate group is quoted as "1 or 2",
    so 0 belongs with the low-risk group. We previously reported it as
    intermediate, following a typo in the abstract."""
    # glucose 1 (category 3 -> 4), weight 0, age -1  ->  total 0
    out = endpac_predict(
        glucose_at_diabetes_mg_dl=130,          # category 4
        glucose_one_year_before_mg_dl=120,      # category 3  -> A = 1
        weight_change_kg=0.0,                   # B = 0
        age_at_diabetes_onset=55,               # C = -1
    )
    assert out["score"] == 0
    assert out["risk_band"] == "very_low"


def test_the_bands_either_side_of_zero():
    common = dict(glucose_at_diabetes_mg_dl=130, glucose_one_year_before_mg_dl=120,
                  age_at_diabetes_onset=55)
    # A=1, C=-1, so total = B
    assert endpac_predict(**common, weight_change_kg=+3.0)["risk_band"] == "very_low"      # -2
    assert endpac_predict(**common, weight_change_kg=0.0)["risk_band"] == "very_low"       #  0
    assert endpac_predict(**common, weight_change_kg=-2.0)["risk_band"] == "intermediate"  # +2
    assert endpac_predict(**common, weight_change_kg=-4.0)["risk_band"] == "high"          # +4


def test_intermediate_is_exactly_one_and_two():
    assert INTERMEDIATE_SCORES == (1, 2)
    assert HIGH_RISK_THRESHOLD == 3
    assert LOW_RISK_AT_OR_BELOW == 0
