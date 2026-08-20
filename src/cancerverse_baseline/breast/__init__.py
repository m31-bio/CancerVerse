"""Breast cancer classical baselines (detection / response / prognosis)."""

from .detection import bcrat_predict
from .prognosis import predict_breast

__all__ = ["bcrat_predict", "predict_breast"]
