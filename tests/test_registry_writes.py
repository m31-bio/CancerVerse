"""The registry may not be replaced by something worse than what is there.

`registry/models.yaml` is the single source of truth: 81 models, ~420 KB, read
by every renderer, every test and both audits. Twelve scripts mutate it, and
until 2026-08-18 every one of them ended the same way --

    p.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=100))

which is not atomic (a reader in the truncate-then-write window gets a
fragment) and cannot fail safely (whatever the script computed is what lands).
The registry has been corrupted mid-write twice in this project, and both times
the recovery depended on someone having made a backup first.

`cancerverse_baseline.registry.save` parses and counts the new document *before* it
replaces anything. These tests hold it to that.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from cancerverse_baseline.registry.load import load_models
from cancerverse_baseline.registry.save import (
    RegistryWriteRefused,
    dump_models,
    save_models,
    save_models_text,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def registry_copy(tmp_path: Path) -> Path:
    p = tmp_path / "models.yaml"
    p.write_text(dump_models(load_models()), encoding="utf-8")
    return p


def test_the_serialisation_is_byte_identical_to_what_the_scripts_produced():
    """The point of the change is safety, not reformatting 420 KB.

    `sort_keys=False`, `allow_unicode=True` and `width=100` are load-bearing:
    they keep each entry in the order a human wrote it, keep the en dashes and
    Greek in the formulas readable rather than escaped, and fix where long
    prose wraps. Drop any one and every future diff is noise.
    """
    doc = yaml.safe_load((ROOT / "registry" / "models.yaml").read_text(encoding="utf-8"))
    expected = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100)
    assert dump_models(doc["models"]) == expected


def test_a_write_that_would_drop_models_is_refused(registry_copy: Path):
    before = registry_copy.read_text(encoding="utf-8")
    models = load_models()
    with pytest.raises(RegistryWriteRefused) as exc:
        save_models(models[:5], registry_copy)
    assert "drop" in str(exc.value)
    assert registry_copy.read_text(encoding="utf-8") == before, "the old file was damaged"


def test_a_deliberate_deletion_is_still_possible(registry_copy: Path):
    """Refusing must be a speed bump, not a wall, deletions are legitimate."""
    save_models(load_models()[:5], registry_copy, allow_shrink=True)
    assert len(yaml.safe_load(registry_copy.read_text(encoding="utf-8"))["models"]) == 5


def test_unparseable_yaml_is_refused_before_it_lands(registry_copy: Path):
    before = registry_copy.read_text(encoding="utf-8")
    with pytest.raises(RegistryWriteRefused) as exc:
        save_models_text("models: [ unclosed\n", registry_copy)
    assert "not valid YAML" in str(exc.value)
    assert registry_copy.read_text(encoding="utf-8") == before


def test_a_document_without_a_models_key_is_refused(registry_copy: Path):
    with pytest.raises(RegistryWriteRefused, match="no top-level `models:` key"):
        save_models_text("diseases: []\n", registry_copy)


def test_duplicate_and_missing_ids_are_refused(registry_copy: Path):
    models = load_models()
    with pytest.raises(RegistryWriteRefused, match="duplicate ids"):
        save_models(models + [dict(models[0])], registry_copy)

    anonymous = [dict(m) for m in models]
    anonymous[3].pop("id")
    with pytest.raises(RegistryWriteRefused, match="have no `id`"):
        save_models(anonymous, registry_copy)


def test_a_full_round_trip_leaves_the_registry_unchanged(registry_copy: Path):
    before = registry_copy.read_text(encoding="utf-8")
    save_models(yaml.safe_load(before)["models"], registry_copy)
    assert registry_copy.read_text(encoding="utf-8") == before


def test_no_script_writes_the_registry_the_unsafe_way():
    """The guard that stops this returning one new script at a time.

    It was never a decision to write the registry unsafely, `write_text` was
    simply the obvious call, made independently twelve times.
    """
    pattern = re.compile(r"\.write_text\(\s*$|\.write_text\(\s*yaml\.(safe_)?dump")
    offenders = []
    for script in sorted((ROOT / "scripts").glob("*.py")):
        text = script.read_text()
        if "registry" not in text or "models.yaml" not in text:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line) and not line.lstrip().startswith("#"):
                offenders.append(f"{script.name}:{i}: {line.strip()[:90]}")
    assert not offenders, (
        "these scripts write the registry without the pre-write checks; use "
        "cancerverse_baseline.registry.save.save_models instead:\n  " + "\n  ".join(offenders)
    )
