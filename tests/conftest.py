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
