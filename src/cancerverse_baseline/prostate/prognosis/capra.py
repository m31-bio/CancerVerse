"""UCSF-CAPRA score — prostate cancer recurrence risk (Cooperberg et al., 2005).

Equation source
---------------
Cooperberg MR, Pasta DJ, Elkin EP, Litwin MS, Latini DM, DuChane J, Carroll PR.
"The UCSF Cancer of the Prostate Risk Assessment (CAPRA) Score: a straightforward
and reliable preoperative predictor of disease recurrence after radical
prostatectomy." J Urol. 2005;173(6):1938-1942. PMC2948569, Table 1.

Integer point table, total 0-10:

    PSA (ng/mL)        2.1-6 = 0, 6.1-10 = 1, 10.1-20 = 2, 20.1-30 = 3, >30 = 4
    Gleason 1st/2nd    1-3/1-3 = 0, 1-3/4-5 = 1, 4-5/any = 3
    Clinical T stage   T1/T2 = 0, T3a = 1
    % positive cores   <34% = 0, >=34% = 1
    Age (years)        <50 = 0, >=50 = 1

    0-2 low, 3-5 intermediate, 6-10 high risk.
"""

from __future__ import annotations

AXIS = "prognosis"
MODEL_ID = "capra"

LOW_MAX = 2
INTERMEDIATE_MAX = 5
MAX_SCORE = 10

MODEL_CITATION = (
    "Cooperberg MR et al. J Urol. 2005;173(6):1938-1942 (UCSF-CAPRA). PMC2948569 Table 1."
)


def psa_points(psa: float) -> int:
    """PSA contributes 0-4 points."""
    if psa <= 0:
        raise ValueError(f"psa must be > 0 ng/mL, got {psa}")
    if psa <= 6.0:
        return 0
    if psa <= 10.0:
        return 1
    if psa <= 20.0:
        return 2
    if psa <= 30.0:
        return 3
    return 4


def gleason_points(primary: int, secondary: int) -> int:
    """Gleason contributes 0, 1 or 3 points — note there is no 2-point level."""
    for name, value in (("primary", primary), ("secondary", secondary)):
        if value not in (1, 2, 3, 4, 5):
            raise ValueError(f"Gleason {name} pattern must be 1-5, got {value}")
    if primary >= 4:
        return 3
    if secondary >= 4:
        return 1
    return 0


def t_stage_points(t_stage: str) -> int:
    """T1/T2 = 0, T3a = 1. CAPRA is a localized-disease score."""
    s = t_stage.strip().upper().replace("C", "", 1) if t_stage.strip().upper().startswith("C") else t_stage.strip().upper()
    if s.startswith("T1") or s.startswith("T2"):
        return 0
    if s == "T3A":
        return 1
    raise ValueError(
        f"CAPRA is defined for T1/T2/T3a localized disease, got {t_stage!r}"
    )


def capra_score(
    *,
    psa: float,
    gleason_primary: int,
    gleason_secondary: int,
    t_stage: str,
    percent_positive_cores: float,
    age: float,
) -> int:
    """Total CAPRA points (0-10)."""
    if not 0.0 <= percent_positive_cores <= 100.0:
        raise ValueError(
            f"percent_positive_cores must be 0-100, got {percent_positive_cores}"
        )
    if age <= 0:
        raise ValueError(f"age must be > 0, got {age}")
    return (
        psa_points(psa)
        + gleason_points(gleason_primary, gleason_secondary)
        + t_stage_points(t_stage)
        + (1 if percent_positive_cores >= 34.0 else 0)
        + (1 if age >= 50.0 else 0)
    )


def risk_group(score: int) -> str:
    if score <= LOW_MAX:
        return "low"
    if score <= INTERMEDIATE_MAX:
        return "intermediate"
    return "high"


def capra_predict(
    *,
    psa: float,
    gleason_primary: int,
    gleason_secondary: int,
    t_stage: str,
    percent_positive_cores: float,
    age: float,
) -> dict:
    """
    UCSF-CAPRA score and risk group.

    Notes
    -----
    CAPRA is a point score, not a probability model: recurrence risk roughly
    doubles per 2-point increase. Mapping score to a survival estimate requires
    the published outcome tables, which are cohort-specific and not included.
    """
    score = capra_score(
        psa=psa,
        gleason_primary=gleason_primary,
        gleason_secondary=gleason_secondary,
        t_stage=t_stage,
        percent_positive_cores=percent_positive_cores,
        age=age,
    )
    return {
        "score": score,
        "risk_group": risk_group(score),
        "risk": None,  # point score, not a probability
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "prostate",
        "components": {
            "psa": psa_points(psa),
            "gleason": gleason_points(gleason_primary, gleason_secondary),
            "t_stage": t_stage_points(t_stage),
            "percent_positive_cores": 1 if percent_positive_cores >= 34.0 else 0,
            "age": 1 if age >= 50.0 else 0,
        },
        "citation": MODEL_CITATION,
        "notes": "0-2 low / 3-5 intermediate / 6-10 high; risk ~doubles per 2 points",
    }
