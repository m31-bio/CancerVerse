"""PLCOm2012 6-year lung-cancer risk for ever-smokers (Tammemägi 2013)."""

from __future__ import annotations

from ...base import logit_risk
from . import coefficients as C

AXIS = "detection"
MODEL_ID = "plcom2012"

_RACE_ALIASES = {
    "white": "white",
    "caucasian": "white",
    "non_hispanic_white": "white",
    "black": "black",
    "african_american": "black",
    "hispanic": "hispanic",
    "latino": "hispanic",
    "asian": "asian",
    "american_indian": "american_indian_alaskan_native",
    "alaskan_native": "american_indian_alaskan_native",
    "american_indian_alaskan_native": "american_indian_alaskan_native",
    "native_hawaiian": "native_hawaiian_pacific_islander",
    "pacific_islander": "native_hawaiian_pacific_islander",
    "native_hawaiian_pacific_islander": "native_hawaiian_pacific_islander",
}


def _race_key(race: str) -> str:
    key = race.strip().lower().replace("-", "_").replace(" ", "_").replace("/", "_")
    while "__" in key:
        key = key.replace("__", "_")
    if key not in _RACE_ALIASES:
        raise ValueError(f"race must be one of {sorted(C.RACE)}, got {race!r}")
    return _RACE_ALIASES[key]


def smoking_intensity_term(cigarettes_per_day: float) -> float:
    """Table 2 transform: (cpd/10)**-1 centered on 0.4021541613."""
    if cigarettes_per_day <= 0:
        raise ValueError(
            "PLCOm2012 applies to ever-smokers; cigarettes_per_day must be > 0"
        )
    return (cigarettes_per_day / 10.0) ** -1.0 - C.SMOKING_INTENSITY_CENTER


def linear_predictor(
    *,
    age: float,
    race: str,
    education_level: int,
    bmi: float,
    copd: bool,
    personal_cancer_history: bool,
    family_history_lung_cancer: bool,
    current_smoker: bool,
    cigarettes_per_day: float,
    smoking_duration_years: float,
    quit_years: float,
) -> float:
    """Model logit as specified in the Table 2 footnote."""
    if education_level not in C.EDUCATION_LEVELS:
        raise ValueError(
            f"education_level must be one of {C.EDUCATION_LEVELS} "
            f"(1=<HS … 6=postgraduate), got {education_level!r}"
        )
    if smoking_duration_years <= 0:
        raise ValueError(
            "PLCOm2012 applies to ever-smokers; smoking_duration_years must be > 0"
        )
    if quit_years < 0:
        raise ValueError(f"quit_years must be >= 0, got {quit_years}")
    if current_smoker and quit_years != 0:
        raise ValueError("current smokers have quit_years=0")

    return (
        C.INTERCEPT
        + C.AGE * (age - C.AGE_CENTER)
        + C.RACE[_race_key(race)]
        + C.EDUCATION * (education_level - C.EDUCATION_CENTER)
        + C.BMI * (bmi - C.BMI_CENTER)
        + C.COPD * (1.0 if copd else 0.0)
        + C.PERSONAL_CANCER_HISTORY * (1.0 if personal_cancer_history else 0.0)
        + C.FAMILY_HISTORY_LUNG_CANCER * (1.0 if family_history_lung_cancer else 0.0)
        + C.SMOKING_STATUS_CURRENT * (1.0 if current_smoker else 0.0)
        + C.SMOKING_INTENSITY * smoking_intensity_term(cigarettes_per_day)
        + C.SMOKING_DURATION * (smoking_duration_years - C.SMOKING_DURATION_CENTER)
        + C.SMOKING_QUIT_TIME * (quit_years - C.SMOKING_QUIT_TIME_CENTER)
    )


def plcom2012_predict(
    *,
    age: float,
    race: str,
    education_level: int,
    bmi: float,
    copd: bool,
    personal_cancer_history: bool,
    family_history_lung_cancer: bool,
    current_smoker: bool,
    cigarettes_per_day: float,
    smoking_duration_years: float,
    quit_years: float = 0.0,
) -> dict:
    """
    6-year probability of a lung-cancer diagnosis in an ever-smoker.

    Notes
    -----
    Development population: PLCO control-group smokers aged 55-74. The model is
    not defined for never-smokers, and the 6-year horizon is unscreened natural
    history (no low-dose CT effect).
    """
    lp = linear_predictor(
        age=age,
        race=race,
        education_level=education_level,
        bmi=bmi,
        copd=copd,
        personal_cancer_history=personal_cancer_history,
        family_history_lung_cancer=family_history_lung_cancer,
        current_smoker=current_smoker,
        cigarettes_per_day=cigarettes_per_day,
        smoking_duration_years=smoking_duration_years,
        quit_years=quit_years,
    )
    return {
        "risk": logit_risk(lp),
        "linear_predictor": lp,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "lung",
        "horizon_years": 6,
        "race_group": _race_key(race),
        "citation": C.MODEL_CITATION,
        "notes": "6y lung-cancer risk in ever-smokers; parity matched vs resplab/PLCOm2012",
    }
