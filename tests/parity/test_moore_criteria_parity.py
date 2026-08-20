"""Parity: our Moore criteria implementation vs. what the paper prints.

Why this test looks different from the coefficient-matching parity tests
--------------------------------------------------------------------------
There is nothing to re-derive here. The published model is a count of five
binary factors, the paper states outright that it declined to weight them by
their fitted odds ratios, so the parity question is not "does our arithmetic
reproduce a formula", it is "does our lookup reproduce Table 4 exactly, cell
for cell, in both cohorts, plus the independent prospective validation".

Twelve values from Table 4 (three bands x two cohorts x two response-rate
columns, plus PFS/OS) and two from Tewari et al's prospective GOG 240 endpoint
are pinned at zero tolerance, these are the exact digits the papers print,
not estimates with rounding to allow for.

Everything here is offline; the source text is quoted inline rather than
regenerated from a fixture, because there is no algorithm to re-run. Table 4
IS the model for the outcome half, transcribed once from PMC4470610 and PMC4896296.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.cervical.response.moore import (
    GOG_240_PROSPECTIVE_VALIDATION,
    TABLE_3_ODDS_RATIOS,
    TABLE_4_VALIDATION,
    moore_criteria_predict,
)

#: Reference patient with zero risk factors; each case flips exactly the
#: named factor(s) to reach the target count.
BASELINE = dict(
    black_race=False, performance_status=0, disease_site="distant",
    prior_radiosensitizer=False, months_diagnosis_to_first_recurrence=24,
)


def _with_count(n: int) -> dict:
    flips = ["black_race", "performance_status", "disease_site",
             "prior_radiosensitizer", "months_diagnosis_to_first_recurrence"]
    case = dict(BASELINE)
    for name in flips[:n]:
        if name == "black_race":
            case["black_race"] = True
        elif name == "performance_status":
            case["performance_status"] = 1
        elif name == "disease_site":
            case["disease_site"] = "pelvic"
        elif name == "prior_radiosensitizer":
            case["prior_radiosensitizer"] = True
        elif name == "months_diagnosis_to_first_recurrence":
            case["months_diagnosis_to_first_recurrence"] = 6
    return case


# ---------------------------------------------------------------------------
# Table 4, "Validation of Prognostic Model", read verbatim from PMC4470610.
# Development = GOG 110+169+179 (n=428); external = GOG 149.
# ---------------------------------------------------------------------------

TABLE_4_PAPER_VALUES = [
    # (band index, cohort, field, printed value)
    (0, "development", "estimated_response_pct", 50.6),
    (0, "development", "observed_response_pct", 47.3),
    (0, "development", "median_pfs_months", 6.34),
    (0, "development", "median_os_months", 11.10),
    (0, "external", "predicted_response_pct", 50.9),
    (0, "external", "observed_response_pct", 42.6),
    (0, "external", "median_pfs_months", 6.87),
    (0, "external", "median_os_months", 11.93),
    (1, "development", "estimated_response_pct", 29.4),
    (1, "development", "observed_response_pct", 31.4),
    (1, "development", "median_pfs_months", 4.60),
    (1, "development", "median_os_months", 9.17),
    (1, "external", "predicted_response_pct", 29.0),
    (1, "external", "observed_response_pct", 29.4),
    (1, "external", "median_pfs_months", 4.44),
    (1, "external", "median_os_months", 7.59),
    (2, "development", "estimated_response_pct", 13.0),
    (2, "development", "observed_response_pct", 9.8),
    (2, "development", "median_pfs_months", 2.79),
    (2, "development", "median_os_months", 5.49),
    (2, "external", "predicted_response_pct", 13.5),
    (2, "external", "observed_response_pct", 14.3),
    (2, "external", "median_pfs_months", 3.38),
    (2, "external", "median_os_months", 5.58),
]


@pytest.mark.parametrize(
    "band,cohort,field,printed", TABLE_4_PAPER_VALUES,
    ids=lambda v: str(v) if not isinstance(v, float) else f"{v}",
)
def test_every_table_4_cell_matches_exactly(band, cohort, field, printed):
    assert TABLE_4_VALIDATION[band][cohort][field] == printed


def test_table_4_has_all_three_bands_both_cohorts_no_more_no_less():
    assert len(TABLE_4_VALIDATION) == 3
    for row in TABLE_4_VALIDATION:
        assert set(row["development"]) == {
            "estimated_response_pct", "observed_response_pct",
            "median_pfs_months", "median_os_months",
        }
        assert set(row["external"]) == {
            "predicted_response_pct", "observed_response_pct",
            "median_pfs_months", "median_os_months",
        }


# ---------------------------------------------------------------------------
# The five Table 3 odds ratios, provenance only, never used to compute
# anything, but pinned so a future edit cannot start using them silently.
# ---------------------------------------------------------------------------

TABLE_3_PAPER_VALUES = [
    ("black_race", 0.49, (0.28, 0.83), 0.008),
    ("performance_status_above_0", 0.60, (0.38, 0.94), 0.027),
    ("pelvic_disease", 0.58, (0.38, 0.90), 0.015),
    ("prior_radiosensitizer", 0.52, (0.32, 0.85), 0.009),
    ("recurrence_within_1_year", 0.61, (0.39, 0.95), 0.027),
]


@pytest.mark.parametrize("name,odds_ratio,ci,p", TABLE_3_PAPER_VALUES)
def test_every_table_3_odds_ratio_is_transcribed_exactly(name, odds_ratio, ci, p):
    row = TABLE_3_ODDS_RATIOS[name]
    assert row["odds_ratio"] == odds_ratio
    assert row["ci"] == ci
    assert row["p"] == p


def test_table_3_odds_ratios_are_provenance_only_and_never_computed_from():
    """The paper's own words: "comparable weights and no interactions", so a
    prognostic index was built by counting factors, not fitting them. If a
    future edit starts multiplying these odds ratios into the score, this
    test's premise, and the module's docstring, would be wrong, so it is
    stated as an explicit assertion about the module's behaviour, not just
    prose: flipping any one factor changes the count by exactly 1, regardless
    of that factor's odds ratio.
    """
    from cancerverse_baseline.cervical.response.moore import moore_risk_factors

    base = moore_risk_factors(**BASELINE)["count"]
    for name in TABLE_3_ODDS_RATIOS:
        case = dict(BASELINE)
        if name == "black_race":
            case["black_race"] = True
        elif name == "performance_status_above_0":
            case["performance_status"] = 2
        elif name == "pelvic_disease":
            case["disease_site"] = "pelvic"
        elif name == "prior_radiosensitizer":
            case["prior_radiosensitizer"] = True
        elif name == "recurrence_within_1_year":
            case["months_diagnosis_to_first_recurrence"] = 3
        assert moore_risk_factors(**case)["count"] - base == 1, name


# ---------------------------------------------------------------------------
# GOG 240 prospective validation (Tewari et al, PMC4896296), the two numbers
# stated in the Results text, not the mid-band figure-only value.
# ---------------------------------------------------------------------------

def test_gog_240_low_risk_matches_the_results_text():
    """Verbatim: "patients with 0 or 1 high risk factor (i.e., low-risk
    cohort) experience 21.8 months OS and 57% RR"."""
    row = GOG_240_PROSPECTIVE_VALIDATION["low"]
    assert row["observed_response_pct"] == 57.0
    assert row["median_os_months"] == 21.8


def test_gog_240_high_risk_matches_the_results_text():
    """Verbatim: "those in the high-risk cohort (4 or 5 factors) have
    significantly worse OS of 8.2 months ... and 18.5% RR"."""
    row = GOG_240_PROSPECTIVE_VALIDATION["high"]
    assert row["observed_response_pct"] == 18.5
    assert row["median_os_months"] == 8.2


def test_gog_240_mid_risk_is_not_claimed_because_it_is_figure_only():
    """The Results text states low- and high-risk numerically and leaves
    mid-risk to Fig. 1, a graphic. Claiming a mid-risk prospective number here
    would be inventing a value the source never printed as text.
    """
    assert "mid" not in GOG_240_PROSPECTIVE_VALIDATION
    assert set(GOG_240_PROSPECTIVE_VALIDATION) == {"low", "high"}


# ---------------------------------------------------------------------------
# End to end, through the public entrypoint.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("count", [0, 1, 2, 3, 4, 5])
def test_the_predicted_band_output_matches_table_4_at_every_count(count):
    out = moore_criteria_predict(**_with_count(count))
    band = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2}[count]
    row = TABLE_4_VALIDATION[band]
    assert out["risk_factor_count"] == count
    assert out["band"] == band
    assert out["development_observed_response_pct"] == row["development"]["observed_response_pct"]
    assert out["external_observed_response_pct"] == row["external"]["observed_response_pct"]


def test_low_risk_band_carries_the_gog_240_prospective_numbers():
    out = moore_criteria_predict(**_with_count(0))
    assert out["gog240_prospective_validation"]["observed_response_pct"] == 57.0


def test_high_risk_band_carries_the_gog_240_prospective_numbers():
    out = moore_criteria_predict(**_with_count(5))
    assert out["gog240_prospective_validation"]["observed_response_pct"] == 18.5


def test_mid_risk_band_carries_no_prospective_numbers():
    out = moore_criteria_predict(**_with_count(2))
    assert out["gog240_prospective_validation"] is None
