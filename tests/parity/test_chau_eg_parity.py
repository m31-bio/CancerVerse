"""Parity: our Chau index against what the paper printed.

Why this test has no fixture file and no reference script
----------------------------------------------------------
There is nothing to run and nothing to re-derive. The published model is a
count of four binary factors, the paper states outright that it declined to
weight them, so parity here means one thing: does every constant transcribed
into the module still equal the digits in the article?

The article is CLOSED ACCESS (OpenAlex `oa_status: closed`, Europe PMC
`isOpenAccess: N`, no repository copy anywhere), so there is no URL a future
reader can open to re-check these, and no mirror to regenerate a fixture from.
The article was read on 2026-08-17 with
`pdftotext -layout`. That makes this file the durable record of what that PDF
said: every number below is pinned at zero tolerance with its table named, so a
later edit to the module fails here rather than silently drifting from a source
nobody can re-open.

Three groups of constants, and they come from three different places in the
article, which is worth keeping straight:

  Table 3   the four hazard ratios with 99% CIs, the SURVIVAL model
  Table 4   a different logistic model for TUMOUR RESPONSE, in which liver
            metastases is not significant at all
  Results   the risk-group Ns, median OS and one-year survival, which are in
            running prose rather than in any table

The Table 3 / Table 4 split is the substantive finding this test protects. A
reader who assumes the paper fits one model to two outcomes would get liver
metastases wrong, and the module would look correct while being wrong about
which factors predict what.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.esophageal.response.chau_eg import (
    ALP_CUTOFF_U_L,
    BANDS,
    COHORT,
    PERFORMANCE_STATUS_CUTOFF,
    RISK_GROUP_OUTCOMES,
    TABLE_3_HAZARD_RATIOS,
    TABLE_4_RESPONSE_FACTORS,
    chau_eg_predict,
    chau_eg_risk_factors,
)

# ---------------------------------------------------------------------------
# Table 3: "Multivariate Baseline Prognostic Model" (n = 817)
# ---------------------------------------------------------------------------

TABLE_3 = [
    ("performance_status", 1.575, (1.251, 1.981), "<.0001"),
    ("liver_metastases", 1.409, (1.139, 1.743), "<.0001"),
    ("peritoneal_metastases", 1.329, (1.013, 1.743), ".007"),
    ("alkaline_phosphatase", 1.412, (1.136, 1.755), "<.0001"),
]


@pytest.mark.parametrize("name,hr,ci,p", TABLE_3)
def test_every_table_3_hazard_ratio_matches_exactly(name, hr, ci, p):
    row = TABLE_3_HAZARD_RATIOS[name]
    assert row["hazard_ratio"] == hr
    assert row["ci99"] == ci
    assert row["p"] == p


def test_table_3_has_exactly_the_four_factors_in_the_published_model():
    """Three more factors were tested and reported as borderline, haemoglobin
    <= 11 g/L (P = .011), white blood cell (P = .06) and previous
    esophagectomy or gastrectomy (P = .054). None entered the model, and none
    may appear here."""
    assert set(TABLE_3_HAZARD_RATIOS) == {
        "performance_status", "liver_metastases",
        "peritoneal_metastases", "alkaline_phosphatase",
    }


def test_the_table_is_stored_not_the_abstracts_rounded_values():
    """The abstract prints 1.58 / 1.41 / 1.33 / 1.41 and Table 3 prints three
    decimals. Whoever quotes the abstract is quoting rounded numbers; the
    module stores the table. Pinned because "correcting" 1.575 to 1.58 to match
    the abstract would look like a tidy-up and would lose real precision.
    """
    assert TABLE_3_HAZARD_RATIOS["performance_status"]["hazard_ratio"] == 1.575
    assert TABLE_3_HAZARD_RATIOS["performance_status"]["hazard_ratio"] != 1.58
    assert TABLE_3_HAZARD_RATIOS["peritoneal_metastases"]["hazard_ratio"] == 1.329
    assert TABLE_3_HAZARD_RATIOS["peritoneal_metastases"]["hazard_ratio"] != 1.33


# ---------------------------------------------------------------------------
# Table 4: "Multivariate Logistic Regression Model for Tumor Response"
# A DIFFERENT model. This is the part most likely to be read wrong.
# ---------------------------------------------------------------------------

TABLE_4 = [
    ("performance_status", 0.469, (0.280, 0.787), "<.001"),
    ("peritoneal_metastases", 0.475, (0.254, 0.889), ".002"),
    ("alkaline_phosphatase", 0.655, (0.433, 0.992), ".009"),
]


@pytest.mark.parametrize("name,rr,ci,p", TABLE_4)
def test_every_significant_table_4_risk_ratio_matches_exactly(name, rr, ci, p):
    row = TABLE_4_RESPONSE_FACTORS[name]
    assert row["risk_ratio"] == rr
    assert row["ci99"] == ci
    assert row["p"] == p


def test_liver_metastases_does_not_predict_tumour_response():
    """The finding this module exists to keep straight. Liver metastasis is one
    of the four SURVIVAL factors (HR 1.409, P < .0001) and is not significant
    for RESPONSE at all (P = .558). Same paper, same cohort, two models."""
    assert TABLE_3_HAZARD_RATIOS["liver_metastases"]["p"] == "<.0001"
    assert TABLE_4_RESPONSE_FACTORS["liver_metastases"]["p"] == ".558"
    assert TABLE_4_RESPONSE_FACTORS["liver_metastases"]["risk_ratio"] is None


def test_haemoglobin_is_recorded_as_non_significant_for_response():
    assert TABLE_4_RESPONSE_FACTORS["haemoglobin_11"]["p"] == ".512"
    assert TABLE_4_RESPONSE_FACTORS["haemoglobin_11"]["risk_ratio"] is None


def test_no_response_probability_is_exposed_anywhere():
    """Table 4 has no intercept and the paper prints no response rate per risk
    band, checked across the full text. So a response probability is not
    recoverable, and the module must not appear to offer one.
    """
    out = chau_eg_predict(performance_status=0, liver_metastases=False,
                          peritoneal_metastases=False,
                          alkaline_phosphatase_u_l=50)
    assert out["risk"] is None
    assert not any("response_p" in k or "p_response" in k for k in out)
    assert "no response probability is available" in out["interpretation"]


# ---------------------------------------------------------------------------
# Risk groups, from the Results text, not from a table.
# ---------------------------------------------------------------------------

RESULTS_TEXT = [
    # (band, n, median OS months, 1-yr survival %, 1-yr 95% CI, HR vs good)
    (0, 239, 11.8, 48.5, (41.9, 54.7), 1.0),
    (1, 487, 7.4, 25.7, (22.5, 29.7), 1.92),
    (2, 91, 4.1, 11.0, (5.6, 18.4), 3.59),
]


@pytest.mark.parametrize("band,n,median,one_yr,ci,hr", RESULTS_TEXT)
def test_every_risk_group_figure_matches_the_results_text(band, n, median, one_yr, ci, hr):
    row = RISK_GROUP_OUTCOMES[band]
    assert row["n"] == n
    assert row["median_os_months"] == median
    assert row["one_year_survival_pct"] == one_yr
    assert row["one_year_ci95"] == ci
    assert row["hazard_ratio_vs_good"] == hr


def test_the_risk_group_totals_are_817_not_1080():
    """The index was fitted on the 817 patients with complete data on all four
    factors, not on the full 1,080, alkaline phosphatase was present for only
    823. Worth pinning because 1,080 is the number in the abstract and the one
    a reader will expect these three groups to sum to.
    """
    assert sum(r["n"] for r in RISK_GROUP_OUTCOMES) == 817 == COHORT["n_in_model"]
    assert COHORT["n_total"] == 1080
    assert COHORT["n_deaths"] == 979


def test_the_hazard_ratio_confidence_intervals_are_the_published_ones():
    assert RISK_GROUP_OUTCOMES[1]["hr_ci99"] == (1.53, 2.40)
    assert RISK_GROUP_OUTCOMES[2]["hr_ci99"] == (2.57, 5.02)


def test_whole_cohort_survival_matches_the_results_text():
    assert COHORT["median_os_months"] == 7.9
    assert COHORT["one_year_survival_pct"] == 30.1
    assert COHORT["one_year_ci95"] == (27.8, 32.9)
    assert COHORT["two_year_survival_pct"] == 11.5
    assert COHORT["two_year_ci95"] == (9.6, 13.5)


def test_survival_falls_monotonically_across_the_bands():
    med = [r["median_os_months"] for r in RISK_GROUP_OUTCOMES]
    one = [r["one_year_survival_pct"] for r in RISK_GROUP_OUTCOMES]
    assert med == sorted(med, reverse=True)
    assert one == sorted(one, reverse=True)
    # The paper's own summary of the spread, quoted: "a difference of 7.7
    # months in median survival and 37.5% in 1-year survival between the good
    # and the bad risk groups."
    assert round(med[0] - med[2], 1) == 7.7
    assert round(one[0] - one[2], 1) == 37.5


# ---------------------------------------------------------------------------
# Site of primary, the numbers that justify an esophageal cell at all.
# ---------------------------------------------------------------------------

def test_the_cohort_is_half_esophageal_or_junctional():
    """The check that decides this entry belongs in an esophageal cell. The
    contrast is AGAMENON (Br J Cancer 2017), which also says "oesophagogastric"
    and is 5.8% esophagus against 83.9% stomach, a label is not evidence about
    a cohort, the site table is.
    """
    assert COHORT["site_esophagus"] == 295
    assert COHORT["site_egj"] == 248
    assert COHORT["site_stomach"] == 512
    assert COHORT["site_unknown"] == 25
    total = (COHORT["site_esophagus"] + COHORT["site_egj"]
             + COHORT["site_stomach"] + COHORT["site_unknown"])
    assert total == COHORT["n_total"] == 1080
    eg = COHORT["site_esophagus"] + COHORT["site_egj"]
    assert eg == 543
    assert round(100 * eg / total, 1) == 50.3


def test_the_cohort_is_adenocarcinoma_not_squamous():
    """4.6% squamous. The single most important scope limit on this model, and
    the reason it must not be run on ESCC."""
    assert COHORT["histology_adenocarcinoma"] == 950
    assert COHORT["histology_squamous"] == 50
    assert round(100 * 50 / 1080, 1) == 4.6


# ---------------------------------------------------------------------------
# Cut-points, as published.
# ---------------------------------------------------------------------------

def test_the_published_cut_points():
    assert PERFORMANCE_STATUS_CUTOFF == 2
    assert ALP_CUTOFF_U_L == 100.0
    at = chau_eg_risk_factors(performance_status=2, liver_metastases=False,
                              peritoneal_metastases=False,
                              alkaline_phosphatase_u_l=100.0)
    below = chau_eg_risk_factors(performance_status=1, liver_metastases=False,
                                 peritoneal_metastases=False,
                                 alkaline_phosphatase_u_l=99.9)
    assert at["factors"]["performance_status"] is True
    assert at["factors"]["alkaline_phosphatase"] is True
    assert below["factors"]["performance_status"] is False
    assert below["factors"]["alkaline_phosphatase"] is False


def test_bands_tile_zero_to_four_without_gap_or_overlap():
    assert [(b["low"], b["high"]) for b in BANDS] == [(0, 0), (1, 2), (3, 4)]
    for count in range(0, 5):
        matches = [b for b in BANDS if b["low"] <= count <= b["high"]]
        assert len(matches) == 1, f"count {count} matched {len(matches)} bands"
