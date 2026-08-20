"""Optum EHR LASSO, 3-year lung cancer risk from routine records (2023).

Chandran U, Reps J, Yang R, Vachani A, Maldonado F, Kalsekar I. Machine
Learning and Real-World Data to Predict Lung Cancer Risk in Routine Care.
Cancer Epidemiol Biomarkers Prev. 2023;32(3):337-343.
doi:10.1158/1055-9965.EPI-22-0873

**Why this sits next to PLCOm2012 rather than replacing it.** PLCOm2012 decides
screening eligibility in national guidelines and every one of its inputs,
pack-years, years since quitting, education level, is a questionnaire field. An
EHR does not hold them. This model was fitted on 4,777,606 Optum records using
only what a record already contains, and it is therefore what a deployed model
is actually competing with. Neither answers the other's question.

**The predictors are not clinical variables, and the API reflects that.** This
is an OHDSI/OMOP model. Every predictor is a `covariateId` integer meaning
"concept X observed in the year before index", encoded as

    covariateId = conceptId * 1000 + analysisId

so 3020891702 is concept 3020891 (body temperature) under analysis 702
(measurement recorded in day -365..0). Two analyses index a bucket rather than
an OMOP concept and carry conceptId 0: analysis 3 is the five-year age band
(`floor(age/5) * 1000 + 3`), and analysis 639 is the study package's own
smoking-status covariate, defined by SQL in its `R/smoking.R`.

Turning 278 covariateIds into a keyword-argument signature would mean inventing
a clinical reading for each one, so the input here is the covariate vector
itself: a mapping of covariateId to value, or an iterable of the ids that are
present. `describe()` and `COEFFICIENTS` expose the names the study package
ships, which is how a caller finds out what a number means.

**Normalisation, which a naive dot product would get wrong on another model.**
PatientLevelPrediction fitted this with `preprocessSettings$normalize = TRUE`,
so at predict time it divides every covariate by the maximum value seen in
training (`applyTidyCovariateData`, using the `normFactors` table) *before*
multiplying by beta. That divisor is not 1 in general. It is 1 for all 278
covariates in this model, checked by the extraction script, which refuses to
write the data file otherwise, because all 278 are 0/1 indicators. So the
plain dot product below is correct **for this model**, and would not be for a
sibling model that kept a count covariate.

**Rounding is the vendor's, not ours.** `model.json` stores betas to four
decimal places, and that file is what PatientLevelPrediction loads and scores
with, so those are the coefficients used here. `covariateImportance.csv` in the
same directory carries the unrounded values; all 278 agree to the rounding, and
the data file keeps both so the difference is visible rather than assumed.

**Scope.** Development was restricted to patients aged 45-65 with an outpatient
visit in 2013 and at least a year of prior observation, and the outcome is a
first lung cancer diagnosis in days 1-1095 after index. The internal AUC was
0.76. Nothing here recalibrates it to another population; a model fitted on one
vendor's EHR carries that vendor's coding habits with it.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ...base import logit_risk

AXIS = "detection"
MODEL_ID = "optum_lung_lasso"
DISEASE = "lung"

_DATA = Path(__file__).resolve().parent / "data" / "optum_lung_lasso_2023.json"
_MODEL = json.loads(_DATA.read_text())

#: The published intercept. On its own it is a 3-year risk of 0.015%.
INTERCEPT: float = _MODEL["intercept"]

#: covariateId -> beta, as `model.json` stores it (four decimal places).
BETAS: dict[int, float] = {c["covariate_id"]: c["beta"]
                           for c in _MODEL["coefficients"]}

#: covariateId -> the full record: beta, unrounded beta, analysisId, conceptId
#: and the covariateName the study package ships. Ordered by |beta|.
COEFFICIENTS: dict[int, dict[str, Any]] = {
    c["covariate_id"]: c for c in _MODEL["coefficients"]
}

#: The study package's own smoking covariate (analysis 639), from its
#: `R/smoking.R`: one row per patient, `max(smoke_value) * 1000 + 639`, where
#: 'Current smoker' is 3, 'Previously smoked' and 'Not currently smoking' are 2,
#: and 'Never smoked' is 1. A patient with no such observation gets none of
#: them, which is not the same as never-smoker.
SMOKING = {"never": 1639, "former": 2639, "current": 3639}

#: The risk window, from the model's populationSettings: days 1-1095 after the
#: index visit.
HORIZON_DAYS = 1095

CITATION = (
    "Chandran U, Reps J, Yang R, Vachani A, Maldonado F, Kalsekar I. Machine "
    "Learning and Real-World Data to Predict Lung Cancer Risk in Routine Care. "
    "Cancer Epidemiol Biomarkers Prev. 2023;32(3):337-343. "
    "doi:10.1158/1055-9965.EPI-22-0873 (coefficients from the study package "
    f"{_MODEL['source']['repo']} at {_MODEL['source']['commit'][:12]}, "
    "Apache-2.0)"
)

SCOPE = (
    "Optum de-identified EHR (cdm_optum_ehr_v1705): 4,777,606 patients aged "
    "45-65 with a 2013 outpatient visit, at least 365 days of prior "
    "observation and no prior lung cancer. Predicts a first lung cancer "
    "diagnosis in days 1-1095 after index, from coded diagnoses, drug eras, "
    "procedures, measurements, observations and demographics in the preceding "
    "year. Internal AUC 0.76. It is not a screening-eligibility rule and does "
    "not substitute for one."
)


def age_group_covariate_id(age: float) -> int:
    """The analysis-3 covariateId for an age, i.e. `floor(age/5) * 1000 + 3`.

    Read off the covariate names the study package ships, 9003 is labelled
    "age group: 45 - 49" and 13003 "age group: 65 - 69", rather than assumed
    from FeatureExtraction. Only the bands the LASSO kept have a coefficient;
    50-54 was dropped before fitting as the redundant reference band, so this
    returning 10003 for a 52-year-old and that id not being in `BETAS` is the
    model working, not a lookup failure.
    """
    if age < 0:
        raise ValueError(f"age must be non-negative, got {age}")
    return int(age // 5) * 1000 + 3


def describe(covariate_id: int) -> dict[str, Any] | None:
    """What a covariateId means, or None if it is not in the model."""
    return COEFFICIENTS.get(int(covariate_id))


def _as_mapping(covariates: Mapping[int, float] | Iterable[int]
                ) -> Mapping[int, float]:
    if isinstance(covariates, Mapping):
        return covariates
    out: dict[int, float] = {}
    for cid in covariates:
        if isinstance(cid, (str, bytes)):
            raise TypeError(f"covariateId must be an integer, got {cid!r}")
        out[int(cid)] = 1.0
    return out


def linear_predictor(covariates: Mapping[int, float] | Iterable[int]) -> float:
    """Intercept plus the dot product over the covariates the model kept.

    Reproduces `PatientLevelPrediction:::predictCyclopsType`, whose join over
    covariateId means an id the model does not carry contributes nothing.
    That is the same treatment given to a covariate the caller simply did not
    record, so **absence and zero are indistinguishable here**, the covariate
    set was built with `missingMeansZero`, and a sparsely coded record will
    score low for the same reason a healthy one does.
    """
    values = _as_mapping(covariates)
    total = INTERCEPT
    for cid, value in values.items():
        beta = BETAS.get(int(cid))
        if beta is None:
            continue
        total += beta * float(value)
    return total


def optum_lung_lasso_predict(
    covariates: Mapping[int, float] | Iterable[int],
) -> dict[str, Any]:
    """3-year lung cancer risk from an OMOP covariate vector.

    `covariates` is either a mapping of covariateId to value, or an iterable of
    the covariateIds present (each taken as 1). Ids outside the model are
    ignored and counted in the result, because a caller feeding a covariate set
    built under different settings will otherwise see a plausible number and no
    warning.
    """
    values = _as_mapping(covariates)
    used = {int(c) for c in values} & set(BETAS)
    lp = linear_predictor(values)
    risk = logit_risk(lp)
    return {
        "risk": risk,
        "percent": risk * 100.0,
        "linear_predictor": lp,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": DISEASE,
        "horizon_days": HORIZON_DAYS,
        "n_covariates_used": len(used),
        "n_covariates_ignored": len(values) - len(used),
        "citation": CITATION,
        "notes": (
            "3-year risk of a first lung cancer diagnosis. Inputs are OMOP "
            "covariateIds (conceptId * 1000 + analysisId) observed in the year "
            "before index; ids the model does not carry contribute nothing, so "
            "an under-coded record scores like a healthy one."
        ),
    }


predict = optum_lung_lasso_predict
