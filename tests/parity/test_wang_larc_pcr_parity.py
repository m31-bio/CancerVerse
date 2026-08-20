"""Parity: our Wang 2024 pCR implementation vs. the authors' own calculator.

Why this test exists
--------------------
Cancer Med 2024;13(11):e7251 cannot produce a probability. It prints odds
ratios (Table 4) and the nomogram's points formula (Results 3.3), but the
intercept and the points-to-probability axis appear nowhere except inside
Figure 3A as a drawn scale. There is no supplement, no erratum and no source
release, so neither of the usual routes was open: no reference implementation
to run, and no worked example to reproduce.

What was open was the authors' own deployed model at
pcrpredict.shinyapps.io/LARC2/, whose URL the article itself prints. It is a
`DynNom` app, and `DynNom` ships a "Model Summary" tab that prints the fitted
`rms::lrm` object, the entire coefficient table, intercept included. That
made this Route A (recover the model) rather than Route B (probe outputs), so
the implementation is pinned everywhere and not merely at the probed points.
The captured printout is committed at reference/wang_larc_pcr_model_summary.txt
and `test_the_committed_model_summary_still_matches_our_coefficients` asserts
our constants against it character by character.

The 13 probed cases below are therefore a check on the transcription and on
the coding decisions the printout leaves implicit, above all which level is
the reference for T stage (cT2, which the paper's ordinal presentation of T
stage actively hides).

Both fixtures are offline. reference/wang_larc_pcr_fetch.py regenerates them
and documents how to drive a Shiny app from a script.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from cancerverse_baseline.colorectal.response.wang_larc_pcr import (
    COEF,
    wang_larc_pcr_predict,
)

REFERENCE = Path(__file__).parent / "reference"
CASES_FILE = REFERENCE / "wang_larc_pcr_cases.json"
SUMMARY_FILE = REFERENCE / "wang_larc_pcr_model_summary.txt"

# The app prints probabilities to 3 decimals. A displayed 0.497 means
# [0.4965, 0.4975), so 0.0005 is the exact rounding half-width; 0.001 absorbs
# any rounding convention. The smallest coefficient in the model (cT4, 0.0587)
# moves the reference patient by 0.0147 in probability, an order of magnitude
# above this tolerance, so no real coefficient error survives it.
TOLERANCE = 0.001


def _fixture() -> dict:
    return json.loads(CASES_FILE.read_text())


def _cases() -> list[dict]:
    return _fixture()["cases"]


def _ours(case: dict) -> float:
    return wang_larc_pcr_predict(
        n_stage=case["n_stage"],
        t_stage=case["t_stage"],
        mri_emvi_positive=case["mri_emvi"] == "Positive",
        total_neoadjuvant_therapy=case["tnt"] == "Yes",
        histopathology=case["histopathology"],
        cea_ng_ml=case["cea_ng_ml"],
    )["p_pcr"]


@pytest.mark.parametrize(
    "case", _cases(),
    ids=lambda c: f"{c['n_stage']}-{c['t_stage']}-cea{c['cea_ng_ml']:g}",
)
def test_matches_the_authors_hosted_calculator(case):
    ours = _ours(case)
    assert ours == pytest.approx(case["prediction"], abs=TOLERANCE), (
        f"{case}: ours {ours:.4f} vs app {case['prediction']}"
    )


def test_the_committed_model_summary_still_matches_our_coefficients():
    """The printout IS the equation source. Pin every constant to it.

    If someone edits a coefficient in the module, this fails; if someone
    refreshes the fixture from a changed deployment, this fails too, which is
    the point, the app is a live artifact and our copy is a dated snapshot.
    """
    text = SUMMARY_FILE.read_text()
    assert "lrm(formula = pCR ~" in text, "not an rms::lrm printout"

    printed = {}
    for name in COEF:
        # The R level names contain regex metacharacters ("/", "-"), and the
        # printout pads each name out to a fixed column width.
        match = re.search(
            rf"^{re.escape(name)}\s+(-?\d+\.\d+)\s*$", text, re.MULTILINE
        )
        assert match, f"{name!r} not found in the committed printout"
        printed[name] = float(match.group(1))

    assert printed == COEF
    # And nothing extra: d.f. 9 plus the intercept is exactly our ten terms.
    assert "d.f.             9" in text
    assert len(COEF) == 10


def test_the_summary_confirms_this_is_the_papers_training_fit():
    """Three numbers tie the deployed app to Cancer Med 2024;13(11):e7251:
    n = 1579 with 350 events (the paper's 350/1579, 22.2%, pCR rate) and
    C = 0.737, which rounds to its published 0.73 (95% CI 0.70-0.75)."""
    text = SUMMARY_FILE.read_text()
    assert "Obs          1579" in text
    assert re.search(r"^ 0           1229", text, re.MULTILINE)
    assert re.search(r"^ 1            350", text, re.MULTILINE)
    assert "C       0.737" in text


def test_the_fixture_exercises_every_level_of_every_covariate():
    """A fixture missing a level cannot detect a wrong coefficient on it, and
    cannot detect a wrong REFERENCE level either."""
    cases = _cases()
    assert {c["n_stage"] for c in cases} == {"cN0", "cN1", "cN2"}
    assert {c["t_stage"] for c in cases} == {"cT2", "cT3", "cT4", "cTcT1"}
    assert {c["mri_emvi"] for c in cases} == {"Negative", "Positive"}
    assert {c["tnt"] for c in cases} == {"No", "Yes"}
    assert len({c["histopathology"] for c in cases}) == 2
    # Both ends of the calculator's own CEA slider.
    assert min(c["cea_ng_ml"] for c in cases) == 0.0
    assert max(c["cea_ng_ml"] for c in cases) == 24.0


def test_the_hosted_tool_also_ranks_ct3_above_ct2():
    """T stage is non-monotone in the fitted model: relative to the cT2
    reference, cT3 is +0.5773 and cT4 only +0.0587, so the app says a cT3
    tumour is MORE likely to achieve pCR than a cT2 one. The paper hides this
    behind a tidy ordinal "15.0 points per T level".

    This is a property of the published model, not of our transcription, the
    authors' own calculator returns 0.568 for the cT3 patient against 0.497
    for the otherwise-identical cT2 reference. Pinned so nobody later reorders
    the coefficients to make T stage behave.
    """
    varying_t = [
        c for c in _cases()
        if c["cea_ng_ml"] == 5 and c["n_stage"] == "cN0"
        and c["mri_emvi"] == "Negative" and c["tnt"] == "No"
        and c["histopathology"] == "Adenocarcinoma"
    ]
    by_t = {c["t_stage"]: c for c in varying_t}
    assert {"cT2", "cT3", "cT4"} <= set(by_t)
    assert by_t["cT3"]["prediction"] > by_t["cT2"]["prediction"], (
        "the app itself ranks cT3 above the cT2 reference"
    )
    assert by_t["cT3"]["prediction"] > by_t["cT4"]["prediction"]
    for case in varying_t:
        assert _ours(case) == pytest.approx(case["prediction"], abs=TOLERANCE)
