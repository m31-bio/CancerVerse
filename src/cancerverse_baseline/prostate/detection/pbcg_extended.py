"""Extended PBCG (2022), risk of high-grade prostate cancer on biopsy.

Neumair M, Kattan MW, Freedland SJ, et al. (Ankerst DP, senior author).
Accommodating heterogeneous missing data patterns for prostate cancer risk
prediction. BMC Med Res Methodol. 2022;22(1):200.
doi:10.1186/s12874-022-01674-x

**Why this replaced the 2018 PBCG here.** The 2018 model's coefficients were
only available in machine-readable form from the calculator deployed at
riskcalc.org, whose source is licensed PolyForm Noncommercial 1.0.0, a licence
that restricts the *purpose*, and a company is outside it. This model's full
coefficient set is published as Additional file 2 of a **CC BY 4.0** article,
which permits commercial use with attribution. Same research group, same
consortium, four years newer.

The replacement is also an upgrade rather than a compromise:

    2018 PBCG                         Extended PBCG 2022
    8 sub-models                      1,024 sub-models
    3 optional predictors             10 optional predictors
    multinomial: none/low/high        binary: high-grade or not

Losing the low-grade split is the one real cost, and it is a small one. A
biopsy decision turns on the probability of *high-grade* disease; the 2018
model's own selling point in this library was that it separated that out. This
model predicts exactly that number and nothing else.

**The 1,024 sub-models are the point.** Ten predictors may each be absent, so
there are 2^10 patterns, and a model was fitted for every one. Nothing is
imputed: a record missing prostate volume and prior PSA is scored by the model
fitted on records missing exactly those two. That is what makes it usable on
real records rather than on complete ones.

Mandatory: age, PSA. Everything else may be None.

**The African-ancestry term changes sign between sub-models.** Measured across
all 1,024: protective in 412, harmful in 100, absent from the rest. It is
OR 0.68 in the full twelve-factor model, fitted on 1,334 biopsies, and OR 1.26
in the six-factor one, fitted on 8,432. Those are different fits on different
subsets, not a contradiction in the data, but the practical consequence is
sharp: which sub-model a patient lands in is decided by which optional fields
the caller happened to supply, so supplying *more* information can move this
term from harmful to protective. The term is not a population effect and must
not be read as one.

Two faithfulness notes:

- PSA and prostate volume enter as **log base 2**, matching the reference.
- The published function ends in `round()`, returning whole percentage points.
  `predict()` returns the unrounded probability; `rounded_like_reference()`
  reproduces the reference's integer output for parity checking. Rounding a
  decision-relevant probability to 1% is a property of the tool, not of the
  model, and callers should get the model.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

AXIS = "detection"
MODEL_ID = "pbcg_extended"
DISEASE = "prostate"

_DATA = Path(__file__).resolve().parent / "data" / "pbcg_extended_2022.json"

#: The ten predictors that may be missing, in the order the coefficient matrix
#: uses. Their presence/absence pattern selects the sub-model.
OPTIONAL = (
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

#: Column name in the published matrix -> our keyword argument.
_COLUMN_TO_ARG = {
    "age": "age",
    "psa": "psa",
    "race": "race",
    "priorbiopsy": "prior_biopsy",
    "dre": "dre_abnormal",
    "famhist.1": "famhist_1",
    "famhist.2": "famhist_2",
    "famhist.bca": "famhist_bca",
    "prosvol": "prostate_volume",
    "ari.use": "ari_use",
    "hispanic": "hispanic",
    "priorpsa": "prior_psa",
}

SCOPE = (
    "Prostate Biopsy Collaborative Group: men referred for prostate biopsy, "
    "pooled across ten international cohorts. Predicts high-grade disease "
    "(Gleason grade group >= 2) found on biopsy, not screening risk in an "
    "unreferred population, and not risk of any cancer. The 2018 predecessor "
    "was found on external validation to over-predict in Black and other "
    "groups; that caveat has not been re-tested for this version here."
)

CITATION = (
    "Neumair M, Kattan MW, Freedland SJ, et al. Accommodating heterogeneous "
    "missing data patterns for prostate cancer risk prediction. "
    "BMC Med Res Methodol. 2022;22(1):200. doi:10.1186/s12874-022-01674-x "
    "(coefficients from Additional file 2, CC BY 4.0)"
)


def _load() -> tuple[list[str], list[list[float | None]]]:
    d = json.loads(_DATA.read_text())
    return d["columns"], d["rows"]


_COLUMNS, _ROWS = _load()

#: pattern of which optional predictors are PRESENT -> that row's coefficients
_BY_PATTERN: dict[tuple[bool, ...], list[float | None]] = {}
for _row in _ROWS:
    _key = tuple(
        _row[_COLUMNS.index(col)] is not None
        for col, arg in _COLUMN_TO_ARG.items()
        if arg in OPTIONAL
    )
    _BY_PATTERN[_key] = _row

assert len(_BY_PATTERN) == 1024, f"expected 1024 sub-models, got {len(_BY_PATTERN)}"


def _bool01(value: Any, name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if value in (0, 1, 0.0, 1.0):
        return float(value)
    raise ValueError(f"{name} must be True/False, 0/1 or None; got {value!r}")


def linear_predictor(
    *,
    age: float,
    psa: float,
    race: Any = None,
    prior_biopsy: Any = None,
    dre_abnormal: Any = None,
    famhist_1: Any = None,
    famhist_2: Any = None,
    famhist_bca: Any = None,
    prostate_volume: float | None = None,
    ari_use: Any = None,
    hispanic: Any = None,
    prior_psa: Any = None,
) -> float:
    """The sub-model's linear predictor, chosen by which inputs are present."""
    if age is None or psa is None:
        raise ValueError("age and psa are mandatory")
    if psa <= 0:
        raise ValueError("psa must be positive (it enters as log2)")
    if prostate_volume is not None and prostate_volume <= 0:
        raise ValueError("prostate_volume must be positive (it enters as log2)")

    values: dict[str, float | None] = {
        "age": float(age),
        # log base 2, as the reference does
        "psa": math.log2(float(psa)),
        "race": _bool01(race, "race"),
        "prior_biopsy": _bool01(prior_biopsy, "prior_biopsy"),
        "dre_abnormal": _bool01(dre_abnormal, "dre_abnormal"),
        "famhist_1": _bool01(famhist_1, "famhist_1"),
        "famhist_2": _bool01(famhist_2, "famhist_2"),
        "famhist_bca": _bool01(famhist_bca, "famhist_bca"),
        "prostate_volume": (
            math.log2(float(prostate_volume)) if prostate_volume is not None else None
        ),
        "ari_use": _bool01(ari_use, "ari_use"),
        "hispanic": _bool01(hispanic, "hispanic"),
        "prior_psa": _bool01(prior_psa, "prior_psa"),
    }

    pattern = tuple(values[name] is not None for name in OPTIONAL)
    row = _BY_PATTERN.get(pattern)
    if row is None:  # unreachable: all 1024 are present
        raise KeyError(f"no sub-model for pattern {pattern}")

    total = row[0] or 0.0  # intercept
    for col, arg in _COLUMN_TO_ARG.items():
        beta = row[_COLUMNS.index(col)]
        x = values[arg]
        if beta is None or x is None:
            continue
        total += beta * x
    return total


def pbcg_extended_predict(
    *,
    age: float,
    psa: float,
    race: Any = None,
    prior_biopsy: Any = None,
    dre_abnormal: Any = None,
    famhist_1: Any = None,
    famhist_2: Any = None,
    famhist_bca: Any = None,
    prostate_volume: float | None = None,
    ari_use: Any = None,
    hispanic: Any = None,
    prior_psa: Any = None,
) -> dict[str, Any]:
    """Probability that a biopsy finds high-grade prostate cancer.

    The signature is spelled out rather than taking **kwargs because the API
    reports a model's required and optional inputs by introspecting it, and a
    model that accepts anything documents nothing.
    """
    kwargs = dict(
        age=age,
        psa=psa,
        race=race,
        prior_biopsy=prior_biopsy,
        dre_abnormal=dre_abnormal,
        famhist_1=famhist_1,
        famhist_2=famhist_2,
        famhist_bca=famhist_bca,
        prostate_volume=prostate_volume,
        ari_use=ari_use,
        hispanic=hispanic,
        prior_psa=prior_psa,
    )
    lp = linear_predictor(**kwargs)
    p = 1.0 / (1.0 + math.exp(-lp))
    used = [k for k in OPTIONAL if kwargs.get(k) is not None]
    return {
        "risk": p,
        "risk_high_grade": p,
        "percent": p * 100.0,
        "linear_predictor": lp,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": DISEASE,
        "sub_model": f"{len(used)} of 10 optional predictors supplied",
        "optional_supplied": tuple(used),
        "citation": CITATION,
        "notes": (
            "High-grade (Gleason grade group >= 2) on biopsy. One of 1,024 "
            "sub-models, selected by which optional predictors were given; "
            "nothing is imputed."
        ),
    }


def rounded_like_reference(**kwargs: Any) -> dict[str, int]:  # noqa: D401
    """Reproduce the published function's integer output.

    Its last steps are `round()` and `min(100, ...)`, then it reports the
    complement as 'Other'. Kept separate from `predict` so the rounding stays a
    property of the reference rather than of the model.
    """
    pct = min(100, round(pbcg_extended_predict(**kwargs)["percent"]))
    return {"Other": 100 - pct, "Risk of High Grade Cancer": pct}


predict = pbcg_extended_predict
