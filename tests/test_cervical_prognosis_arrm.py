"""ARRM (Cibula 2021), the contract, not the arithmetic.

The coefficients and the outcome grid are checked in
tests/parity/test_cibula_arrm_parity.py against the paper and against the
authors' own deployment. This file checks the things a parity test cannot: how
the module behaves when a caller gives it something the paper did not
anticipate, and whether the two dangerous defaults stay visible.

The dangerous defaults are the reason this file is longer than the model.
Table 2 pools "not assessed" with "negative" for pelvic nodes and for LVSI, so
a patient who never had a lymphadenectomy scores identically to a node-negative
one. That is the published model and the module reproduces it, but it means a
missing field is silently *optimistic*, which is the wrong direction for a
surveillance tool to fail in. Every test below that touches `None` exists to
keep that pooling loud rather than quiet.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.cervical.prognosis.arrm import (
    AXIS,
    DISEASE,
    MODEL_ID,
    POINTS,
    arrm_points,
    band_for,
    cibula_arrm_predict,
    diameter_level,
    grade_level,
    node_level,
)

#: A patient with every risk factor at its reference level.
BASELINE = dict(
    histotype="squamous", tumour_diameter_cm=0.3, grade=1,
    positive_pelvic_nodes=0, lvsi=False,
)


def test_the_result_identifies_itself_to_the_registry():
    out = cibula_arrm_predict(**BASELINE)
    assert (out["model_id"], out["axis"], out["disease"]) == (
        MODEL_ID, AXIS, DISEASE) == ("cibula_arrm", "prognosis", "cervical")


def test_risk_is_none_because_this_model_does_not_produce_a_probability():
    """Every other model in this library returns a probability under `risk`.
    ARRM returns a points score and a band lookup, and pretending otherwise
    would let it be averaged or thresholded as though it were calibrated.
    """
    assert cibula_arrm_predict(**BASELINE)["risk"] is None


# --------------------------------------------------------------------------
# The banding functions, at their cut-points.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cm,expected",
    [(0.0, "<0.5cm"), (0.49, "<0.5cm"), (0.5, "0.5-1.99cm"),
     (1.99, "0.5-1.99cm"), (2.0, "2-3.99cm"), (3.99, "2-3.99cm"),
     (4.0, ">=4cm"), (12.0, ">=4cm")],
)
def test_diameter_cut_points_are_closed_on_the_left(cm, expected):
    """The paper's bands are < 0.5, 0.5-1.99, 2-3.99, >= 4 cm. A 2.0 cm tumour
    is in the third band, not the second, 20 points against 10, which is a
    band change for many patients.
    """
    assert diameter_level(cm) == expected


def test_diameter_is_centimetres_not_millimetres():
    """The deployed calculator labels the same four levels in mm (< 5, 5-19,
    20-39, >= 40) and this module takes cm, as the paper does. A caller who
    passes 20 meaning millimetres gets the >= 4 cm level, which is the safe
    direction to be wrong but is still wrong; there is no way to detect it, so
    the unit is pinned here and named in the signature.
    """
    assert diameter_level(2.0) == "2-3.99cm"
    assert diameter_level(20.0) == ">=4cm"


def test_a_negative_diameter_is_refused():
    with pytest.raises(ValueError, match="must be >= 0"):
        diameter_level(-1.0)


@pytest.mark.parametrize(
    "n,expected",
    [(0, "0_or_not_assessed"), (1, "1"), (2, "2"), (3, ">=3"), (17, ">=3"),
     (None, "0_or_not_assessed")],
)
def test_node_levels_including_the_pooling_of_not_assessed(n, expected):
    assert node_level(n) == expected


def test_a_fractional_or_negative_node_count_is_refused():
    for bad in (-1, 1.5):
        with pytest.raises(ValueError, match="non-negative whole number"):
            node_level(bad)


@pytest.mark.parametrize("grade", [1, 2, 3, "1", "2", "3"])
def test_grade_accepts_the_three_published_levels_as_int_or_str(grade):
    assert grade_level(grade) in POINTS["grade"]


@pytest.mark.parametrize("bad", [0, 4, None, "unknown", "not assessed", "G2"])
def test_an_unknown_grade_is_refused_rather_than_defaulted(bad):
    """This is the asymmetry that matters. Nodes and LVSI have a published
    "not assessed" level and so accept None; grade does not. The authors
    multiply imputed missing grade when fitting, which cannot be reproduced for
    one patient, so guessing grade 1 here would invent a favourable value the
    paper never sanctioned.
    """
    with pytest.raises(ValueError, match="no.*not assessed.*level for grade"):
        grade_level(bad)


@pytest.mark.parametrize(
    "given,expected",
    [("squamous", "squamous"), ("SCC", "squamous"), ("Squamous Cell", "squamous"),
     ("adenocarcinoma", "adenocarcinoma"), ("Adenosquamous", "adenosquamous"),
     ("adenosquamous carcinoma", "adenosquamous"),
     ("neuroendocrine", "neuroendocrine"), ("other", "other")],
)
def test_histotype_aliases(given, expected):
    assert arrm_points(**{**BASELINE, "histotype": given})["levels"]["histotype"] == expected


def test_the_ambiguous_abbreviation_adeno_is_refused():
    """"adeno" is equally close to adenocarcinoma (7 points) and adenosquamous
    (11 points). Guessing between them would be a 4-point silent error, so the
    alias table deliberately omits it.
    """
    with pytest.raises(ValueError, match="histotype must be one of"):
        cibula_arrm_predict(**{**BASELINE, "histotype": "adeno"})


# --------------------------------------------------------------------------
# The pooling of "not assessed", and whether the caller is told.
# --------------------------------------------------------------------------


def test_unassessed_nodes_score_exactly_like_node_negative():
    """The published model's choice, reproduced deliberately."""
    unknown = cibula_arrm_predict(**{**BASELINE, "positive_pelvic_nodes": None})
    negative = cibula_arrm_predict(**{**BASELINE, "positive_pelvic_nodes": 0})
    assert unknown["score"] == negative["score"]
    assert unknown["points"] == negative["points"]


def test_but_the_caller_is_told_every_time_it_happens():
    """Identical scores, different notes. The note is the only thing standing
    between "we did not look" and "we looked and it was clean".
    """
    unknown = cibula_arrm_predict(**{**BASELINE, "positive_pelvic_nodes": None})
    negative = cibula_arrm_predict(**{**BASELINE, "positive_pelvic_nodes": 0})
    assert "pelvic nodes not assessed" in unknown["notes"]
    assert "pelvic nodes not assessed" not in negative["notes"]


def test_the_same_holds_for_lvsi_independently():
    unknown = cibula_arrm_predict(**{**BASELINE, "lvsi": None})
    assert unknown["score"] == cibula_arrm_predict(**BASELINE)["score"]
    assert "LVSI not assessed" in unknown["notes"]


def test_both_optional_fields_default_to_not_assessed_and_both_are_flagged():
    """The signature defaults are None for both, which reproduces the paper's
    pooling. A caller who supplies only the three required fields therefore
    gets the optimistic reading, and must be told twice.
    """
    out = cibula_arrm_predict(histotype="squamous", tumour_diameter_cm=0.3, grade=1)
    assert out["score"] == 0
    assert "pelvic nodes not assessed" in out["notes"]
    assert "LVSI not assessed" in out["notes"]


# --------------------------------------------------------------------------
# Scoring end to end.
# --------------------------------------------------------------------------


def test_the_reference_patient_scores_zero_and_the_worst_scores_one_hundred():
    assert cibula_arrm_predict(**BASELINE)["score"] == 0
    worst = cibula_arrm_predict(
        histotype="neuroendocrine", tumour_diameter_cm=6.0, grade=3,
        positive_pelvic_nodes=5, lvsi=True,
    )
    assert worst["score"] == 100
    assert worst["band"] == 4


def test_points_are_additive_and_the_breakdown_sums_to_the_score():
    """The breakdown is returned so a clinician can see which factor drove the
    band. If it did not sum to the score it would be decoration.
    """
    out = cibula_arrm_predict(
        histotype="adenocarcinoma", tumour_diameter_cm=3.0, grade=2,
        positive_pelvic_nodes=1, lvsi=True,
    )
    assert out["points"] == {
        "histotype": 7, "tumour_diameter": 21, "grade": 5,
        "positive_pelvic_nodes": 5, "lvsi": 10,
    }
    assert sum(out["points"].values()) == out["score"] == 48
    assert out["band"] == 2  # 26-50


def test_worsening_any_single_factor_never_lowers_the_score():
    """Every beta in Table 2 is positive, so the score is monotone in each
    input. Non-monotonicity here would mean a level was mis-ordered, the
    failure mode that bit the colorectal response model, where T stage really
    is non-monotone and the paper hid it.
    """
    base = cibula_arrm_predict(**BASELINE)["score"]
    for change in (
        {"histotype": "adenocarcinoma"}, {"histotype": "adenosquamous"},
        {"histotype": "other"}, {"histotype": "neuroendocrine"},
        {"tumour_diameter_cm": 1.0}, {"tumour_diameter_cm": 3.0},
        {"tumour_diameter_cm": 5.0}, {"grade": 2}, {"grade": 3},
        {"positive_pelvic_nodes": 1}, {"positive_pelvic_nodes": 2},
        {"positive_pelvic_nodes": 9}, {"lvsi": True},
    ):
        assert cibula_arrm_predict(**{**BASELINE, **change})["score"] > base, change


def test_histotype_is_the_single_largest_lever_in_the_model():
    """Neuroendocrine alone is 33 points, a third of the whole scale, and more
    than the largest tumour-diameter step. A patient whose only risk factor is
    neuroendocrine histology lands in band 2, two bands above an otherwise
    identical squamous patient.
    """
    assert max(POINTS["histotype"].values()) == 33
    assert max(POINTS["histotype"].values()) > max(POINTS["tumour_diameter"].values())
    out = cibula_arrm_predict(**{**BASELINE, "histotype": "neuroendocrine"})
    assert out["score"] == 33 and out["band"] == 2


def test_band_boundaries_are_inclusive_on_both_ends():
    assert band_for(0)["index"] == 0
    assert band_for(1)["index"] == 1
    assert band_for(25)["index"] == 1
    assert band_for(26)["index"] == 2
    assert band_for(50)["index"] == 2
    assert band_for(51)["index"] == 3
    assert band_for(75)["index"] == 3
    assert band_for(76)["index"] == 4
    assert band_for(100)["index"] == 4


@pytest.mark.parametrize("score", [-1, 101])
def test_a_score_outside_the_scale_is_refused(score):
    with pytest.raises(ValueError, match="outside 0-100"):
        band_for(score)


# --------------------------------------------------------------------------
# What the caller is handed back about the band.
# --------------------------------------------------------------------------


def test_the_outcome_is_named_as_the_derivation_cohorts_and_not_a_prediction():
    """These are Kaplan-Meier estimates over the band the patient falls in, not
    an individualised probability. The key names say so, and they are pinned:
    renaming `observed_dfs_in_derivation` to `dfs` would turn a group statistic
    into something that reads like a personal forecast.
    """
    out = cibula_arrm_predict(**BASELINE)
    for key in ("band_n_in_derivation", "band_recurrences_in_derivation",
                "observed_dfs_in_derivation", "observed_dfs_ci_in_derivation",
                "annual_recurrence_risk_in_derivation"):
        assert key in out
    assert "not an individual prediction" in out["notes"]


def test_the_annual_risk_is_conditional_and_says_so():
    """Year 3 is the risk for someone already recurrence-free for two years,
    not a cumulative three-year risk. Reading it as cumulative understates late
    risk in the low bands and overstates it nowhere useful.
    """
    out = cibula_arrm_predict(**BASELINE)
    assert "conditional on being recurrence-free" in out["notes"]
    assert len(out["annual_recurrence_risk_in_derivation"]) == 5


@pytest.mark.parametrize(
    "patient",
    [BASELINE,
     {**BASELINE, "grade": 2},                                   # band 1
     {**BASELINE, "histotype": "neuroendocrine"},                # band 2
     {**BASELINE, "histotype": "neuroendocrine",
      "tumour_diameter_cm": 5.0, "lvsi": True},                  # band 3
     {"histotype": "neuroendocrine", "tumour_diameter_cm": 6.0,
      "grade": 3, "positive_pelvic_nodes": 5, "lvsi": True}],    # band 4
    ids=["band0", "band1", "band2", "band3", "band4"],
)
def test_the_confidence_intervals_bracket_the_estimate(patient):
    out = cibula_arrm_predict(**patient)
    for point, (lo, hi) in zip(out["observed_dfs_in_derivation"],
                               out["observed_dfs_ci_in_derivation"],
                               strict=True):
        assert lo <= point <= hi, f"band {out['band']}: {lo} <= {point} <= {hi}"


def test_the_top_band_reports_none_rather_than_zero_for_the_empty_years():
    """13 patients, 12 recurrences, and the paper stops its landmark analysis
    at year three. The arithmetic returns 0.0% for years four and five because
    nobody is left, and 0.0% would read as "no risk".
    """
    out = cibula_arrm_predict(
        histotype="neuroendocrine", tumour_diameter_cm=6.0, grade=3,
        positive_pelvic_nodes=5, lvsi=True,
    )
    arrm = out["annual_recurrence_risk_in_derivation"]
    assert arrm[:3] == [53.8, 66.7, 50.0]
    assert arrm[3:] == [None, None]
    assert out["arrm_reliable_through_year"] == 3
    assert "stops the landmark analysis" in out["notes"]


def test_the_interpretation_omits_the_years_it_has_no_number_for():
    """A rendered sentence that said "year 4 None%" would be worse than one
    that stops at year three.
    """
    out = cibula_arrm_predict(
        histotype="neuroendocrine", tumour_diameter_cm=6.0, grade=3,
        positive_pelvic_nodes=5, lvsi=True,
    )
    assert "None" not in out["interpretation"]
    assert "year 3 50.0%" in out["interpretation"]
    assert "year 4" not in out["interpretation"]


def test_the_module_does_not_attribute_an_action_threshold_to_the_authors():
    """The authors explicitly declined to set one, and saying otherwise would
    put a clinical recommendation in their mouths.

    The Discussion reads: "Surveillance strategy can be consequently adopted
    individually using the preferred threshold for an acceptable annual risk."
    1% appears in the Abstract descriptively, the lowest group stays under it
    throughout and the middle groups fall under it at years three and four,
    and nowhere as a rule for what to do. An earlier draft of this module said
    "the paper's worked example takes 1% annual risk as the threshold for
    continued institutional follow-up", which is a recommendation the paper
    does not make and a worked example it does not contain.
    """
    text = cibula_arrm_predict(**BASELINE)["interpretation"]
    assert "sets no action threshold" in text
    assert "preferred threshold for an acceptable annual risk" in text
    assert "not a recommendation the authors make" in text


def test_the_citation_and_scope_travel_with_the_result():
    out = cibula_arrm_predict(**BASELINE)
    assert "10.1016/j.ejca.2021.09.008" in out["citation"]
    assert "Table 2" in out["citation"]
    assert "primary surgery" in out["scope"]
    assert "chemoradiation" in out["scope"]
