"""Optum EHR LASSO parity, route 1, against PatientLevelPrediction itself.

What this proves. The reference values were produced by
`PatientLevelPrediction::loadPlpModel` followed by
`PatientLevelPrediction::predictPlp` on the study package's own
`inst/models/full_model` directory, so the arithmetic being reproduced is the
vendor's whole predict path: covariate deletion, normalisation by the stored
`normFactors`, the join on covariateId, the dot product, and the logistic link.
It is the same code an OHDSI site would run against a real CDM.

What it does not prove. There is no published worked example for this model,
the paper reports AUCs, not patient-level predictions, so nothing here checks
the *artifact* against the *paper*. It checks our implementation against the
artifact. The artifact's own internal consistency is checked separately by
`optum_lung_lasso_extract.py`, which refuses to write the data file unless
`model.json` and `covariateImportance.csv` agree on all 278 coefficients.

The fixture is committed so this runs offline. Regenerate with:

    Rscript tests/parity/reference/optum_lung_lasso_reference.R
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cancerverse_baseline.lung.detection.optum_lung_lasso import (
    BETAS,
    INTERCEPT,
    optum_lung_lasso_predict,
)

CASES = json.loads(
    (Path(__file__).parent / "reference" / "optum_lung_lasso_cases.json").read_text()
)


def _covariates(case: dict) -> dict[int, float]:
    return {int(k): float(v) for k, v in case["covariates"].items()}


@pytest.mark.parity
@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_matches_patient_level_prediction(case):
    got = optum_lung_lasso_predict(_covariates(case))
    assert got["linear_predictor"] == pytest.approx(
        case["linear_predictor"], abs=1e-9
    ), f"{case['name']}: lp {got['linear_predictor']} vs R {case['linear_predictor']}"
    assert got["risk"] == pytest.approx(case["risk"], rel=1e-12, abs=1e-15)


@pytest.mark.parity
def test_the_cases_exercise_every_coefficient():
    """Two of the cases are the whole positive and whole negative halves of the
    model, so between them every one of the 278 betas is multiplied by a
    non-zero value at least once. A parity suite over five plausible patients
    would leave most of a LASSO model untouched."""
    covered: set[int] = set()
    for case in CASES:
        covered |= {int(k) for k in case["covariates"]} & set(BETAS)
    assert covered == set(BETAS), f"{len(set(BETAS) - covered)} betas never exercised"


@pytest.mark.parity
def test_ids_the_model_does_not_carry_are_dropped_exactly_as_r_drops_them():
    """Four distinct ways an id can fail to reach the score, and PLP treats all
    four the same: never in the covariate set, deleted as infrequent, deleted
    as the redundant reference band, and kept with a beta of exactly zero.

    They are separate cases because they take different routes through the R
    pipeline, the first three are removed by `applyTidyCovariateData`, the
    fourth survives into `predictCyclopsType` and is filtered by `beta != 0`.
    Our code has no such stages, so this is where a shortcut would show.
    """
    baseline = next(c for c in CASES if c["name"] == "intercept only")
    inert = [
        "zero-beta candidate only (262923)",
        "covariate dropped as infrequent (8715802)",
        "redundant reference age band 50-54 (10003)",
    ]
    for name in inert:
        case = next(c for c in CASES if c["name"] == name)
        assert case["linear_predictor"] == pytest.approx(INTERCEPT)
        got = optum_lung_lasso_predict(_covariates(case))
        assert got["linear_predictor"] == pytest.approx(
            baseline["linear_predictor"], abs=1e-12
        )
        assert got["n_covariates_used"] == 0


@pytest.mark.parity
def test_a_non_binary_value_is_multiplied_rather_than_clamped():
    """Every covariate in this model has a normalisation factor of 1, so PLP
    scores a value of 3 as three times the beta. Nothing in the model or in our
    code coerces a covariate to 0/1, and this pins that down: a caller who
    passes counts where the model expects indicators gets a wrong answer
    quietly, from the reference implementation as much as from ours.
    """
    case = next(c for c in CASES if c["name"] == "count value 3 on the smoking covariate")
    assert case["linear_predictor"] == pytest.approx(INTERCEPT + 3 * BETAS[3639])
    got = optum_lung_lasso_predict(_covariates(case))
    assert got["linear_predictor"] == pytest.approx(case["linear_predictor"], abs=1e-12)
