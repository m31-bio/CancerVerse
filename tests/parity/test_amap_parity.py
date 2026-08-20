"""Parity: our aMAP implementation vs. CUHK's custodial calculator.

aMAP publishes no worked example, so the calculator hosted by CUHK's Medical
Data Analytics Centre — an aMAP collaborating site — is the only external check
available. Route 3 (POST to a server-side endpoint).

**This test closes what this repo recorded as its one unresolved conflict.** An
earlier probe of the same calculator returned scores 2-3 points above the
published formula on three test patients, and rather than bend the code to match
a tool that contradicted the paper, the model was left unchecked pending an
answer from the authors. Re-probing those exact three patients now returns
precisely what the published formula gives (54 / 41 / 65, not 56 / 44 / 68).
The conflict does not reproduce and needs no adjudication.

Fixture: reference/amap_cases.json, captured by reference/amap_fetch.py.
This test is offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cancerverse_baseline.liver.detection.amap import amap_predict

CASES_FILE = Path(__file__).parent / "reference" / "amap_cases.json"

# The tool's banding vocabulary vs. ours.
GROUP_ALIASES = {"low": "Low", "medium": "Intermediate", "high": "High"}


def _cases():
    return json.loads(CASES_FILE.read_text())["cases"]


def _ours(case: dict) -> dict:
    return amap_predict(
        age=case["age"],
        male=case["male"],
        platelets=case["plt"],
        bilirubin_umol_l=case["bili"],
        albumin_g_l=case["alb"],
    )


def _id(c):
    return f"{c['age']}{'M' if c['male'] else 'F'}-b{c['bili']}-a{c['alb']}-p{c['plt']}"


@pytest.mark.parametrize("case", _cases(), ids=_id)
def test_score_matches_the_custodial_calculator(case):
    """The tool returns an integer, so our float must round to it exactly."""
    ours = _ours(case)["score"]
    assert round(ours) == case["score"], (
        f"ours {ours:.4f} -> {round(ours)}, CUHK {case['score']}"
    )


@pytest.mark.parametrize("case", _cases(), ids=_id)
def test_risk_group_matches_the_custodial_calculator(case):
    ours = _ours(case)["risk_group"]
    assert GROUP_ALIASES[ours] == case["risk_group"]


def test_the_historic_discrepancy_does_not_reproduce():
    """The three patients that once returned 2-3 points high now return the
    published values. Pinned so the closed conflict is not silently reopened by
    a future capture, and so the old numbers stay on the record."""
    historic = [c for c in _cases() if c.get("historic") is not None]
    assert len(historic) == 3, "the three original probe patients must stay in the fixture"
    for c in historic:
        ours = _ours(c)["score"]
        assert round(ours) == c["score"]
        assert c["score"] < c["historic"], (
            f"expected the tool to no longer return the historic {c['historic']}"
        )
        # The old gap was 2-3 points; confirm that is the size of what vanished.
        assert 2 <= c["historic"] - c["score"] <= 3


def test_the_fixture_covers_both_sexes_and_all_three_bands():
    cases = _cases()
    assert {c["male"] for c in cases} == {True, False}
    assert {c["risk_group"] for c in cases} == {"Low", "Intermediate", "High"}


def test_sex_is_the_only_difference_in_the_paired_cases():
    """Three pairs differ only in sex. The male-minus-female gap must be the
    same constant everywhere, which is what makes a level-only discrepancy
    distinguishable from a sex-coefficient error."""
    cases = _cases()
    gaps = []
    for c in cases:
        if not c["male"]:
            continue
        mate = next(
            (o for o in cases
             if not o["male"] and (o["age"], o["bili"], o["alb"], o["plt"])
             == (c["age"], c["bili"], c["alb"], c["plt"])),
            None,
        )
        if mate:
            gaps.append(_ours(c)["score"] - _ours(mate)["score"])
    assert len(gaps) == 3
    for g in gaps:
        assert g == pytest.approx(gaps[0])
    # 0.89 / 14.77 * 100
    assert gaps[0] == pytest.approx(6.026, abs=0.01)
