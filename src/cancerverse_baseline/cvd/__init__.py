"""Cardiovascular disease classical baselines."""

from .detection import (
    CoefficientsNotAvailable,
    prevent_predict,
    prevent_predict_all,
    score2_predict,
)
from .prognosis import cha2ds2_vasc_predict

__all__ = [
    "CoefficientsNotAvailable",
    "cha2ds2_vasc_predict",
    "prevent_predict",
    "prevent_predict_all",
    "score2_predict",
]
