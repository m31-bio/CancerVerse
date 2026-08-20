"""Ang 2010 recursive-partitioning risk groups for HPV-associated oropharyngeal cancer.

Equation source
---------------
Ang KK, Harris J, Wheeler R, et al. "Human Papillomavirus and Survival of
Patients with Oropharyngeal Cancer." N Engl J Med. 2010;363(1):24-35 (RTOG
0129). PMC2943767.

Exact quote from the Results section (the decision tree, verbatim):

    "Patients with HPV-positive tumors were considered to be at low risk, with
    the exception of smokers with a high nodal stage (i.e., N2b to N3), who
    were considered to be at intermediate risk; patients with HPV-negative
    tumors were considered to be at high risk, with the exception of
    nonsmokers with tumors of stage T2 or T3, who were considered to be at
    intermediate risk."

The paper separately identifies the smoking dichotomization used by the
recursive-partitioning algorithm as pack-years <=10 vs. >10 (this is the
"heavy smoker" split for the HPV-positive branch, confirmed independently by
Fakhry et al.'s external validation of these risk groups, e.g. Cancer.
2019;125(12):2027-2038, which states low risk = HPV+ with <=10 pack-years
(any N) or HPV+ with >10 pack-years and N0-N2a; intermediate = HPV+ with >10
pack-years and N2b-N3).

3-year overall survival by group: low 93.0% (95% CI 88.3-97.7), intermediate
70.8% (95% CI 60.7-80.8), high 46.2% (95% CI 34.7-57.7). Hazard ratios vs. low
risk: intermediate 3.54, high 7.16.

TWO OPERATIONALIZATIONS, SELECTABLE VIA `definition`
-----------------------------------------------------
The primary text leaves two things unstated, and the validation literature
resolves them differently from a literal reading.

**1. What "nonsmokers" means.** Ang's Results text says ">10 pack-years" on the
HPV-positive branch but "nonsmokers" on the HPV-negative one. Fakhry et al.'s
external validation (Cancer 2019;125:2027-2038, PMC6594017) operationalizes
BOTH branches as "low tobacco exposure", the same <=10 pack-years split.
That settles it; this module applies <=10/>10 to both branches either way.

**2. Where T1 falls.** Ang names only "T2 or T3" in the HPV-negative
intermediate exception and is silent on T1. Fakhry operationalizes the same
group as "low tobacco exposure and <T4", which includes T1.

    definition="ang2010" (default)   HPV-neg, low smoking, T2/T3 -> intermediate
                                     T1 -> high   (literal reading)
    definition="fakhry"              HPV-neg, low smoking, <T4   -> intermediate
                                     T1 -> intermediate

The two differ for exactly one cell: HPV-negative, low-smoking, T1. RTOG 0129
enrolled stage III-IV disease, so T1 was likely rare or absent in that
subgroup, which plausibly explains the primary's silence. The default is the
literal primary reading, per this project's rule of reproducing what was
published; use "fakhry" when comparing against published validation cohorts.

Verbatim from Fakhry: low risk = "HPV-positive patients with low tobacco
exposure (regardless of T- or N-classification) or >10 pack-years and one
ipsilateral lymph node <6 centimeter"; intermediate = "HPV-positive patients
with >10 pack-years and advanced nodal disease ... as well as HPV-negative
patients with low tobacco exposure and <T4"; high = "HPV-negative patients
with >10 pack-years or T4".
"""

from __future__ import annotations

AXIS = "prognosis"
MODEL_ID = "ang2010_rpa"

PACK_YEARS_THRESHOLD = 10.0
HIGH_N_STAGES = {"n2b", "n2c", "n3"}

# HPV-negative intermediate-risk exception, by operationalization.
INTERMEDIATE_T_STAGES_HPV_NEGATIVE = {
    "ang2010": {"t2", "t3"},  # literal: the primary names only T2/T3
    "fakhry": {"t1", "t2", "t3"},  # validation: "<T4"
}
DEFINITIONS = tuple(INTERMEDIATE_T_STAGES_HPV_NEGATIVE)

THREE_YEAR_OS = {
    "low": 0.930,
    "intermediate": 0.708,
    "high": 0.462,
}
THREE_YEAR_OS_CI = {
    "low": (0.883, 0.977),
    "intermediate": (0.607, 0.808),
    "high": (0.347, 0.577),
}
HAZARD_RATIO_VS_LOW = {
    "intermediate": 3.54,
    "high": 7.16,
}

MODEL_CITATION = (
    "Ang KK et al. N Engl J Med. 2010;363(1):24-35 (RTOG 0129). PMC2943767. "
    "Risk-group definitions verbatim from the Results section."
)


def _normalize_stage(stage: str, *, kind: str) -> str:
    s = stage.strip().lower()
    for prefix in ("c", "p"):
        if s.startswith(prefix) and len(s) > 1 and s[1] in "nt":
            s = s[1:]
    if kind == "n" and not s.startswith("n"):
        raise ValueError(f"n_stage must look like 'N0'..'N3', got {stage!r}")
    if kind == "t" and not s.startswith("t"):
        raise ValueError(f"t_stage must look like 'T1'..'T4', got {stage!r}")
    return s


def ang2010_rpa_predict(
    *,
    hpv_positive: bool,
    pack_years: float,
    n_stage: str,
    t_stage: str,
    definition: str = "ang2010",
) -> dict:
    """
    RTOG 0129 recursive-partitioning risk group for oropharyngeal cancer.

    Parameters
    ----------
    hpv_positive : p16/HPV status of the tumor.
    pack_years : lifetime smoking pack-years (0 for never-smokers).
    n_stage : AJCC 7th-edition N stage, e.g. "N0".."N3" (accepts "N2b" etc.,
        and a leading "c"/"p" prefix).
    t_stage : AJCC 7th-edition T stage, e.g. "T1".."T4".

    definition : "ang2010" (default, literal primary reading) or "fakhry"
        (the validation literature's operationalization). They differ only for
        HPV-negative, low-smoking **T1** tumours: high vs intermediate. See the
        module docstring.
    """
    if definition not in INTERMEDIATE_T_STAGES_HPV_NEGATIVE:
        raise ValueError(f"definition must be one of {DEFINITIONS}, got {definition!r}")
    if pack_years < 0:
        raise ValueError(f"pack_years must be >= 0, got {pack_years}")
    n = _normalize_stage(n_stage, kind="n")
    t = _normalize_stage(t_stage, kind="t")
    heavy_smoker = pack_years > PACK_YEARS_THRESHOLD

    if hpv_positive:
        if heavy_smoker and n in HIGH_N_STAGES:
            group = "intermediate"
        else:
            group = "low"
    else:
        if (not heavy_smoker) and t in INTERMEDIATE_T_STAGES_HPV_NEGATIVE[definition]:
            group = "intermediate"
        else:
            group = "high"

    return {
        "risk_group": group,
        "definition": definition,
        "risk": None,  # decision-tree group, not a per-patient probability
        "three_year_os": THREE_YEAR_OS[group],
        "three_year_os_ci": THREE_YEAR_OS_CI[group],
        "hazard_ratio_vs_low": HAZARD_RATIO_VS_LOW.get(group),
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "head_neck",
        "citation": MODEL_CITATION,
        "notes": "3-year OS by RPA group; HPV-negative smoking threshold is a documented ambiguity, see module docstring",
    }
