"""END-PAC, pancreatic cancer risk in new-onset diabetes (Sharma et al., 2018).

Equation source
---------------
Sharma A, Kandlakunta H, Nagpal SJS, et al. "Model to Determine Risk of
Pancreatic Cancer in Patients With New-Onset Diabetes." Gastroenterology.
2018;155(3):730-739.e3. Table 1 ("END-PDAC score parameters"), read from the
NIH author manuscript.

Around 1% of people over 50 with new-onset diabetes are diagnosed with
pancreatic cancer within 3 years, diabetes can be a *consequence* of the
tumour rather than a risk factor for it. END-PAC separates that group from
ordinary type 2 diabetes using three signals available in routine records.

    A. Blood glucose change  = BG_category(at diabetes onset) - BG_category(1y before)
       BG categories: <100 -> 1, 100-109 -> 2, 110-125 -> 3, 126-160 -> 4, >160 -> 5
       so A ranges 1-4  (note: a CATEGORY difference, not a mg/dL difference)

       Table 1 labels categories 1-3 as "BG category at -1 years" and 4-5 as
       "BG category at glycemically-defined new-onset diabetes", and states the
       score range as 1-4. That is not a free 1-5 scale on both sides: by the
       definition of glycemically-defined new-onset diabetes the earlier
       reading is below 126 mg/dL and the later one is at or above it. The
       module enforces this (see `_check_glucose_pair`), without it, an
       out-of-scope pair such as a FALL from diabetic to normal silently yields
       a score far outside the published range.

       CAUTION, added 2026-08-18: that guard is OURS, not the paper's, and it
       is stricter than the paper's own data. Sharma et al. never state the
       rule; it was inferred from Table 1's category labelling. Table 3
       ("Univariate model for predictors of pancreatic cancer in new-onset
       diabetes") has a "Blood Glucose category at -1y" block whose top row is
       ">=126 (Category 4)", holding 3 (5%) of PC-NOD and 45 (23%) of T2-NOD
       subjects. So roughly a fifth of the paper's own discovery cohort had a
       >=126 reading a year before onset and was still scored, and this module
       would refuse every one of them. Treat the guard as an implementation
       choice under review, not as a published constraint.

    B. Weight change (kg over the preceding year), LOSS scores positive:
       <= -6.0 -> +6,  -5.9..-4.0 -> +4,  -3.9..-2.0 -> +2,  -1.9..+1.9 -> 0,
       +2.0..+3.9 -> -2,  +4.0..+5.9 -> -4,  >= +6.0 -> -6

    C. Age at diabetes onset: <=59 -> -1,  60-69 -> 0,  >=70 -> +1

    Total = A + B + C

Thresholds from the paper: **>= 3** is the high-risk cut (80% sensitivity and
specificity in discovery; in validation it caught 7/9 cancers, sensitivity
78%, with a 3.6% cancer prevalence, 4.4x the base rate). The low-risk group
is **<= 0**, and the intermediate group is exactly **1 or 2**.

The validation SPECIFICITY is stated twice and differently, 2026-08-18
------------------------------------------------------------------------
The abstract says the >= 3 cut had "**85% specificity**"; the Results say
"sensitivity of 78%, **specificity of 82%**" for the same cohort and the same
cut-off. Both cannot be right, and the paper never reconciles them. This
module used to quote the abstract's 85%, which is the same source the
abstract's "<0" typo came from, and this project already decided against it
once (below). The Results figure is preferred for the same reason: it is the
fuller statement, giving sensitivity and specificity together in the section
that reports the validation. **Neither figure is used in any computation** —
END-PAC emits a score and a band, not a probability, so this is a
documentation correction, not a behavioural one. It is recorded rather than
silently swapped because the discrepancy is a fact about the paper that the
next reader will hit too.

The <= 0 boundary is worth defending, because the paper states it both ways
-----------------------------------------------------------------------------
The abstract writes "An END-PAC score **<0** (in 49% of subjects) meant that
patients had an extremely low-risk", but the Results write "Two PC-NODs
subjects (2%) had an END-PAC score **<=0** to 632 T2-NOD subjects (**49%**)".
Same 49%, two different inequalities, so one of them is a slip.

The paper's own group proportions settle it. Its three groups are quoted as
">=3", "1 or 2" and "<=0", and they sum to exactly 100% in both cohorts:

    T2-NOD   19% + 32% + 49% = 100%
    PC-NOD   77% + 21% +  2% = 100%

A partition of the score line into {>=3, 1..2, <0} would leave score 0 with no
group and could not sum to 100%. The Results text is right and the abstract's
"<0" is the typo. Two further passages agree with the Results ("530 subjects
(48%) had an END-PAC score of <=0"; "42 subjects (57%) had an END-PAC score of
<=0").

This module previously implemented the abstract's "<0", which put a score of
exactly 0 in the intermediate group, the boundary between "extremely low risk,
reassure" and "needs follow-up".

Two details that are easy to get wrong
--------------------------------------
1. The glucose term is a **difference of category indices**, not of mg/dL
   values. A rise from 95 to 130 mg/dL is category 1 -> 4, i.e. A = 3. The
   paper's Table 2 footnote describes a *different* model variant ("model B")
   that scored 1 point per 10 mg/dL; that is not this score.
2. **Weight LOSS is positive.** Losing >= 6 kg scores +6; gaining >= 6 kg
   scores -6. Sign errors here invert the whole model.

Population: adults (the validation work is in >= 50-year-olds) with
glycemically-defined new-onset diabetes. Not a general-population screening
tool, it enriches an already-selected group.
"""

from __future__ import annotations

AXIS = "detection"
MODEL_ID = "endpac"

HIGH_RISK_THRESHOLD = 3
# The paper's three groups are ">=3", "1 or 2" and "<=0", an exhaustive,
# non-overlapping partition whose proportions sum to exactly 100% in both
# cohorts. See the module docstring: the abstract's "<0" is a typo.
LOW_RISK_AT_OR_BELOW = 0
INTERMEDIATE_SCORES = (1, 2)

# Table 1 assigns categories 1-3 to the -1 year reading and 4-5 to the reading
# at diabetes onset. Score range for the glucose term is therefore 1-4.
DIABETES_GLUCOSE_MG_DL = 126.0
GLUCOSE_SCORE_RANGE = (1, 4)
TOTAL_SCORE_RANGE = (1 - 6 - 1, 4 + 6 + 1)  # A + B + C  ->  -6 .. 11

MODEL_CITATION = (
    "Sharma A, Kandlakunta H, Nagpal SJS, et al. Gastroenterology. "
    "2018;155(3):730-739.e3, Table 1 (END-PAC score)."
)


def bg_category(glucose_mg_dl: float) -> int:
    """Blood-glucose category index, 1-5 (Table 1)."""
    if glucose_mg_dl <= 0:
        raise ValueError(f"glucose must be > 0 mg/dL, got {glucose_mg_dl}")
    if glucose_mg_dl < 100:
        return 1
    if glucose_mg_dl < 110:
        return 2
    if glucose_mg_dl <= 125:
        return 3
    if glucose_mg_dl <= 160:
        return 4
    return 5


def weight_score(weight_change_kg: float) -> int:
    """Weight change over the preceding year. LOSS is negative input, positive score."""
    if weight_change_kg <= -6.0:
        return 6
    if weight_change_kg <= -4.0:
        return 4
    if weight_change_kg <= -2.0:
        return 2
    if weight_change_kg < 2.0:
        return 0
    if weight_change_kg < 4.0:
        return -2
    if weight_change_kg < 6.0:
        return -4
    return -6


def age_score(age: float) -> int:
    if age <= 0:
        raise ValueError(f"age must be > 0, got {age}")
    if age <= 59:
        return -1
    if age <= 69:
        return 0
    return 1


def _check_glucose_pair(at_diabetes: float, one_year_before: float) -> None:
    """The score is defined only for someone who actually crossed into diabetes.

    Table 1 splits the BG categories by timepoint: 1-3 belong to the -1 year
    reading, 4-5 to the reading at diagnosis. Feeding a pair that violates that
    split produces a glucose term outside the published 1-4 range and a total
    outside 1-11, which is meaningless rather than merely unusual.
    """
    if at_diabetes < DIABETES_GLUCOSE_MG_DL:
        raise ValueError(
            f"glucose_at_diabetes_mg_dl must be >= {DIABETES_GLUCOSE_MG_DL:.0f} "
            f"(glycemically-defined new-onset diabetes), got {at_diabetes}"
        )
    if one_year_before >= DIABETES_GLUCOSE_MG_DL:
        raise ValueError(
            f"glucose_one_year_before_mg_dl must be < {DIABETES_GLUCOSE_MG_DL:.0f} "
            f"— the patient would already have been diabetic, so this is not "
            f"new-onset diabetes; got {one_year_before}"
        )


def endpac_predict(
    *,
    glucose_at_diabetes_mg_dl: float,
    glucose_one_year_before_mg_dl: float,
    weight_change_kg: float,
    age_at_diabetes_onset: float,
) -> dict:
    """
    END-PAC score and risk band for a patient with new-onset diabetes.

    `weight_change_kg` is the change over the preceding year: **negative for
    weight loss**, which is the direction that raises the score.

    Both glucose values are required to be consistent with new-onset diabetes:
    below 126 mg/dL a year earlier, at or above it at diagnosis. Anything else
    is outside the model's scope and raises.
    """
    _check_glucose_pair(glucose_at_diabetes_mg_dl, glucose_one_year_before_mg_dl)
    bg_now = bg_category(glucose_at_diabetes_mg_dl)
    bg_before = bg_category(glucose_one_year_before_mg_dl)
    a = bg_now - bg_before
    b = weight_score(weight_change_kg)
    c = age_score(age_at_diabetes_onset)
    total = a + b + c

    if total >= HIGH_RISK_THRESHOLD:
        band = "high"
    elif total <= LOW_RISK_AT_OR_BELOW:
        band = "very_low"
    else:
        band = "intermediate"

    return {
        "score": total,
        "risk_band": band,
        "risk": None,  # point score, not a probability
        "components": {"glucose": a, "weight": b, "age": c},
        "bg_category_now": bg_now,
        "bg_category_before": bg_before,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "pancreatic",
        "citation": MODEL_CITATION,
        "notes": "score >=3 high risk (~4.4x enrichment); 1-2 intermediate; "
        "<=0 extremely low risk; "
        "enriches an already-selected new-onset-diabetes group, not a "
        "general-population screen",
    }
