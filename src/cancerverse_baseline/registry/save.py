"""Write the registry back, atomically, and refuse to write a broken one.

The registry is the single source of truth: 81 models, ~420 KB, read by every
renderer, every test and both audits. Eleven scripts mutate it, and every one
of them ended with the same line --

    p.write_text(yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=100))

which has two problems and had them eleven times over.

**It is not atomic.** `write_text` truncates before it writes, so a reader in
that window gets a fragment. See `cancerverse_baseline.reporting.atomic`.

**It cannot fail safely.** Whatever the script computed is what lands. If a
transform dropped half the models, or produced something that no longer parses,
the file is already gone by the time anyone notices. That has happened twice in
this project and both times the fix was to restore from a backup, which only
worked because someone had made one.

So the write goes through here instead, and the document is *parsed and counted
before it replaces anything*. A save that would shrink the registry raises with
the ids it was about to lose. Refusing to write is recoverable; writing a
truncated registry is the state we keep having to recover from.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..reporting.atomic import write_text_atomically
from .load import _registry_dir

__all__ = ["dump_models", "save_models", "save_models_text"]


class RegistryWriteRefused(RuntimeError):
    """Raised instead of replacing the registry with something worse."""


def _models_path(path: Path | None) -> Path:
    return path or (_registry_dir() / "models.yaml")


def dump_models(models: list[dict[str, Any]]) -> str:
    """Serialise exactly as the eleven scripts did, so output is unchanged.

    The three keyword arguments are load-bearing and not stylistic:
    `sort_keys=False` keeps each entry in the order a human wrote it,
    `allow_unicode=True` keeps the en dashes and Greek in the formulas readable
    rather than escaped, and `width=100` sets where long prose fields wrap.
    Changing any of them reflows the whole 420 KB file and turns every future
    diff into noise.
    """
    import yaml

    return yaml.safe_dump(
        {"models": models}, sort_keys=False, allow_unicode=True, width=100
    )


def save_models_text(
    text: str, path: Path | None = None, *, allow_shrink: bool = False
) -> Path:
    """Replace models.yaml with `text`, but only if `text` is a better file.

    For callers that edit the YAML as *lines*, inserting a field under a known
    anchor, say, rather than re-dumping a parsed object. That style is worth
    supporting: a re-dump reflows all 420 KB, so a one-field change becomes an
    unreviewable diff.
    """
    import yaml

    path = _models_path(path)

    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise RegistryWriteRefused(
            f"refusing to write {path.name}: the new text is not valid YAML "
            f"({exc.__class__.__name__}). The file on disk is untouched."
        ) from exc

    if not isinstance(parsed, dict) or "models" not in parsed:
        raise RegistryWriteRefused(
            f"refusing to write {path.name}: the new text parses but has no "
            f"top-level `models:` key."
        )

    new_ids = [m.get("id") for m in parsed["models"]]
    missing_id = [i for i, m in enumerate(parsed["models"]) if not m.get("id")]
    if missing_id:
        raise RegistryWriteRefused(
            f"refusing to write {path.name}: entries at positions {missing_id} "
            f"have no `id`."
        )
    duplicates = sorted({i for i in new_ids if new_ids.count(i) > 1})
    if duplicates:
        raise RegistryWriteRefused(
            f"refusing to write {path.name}: duplicate ids {duplicates}."
        )

    if path.exists() and not allow_shrink:
        old = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        lost = sorted({m.get("id") for m in old.get("models", [])} - set(new_ids))
        if lost:
            raise RegistryWriteRefused(
                f"refusing to write {path.name}: it would drop {len(lost)} "
                f"model(s) -- {lost[:8]}{' ...' if len(lost) > 8 else ''}. "
                f"Pass allow_shrink=True if a deletion is what you meant."
            )

    return write_text_atomically(path, text)


def save_models(
    models: list[dict[str, Any]], path: Path | None = None, *, allow_shrink: bool = False
) -> Path:
    """Re-dump a parsed registry and write it, with the same checks."""
    return save_models_text(dump_models(models), path, allow_shrink=allow_shrink)
