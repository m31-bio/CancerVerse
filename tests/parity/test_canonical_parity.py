"""Parity placeholders vs canonical calculators.

Fill expected risks from the live SWOP / Cambridge tools, then remove xfail.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.cvd.detection import prevent_predict_all
from cancerverse_baseline.cvd.prognosis import grace_predict
from cancerverse_baseline.lung.detection import plcom2012_predict


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


# Two web-calculator placeholders were removed here on 2026-08-18. Both were
# `xfail(strict=False)` around `expected_risk = None; assert expected_risk is
# not None` -- bodies that could never pass, so they reported nothing whether
# the model was right or wrong, and they inflated the test count with two
# entries that asserted nothing about the library.
#
# They were also stale. The erspc_rc3 one gave its reason as
# `parity_status=not_checked`; the registry has said `checked` since
# 2026-08-05, and its TODO asked a future reader to obtain SWOP outputs that
# the same registry entry records as unobtainable (the calculator is a 2011
# Flash SWF and Flash is EOL). Parity there was established by extracting all
# six constants from that SWF directly -- a claim about the model rather than
# about one output. See tests/parity/reference/swop_rc3_swf_extract.py.
#
# The score2 one wanted a Cambridge chart vignette; SCORE2 was checked against
# CRAN RiskScorescvd::SCORE2 across all four ESC regions, and its registry note
# says in as many words that no web calculator was needed.
#
# If a second, independent parity route is ever wanted for either model, the
# place to record that intent is the model's registry entry, not a test that
# cannot run. `test_no_test_can_never_pass` in tests/test_test_hygiene.py
# now fails if a placeholder of this shape is added back.


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
