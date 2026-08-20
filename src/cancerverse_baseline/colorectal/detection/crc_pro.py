"""CRC-PRO, 10-year colorectal cancer risk (Multi-Ethnic Cohort).

Equation source
---------------
Wells BJ, Kattan MW, Cooper GS, Jackson L, Koroukian S. "Colorectal cancer
predicted risk online (CRC-PRO) calculator using data from the multi-ethnic
cohort study." J Am Board Fam Med. 2014;27(1):42-55.
doi:10.3122/jabfm.2014.01.130040 (open access). PMC4219857.

Coefficients transcribed from the deployed calculator's published R source,

    https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/ColorectalCancer

which is the model hosted at riskcalc.org. The paper is the scientific record;
the source is where the numbers are legible.

Form
----
    risk(10y) = 1 - S0 ** exp(Xb)      S0 = 0.9901043 (women), 0.9846654 (men)

**Men and women get different models with different predictor sets**, not one
model with a sex term. The paper is explicit: "NSAIDs were important for women
but not men; red meat intake and physical activity appeared only in the men's
model."

    women (11)  age, ethnicity, education, estrogen, diabetes, pack-years,
                family history, multivitamins, BMI, NSAIDs, alcohol
    men   (12)  age, ethnicity, pack-years, alcohol, BMI, education, aspirin,
                family history, multivitamins, red meat, diabetes, activity

Age, education, pack-years, BMI and alcohol are splined in both; red meat and
activity are splined in the men's model only. Ethnicity reference is **Black**.

A DEFECT IN THE DEPLOYED CALCULATOR, AND WHAT WE DO ABOUT IT
------------------------------------------------------------
The hosted tool cannot apply its own "previous estrogen use" coefficient. Its
UI offers three choices —

    'No'  |  'Yes, but not currently'  |  'Yes-currently'

while the model tests for

    (Estrogen == "Yes-currently")     -> reachable
    (Estrogen == "Yes-previously")    -> matches nothing the UI can produce

so the -0.044320489 term is dead code, and a woman who reports **previous**
estrogen use is scored identically to one who reports **none**.

The paper is unambiguous that this is a three-level variable ("currently,
previously, or no"), and the coefficient plainly exists and was plainly meant
for the middle level. So this module implements the paper: all three levels are
live. `emulate_deployed_defect=True` reproduces the hosted tool exactly, which
is what the parity test needs in order to compare against it honestly.

Units, from the app's own input validation
------------------------------------------
Weight is in POUNDS and height in INCHES; BMI is derived internally as
(lb x 0.45359237) / (in x 0.0254)^2. Alcohol is drinks per day, red meat is
ounces per day, activity is hours per day of moderate exercise, all
continuous, and all splined at knots that assume those units.

Validated input ranges (enforced): age 45-85, weight 75-350 lb, height 60-80 in,
pack-years 0-50, alcohol 0-12, education 6-20 years, activity 0-4, meat 0-5.
"""

from __future__ import annotations

import math

AXIS = "detection"
MODEL_ID = "crc_pro"

BASELINE_SURVIVAL = {"female": 0.9901043, "male": 0.9846654}
HORIZON_YEARS = 10

LB_TO_KG = 0.45359237
IN_TO_M = 0.0254

# Ethnicity reference level is Black, which carries no term.
ETHNICITIES = ("hawaiian", "japanese", "latino", "white", "black")
ETHNICITY_BETA = {
    "female": {
        "hawaiian": -0.24100367,
        "japanese": 0.014010715,
        "latino": -0.39669678,
        "white": -0.34056094,
        "black": 0.0,
    },
    "male": {
        "hawaiian": 0.16092241,
        "japanese": 0.25353936,
        "latino": -0.13659953,
        "white": -0.16728044,
        "black": 0.0,
    },
}
# Women's model. "previously" is the level the deployed tool cannot reach.
ESTROGEN_BETA = {"no": 0.0, "previously": -0.044320489, "currently": -0.24500762}
NSAID_BETA = {"no": 0.0, "previously": -0.046383323, "currently": -0.236997}
# Men's model.
ASPIRIN_BETA = {"no": 0.0, "previously": -0.032284161, "currently": -0.20960315}

RANGES = {
    "age": (45.0, 85.0),
    "weight_lb": (75.0, 350.0),
    "height_in": (60.0, 80.0),
    "pack_years": (0.0, 50.0),
    "alcohol_drinks_per_day": (0.0, 12.0),
    "years_education": (6.0, 20.0),
    "activity_hours_per_day": (0.0, 4.0),
    "red_meat_oz_per_day": (0.0, 5.0),
}

MODEL_CITATION = (
    "Wells BJ, Kattan MW, Cooper GS, Jackson L, Koroukian S. J Am Board Fam Med. "
    "2014;27(1):42-55 (CRC-PRO). doi:10.3122/jabfm.2014.01.130040"
)


def _p3(x: float) -> float:
    """(x)_+ cubed."""
    return x**3 if x > 0 else 0.0


def _check(name: str, value: float) -> float:
    lo, hi = RANGES[name]
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be within [{lo}, {hi}], got {value}")
    return float(value)


def _level(value: str, table: dict, name: str) -> str:
    key = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "yes": "currently",
        "yes_currently": "currently",
        "yes_previously": "previously",
        "former": "previously",
        "current": "currently",
        "never": "no",
        "none": "no",
        "african_american": "black",
        "caucasian": "white",
    }
    key = aliases.get(key, key)
    if key not in table:
        raise ValueError(f"{name} must be one of {sorted(table)}, got {value!r}")
    return key


def bmi_from_imperial(*, weight_lb: float, height_in: float) -> float:
    """The app's own conversion, kept explicit because the spline knots assume it."""
    return (weight_lb * LB_TO_KG) / ((height_in * IN_TO_M) ** 2)


def _female_lp(
    *,
    age,
    ethnicity,
    years_education,
    estrogen,
    diabetes,
    pack_years,
    family_history,
    multivitamin,
    bmi,
    nsaid,
    alcohol,
    emulate_deployed_defect,
):
    lp = -5.9026635
    lp += (
        0.090012542 * age
        - 4.4217156e-05 * _p3(age - 47.0)
        + 9.2119076e-05 * _p3(age - 60.0)
        - 4.7901919e-05 * _p3(age - 72.0)
    )
    lp += ETHNICITY_BETA["female"][ethnicity]
    lp += (
        0.07443905 * years_education
        - 0.00062546554 * _p3(years_education - 7.0)
        + 0.0017200302 * _p3(years_education - 14.0)
        - 0.0010945647 * _p3(years_education - 18.0)
    )
    if emulate_deployed_defect and estrogen == "previously":
        pass  # the dead branch, reproduced
    else:
        lp += ESTROGEN_BETA[estrogen]
    lp += 0.23328937 * diabetes
    lp += (
        0.062703176 * pack_years
        - 0.002446026 * _p3(pack_years)
        + 0.003038396 * _p3(pack_years - 1.25)
        - 0.00059134632 * _p3(pack_years - 6.375)
        - 1.023614e-06 * _p3(pack_years - 27.5125)
    )
    lp += 0.31589053 * family_history
    lp += -0.1665365 * multivitamin
    lp += (
        0.0075233925 * bmi
        + 6.7918662e-05 * _p3(bmi - 20.371336)
        - 0.00011039091 * _p3(bmi - 25.508027)
        + 4.2472244e-05 * _p3(bmi - 33.722266)
    )
    lp += NSAID_BETA[nsaid]
    lp += (
        -0.08856241 * alcohol
        + 0.62375456 * _p3(alcohol)
        - 0.7191129 * _p3(alcohol - 0.10740682)
        + 0.095358349 * _p3(alcohol - 0.8099724)
    )
    return lp


def _male_lp(
    *,
    age,
    ethnicity,
    pack_years,
    alcohol,
    bmi,
    years_education,
    aspirin,
    family_history,
    multivitamin,
    red_meat,
    diabetes,
    activity,
):
    lp = -6.6419738
    lp += (
        0.091669179 * age
        - 3.7411814e-05 * _p3(age - 47.0)
        + 7.794128e-05 * _p3(age - 60.0)
        - 4.0529466e-05 * _p3(age - 72.0)
    )
    lp += ETHNICITY_BETA["male"][ethnicity]
    lp += (
        0.00022581331 * pack_years
        + 1.1341047e-05 * _p3(pack_years)
        - 1.3522018e-05 * _p3(pack_years - 6.375)
        + 2.1809706e-06 * _p3(pack_years - 39.525)
    )
    lp += (
        0.28379769 * alcohol
        - 0.21424251 * _p3(alcohol)
        + 0.22570057 * _p3(alcohol - 0.14457189)
        - 0.011458065 * _p3(alcohol - 2.8477722)
    )
    lp += (
        0.018020786 * bmi
        + 9.4715899e-05 * _p3(bmi - 22.047175)
        - 0.00015791645 * _p3(bmi - 25.941735)
        + 6.3200548e-05 * _p3(bmi - 31.778341)
    )
    lp += (
        0.072052428 * years_education
        - 0.00060634342 * _p3(years_education - 7.0)
        + 0.0016674444 * _p3(years_education - 14.0)
        - 0.001061101 * _p3(years_education - 18.0)
    )
    lp += ASPIRIN_BETA[aspirin]
    lp += 0.24250922 * family_history
    lp += -0.19175375 * multivitamin
    lp += (
        0.073141733 * red_meat
        - 0.0043503766 * _p3(red_meat - 0.59081962)
        + 0.0065250851 * _p3(red_meat - 2.0822052)
        - 0.0021747085 * _p3(red_meat - 5.0656345)
    )
    lp += 0.11020556 * diabetes
    lp += (
        -0.090669913 * activity
        + 0.0093816671 * _p3(activity - 0.10714286)
        - 0.011850527 * _p3(activity - 0.82142857)
        + 0.0024688598 * _p3(activity - 3.5357143)
    )
    return lp


def crc_pro_predict(
    *,
    male: bool,
    age: float,
    ethnicity: str,
    weight_lb: float,
    height_in: float,
    years_education: float,
    pack_years: float,
    alcohol_drinks_per_day: float,
    family_history: bool,
    multivitamin: bool,
    diabetes: bool,
    # women only
    estrogen: str = "no",
    nsaid: str = "no",
    # men only
    aspirin: str = "no",
    red_meat_oz_per_day: float = 0.0,
    activity_hours_per_day: float = 0.0,
    emulate_deployed_defect: bool = False,
) -> dict:
    """
    10-year colorectal cancer risk.

    Weight in POUNDS, height in INCHES, the spline knots assume the app's own
    conversion. `estrogen`, `nsaid` and `aspirin` are "no" / "previously" /
    "currently".

    The sex-specific arguments are ignored for the other sex, because the two
    models genuinely have different predictor sets, see the module docstring.

    `emulate_deployed_defect` reproduces the hosted calculator's inability to
    apply its own previous-estrogen coefficient. Leave it False unless you are
    comparing against that tool.
    """
    a = _check("age", age)
    w = _check("weight_lb", weight_lb)
    h = _check("height_in", height_in)
    py = _check("pack_years", pack_years)
    alc = _check("alcohol_drinks_per_day", alcohol_drinks_per_day)
    edu = _check("years_education", years_education)
    eth = _level(ethnicity, ETHNICITY_BETA["male"], "ethnicity")
    bmi = bmi_from_imperial(weight_lb=w, height_in=h)

    if male:
        lp = _male_lp(
            age=a,
            ethnicity=eth,
            pack_years=py,
            alcohol=alc,
            bmi=bmi,
            years_education=edu,
            aspirin=_level(aspirin, ASPIRIN_BETA, "aspirin"),
            family_history=float(family_history),
            multivitamin=float(multivitamin),
            red_meat=_check("red_meat_oz_per_day", red_meat_oz_per_day),
            diabetes=float(diabetes),
            activity=_check("activity_hours_per_day", activity_hours_per_day),
        )
        s0 = BASELINE_SURVIVAL["male"]
    else:
        lp = _female_lp(
            age=a,
            ethnicity=eth,
            years_education=edu,
            estrogen=_level(estrogen, ESTROGEN_BETA, "estrogen"),
            diabetes=float(diabetes),
            pack_years=py,
            family_history=float(family_history),
            multivitamin=float(multivitamin),
            bmi=bmi,
            nsaid=_level(nsaid, NSAID_BETA, "nsaid"),
            alcohol=alc,
            emulate_deployed_defect=emulate_deployed_defect,
        )
        s0 = BASELINE_SURVIVAL["female"]

    risk = 1.0 - s0 ** math.exp(lp)
    return {
        "risk": risk,
        "linear_predictor": lp,
        "baseline_survival": s0,
        "bmi": bmi,
        "horizon_years": HORIZON_YEARS,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "colorectal",
        "citation": MODEL_CITATION,
        "notes": "10-year colorectal cancer risk; men and women have different "
        "predictor sets, not one model with a sex term",
    }
