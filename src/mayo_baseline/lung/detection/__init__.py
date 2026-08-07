"""Lung detection-axis models."""

from .plcom2012 import linear_predictor, plcom2012_predict, smoking_intensity_term

__all__ = ["linear_predictor", "plcom2012_predict", "smoking_intensity_term"]
