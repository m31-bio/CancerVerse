"""Tests for the cervical CIN2+/CIN3+ logistic models (BMC Med 2021 Table S1)."""

import math

import pytest

from cancerverse_baseline.cervical.detection import cervical_cin_risk_predict as predict
from cancerverse_baseline.cervical.detection.cin_risk import (
    CYTOLOGY_LEVELS,
    GENOTYPE_GROUPS,
    MODELS,
)


def test_base_model_matches_table_s1_by_hand():
    b = MODELS["base"]
    expected_lp = b["intercept"] + b["hrHPV"] * 1 + b["age"] * 40 + b["LSIL"]
    out = predict(hrhpv_positive=True, cytology="LSIL", age=40)
    assert out["linear_predictor"] == pytest.approx(expected_lp)
    assert out["risk"] == pytest.approx(1 / (1 + math.exp(-expected_lp)))


def test_nilm_is_the_cytology_reference_level():
    """NILM contributes nothing; every other level adds its own positive beta."""
    base = predict(hrhpv_positive=True, cytology="NILM", age=40)["linear_predictor"]
    b = MODELS["base"]
    for level in CYTOLOGY_LEVELS:
        lp = predict(hrhpv_positive=True, cytology=level, age=40)["linear_predictor"]
        if level == "NILM":
            assert lp == pytest.approx(base)
        else:
            assert lp - base == pytest.approx(b[level]), level


def test_cytology_severity_is_ordered_and_scc_dominates():
    order = ["NILM", "ASC-US", "LSIL", "ASC-H", "AGC", "HSIL/AIS", "SCC/ADC"]
    risks = [predict(hrhpv_positive=True, cytology=c, age=40)["risk"] for c in order]
    assert risks == sorted(risks)
    # SCC/ADC is the largest single term in the model — ~3.5x the hrHPV beta.
    assert MODELS["base"]["SCC/ADC"] > 3 * MODELS["base"]["hrHPV"]


def test_age_coefficient_is_negative_by_design():
    """Conditional on HPV and cytology, older women were at slightly lower risk.
    This is the published sign, not a transcription error."""
    for variant in MODELS:
        assert MODELS[variant]["age"] < 0, variant
    young = predict(hrhpv_positive=True, cytology="ASC-US", age=25)["risk"]
    old = predict(hrhpv_positive=True, cytology="ASC-US", age=60)["risk"]
    assert old < young


def test_hrhpv_positivity_raises_risk_in_every_variant():
    for variant in MODELS:
        kw = {}
        if "E6" in MODELS[variant]:
            kw["e6_positive"] = False
        if any(g in MODELS[variant] for g in GENOTYPE_GROUPS):
            kw["genotypes"] = {}
        neg = predict(
            hrhpv_positive=False, cytology="ASC-US", age=40, variant=variant, **kw
        )["risk"]
        pos = predict(
            hrhpv_positive=True, cytology="ASC-US", age=40, variant=variant, **kw
        )["risk"]
        assert pos > neg, variant


def test_e6_positivity_raises_risk():
    off = predict(
        hrhpv_positive=True, cytology="ASC-US", age=40, variant="e6", e6_positive=False
    )["risk"]
    on = predict(
        hrhpv_positive=True, cytology="ASC-US", age=40, variant="e6", e6_positive=True
    )["risk"]
    assert on > off


def test_some_genotype_groups_carry_negative_betas():
    """HPV59/56/66 and HPV51 reduce risk relative to other hrHPV types,
    published, and clinically sensible since they are lower-oncogenic-risk."""
    g = MODELS["genotyping"]
    assert g["HPV16"] > 0 and g["HPV33/58"] > 0
    assert g["HPV59/56/66"] < 0 and g["HPV51"] < 0

    base = predict(
        hrhpv_positive=True,
        cytology="ASC-US",
        age=40,
        variant="genotyping",
        genotypes={},
    )["risk"]
    hpv16 = predict(
        hrhpv_positive=True,
        cytology="ASC-US",
        age=40,
        variant="genotyping",
        genotypes={"HPV16": True},
    )["risk"]
    low_risk_type = predict(
        hrhpv_positive=True,
        cytology="ASC-US",
        age=40,
        variant="genotyping",
        genotypes={"HPV59/56/66": True},
    )["risk"]
    assert hpv16 > base > low_risk_type


def test_cytology_aliases_normalize():
    for alias, canonical in (
        ("normal", "NILM"),
        ("ASCUS", "ASC-US"),
        ("hsil", "HSIL/AIS"),
        ("scc", "SCC/ADC"),
    ):
        assert (
            predict(hrhpv_positive=True, cytology=alias, age=40)["cytology"]
            == canonical
        )


def test_variant_input_requirements_are_enforced():
    with pytest.raises(ValueError, match="requires e6_positive"):
        predict(hrhpv_positive=True, cytology="NILM", age=40, variant="e6")
    with pytest.raises(ValueError, match="does not use e6_positive"):
        predict(hrhpv_positive=True, cytology="NILM", age=40, e6_positive=True)
    with pytest.raises(ValueError, match="requires genotypes"):
        predict(hrhpv_positive=True, cytology="NILM", age=40, variant="genotyping")
    with pytest.raises(ValueError, match="unknown genotype"):
        predict(
            hrhpv_positive=True,
            cytology="NILM",
            age=40,
            variant="genotyping",
            genotypes={"HPV99": True},
        )


def test_invalid_inputs():
    with pytest.raises(ValueError, match="variant"):
        predict(hrhpv_positive=True, cytology="NILM", age=40, variant="bogus")
    with pytest.raises(ValueError, match="cytology"):
        predict(hrhpv_positive=True, cytology="weird", age=40)
    with pytest.raises(ValueError, match="age"):
        predict(hrhpv_positive=True, cytology="NILM", age=0)


def test_metadata():
    out = predict(hrhpv_positive=True, cytology="NILM", age=40)
    assert out["model_id"] == "cervical_cin_risk"
    assert out["axis"] == "detection"
    assert out["disease"] == "cervical"
    assert 0.0 < out["risk"] < 1.0
