"""ABC method — serological stratification of gastric cancer risk.

Not a regression: a 2x2 rule over two serum tests. H. pylori antibody and
serum-pepsinogen "atrophic" status are each dichotomised; the four
combinations define groups A-D, each with a published annual gastric-cancer
incidence rate.

    PG+ ("atrophic")  <=>  PG I <= 70 ng/mL  AND  PG I / PG II <= 3.0

    group  Hp    PG      annual incidence
    A      -     -       0.04%
    B      +     -       0.06%
    C      +     +       0.35%
    D      -     +       0.60%

Group ordering is NOT monotone in either test alone: group D (seronegative
WITH atrophy) is the highest-risk group, because extensive atrophy destroys
the niche H. pylori lives in, so the antibody titre falls as damage
progresses. That interaction — not either test alone — is the point of the
method.

Equation source
----------------
Watabe H, Mitsushima T, Yamaji Y, et al. Predicting the development of
gastric cancer from combining Helicobacter pylori antibodies and serum
pepsinogen status: a prospective endoscopic cohort study. Gut.
2005;54(6):764-768. doi:10.1136/gut.2004.055400 — group definitions from
Table 1/Methods, incidence rates from Table 2, hazard ratios from Table 3.
PMC1774550, retrieved 2026-08-05. Rates cross-checked by re-deriving
cases/(subjects x mean follow-up) from Tables 1-2: 7/(3324*4.8y)=0.044%/y,
6/(2134*4.7y)=0.060%/y, 18/(1082*4.7y)=0.354%/y, 12/(443*4.5y)=0.602%/y.

The "ABC" name and screening-interval scheme are Miki K's (Gastric Cancer
2006; Proc Jpn Acad Ser B 2011;87:405-414); the incidence rates implemented
here are Watabe's prospective-cohort numbers.

Caveats
-------
Group A is low-risk, not zero-risk (7/3324 group-A subjects still developed
gastric cancer). The rule is invalid after H. pylori eradication therapy —
seroreversion moves people into A/B while atrophy, and risk, persists. Both
tests are assay-specific (Biomerica GAP-IgG; PG I/II cutoff pair) and do not
transfer across assays without a bridging study. The absolute rates are
Japanese rates (age-standardised incidence ~27/100,000); in lower-incidence
populations the ordering holds but the absolute numbers do not transfer.
"""

from __future__ import annotations

AXIS = "detection"
MODEL_ID = "abc_method"

PG1_ATROPHIC_CUTOFF = 70.0       # ng/mL, inclusive
PG_RATIO_ATROPHIC_CUTOFF = 3.0   # PG I / PG II, inclusive

GROUP_BY_SEROLOGY = {
    (False, False): "A",
    (True, False): "B",
    (True, True): "C",
    (False, True): "D",
}

ANNUAL_INCIDENCE = {"A": 0.0004, "B": 0.0006, "C": 0.0035, "D": 0.0060}

GROUP_COUNTS = {
    "A": {"subjects": 3324, "cancers": 7, "mean_followup_years": 4.8},
    "B": {"subjects": 2134, "cancers": 6, "mean_followup_years": 4.7},
    "C": {"subjects": 1082, "cancers": 18, "mean_followup_years": 4.7},
    "D": {"subjects": 443, "cancers": 12, "mean_followup_years": 4.5},
}

HAZARD_RATIO_VS_A = {
    "A": (1.0, None),
    "B": (1.1, (0.4, 3.4)),
    "C": (6.0, (2.4, 14.5)),
    "D": (8.2, (3.2, 21.5)),
}

GROUP_INTERPRETATION = {
    "A": "no H. pylori infection and no serological atrophy",
    "B": "H. pylori infection without significant atrophy",
    "C": "H. pylori infection with chronic atrophic gastritis",
    "D": "severe atrophy with extensive intestinal metaplasia; serology reverted",
}

MODEL_CITATION = (
    "Watabe H et al. Gut. 2005;54(6):764-768. doi:10.1136/gut.2004.055400 "
    "(ABC method groups and rates); naming/screening scheme: Miki K, "
    "Proc Jpn Acad Ser B 2011;87:405-414."
)


def is_pepsinogen_atrophic(*, pepsinogen_i: float, pepsinogen_i_ii_ratio: float) -> bool:
    return (
        pepsinogen_i <= PG1_ATROPHIC_CUTOFF
        and pepsinogen_i_ii_ratio <= PG_RATIO_ATROPHIC_CUTOFF
    )


def abc_group(*, h_pylori_antibody_positive: bool, pepsinogen_i: float,
              pepsinogen_i_ii_ratio: float) -> str:
    atrophic = is_pepsinogen_atrophic(
        pepsinogen_i=pepsinogen_i, pepsinogen_i_ii_ratio=pepsinogen_i_ii_ratio
    )
    return GROUP_BY_SEROLOGY[(bool(h_pylori_antibody_positive), atrophic)]


def abc_method_predict(
    *,
    h_pylori_antibody_positive: bool,
    pepsinogen_i: float,
    pepsinogen_i_ii_ratio: float,
    prior_eradication: bool = False,
) -> dict:
    """
    ABC group (A-D) and the group's published annual gastric-cancer
    incidence rate.

    Notes
    -----
    Population: asymptomatic Japanese health-checkup endoscopy attendees
    (Watabe cohort: mean age 48.9, 68% male). Set ``prior_eradication=True``
    to flag that the classification is not valid — seroreversion after
    eradication misclassifies persistently high-atrophy patients as A/B.
    """
    group = abc_group(
        h_pylori_antibody_positive=h_pylori_antibody_positive,
        pepsinogen_i=pepsinogen_i,
        pepsinogen_i_ii_ratio=pepsinogen_i_ii_ratio,
    )
    rate = ANNUAL_INCIDENCE[group]
    hr, hr_ci = HAZARD_RATIO_VS_A[group]
    counts = GROUP_COUNTS[group]

    notes = []
    if prior_eradication:
        notes.append(
            "history of H. pylori eradication: this classification is NOT "
            "valid — use pre-eradication serology or endoscopic OLGA/OLGIM "
            "atrophy staging instead"
        )
    if group == "A":
        notes.append("group A is low-risk, not zero-risk (7/3324 developed gastric cancer)")

    return {
        "risk": rate,
        "group": group,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "gastric",
        "horizon_years": 1,
        "interpretation": GROUP_INTERPRETATION[group],
        "hazard_ratio_vs_group_a": hr,
        "hazard_ratio_95ci": hr_ci,
        "derivation_subjects_in_group": counts["subjects"],
        "derivation_cancers_in_group": counts["cancers"],
        "citation": MODEL_CITATION,
        "notes": "; ".join(notes) if notes else (
            "annual gastric-cancer incidence rate for the assigned ABC group"
        ),
    }
