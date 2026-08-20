"""Breast cancer classical baselines (detection / response / prognosis)."""

from .detection import bcrat_predict, bcsc_v2_predict
from .prognosis import predict_breast

# bcsc_v2_predict is the detection flagship and was missing here while
# bcrat_predict, the model it superseded, was exported, so
# `from cancerverse_baseline.breast import *` handed out the alternative and withheld
# the default. Both are exported: BCRAT stays callable as
# the parity-checked comparator.
__all__ = ["bcrat_predict", "bcsc_v2_predict", "predict_breast"]
