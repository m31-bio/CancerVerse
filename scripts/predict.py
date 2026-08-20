#!/usr/bin/env python3
"""Thin wrapper around the package CLI. No logic lives here.

    python scripts/predict.py predict albi --bilirubin_umol_l 20 --albumin_g_l 40

Prefer the installed entry point once the package is installed:

    uv sync
    uv run cancerverse-baseline predict albi --bilirubin_umol_l 20 --albumin_g_l 40

This file exists so the repository has the conventional `scripts/predict.py`
and so the CLI is reachable from a plain checkout without installing. Every
behaviour it has is `cancerverse_baseline.cli`'s.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cancerverse_baseline.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
