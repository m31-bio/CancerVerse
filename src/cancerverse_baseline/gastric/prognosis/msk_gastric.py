"""MSK gastric nomogram — disease-specific survival after R0 resection.

Equation source
---------------
Kattan MW, Karpeh MS, Mazumdar M, Brennan MF. "Postoperative nomogram for
disease-specific survival after an R0 resection for gastric carcinoma."
J Clin Oncol. 2003;21(19):3647-3650.

**The equation does not come from the paper.** The paper publishes a
points-and-axes nomogram figure and no closed-form model, which is why this
cell sat unimplemented for so long and why a request was open for a validation
paper that republished a recovered linear predictor. No such paper was needed:
Cleveland Clinic serves the deployed model's complete R source at

    https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/GastricCancer

which is the calculator hosted at riskcalc.org, and its own page cites Kattan
2003. Everything below is transcribed from that source. The paper remains the
scientific reference; the source is where the numbers are legible.

Form
----
    DSS(t) = S0(t) ** exp(Xb)          S0(5y) = 0.579053, S0(9y) = 0.5089101

    Xb = -2.3678975
       + 0.227464 [male]
       - 0.011606041 age
         + 3.4469803e-5 (age-48)^3+ - 8.4848746e-5 (age-67)^3+
         + 5.0378943e-5 (age-80)^3+
       + 0.23855249 [body/middle third] + 0.7131089 [GE junction]
         + 0.14158861 [proximal/upper third]
       - 0.19097534 [intestinal] - 0.075717935 [mixed]
       + 0.0097446167 size_cm
       + 0.34360148 posLN - 0.0096735309 (posLN)^3+
         + 0.010640884 (posLN-1)^3+ - 0.00096735309 (posLN-11)^3+
       - 0.047258944 negLN + 4.5172072e-5 (negLN-5)^3+
         - 7.2275315e-5 (negLN-17)^3+ + 2.7103243e-5 (negLN-37)^3+
       + 0.6913717 depth - 0.024435477 (depth-2)^3+
         + 0.048870953 (depth-4)^3+ - 0.024435477 (depth-6)^3+

Four things that are easy to get wrong
--------------------------------------
1. **Depth is an ordinal entered as a NUMBER, then splined.** The seven levels
   are coded 1-7 in the order mucosa, submucosa, propria muscularis, subserosa,
   suspected serosal invasion, definite serosal invasion, adjacent organ
   involvement. Treating it as a set of indicators, or reordering the levels,
   silently changes every prediction.
2. **Reference categories are the ones with no term**: female, Lauren diffuse,
   and antrum/pyloric primary site. Note diffuse is the reference even though
   it is the worst-prognosis Lauren type, so both other types carry *negative*
   coefficients.
3. **Negative nodes protect, and the effect is large.** The linear term is
   -0.047 per node with the count running to 146, so a thorough lymphadenectomy
   moves the prediction more than most single risk factors. That is the
   well-known stage-migration property of this nomogram, not an error.
4. **Age is non-monotonic.** The three spline terms produce a U-shaped age
   effect, which is why reading the published figure's age axis looked wrong
   when this model was first examined.

Scope
-----
Patients who have had an **R0 resection** for gastric carcinoma. The hosted
calculator validates its inputs to age 25-96, positive nodes 0-23, negative
nodes 0-146 and tumour size 0.1-21 cm; those bounds are enforced here, because
the splines are only anchored inside them.
"""

from __future__ import annotations

AXIS = "prognosis"
MODEL_ID = "msk_gastric"

# S0 at the two published horizons, in years.
BASELINE_SURVIVAL = {5: 0.579053, 9: 0.5089101}
SUPPORTED_YEARS = tuple(BASELINE_SURVIVAL)

INTERCEPT = -2.3678975

# Depth of invasion, ordinal 1-7 in the order the source factor declares them.
DEPTH_LEVELS = (
    "mucosa",
    "submucosa",
    "propria_muscularis",
    "subserosa",
    "suspected_serosal_invasion",
    "definite_serosal_invasion",
    "adjacent_organ_involvement",
)
DEPTH_CODE = {name: i for i, name in enumerate(DEPTH_LEVELS, start=1)}

# Reference level carries no term.
PRIMARY_SITE_BETA = {
    "antrum_or_pyloric": 0.0,                 # reference
    "body_or_middle_third": 0.23855249,
    "gastroesophageal_junction": 0.7131089,
    "proximal_or_upper_third": 0.14158861,
}
LAUREN_BETA = {
    "diffuse": 0.0,                           # reference
    "intestinal": -0.19097534,
    "mixed": -0.075717935,
}
MALE_BETA = 0.227464
SIZE_BETA = 0.0097446167

# Input bounds the hosted calculator enforces; the splines are anchored inside.
AGE_RANGE = (25.0, 96.0)
POSITIVE_NODES_RANGE = (0, 23)
NEGATIVE_NODES_RANGE = (0, 146)
SIZE_CM_RANGE = (0.1, 21.0)

MODEL_CITATION = (
    "Kattan MW, Karpeh MS, Mazumdar M, Brennan MF. J Clin Oncol. "
    "2003;21(19):3647-3650 (MSK postoperative gastric nomogram). Coefficients "
    "from the deployed model's published R source at riskcalc.org, since the "
    "paper itself publishes only a nomogram figure."
)


def _plus3(x: float) -> float:
    """(x)_+ cubed."""
    return x**3 if x > 0 else 0.0


def _check(name: str, value: float, lo: float, hi: float) -> float:
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be within [{lo}, {hi}], got {value}")
    return float(value)


def _normalize(value: str, table: dict, name: str) -> str:
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    key = key.replace("/", "_or_").replace("__", "_")
    if key not in table:
        raise ValueError(f"{name} must be one of {sorted(table)}, got {value!r}")
    return key


def linear_predictor(
    *,
    age: float,
    male: bool,
    primary_site: str,
    lauren: str,
    size_cm: float,
    positive_nodes: int,
    negative_nodes: int,
    depth: str,
) -> float:
    """X*beta for the MSK gastric nomogram."""
    a = _check("age", age, *AGE_RANGE)
    s = _check("size_cm", size_cm, *SIZE_CM_RANGE)
    p = _check("positive_nodes", positive_nodes, *POSITIVE_NODES_RANGE)
    n = _check("negative_nodes", negative_nodes, *NEGATIVE_NODES_RANGE)

    site = _normalize(primary_site, PRIMARY_SITE_BETA, "primary_site")
    lau = _normalize(lauren, LAUREN_BETA, "lauren")
    d_key = _normalize(depth, DEPTH_CODE, "depth")
    d = float(DEPTH_CODE[d_key])

    lp = INTERCEPT
    lp += MALE_BETA * (1.0 if male else 0.0)
    lp += (
        -0.011606041 * a
        + 3.4469803e-05 * _plus3(a - 48.0)
        - 8.4848746e-05 * _plus3(a - 67.0)
        + 5.0378943e-05 * _plus3(a - 80.0)
    )
    lp += PRIMARY_SITE_BETA[site]
    lp += LAUREN_BETA[lau]
    lp += SIZE_BETA * s
    lp += (
        0.34360148 * p
        - 0.0096735309 * _plus3(p)
        + 0.010640884 * _plus3(p - 1.0)
        - 0.00096735309 * _plus3(p - 11.0)
    )
    lp += (
        -0.047258944 * n
        + 4.5172072e-05 * _plus3(n - 5.0)
        - 7.2275315e-05 * _plus3(n - 17.0)
        + 2.7103243e-05 * _plus3(n - 37.0)
    )
    lp += (
        0.6913717 * d
        - 0.024435477 * _plus3(d - 2.0)
        + 0.048870953 * _plus3(d - 4.0)
        - 0.024435477 * _plus3(d - 6.0)
    )
    return lp


def msk_gastric_predict(
    *,
    age: float,
    male: bool,
    primary_site: str,
    lauren: str,
    size_cm: float,
    positive_nodes: int,
    negative_nodes: int,
    depth: str,
    years: int = 5,
) -> dict:
    """
    Disease-specific survival at 5 or 9 years after an R0 resection.

    `depth` is one of DEPTH_LEVELS, `primary_site` one of PRIMARY_SITE_BETA,
    `lauren` one of LAUREN_BETA. Only 5 and 9 years are published, so any other
    horizon is refused rather than interpolated.
    """
    import math

    if years not in BASELINE_SURVIVAL:
        raise ValueError(
            f"years must be one of {SUPPORTED_YEARS} (the published horizons), "
            f"got {years}"
        )
    lp = linear_predictor(
        age=age, male=male, primary_site=primary_site, lauren=lauren,
        size_cm=size_cm, positive_nodes=positive_nodes,
        negative_nodes=negative_nodes, depth=depth,
    )
    s0 = BASELINE_SURVIVAL[years]
    survival = s0 ** math.exp(lp)
    return {
        "survival": survival,
        "risk": 1.0 - survival,
        "linear_predictor": lp,
        "baseline_survival": s0,
        "years": years,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "gastric",
        "citation": MODEL_CITATION,
        "notes": "disease-specific survival after R0 resection; depth is an "
        "ordinal 1-7 entered as a continuous splined term",
    }
