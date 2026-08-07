"""Cervical CIN2+/CIN3+ risk from hrHPV, cytology and age (Xia et al., BMC Med 2021).

Equation source
---------------
"Development of models for cervical cancer screening: construction in a
cross-sectional population and validation in two screening cohorts in China."
BMC Medicine. 2021;19:237. doi:10.1186/s12916-021-02078-2 (open access).
Coefficients from Additional file 1, **Table S1** ("Logistic Regression
Parameters"), retrieved from the PMC-mirrored supplement (PMC8414700).

Four nested logistic models. All share hrHPV + cytology + age; the extended
ones add HPV16/18 E6 oncoprotein and/or extended genotyping:

    logit(p) = intercept + b_hrHPV*hrHPV + b_cytology + b_age*age  [+ b_E6*E6]
                                                                  [+ genotype terms]

Cytology is a 7-level categorical with **NILM as the reference** (contributing
0). The remaining six levels each carry their own beta, and they are strongly
ordered: SCC/ADC at 7.199 is by far the largest single term in the model —
about 3.5x the hrHPV coefficient.

Age carries a small NEGATIVE coefficient (-0.019 in the base model). That is
not an error: conditional on hrHPV status and cytology, older women in this
screening population were at slightly lower CIN risk, because prevalent HPV
infection in younger women is more likely to be transient but is still counted
as positive. Do not "correct" the sign.

Why this model and not ASCCP
----------------------------
ASCCP risk-based management is a lookup of CIN3+ risk over combinations of
current and prior results — a consensus data table, not an equation, and so
not reproducible in this project's sense. This model is a published logistic
regression with printed coefficients, which is.

Scope
-----
Chinese screening population; outcome CIN2+/CIN3+ at colposcopy, not invasive
cancer incidence over time. Cytology must be reported on the Bethesda system.
Genotyping variants expect the paper's specific pooled groups (e.g. 33/58,
59/56/66, 39/68/35), which are not interchangeable with other groupings.
"""

from __future__ import annotations

import math

AXIS = "detection"
MODEL_ID = "cervical_cin_risk"

CYTOLOGY_LEVELS = ("NILM", "ASC-US", "ASC-H", "AGC", "LSIL", "HSIL/AIS", "SCC/ADC")
GENOTYPE_GROUPS = (
    "HPV16", "HPV18", "HPV45", "HPV33/58", "HPV31",
    "HPV59/56/66", "HPV51", "HPV52", "HPV39/68/35",
)

# Table S1. NILM is the cytology reference level and carries no term.
MODELS: dict[str, dict[str, float]] = {
    "base": {
        "intercept": -3.19059, "hrHPV": 2.06771, "age": -0.01935,
        "ASC-US": 1.36354, "ASC-H": 3.55612, "AGC": 4.28591,
        "LSIL": 1.51085, "HSIL/AIS": 4.90115, "SCC/ADC": 7.19866,
    },
    "e6": {
        "intercept": -1.63734, "hrHPV": 1.92905, "age": -0.04903, "E6": 1.9361,
        "ASC-US": 1.47615, "ASC-H": 2.97602, "AGC": 4.89681,
        "LSIL": 1.38943, "HSIL/AIS": 4.23318, "SCC/ADC": 6.37628,
    },
    "genotyping": {
        "intercept": -3.24223, "hrHPV": 1.51746, "age": -0.01872,
        "ASC-US": 1.43124, "ASC-H": 3.34987, "AGC": 4.16086,
        "LSIL": 1.45479, "HSIL/AIS": 4.49912, "SCC/ADC": 6.80578,
        "HPV16": 1.44896, "HPV18": 0.95014, "HPV45": 0.12346,
        "HPV33/58": 0.79158, "HPV31": 0.35975, "HPV59/56/66": -1.14307,
        "HPV51": -1.08557, "HPV52": 0.89489, "HPV39/68/35": 0.6052,
    },
    "full": {
        "intercept": -1.93218, "hrHPV": 1.51297, "age": -0.044, "E6": 1.98602,
        "ASC-US": 1.58716, "ASC-H": 2.93224, "AGC": 4.85179,
        "LSIL": 1.37952, "HSIL/AIS": 4.21336, "SCC/ADC": 6.33502,
        "HPV16": 0.88724, "HPV18": -0.40204, "HPV45": 0.06988,
        "HPV33/58": 0.79169, "HPV31": 0.44194, "HPV59/56/66": -0.99504,
        "HPV51": -0.98537, "HPV52": 1.09372, "HPV39/68/35": 0.78841,
    },
}

MODEL_CITATION = (
    "Development of models for cervical cancer screening. BMC Medicine. "
    "2021;19:237. doi:10.1186/s12916-021-02078-2, Additional file 1 Table S1."
)


def _normalize_cytology(cytology: str) -> str:
    c = cytology.strip().upper().replace(" ", "")
    aliases = {
        "NILM": "NILM", "NORMAL": "NILM", "NEGATIVE": "NILM",
        "ASCUS": "ASC-US", "ASC-US": "ASC-US",
        "ASCH": "ASC-H", "ASC-H": "ASC-H",
        "AGC": "AGC", "LSIL": "LSIL",
        "HSIL": "HSIL/AIS", "AIS": "HSIL/AIS", "HSIL/AIS": "HSIL/AIS",
        "SCC": "SCC/ADC", "ADC": "SCC/ADC", "SCC/ADC": "SCC/ADC",
    }
    if c not in aliases:
        raise ValueError(f"cytology must be one of {CYTOLOGY_LEVELS}, got {cytology!r}")
    return aliases[c]


def cervical_cin_risk_predict(
    *,
    hrhpv_positive: bool,
    cytology: str,
    age: float,
    variant: str = "base",
    e6_positive: bool | None = None,
    genotypes: dict[str, bool] | None = None,
) -> dict:
    """
    Probability of CIN2+/CIN3+ at colposcopy.

    `variant` selects the published model: base / e6 / genotyping / full.
    `e6_positive` is required for the e6 and full variants; `genotypes` is a
    mapping of the paper's pooled genotype groups to booleans and is required
    for the genotyping and full variants.
    """
    if variant not in MODELS:
        raise ValueError(f"variant must be one of {sorted(MODELS)}, got {variant!r}")
    if age <= 0:
        raise ValueError(f"age must be > 0, got {age}")
    b = MODELS[variant]
    cyt = _normalize_cytology(cytology)

    lp = b["intercept"] + b["hrHPV"] * (1.0 if hrhpv_positive else 0.0) + b["age"] * age
    if cyt != "NILM":                      # NILM is the reference level
        lp += b[cyt]

    if "E6" in b:
        if e6_positive is None:
            raise ValueError(f"variant {variant!r} requires e6_positive")
        lp += b["E6"] * (1.0 if e6_positive else 0.0)
    elif e6_positive is not None:
        raise ValueError(f"variant {variant!r} does not use e6_positive")

    uses_genotypes = any(g in b for g in GENOTYPE_GROUPS)
    if uses_genotypes:
        if genotypes is None:
            raise ValueError(f"variant {variant!r} requires genotypes")
        unknown = set(genotypes) - set(GENOTYPE_GROUPS)
        if unknown:
            raise ValueError(f"unknown genotype groups: {sorted(unknown)}")
        for g in GENOTYPE_GROUPS:
            if genotypes.get(g):
                lp += b[g]
    elif genotypes is not None:
        raise ValueError(f"variant {variant!r} does not use genotypes")

    return {
        "risk": 1.0 / (1.0 + math.exp(-lp)),
        "linear_predictor": lp,
        "variant": variant,
        "cytology": cyt,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "cervical",
        "citation": MODEL_CITATION,
        "notes": "CIN2+/CIN3+ at colposcopy in a Chinese screening population; "
        "NILM is the cytology reference; age coefficient is negative by design",
    }
