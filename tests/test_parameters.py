"""Tests for the parameter-level audit in registry/parameters.yaml.

The audit is prose about running code, which is the kind of document that rots
silently. These tests make it fail loudly instead: every implemented model must
appear, every parameter must name an argument the code actually accepts, and
every coefficient recorded as a number must be the number the module holds.

The last one is the point. A coefficient typed into a YAML file is a second
copy, and this repository has already shipped one wrong coefficient (ALBI's
-0.0852, taken from a search summary rather than the paper) from a far smaller
transcription than 210 rows.
"""

from __future__ import annotations

import contextlib
import importlib
import inspect
import re
from pathlib import Path

import pytest
import yaml

from cancerverse_baseline.registry import load_models

ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = ROOT / "registry" / "parameters.yaml"

AUDIT = yaml.safe_load(PARAMETERS.read_text())["parameters"]
IMPLEMENTED = [m for m in load_models() if m.get("status") == "implemented"]


#: Rows that describe something other than a keyword argument, an intercept, a
#: baseline hazard, a rescaling step, a selection rule. They are bracketed by
#: convention so they can be told apart from real inputs without a list here.
def _is_structural(name: str) -> bool:
    return name.strip().startswith("(")


def test_every_implemented_model_is_audited():
    missing = sorted({m["id"] for m in IMPLEMENTED} - set(AUDIT))
    assert not missing, f"implemented but absent from parameters.yaml: {missing}"


def test_no_audited_model_has_been_retired():
    """A model demoted to `catalog` must not linger here claiming to be live.

    This caught the 2018 PBCG on the day it was superseded by pbcg_extended.
    """
    extra = sorted(set(AUDIT) - {m["id"] for m in IMPLEMENTED})
    assert not extra, f"audited but no longer implemented: {extra}"


@pytest.mark.parametrize("model_id", sorted(AUDIT))
def test_axis_matches_the_registry(model_id):
    registry_axis = next(m["axis"] for m in IMPLEMENTED if m["id"] == model_id)
    assert AUDIT[model_id]["axis"] == registry_axis


@pytest.mark.parametrize("model_id", sorted(AUDIT))
def test_every_model_states_how_importance_was_decided(model_id):
    block = AUDIT[model_id]
    for field in ("importance_basis", "top_parameter", "top_parameter_why"):
        assert block.get(field), f"{model_id} is missing {field}"


@pytest.mark.parametrize("model_id", sorted(AUDIT))
def test_the_top_parameter_is_one_of_the_parameters(model_id):
    block = AUDIT[model_id]
    names = {p["name"] for p in block["params"]}
    top = block["top_parameter"]
    assert top in names, (
        f"{model_id}: top_parameter {top!r} is not among its parameters {sorted(names)}"
    )


@pytest.mark.parametrize("model_id", sorted(AUDIT))
def test_rank_one_exists_and_agrees_with_the_top_parameter(model_id):
    block = AUDIT[model_id]
    firsts = [p["name"] for p in block["params"] if p.get("importance_rank") == 1]
    assert firsts, f"{model_id} has no parameter ranked 1"
    assert block["top_parameter"] in firsts, (
        f"{model_id}: top_parameter is {block['top_parameter']!r} but rank 1 is {firsts}"
    )


@pytest.mark.parametrize("model_id", sorted(AUDIT))
def test_every_parameter_carries_a_transform(model_id):
    """`transform` and `transform_kind` are the whole point of the audit.

    A blank one means somebody added a row and did not answer the question the
    file exists to answer.
    """
    for p in AUDIT[model_id]["params"]:
        assert p.get("transform"), f"{model_id}.{p['name']} has no transform"
        assert p.get("transform_kind"), f"{model_id}.{p['name']} has no transform_kind"
        assert p.get("units"), f"{model_id}.{p['name']} has no units"


def _entrypoint(model: dict):
    module = importlib.import_module(model["code"])
    return getattr(module, model["entrypoint"])


@pytest.mark.parametrize("model_id", sorted(AUDIT))
def test_parameter_names_are_real_arguments(model_id):
    """Every non-structural parameter must be an argument the function takes.

    Several rows deliberately name a pair (`weight_lb / height_in`) or a
    sex-specific argument, so the check accepts any of the slash-separated
    parts being real.
    """
    model = next(m for m in IMPLEMENTED if m["id"] == model_id)
    if not model.get("entrypoint") or not model.get("code"):
        pytest.skip(f"{model_id} declares no entrypoint")
    sig = inspect.signature(_entrypoint(model))
    accepted = set(sig.parameters)
    if any(p.kind is p.VAR_KEYWORD for p in sig.parameters.values()):
        pytest.skip(f"{model_id} takes **kwargs; names cannot be checked here")

    for p in AUDIT[model_id]["params"]:
        name = p["name"]
        if _is_structural(name):
            continue
        parts = [q.strip() for q in name.split("/")]
        assert any(q in accepted for q in parts), (
            f"{model_id}: parameter {name!r} is not an argument of "
            f"{model['entrypoint']}; accepted are {sorted(accepted)}"
        )


#: (model id, parameter name) -> (module path, constant name). Only where the
#: module exposes the coefficient as a named constant; splined and per-variant
#: coefficients live in tables and are covered by the parity tests instead.
PINNED = {
    ("albi", "albumin_g_l"): ("cancerverse_baseline.liver.prognosis.albi", "ALBUMIN_COEF"),
    ("albi", "bilirubin_umol_l"): (
        "cancerverse_baseline.liver.prognosis.albi",
        "BILIRUBIN_COEF",
    ),
    ("amap", "age"): ("cancerverse_baseline.liver.detection.amap", "AGE_BETA"),
    ("amap", "male"): ("cancerverse_baseline.liver.detection.amap", "MALE_BETA"),
    ("amap", "platelets"): ("cancerverse_baseline.liver.detection.amap", "PLATELET_BETA"),
    ("amap", "(ALBI component)"): ("cancerverse_baseline.liver.detection.amap", "ALBI_BETA"),
    ("erspc_rc3", "psa"): ("cancerverse_baseline.prostate.detection.coefficients", "RC3_PSA"),
    ("erspc_rc3", "volume_ml"): (
        "cancerverse_baseline.prostate.detection.coefficients",
        "RC3_VOL",
    ),
    ("erspc_rc3", "dre_positive"): (
        "cancerverse_baseline.prostate.detection.coefficients",
        "RC3_DRE",
    ),
    ("erspc_rc3", "(intercept)"): (
        "cancerverse_baseline.prostate.detection.coefficients",
        "RC3_INTERCEPT",
    ),
    ("ukb_hnc", "age"): ("cancerverse_baseline.head_neck.detection.ukb_hnc", "BETA_AGE"),
    ("ukb_hnc", "bmi"): ("cancerverse_baseline.head_neck.detection.ukb_hnc", "BETA_BMI"),
    ("ukb_hnc", "male"): ("cancerverse_baseline.head_neck.detection.ukb_hnc", "BETA_MALE"),
    ("ukb_hnc", "(intercept)"): (
        "cancerverse_baseline.head_neck.detection.ukb_hnc",
        "INTERCEPT",
    ),
    ("plcom2012", "age"): ("cancerverse_baseline.lung.detection.coefficients", "AGE"),
    ("plcom2012", "bmi"): ("cancerverse_baseline.lung.detection.coefficients", "BMI"),
    ("plcom2012", "copd"): ("cancerverse_baseline.lung.detection.coefficients", "COPD"),
    ("plcom2012", "cigarettes_per_day"): (
        "cancerverse_baseline.lung.detection.coefficients",
        "SMOKING_INTENSITY",
    ),
    ("plcom2012", "smoking_duration_years"): (
        "cancerverse_baseline.lung.detection.coefficients",
        "SMOKING_DURATION",
    ),
    ("plcom2012", "quit_years"): (
        "cancerverse_baseline.lung.detection.coefficients",
        "SMOKING_QUIT_TIME",
    ),
    ("plcom2012", "education_level"): (
        "cancerverse_baseline.lung.detection.coefficients",
        "EDUCATION",
    ),
    ("plcom2012", "(intercept)"): (
        "cancerverse_baseline.lung.detection.coefficients",
        "INTERCEPT",
    ),
    ("plcom2012", "family_history_lung_cancer"): (
        "cancerverse_baseline.lung.detection.coefficients",
        "FAMILY_HISTORY_LUNG_CANCER",
    ),
    ("plcom2012", "personal_cancer_history"): (
        "cancerverse_baseline.lung.detection.coefficients",
        "PERSONAL_CANCER_HISTORY",
    ),
    ("plcom2012", "current_smoker"): (
        "cancerverse_baseline.lung.detection.coefficients",
        "SMOKING_STATUS_CURRENT",
    ),
    ("score2", "age"): ("cancerverse_baseline.cvd.detection.coefficients", "COEFFS.male.age"),
    ("score2", "smoker"): (
        "cancerverse_baseline.cvd.detection.coefficients",
        "COEFFS.male.smoking",
    ),
    ("score2", "sbp"): ("cancerverse_baseline.cvd.detection.coefficients", "COEFFS.male.sbp"),
    ("score2", "total_chol_mmol"): (
        "cancerverse_baseline.cvd.detection.coefficients",
        "COEFFS.male.tchol",
    ),
    ("score2", "hdl_mmol"): (
        "cancerverse_baseline.cvd.detection.coefficients",
        "COEFFS.male.hdl",
    ),
    ("score2", "diabetes"): (
        "cancerverse_baseline.cvd.detection.coefficients",
        "COEFFS.male.diabetes",
    ),
    ("msk_gastric", "male"): (
        "cancerverse_baseline.gastric.prognosis.msk_gastric",
        "MALE_BETA",
    ),
    ("msk_gastric", "size_cm"): (
        "cancerverse_baseline.gastric.prognosis.msk_gastric",
        "SIZE_BETA",
    ),
    ("predict_breast_response", "trastuzumab"): (
        "cancerverse_baseline.breast.prognosis.predict",
        "TRASTUZUMAB_BETA",
    ),
    ("predict_breast_response", "hormone"): (
        "cancerverse_baseline.breast.prognosis.predict",
        "HORMONE_BETA",
    ),
    ("predict_breast_response", "bisphosphonate"): (
        "cancerverse_baseline.breast.prognosis.predict",
        "BISPHOSPHONATE_BETA",
    ),
    ("kunzmann", "(points divisor)"): (
        "cancerverse_baseline.esophageal.detection.kunzmann",
        "SMALLEST_COEFFICIENT",
    ),
}


def _resolve(path: str, dotted: str):
    obj = importlib.import_module(path)
    for part in dotted.split("."):
        obj = obj[part] if isinstance(obj, dict) else getattr(obj, part)
    return obj


@pytest.mark.parametrize("key", sorted(PINNED))
def test_recorded_coefficient_matches_the_code(key):
    model_id, param_name = key
    module_path, dotted = PINNED[key]
    param = next(p for p in AUDIT[model_id]["params"] if p["name"] == param_name)
    recorded = param["coefficient"]
    assert recorded is not None, f"{model_id}.{param_name} records no coefficient"
    assert recorded == pytest.approx(_resolve(module_path, dotted)), (
        f"{model_id}.{param_name}: parameters.yaml says {recorded}, "
        f"{module_path}.{dotted} says {_resolve(module_path, dotted)}"
    )


#: Coefficients that are deliberately NOT findable in the model's own tree, with
#: the reason. Each one is a real fact about where the number lives, not an
#: excuse: keep this list short and make every entry say something checkable.
_UNFINDABLE_OK = {
    # PREDICT is one implementation serving two axes, the treatment betas live
    # in the prognosis module, and the response entry points at the same code.
    (
        "predict_breast_response",
        "(radiotherapy)",
    ): "a zero-effect placeholder; the model has no radiotherapy term at all",
}


def _numeric_literals(paths):
    """Every number that appears anywhere in these files."""
    out = set()
    for p in paths:
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        for token in re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", text):
            # The regex over-matches: a bare "-" or a trailing "." reaches
            # here and is not a number worth collecting.
            with contextlib.suppress(ValueError):
                out.add(float(token))
    return out


def _search_tree(model_id: str) -> list[Path]:
    """The files a model's coefficients could legitimately live in.

    Its own module, plus everything beside it, coefficients are routinely
    split into a `coefficients.py` or shipped as .json/.csv next to the code,
    and PLCOm2012, SCORE2, PREVENT, PBCG and the Optum LASSO all do exactly
    that. `predict_breast_response` reaches wider still: it is the same
    implementation as `predict_breast`, one directory over.
    """
    entry = next(m for m in IMPLEMENTED if m["id"] == model_id)
    module = importlib.import_module(entry["code"])
    here = Path(inspect.getfile(module)).parent
    roots = [here]
    # one implementation serving two axes: search the whole disease package
    if model_id.startswith("predict_breast"):
        roots = [here.parent]
    files = []
    for root in roots:
        files += [
            p
            for p in root.rglob("*")
            if p.is_file() and p.suffix in {".py", ".json", ".csv", ".tsv", ".txt"}
        ]
    return files


_UNPINNED = sorted(
    (mid, p["name"])
    for mid, audit in AUDIT.items()
    for p in audit["params"]
    if p.get("coefficient") is not None and (mid, p["name"]) not in PINNED
)


@pytest.mark.parametrize("key", _UNPINNED)
def test_unpinned_coefficients_still_appear_in_the_code(key):
    """The backstop under `PINNED`, which covers only 33 of 166 coefficients.

    `PINNED` names the exact constant and is the stronger check; it is also
    hand-written, so it will always trail the registry. Everything it does not
    reach gets this weaker test instead: the recorded value must at least occur
    somewhere in the model's own code tree.

    What it catches is the failure that actually happens, someone edits a
    coefficient on one side and not the other, and nothing notices because the
    two files are hundreds of lines apart in different directories. What it
    cannot catch is a value that appears in the tree but is not the constant
    this row describes. When that distinction matters, add the row to `PINNED`.

    Written 2026-08-17 after a manual sweep of all 38 implemented models found
    no drift. The point of the test is that the next sweep should not have to
    be manual.
    """
    model_id, param_name = key
    if key in _UNFINDABLE_OK:
        pytest.skip(_UNFINDABLE_OK[key])
    param = next(p for p in AUDIT[model_id]["params"] if p["name"] == param_name)
    recorded = float(param["coefficient"])
    literals = _numeric_literals(_search_tree(model_id))
    assert any(
        abs(recorded - lit) <= max(1e-9, abs(recorded) * 1e-9) for lit in literals
    ), (
        f"{model_id}.{param_name}: parameters.yaml records {recorded}, which "
        f"appears nowhere in the model's code tree. Either the registry drifted "
        f"from the code, or the coefficient lives somewhere this test does not "
        f"look, if the latter, pin it in PINNED or record it in _UNFINDABLE_OK."
    )


def test_the_audit_covers_every_parameter_the_sweep_measures():
    """Anything feature_importance.py sweeps must appear in the audit.

    The sweep and the audit are the two halves of the importance answer,
    measured and cited. A predictor in one and not the other means one of them
    was updated and the other was not.
    """
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    import feature_importance as fi

    implemented = {m["id"] for m in IMPLEMENTED}
    problems = []
    for model_id, spec in fi.SPEC.items():
        if model_id not in implemented:
            # The sweep may still carry a model the registry has demoted to
            # `catalog`, that is staleness in the sweep, not a hole in the
            # audit, and test_no_audited_model_has_been_retired covers the
            # direction that matters.
            continue
        if model_id not in AUDIT:
            problems.append(f"{model_id} is swept but not audited")
            continue
        kwargs = {kw for _, (kw, _) in spec[5].items()}
        audited = {p["name"] for p in AUDIT[model_id]["params"]}
        # a row may name a pair, e.g. "weight_lb / height_in"
        audited |= {q.strip() for n in audited for q in n.split("/")}
        for kw in kwargs - audited:
            problems.append(f"{model_id}: sweep varies {kw!r}, audit does not list it")
    assert not problems, "\n".join(problems)


#: The vocabulary documented at the top of registry/parameters.yaml. A
#: transform_kind is allowed to compose these with " + ", and to carry a
#: parenthesised qualifier, but it may not invent a new base word.
#:
#: This exists because the ADNEX entry arrived using `indicator`, `linear` and
#: `ratio` where the rest of the file says `dichotomy`, `identity` and
#: `derived`. Three synonyms for things already named is how a controlled
#: vocabulary stops being one, and the Parameters sheet groups on this column.
TRANSFORM_KINDS = {
    # the shapes a value can be put through
    "identity",
    "centering",
    "scaling",
    "negative scaling",
    "unit conversion",
    "log",
    "log2",
    "log10",
    "reciprocal",
    "power",
    "fractional polynomial",
    "spline",
    "banding",
    "difference",
    "rescaling",
    # the shapes a category can be put through
    "dichotomy",
    "categorical",
    "ordinal",
    # structural: not a transform of one value at all
    "derived",
    "interaction",
    "integration",
    "stratified slope",
    "time-varying",
    "fractional imputation",
    "none",
}

#: transform_kind composes with " + " (both apply), " / " (one per stratum,
#: e.g. ER-positive versus ER-negative) and " with " (a qualifier). A
#: parenthesised aside is dropped before checking.
_KIND_SPLIT = re.compile(r"\s*[+/]\s*|\s+with\s+")


def _base_words(kind: str) -> list[str]:
    kind = re.sub(r"\(.*?\)", " ", kind)
    return [w.strip().lower() for w in _KIND_SPLIT.split(kind) if w.strip()]


@pytest.mark.parametrize("model_id", sorted(AUDIT))
def test_transform_kind_uses_the_documented_vocabulary(model_id):
    for p in AUDIT[model_id]["params"]:
        for word in _base_words(str(p["transform_kind"])):
            # allow multi-word qualifiers like "unit conversion"
            if any(w in TRANSFORM_KINDS for w in word.split()):
                continue
            assert word in TRANSFORM_KINDS, (
                f"{model_id}.{p['name']}: transform_kind {p['transform_kind']!r} "
                f"uses {word!r}, which is not in the documented vocabulary "
                f"{sorted(TRANSFORM_KINDS)}"
            )


def test_adnex_coefficients_match_the_published_appendix_d():
    """ADNEX records the stage II-IV column; pin it to the code's own table.

    Its `coefficient_note` carries all four linear predictors as prose, which
    no test can check. The one machine-checkable number per row is the headline
    `coefficient`, and this asserts it against _Z rather than against a second
    transcription.
    """
    from cancerverse_baseline.ovarian.detection.adnex import _Z

    # _Z rows are (intercept, age, log2 CA-125, log2 lesion, D/C, (D/C)^2,
    # locules, papillary, shadows, ascites, centre)
    expected = dict(
        zip(
            [
                "(intercept)",
                "age",
                "ca125",
                "lesion_diameter_mm",
                "solid_diameter_mm",
                None,
                "more_than_10_locules",
                "papillary_structures",
                "acoustic_shadows",
                "ascites",
                "oncology_centre",
            ],
            _Z["stage_ii_iv"],
            strict=True,
        )
    )
    expected.pop(None)

    audited = {p["name"]: p for p in AUDIT["iota_adnex"]["params"]}
    assert set(audited) == set(expected), (
        f"audit lists {sorted(audited)}, Appendix D has {sorted(expected)}"
    )
    for name, beta in expected.items():
        assert audited[name]["coefficient"] == pytest.approx(beta), name

    # the squared ratio term is a term, not a footnote
    assert audited["solid_diameter_mm"]["coefficient_squared"] == pytest.approx(
        _Z["stage_ii_iv"][5]
    )
