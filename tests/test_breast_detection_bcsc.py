"""BCSC breast density model (Tice 2008), the calculator's version 1.0."""

from __future__ import annotations

import pytest

from cancerverse_baseline.breast.detection import bcsc_v2_predict


def test_missing_family_or_biopsy_history_is_not_the_same_as_no():
    """Omitting an optional risk factor must leave the patient at reference.

    Both optional inputs are frequently absent in real records, so how absence
    is handled decides what the model returns for a large share of patients.
    This module treats `None` as "not known" and applies no multiplier at all,
    which is the correct reading: the multipliers (0.938 / 1.454 for family
    history, 0.906 / 1.495 for biopsy) are relative to a reference group, so
    scoring an unknown as `False` would apply a protective 0.938 the evidence
    does not support.

    Pinned on 2026-08-18 after the registry described these inputs as
    "yes/no/unknown", which reads as though the string "unknown" were an
    accepted value. It is not, it raises KeyError. The wording was corrected;
    this test fixes the behaviour it described.
    """
    base = dict(start_age=55, race="white", density=2)

    unknown = bcsc_v2_predict(**base)["risk"]
    no = bcsc_v2_predict(**base, family_history=False, biopsy_history=False)["risk"]
    yes = bcsc_v2_predict(**base, family_history=True, biopsy_history=True)["risk"]

    assert no < unknown < yes, (
        f"unknown ({unknown:.6f}) must sit between no ({no:.6f}) and yes "
        f"({yes:.6f}), it is the reference group, not a 'no'")
    assert unknown != no, "omitting a factor must not be scored as its absence"

    # and the string that used to be documented is still not a value
    with pytest.raises((KeyError, ValueError, TypeError)):
        bcsc_v2_predict(**base, family_history="unknown")
