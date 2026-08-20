"""Shared helpers for logistic risk models."""

from __future__ import annotations

import math
from collections.abc import Iterable


def logit_risk(lp: float) -> float:
    """Convert linear predictor to probability via logistic function."""
    # numerically stable
    if lp >= 0:
        z = math.exp(-lp)
        return 1.0 / (1.0 + z)
    z = math.exp(lp)
    return z / (1.0 + z)


def log2(x: float) -> float:
    if x <= 0:
        raise ValueError(f"log2 requires positive input, got {x}")
    return math.log(x, 2)


def require_keys(data: dict, keys: Iterable[str]) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise KeyError(f"Missing required features: {missing}")
