"""Chau index, survival under first-line palliative chemotherapy in locally
advanced or metastatic esophago-gastric cancer.

Equation source
----------------
Chau I, Norman AR, Cunningham D, Waters JS, Oates J, Ross PJ. "Multivariate
prognostic factor analysis in locally advanced and metastatic esophago-gastric
cancer, pooled analysis from three multicenter, randomized, controlled trials
using individual patient data." J Clin Oncol. 2004;22(12):2395-2403.
doi:10.1200/jco.2004.08.154, PMID 15197201.

Pooled INDIVIDUAL PATIENT DATA from three randomised controlled trials run at
the Royal Marsden between 1992 and 2001 (ECF v FAMTX, n=256; ECF v MCF, n=574;
PVI FU v PVI FU+MMC, n=250), 1,080 patients, 979 (91%) died. Read in full from
the article on 2026-08-17.

Not a regression at prediction time
------------------------------------
Four binary poor-prognosis factors, each independently significant at a 99%
confidence level (Table 3). The paper does not weight them: "All four factors
have a similar order of magnitude, therefore they can be combined into a simple
prognostic score without loss of relevant information." The index is a COUNT,
0-4, banded good (0) / moderate (1-2) / poor (3-4). Table 3's hazard ratios are
carried below for provenance and enter no arithmetic.

Why this is filed under `response` and not `prognosis`
--------------------------------------------------------
It predicts survival, not tumour shrinkage, so on its face it looks like a
prognosis model. It is filed here on the same reading this library already
applies to `lipi` and `hap`: a score that ranks survival UNDER a named therapy,
used to decide who gets that therapy and how intensively, rather than
estimating what the therapy adds. The paper's own stated use is exactly that —
"identify a group of patients that benefit most from intensified combination
treatment and/or novel targeted therapy" and stratification in phase III
trials. Note the esophageal prognosis cell is separately unfilled; this model
was not put there because its population is defined by starting chemotherapy.

The response half of the paper is NOT implemented, and that is deliberate
--------------------------------------------------------------------------
Table 4 fits a separate logistic model for TUMOUR RESPONSE, and it is a
genuinely different model: only three of the four survival factors survive.

    performance status >= 2      risk ratio 0.469   P < .001
    peritoneal metastases        risk ratio 0.475   P = .002
    alkaline phosphatase >= 100  risk ratio 0.655   P = .009
    liver metastases             ---                P = .558   NOT significant
    haemoglobin <= 11 g/L        ---                P = .512   NOT significant

Liver metastasis is the fourth survival factor and does not predict response at
all. That is a real finding about the disease and it is why this module does
NOT expose a response probability: Table 4 prints risk ratios with no
intercept, and the paper gives no response rate per risk band anywhere
(checked). So the continuous response model is half a formula, the same defect
that keeps several nomogram papers out of this library, and inventing a band
lookup for it would mean inventing numbers. `TABLE_4_RESPONSE_FACTORS` records
the finding for a reader; nothing computes from it.

Applying an "esophago-gastric" model to esophageal cancer
-----------------------------------------------------------
This is the question that decides whether the entry belongs in an esophageal
cell at all, and the paper answers it directly rather than leaving it to be
assumed. Site of primary in the pooled cohort (Table 1):

    esophagus     295   27.3%
    EGJ           248   23.0%      esophageal or junctional: 543, 50.3%
    stomach       512   47.4%
    unknown        25    2.3%

and the authors tested whether site mattered, twice, and found it did not:
"Age, sex, and location of primary tumor were not significant in univariate
analyses", then in the Discussion, "In our analysis, there were no survival
differences among patients with esophageal, EGJ, or gastric cancers... there is
no definite need for future phase III studies to distinguish patients with
tumors from different anatomic origins if they have advanced disease."

The contrast worth knowing: the AGAMENON nomogram (Br J Cancer 2017) also says
"oesophagogastric" and is 5.8% esophagus against 83.9% stomach. A label of
"esophago-gastric" is not evidence about a cohort; the site table is.

Scope, and the two limits most likely to be read past
--------------------------------------------------------
**Histology is 88% adenocarcinoma and only 4.6% squamous** (950 v 50 of 1,080).
This is not a model for esophageal squamous cell carcinoma, which is the
dominant histology across East Asia and a different disease with different risk
factors. Applying it there is a category error of the same kind as running
`kunzmann` (adenocarcinoma) on squamous disease.

**The therapy is 1990s fluorouracil-based combination chemotherapy** — ECF,
FAMTX, MCF, PVI FU with or without mitomycin C. The cohort predates
trastuzumab, and predates checkpoint inhibitors entirely. The index describes
survival under that era's treatment.

The authors also state plainly that "our prognostic index requires validation",
naming their own then-ongoing REAL-2 study as the intended validation set. No
completed external validation is claimed by this paper, and none is claimed
here.
"""

from __future__ import annotations

from typing import Any

AXIS = "response"
MODEL_ID = "chau_eg"
DISEASE = "esophageal"

ALP_CUTOFF_U_L = 100.0          # ">= 100 U/L" scores
PERFORMANCE_STATUS_CUTOFF = 2   # ">= 2" scores

#: Table 3, "Multivariate Baseline Prognostic Model" (n=817 with complete
#: data), transcribed from the published PDF. Kept for provenance only: the
#: published index counts these factors equally and does not weight them.
#:
#: NOTE the abstract rounds every one of these, 1.58 / 1.41 / 1.33 / 1.41 —
#: while Table 3 carries three decimals. The table is the primary record and is
#: what is stored here; anyone quoting the abstract will be quoting rounded
#: values.
TABLE_3_HAZARD_RATIOS: dict[str, dict[str, Any]] = {
    "performance_status": {
        "label": "Performance status 2-3 (v 0-1)",
        "hazard_ratio": 1.575, "ci99": (1.251, 1.981), "p": "<.0001",
    },
    "liver_metastases": {
        "label": "Liver metastases",
        "hazard_ratio": 1.409, "ci99": (1.139, 1.743), "p": "<.0001",
    },
    "peritoneal_metastases": {
        "label": "Peritoneal metastases",
        "hazard_ratio": 1.329, "ci99": (1.013, 1.743), "p": ".007",
    },
    "alkaline_phosphatase": {
        "label": "Alkaline phosphatase >= 100 U/L",
        "hazard_ratio": 1.412, "ci99": (1.136, 1.755), "p": "<.0001",
    },
}

FACTOR_ORDER = tuple(TABLE_3_HAZARD_RATIOS)

#: Table 4, "Multivariate Logistic Regression Model for Tumor Response to
#: Chemotherapy". Recorded because it is a different model from Table 3 and a
#: reader will assume it is the same one. NOTHING COMPUTES FROM THIS, the
#: table has no intercept and the paper prints no response rate per risk band,
#: so no response probability is recoverable. See the module docstring.
TABLE_4_RESPONSE_FACTORS: dict[str, dict[str, Any]] = {
    "performance_status": {"risk_ratio": 0.469, "ci99": (0.280, 0.787), "p": "<.001"},
    "peritoneal_metastases": {"risk_ratio": 0.475, "ci99": (0.254, 0.889), "p": ".002"},
    "alkaline_phosphatase": {"risk_ratio": 0.655, "ci99": (0.433, 0.992), "p": ".009"},
    "liver_metastases": {"risk_ratio": None, "ci99": None, "p": ".558"},
    "haemoglobin_11": {"risk_ratio": None, "ci99": None, "p": ".512"},
}

BANDS = (
    {"index": 0, "low": 0, "high": 0, "label": "good risk (0 factors)"},
    {"index": 1, "low": 1, "high": 2, "label": "moderate risk (1-2 factors)"},
    {"index": 2, "low": 3, "high": 4, "label": "poor risk (3-4 factors)"},
)

#: Survival by risk group, from the Results text. n sums to 817, the patients
#: with complete data on all four factors, not the full 1,080; the variable
#: with missing data was alkaline phosphatase (present on 823). The paper
#: checked and reports "no difference in survival between those patients
#: included in the prognostic model and those excluded because of missing
#: data (log-rank P = .992)".
RISK_GROUP_OUTCOMES: list[dict[str, Any]] = [
    {
        "band_index": 0, "band_label": "good risk (0 factors)", "n": 239,
        "median_os_months": 11.8,
        "one_year_survival_pct": 48.5, "one_year_ci95": (41.9, 54.7),
        "hazard_ratio_vs_good": 1.0, "hr_ci99": None,
    },
    {
        "band_index": 1, "band_label": "moderate risk (1-2 factors)", "n": 487,
        "median_os_months": 7.4,
        "one_year_survival_pct": 25.7, "one_year_ci95": (22.5, 29.7),
        "hazard_ratio_vs_good": 1.92, "hr_ci99": (1.53, 2.40),
    },
    {
        "band_index": 2, "band_label": "poor risk (3-4 factors)", "n": 91,
        "median_os_months": 4.1,
        "one_year_survival_pct": 11.0, "one_year_ci95": (5.6, 18.4),
        "hazard_ratio_vs_good": 3.59, "hr_ci99": (2.57, 5.02),
    },
]

#: The whole pooled cohort, for context when a band figure is quoted alone.
COHORT = {
    "n_total": 1080, "n_deaths": 979, "n_in_model": 817,
    "median_os_months": 7.9,
    "one_year_survival_pct": 30.1, "one_year_ci95": (27.8, 32.9),
    "two_year_survival_pct": 11.5, "two_year_ci95": (9.6, 13.5),
    "site_esophagus": 295, "site_egj": 248, "site_stomach": 512,
    "site_unknown": 25,
    "histology_adenocarcinoma": 950, "histology_squamous": 50,
}

MODEL_CITATION = (
    "Chau I, Norman AR, Cunningham D, Waters JS, Oates J, Ross PJ. "
    "Multivariate prognostic factor analysis in locally advanced and "
    "metastatic esophago-gastric cancer, pooled analysis from three "
    "multicenter, randomized, controlled trials using individual patient "
    "data. J Clin Oncol. 2004;22(12):2395-2403. "
    "doi:10.1200/jco.2004.08.154 (factors and hazard ratios from Table 3; "
    "risk-group survival from the Results text)"
)

SCOPE = (
    "Locally advanced or metastatic esophago-gastric cancer at the start of "
    "first-line fluorouracil-based palliative chemotherapy. Cohort was 27.3% "
    "esophagus, 23.0% EGJ, 47.4% stomach, and the authors found no survival "
    "difference by primary site. HISTOLOGY WAS 88% ADENOCARCINOMA and only "
    "4.6% squamous, so this is not a model for esophageal squamous cell "
    "carcinoma. Treatment era is 1992-2001 (ECF, FAMTX, MCF, PVI FU +/- MMC), "
    "predating trastuzumab and checkpoint inhibitors. The authors state the "
    "index requires validation and name their own REAL-2 study as the "
    "intended validation set; no completed external validation is claimed."
)


def _band_for_count(count: int) -> dict[str, Any]:
    for band in BANDS:
        if band["low"] <= count <= band["high"]:
            return band
    raise ValueError(f"risk factor count {count} falls outside 0-4")


def _validate_performance_status(performance_status: int) -> int:
    ps = int(performance_status)
    if ps != float(performance_status) or not 0 <= ps <= 4:
        raise ValueError(
            f"performance_status must be a WHO/ECOG score 0-4, got "
            f"{performance_status!r}"
        )
    return ps


def chau_eg_risk_factors(
    *,
    performance_status: int,
    liver_metastases: bool,
    peritoneal_metastases: bool,
    alkaline_phosphatase_u_l: float,
) -> dict[str, Any]:
    """The four factor flags and their count (0-4).

    `performance_status` is the raw WHO/ECOG score; the published factor is
    PS >= 2, dichotomised here rather than asking the caller to pre-band it.
    `alkaline_phosphatase_u_l` is likewise the raw value against the paper's
    >= 100 U/L cut-point.
    """
    ps = _validate_performance_status(performance_status)
    alp = float(alkaline_phosphatase_u_l)
    if alp < 0:
        raise ValueError(
            f"alkaline_phosphatase_u_l must be >= 0, got {alp}")

    factors = {
        "performance_status": ps >= PERFORMANCE_STATUS_CUTOFF,
        "liver_metastases": bool(liver_metastases),
        "peritoneal_metastases": bool(peritoneal_metastases),
        "alkaline_phosphatase": alp >= ALP_CUTOFF_U_L,
    }
    return {"factors": factors, "count": sum(factors.values())}


def chau_eg_predict(
    *,
    performance_status: int,
    liver_metastases: bool,
    peritoneal_metastases: bool,
    alkaline_phosphatase_u_l: float,
) -> dict[str, Any]:
    """Chau risk group and its published survival, for a patient starting
    first-line palliative chemotherapy for advanced esophago-gastric cancer.

    Returns the factor count (0-4), the risk band, and that band's median
    overall survival and one-year survival in the derivation cohort. `risk` is
    None: the paper publishes no points-to-probability mapping, only the
    three-band lookup.

    The alkaline-phosphatase cut-point deserves a second look before use,
    100 U/L is at or below the lower end of many laboratories' reference
    range, so this factor fires for a substantial share of patients with
    entirely normal liver chemistry. That is the published cut-point and it is
    reproduced, but it is not a marker of abnormality.
    """
    scored = chau_eg_risk_factors(
        performance_status=performance_status,
        liver_metastases=liver_metastases,
        peritoneal_metastases=peritoneal_metastases,
        alkaline_phosphatase_u_l=alkaline_phosphatase_u_l,
    )
    count = scored["count"]
    band = _band_for_count(count)
    row = RISK_GROUP_OUTCOMES[band["index"]]

    notes = [
        "band lookup from the paper's Results text, not a fitted probability "
        "-- no points-to-probability mapping is published for this index",
        "the four factors are counted equally; the paper states they are of "
        "'similar order of magnitude' and declines to weight them",
        "88% of the derivation cohort was adenocarcinoma and 4.6% squamous: "
        "this is not a model for esophageal squamous cell carcinoma",
        "treatment era is 1992-2001 fluorouracil-based chemotherapy, "
        "predating trastuzumab and checkpoint inhibitors",
    ]
    if scored["factors"]["alkaline_phosphatase"]:
        notes.append(
            "the alkaline phosphatase factor fired at the published >= 100 "
            "U/L cut-point, which sits at or below many laboratories' upper "
            "reference limit and is not itself a sign of abnormality"
        )

    return {
        "risk_factor_count": count,
        "risk_factors_present": scored["factors"],
        "band": band["index"],
        "band_label": band["label"],
        "band_n_in_derivation": row["n"],
        "median_os_months_in_derivation": row["median_os_months"],
        "one_year_survival_pct_in_derivation": row["one_year_survival_pct"],
        "one_year_survival_ci95": list(row["one_year_ci95"]),
        "hazard_ratio_vs_good_risk": row["hazard_ratio_vs_good"],
        "risk": None,  # a band lookup, not a fitted probability
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": DISEASE,
        "interpretation": (
            f"{count}/4 risk factors present, {band['label']}. Median overall "
            f"survival in this band was {row['median_os_months']} months and "
            f"one-year survival {row['one_year_survival_pct']}% "
            f"({row['one_year_ci95'][0]}-{row['one_year_ci95'][1]}%), among "
            f"{row['n']} patients. Whole-cohort median was "
            f"{COHORT['median_os_months']} months. "
            "The paper's separate response model (Table 4) drops liver "
            "metastases entirely and publishes no intercept, so no response "
            "probability is available from this index."
        ),
        "citation": MODEL_CITATION,
        "scope": SCOPE,
        "notes": "; ".join(notes),
    }
