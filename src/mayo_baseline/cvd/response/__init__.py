"""Cardiovascular response-axis models.

One entry, and it is unlike the rest of this library: `cvd_statin_benefit` is a
COMPOSITION of a published trial effect with a baseline risk from a separate
model, not a reimplemented published equation. Read its module docstring before
using it.
"""

from .statin_benefit import cvd_statin_benefit_predict, ldl_reduction_mmol

__all__ = ["cvd_statin_benefit_predict", "ldl_reduction_mmol"]
