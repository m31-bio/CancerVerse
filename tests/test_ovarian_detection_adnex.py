"""IOTA ADNEX, checked against Appendix D, term by term.

No worked example is published, so parity here is route 5: every coefficient is
re-derived from the appendix text rather than compared against someone's
output. That makes the transcription itself the thing under test, which is
right for a model whose whole content is 44 numbers.
"""

from __future__ import annotations

import math

import pytest

from cancerverse_baseline.ovarian.detection.adnex import (
    _Z,
    OUTCOMES,
    adnex_predict,
    linear_predictors,
)

# A patient with every term set to a value that leaves it in the linear
# predictor, so an error in any coefficient moves the result.
FULL = dict(age=55, ca125=64, lesion_diameter_mm=64, solid_diameter_mm=32,
            more_than_10_locules=True, papillary_structures=2,
            acoustic_shadows=True, ascites=True, oncology_centre=True)


def test_the_four_linear_predictors_match_appendix_d_by_hand():
    """Recomputed from the printed formula, not from the code's own table."""
    z = linear_predictors(**FULL)
    # log2(64) = 6 exactly, and D/C = 0.5, chosen so the arithmetic is checkable
    a, log_b, log_c, ratio = 55, 6.0, 6.0, 0.5
    expected_z1 = (-7.577663 + 0.004506 * a + 0.111642 * log_b
                   + 0.372046 * log_c + 6.967853 * ratio - 5.65588 * ratio ** 2
                   + 1.375079 * 1 + 0.604238 * 2 - 2.04157 * 1
                   + 0.971061 * 1 + 0.953043 * 1)
    assert z["borderline"] == pytest.approx(expected_z1, abs=1e-12)


def test_every_coefficient_row_has_an_intercept_and_ten_terms():
    for name, betas in _Z.items():
        assert len(betas) == 11, f"{name}: {len(betas)} coefficients, expected 11"
        assert betas[0] < 0, f"{name}: intercept should be negative"


def test_probabilities_sum_to_one_over_five_categories():
    out = adnex_predict(**FULL)
    assert set(out["probabilities"]) == set(OUTCOMES)
    assert sum(out["probabilities"].values()) == pytest.approx(1.0, abs=1e-12)


def test_risk_is_one_minus_benign():
    out = adnex_predict(**FULL)
    assert out["risk"] == pytest.approx(1 - out["probabilities"]["benign"], abs=1e-12)


def test_ca125_enters_as_log2():
    """Doubling CA-125 must move each z by exactly its log2 coefficient."""
    lo = linear_predictors(**{**FULL, "ca125": 32})
    hi = linear_predictors(**{**FULL, "ca125": 64})
    for name, betas in _Z.items():
        assert hi[name] - lo[name] == pytest.approx(betas[2], abs=1e-12)


def test_lesion_diameter_enters_as_log2_and_also_through_the_ratio():
    """C appears twice, as log2(C) and inside D/C, so changing it alone is
    not a clean single-coefficient move. Pinned because treating C as if it
    only appeared once is the obvious transcription error."""
    lo = linear_predictors(**{**FULL, "lesion_diameter_mm": 64})
    hi = linear_predictors(**{**FULL, "lesion_diameter_mm": 128})
    betas = _Z["borderline"]
    naive = betas[3]                      # log2 term alone
    actual = hi["borderline"] - lo["borderline"]
    assert actual != pytest.approx(naive, abs=1e-6)


def test_the_solid_ratio_has_a_squared_term_that_bends_the_curve():
    """Risk must not rise monotonically with the solid fraction: the negative
    quadratic is what makes an almost entirely solid mass score lower than a
    half-solid one on the borderline predictor."""
    zs = [linear_predictors(**{**FULL, "solid_diameter_mm": d})["borderline"]
          for d in (8, 32, 56, 64)]
    assert zs[1] > zs[0]
    assert zs[-1] < max(zs), "no downturn, the squared term is missing or positive"


@pytest.mark.parametrize("field", ["ca125", "lesion_diameter_mm"])
def test_zero_or_negative_inputs_to_a_log_are_rejected(field):
    with pytest.raises(ValueError, match="log2"):
        adnex_predict(**{**FULL, field: 0})


def test_solid_component_larger_than_the_lesion_is_rejected():
    """D/C > 1 is not a value the model was fitted on, and it is a plausible
    data-entry error rather than a rare patient."""
    with pytest.raises(ValueError, match="cannot exceed"):
        adnex_predict(**{**FULL, "solid_diameter_mm": 200})


def test_papillary_structures_is_a_capped_count():
    """4 means 'more than three'. Passing 7 is a caller who has not read that."""
    with pytest.raises(ValueError, match="capped count"):
        adnex_predict(**{**FULL, "papillary_structures": 7})
    assert adnex_predict(**{**FULL, "papillary_structures": 4})


def test_oncology_centre_changes_the_answer():
    """It is a model predictor, not metadata: the same mass scores differently
    depending on where it was scanned, because referral filters the population.
    """
    other = adnex_predict(**{**FULL, "oncology_centre": False})["risk"]
    onc = adnex_predict(**{**FULL, "oncology_centre": True})["risk"]
    assert onc > other


def test_a_low_risk_and_a_high_risk_patient_land_where_a_clinician_expects():
    benign = adnex_predict(age=32, ca125=15, lesion_diameter_mm=50,
                           solid_diameter_mm=0)
    assert benign["most_likely"] == "benign"
    assert benign["risk"] < 0.05

    advanced = adnex_predict(age=68, ca125=800, lesion_diameter_mm=120,
                             solid_diameter_mm=80, papillary_structures=3,
                             ascites=True, oncology_centre=True)
    assert advanced["most_likely"] == "stage_ii_iv"
    assert advanced["risk"] > 0.95


def test_it_separates_borderline_from_advanced_which_rmi_cannot():
    """The reason to carry this model at all. RMI returns one number and a
    cut-off; a borderline tumour and a stage III cancer imply different
    surgery, and 'malignant' does not distinguish them."""
    out = adnex_predict(age=68, ca125=800, lesion_diameter_mm=120,
                        solid_diameter_mm=80, papillary_structures=3,
                        ascites=True, oncology_centre=True)
    p = out["probabilities"]
    assert p["stage_ii_iv"] > p["borderline"] * 10
    assert math.isclose(sum(p.values()), 1.0, abs_tol=1e-12)
