"""Shapiro nomogram, the contract, not the arithmetic.

Fig. 1's constants are pinned in tests/parity/test_shapiro_ncrt_parity.py.
This file checks what a parity test cannot: that the four unpublished totals
stay unpublished, that the staging-edition trap is refused rather than
silently mis-scored, and that the model's real weakness reaches the caller.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.esophageal.prognosis.shapiro_ncrt import (
    AXIS,
    DISEASE,
    MODEL_ID,
    shapiro_ncrt_predict,
    shapiro_points,
)

BASELINE = dict(cn_category="cN0", ypt_category="ypT0", ypn_category="ypN0")


def test_the_result_identifies_itself_to_the_registry():
    out = shapiro_ncrt_predict(**BASELINE)
    assert (out["model_id"], out["axis"], out["disease"]) == (
        MODEL_ID, AXIS, DISEASE) == ("shapiro_ncrt", "prognosis", "esophageal")


def test_risk_is_none_because_this_returns_published_percentages():
    assert shapiro_ncrt_predict(**BASELINE)["risk"] is None


def test_the_best_patient_gets_the_top_of_both_axes():
    out = shapiro_ncrt_predict(**BASELINE)
    assert out["total_points"] == 0
    assert (out["one_year_survival_pct"], out["five_year_survival_pct"]) == (91.0, 70.0)


def test_the_worst_patient_gets_the_bottom_of_both_axes():
    out = shapiro_ncrt_predict(cn_category="cN1", ypt_category="ypT3",
                               ypn_category="ypN3")
    assert out["total_points"] == 16
    assert (out["one_year_survival_pct"], out["five_year_survival_pct"]) == (41.0, 3.0)


def test_points_are_additive_and_the_breakdown_sums_to_the_total():
    out = shapiro_ncrt_predict(cn_category="cN1", ypt_category="ypT3",
                               ypn_category="ypN1")
    assert out["points"] == {"cn": 2, "ypt": 4, "ypn": 4}
    assert sum(out["points"].values()) == out["total_points"] == 10


# ---------------------------------------------------------------------------
# The four unpublished totals, the behaviour this module exists to get right.
# ---------------------------------------------------------------------------

def test_a_ypN2_patient_gets_none_rather_than_an_interpolated_number():
    out = shapiro_ncrt_predict(cn_category="cN0", ypt_category="ypT0",
                               ypn_category="ypN2")
    assert out["total_points"] == 5
    assert out["survival_available"] is False
    assert out["one_year_survival_pct"] is None
    assert out["five_year_survival_pct"] is None


def test_every_ypN2_patient_lands_on_an_unlabelled_total():
    """Not a rare corner. ypN2 is 3-6 positive nodes and every one of its
    twelve input combinations falls between labelled ticks, because ypN2 is
    the only odd point value in the model."""
    for cn in ("cN0", "cN1"):
        for ypt in ("ypT0", "ypT1", "ypT2", "ypT3"):
            out = shapiro_ncrt_predict(cn_category=cn, ypt_category=ypt,
                                       ypn_category="ypN2")
            assert out["survival_available"] is False, (cn, ypt)


def test_every_non_ypN2_patient_does_get_a_published_figure():
    """The complement: the gap is exactly ypN2 and nothing else, so 90% of
    patients are served normally."""
    for cn in ("cN0", "cN1"):
        for ypt in ("ypT0", "ypT1", "ypT2", "ypT3"):
            for ypn in ("ypN0", "ypN1", "ypN3"):
                out = shapiro_ncrt_predict(cn_category=cn, ypt_category=ypt,
                                           ypn_category=ypn)
                assert out["survival_available"] is True, (cn, ypt, ypn)
                assert out["one_year_survival_pct"] is not None


def test_the_interpretation_never_prints_none_as_a_number():
    out = shapiro_ncrt_predict(cn_category="cN1", ypt_category="ypT3",
                               ypn_category="ypN2")
    assert "None%" not in out["interpretation"]
    assert "publishes no survival at this total" in out["interpretation"]


def test_the_reason_for_the_gap_is_explained_not_just_flagged():
    """A bare None invites someone to fill it in. The note has to say why it is
    None and why interpolating would be wrong."""
    out = shapiro_ncrt_predict(**{**BASELINE, "ypn_category": "ypN2"})
    assert "Fig. 1 labels even totals only" in out["notes"]
    assert "inventing a number" in out["notes"]
    assert "9.6%" in out["notes"]


# ---------------------------------------------------------------------------
# Staging editions, the trap that would silently mis-score a patient.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad", ["cN2", "cN3", "N0", "cNx", "0"])
def test_a_non_sixth_edition_cn_category_is_refused(bad):
    """cN here is UICC TNM SIXTH edition, which is binary. A pipeline holding
    modern cN0-cN3 would otherwise pass cN2 and get either a crash or, worse,
    a silent mis-score. The error names the edition rather than just listing
    the accepted strings."""
    with pytest.raises(ValueError, match="6th edition"):
        shapiro_points(**{**BASELINE, "cn_category": bad})


@pytest.mark.parametrize("bad", ["ypT4", "ypTx", "T3", "ypT3a"])
def test_an_unknown_ypt_category_is_refused(bad):
    with pytest.raises(ValueError, match="ypt must be one of"):
        shapiro_points(**{**BASELINE, "ypt_category": bad})


@pytest.mark.parametrize("bad", ["ypN4", "ypNx", "N1", ""])
def test_an_unknown_ypn_category_is_refused(bad):
    with pytest.raises(ValueError, match="ypn must be one of"):
        shapiro_points(**{**BASELINE, "ypn_category": bad})


def test_ypt1_and_ypt2_give_the_same_answer():
    a = shapiro_ncrt_predict(**{**BASELINE, "ypt_category": "ypT1"})
    b = shapiro_ncrt_predict(**{**BASELINE, "ypt_category": "ypT2"})
    assert a["total_points"] == b["total_points"] == 2


# ---------------------------------------------------------------------------
# Scope: the limits that decide whether this model may be used at all.
# ---------------------------------------------------------------------------

def test_the_post_operative_limit_is_stated_on_every_call():
    """Two of three inputs are resection pathology. This cannot inform a
    decision about whether to operate, which is the question someone reaching
    for an 'oesophageal prognosis model' most often has."""
    out = shapiro_ncrt_predict(**BASELINE)
    assert "not a pre-operative model" in out["notes"]
    assert "cannot be run pre-operatively" in out["scope"]


def test_the_weak_discrimination_is_stated_on_every_call():
    """c-index 0.61-0.63. Shipping this without saying so would be the
    misleading part, not the model itself."""
    out = shapiro_ncrt_predict(**BASELINE)
    assert "discrimination is weak" in out["notes"].lower()
    assert "0.63" in out["notes"] and "0.61" in out["notes"]


def test_the_scope_says_a_better_model_exists_and_why_it_is_not_used():
    """AUGIS beats this substantially and is a random forest. A reader
    choosing a model deserves to know both halves of that."""
    out = shapiro_ncrt_predict(**BASELINE)
    assert "AUGIS" in out["scope"]
    assert "best IMPLEMENTABLE" in out["scope"]


def test_the_citation_names_the_figure_and_the_external_validation():
    out = shapiro_ncrt_predict(**BASELINE)
    assert "10.1002/bjs.10142" in out["citation"]
    assert "Fig. 1" in out["citation"]
    assert "29932887" in out["citation"]
