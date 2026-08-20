"""Breast response-axis models.

PREDICT's treatment-benefit output lives on the prognosis axis module
(`cancerverse_baseline.breast.prognosis.predict`) because one model produces
both; it is re-exported here so the response cell resolves to real code.
"""

from ..prognosis.predict import predict_breast

__all__ = ["predict_breast"]
