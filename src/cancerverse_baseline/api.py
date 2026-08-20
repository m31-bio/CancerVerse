"""One way in.

Every model has its own module path and its own signature, which is correct —
they take different clinical inputs — but it means a consumer had to know 27
import paths to use this library. This module is the dispatcher:

    >>> import cancerverse_baseline as mb
    >>> mb.predict("albi", bilirubin_umol_l=20.0, albumin_g_l=40.0)["grade"]
    2

    >>> [m.id for m in mb.list_models(disease="liver")]
    ['amap', 'hap', 'albi']

    >>> mb.model_info("albi").required_inputs
    ()

    >>> mb.predict_many(["amap", "albi"], age=55, male=True, platelets=200,
    ...                 bilirubin_umol_l=15.0, albumin_g_l=42.0)["albi"]["grade"]
    1

Everything is driven by `registry/models.yaml`, so a model that is registered
is callable, and one that is not registered does not exist as far as this
library is concerned.

A deliberate omission
---------------------
There is no "run every model on this patient" convenience. Each model carries a
population it was built for — END-PAC is only meaningful in new-onset diabetes,
the MSK nomograms only after a specific resection — and a function that
cheerfully returned 27 numbers would invite exactly the misuse the scope notes
exist to prevent. `predict_many` takes an explicit list, and every result
carries that model's `scope` back to the caller.
"""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache, lru_cache
from pathlib import Path
from typing import Any

import yaml

_REGISTRY = Path(__file__).resolve().parents[2] / "registry" / "models.yaml"


@dataclass(frozen=True)
class ModelInfo:
    """What a caller needs to decide whether to use a model, and how."""

    id: str
    title: str
    disease: str
    axis: str
    year: int | None
    architecture: str
    core_formula: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...]
    scope: str
    citation: str
    source_url: str
    public_repo: str | None
    verified: bool
    verification: str
    discrimination: str | None
    developed_on: str | None
    code: str
    _fn: Callable[..., dict] = field(repr=False, compare=False, default=None)

    def __call__(self, **inputs: Any) -> dict:
        return self._fn(**inputs)


@lru_cache(maxsize=1)
def _registry() -> list[dict]:
    return yaml.safe_load(_REGISTRY.read_text())["models"]


def _resolve(entry: dict) -> Callable[..., dict]:
    """Look up the model's function by the name the registry gives.

    Deliberately not inferred. Two things defeat inference here: `erspc_rc3`'s
    module exposes both `erspc_rc3_predict` and `erspc_rc45_predict`, and the
    dual-axis rows (`predict_breast_response`, `lipi_prognosis`) point at
    packages that RE-EXPORT a function defined elsewhere, so its `__module__`
    does not match. Guessing between near-identical names is also the exact
    shape of a defect this project already hit once, when PREDICT was compared
    against `benefits222` (disease-free survival) instead of `benefits22`
    (overall survival). So the registry names the entrypoint and we use it.
    """
    name = entry.get("entrypoint")
    if not name:
        raise LookupError(
            f"{entry['id']!r} has no `entrypoint` in the registry, so there is "
            f"no unambiguous function to call in {entry['code']}"
        )
    module = importlib.import_module(entry["code"])
    try:
        return getattr(module, name)
    except AttributeError as exc:
        raise LookupError(
            f"{entry['id']!r}: {entry['code']} has no {name!r}"
        ) from exc


def _split_inputs(fn: Callable) -> tuple[tuple[str, ...], tuple[str, ...]]:
    required, optional = [], []
    for name, p in inspect.signature(fn).parameters.items():
        if p.kind in (p.VAR_KEYWORD, p.VAR_POSITIONAL):
            continue
        (optional if p.default is not p.empty else required).append(name)
    return tuple(required), tuple(optional)


@cache
def _info(model_id: str) -> ModelInfo:
    for entry in _registry():
        if entry["id"] != model_id:
            continue
        if entry.get("status") != "implemented":
            raise KeyError(
                f"{model_id!r} is registered with status {entry.get('status')!r}, "
                f"not 'implemented' — there is no code to call"
            )
        fn = _resolve(entry)
        req, opt = _split_inputs(fn)
        return ModelInfo(
            id=entry["id"],
            title=entry.get("title", ""),
            disease=entry.get("disease", ""),
            axis=entry.get("axis", ""),
            year=entry.get("year"),
            architecture=entry.get("architecture_family", ""),
            core_formula=entry.get("core_formula", ""),
            required_inputs=req,
            optional_inputs=opt,
            scope=entry.get("scope_note", ""),
            citation=entry.get("citation", ""),
            source_url=entry.get("source_url", ""),
            public_repo=entry.get("public_repo"),
            verified=entry.get("parity_status") in {"checked", "matched"},
            verification=entry.get("parity_note", ""),
            discrimination=entry.get("discrimination"),
            developed_on=entry.get("development_cohort"),
            code=entry["code"],
            _fn=fn,
        )
    known = ", ".join(sorted(m["id"] for m in _registry()
                             if m.get("status") == "implemented"))
    raise KeyError(f"unknown model {model_id!r}. Implemented models: {known}")


def model_info(model_id: str) -> ModelInfo:
    """Everything the registry knows about one model, plus its real signature."""
    return _info(model_id)


def list_models(
    *,
    disease: str | None = None,
    axis: str | None = None,
    verified: bool | None = None,
    has_public_repo: bool | None = None,
) -> list[ModelInfo]:
    """Implemented models, optionally filtered. Sorted by disease then axis."""
    order = {"detection": 0, "response": 1, "prognosis": 2}
    out = []
    for entry in _registry():
        if entry.get("status") != "implemented":
            continue
        if disease and entry.get("disease") != disease:
            continue
        if axis and entry.get("axis") != axis:
            continue
        info = _info(entry["id"])
        if verified is not None and info.verified is not verified:
            continue
        if has_public_repo is not None and bool(info.public_repo) is not has_public_repo:
            continue
        out.append(info)
    out.sort(key=lambda i: (i.disease, order.get(i.axis, 9), i.id))
    return out


def predict(model_id: str, /, **inputs: Any) -> dict:
    """Run one model.

    Unknown or missing arguments raise with the model's actual signature
    attached, because "unexpected keyword argument" on its own does not tell
    you what the model wanted.
    """
    info = _info(model_id)
    try:
        out = dict(info(**inputs))
    except TypeError as exc:
        raise TypeError(
            f"{model_id}: {exc}\n"
            f"  required: {', '.join(info.required_inputs) or '(none)'}\n"
            f"  optional: {', '.join(info.optional_inputs) or '(none)'}"
        ) from exc
    return _stamp(out, model_id)


def _stamp(out: dict, requested: str) -> dict:
    """Record which registry row was invoked.

    Two rows can share one function: LIPI is registered on both the response
    and prognosis axes, and PREDICT's benefit output on the response axis is
    the same model as its prognosis row. The module returns its own identity in
    `model_id`, which is right — it is one model — but a caller who asked for
    `lipi_prognosis` and got back `lipi` cannot tie the result to the row that
    documents it. So the requested id is stamped alongside rather than over.

    This is the same traceability the `gail_bcrat` / `bcrat` mismatch broke
    earlier in this project.
    """
    out["registry_id"] = requested
    if out.get("model_id") != requested:
        out["shares_model_with"] = out.get("model_id")
    return out


def predict_many(model_ids: list[str], /, **patient: Any) -> dict[str, dict]:
    """Run several models on one patient, passing each only what it accepts.

    Extra keys in `patient` are ignored per model rather than raising, which is
    the point — one patient record feeds models with different variable sets.
    A model missing a *required* input is reported, not silently skipped:

        {"albi": {...result...},
         "amap": {"error": "missing required inputs: platelets"}}

    Each successful result carries `scope`, because running a model is not the
    same as being entitled to believe it.
    """
    results: dict[str, dict] = {}
    for model_id in model_ids:
        info = _info(model_id)
        accepted = set(info.required_inputs) | set(info.optional_inputs)
        missing = [k for k in info.required_inputs if k not in patient]
        if missing:
            results[model_id] = {
                "error": f"missing required inputs: {', '.join(missing)}",
                "required": list(info.required_inputs),
            }
            continue
        try:
            out = _stamp(
                dict(info(**{k: v for k, v in patient.items() if k in accepted})),
                model_id,
            )
            out["scope"] = info.scope
            results[model_id] = out
        except Exception as exc:                    # out-of-scope values raise
            results[model_id] = {"error": f"{type(exc).__name__}: {exc}"}
    return results
