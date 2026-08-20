"""Kunzmann model — esophageal adenocarcinoma risk in primary care.

Equation source
---------------
Kunzmann AT, Thrift AP, Cardwell CR, et al. "Model for Identifying Individuals
at Risk for Esophageal Adenocarcinoma." Clin Gastroenterol Hepatol. Table 2 —
stepwise logistic regression with an accompanying points-based model.

Points table, transcribed from Table 2 (total 0-15):

    Age (y)      50-55  0     55-60  1.5   60-65  2.5   65+  3.5
    Sex          female 0     male   4.0
    BMI          <25    0     25-<30 1.0   30-<35 1.5   35+  2.5
    Smoking      never  0     former 2.0   current 3.5
    Esophageal condition (reflux/Barrett's etc.)  no 0   yes 1.5

    Screening referral threshold: **>= 8 points**

The points are the fitted coefficients divided by the smallest coefficient in
the model and rounded to the nearest 0.5 — the paper's own construction, so the
points ARE the model, not a lossy summary of it.

The divisor: the paper gives two, and only one works
-----------------------------------------------------
The Methods worked example says the smallest coefficient is **0.40** ("the
coefficient for men was 1.64, and the smallest coefficient in the model was
0.40 ... so men were assigned 4 points (1.64/0.40, then rounded to nearest
0.5)"). The Table 2 footnote says **0.41**.

Table 2 settles it without appeal to authority. Each published point constrains
the divisor, since round_to_half(b/d) == p requires p-0.25 <= b/d < p+0.25.
Intersecting all ten rows admits only

    d in (0.3958, 0.4046]

which contains the Methods' 0.40 and excludes the footnote's 0.41. With 0.41,
"Smoking, former" comes out 1.5 against a published 2.0. Note that ln(1.50) =
0.4055 is also outside the interval, and narrowly — which is likely where the
footnote came from: recomputing the smallest coefficient from the rounded odds
ratio rather than reading the fitted value. It also implies the true BMI 25-<30
odds ratio is about 1.492-1.499, printed as 1.50.

An earlier version of this docstring repeated the footnote's 0.41.

What the model is not
---------------------
This predicts **esophageal adenocarcinoma (EAC) only**, not squamous cell
carcinoma. The two are different diseases with different risk factors: ESCC is
driven by alcohol, tobacco and hot beverages and dominates incidence in East
Asia and East Africa, while EAC is driven by reflux, obesity and male sex and
dominates in Western populations. Applying this model where ESCC predominates
would be a category error.

Developed in a UK primary-care population aged 50+. Male sex alone carries 4.0
of the 15 available points — more than any other single factor and half of the
referral threshold, reflecting the roughly 5-fold male excess in EAC.

Factors tested and dropped by stepwise selection: height, respiratory
sympathomimetic use, statins, diabetes, hypertension, high baseline BP.
"""

from __future__ import annotations

AXIS = "detection"
MODEL_ID = "kunzmann"

REFERRAL_THRESHOLD = 8.0
MAX_POINTS = 15.0
MIN_AGE = 50.0

SEX_POINTS = {"male": 4.0, "female": 0.0}
SMOKING_POINTS = {"never": 0.0, "former": 2.0, "current": 3.5}
ESOPHAGEAL_CONDITION_POINTS = 1.5

# Table 2's construction: points = round_to_half(coefficient / SMALLEST_COEFFICIENT),
# where the coefficients are the printed 2-decimal values. See the docstring —
# the Methods worked example says 0.40 and the Table 2 footnote says 0.41, and
# only 0.40 reproduces all ten published point values.
SMALLEST_COEFFICIENT = 0.40

MODEL_CITATION = (
    "Kunzmann AT, Thrift AP, Cardwell CR, et al. Clin Gastroenterol Hepatol., "
    "Table 2 (points-based esophageal adenocarcinoma risk model)."
)


def age_points(age: float) -> float:
    if age < MIN_AGE:
        raise ValueError(
            f"model was developed in adults aged {MIN_AGE:.0f}+, got {age}"
        )
    if age < 55:
        return 0.0
    if age < 60:
        return 1.5
    if age < 65:
        return 2.5
    return 3.5


def bmi_points(bmi: float) -> float:
    if bmi <= 0:
        raise ValueError(f"bmi must be > 0, got {bmi}")
    if bmi < 25:
        return 0.0
    if bmi < 30:
        return 1.0
    if bmi < 35:
        return 1.5
    return 2.5


def kunzmann_predict(
    *,
    age: float,
    male: bool,
    bmi: float,
    smoking: str,
    esophageal_condition: bool,
) -> dict:
    """
    Kunzmann points (0-15) for esophageal ADENOCARCINOMA risk.

    `smoking` is one of never / former / current. `esophageal_condition` means
    a recorded esophageal diagnosis or treatment (reflux, Barrett's, etc.).
    """
    smoke = smoking.strip().lower()
    if smoke not in SMOKING_POINTS:
        raise ValueError(
            f"smoking must be one of {sorted(SMOKING_POINTS)}, got {smoking!r}"
        )

    components = {
        "age": age_points(age),
        "sex": SEX_POINTS["male" if male else "female"],
        "bmi": bmi_points(bmi),
        "smoking": SMOKING_POINTS[smoke],
        "esophageal_condition": (
            ESOPHAGEAL_CONDITION_POINTS if esophageal_condition else 0.0
        ),
    }
    score = sum(components.values())
    return {
        "score": score,
        "refer_for_screening": score >= REFERRAL_THRESHOLD,
        "risk": None,  # point score, not a probability
        "components": components,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "esophageal",
        "citation": MODEL_CITATION,
        "notes": "adenocarcinoma only (not squamous); UK primary care, age 50+; "
        "referral threshold >= 8 of 15 points",
    }
