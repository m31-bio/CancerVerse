"""Parity against the canonical R reference implementations.

The expected values below were produced by the scripts in
`tests/parity/reference/`, run against R 4.6.1 with CRAN `BCRA` and
`WintonCentre/predictv30r` on 2026-08-05. They are pinned here so the check
runs in CI without an R toolchain; re-run those scripts to refresh them.

Full narrative of how these were obtained — including two defects the
comparison exposed — is in `docs/VERIFICATION.md`.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.breast.detection import bcrat_predict
from cancerverse_baseline.breast.prognosis import predict_breast

# Percentage points. R prints 6 dp; we match far tighter than that.
TOL = 1e-5


# --- BCRAT vs CRAN `BCRA::absolute.risk()` -----------------------------------

BCRA_CASES = [
    (dict(start_age=50, end_age=55, n_biopsies=0, atypical_hyperplasia="unknown",
          age_menarche=13, age_first_birth=25, n_relatives=0), 1.072818),
    (dict(start_age=45, end_age=50, n_biopsies=1, atypical_hyperplasia="no",
          age_menarche=11, age_first_birth=30, n_relatives=1), 2.858841),
    # Exercises every non-default path at once: nulliparity sentinel (98),
    # atypical hyperplasia, two affected relatives, oldest age band.
    (dict(start_age=65, end_age=70, n_biopsies=2, atypical_hyperplasia="yes",
          age_menarche=14, age_first_birth=98, n_relatives=2), 14.607879),
    (dict(start_age=40, end_age=45, n_biopsies=0, atypical_hyperplasia="unknown",
          age_menarche=12, age_first_birth=22, n_relatives=0), 0.497614),
]


@pytest.mark.parametrize("kwargs,expected", BCRA_CASES)
def test_bcrat_matches_cran_bcra(kwargs, expected):
    got = bcrat_predict(race="white", **kwargs)["risk"] * 100
    assert got == pytest.approx(expected, abs=TOL)


# --- PREDICT vs `predictv30r:::benefits22` ------------------------------------
#
# benefits22 is UNEXPORTED. The exported `benefits222` computes DISEASE-FREE
# survival (it scales the baseline breast hazard by a relapse factor) and does
# not match this model. Using it cost 5.5 percentage points of apparent error.

ER_POS = dict(age=57, size_mm=29, nodes=5, grade=2, er_positive=True,
              her2=1, ki67=1, screen_detected=0)
FULL_RX = dict(chemo_generation=3, hormone=True, trastuzumab=True,
               bisphosphonate=True)


def test_predict_untreated_survival_er_positive():
    out = predict_breast(**ER_POS, **FULL_RX, years=10)
    assert out["survival_no_treatment"] * 100 == pytest.approx(42.487175, abs=TOL)


def test_predict_treatment_benefit_er_positive_10y():
    out = predict_breast(**ER_POS, **FULL_RX, years=10)
    assert out["benefit_percentage_points"] == pytest.approx(34.118736, abs=TOL)


def test_predict_standard_vs_extended_endocrine_are_distinct_arms():
    """The reference emits both `hctb` and `h10ctb`; they diverge only after
    year 10. Conflating them silently changes the patient's regimen — which is
    exactly the bug this test was written to prevent recurring.
    """
    standard = predict_breast(**ER_POS, **FULL_RX, years=15)
    extended = predict_breast(**ER_POS, **FULL_RX, extended_hormone=True, years=15)
    assert standard["benefit_percentage_points"] == pytest.approx(39.102128, abs=TOL)
    assert extended["benefit_percentage_points"] == pytest.approx(40.924915, abs=TOL)
    assert extended["benefit_percentage_points"] > standard["benefit_percentage_points"]

    # At 10 years the extended arm has not yet diverged.
    s10 = predict_breast(**ER_POS, **FULL_RX, years=10)["benefit_percentage_points"]
    e10 = predict_breast(**ER_POS, **FULL_RX, extended_hormone=True,
                         years=10)["benefit_percentage_points"]
    assert e10 == pytest.approx(s10, abs=TOL)


def test_predict_er_negative_case():
    kw = dict(age=45, size_mm=15, nodes=0, grade=1, er_positive=False,
              her2=0, ki67=9, screen_detected=1)
    out = predict_breast(**kw, chemo_generation=2, years=10)
    assert out["survival_no_treatment"] * 100 == pytest.approx(90.734652, abs=TOL)
    assert out["benefit_percentage_points"] == pytest.approx(1.353950, abs=TOL)


# --- SCORE2 vs CRAN `RiskScorescvd::SCORE2` ----------------------------------
#
# That package rounds its return to one decimal place (`return(round(x, 1))`),
# so the tolerance here is 0.05 percentage points, not machine epsilon. This is
# a limitation of the reference, not of our implementation.

SCORE2_TOL = 0.05

SCORE2_CASES = [
    ("low", dict(sex="male", age=50, sbp=140, total_chol_mmol=6.0,
                 hdl_mmol=1.0, smoker=True), 7.4),
    ("moderate", dict(sex="male", age=50, sbp=140, total_chol_mmol=6.0,
                      hdl_mmol=1.0, smoker=True), 9.6),
    ("high", dict(sex="female", age=65, sbp=130, total_chol_mmol=5.5,
                  hdl_mmol=1.4, smoker=False), 8.0),
    ("very_high", dict(sex="female", age=45, sbp=160, total_chol_mmol=7.0,
                       hdl_mmol=0.9, smoker=True), 22.6),
]


@pytest.mark.parametrize("region,kwargs,expected", SCORE2_CASES)
def test_score2_matches_riskscorescvd(region, kwargs, expected):
    from cancerverse_baseline.cvd.detection import score2_predict

    got = score2_predict(**kwargs, region=region)["risk"] * 100
    assert got == pytest.approx(expected, abs=SCORE2_TOL)


def test_score2_regional_recalibration_is_ordered():
    """All four ESC risk regions, same patient: risk must increase low -> very high."""
    from cancerverse_baseline.cvd.detection import score2_predict

    kw = dict(sex="male", age=50, sbp=140, total_chol_mmol=6.0,
              hdl_mmol=1.0, smoker=True)
    risks = [score2_predict(**kw, region=r)["risk"]
             for r in ("low", "moderate", "high", "very_high")]
    assert risks == sorted(risks)


def test_riskscorescvd_grace_is_a_different_model_and_is_not_our_reference():
    """Guard against a tempting but wrong parity target.

    `RiskScorescvd::GRACE_scores` takes `Gender` and `presentation_hstni`
    (high-sensitivity troponin) — neither appears in the Granger 2003 points
    nomogram this project implements. Fed our worked example 2 (Killip I,
    SBP 80, HR 60, age 55, creatinine 0.4 mg/dL, no arrest / ST depression /
    enzyme rise), it returns **79** where the published nomogram gives **103**.

    It is a different GRACE variant. Using it as a reference would force our
    implementation to agree with a model the paper did not publish. Recorded
    here so nobody wires it up later.
    """
    from cancerverse_baseline.cvd.prognosis import grace_predict

    ours = grace_predict(killip_class=1, sbp=80, heart_rate=60, age=55,
                         creatinine_mg_dl=0.4)
    assert ours["score"] == 103          # Granger 2003 Fig 4, worked example 2
    assert ours["score"] != 79           # what RiskScorescvd returns


# --- ERSPC RC3 vs SWOP's official Flash calculator ---------------------------
#
# SWOP's canonical tool cannot be probed for outputs: the arithmetic lives in a
# Flash object (`/2011/swf/c03dre.swf`) and Flash has been EOL since 2020, so
# the calculator no longer runs. The SWF is still served, and its ActionScript
# stores numeric literals as raw IEEE-754 doubles.
#
# Extracting them verifies the MODEL rather than a single output — a stronger
# check, since it covers the whole input space at once. Values below were
# recovered by `tests/parity/reference/swop_rc3_swf_extract.py` on 2026-08-05;
# worst deviation 2.2e-06, i.e. float round-tripping, not disagreement.

SWF_RC3_CONSTANTS = {
    "RC3_INTERCEPT": (-1.826, -1.825999),
    "RC3_PSA": (1.024, 1.023999),
    "RC3_VOL": (-1.50, -1.500000),
    "RC3_DRE": (0.992, 0.992000),
    "RC3_PSA_CENTER": (2.0, 1.999999),
    "RC3_VOL_CENTER": (5.4, 5.399998),
}


@pytest.mark.parametrize("name,pair", sorted(SWF_RC3_CONSTANTS.items()))
def test_erspc_rc3_coefficients_match_swop_flash_calculator(name, pair):
    from cancerverse_baseline.prostate.detection import coefficients as C

    ours, in_swf = pair
    assert getattr(C, name) == pytest.approx(ours)
    assert getattr(C, name) == pytest.approx(in_swf, abs=1e-5)


# --- Point tables vs MDCalc's published schema -------------------------------
#
# For models with no per-patient worked example, an independent reimplementation
# that publishes its own point table can still be compared entry-by-entry —
# which covers the whole input space, not one point. Values below were extracted
# from MDCalc's `__NEXT_DATA__` on 2026-08-05 by
# `tests/parity/reference/mdcalc_extract.py`.
#
# This is corroboration, not proof: MDCalc is secondary. It is decisive when the
# two DISAGREE — that is how the ALBI `-0.0852` error was found.

def test_capra_point_table_matches_mdcalc():
    from cancerverse_baseline.prostate.prognosis.capra import (
        gleason_points,
        psa_points,
        t_stage_points,
    )

    # MDCalc: <6=0, >=6-10=1, >=10-20=2, >=20-30=3, >30=4
    assert [psa_points(v) for v in (5.0, 8.0, 15.0, 25.0, 40.0)] == [0, 1, 2, 3, 4]
    # MDCalc: no 4/5 pattern=0, 4/5 in secondary=1, 4/5 in primary=3 (no 2!)
    assert gleason_points(3, 3) == 0
    assert gleason_points(3, 4) == 1
    assert gleason_points(4, 3) == 3
    # MDCalc: T1 or T2=0, T3a=1
    assert t_stage_points("T2") == 0
    assert t_stage_points("T3a") == 1


def test_cha2ds2_vasc_point_table_matches_mdcalc():
    from cancerverse_baseline.cvd.prognosis import cha2ds2_vasc_score

    base = dict(heart_failure=False, hypertension=False, age=50, diabetes=False,
                prior_stroke_tia_thromboembolism=False, vascular_disease=False,
                female=False)
    # MDCalc: age <65=0, 65-74=1, >=75=2
    assert cha2ds2_vasc_score(**{**base, "age": 64}) == 0
    assert cha2ds2_vasc_score(**{**base, "age": 70}) == 1
    assert cha2ds2_vasc_score(**{**base, "age": 80}) == 2
    # MDCalc: female=1, CHF=1, HTN=1, stroke=2, vascular=1, diabetes=1
    assert cha2ds2_vasc_score(**{**base, "female": True}) == 1
    assert cha2ds2_vasc_score(**{**base, "heart_failure": True}) == 1
    assert cha2ds2_vasc_score(**{**base, "hypertension": True}) == 1
    assert cha2ds2_vasc_score(**{**base, "prior_stroke_tia_thromboembolism": True}) == 2
    assert cha2ds2_vasc_score(**{**base, "vascular_disease": True}) == 1
    assert cha2ds2_vasc_score(**{**base, "diabetes": True}) == 1


def test_albi_formula_matches_mdcalc_statement():
    """MDCalc prints: ALBI = (log10 bilirubin x 0.66) + (albumin x -0.085),
    bilirubin in umol/L, albumin in g/L. Identical to Johnson 2015."""
    from cancerverse_baseline.liver.prognosis import albi as A

    assert A.BILIRUBIN_COEF == 0.66
    assert A.ALBUMIN_COEF == -0.085
