"""Parity: Kunzmann points re-derived from the paper's own odds ratios.

Kunzmann AT, Thrift AP, Cardwell CR, et al. "Model for Identifying Individuals
at Risk for Esophageal Adenocarcinoma." Clin Gastroenterol Hepatol.
2018;16(8):1229-1236, Table 2.

No worked patient is published, and the full text is paywalled (this check was
blocked on paper access until the PDF was supplied). But the paper states how
the points were built, which makes the WHOLE model re-derivable rather than one
point of it — a stronger check than a worked example would have been:

    Methods: "Points-based models were created from the coefficient-based model
    by dividing the coefficient of each variable by the smallest coefficient in
    the model and rounding to the nearest 0.5 ... For example, the coefficient
    for men was 1.64, and the smallest coefficient in the model was 0.40 (BMI,
    25 to <30 kg/m2), so men were assigned 4 points (1.64/0.40, then rounded to
    nearest 0.5)."

So for every row: points == round_to_half(ln(OR) / d), for the divisor d the
paper says it used. All 10 reproduce — but only for one of the two values the
paper gives.

THE PAPER CONTRADICTS ITSELF ON THE DIVISOR, AND THE TABLE DECIDES IT
----------------------------------------------------------------------
The Methods worked example divides by **0.40**. The Table 2 footnote says the
smallest coefficient is **0.41**. They cannot both be right, and it is not
cosmetic — it changes a published point value:

    divisor 0.40   10/10 rows reproduce
    divisor 0.41    9/10  — "Smoking, former" comes out 1.5, published 2.0

Rather than argue from which sentence looks more authoritative, invert the
problem: each published point pins its divisor to an interval, because
round_to_half(b/d) == p requires p - 0.25 <= b/d < p + 0.25. Intersecting all
ten rows gives

    d must lie in (0.3958, 0.4046]

    Methods 0.40      INSIDE
    footnote 0.41     OUTSIDE
    ln(1.50) = 0.4055 OUTSIDE, and only just

So the Methods figure is right and the footnote is the typo. The interval also
explains where the footnote came from: 0.4055 rounds to 0.41, so whoever wrote
the footnote recomputed ln(1.50) from the printed odds ratio instead of reading
the fitted coefficient. And since the true divisor is below 0.4046, the real
BMI 25-<30 odds ratio must be about 1.492-1.499 — printed as 1.50.

Our module docstring previously repeated the footnote's 0.41; corrected.
"""

from __future__ import annotations

import math

import pytest

from cancerverse_baseline.esophageal.detection.kunzmann import (
    ESOPHAGEAL_CONDITION_POINTS,
    MAX_POINTS,
    REFERRAL_THRESHOLD,
    SEX_POINTS,
    SMALLEST_COEFFICIENT,
    SMOKING_POINTS,
    age_points,
    bmi_points,
    kunzmann_predict,
)

# Table 2, verbatim: (label, adjusted odds ratio, published points)
TABLE_2 = [
    ("Age 55-60", 1.99, 1.5),
    ("Age 60-65", 2.76, 2.5),
    ("Age 65+", 4.03, 3.5),
    ("Male", 5.16, 4.0),
    ("BMI 25-<30", 1.50, 1.0),
    ("BMI 30-<35", 1.91, 1.5),
    ("BMI 35+", 2.97, 2.5),
    ("Smoking former", 2.03, 2.0),
    ("Smoking current", 3.83, 3.5),
    ("Esophageal condition", 1.88, 1.5),
]

def _round_to_half(x: float) -> float:
    return round(x * 2) / 2


def _points_from(odds_ratio: float, divisor: float = SMALLEST_COEFFICIENT) -> float:
    """The paper's construction: coefficient / smallest coefficient, to nearest 0.5."""
    return _round_to_half(math.log(odds_ratio) / divisor)


@pytest.mark.parametrize("label,odds_ratio,published", TABLE_2,
                         ids=[r[0] for r in TABLE_2])
def test_every_published_point_is_re_derivable_from_its_odds_ratio(
    label, odds_ratio, published
):
    assert _points_from(odds_ratio) == published


def test_the_papers_own_worked_example():
    """Methods: men, coefficient 1.64, smallest 0.40 -> 4 points."""
    assert _round_to_half(1.64 / 0.40) == 4.0
    assert SEX_POINTS["male"] == 4.0
    # The stated coefficient for men agrees with the printed odds ratio.
    assert round(math.log(5.16), 2) == 1.64


def _admissible_divisor_interval():
    """Every published point constrains the divisor, because
    round_to_half(b/d) == p requires p - 0.25 <= b/d < p + 0.25."""
    lo, hi = 0.0, math.inf
    for _label, odds_ratio, published in TABLE_2:
        b = math.log(odds_ratio)
        lo = max(lo, b / (published + 0.25))
        if published > 0.25:
            hi = min(hi, b / (published - 0.25))
    return lo, hi


def test_the_table_itself_pins_the_divisor_and_excludes_the_footnote():
    """The decisive check: the ten published points jointly admit only a narrow
    band of divisors. The Methods value is inside it; the footnote's is not."""
    lo, hi = _admissible_divisor_interval()
    assert (round(lo, 4), round(hi, 4)) == (0.3958, 0.4046)
    assert lo < SMALLEST_COEFFICIENT <= hi, "the Methods divisor must be admissible"
    assert not (lo < 0.41 <= hi), "the footnote divisor must be excluded"
    # ln(1.50) is where the footnote's 0.41 plausibly came from, and it is also
    # outside — narrowly. That is the tell that it was recomputed, not read.
    assert not (lo < math.log(1.50) <= hi)


def test_the_footnote_divisor_breaks_exactly_one_row():
    """Pinned so nobody 'corrects' the module back to 0.41 — and so the cost of
    doing so is on the record."""
    failures = [
        label for label, odds_ratio, published in TABLE_2
        if _points_from(odds_ratio, divisor=0.41) != published
    ]
    assert failures == ["Smoking former"], failures


# ------------------------------------- our point table vs. Table 2 directly ---

def test_our_age_points_match_table_2():
    assert age_points(50) == 0.0
    assert age_points(54.9) == 0.0
    assert age_points(55) == 1.5
    assert age_points(60) == 2.5
    assert age_points(65) == 3.5
    assert age_points(80) == 3.5


def test_our_bmi_points_match_table_2():
    assert bmi_points(22) == 0.0
    assert bmi_points(25) == 1.0
    assert bmi_points(30) == 1.5
    assert bmi_points(35) == 2.5


def test_our_sex_and_smoking_and_condition_points_match_table_2():
    assert SEX_POINTS == {"male": 4.0, "female": 0.0}
    assert SMOKING_POINTS == {"never": 0.0, "former": 2.0, "current": 3.5}
    assert ESOPHAGEAL_CONDITION_POINTS == 1.5


def test_the_published_maximum_and_threshold():
    """Figure 2 is captioned "out of total of 15"; the referral cut is 8+."""
    assert MAX_POINTS == 15.0
    assert REFERRAL_THRESHOLD == 8.0
    worst = kunzmann_predict(age=70, male=True, bmi=40, smoking="current",
                             esophageal_condition=True)
    assert worst["score"] == MAX_POINTS
    assert worst["refer_for_screening"] is True
    best = kunzmann_predict(age=50, male=False, bmi=22, smoking="never",
                            esophageal_condition=False)
    assert best["score"] == 0.0
    assert best["refer_for_screening"] is False


def test_the_referral_threshold_is_inclusive():
    """The paper reports "8+ points" as the cutoff, so exactly 8 refers."""
    # male 4.0 + age 65+ 3.5 + esophageal condition 1.5 = 9.0; drop to exactly 8
    # via male 4.0 + age 60-65 2.5 + smoking former 2.0 - no, use 4.0+2.5+1.5 = 8.0
    out = kunzmann_predict(age=62, male=True, bmi=22, smoking="never",
                           esophageal_condition=True)
    assert out["score"] == 8.0
    assert out["refer_for_screening"] is True
