"""7-year head and neck cancer risk from routine and lifestyle variables (UK Biobank).

Equation source
---------------
McCarthy CE, Bonnet LJ, Marcus MW, Field JK. "Development and validation of a
multivariable risk prediction model for head and neck cancer using the UK
Biobank." Int J Oncol. 2020;57(5):1192-1202. doi:10.3892/ijo.2020.5123.
PubMed 33491742.

Coefficients from **Table III** ("Multivariable model for head and neck cancer
risk in the UK Biobank"), read on 2026-08-17. The table
prints odds ratios; the constant is in its caption, which is what makes this
model implementable at all:

    "Model Intercept Coefficient -9.54 (95% confidence interval,
     -11.2 - -7.88; P<0.001). Based on 397,179 observations (n=232 cases and
     n=396,947 controls with no missing data available for complete cases
     analysis)."

    logit(p) = -9.54 + b_age*age + b_male + b_smoking + b_tdi
                     + b_bmi*bmi + b_alcohol + b_exercise + b_fruitveg

Every beta is ln(OR). Age and BMI enter as raw continuous values, the paper
models them continuous "to prevent biological implausibility and inefficient
use of data" and nowhere centres them, so the intercept is the log-odds at
age 0 and BMI 0 and is not interpretable on its own.

What it predicts
----------------
Incident head and neck cancer within **7 years** of recruitment, defined as
ICD-10 C00-C14 and C30-C31. **Laryngeal cancer (C32) is deliberately excluded**
from the outcome: the authors excluded it because "screening for oral cancers
and laryngeal cancers requires different expertise and laryngeal cancer would
not be visible during routine oral examination". A user who wants all head and
neck sites is not asking this model's question.

Two coefficients that look wrong and are not
--------------------------------------------
**BMI is protective** (OR 0.96 per unit). Higher BMI carried lower HNC risk in
this cohort. That is the direction the paper reports and discusses; do not
"correct" the sign.

**Alcohol is non-monotonic, and current drinking is not significant.** Against
never-drinkers, PREVIOUS drinkers carry OR 3.26 (1.32-8.04) while CURRENT
drinkers carry 1.42 with a confidence interval spanning 1 (0.62-3.21). This is
the sick-quitter pattern, people who stopped drinking because they were
already unwell, so the alcohol term does not run in the direction a clinician
expects, and the largest alcohol effect attaches to the category that has
stopped. Deprivation is non-monotonic too: quintile 4 (1.81) exceeds quintile 5
(1.66).

Scope and what does not transfer
--------------------------------
The Townsend Deprivation Index is a UK **area-level** measure, quintiled with
1 = least deprived. There is no US equivalent, so this input does not carry
over to a US record system unaltered, the same class of problem this project
records for PREVENT's SDI decile. Exercise days per week and five-a-day intake
are questionnaire items. Together those three put this model at
`ehr_availability: not_ehr`, like CRC-PRO.

Validation is weaker than the cohort size suggests. C-statistic 0.69
(95% CI 0.66-0.71) in development with good calibration; 0.64 (0.60-0.68) on
"the North West Cohort from the UK Biobank", a geographic subset of the same
dataset, not an independent cohort. The paper also states bootstrapping "was
not completed as the dataset is sufficiently large".
"""

from __future__ import annotations

import math

AXIS = "detection"
MODEL_ID = "ukb_hnc"

#: Table III caption. The log-odds at age 0 and BMI 0; not interpretable alone.
INTERCEPT = -9.54
INTERCEPT_CI = (-11.2, -7.88)

#: Odds ratios exactly as Table III prints them. Betas are ln(OR); the ratios
#: are kept as the literals so the source can be checked against the paper
#: without undoing a logarithm.
OR_AGE_PER_YEAR = 1.04
OR_BMI_PER_UNIT = 0.96
OR_MALE = 1.81

#: never is the reference for both, contributing 0.
OR_SMOKING = {"never": 1.00, "previous": 1.59, "current": 3.10}
OR_ALCOHOL = {"never": 1.00, "previous": 3.26, "current": 1.42}

#: Townsend Deprivation Index quintile, 1 = LEAST deprived and the reference.
OR_TDI = {1: 1.00, 2: 1.30, 3: 1.14, 4: 1.81, 5: 1.66}

#: Days per week of moderate exercise (>=10 min), banded as the paper bands it.
OR_EXERCISE = {"none": 1.00, "1-4_days": 0.68, "5_or_more_days": 0.66}

#: Fruit and vegetable portions per day, split at the NHS five-a-day guideline.
OR_FRUIT_VEG = {"under_5": 1.00, "5_or_more": 0.71}

#: The three continuous/binary terms as betas, derived once rather than per
#: call. The odds ratios above stay the literals of record so they can be read
#: straight off Table III; these are what the arithmetic uses, and what
#: registry/parameters.yaml pins against.
BETA_AGE = math.log(OR_AGE_PER_YEAR)
BETA_BMI = math.log(OR_BMI_PER_UNIT)
BETA_MALE = math.log(OR_MALE)

HORIZON_YEARS = 7

MODEL_CITATION = (
    "McCarthy CE, Bonnet LJ, Marcus MW, Field JK. Int J Oncol. "
    "2020;57(5):1192-1202 (UK Biobank head and neck cancer risk model)."
)


def _beta(table: dict, key, name: str) -> float:
    if key not in table:
        raise ValueError(
            f"{name} must be one of {sorted(table, key=str)}, got {key!r}")
    return math.log(table[key])


def ukb_hnc_linear_predictor(
    *,
    age: float,
    male: bool,
    smoking_status: str,
    townsend_quintile: int,
    bmi: float,
    alcohol_status: str,
    exercise_days: str,
    fruit_veg: str,
) -> float:
    """The log-odds. Separated out so the terms can be inspected in tests."""
    if not 0 < age < 120:
        raise ValueError(f"age must be in (0, 120), got {age}")
    if not 5 < bmi < 100:
        raise ValueError(f"bmi must be in (5, 100), got {bmi}")

    return (
        INTERCEPT
        + BETA_AGE * age
        + BETA_BMI * bmi
        + (BETA_MALE if male else 0.0)
        + _beta(OR_SMOKING, smoking_status, "smoking_status")
        + _beta(OR_TDI, townsend_quintile, "townsend_quintile")
        + _beta(OR_ALCOHOL, alcohol_status, "alcohol_status")
        + _beta(OR_EXERCISE, exercise_days, "exercise_days")
        + _beta(OR_FRUIT_VEG, fruit_veg, "fruit_veg")
    )


def ukb_hnc_predict(
    *,
    age: float,
    male: bool,
    smoking_status: str,
    townsend_quintile: int,
    bmi: float,
    alcohol_status: str,
    exercise_days: str,
    fruit_veg: str,
) -> dict:
    """7-year risk of incident head and neck cancer (ICD-10 C00-C14, C30-C31).

    `smoking_status` and `alcohol_status` are "never" / "previous" / "current".
    `townsend_quintile` is 1-5 with 1 the LEAST deprived.
    `exercise_days` is "none" / "1-4_days" / "5_or_more_days".
    `fruit_veg` is "under_5" / "5_or_more" portions per day.

    Laryngeal cancer is NOT in the outcome, see the module docstring.
    """
    lp = ukb_hnc_linear_predictor(
        age=age, male=male, smoking_status=smoking_status,
        townsend_quintile=townsend_quintile, bmi=bmi,
        alcohol_status=alcohol_status, exercise_days=exercise_days,
        fruit_veg=fruit_veg,
    )
    return {
        "risk": 1.0 / (1.0 + math.exp(-lp)),
        "linear_predictor": lp,
        "horizon_years": HORIZON_YEARS,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "head_neck",
        "citation": MODEL_CITATION,
        "notes": ("7-year risk of ICD-10 C00-C14 and C30-C31; laryngeal cancer "
                  "(C32) is excluded from the outcome. Townsend index is a UK "
                  "area-level measure with no US equivalent."),
    }
