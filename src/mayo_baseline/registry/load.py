"""Load disease/model registry YAML (single source of truth)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

AXES = ("detection", "response", "prognosis")

# Two independent queues for each coded model:
#   open_source:   available | web_only | none
#   parity_status: checked | not_checked | blocked_by_license | n/a


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _registry_dir() -> Path:
    return _repo_root() / "registry"


def load_diseases(path: Path | None = None) -> list[dict[str, Any]]:
    import yaml

    p = path or (_registry_dir() / "diseases.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return list(data.get("diseases", []))


def load_models(path: Path | None = None) -> list[dict[str, Any]]:
    import yaml

    p = path or (_registry_dir() / "models.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return list(data.get("models", []))


_STATUS_RANK = {"implemented": 0, "stub": 1, "catalog": 2, "gap": 3}
_PARITY_RANK = {"checked": 0, "matched": 0}  # matched kept as alias during transition


def _flagship_rank(model: dict[str, Any]) -> tuple[int, int]:
    return (
        _STATUS_RANK.get(model.get("status", "gap"), 9),
        _PARITY_RANK.get(model.get("parity_status"), 1),
    )


def _is_checked(model: dict[str, Any]) -> bool:
    return model.get("parity_status") in {"checked", "matched"}


def reproducibility_scoreboard(
    models: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Count models on two queues: open source, and reproduction check."""
    models = models if models is not None else load_models()
    implemented = [m for m in models if m.get("status") == "implemented"]
    checked = [m for m in implemented if _is_checked(m)]
    not_checked = [m for m in implemented if not _is_checked(m)]

    by_open: dict[str, list[str]] = {"available": [], "web_only": [], "none": []}
    for m in implemented:
        key = m.get("open_source") or "none"
        by_open.setdefault(key, []).append(m["id"])

    return {
        "implemented": sorted(m["id"] for m in implemented),
        "checked": sorted(m["id"] for m in checked),
        "not_checked": sorted(m["id"] for m in not_checked),
        # Back-compat aliases
        "matched": sorted(m["id"] for m in checked),
        "unmatched": sorted(m["id"] for m in not_checked),
        "open_source_available": sorted(by_open.get("available", [])),
        "open_source_web_only": sorted(by_open.get("web_only", [])),
        "open_source_none": sorted(by_open.get("none", [])),
        "n_cells": len(load_diseases()) * len(AXES),
        "n_implemented": len(implemented),
        "n_checked": len(checked),
        "n_matched": len(checked),
        "n_open_source_available": len(by_open.get("available", [])),
    }


_TIER_RANK = {"A": 0, "B": 1, "C": 2, "D": 3}


def cell_tiers(
    diseases: list[dict[str, Any]] | None = None,
    models: list[dict[str, Any]] | None = None,
) -> dict[tuple[str, str], str]:
    diseases = diseases if diseases is not None else load_diseases()
    models = models if models is not None else load_models()
    best: dict[tuple[str, str], str] = {}
    for m in models:
        tier = m.get("repro_tier")
        if not tier:
            continue
        key = (m["disease"], m["axis"])
        if key not in best or _TIER_RANK[tier] < _TIER_RANK[best[key]]:
            best[key] = tier
    return {
        (d["id"], a): best.get((d["id"], a), "?")
        for d in diseases
        for a in AXES
    }


def progress_report(
    diseases: list[dict[str, Any]] | None = None,
    models: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    diseases = diseases if diseases is not None else load_diseases()
    models = models if models is not None else load_models()
    tiers = cell_tiers(diseases, models)
    matrix = coverage_matrix(diseases, models)

    implemented_cells, reachable_cells, unreachable_cells, unassessed = [], [], [], []
    checked_cells = []
    for (disease, axis), tier in tiers.items():
        cell = matrix[disease][axis]
        done = bool(cell and cell.get("status") == "implemented")
        if done:
            implemented_cells.append((disease, axis))
            if _is_checked(cell):
                checked_cells.append((disease, axis))
        if tier == "D":
            unreachable_cells.append((disease, axis))
        elif tier == "?":
            unassessed.append((disease, axis))
        else:
            reachable_cells.append((disease, axis))

    reachable = set(reachable_cells) | set(implemented_cells)
    reachable -= set(unreachable_cells)
    remaining = sorted(reachable - set(implemented_cells))

    impl_models = [m for m in models if m.get("status") == "implemented"]
    checked_models = [m for m in impl_models if _is_checked(m)]

    n_cells = len(diseases) * len(AXES)
    return {
        "n_cells_nominal": n_cells,
        "n_cells_unreachable": len(unreachable_cells),
        "n_cells_reachable": len(reachable),
        "n_cells_implemented": len(implemented_cells),
        "n_cells_remaining": len(remaining),
        "pct_of_nominal": 100.0 * len(implemented_cells) / n_cells,
        "pct_of_reachable": (
            100.0 * len(implemented_cells) / len(reachable) if reachable else 0.0
        ),
        "n_models_implemented": len(impl_models),
        "n_models_checked": len(checked_models),
        "n_models_matched": len(checked_models),
        "pct_models_checked": (
            100.0 * len(checked_models) / len(impl_models) if impl_models else 0.0
        ),
        "pct_models_matched": (
            100.0 * len(checked_models) / len(impl_models) if impl_models else 0.0
        ),
        "remaining_cells": remaining,
        "unreachable_cells": sorted(unreachable_cells),
        "unassessed_cells": sorted(unassessed),
        "checked_cells": sorted(checked_cells),
        "matched_cells": sorted(checked_cells),
        "by_axis": {
            axis: {
                "implemented": sum(1 for d, a in implemented_cells if a == axis),
                "reachable": sum(1 for d, a in reachable if a == axis),
                "unreachable": sum(1 for d, a in unreachable_cells if a == axis),
            }
            for axis in AXES
        },
        "parity_blockers": parity_blockers(models),
        "open_source_queues": open_source_queues(models),
    }


def open_source_queues(models: list[dict[str, Any]] | None = None) -> dict[str, list[str]]:
    """Queue 1: does an open upstream implementation exist?"""
    models = models if models is not None else load_models()
    out: dict[str, list[str]] = {"available": [], "web_only": [], "none": []}
    for m in models:
        if m.get("status") != "implemented":
            continue
        key = m.get("open_source") or "none"
        out.setdefault(key, []).append(m["id"])
    return {k: sorted(v) for k, v in out.items()}


def parity_blockers(models: list[dict[str, Any]] | None = None) -> dict[str, list[str]]:
    """Queue 2 blockers: why a coded model is not_checked yet."""
    models = models if models is not None else load_models()
    out: dict[str, list[str]] = {}
    for m in models:
        if m.get("status") != "implemented" or _is_checked(m):
            continue
        out.setdefault(m.get("parity_blocker", "unclassified"), []).append(m["id"])
    return {k: sorted(v) for k, v in sorted(out.items())}


def coverage_matrix(
    diseases: list[dict[str, Any]] | None = None,
    models: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, dict[str, Any] | None]]:
    diseases = diseases if diseases is not None else load_diseases()
    models = models if models is not None else load_models()

    matrix: dict[str, dict[str, dict[str, Any] | None]] = {
        d["id"]: {a: None for a in AXES} for d in diseases
    }

    for m in models:
        if m.get("role") != "flagship":
            continue
        did, axis = m["disease"], m["axis"]
        if did not in matrix or axis not in matrix[did]:
            continue
        cur = matrix[did][axis]
        if cur is None or _flagship_rank(m) < _flagship_rank(cur):
            matrix[did][axis] = m
    return matrix


def load() -> dict[str, Any]:
    diseases = load_diseases()
    models = load_models()
    return {
        "diseases": diseases,
        "models": models,
        "matrix": coverage_matrix(diseases, models),
        "axes": list(AXES),
    }
