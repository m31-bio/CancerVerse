"""Breast response-axis models.

PREDICT's treatment-benefit output lives on the prognosis axis module
(`mayo_baseline.breast.prognosis.predict_breast`) because one model produces
both; it is re-exported here so the response cell resolves to real code.
"""

from ..prognosis.predict_breast import predict_breast

__all__ = ["predict_breast"]
