"""Parity placeholders vs canonical calculators.

Fill expected risks from the live SWOP / Cambridge tools, then remove xfail.
"""

from __future__ import annotations

import pytest

from mayo_baseline.cvd.detection import prevent_predict_all
from mayo_baseline.cvd.prognosis import grace_predict
from mayo_baseline.lung.detection import plcom2012_predict
from mayo_baseline.prostate.detection import erspc_rc3_predict


def test_prevent_supplemental_table_s25_vignette():
    """Worked example from Table S25 of the PREVENT development article.

    Female, 50 y, SBP 160 on antihypertensives, total cholesterol 200 mg/dL,
    HDL 45 mg/dL, no statin, diabetes, non-smoker, eGFR 90, BMI 35.
    Published 10-year risks are quoted to 3 decimal places.
    """
    risks = prevent_predict_all(
        sex="female",
        age=50,
        sbp=160,
        htn_meds=True,
        total_chol_mg_dl=200,
        hdl_mg_dl=45,
        statin=False,
        diabetes=True,
        smoker=False,
        egfr=90,
        bmi=35,
    )
    expected = {
        "total_cvd": 0.147,
        "ascvd": 0.092,
        "heart_failure": 0.081,
        "chd": 0.044,
        "stroke": 0.054,
    }
    for outcome, want in expected.items():
        assert risks[outcome] == pytest.approx(want, abs=5e-4), outcome


def test_plcom2012_resplab_worked_example():
    """Worked example from the canonical R package resplab/PLCOm2012 README.

    62 y, White, education level 4, BMI 27, no COPD / cancer history / family
    history, former smoker, 80 cigarettes/day for 27 years, quit 10 years ago
    → 6-year risk 0.01750922.
    """
    out = plcom2012_predict(
        age=62,
        race="white",
        education_level=4,
        bmi=27,
        copd=False,
        personal_cancer_history=False,
        family_history_lung_cancer=False,
        current_smoker=False,
        cigarettes_per_day=80,
        smoking_duration_years=27,
        quit_years=10,
    )
    assert out["risk"] == pytest.approx(0.01750922, abs=1e-8)


@pytest.mark.xfail(reason="SWOP UI vignette not yet recorded; parity_status=not_checked", strict=False)
def test_erspc_rc3_swop_vignette_placeholder():
    # TODO: run the same inputs on https://www.prostatecancer-riskcalculator.com
    # and set expected_risk to the displayed any-PCa probability.
    out = erspc_rc3_predict(psa=4.0, volume_ml=40.0, dre_positive=False)
    expected_risk = None  # fill from SWOP UI
    assert expected_risk is not None
    assert out["risk"] == pytest.approx(expected_risk, abs=0.01)


@pytest.mark.xfail(reason="Cambridge score2risk / chart vignette not yet recorded", strict=False)
def test_score2_cambridge_vignette_placeholder():
    from mayo_baseline.cvd.detection import score2_predict

    out = score2_predict(
        sex="male",
        age=50,
        sbp=140,
        total_chol_mmol=6.0,
        hdl_mmol=1.0,
        smoker=True,
        region="low",
    )
    # Eur Heart J chart example text: ~2.9% in low-risk countries for similar profile
    # (confirm exact inputs against chart before enabling).
    expected_risk = None
    assert expected_risk is not None
    assert out["risk"] == pytest.approx(expected_risk, abs=0.005)


def test_grace_published_worked_examples():
    """Both worked examples from Granger et al. 2003, Figure 4.

    Example 1's published total (196) is an arithmetic slip — the components
    the paper itself lists sum to 195. We reproduce every component exactly,
    which is the real parity claim; see the module docstring.
    """
    ex1 = grace_predict(
        killip_class=2, sbp=100, heart_rate=100, age=65, creatinine_mg_dl=1.0,
        cardiac_arrest_at_admission=False, st_segment_deviation=True,
        elevated_cardiac_enzymes=True,
    )
    assert list(ex1["components"].values()) == [20, 53, 15, 58, 7, 0, 28, 14]
    assert ex1["risk"] == pytest.approx(0.16, abs=0.01)   # paper: "about 16%"

    ex2 = grace_predict(
        killip_class=1, sbp=80, heart_rate=60, age=55, creatinine_mg_dl=0.4,
    )
    assert ex2["score"] == 103                             # paper: 103
    assert ex2["risk"] == pytest.approx(0.009, abs=0.001)  # paper: "about 0.9%"
