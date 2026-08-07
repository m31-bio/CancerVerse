"""Classical clinical baselines: published risk equations, independently verified.

    >>> import mayo_baseline as mb
    >>> mb.predict("albi", bilirubin_umol_l=20.0, albumin_g_l=40.0)["grade"]
    2

`list_models()` enumerates what is available, `model_info()` says what each one
needs and what it was built for, and `predict_many()` runs several on one
patient. See `mayo_baseline.api` for the reasoning, including why there is no
"run everything" convenience.

Not a medical device. Not for clinical use.
"""

from .api import ModelInfo, list_models, model_info, predict, predict_many

__version__ = "0.2.0"
__all__ = ["predict", "predict_many", "list_models", "model_info", "ModelInfo"]
