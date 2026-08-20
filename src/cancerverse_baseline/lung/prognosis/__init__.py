"""Lung prognosis-axis models.

LIPI was developed and validated as a prognostic index as well as a predictor
of immunotherapy benefit, so the same function serves both cells. It lives in
`cancerverse_baseline.lung.response.lipi` and is re-exported here rather than
duplicated — see [[LIPI]].
"""

from ..response.lipi import lipi_predict

__all__ = ["lipi_predict"]
