"""Unit maths for the Wang 2024 pCR nomogram.

The parity test (tests/parity/test_wang_larc_pcr_parity.py) checks us against
the authors' deployed calculator. This file checks the things a calculator
cannot: the reference levels, the input contract, and the several places where
this model's behaviour is surprising enough that someone will eventually
"fix" it.
"""

from __future__ import annotations

import math

import pytest

from cancerverse_baseline.colorectal.response import wang_larc_pcr_predict
from cancerverse_baseline.colorectal.response.wang_larc_pcr import (
    AXIS,
    CEA_MAX_NG_ML,
    COEF,
    MODEL_ID,
    REFERENCE_LEVELS,
    linear_predictor,
)

#: The patient every coefficient is measured against: all reference levels
#: and CEA 0, so the linear predictor is the intercept alone.
REFERENCE_PATIENT = dict(
    n_stage="cN0",
    t_stage="cT2",
    mri_emvi_positive=False,
    total_neoadjuvant_therapy=False,
    histopathology="adenocarcinoma",
    cea_ng_ml=0.0,
)


def test_the_reference_patient_is_the_intercept_alone():
    lp = linear_predictor(**REFERENCE_PATIENT)
    assert lp == pytest.approx(COEF["Intercept"])
    out = wang_larc_pcr_predict(**REFERENCE_PATIENT)
    assert out["p_pcr"] == pytest.approx(1 / (1 + math.exp(-COEF["Intercept"])))
    assert out["p_pcr"] == pytest.approx(0.4967, abs=5e-5)


def test_the_reference_levels_are_the_ones_carrying_no_term():
    """Stated as a test because the paper does not state them at all. cT2 in
    particular is impossible to guess: Table 4 presents T stage as an ordinal
    score, so a reader would naturally assume cT1 is the base level."""
    assert REFERENCE_LEVELS["t_stage"] == "cT2"
    base = linear_predictor(**REFERENCE_PATIENT)
    for field, level in [
        ("n_stage", "cN0"),
        ("t_stage", "cT2"),
        ("histopathology", "adenocarcinoma"),
    ]:
        assert linear_predictor(**{**REFERENCE_PATIENT, field: level}) == base
    assert linear_predictor(
        **{**REFERENCE_PATIENT, "mri_emvi_positive": False}
    ) == base
    assert linear_predictor(
        **{**REFERENCE_PATIENT, "total_neoadjuvant_therapy": False}
    ) == base


@pytest.mark.parametrize(
    "field,value,expected_delta",
    [
        ("n_stage", "cN1", COEF["Pre_CRT_N_stage=cN1"]),
        ("n_stage", "cN2", COEF["Pre_CRT_N_stage=cN2"]),
        ("t_stage", "cT1", COEF["Pre_CRT_T_stage=cTcT1"]),
        ("t_stage", "cT3", COEF["Pre_CRT_T_stage=cT3"]),
        ("t_stage", "cT4", COEF["Pre_CRT_T_stage=cT4"]),
        ("mri_emvi_positive", True, COEF["Pre_CRT_MRI_EMVI=Positive"]),
        ("total_neoadjuvant_therapy", True,
         COEF["Total_neoadjuvant_therapy=Yes"]),
        ("histopathology", "signet_ring_mucinous",
         COEF["Histopathology=Signet-ring cell carcinoma/Mucinous "
              "adenocarcinoma"]),
    ],
)
def test_each_level_moves_the_logit_by_exactly_its_coefficient(
    field, value, expected_delta
):
    base = linear_predictor(**REFERENCE_PATIENT)
    moved = linear_predictor(**{**REFERENCE_PATIENT, field: value})
    assert moved - base == pytest.approx(expected_delta)


def test_cea_is_linear_per_ng_per_ml_and_lowers_the_probability():
    """The paper's points term reads "+3.85 x CEA", but its axis is REVERSED
    (">= 24 = 0" points). The regression coefficient is negative. Anyone who
    wires the points sign straight into a logit inverts this covariate."""
    assert COEF["Pre_CRT_CEA"] < 0
    base = linear_predictor(**REFERENCE_PATIENT)
    for cea in (1.0, 7.5, 24.0):
        lp = linear_predictor(**{**REFERENCE_PATIENT, "cea_ng_ml": cea})
        assert lp - base == pytest.approx(COEF["Pre_CRT_CEA"] * cea)
    high = wang_larc_pcr_predict(**{**REFERENCE_PATIENT, "cea_ng_ml": 24.0})
    low = wang_larc_pcr_predict(**REFERENCE_PATIENT)
    assert high["p_pcr"] < low["p_pcr"]


def test_t_stage_is_not_monotone_and_that_is_the_published_model():
    """cT3 sits ABOVE cT2 and cT4 barely differs from it. Clinically backwards,
    statistically what was fitted (cT4 is p = 0.836), and reproduced by the
    authors' own calculator. Pinned so it is not quietly reordered."""
    lp = {
        stage: linear_predictor(**{**REFERENCE_PATIENT, "t_stage": stage})
        for stage in ("cT1", "cT2", "cT3", "cT4")
    }
    assert lp["cT1"] > lp["cT3"] > lp["cT4"] > lp["cT2"]


def test_n_stage_is_monotone_downward():
    lp = {
        stage: linear_predictor(**{**REFERENCE_PATIENT, "n_stage": stage})
        for stage in ("cN0", "cN1", "cN2")
    }
    assert lp["cN0"] > lp["cN1"] > lp["cN2"]


@pytest.mark.parametrize(
    "given", ["cT1", "ct1", "T1", "t1", "cTcT1", "ctct1", "cT 1"]
)
def test_the_mangled_source_level_name_is_accepted_for_ct1(given):
    """The fitted level is literally called `cTcT1`, a doubled prefix baked
    into the authors' dataset. Both spellings must reach the same term."""
    assert linear_predictor(
        **{**REFERENCE_PATIENT, "t_stage": given}
    ) == pytest.approx(
        linear_predictor(**{**REFERENCE_PATIENT, "t_stage": "cT1"})
    )


@pytest.mark.parametrize(
    "given",
    ["Adenocarcinoma", "adenocarcinoma", "ADENOCARCINOMA"],
)
def test_adenocarcinoma_spellings(given):
    assert linear_predictor(
        **{**REFERENCE_PATIENT, "histopathology": given}
    ) == pytest.approx(linear_predictor(**REFERENCE_PATIENT))


@pytest.mark.parametrize(
    "given",
    [
        "signet_ring_mucinous",
        "Signet-ring cell carcinoma/Mucinous adenocarcinoma",
        "mucinous adenocarcinoma",
    ],
)
def test_signet_ring_and_mucinous_are_one_level(given):
    """The fit pools them; a caller who expects two distinct effects should
    find out here rather than by getting a plausible wrong number."""
    delta = linear_predictor(
        **{**REFERENCE_PATIENT, "histopathology": given}
    ) - linear_predictor(**REFERENCE_PATIENT)
    assert delta == pytest.approx(
        COEF["Histopathology=Signet-ring cell carcinoma/Mucinous adenocarcinoma"]
    )


@pytest.mark.parametrize("cea", [-0.1, 24.1, 100.0])
def test_cea_outside_the_deployed_range_is_refused_not_extrapolated(cea):
    """0-24 ng/mL is the authors' own slider range and the paper's ">= 24"
    floor. A linear logit term run past its fitted range is our invention."""
    with pytest.raises(ValueError, match="cea_ng_ml"):
        wang_larc_pcr_predict(**{**REFERENCE_PATIENT, "cea_ng_ml": cea})
    assert CEA_MAX_NG_ML == 24.0


@pytest.mark.parametrize(
    "field,value",
    [("n_stage", "cN3"), ("n_stage", "N"), ("t_stage", "cT0"),
     ("t_stage", "cT5"), ("histopathology", "squamous")],
)
def test_unknown_levels_are_rejected(field, value):
    with pytest.raises(ValueError):
        wang_larc_pcr_predict(**{**REFERENCE_PATIENT, field: value})


def test_the_worst_and_best_patients_bracket_everyone():
    worst = wang_larc_pcr_predict(
        n_stage="cN2", t_stage="cT2", mri_emvi_positive=True,
        total_neoadjuvant_therapy=False,
        histopathology="signet_ring_mucinous", cea_ng_ml=24.0,
    )["p_pcr"]
    best = wang_larc_pcr_predict(
        n_stage="cN0", t_stage="cT1", mri_emvi_positive=False,
        total_neoadjuvant_therapy=True,
        histopathology="adenocarcinoma", cea_ng_ml=0.0,
    )["p_pcr"]
    assert 0.0 < worst < 0.02
    assert 0.85 < best < 1.0


def test_the_api_shape_and_the_direction_of_risk():
    out = wang_larc_pcr_predict(**REFERENCE_PATIENT)
    assert out["model_id"] == MODEL_ID == "wang_larc_pcr"
    assert out["axis"] == AXIS == "response"
    assert out["disease"] == "colorectal"
    assert "cam4.7251" in out["citation"]
    # `risk` is the repo-wide name for the primary scalar, but for this model
    # it is the probability of a GOOD outcome. Both keys must agree.
    assert out["risk"] == out["p_pcr"]
    assert "GOOD outcome" in out["notes"]
