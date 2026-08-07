"""CHA2DS2-VASc — stroke risk in atrial fibrillation (Lip et al., Chest 2010).

Equation source
---------------
Lip GYH, Nieuwlaat R, Pisters R, Lane DA, Crijns HJGM. "Refining Clinical Risk
Stratification for Predicting Stroke and Thromboembolism in Atrial
Fibrillation Using a Novel Risk Factor-Based Approach: The Euro Heart Survey
on Atrial Fibrillation." Chest. 2010;137(2):263-272.

Integer point table, total 0-9:

    Congestive heart failure / LV dysfunction   1
    Hypertension                                1
    Age >= 75                                   2
    Diabetes mellitus                           1
    prior Stroke / TIA / thromboembolism         2
    Vascular disease (MI, PAD, aortic plaque)   1
    Age 65-74                                   1
    Sex category (female)                       1

Age 65-74 and Age >=75 are mutually exclusive (age contributes at most once).

Deliberately not included here: a stroke-rate-by-score lookup table. Multiple
published cohorts (the original Euro Heart Survey derivation, later external
validations) report different annual event rates for the same score, and this
project's rule is not to attach a numeric claim without pinning it to one
specific, checked source. The guideline-level category returned below (0 = low
/ no anticoagulation, 1 in a male = consider, >=2 = anticoagulation generally
indicated) is the widely stated qualitative interpretation, not a rate.
"""

from __future__ import annotations

AXIS = "prognosis"
MODEL_ID = "cha2ds2_vasc"

MAX_SCORE = 9

MODEL_CITATION = (
    "Lip GYH et al. Chest. 2010;137(2):263-272 (CHA2DS2-VASc)."
)


def cha2ds2_vasc_score(
    *,
    heart_failure: bool,
    hypertension: bool,
    age: float,
    diabetes: bool,
    prior_stroke_tia_thromboembolism: bool,
    vascular_disease: bool,
    female: bool,
) -> int:
    """Total CHA2DS2-VASc points (0-9)."""
    if age < 0:
        raise ValueError(f"age must be >= 0, got {age}")
    age_points = 2 if age >= 75 else (1 if age >= 65 else 0)
    return (
        (1 if heart_failure else 0)
        + (1 if hypertension else 0)
        + age_points
        + (1 if diabetes else 0)
        + (2 if prior_stroke_tia_thromboembolism else 0)
        + (1 if vascular_disease else 0)
        + (1 if female else 0)
    )


def risk_category(score: int, *, female: bool) -> str:
    """Guideline-level category, not a numeric stroke rate (see module docstring).

    A lone point from female sex alone (score 1, no other factor) is generally
    treated as low risk — sex category only counts as a true risk modifier
    when it accompanies at least one other risk factor.
    """
    if score == 0:
        return "low"
    if score == 1 and female:
        return "low"
    if score == 1:
        return "intermediate"
    return "high"


def cha2ds2_vasc_predict(
    *,
    heart_failure: bool,
    hypertension: bool,
    age: float,
    diabetes: bool,
    prior_stroke_tia_thromboembolism: bool,
    vascular_disease: bool,
    female: bool,
) -> dict:
    """CHA2DS2-VASc score and guideline-level risk category."""
    score = cha2ds2_vasc_score(
        heart_failure=heart_failure,
        hypertension=hypertension,
        age=age,
        diabetes=diabetes,
        prior_stroke_tia_thromboembolism=prior_stroke_tia_thromboembolism,
        vascular_disease=vascular_disease,
        female=female,
    )
    return {
        "score": score,
        "risk_category": risk_category(score, female=female),
        "risk": None,  # point score; see module docstring on rate tables
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "cvd",
        "citation": MODEL_CITATION,
        "notes": "0-9 points; a lone point from female sex alone is treated as low risk",
    }
