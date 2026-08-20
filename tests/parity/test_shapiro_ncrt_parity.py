"""Parity: our Shapiro nomogram against Fig. 1 and the paper's worked example.

Why there is no fixture and no reference script
------------------------------------------------
Nothing to run: the model is three integer point scales and a printed lookup.
The article is closed access with no PMC record, so there is no URL a later
reader can open and no mirror to regenerate anything from, which makes this
file the durable record of what the article said. Every constant is
pinned at zero tolerance with its locus named.

Fig. 1 is a FIGURE, so the numbers were read twice by the rule this project
uses for image-only sources (see msk_rectal): once from `pdftotext -layout`
and once from PNG renders of page 1043 at 300 and 600 dpi. Both readings
agree.

The load-bearing test is `test_the_papers_own_worked_example`. It is the only
end-to-end check the article supplies, and it exercises the exact thing a
transcription error would break, a patient, through the points, to a printed
survival pair.
"""

from __future__ import annotations

import math

import pytest

from cancerverse_baseline.esophageal.prognosis.shapiro_ncrt import (
    COHORT,
    DISCRIMINATION,
    MAX_POINTS,
    POINTS,
    SCORES_WITHOUT_SURVIVAL,
    SURVIVAL_BY_POINTS,
    shapiro_ncrt_predict,
)

# ---------------------------------------------------------------------------
# Fig. 1, the three predictor scales.
# ---------------------------------------------------------------------------

FIG1_POINTS = [
    ("cn", "cN0", 0), ("cn", "cN1", 2),
    ("ypt", "ypT0", 0), ("ypt", "ypT1", 2), ("ypt", "ypT2", 2), ("ypt", "ypT3", 4),
    ("ypn", "ypN0", 0), ("ypn", "ypN1", 4), ("ypn", "ypN2", 5), ("ypn", "ypN3", 10),
]


@pytest.mark.parametrize("kind,level,pts", FIG1_POINTS)
def test_every_point_value_matches_figure_1(kind, level, pts):
    assert POINTS[kind][level] == pts


def test_ypt1_and_ypt2_share_a_point_value():
    """The figure's middle ypT tick is labelled "ypT1/pT2" over a single mark,
    one point value for two categories. Easy to miss, and splitting them
    would invent a distinction the model does not make."""
    assert POINTS["ypt"]["ypT1"] == POINTS["ypt"]["ypT2"] == 2


def test_the_worst_patient_scores_sixteen():
    assert sum(max(v.values()) for v in POINTS.values()) == MAX_POINTS == 16


# ---------------------------------------------------------------------------
# Fig. 1, the survival axes.
# ---------------------------------------------------------------------------

FIG1_AXIS = [
    (0, 91.0, 70.0), (2, 88.0, 62.0), (4, 85.0, 53.0), (6, 81.0, 43.0),
    (8, 75.0, 33.0), (10, 68.0, 23.0), (12, 60.0, 14.0), (14, 51.0, 7.0),
    (16, 41.0, 3.0),
]


@pytest.mark.parametrize("pts,one_yr,five_yr", FIG1_AXIS)
def test_every_survival_tick_matches_figure_1(pts, one_yr, five_yr):
    row = SURVIVAL_BY_POINTS[pts]
    assert row["one_year_pct"] == one_yr
    assert row["five_year_pct"] == five_yr


def test_the_axis_labels_only_even_totals():
    assert sorted(SURVIVAL_BY_POINTS) == [0, 2, 4, 6, 8, 10, 12, 14, 16]


def test_survival_falls_monotonically_with_points():
    pts = sorted(SURVIVAL_BY_POINTS)
    for key in ("one_year_pct", "five_year_pct"):
        vals = [SURVIVAL_BY_POINTS[p][key] for p in pts]
        assert vals == sorted(vals, reverse=True), key


# ---------------------------------------------------------------------------
# The paper's own worked example, the only end-to-end check it supplies.
# ---------------------------------------------------------------------------

def test_the_papers_own_worked_example():
    """Verbatim: "patients with pretreatment suspicion of nodal disease (cN1)
    and a complete response in the resection specimen (ypT0, ypN0) would have
    a total of 2 points, corresponding to estimated 1- and 5-year survival
    rates of 88 and 62 per cent respectively"."""
    out = shapiro_ncrt_predict(cn_category="cN1", ypt_category="ypT0",
                               ypn_category="ypN0")
    assert out["total_points"] == 2
    assert out["one_year_survival_pct"] == 88.0
    assert out["five_year_survival_pct"] == 62.0


# ---------------------------------------------------------------------------
# The four reachable totals with no published survival.
# ---------------------------------------------------------------------------

def test_the_reachable_totals_are_thirteen_and_four_are_unlabelled():
    reachable = sorted({a + b + c
                        for a in POINTS["cn"].values()
                        for b in POINTS["ypt"].values()
                        for c in POINTS["ypn"].values()})
    assert reachable == [0, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16]
    missing = [t for t in reachable if t not in SURVIVAL_BY_POINTS]
    assert missing == list(SCORES_WITHOUT_SURVIVAL) == [5, 7, 9, 11]


def test_every_unlabelled_total_comes_from_ypN2():
    """ypN2 = 5 is the model's only odd point value, so it is the sole cause.
    That is why the hole is not a rounding curiosity: it is exactly the
    3-6-positive-node patients, 60 of 626 in the derivation cohort."""
    for a in POINTS["cn"].values():
        for b in POINTS["ypt"].values():
            for c_name, c in POINTS["ypn"].items():
                total = a + b + c
                if total in SCORES_WITHOUT_SURVIVAL:
                    assert c_name == "ypN2", (total, c_name)


@pytest.mark.parametrize("total", SCORES_WITHOUT_SURVIVAL)
def test_no_survival_is_invented_for_an_unlabelled_total(total):
    """The whole point. A fitted Cox curve reproduces the printed axis to 0.36
    percentage points, so filling these four in would be easy and would look
    authoritative. It would also be this project generating numbers rather
    than reading them, which is the one thing the repository does not do.
    """
    # construct a patient with this exact total: ypN2 plus an even remainder
    remainder = total - POINTS["ypn"]["ypN2"]
    cn = "cN1" if remainder >= 2 else "cN0"
    rest = remainder - POINTS["cn"][cn]
    ypt = {0: "ypT0", 2: "ypT1", 4: "ypT3"}[rest]
    out = shapiro_ncrt_predict(cn_category=cn, ypt_category=ypt,
                               ypn_category="ypN2")
    assert out["total_points"] == total
    assert out["survival_available"] is False
    assert out["one_year_survival_pct"] is None
    assert out["five_year_survival_pct"] is None
    assert "NO PUBLISHED SURVIVAL" in out["notes"]


def test_the_cox_fit_that_is_deliberately_not_used():
    """Recorded, not applied. S(p) = S0^exp(k*p) with S0 = 0.91 and 0.70 and a
    shared k near 0.1411 reproduces all eighteen printed values closely, which     is what makes the refusal above a choice rather than an inability.

    It also exposes an inconsistency in the source worth knowing about: the
    Methods say the points are the Cox coefficients "multiplied by ten", which
    implies k = 0.1, and the axis behaves like k = 0.141. The final model's
    coefficients are printed nowhere, so this cannot be resolved from the
    article, and nothing in the module depends on resolving it.
    """
    k = 0.1411
    worst = 0.0
    for pts, one_yr, five_yr in FIG1_AXIS:
        for s0, published in ((0.91, one_yr), (0.70, five_yr)):
            pred = 100 * s0 ** math.exp(k * pts)
            worst = max(worst, abs(pred - published))
    assert worst < 1.0, f"worst deviation {worst:.2f} pp"
    assert abs(k - 0.1) > 0.03, "the fitted scale is not the Methods' 1/10"


# ---------------------------------------------------------------------------
# Cohort and performance, as published.
# ---------------------------------------------------------------------------

def test_the_cohort_counts_match_table_1():
    assert COHORT["n"] == 626 and COHORT["n_screened"] == 661
    assert COHORT["adenocarcinoma"] == 481 and COHORT["squamous"] == 139
    assert COHORT["cN0"] + COHORT["cN1"] == 612          # 14 not stated
    assert COHORT["ypT0"] + COHORT["ypT1"] + COHORT["ypT2"] + COHORT["ypT3"] == 622
    assert COHORT["ypN0"] + COHORT["ypN1"] + COHORT["ypN2"] + COHORT["ypN3"] == 626


def test_squamous_histology_is_well_represented_unlike_chau_eg():
    """22.2% here against 4.6% in chau_eg. The two esophageal models have
    genuinely different applicability by histology, and a reader carrying the
    chau_eg caveat across to this one would be wrong."""
    assert round(100 * COHORT["squamous"] / COHORT["n"], 1) == 22.2


def test_the_ypN2_share_that_makes_the_gap_matter():
    assert COHORT["ypN2"] == 60
    assert round(100 * COHORT["ypN2"] / COHORT["n"], 1) == 9.6


def test_discrimination_is_recorded_as_weak_and_externally_validated():
    assert DISCRIMINATION["internal_c_index"] == 0.63
    assert DISCRIMINATION["cross_validation_c_index"] == (0.62, 0.63)
    assert DISCRIMINATION["external_c_index_os"] == 0.61
    assert DISCRIMINATION["external_c_index_pfs"] == 0.64
    assert DISCRIMINATION["external_n"] == 975
    assert DISCRIMINATION["external_centres"] == 3
