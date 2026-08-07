"""LIPI — Lung Immune Prognostic Index (Mezquita et al.).

Equation source
---------------
Mezquita L, Auclin E, Ferrara R, et al. LIPI and outcomes with immune checkpoint
inhibitors in advanced NSCLC. Two items, one point each:

    derived neutrophil-lymphocyte ratio (dNLR) > 3      -> 1 point
    lactate dehydrogenase (LDH) > upper limit of normal -> 1 point

    0 = good, 1 = intermediate, 2 = poor

    dNLR = neutrophils / (leukocytes - neutrophils)

Reference: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7481630/
Validation in IMpower130/131/150 post hoc analysis:
https://www.sciencedirect.com/science/article/pii/S0169500224005737

Used on both axes: `response` (ICI benefit) and `prognosis` (survival).
"""

from __future__ import annotations

AXIS = "response"
MODEL_ID = "lipi"

DNLR_THRESHOLD = 3.0
GROUPS = {0: "good", 1: "intermediate", 2: "poor"}

MODEL_CITATION = (
    "Mezquita L et al., Lung Immune Prognostic Index (dNLR > 3, LDH > ULN). "
    "PMC7481630; validated in IMpower130/131/150 post hoc analysis."
)


def derived_nlr(*, neutrophils: float, leukocytes: float) -> float:
    """dNLR = neutrophils / (leukocytes - neutrophils).

    The denominator is the *non-neutrophil* white count, which is why this is
    "derived" NLR rather than the ordinary neutrophil-to-lymphocyte ratio — it
    does not need a lymphocyte count.
    """
    if neutrophils <= 0:
        raise ValueError(f"neutrophils must be > 0, got {neutrophils}")
    other = leukocytes - neutrophils
    if other <= 0:
        raise ValueError(
            f"leukocytes ({leukocytes}) must exceed neutrophils ({neutrophils})"
        )
    return neutrophils / other


def lipi_predict(
    *,
    dnlr: float | None = None,
    neutrophils: float | None = None,
    leukocytes: float | None = None,
    ldh: float,
    ldh_upper_limit_normal: float,
) -> dict:
    """
    LIPI score (0-2) and group. Supply `dnlr` directly, or a neutrophil and
    leukocyte count to derive it.

    LDH is compared against the reporting lab's own upper limit of normal, so
    both the value and its ULN must be passed — there is no universal cutoff.
    """
    if dnlr is None:
        if neutrophils is None or leukocytes is None:
            raise ValueError("provide dnlr, or both neutrophils and leukocytes")
        dnlr = derived_nlr(neutrophils=neutrophils, leukocytes=leukocytes)
    elif neutrophils is not None or leukocytes is not None:
        raise ValueError("provide dnlr or the counts, not both")

    if ldh <= 0 or ldh_upper_limit_normal <= 0:
        raise ValueError("ldh and ldh_upper_limit_normal must be > 0")

    dnlr_point = 1 if dnlr > DNLR_THRESHOLD else 0
    ldh_point = 1 if ldh > ldh_upper_limit_normal else 0
    score = dnlr_point + ldh_point
    return {
        "score": score,
        "group": GROUPS[score],
        "risk": None,  # point score, not a probability
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "lung",
        "dnlr": dnlr,
        "components": {"dnlr": dnlr_point, "ldh": ldh_point},
        "citation": MODEL_CITATION,
        "notes": "0 good / 1 intermediate / 2 poor; also used on the prognosis axis",
    }
