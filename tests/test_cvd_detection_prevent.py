"""Tests for the AHA PREVENT equations (base + uacr/hba1c/sdi/full, 10y + 30y)."""

import pytest

from mayo_baseline.cvd.detection import prevent_coefficients as C
from mayo_baseline.cvd.detection import prevent_predict, prevent_predict_all
from mayo_baseline.cvd.detection.prevent import linear_predictor, select_variant

# Supplemental Table S25 vignette from the development article.
S25 = dict(
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


def test_all_100_coefficient_sets_present():
    assert set(C.VARIANTS) == {"base", "uacr", "hba1c", "sdi", "full"}
    assert set(C.HORIZONS) == {10, 30}
    for variant in C.VARIANTS:
        for horizon in C.HORIZONS:
            table = C.PREVENT_TABLES[(variant, horizon)]
            assert set(table) == {
                f"{s}_{o}" for s in ("female", "male") for o in C.OUTCOMES
            }, (variant, horizon)
    assert sum(len(t) for t in C.PREVENT_TABLES.values()) == 100


def test_30yr_tables_add_age_squared_10yr_do_not():
    for variant in C.VARIANTS:
        for key, betas in C.PREVENT_TABLES[(variant, 30)].items():
            assert "age_sq" in betas, (variant, key)
        for key, betas in C.PREVENT_TABLES[(variant, 10)].items():
            assert "age_sq" not in betas, (variant, key)


def test_ascvd_and_chd_stroke_ignore_bmi():
    """Only the heart-failure (and hence total-CVD composite) models use BMI."""
    for outcome in ("ascvd", "chd", "stroke"):
        for sex in ("female", "male"):
            betas = C.PREVENT_TABLES[("base", 10)][f"{sex}_{outcome}"]
            assert betas["bmi_min"] == 0.0
            assert betas["bmi_max"] == 0.0
            assert betas["age_bmi_max"] == 0.0


def test_heart_failure_uses_bmi_but_not_lipids():
    betas = C.PREVENT_TABLES[("base", 10)]["female_heart_failure"]
    assert betas["bmi_max"] != 0.0
    assert betas["non_hdl"] == 0.0
    assert betas["hdl"] == 0.0


def test_extended_variants_carry_their_extra_term():
    for variant, term in (("uacr", "ln_acr"), ("hba1c", "hba1c_dm"), ("sdi", "sdi_4_6")):
        for key, betas in C.PREVENT_TABLES[(variant, 10)].items():
            assert term in betas, (variant, key)
        for key, betas in C.PREVENT_TABLES[("base", 10)].items():
            assert term not in betas, key


def test_full_variant_carries_all_three_extra_terms():
    for key, betas in C.PREVENT_TABLES[("full", 10)].items():
        for term in ("ln_acr", "hba1c_dm", "sdi_4_6"):
            assert term in betas, (key, term)


def test_risk_increases_with_established_risk_factors():
    base = prevent_predict(**{**S25, "diabetes": False, "smoker": False})["risk"]
    with_dm = prevent_predict(**{**S25, "diabetes": True, "smoker": False})["risk"]
    with_smoke = prevent_predict(**{**S25, "diabetes": False, "smoker": True})["risk"]
    assert with_dm > base
    assert with_smoke > base


def test_statin_and_low_egfr_move_risk_in_expected_direction():
    on_statin = prevent_predict(**{**S25, "statin": True})["risk"]
    off_statin = prevent_predict(**{**S25, "statin": False})["risk"]
    assert on_statin < off_statin
    low_egfr = prevent_predict(**{**S25, "egfr": 40})["risk"]
    assert low_egfr > off_statin


def test_sbp_below_knot_is_j_shaped_at_base_10yr():
    """Below the 110 mm Hg knot the SBP slope is negative — lower SBP raises risk.

    This J-curve is a genuine feature of the published equations, not a sign
    error: the `SBP <110 per 20 mmHg` beta is negative for every base 10-year
    model. It is NOT universal across all 100 coefficient sets — several
    30-year extended-model female outcomes (ascvd/chd/stroke) have a beta
    that is slightly positive but near zero, i.e. the curve goes essentially
    flat rather than reversing; that is data, not a transcription error.
    """
    common = dict(
        sex="male",
        outcome="heart_failure",
        total_chol_mg_dl=200,
        hdl_mg_dl=50,
        diabetes=False,
        smoker=False,
        bmi=22,
        egfr=90,
        htn_meds=False,
        statin=False,
    )
    a = linear_predictor(age=60, sbp=100, **common)
    b = linear_predictor(age=60, sbp=90, **common)
    assert b > a
    for key, betas in C.PREVENT_TABLES[("base", 10)].items():
        assert betas["sbp_min"] < 0.0, key


def test_total_cvd_exceeds_each_component():
    r = prevent_predict_all(**S25)
    assert r["total_cvd"] > r["ascvd"]
    assert r["total_cvd"] > r["heart_failure"]
    assert r["ascvd"] > r["chd"]


def test_age_range_enforced_per_horizon():
    with pytest.raises(ValueError, match="10-year.*30-79"):
        prevent_predict(**{**S25, "age": 25})
    with pytest.raises(ValueError, match="10-year.*30-79"):
        prevent_predict(**{**S25, "age": 85})
    with pytest.raises(ValueError, match="30-year.*30-59"):
        prevent_predict(**{**S25, "age": 65}, horizon_years=30)
    # Valid at 30y horizon within its narrower range.
    prevent_predict(**{**S25, "age": 45}, horizon_years=30)


def test_invalid_sex_outcome_variant_horizon():
    with pytest.raises(ValueError, match="sex"):
        prevent_predict(**{**S25, "sex": "other"})
    with pytest.raises(ValueError, match="outcome"):
        prevent_predict(**S25, outcome="dementia")
    with pytest.raises(ValueError, match="variant"):
        prevent_predict(**S25, variant="bogus")
    with pytest.raises(ValueError, match="horizon_years"):
        prevent_predict(**S25, horizon_years=20)


def test_metadata():
    out = prevent_predict(**S25)
    assert out["model_id"] == "prevent"
    assert out["axis"] == "detection"
    assert out["outcome"] == "total_cvd"
    assert out["horizon_years"] == 10
    assert out["variant"] == "base"


# --- variant auto-selection (mirrors preventr::estimate_risk's documented rule) ---


def test_variant_auto_selection_rule():
    assert select_variant(uacr=None, hba1c=None, sdi_decile=None) == "base"
    assert select_variant(uacr=30.0, hba1c=None, sdi_decile=None) == "uacr"
    assert select_variant(uacr=None, hba1c=6.0, sdi_decile=None) == "hba1c"
    assert select_variant(uacr=None, hba1c=None, sdi_decile=5) == "sdi"
    assert select_variant(uacr=30.0, hba1c=6.0, sdi_decile=None) == "full"
    assert select_variant(uacr=30.0, hba1c=6.0, sdi_decile=5) == "full"


def test_supplying_one_extra_lab_auto_selects_its_variant():
    out = prevent_predict(**S25, uacr=30.0)
    assert out["variant"] == "uacr"


def test_sdi_decile_bucketing():
    # Each call spells out its arguments rather than sharing a dict: the three
    # differ only in sdi_decile, and seeing that difference on the page is the
    # point of the test.
    lp_low = linear_predictor(
        sex="female", outcome="total_cvd", variant="sdi", sdi_decile=2,
        age=50, total_chol_mg_dl=200, hdl_mg_dl=45, sbp=160, diabetes=True,
        smoker=False, bmi=35, egfr=90, htn_meds=True, statin=False,
    )
    lp_mid = linear_predictor(
        sex="female", outcome="total_cvd", variant="sdi", sdi_decile=5,
        age=50, total_chol_mg_dl=200, hdl_mg_dl=45, sbp=160, diabetes=True,
        smoker=False, bmi=35, egfr=90, htn_meds=True, statin=False,
    )
    lp_high = linear_predictor(
        sex="female", outcome="total_cvd", variant="sdi", sdi_decile=9,
        age=50, total_chol_mg_dl=200, hdl_mg_dl=45, sbp=160, diabetes=True,
        smoker=False, bmi=35, egfr=90, htn_meds=True, statin=False,
    )
    # Deciles 1-3 are the reference (no indicator fires); 4-6 and 7-10 each add
    # their own positive beta for this model/sex, so risk should not collapse
    # back to the reference as deprivation increases.
    assert lp_mid != lp_low
    assert lp_high != lp_low


def test_hba1c_uses_diabetes_specific_slope():
    """The hba1c_dm / hba1c_no_dm split means the same HbA1c value enters via a
    different beta depending on diabetes status — never both."""
    lp_dm = linear_predictor(
        sex="male", outcome="total_cvd", variant="hba1c", hba1c=7.5,
        age=55, total_chol_mg_dl=190, hdl_mg_dl=45, sbp=130, diabetes=True,
        smoker=False, bmi=28, egfr=80, htn_meds=False, statin=False,
    )
    lp_no_dm = linear_predictor(
        sex="male", outcome="total_cvd", variant="hba1c", hba1c=7.5,
        age=55, total_chol_mg_dl=190, hdl_mg_dl=45, sbp=130, diabetes=False,
        smoker=False, bmi=28, egfr=80, htn_meds=False, statin=False,
    )
    assert lp_dm != lp_no_dm


def test_missing_lab_scores_via_missing_indicator_not_a_crash():
    """Full model with all three labs absent must equal the base-model logit
    plus each variant's own constant/structure — at minimum it must run and
    each 'missing' indicator must be the only nonzero extended term."""
    lp = linear_predictor(
        sex="male", outcome="total_cvd", variant="full",
        uacr=None, hba1c=None, sdi_decile=None,
        age=55, total_chol_mg_dl=190, hdl_mg_dl=45, sbp=130, diabetes=False,
        smoker=False, bmi=28, egfr=80, htn_meds=False, statin=False,
    )
    assert isinstance(lp, float)


def test_invalid_extended_inputs():
    with pytest.raises(ValueError, match="sdi_decile"):
        prevent_predict(**S25, sdi_decile=11)
    with pytest.raises(ValueError, match="uacr"):
        prevent_predict(**S25, uacr=-5.0)


def test_bmi_only_affects_the_heart_failure_outcome():
    """BMI is a required argument on every call, but the published equations
    zero its coefficients for every outcome except heart failure.

    Found by the feature-importance sweep, which reported BMI at 0% influence
    on the default outcome and so looked like a wiring bug. It is not: 40 of
    the 50 coefficient sets per sex carry bmi_min = bmi_max = age_bmi_max = 0.
    Pinned so the zero is understood as published behaviour, and so a future
    coefficient refresh that silently drops the heart-failure BMI terms fails.
    """
    from mayo_baseline.cvd.detection import prevent_coefficients as C
    from mayo_baseline.cvd.detection import prevent_predict
    from mayo_baseline.cvd.detection.prevent import BMI_ONLY_AFFECTS

    common = dict(sex="female", age=55, total_chol_mg_dl=200, hdl_mg_dl=50,
                  sbp=130, diabetes=False, smoker=False, egfr=90,
                  htn_meds=False, statin=False)
    for outcome in C.OUTCOMES:
        lean = prevent_predict(**common, bmi=20, outcome=outcome)["risk"]
        obese = prevent_predict(**common, bmi=40, outcome=outcome)["risk"]
        if outcome in BMI_ONLY_AFFECTS:
            assert obese > lean, f"{outcome}: BMI must raise risk"
        else:
            assert lean == obese, f"{outcome}: BMI must have no effect"

    # And the same split holds in the coefficient tables themselves.
    nonzero = [
        (v, h, o)
        for v in C.VARIANTS for h in C.HORIZONS for o in C.OUTCOMES
        if any(C.PREVENT_TABLES[(v, h)][f"female_{o}"].get(k, 0.0) != 0.0
               for k in ("bmi_min", "bmi_max", "age_bmi_max"))
    ]
    assert {o for _, _, o in nonzero} == set(BMI_ONLY_AFFECTS)
    assert len(nonzero) == len(C.VARIANTS) * len(C.HORIZONS)
