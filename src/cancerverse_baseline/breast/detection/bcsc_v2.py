"""BCSC breast density model ("version 1.0"), 5-year invasive breast cancer risk.

Tice JA, Cummings SR, Smith-Bindman R, Ichikawa L, Barlow WE, Kerlikowske K.
Ann Intern Med. 2008;148(5):337-347. See `bcsc_v2_coefficients.py` for the
full provenance of every number used here and the unit note explaining why
I(x,r) and D(x,r) are divided by 100 despite the paper's "per 100 000" label.

Why this is the breast detection flagship
------------------------------------------
Replaces BCRAT (Gail 1989) here. BCRAT's two hardest inputs, age at
menarche and age at first live birth, are among the fields the target
platform does not hold, so it cannot run on that data at all. This
model instead asks for BI-RADS breast density, a field a screening centre
already records as structured data, plus family history and biopsy history
as simple yes/no/unknown, no reproductive history interview needed. Its
reported concordance (0.66) is also modestly higher than BCRAT's pooled
AUC (~0.60).

VERSION LABEL, corrected 2026-08-17: this module used to call itself
"version 2.0" of the BCSC calculator. That was backwards. The BCSC's own
site (intro.htm) states plainly that version 2.0 is the 2015 update that
adds benign-breast-disease detail and a ten-year horizon, neither of which
this module has. What this module implements, five-year risk only, biopsy
history as a bare yes/no, is the calculator's version 1.0. See
`bcsc_v2_bbd_extension_coefficients.py` for what the real version 2.0 (the
2015 refinement) still needs before it can replace this module. The module
and file names keep the `bcsc_v2` id for registry continuity; they do not
assert a version number.
"""

from __future__ import annotations

import math

from . import bcsc_v2_coefficients as C

AXIS = "detection"
MODEL_ID = "bcsc_v2"

YEARS = 5  # the paper only develops and validates a 5-year risk


def _annual_incidence(age: float, race: str) -> float:
    a, b, c, d = C.BASELINE_INCIDENCE[race]
    return a * age**3 + b * age**2 + c * age + d


def _annual_mortality(age: float, race: str) -> float:
    n, m = C.MORTALITY[race]
    return n * math.exp(m * age)


def _race_specific_five_year_risk(start_age: float, race: str) -> float:
    """Average 5-year risk for a woman of this race/age, before density,
    family history or biopsy history are taken into account."""
    ages = [start_age + i for i in range(YEARS)]
    incidence = [_annual_incidence(x, race) / 100.0 for x in ages]
    mortality = [_annual_mortality(x, race) / 100.0 for x in ages]

    p = 1.0
    risk = 0.0
    for i in range(YEARS):
        risk += incidence[i] * p
        p = p - incidence[i] - mortality[i]
    return risk


def bcsc_v2_predict(
    *,
    start_age: float,
    race: str,
    density: int,
    family_history: bool | None = None,
    biopsy_history: bool | None = None,
) -> dict:
    """
    5-year risk of invasive breast cancer starting at ``start_age``.

    Parameters
    ----------
    start_age : age at the start of the 5-year window. The lower bound is the
        paper's, it included "1 095 484 women age 35 years or older". The
        UPPER bound of 79 is OURS, not the paper's: Tice 2008 states no upper
        limit and its own results tables run to an 80-84 band, so the ceiling
        refuses a patient the paper reports on. It is kept because the model
        has not been shown to hold past it and silently extrapolating a
        cancer-risk estimate is the worse failure, but it is a choice this
        library made and is labelled as such rather than attributed to the
        source. See docs/MODEL_CONSTRAINTS.md. There is also no published
        extension to a 10-year horizon for this version (that is the 2015
        update's contribution, not yet implemented here).
    race : one of ``bcsc_v2_coefficients.RACE_GROUPS`` (white/black/asian/hispanic).
        The paper excluded American Indian/Alaskan Native for inconsistent
        SEER rates, so there is no fifth group to fall back to.
    density : BI-RADS breast density category, 1 (almost entirely fat) to
        4 (extremely dense). 2 (scattered fibroglandular densities) is the
        reference category the model was standardized to.
    family_history : whether the woman has >=1 first-degree relative with
        breast cancer. ``None`` if unknown, per the paper, an unknown
        value means no further multiplication is applied, not an imputed
        average.
    biopsy_history : whether the woman has ever had a breast biopsy.
        Same ``None``-means-skip convention as ``family_history``.
    """
    if race not in C.RACE_GROUPS:
        raise ValueError(f"race must be one of {C.RACE_GROUPS}, got {race!r}")
    if density not in (1, 2, 3, 4):
        raise ValueError(f"density must be 1-4 (BI-RADS category), got {density!r}")
    if start_age < 35 or start_age > 79:
        raise ValueError(
            f"start_age must fall within [35, 79], got {start_age}. The lower "
            f"bound is the paper's; the upper bound is this library's own and "
            f"is not stated by Tice 2008, see docs/MODEL_CONSTRAINTS.md"
        )

    race_risk = _race_specific_five_year_risk(start_age, race)

    adjustment = C.AGE_RACE_DENSITY_ADJUSTMENT[race][C.age_band(start_age)]
    reference_group_risk = race_risk * adjustment

    density_hazards = (
        C.DENSITY_RELATIVE_HAZARD["under_65"]
        if start_age < C.DENSITY_AGE_CUTOFF
        else C.DENSITY_RELATIVE_HAZARD["65_or_over"]
    )
    risk = reference_group_risk * density_hazards[density]

    if family_history is not None:
        risk *= C.FAMILY_HISTORY_MULTIPLIER[family_history]
    if biopsy_history is not None:
        risk *= C.BIOPSY_HISTORY_MULTIPLIER[biopsy_history]

    return {
        "risk": risk,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "breast",
        "start_age": start_age,
        "end_age": start_age + YEARS,
        "race": race,
        "density": density,
        "family_history": family_history,
        "biopsy_history": biopsy_history,
        "citation": C.MODEL_CITATION,
        "notes": (
            "5-year invasive breast cancer risk; formula transcribed from the "
            "paper's own Appendix Figure algorithm and cross-checked against "
            "its Table 5 worked examples (2026-08-17), not against an "
            "independent reference implementation, see "
            "docs/VERIFICATION.md for what that distinction means here."
        ),
    }
