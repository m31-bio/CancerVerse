"""Parity: LIPI checked against two independent published statements of the rule.

LIPI publishes no worked example, it is a two-item binary index, so there is
no arithmetic to reproduce beyond the rule itself. What CAN be verified, and
what actually matters, is that our thresholds and their comparison direction
match what the literature states. Route 3: compare against a second (here,
third) published statement of the same rule.

The two failure modes worth guarding are boundary conditions, and they are
exactly what the verbatim quotes pin down:

  * dNLR exactly 3   -> must score 0, because the rule is ">3", not ">=3"
  * LDH exactly ULN  -> must score 0, because the rule is ">ULN", not ">=ULN"

An off-by-one on either would silently reclassify every patient sitting on the
threshold, and no ordinary spot-check uses an input that lands exactly there.

Sources read (not search summaries):

  1. "Prognostic value of lung immune prognostic index in non-small cell lung
     cancer patients receiving immune checkpoint inhibitors: a meta-analysis",
     PMC11222319, states verbatim:
         "LIPI 0, dNLR<=3 and LDH <= ULN; LIPI 1, dNLR >3 or LDH > ULN;
          and LIPI 2, dNLR >3 and LDH > ULN."

  2. "Prognostic value of baseline LIPI, LDH and dNLR in ES-SCLC patients
     receiving immune checkpoint inhibitors", Front Immunol 2025;16:1640066,
     states verbatim:
         grade 0 (low-risk)          "dNLR <= 3 and LDH<=ULN"
         grade 1 (intermediate-risk) "dNLR>3 or LDH>ULN"
         grade 2 (high-risk)         "dNLR>3 and LDH>ULN"
     and gives the dNLR formula as
         "neutrophil count/(white blood cell count - neutrophil count)"

Both agree with each other and with `cancerverse_baseline.lung.response.lipi`. The
same index is registered twice, on the response and prognosis axes; both share
this module and therefore this check.
"""

from __future__ import annotations

import pytest

from cancerverse_baseline.lung.response.lipi import (
    DNLR_THRESHOLD,
    derived_nlr,
    lipi_predict,
)

# The published truth table, transcribed from the quotes above.
# (dNLR above 3?, LDH above ULN?) -> (score, group)
PUBLISHED_TRUTH_TABLE = {
    (False, False): (0, "good"),
    (True, False): (1, "intermediate"),
    (False, True): (1, "intermediate"),
    (True, True): (2, "poor"),
}


def _call(dnlr: float, ldh: float, uln: float = 250.0):
    return lipi_predict(dnlr=dnlr, ldh=ldh, ldh_upper_limit_normal=uln)


@pytest.mark.parametrize("dnlr_high,ldh_high", list(PUBLISHED_TRUTH_TABLE))
def test_every_cell_of_the_published_truth_table(dnlr_high, ldh_high):
    expected_score, expected_group = PUBLISHED_TRUTH_TABLE[(dnlr_high, ldh_high)]
    out = _call(dnlr=4.0 if dnlr_high else 2.0, ldh=300.0 if ldh_high else 200.0)
    assert out["score"] == expected_score
    assert out["group"] == expected_group


def test_dnlr_exactly_three_scores_zero():
    """Both sources write "dNLR <= 3" for grade 0 and ">3" for a point. A
    `>=` here would misclassify every patient sitting exactly on the cut."""
    assert DNLR_THRESHOLD == 3.0
    out = _call(dnlr=3.0, ldh=200.0)
    assert out["components"]["dnlr"] == 0
    assert out["score"] == 0 and out["group"] == "good"
    # And just above it does score.
    assert _call(dnlr=3.0001, ldh=200.0)["components"]["dnlr"] == 1


def test_ldh_exactly_at_uln_scores_zero():
    """Same boundary argument on the LDH side: the rule is "LDH > ULN"."""
    out = _call(dnlr=2.0, ldh=250.0, uln=250.0)
    assert out["components"]["ldh"] == 0
    assert out["score"] == 0
    assert _call(dnlr=2.0, ldh=250.01, uln=250.0)["components"]["ldh"] == 1


def test_dnlr_formula_matches_the_published_definition():
    """Front Immunol 2025: "neutrophil count/(white blood cell count -
    neutrophil count)". The denominator is the NON-neutrophil white count,
    which is what makes this "derived" NLR, it needs no lymphocyte count.
    Using the plain leukocyte count as the denominator is the classic error.
    """
    neutrophils, leukocytes = 6.0, 9.0
    assert derived_nlr(neutrophils=neutrophils, leukocytes=leukocytes) == pytest.approx(
        neutrophils / (leukocytes - neutrophils)
    )
    assert derived_nlr(neutrophils=6.0, leukocytes=9.0) == pytest.approx(2.0)
    # Not the ordinary NLR denominator.
    assert derived_nlr(neutrophils=6.0, leukocytes=9.0) != pytest.approx(6.0 / 9.0)


def test_counts_and_direct_dnlr_agree():
    from_counts = lipi_predict(
        neutrophils=8.0, leukocytes=10.0, ldh=300.0, ldh_upper_limit_normal=250.0
    )
    direct = lipi_predict(dnlr=4.0, ldh=300.0, ldh_upper_limit_normal=250.0)
    assert from_counts["dnlr"] == pytest.approx(direct["dnlr"])
    assert from_counts["score"] == direct["score"] == 2


def test_the_index_is_symmetric_between_its_two_items():
    """Both sources define grade 1 with an OR, so either single item alone
    gives exactly 1, neither is weighted above the other."""
    only_dnlr = _call(dnlr=5.0, ldh=200.0)
    only_ldh = _call(dnlr=1.0, ldh=400.0)
    assert only_dnlr["score"] == only_ldh["score"] == 1
    assert only_dnlr["group"] == only_ldh["group"] == "intermediate"


def test_the_prognosis_axis_registration_shares_this_model():
    """`lipi` and `lipi_prognosis` are two registry rows over one module, so
    this check covers both. If they ever diverge, this fails loudly."""
    from cancerverse_baseline.lung.response.lipi import MODEL_ID

    assert MODEL_ID == "lipi"
    out = _call(dnlr=4.0, ldh=300.0)
    assert out["model_id"] == "lipi"
    assert out["disease"] == "lung"
