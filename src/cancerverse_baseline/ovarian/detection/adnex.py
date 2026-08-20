"""IOTA ADNEX, five-category classification of an adnexal mass.

Van Calster B, Van Hoorde K, Valentin L, et al. Evaluating the risk of ovarian
cancer before surgery using the ADNEX model to differentiate between benign,
borderline, early and advanced stage invasive, and secondary metastatic
tumours: prospective multicentre diagnostic study. BMJ. 2014;349:g5920.

Coefficients are Appendix D of the supplement, "The formula of the ADNEX model
after retraining on the pooled data", the retrained version, not the
development one, which is the version the published performance refers to.

**Why this is here.** It replaces RMI (1990), the second-oldest model in the
library. In a 2026 prospective head-to-head on the same patients ADNEX scored
AUC 0.93 with CA-125 and 0.92 without, against RMI's 0.88. It also takes the
same class of inputs, an ultrasound examination plus CA-125, so the swap
costs no new data.

**Five outcomes, not two.** Benign, borderline, stage I invasive, stage II-IV
invasive, and secondary metastatic. RMI returns one number and a cut-off; this
returns a distribution over five diagnoses, which is what the referral decision
actually turns on: a borderline tumour and a stage III cancer imply different
surgery, and "malignant" does not distinguish them.

Two details that are easy to get wrong and are asserted in the tests:

- **CA-125 and lesion diameter enter as log base 2**, and the ratio of solid
  component to lesion diameter enters both linearly and squared. The squared
  term is what lets risk fall again for masses that are almost entirely solid.
- **`type of centre` is a predictor.** It is 1 for an oncology centre and 0
  otherwise, and it is not a patient characteristic, it encodes referral
  filtering. A prediction is only interpretable if this matches where the scan
  was actually done.

CA-125 is optional in clinical use of ADNEX. This implementation requires it,
because Appendix D publishes only the with-CA-125 formula; the without-CA-125
variant is a separately fitted model that the supplement does not give.
"""

from __future__ import annotations

import math
from typing import Any

AXIS = "detection"
MODEL_ID = "iota_adnex"
DISEASE = "ovarian"

#: Appendix D, verbatim. Rows are the four linear predictors z1..z4 (borderline,
#: stage I, stage II-IV, and metastatic, each versus benign); columns are the
#: intercept and the nine predictor terms in the order used below.
#:
#:   A  patient age (years)              F  number of papillary structures 0-4
#:   B  serum CA-125 (U/mL), log2        G  acoustic shadows (0/1)
#:   C  max lesion diameter (mm), log2   H  ascites (0/1)
#:   D  max solid component (mm)         I  oncology centre (0/1)
_Z = {
    # name          intercept      A          log2 B     log2 C     D/C        (D/C)^2    E          F          G          H          I
    "borderline":  (-7.577663,  0.004506,  0.111642,  0.372046,  6.967853, -5.65588,  1.375079,  0.604238, -2.04157,  0.971061,  0.953043),
    "stage_i":     (-12.276041, 0.017260,  0.197249,  0.873530,  9.583053, -5.83319,  0.791873,  0.400369, -1.87763,  0.452731,  0.452484),
    "stage_ii_iv": (-14.915830, 0.051239,  0.765456,  0.430477, 10.37696,  -5.70975,  0.273692,  0.389874, -2.35516,  1.348408,  0.459021),
    "metastatic":  (-11.909267, 0.033601,  0.276166,  0.449025,  6.644939, -2.30330,  0.899980,  0.215645, -2.49845,  1.636407,  0.808887),
}

OUTCOMES = ("benign", "borderline", "stage_i", "stage_ii_iv", "metastatic")

LABELS = {
    "benign": "benign",
    "borderline": "borderline tumour",
    "stage_i": "stage I invasive cancer",
    "stage_ii_iv": "stage II-IV invasive cancer",
    "metastatic": "secondary metastatic cancer",
}

SCOPE = (
    "IOTA phase 3 pooled data: women with at least one adnexal mass, examined "
    "by an experienced ultrasound operator and selected for surgery. It "
    "estimates what a mass IS, not whether one is present, so it does not "
    "apply to screening an unselected population. `oncology_centre` is part "
    "of the model and encodes referral filtering rather than the patient; a "
    "prediction is only interpretable if it matches where the scan was done."
)

CITATION = (
    "Van Calster B, Van Hoorde K, Valentin L, et al. BMJ. 2014;349:g5920 "
    "(coefficients from Appendix D of the supplement, retrained pooled model)"
)


def _bool01(value: Any, name: str) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if value in (0, 1, 0.0, 1.0):
        return float(value)
    raise ValueError(f"{name} must be True/False or 0/1; got {value!r}")


def linear_predictors(
    *,
    age: float,
    ca125: float,
    lesion_diameter_mm: float,
    solid_diameter_mm: float,
    more_than_10_locules: Any,
    papillary_structures: int,
    acoustic_shadows: Any,
    ascites: Any,
    oncology_centre: Any,
) -> dict[str, float]:
    """z1..z4, each versus benign."""
    if ca125 <= 0:
        raise ValueError("ca125 must be positive (it enters as log2)")
    if lesion_diameter_mm <= 0:
        raise ValueError("lesion_diameter_mm must be positive (it enters as log2)")
    if solid_diameter_mm < 0:
        raise ValueError("solid_diameter_mm cannot be negative")
    if solid_diameter_mm > lesion_diameter_mm:
        raise ValueError(
            "solid_diameter_mm cannot exceed lesion_diameter_mm: the solid "
            "component is part of the lesion, and D/C > 1 is outside anything "
            "the model was fitted on")
    if papillary_structures not in (0, 1, 2, 3, 4):
        raise ValueError(
            "papillary_structures is 0-4, where 4 means MORE THAN THREE, it "
            "is a capped count, not the raw number")

    ratio = solid_diameter_mm / lesion_diameter_mm
    x = (
        1.0,
        float(age),
        math.log2(float(ca125)),
        math.log2(float(lesion_diameter_mm)),
        ratio,
        ratio ** 2,
        _bool01(more_than_10_locules, "more_than_10_locules"),
        float(papillary_structures),
        _bool01(acoustic_shadows, "acoustic_shadows"),
        _bool01(ascites, "ascites"),
        _bool01(oncology_centre, "oncology_centre"),
    )
    return {name: sum(b * v for b, v in zip(betas, x, strict=True))
            for name, betas in _Z.items()}


def adnex_predict(
    *,
    age: float,
    ca125: float,
    lesion_diameter_mm: float,
    solid_diameter_mm: float,
    more_than_10_locules: Any = False,
    papillary_structures: int = 0,
    acoustic_shadows: Any = False,
    ascites: Any = False,
    oncology_centre: Any = False,
) -> dict[str, Any]:
    """Probability of each of the five diagnoses."""
    z = linear_predictors(
        age=age, ca125=ca125, lesion_diameter_mm=lesion_diameter_mm,
        solid_diameter_mm=solid_diameter_mm,
        more_than_10_locules=more_than_10_locules,
        papillary_structures=papillary_structures,
        acoustic_shadows=acoustic_shadows, ascites=ascites,
        oncology_centre=oncology_centre)

    exps = {k: math.exp(v) for k, v in z.items()}
    denom = 1.0 + sum(exps.values())
    probs = {"benign": 1.0 / denom}
    probs.update({k: v / denom for k, v in exps.items()})

    malignant = 1.0 - probs["benign"]
    most = max(probs, key=probs.get)
    return {
        # The headline number a triage decision uses: anything but benign.
        "risk": malignant,
        "risk_malignant": malignant,
        "probabilities": probs,
        "most_likely": most,
        "most_likely_label": LABELS[most],
        "linear_predictors": z,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": DISEASE,
        "citation": CITATION,
        "notes": (
            "Five categories, not two. `risk` is 1 - P(benign); the split "
            "between borderline, stage I, stage II-IV and metastatic is in "
            "`probabilities` and is what distinguishes referral decisions "
            "that 'malignant' alone cannot."
        ),
    }


predict = adnex_predict
