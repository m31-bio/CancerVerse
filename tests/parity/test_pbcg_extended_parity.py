"""Extended PBCG parity, route 1, against the authors' own published R.

The reference is Additional file 2 of the CC BY 4.0 article itself, not a
vendor's deployment, which makes this the best-provenanced check in the
library: the arithmetic being reproduced is the arithmetic the authors
published, under a licence that permits us to hold it.

`pbcg_extended_reference.R` loads the coefficient matrix from the same JSON the
Python package ships, so the two paths cannot drift apart while still agreeing.
That is deliberate: the thing under test is the *implementation*, the log2
transforms, the sub-model selection over 1,024 missing-data patterns, the
NA-skipping sum, not whether two copies of 8,192 numbers were transcribed
consistently.

Regenerate with:

    Rscript tests/parity/reference/pbcg_extended_reference.R \
        > tests/parity/reference/pbcg_extended_cases.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cancerverse_baseline.prostate.detection.pbcg_extended import (
    _BY_PATTERN,
    OPTIONAL,
    pbcg_extended_predict,
    rounded_like_reference,
)

CASES = json.loads(
    (Path(__file__).parent / "reference" / "pbcg_extended_cases.json").read_text()
)

ARGS = (
    "age",
    "psa",
    "race",
    "prior_biopsy",
    "dre_abnormal",
    "famhist_1",
    "famhist_2",
    "famhist_bca",
    "prostate_volume",
    "ari_use",
    "hispanic",
    "prior_psa",
)


def _kwargs(case: dict) -> dict:
    return {k: case[k] for k in ARGS if case.get(k) is not None}


@pytest.mark.parity
@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c['age']}y_psa{c['psa']}")
def test_matches_the_published_r(case):
    got = pbcg_extended_predict(**_kwargs(case))["percent"]
    assert got == pytest.approx(case["percent"], abs=1e-9), (
        f"{got} vs published {case['percent']}"
    )


@pytest.mark.parity
def test_every_count_of_supplied_predictors_is_exercised():
    """The sub-model selection is the model. A parity suite that only ever
    supplies the same predictors tests one of 1,024 fitted models."""
    counts = {sum(1 for k in OPTIONAL if c.get(k) is not None) for c in CASES}
    assert counts >= set(range(0, 11)), (
        f"missing predictor counts: {sorted(set(range(11)) - counts)}"
    )


def test_all_1024_sub_models_are_present_and_distinct():
    assert len(_BY_PATTERN) == 1024
    intercepts = {row[0] for row in _BY_PATTERN.values()}
    # not a hard requirement of the model, but 1,024 identical intercepts would
    # mean the extraction collapsed the matrix
    assert len(intercepts) > 900, f"only {len(intercepts)} distinct intercepts"


def test_supplying_a_predictor_selects_a_different_sub_model():
    """Not an imputation model: adding a predictor changes which fitted model
    runs, so the answer may move in either direction."""
    bare = pbcg_extended_predict(age=65, psa=5.0)
    with_dre = pbcg_extended_predict(age=65, psa=5.0, dre_abnormal=0)
    assert bare["sub_model"] != with_dre["sub_model"]
    assert bare["percent"] != pytest.approx(with_dre["percent"], abs=1e-6)


def test_psa_enters_as_log2():
    """Doubling PSA must move the linear predictor by exactly one psa beta."""
    a = pbcg_extended_predict(age=65, psa=4.0)["linear_predictor"]
    b = pbcg_extended_predict(age=65, psa=8.0)["linear_predictor"]
    row = _BY_PATTERN[tuple([False] * 10)]
    beta_psa = row[2]
    assert (b - a) == pytest.approx(beta_psa, abs=1e-9)


def test_age_and_psa_are_mandatory():
    with pytest.raises(TypeError):
        pbcg_extended_predict(psa=5.0)
    with pytest.raises(ValueError):
        pbcg_extended_predict(age=65, psa=0)


def test_rounded_output_reproduces_the_reference_shape():
    out = rounded_like_reference(age=65, psa=5.0)
    assert set(out) == {"Other", "Risk of High Grade Cancer"}
    assert out["Other"] + out["Risk of High Grade Cancer"] == 100
    assert isinstance(out["Risk of High Grade Cancer"], int)


def test_rounding_is_the_references_property_not_the_models():
    """`predict` must not round. The published function ends in `round()`,
    which turns a 46.786% risk into 47%, a property of that tool's display,
    and not something a caller should be given silently."""
    exact = pbcg_extended_predict(age=65, psa=5.0)["percent"]
    assert exact != round(exact)


def test_the_ancestry_term_changes_sign_between_sub_models():
    """Pinned because it is the model's sharpest trap, and it is silent.

    The African-ancestry coefficient is protective in 412 of the 1,024
    sub-models and harmful in 100. Which one a patient lands in depends on
    which optional fields the caller supplied, so adding information can flip
    the term. If a future coefficient update makes this uniform, this test
    fails and the warning in the module docstring and the registry's
    scope_note should be removed with it, rather than being left in place
    describing something that is no longer true.
    """
    from cancerverse_baseline.prostate.detection.pbcg_extended import _COLUMNS

    i = _COLUMNS.index("race")
    betas = [r[i] for r in _BY_PATTERN.values() if r[i] is not None]
    negative = sum(1 for b in betas if b < 0)
    positive = sum(1 for b in betas if b > 0)
    assert negative and positive, (
        "the ancestry term no longer changes sign; remove the warnings that say it does"
    )
    assert (negative, positive) == (412, 100), (
        f"sign split moved to {negative} protective / {positive} harmful: "
        "update the module docstring and scope_note, which quote these counts"
    )
