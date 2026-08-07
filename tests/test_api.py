"""The public API: one entry point over 27 models.

The load-bearing test here is `test_every_model_runs_through_predict`, which
calls all 27 through the dispatcher using the reference patients from the
feature sweep. A dispatcher that works for the models someone happened to try
is not a dispatcher.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import mayo_baseline as mb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


# The four models the sensitivity sweep cannot cover, because their output is a
# category or a survival curve rather than one number to sweep. They still have
# to be callable through the dispatcher, so their reference patients live here.
EXTRA_PATIENTS = {
    "ang2010_rpa": dict(hpv_positive=True, pack_years=5, n_stage="N2b",
                        t_stage="T2"),
    "lipi_prognosis": dict(ldh=300.0, ldh_upper_limit_normal=250.0, dnlr=4.0),
    "predict_breast": dict(age=55, size_mm=20, nodes=1, grade=2,
                           er_positive=True),
    "predict_breast_response": dict(age=55, size_mm=20, nodes=1, grade=2,
                                    er_positive=True),
    # takes a baseline risk rather than patient variables, so there is nothing
    # to sweep — it is a transformation of another model's output
    "cvd_statin_benefit": dict(baseline_risk=0.20, ldl_reduction_mmol_l=1.0),
    # nine outcomes rather than one number, so nothing to sweep
    "dutasteride": dict(age=63, psa=5.7, dre_abnormal=False, sexually_active=True,
                        history_of_impotence=False,
                        history_of_libido_problems=False,
                        family_history_prostate_cancer=False,
                        percent_free_psa=16.0, bmi=26.8, ipss_score=12,
                        max_urinary_flow_ml_s=12.0, biopsy_cores=9,
                        prostate_volume_ml=43.5, residual_urine_ml=40.0),
}


def _reference_patients() -> dict[str, dict]:
    """The clinically ordinary inputs the sensitivity sweep already defines,
    plus the four it cannot cover."""
    import feature_importance as fi

    return {mid: dict(spec[4]) for mid, spec in fi.SPEC.items()} | EXTRA_PATIENTS


ALL_IDS = [m.id for m in mb.list_models()]


def test_list_models_returns_every_implemented_model():
    from mayo_baseline.api import _registry

    implemented = {m["id"] for m in _registry() if m.get("status") == "implemented"}
    assert {m.id for m in mb.list_models()} == implemented
    assert len(implemented) >= 27


@pytest.mark.parametrize("model_id", ALL_IDS)
def test_every_model_resolves_and_reports_its_signature(model_id):
    info = mb.model_info(model_id)
    assert info.id == model_id
    assert info.disease and info.axis and info.year
    assert info.required_inputs or info.optional_inputs, "a model with no inputs"
    assert info.source_url.startswith("https://")


@pytest.mark.parametrize("model_id", ALL_IDS)
def test_every_model_runs_through_predict(model_id):
    """The whole point of the dispatcher. Uses the sweep's reference patient,
    so this also fails if a model's signature drifts from that spec."""
    patients = _reference_patients()
    assert model_id in patients, f"no reference patient for {model_id}"
    out = mb.predict(model_id, **patients[model_id])
    assert isinstance(out, dict)
    assert out["registry_id"] == model_id, (
        f"asked for {model_id} but the result is stamped "
        f"{out.get('registry_id')!r} — the dispatcher lost track of the row"
    )


def test_the_reference_patients_cover_almost_every_model():
    """If the sweep spec falls behind the registry, the test above starts
    skipping silently. This makes that visible."""
    missing = set(ALL_IDS) - set(_reference_patients())
    assert not missing, (
        f"{len(missing)} models have no reference patient, so they are never "
        f"exercised through the API: {sorted(missing)}"
    )


def test_unknown_model_says_what_is_available():
    with pytest.raises(KeyError, match="unknown model"):
        mb.predict("not_a_model", age=50)
    with pytest.raises(KeyError) as exc:
        mb.model_info("not_a_model")
    assert "albi" in str(exc.value), "the error should list what does exist"


def test_a_registered_but_unimplemented_model_says_so():
    """Catalog and gap rows are in the registry but have no code."""
    from mayo_baseline.api import _registry

    catalog = next(m["id"] for m in _registry()
                   if m.get("status") in {"catalog", "gap"})
    with pytest.raises(KeyError, match="not 'implemented'"):
        mb.model_info(catalog)


def test_wrong_arguments_report_the_models_real_signature():
    """`unexpected keyword argument` alone does not tell you what it wanted."""
    with pytest.raises(TypeError) as exc:
        mb.predict("amap", age=55)
    msg = str(exc.value)
    assert "required: age, male, platelets" in msg
    assert "optional:" in msg


def test_filters():
    assert {m.id for m in mb.list_models(disease="liver")} == {"amap", "hap", "albi"}
    assert all(m.axis == "prognosis" for m in mb.list_models(axis="prognosis"))
    assert all(m.verified for m in mb.list_models(verified=True))
    assert all(m.public_repo for m in mb.list_models(has_public_repo=True))
    assert all(not m.public_repo for m in mb.list_models(has_public_repo=False))


def test_predict_many_passes_each_model_only_what_it_accepts():
    """One patient record, several models with different variable sets. Extra
    keys must not raise — that is the whole reason this function exists."""
    out = mb.predict_many(
        ["albi", "amap"],
        age=55, male=True, platelets=200,
        bilirubin_umol_l=15.0, albumin_g_l=42.0,
        irrelevant_field="ignored", another=123,
    )
    assert out["albi"]["grade"] in (1, 2, 3)
    assert 0 <= out["amap"]["score"] <= 100


def test_predict_many_reports_missing_inputs_rather_than_skipping():
    out = mb.predict_many(["albi", "hap"], bilirubin_umol_l=15.0, albumin_g_l=42.0)
    assert "grade" in out["albi"]
    assert "error" in out["hap"]
    assert "afp_ng_ml" in out["hap"]["error"]
    assert "required" in out["hap"]


def test_predict_many_reports_out_of_scope_values_rather_than_raising():
    """A value the model refuses must surface as that model's error, not kill
    the whole batch."""
    out = mb.predict_many(
        ["albi", "amap"],
        age=55, male=True, platelets=-5,          # amap rejects this
        bilirubin_umol_l=15.0, albumin_g_l=42.0,
    )
    assert "grade" in out["albi"], "one model's bad input must not lose the others"
    assert "error" in out["amap"] and "platelets" in out["amap"]["error"]


def test_every_result_carries_its_scope():
    """Running a model is not the same as being entitled to believe it."""
    out = mb.predict_many(["endpac"], glucose_at_diabetes_mg_dl=130,
                          glucose_one_year_before_mg_dl=105,
                          weight_change_kg=-5.0, age_at_diabetes_onset=65)
    assert "new-onset diabetes" in out["endpac"]["scope"]


def test_dual_axis_rows_are_traceable_to_the_row_that_was_asked_for():
    """LIPI is registered on two axes and PREDICT's benefit arm shares its
    prognosis model, so one function serves two rows. The result must say both
    which row was invoked and which model actually ran."""
    out = mb.predict("lipi_prognosis", dnlr=4.0, ldh=300.0,
                     ldh_upper_limit_normal=250.0)
    assert out["registry_id"] == "lipi_prognosis"
    assert out["model_id"] == "lipi"
    assert out["shares_model_with"] == "lipi"

    solo = mb.predict("albi", bilirubin_umol_l=20.0, albumin_g_l=40.0)
    assert solo["registry_id"] == solo["model_id"] == "albi"
    assert "shares_model_with" not in solo, (
        "only genuinely shared models should carry this key"
    )


def test_there_is_no_run_everything_convenience():
    """Deliberate. Each model has a population it was built for, and a function
    that returned 27 numbers for one patient would invite exactly the misuse
    the scope notes exist to prevent."""
    assert not hasattr(mb, "predict_all")
    assert set(mb.__all__) == {
        "predict", "predict_many", "list_models", "model_info", "ModelInfo"
    }
