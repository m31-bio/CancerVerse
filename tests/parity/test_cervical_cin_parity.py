"""Parity: cervical CIN2+/CIN3+ models vs. the paper's own supplement workbook.

Xia et al., BMC Medicine 2021;19:237 publishes no worked example, no calibration
table and no cross-tabulation of predicted vs. observed risk — checked, and it
does not. So there is no output to reproduce.

What it does publish is the coefficient table as a real .xlsx (Additional file 1,
Table S1), not as a figure. That makes a stronger check available than a worked
example would have been: an independently downloaded, machine-readable copy of
the source table compared to our shipped constants term by term, at ZERO
tolerance, across all four nested models.

A worked example verifies the model at one point in the input space. This
verifies every coefficient in it.

    56 / 56 coefficients match exactly.

Fixture: reference/cervical_table_s1.json, captured by cervical_s1_extract.py
(which also records why PMC's mirror path returns HTML instead of the workbook).
This test is offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mayo_baseline.cervical.detection.cin_risk import MODELS

S1_FILE = Path(__file__).parent / "reference" / "cervical_table_s1.json"

# our MODELS key -> the block heading used in Table S1
MODEL_BLOCKS = {
    "base": "Base model",
    "e6": "Base Model+E6",
    "genotyping": "Base Model+Genotyping",
    "full": "Base Model+E6+Genotyping",
}

# Table S1 spells two terms differently from our dict keys.
TERM_ALIASES = {"Intercept": "intercept", "Age": "age"}


def _supplement():
    return json.loads(S1_FILE.read_text())


def _block(name: str) -> dict[str, float]:
    raw = _supplement()[MODEL_BLOCKS[name]]
    return {TERM_ALIASES.get(k, k): v for k, v in raw.items()}


def _pairs():
    out = []
    for ours_key in MODEL_BLOCKS:
        for term, value in _block(ours_key).items():
            out.append((ours_key, term, value))
    return out


@pytest.mark.parametrize(
    "model,term,published", _pairs(), ids=lambda v: v if isinstance(v, str) else ""
)
def test_every_coefficient_matches_table_s1_exactly(model, term, published):
    ours = MODELS[model].get(term)
    assert ours is not None, f"{model}: we have no term {term!r}"
    assert ours == published, f"{model}.{term}: ours {ours} vs Table S1 {published}"


@pytest.mark.parametrize("model", list(MODEL_BLOCKS))
def test_we_ship_no_terms_the_supplement_does_not_have(model):
    """The other direction. An extra term would be silently added risk."""
    extra = sorted(set(MODELS[model]) - set(_block(model)))
    assert not extra, f"{model} has terms absent from Table S1: {extra}"


@pytest.mark.parametrize("model", list(MODEL_BLOCKS))
def test_term_counts_agree(model):
    assert len(MODELS[model]) == len(_block(model))


def test_all_fifty_six_coefficients_are_covered():
    """Guards the fixture itself: if a future capture silently truncated a
    block, the parametrized test above would just run fewer cases and still
    pass green."""
    assert sum(len(_block(m)) for m in MODEL_BLOCKS) == 56
    assert len(_supplement()) == 4


def test_the_negative_age_coefficient_is_real_in_every_model():
    """Age carries a small NEGATIVE coefficient in all four models. It looks
    like a sign error and is not: conditional on hrHPV and cytology, older
    women in this screening population were at slightly lower CIN risk, because
    prevalent HPV in younger women is more often transient but still counts as
    positive. Pinned so nobody "corrects" it."""
    for model in MODEL_BLOCKS:
        assert _block(model)["age"] < 0
        assert MODELS[model]["age"] < 0


def test_cytology_terms_separate_low_grade_from_high_grade_in_every_model():
    """An independent shape check on top of the value-by-value comparison: a
    pair of terms transposed identically in both sources would survive the
    coefficient check but not this one.

    The claim deliberately stops where the data stops. Every low-grade term
    sits below every high-grade term in all four models, and SCC/ADC is always
    the largest. But ASC-US and LSIL SWAP between models (LSIL is above ASC-US
    in base and genotyping, below it in e6 and full), so they cannot be ordered
    against each other — they are adjacent low-grade categories whose estimates
    overlap. Asserting a fixed order there would be our invention, not the
    paper's finding.
    """
    low = ["ASC-US", "LSIL"]
    high = ["ASC-H", "AGC", "HSIL/AIS", "SCC/ADC"]
    for model in MODEL_BLOCKS:
        coefs = MODELS[model]
        assert "NILM" not in coefs, "NILM is the reference level; it must carry no term"
        assert max(coefs[c] for c in low) < min(coefs[c] for c in high), model
        assert coefs["SCC/ADC"] == max(coefs[c] for c in low + high), model


def test_the_low_grade_pair_really_does_swap():
    """Pins the swap itself, so the weaker claim above is not mistaken for
    laziness by a future reader."""
    assert MODELS["base"]["LSIL"] > MODELS["base"]["ASC-US"]
    assert MODELS["e6"]["LSIL"] < MODELS["e6"]["ASC-US"]
