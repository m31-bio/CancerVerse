"""Moore criteria, response to cisplatin-based chemotherapy in advanced,
recurrent or metastatic cervical carcinoma (Gynecologic Oncology Group).

Equation source
----------------
Moore DH, Tian C, Monk BJ, Long HJ, Omura GA, Bloss JD. "Prognostic factors
for response to cisplatin-based chemotherapy in advanced cervical carcinoma:
a Gynecologic Oncology Group study." Gynecol Oncol. 2010;116(1):44-49.
doi:10.1016/j.ygyno.2009.09.006 (PMC4470610), read in full 2026-08-14.

Development = GOG 110 + 169 + 179 pooled (428 enrolled, 409 with response
data). External validation = GOG 149, not used in development. Prospectively
validated as a tertiary endpoint of GOG 240 (Tewari et al, Clin Cancer Res
2015;21(3):579-588, doi:10.1158/1078-0432.CCR-15-1346, PMC4896296): "the
first prospectively validated scoring system in cervical cancer".

Not a regression at prediction time
------------------------------------
Five factors, each independently associated with poor response to
chemotherapy on multivariable analysis (Table 3): race (Black vs. non-Black),
GOG performance status > 0, pelvic (vs. non-pelvic) site of disease, prior
radiosensitizing chemotherapy, and recurrence within one year of diagnosis.
The paper does not use the fitted odds ratios as weights. It states plainly:
"Given that the five risk factors identified conferred comparable weights and
there were no interactions across them, a simple prognostic index was
developed by combining the number of risk factors." The score is therefore a
COUNT, 0-5, of how many factors are present, this module reproduces the
count, not a logistic combination of the odds ratios.

Table 3's odds ratios are kept below for provenance (a reader checking the
direction and significance of each factor needs them), and none of them enters
the arithmetic. That is not a simplification this module made; it is what the
paper published as the model.

Bands: low risk 0-1 factors, mid risk 2-3, high risk 4-5. `Table 4`
("Validation of Prognostic Model") gives the estimated/observed response rate
and median PFS/OS for each band in BOTH the development set and GOG 149. It is
a complete numeric statement over the model's entire three-cell output space,
`Fig. 1` gives the finer six-level (0-5) resolution and is a graphic; Table 4
is the artifact used here. All twelve values are transcribed and pinned in
`tests/parity/test_moore_criteria_parity.py`.

The race factor: read exactly, and not softened
--------------------------------------------------
Table 3 tests "Race: Black vs. Non-black" (OR 0.49, 95% CI 0.28-0.83,
p=0.008). Black patients had roughly half the odds of responding, adjusted
for the other four factors. The Results text and Discussion instead say
"African-American" throughout, the paper itself is not consistent about
which word it uses for the same variable, and this module follows Table 3,
where the actual statistical test lives, rather than the looser prose term.

The Discussion addresses the finding directly rather than passing over it:
"African-American patients were more likely to have a poor response to
chemotherapy... Using state registry data, Brookfield and associates showed
that African-American women with cervical carcinoma had a worse prognosis,"
going on to weigh access-to-care against biological hypotheses without
resolving which explains the association.

This module reproduces the published index as published rather than omitting
or re-deriving it, for the same reason `pbcg_extended` keeps its African-
ancestry term: a race coefficient the authors report is a fact about what was
measured in their cohort, not an endorsement of race as a biological
explanation. It should not be used to reason about mechanism, and every
`moore_criteria_predict` result whose input includes this factor says so in
`notes`. See `docs/COMMERCIAL_USE_AUDIT.md` and `pbcg_extended`'s own
scope_note for the two closest precedents in this library, one of which
documents a race coefficient that flips sign between sub-models, a reminder
that these terms are cohort-specific and not stable biological constants.

Two inputs that are collapsed from a wider variable, and one that is not
--------------------------------------------------------------------------
`performance_status` and `months_diagnosis_to_first_recurrence` are accepted
as the underlying ordinal/continuous values (GOG performance status 0-4;
months from the original diagnosis to the FIRST recurrence, not from the
start of the chemotherapy being evaluated) and dichotomised here at the
paper's own cut-points, PS > 0, interval <= 12 months, the same way
`cibula_arrm` bands a continuous tumour diameter rather than asking the
caller to pre-band it.

`disease_site` is the one genuine gap in the source. Table 1/2 record THREE
levels, pelvic, distant, combined, but Table 3 tests a binary "Pelvic vs.
Non-pelvic", and the paper never states in prose how "combined" (both pelvic
and distant disease, 13.1% of the development cohort) was assigned to one
side. This module reads "Non-pelvic" as its label states, everything that is
not pelvic-only, so combined counts as non-pelvic, which is the plain
reading of the label and not a statement the paper makes explicitly. Flagged
here and in `notes` rather than presented as settled, because 56 of 428
development patients (13.1%) fall in the category the paper does not resolve.

`prior_radiosensitizer` means concurrent cisplatin given WITH prior
radiotherapy (chemoradiation), not cisplatin given alone. Table 1 reports it
as a variable distinct from any later recurrence chemotherapy, and it is
already binary in the source with no collapsing question attached to it.

What this model does not give you
------------------------------------
A continuous probability. Table 3's odds ratios describe a fitted logistic
model but that model has no printed intercept anywhere in the paper, the same
half-a-formula defect that keeps three SEER cervical prognosis nomograms out
of this library (see `docs/diseases/cervical/README.md`). The paper did not
publish that continuous model; it published the three-band count index, and
Table 4 is a complete numeric statement of it. `risk` is None throughout: this
returns a band and that band's observed outcomes, not an individual
probability.

Scope
-----
Advanced, recurrent, or metastatic cervical carcinoma being started on
cisplatin-based chemotherapy, the GOG 110/169/179/149 population. It answers
"how likely is this regimen to work", not "will this patient survive" and not
"will this tumour respond to primary chemoradiation for newly diagnosed
disease", which is a different clinical question this model was never fit to.
"""

from __future__ import annotations

from typing import Any

AXIS = "response"
MODEL_ID = "moore_criteria"
DISEASE = "cervical"

RECURRENCE_INTERVAL_CUTOFF_MONTHS = 12.0  # "within one year", <= scores
_DISEASE_SITES = {"pelvic", "distant", "combined"}

#: Table 3, "Multivariate Analysis of Prognostic Factors of Treatment
#: Response", kept for provenance. NOT used to compute anything: the
#: published model is a count of how many factors are present, not a
#: logistic combination of these odds ratios. See the module docstring.
TABLE_3_ODDS_RATIOS: dict[str, dict[str, Any]] = {
    "black_race": {
        "label": "Race: Black vs. non-Black",
        "odds_ratio": 0.49, "ci": (0.28, 0.83), "p": 0.008,
    },
    "performance_status_above_0": {
        "label": "GOG performance status: 1 or 2 vs. 0",
        "odds_ratio": 0.60, "ci": (0.38, 0.94), "p": 0.027,
    },
    "pelvic_disease": {
        "label": "Site of disease: pelvic vs. non-pelvic",
        "odds_ratio": 0.58, "ci": (0.38, 0.90), "p": 0.015,
    },
    "prior_radiosensitizer": {
        "label": "Radiosensitizer: yes vs. no",
        "odds_ratio": 0.52, "ci": (0.32, 0.85), "p": 0.009,
    },
    "recurrence_within_1_year": {
        "label": "1st recurrence within one year since diagnosis: yes vs. no",
        "odds_ratio": 0.61, "ci": (0.39, 0.95), "p": 0.027,
    },
}

FACTOR_ORDER = tuple(TABLE_3_ODDS_RATIOS)

BANDS = (
    {"index": 0, "low": 0, "high": 1, "label": "low risk (0-1 factors)"},
    {"index": 1, "low": 2, "high": 3, "label": "mid risk (2-3 factors)"},
    {"index": 2, "low": 4, "high": 5, "label": "high risk (4-5 factors)"},
)

#: Table 4, "Validation of Prognostic Model", transcribed verbatim from
#: PMC4470610. Development = GOG 110+169+179 (n=428 enrolled, 409 with
#: response data, overall response 32%); external = GOG 149, not used in
#: development. Response rates are percentages; survival is median months.
TABLE_4_VALIDATION: list[dict[str, Any]] = [
    {
        "band_index": 0, "band_label": "low risk (0-1 factors)",
        "development": {"estimated_response_pct": 50.6, "observed_response_pct": 47.3,
                        "median_pfs_months": 6.34, "median_os_months": 11.10},
        "external": {"predicted_response_pct": 50.9, "observed_response_pct": 42.6,
                     "median_pfs_months": 6.87, "median_os_months": 11.93},
    },
    {
        "band_index": 1, "band_label": "mid risk (2-3 factors)",
        "development": {"estimated_response_pct": 29.4, "observed_response_pct": 31.4,
                        "median_pfs_months": 4.60, "median_os_months": 9.17},
        "external": {"predicted_response_pct": 29.0, "observed_response_pct": 29.4,
                     "median_pfs_months": 4.44, "median_os_months": 7.59},
    },
    {
        "band_index": 2, "band_label": "high risk (4-5 factors)",
        "development": {"estimated_response_pct": 13.0, "observed_response_pct": 9.8,
                        "median_pfs_months": 2.79, "median_os_months": 5.49},
        "external": {"predicted_response_pct": 13.5, "observed_response_pct": 14.3,
                     "median_pfs_months": 3.38, "median_os_months": 5.58},
    },
]

#: Tewari et al, GOG 240 (n=452), Clin Cancer Res 2015, the PROSPECTIVE
#: validation, a tertiary endpoint of a phase III trial. Only low- and
#: high-risk are stated numerically in the Results text; mid-risk appears
#: only in Fig. 1, a graphic, and is not transcribed here.
GOG_240_PROSPECTIVE_VALIDATION: dict[str, dict[str, Any]] = {
    "low": {"band_label": "low risk (0-1 factors)",
            "observed_response_pct": 57.0, "median_os_months": 21.8},
    "high": {"band_label": "high risk (4-5 factors)",
             "observed_response_pct": 18.5, "median_os_months": 8.2},
}

MODEL_CITATION = (
    "Moore DH, Tian C, Monk BJ, Long HJ, Omura GA, Bloss JD. Prognostic "
    "factors for response to cisplatin-based chemotherapy in advanced "
    "cervical carcinoma: a Gynecologic Oncology Group study. Gynecol Oncol. "
    "2010;116(1):44-49. doi:10.1016/j.ygyno.2009.09.006 (band outcomes from "
    "Table 4; prospective validation from Tewari et al, Clin Cancer Res "
    "2015;21(3):579-588, doi:10.1158/1078-0432.CCR-15-1346)"
)

SCOPE = (
    "Advanced, recurrent, or metastatic cervical carcinoma starting "
    "cisplatin-based chemotherapy: GOG 110/169/179 (development, n=428) and "
    "GOG 149 (external validation), prospectively validated as a tertiary "
    "endpoint of GOG 240 (n=452). Answers whether THIS regimen is likely to "
    "produce a response, not whether the patient will survive and not "
    "response to primary chemoradiation for newly diagnosed, non-metastatic "
    "disease, a different question this model was never fit to."
)


def _band_for_count(count: int) -> dict[str, Any]:
    for band in BANDS:
        if band["low"] <= count <= band["high"]:
            return band
    raise ValueError(f"risk factor count {count} falls outside 0-5")


def _validate_performance_status(performance_status: int) -> int:
    ps = int(performance_status)
    if ps != float(performance_status) or not 0 <= ps <= 4:
        raise ValueError(
            f"performance_status must be a GOG/ECOG score 0-4, got "
            f"{performance_status!r}"
        )
    return ps


def _validate_disease_site(disease_site: str) -> str:
    key = str(disease_site).strip().lower()
    if key not in _DISEASE_SITES:
        raise ValueError(
            f"disease_site must be one of {sorted(_DISEASE_SITES)}, got "
            f"{disease_site!r}"
        )
    return key


def moore_risk_factors(
    *,
    black_race: bool,
    performance_status: int,
    disease_site: str,
    prior_radiosensitizer: bool,
    months_diagnosis_to_first_recurrence: float,
) -> dict[str, Any]:
    """The five factor flags, the count (0-5), and what was inferred to get
    there for the two collapsed inputs."""
    ps = _validate_performance_status(performance_status)
    site = _validate_disease_site(disease_site)
    months = float(months_diagnosis_to_first_recurrence)
    if months < 0:
        raise ValueError(
            f"months_diagnosis_to_first_recurrence must be >= 0, got {months}"
        )

    factors = {
        "black_race": bool(black_race),
        "performance_status_above_0": ps > 0,
        "pelvic_disease": site == "pelvic",
        "prior_radiosensitizer": bool(prior_radiosensitizer),
        "recurrence_within_1_year": months <= RECURRENCE_INTERVAL_CUTOFF_MONTHS,
    }
    return {
        "factors": factors,
        "count": sum(factors.values()),
        "disease_site_collapsed_from_three_levels": site == "combined",
    }


def moore_criteria_predict(
    *,
    black_race: bool,
    performance_status: int,
    disease_site: str,
    prior_radiosensitizer: bool,
    months_diagnosis_to_first_recurrence: float,
) -> dict[str, Any]:
    """The Moore criteria risk band and its published response/survival data.

    `black_race` reproduces a published, cohort-specific association, not a
    claim about biology, see the module docstring before using this as a
    basis for care. `performance_status` is the GOG/ECOG score 0-4; the risk
    factor is PS > 0. `disease_site` is ``"pelvic"``, ``"distant"`` or
    ``"combined"`` (both sites involved); only ``"pelvic"`` counts as the risk
    factor, and the paper never states in prose how "combined" should be
    classified, see the module docstring, and this is flagged in `notes`
    whenever a combined-site patient is scored.
    `months_diagnosis_to_first_recurrence` is measured from the ORIGINAL
    cancer diagnosis to the FIRST recurrence, not from the start of the
    chemotherapy regimen being evaluated; the risk factor is <= 12 months.

    Returns the count (0-5), the risk band, and that band's response rate and
    median PFS/OS in both the development cohort and the external (GOG 149)
    validation cohort, plus GOG 240's prospective validation where the band
    has one. `risk` is None: the paper publishes no points-to-probability
    formula, only the three-band lookup in Table 4.
    """
    scored = moore_risk_factors(
        black_race=black_race,
        performance_status=performance_status,
        disease_site=disease_site,
        prior_radiosensitizer=prior_radiosensitizer,
        months_diagnosis_to_first_recurrence=months_diagnosis_to_first_recurrence,
    )
    count = scored["count"]
    band = _band_for_count(count)
    row = TABLE_4_VALIDATION[band["index"]]

    notes = [
        "band lookup from Table 4, not a fitted probability, the paper "
        "publishes no points-to-probability formula for this index",
        "the five factors are counted equally; the paper explicitly declines "
        "to weight them by their fitted odds ratios",
    ]
    if scored["factors"]["black_race"]:
        notes.append(
            "race counted as a risk factor per Table 3 (Black vs. non-Black, "
            "OR 0.49 for response, adjusted); this is a cohort-specific "
            "association the authors report and discuss, not a biological "
            "claim, see the module docstring"
        )
    if scored["disease_site_collapsed_from_three_levels"]:
        notes.append(
            "disease_site='combined' was scored as non-pelvic by the plain "
            "reading of Table 3's 'Pelvic vs. Non-pelvic' label; the paper "
            "never states this collapsing rule in prose (13.1% of the "
            "development cohort was 'combined')"
        )
    prospective_key = {0: "low", 2: "high"}.get(band["index"])
    prospective = GOG_240_PROSPECTIVE_VALIDATION.get(prospective_key)

    return {
        "risk_factor_count": count,
        "risk_factors_present": scored["factors"],
        "band": band["index"],
        "band_label": band["label"],
        "development_estimated_response_pct":
            row["development"]["estimated_response_pct"],
        "development_observed_response_pct":
            row["development"]["observed_response_pct"],
        "development_median_pfs_months": row["development"]["median_pfs_months"],
        "development_median_os_months": row["development"]["median_os_months"],
        "external_predicted_response_pct":
            row["external"]["predicted_response_pct"],
        "external_observed_response_pct":
            row["external"]["observed_response_pct"],
        "external_median_pfs_months": row["external"]["median_pfs_months"],
        "external_median_os_months": row["external"]["median_os_months"],
        "gog240_prospective_validation": prospective,
        "risk": None,  # a band lookup, not a fitted probability
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": DISEASE,
        "interpretation": (
            f"{count}/5 risk factors present, {band['label']}. Observed "
            f"response rate {row['development']['observed_response_pct']}% "
            f"in the development cohort, "
            f"{row['external']['observed_response_pct']}% in external "
            "validation (GOG 149)."
            + (
                f" GOG 240 prospectively observed "
                f"{prospective['observed_response_pct']}% response and "
                f"{prospective['median_os_months']} months median OS in "
                f"this band."
                if prospective else ""
            )
        ),
        "citation": MODEL_CITATION,
        "scope": SCOPE,
        "notes": "; ".join(notes),
    }
