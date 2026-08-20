#!/usr/bin/env python3
"""Is the registry parseable? Answer in one line, before anything else runs.

    python scripts/check_registry_syntax.py

A YAML syntax error in registry/models.yaml is this repository's widest single
failure: 28 scripts and every one of the tests read that file, so one stray
colon takes down the build, the renderers and the whole safety net at once.

The failure is also unusually hard to read. pytest parses the registry in
`pytest_configure`, before collection, so there is no test to attach the error
to, it surfaces as a bare INTERNALERROR with a traceback through
yaml/scanner.py, which names neither the registry nor the line. That happened
on 2026-08-18, from a concurrent edit that left an unquoted scalar containing a
second colon.

`check-yaml` in .pre-commit-config.yaml catches this too, and is the right
place for it, but it only runs at `git commit`. This is the version you can run
mid-edit, in a loop, or as the first step of CI.

Exit code 0 if the registry parses, 1 if it does not.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

#: Every YAML file the library will not start without.
REQUIRED = ("registry/models.yaml", "registry/parameters.yaml",
            "collected/MANIFEST.yaml")


def check(rel: str) -> str | None:
    """None if it parses, else a message a human can act on."""
    path = ROOT / rel
    if not path.exists():
        return f"{rel}: missing"
    try:
        yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        if mark is None:
            return f"{rel}: {exc}"
        line = path.read_text(encoding="utf-8").splitlines()[mark.line]
        return (f"{rel}:{mark.line + 1}:{mark.column + 1}: "
                f"{getattr(exc, 'problem', exc)}\n"
                f"    {line.strip()[:100]}\n"
                f"    The usual cause is an unquoted value containing a colon. "
                f"Wrap it in a `>-` block scalar.")
    return None


def main() -> int:
    problems = [msg for rel in REQUIRED if (msg := check(rel))]
    for msg in problems:
        print(msg, file=sys.stderr)
    if problems:
        print(f"\n{len(problems)} file(s) will not parse, nothing that reads "
              f"them can run.", file=sys.stderr)
        return 1
    print(f"ok — {len(REQUIRED)} registry file(s) parse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
