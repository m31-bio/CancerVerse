"""Shared fixtures.

Kept deliberately small. The parity tests each pin their own reference data
next to themselves under `tests/parity/reference/`, because a fixture shared
across models is a place where one model's captured values can silently start
serving another's test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def registry() -> list[dict]:
    """The registry, loaded once per session."""
    import yaml

    return yaml.safe_load((ROOT / "registry" / "models.yaml").read_text())["models"]


@pytest.fixture(scope="session")
def implemented(registry: list[dict]) -> list[dict]:
    return [m for m in registry if m.get("status") == "implemented"]


@pytest.fixture
def reference_cases():
    """Load a captured reference file by name from tests/parity/reference/.

    def test_x(reference_cases):
        cases = reference_cases("crc_pro_cases.json")
    """
    base = ROOT / "tests" / "parity" / "reference"

    def _load(name: str):
        path = base / name
        assert path.exists(), (
            f"missing reference data: {path.relative_to(ROOT)}. "
            "Regenerate it with the script named in the model's registry entry."
        )
        return json.loads(path.read_text())

    return _load

# --- one registry per run -------------------------------------------------
#
# `load_models()` re-reads and re-parses registry/models.yaml on every call,
# and the suite calls it at least 77 times: 9.5s of a 15.3s run spent parsing
# the same 384 KB file, and 77 separate chances to see a different version of
# it.
#
# That stopped being theoretical on 2026-08-18. A second session was editing
# the registry while the suite ran, and two consecutive full runs each failed a
# DIFFERENT unrelated test -- `test_no_public_repo_is_claimed_for_a_model_
# marked_otherwise`, then `test_no_registry_url_is_visibly_malformed` -- both
# passing on their own seconds later. Nothing in the output said "the file
# changed underneath you"; diagnosing it meant stat-ing the file by hand.
#
# So: load once, hand every caller a copy of that one snapshot, and if the file
# changes during the run, say so in those words and fail. A run that read two
# different registries has not tested either of them.

_SNAPSHOT: dict = {}


def _registry_digest() -> str:
    import hashlib

    return hashlib.sha256(
        (ROOT / "registry" / "models.yaml").read_bytes()
    ).hexdigest()


def pytest_configure(config):
    """Pin the whole session to a single parse of the registry.

    This has to be `pytest_configure` and not a session fixture: fixtures run
    after collection, and `tests/test_registry.py` binds `load_models` at
    module import time. A fixture-based version of this patch left 66 of the
    77 reads in place, because that one `from ... import load_models` had
    already copied the unpatched reference. `pytest_configure` runs before any
    test module is imported, so the name it binds is the pinned one.
    """
    import copy
    import importlib
    import sys

    import yaml

    import mayo_baseline.registry as pkg

    # `registry/__init__.py` re-exports a FUNCTION named `load`, which shadows
    # the submodule of the same name -- `from mayo_baseline.registry import
    # load` hands back the function. Go through sys.modules for the module.
    importlib.import_module("mayo_baseline.registry.load")
    loader = sys.modules["mayo_baseline.registry.load"]

    path = ROOT / "registry" / "models.yaml"
    snapshot = yaml.safe_load(path.read_text(encoding="utf-8"))["models"]
    _SNAPSHOT["digest"] = _registry_digest()
    _SNAPSHOT["original"] = loader.load_models

    def pinned(p=None):
        # An explicit path means the caller wants that file, not the default.
        if p is not None and Path(p) != path:
            return _SNAPSHOT["original"](p)
        # A copy per call, because the unpinned loader returned fresh objects
        # and a test that mutates a model dict must not poison later ones.
        return copy.deepcopy(snapshot)

    loader.load_models = pinned
    pkg.load_models = pinned


def pytest_unconfigure(config):
    import sys

    if "original" not in _SNAPSHOT:
        return
    import mayo_baseline.registry as pkg

    sys.modules["mayo_baseline.registry.load"].load_models = _SNAPSHOT["original"]
    pkg.load_models = _SNAPSHOT["original"]


def pytest_sessionfinish(session, exitstatus):
    """Fail loudly if the registry moved while the suite was running."""
    if not _SNAPSHOT:
        return
    if _registry_digest() == _SNAPSHOT["digest"]:
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    msg = (
        "registry/models.yaml CHANGED DURING THIS RUN. Results are not "
        "trustworthy -- different tests may have been checked against "
        "different registries. Re-run on a quiet tree before believing "
        "either outcome."
    )
    if reporter is not None:
        reporter.write_sep("=", "unreliable run", red=True)
        reporter.write_line(msg, red=True)
    session.exitstatus = 1
