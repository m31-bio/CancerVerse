"""Prostate detection-axis models.

Two calculators, kept side by side deliberately. ERSPC RC3 (2012) is the
long-standing European standard; PBCG (2018) is its contemporary successor,
predicts high-grade disease separately, and handles missing predictors, but over-predicts in Black and other groups, so neither supersedes the other.
"""

from .erspc_rc3 import (
    erspc_rc3_predict,
    erspc_rc45_predict,
    linear_predictor_rc3,
    linear_predictor_rc45,
    volume_class,
)
from .pbcg import pbcg_predict, rounded_like_riskcalc
from .pbcg_extended import pbcg_extended_predict, rounded_like_reference

__all__ = [
    "rounded_like_reference",
    "erspc_rc3_predict",
    "erspc_rc45_predict",
    "linear_predictor_rc3",
    "linear_predictor_rc45",
    "volume_class",
    "pbcg_predict",
    "pbcg_extended_predict",
    "rounded_like_riskcalc",
]
