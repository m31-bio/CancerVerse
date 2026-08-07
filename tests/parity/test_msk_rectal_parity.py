"""Parity: our MSK rectal implementation vs. MSK's own hosted calculator.

Why this test exists
--------------------
The Weiser 2021 model is published only as a rendered image in a JAMA Network
Open supplement (eFigure), with no worked example. Two of the usual routes are
therefore closed: there is no reference implementation to run, and no printed
patient to reproduce.

Route 5 (re-derive the paper's own statistics) half-worked and is what forced
this test. exp(beta) from the eFigure was compared against the hazard ratios in
the eTable of the same supplement:

    RFS   6 of 6 terms agree to 3 significant figures
    OS    0 of 5 terms agree   (T3 1.31 vs 1.48, T4 4.00 vs 3.80,
                                DTAV 0.64 vs 0.69, VI 1.60 vs 1.09,
                                PNI 1.97 vs 2.02)

Both artifacts were re-read from PNG renders at 300 and 600 dpi to rule out a
transcription error; both readings are exact. The RFS model has no age term and
its eTable has no Age row; the OS model has an age spline and its eTable does.
The published correction notice for this article (PMC8759003) fixes only three
collaborator names, so the discrepancy stands uncorrected.

That left a real question: which artifact does the actual model use? This test
answers it with route 6 — MSK hosts the deployed model at
mskcc.org/nomograms/rectal/post-treatment and the tool's own "Supporting
Publication" block cites this exact paper. Our eFigure-based implementation
reproduces the hosted tool on all 12 captured cases, so the eFigure is the
model and the eTable's OS hazard-ratio column is the inconsistent artifact.

Fixture: reference/msk_rectal_cases.json, captured by
reference/msk_rectal_fetch.py. This test is offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mayo_baseline.colorectal.prognosis.msk_rectal import msk_rectal_predict

CASES_FILE = Path(__file__).parent / "reference" / "msk_rectal_cases.json"

# The tool displays whole percentages. A displayed 83 means [82.5, 83.5), so
# half a point is the exact rounding half-width; 1.0 absorbs any difference in
# rounding convention (round-half-up vs. banker's) without letting a real
# coefficient error through — the smallest coefficient in the model moves a
# typical patient by far more than a point.
TOLERANCE_PCT = 1.0


def _cases():
    data = json.loads(CASES_FILE.read_text())
    return data["cases"]


def _ours(case: dict, endpoint: str) -> float:
    # The fixture stores MSK's binary "distance > 5 cm" answer. Map it onto a
    # distance that lands on the same side of the published >= 5 cut, staying
    # clear of 5.0 itself so the >/>= ambiguity in MSK's field name is never
    # exercised. See the note in msk_rectal_fetch.py.
    distance = 8.0 if case["dtav_gt5"] else 2.0
    out = msk_rectal_predict(
        endpoint=endpoint,
        months=60,
        ypt=case["t_stage"],
        positive_nodes=case["nodes"],
        distance_to_anal_verge_cm=distance,
        venous_invasion=case["vi"],
        perineural_invasion=case["pni"],
        age=case["age"],
    )
    return out["survival"] * 100.0


@pytest.mark.parametrize("case", _cases(), ids=lambda c: f"age{c['age']}-{c['t_stage']}-n{c['nodes']}")
@pytest.mark.parametrize("endpoint", ["rfs", "os"])
def test_matches_the_hosted_msk_calculator(endpoint, case):
    ours = _ours(case, endpoint)
    theirs = case[endpoint]
    assert ours == pytest.approx(theirs, abs=TOLERANCE_PCT), (
        f"{endpoint} for {case}: ours {ours:.2f}% vs MSK {theirs}%"
    )


def test_the_fixture_covers_both_ypt_reference_groups():
    """RFS is coded against ypT0/T1 and OS against ypT0/T1/T2. A fixture with
    no ypT2 case could not tell the two codings apart."""
    stages = {c["t_stage"] for c in _cases()}
    assert "T2" in stages, "need a ypT2 case to exercise the differing references"
    assert {"T3", "T4"} <= stages
    assert len(stages) >= 4


def test_the_fixture_exercises_the_positive_node_spline_knots():
    """Knots sit at 0, 1 and 3 positive nodes; the fixture must straddle them."""
    nodes = {c["nodes"] for c in _cases()}
    assert 0 in nodes and 1 in nodes
    assert any(n > 3 for n in nodes)


def test_the_hosted_tool_also_puts_os_below_rfs_for_older_patients():
    """RFS <= OS holds by definition (every death is also an RFS event), yet
    the two endpoints are fit as separate marginal Cox models and only the OS
    model carries age. For an 80-year-old the OS model predicts heavy mortality
    while the age-blind RFS model does not follow, and the ordering inverts.

    This is a property of the published model pair, not of our transcription —
    MSK's own deployed tool returns RFS 42% with OS 15% for that patient. The
    test pins the fact so nobody later "fixes" our code to enforce RFS <= OS.
    """
    inverted = [c for c in _cases() if c["os"] < c["rfs"]]
    assert inverted, "expected the published models to invert somewhere"
    assert all(c["age"] >= 70 for c in inverted), (
        f"inversion should be driven by age, got {inverted}"
    )
    # And ours reproduces the inversion rather than papering over it.
    for c in inverted:
        assert _ours(c, "os") < _ours(c, "rfs")
