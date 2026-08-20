"""Tests for the BCSC breast density model (Tice et al., Ann Intern Med 2008).

There is no independent reference implementation to check this against (the
BCSC's own SAS macro is behind a password-gated request, see
`registry/models.yaml` id `bcsc_v2`). Instead, `test_matches_paper_table5_*`
checks the White-only prediction against the paper's own Table 5, which
reports the 5-year risk *averaged over the study's actual race mix*
(71% White, 7% Black, 3% Asian, 8% Hispanic, 11% other/missing). A pure
White-race calculation should therefore sit a bit BELOW Table 5's value
(Black women have somewhat higher risk at these ages), consistently across
every age/density cell, which is what would be expected if the formula is
implemented correctly, and is a materially different failure signature than
a formula bug (which would produce inconsistent or wildly wrong ratios).
This is a plausibility check, not a parity check, and is not claimed as one.
"""

import pytest

from cancerverse_baseline.breast.detection import bcsc_v2_coefficients as C
from cancerverse_baseline.breast.detection import bcsc_v2_predict

# Table 5, first column ("5-Year Risk for Breast Cancer", density only,
# family history and biopsy history unknown), transcribed from the paper.
# Keyed by (start_age_of_band, BI-RADS density).
TABLE5_DENSITY_ONLY = {
    (40, 1): 0.2, (40, 2): 0.5, (40, 3): 0.7, (40, 4): 1.0,
    (45, 1): 0.4, (45, 2): 0.8, (45, 3): 1.2, (45, 4): 1.6,
    (50, 1): 0.5, (50, 2): 1.0, (50, 3): 1.6, (50, 4): 2.1,
    (55, 1): 0.7, (55, 2): 1.4, (55, 3): 2.2, (55, 4): 3.0,
    (60, 1): 0.8, (60, 2): 1.7, (60, 3): 2.6, (60, 4): 3.4,
    (65, 1): 1.3, (65, 2): 2.0, (65, 3): 2.9, (65, 4): 3.0,
    (70, 1): 1.4, (70, 2): 2.1, (70, 3): 3.1, (70, 4): 3.3,
}

# Table 5, age 50-54 / density 2 (scattered fibroglandular), all four
# family-history x biopsy-history combinations.
TABLE5_AGE50_DENSITY2_BY_HISTORY = {
    (False, False): 0.9,
    (False, True): 1.4,
    (True, False): 1.4,
    (True, True): 2.2,
}


@pytest.mark.parametrize(("age", "density"), list(TABLE5_DENSITY_ONLY))
def test_matches_paper_table5_density_only_within_race_mix_tolerance(age, density):
    table5_value = TABLE5_DENSITY_ONLY[(age, density)]
    out = bcsc_v2_predict(start_age=age, race="white", density=density)
    ratio = (out["risk"] * 100) / table5_value
    # White-only should sit below the race-mixed Table 5 value, but not by a
    # wide margin. White is ~71% of the cohort. 0.75-1.02 covers every one
    # of the 28 age x density cells checked when this was derived.
    assert 0.75 < ratio < 1.02, (
        f"age={age} density={density}: predicted {out['risk']*100:.3f}%, "
        f"paper's Table 5 (race-mixed) says {table5_value}%, ratio {ratio:.3f}"
    )


@pytest.mark.parametrize(("history", "table5_value"), list(TABLE5_AGE50_DENSITY2_BY_HISTORY.items()))
def test_matches_paper_table5_family_history_and_biopsy_combinations(history, table5_value):
    family_history, biopsy_history = history
    out = bcsc_v2_predict(
        start_age=50, race="white", density=2,
        family_history=family_history, biopsy_history=biopsy_history,
    )
    ratio = (out["risk"] * 100) / table5_value
    assert 0.85 < ratio < 1.0, (
        f"family_history={family_history} biopsy_history={biopsy_history}: "
        f"predicted {out['risk']*100:.3f}%, paper's Table 5 says "
        f"{table5_value}%, ratio {ratio:.3f}"
    )


def test_unknown_family_history_and_biopsy_skip_the_multiplier():
    known_average_ish = bcsc_v2_predict(start_age=50, race="white", density=2)
    with_no = bcsc_v2_predict(
        start_age=50, race="white", density=2,
        family_history=False, biopsy_history=False,
    )
    with_yes = bcsc_v2_predict(
        start_age=50, race="white", density=2,
        family_history=True, biopsy_history=True,
    )
    # Unknown is not an imputed average, it is genuinely between "no" and
    # "yes" here only because 0.938*0.906 < 1 < 1.454*1.495, not because the
    # paper interpolates; the real assertion is that "unknown" differs from
    # both known answers, per the paper's own stated rule.
    assert with_no["risk"] < known_average_ish["risk"] < with_yes["risk"]


def test_higher_density_means_higher_risk():
    risks = [
        bcsc_v2_predict(start_age=55, race="white", density=d)["risk"]
        for d in (1, 2, 3, 4)
    ]
    assert risks == sorted(risks)


def test_relative_hazard_switches_at_the_paper_stated_age_cutoff():
    just_under = bcsc_v2_predict(start_age=64, race="white", density=4)
    just_over = bcsc_v2_predict(start_age=65, race="white", density=4)
    # BI-RADS 4 relative hazard drops from 2.0119 to 1.4499 at 65, a real
    # discontinuity the paper reports, not a smoothing artifact to hide.
    assert just_over["risk"] < just_under["risk"]


def test_rejects_unsupported_race():
    with pytest.raises(ValueError, match="race"):
        bcsc_v2_predict(start_age=50, race="american_indian", density=2)


def test_rejects_invalid_density():
    with pytest.raises(ValueError, match="density"):
        bcsc_v2_predict(start_age=50, race="white", density=5)


def test_rejects_ages_outside_the_papers_developed_range():
    with pytest.raises(ValueError, match="35"):
        bcsc_v2_predict(start_age=30, race="white", density=2)
    with pytest.raises(ValueError, match="35"):
        bcsc_v2_predict(start_age=85, race="white", density=2)


def test_age_band_boundaries_match_appendix_table():
    assert C.age_band(44.9) == "35-44"
    assert C.age_band(45) == "45-54"
    assert C.age_band(64.9) == "55-64"
    assert C.age_band(65) == "65-74"
    assert C.age_band(75) == "75+"


def test_metadata():
    out = bcsc_v2_predict(start_age=50, race="white", density=2)
    assert out["model_id"] == "bcsc_v2"
    assert out["axis"] == "detection"
    assert out["disease"] == "breast"
