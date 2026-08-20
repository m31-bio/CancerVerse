"""CVD coefficient tables and literature pointers."""

from __future__ import annotations

# --- PREVENT: coefficients live in prevent_coefficients.py ---
PREVENT_REFS = [
    "https://www.ahajournals.org/doi/10.1161/CIRCULATIONAHA.123.067626",
    "https://github.com/martingmayer/preventr",  # MIT canonical impl
    "https://www.nature.com/articles/s41591-026-04437-z",  # validation only
    "https://professional.heart.org/en/guidelines-and-statements/about-prevent-calculator",
]

# --- SCORE2 (Hageman et al. 4 d.p. table) ---
COEFFS = {
    "male": {
        "age": 0.3742,
        "smoking": 0.6012,
        "sbp": 0.2777,
        "diabetes": 0.6457,
        "tchol": 0.1458,
        "hdl": -0.2698,
        "smoking_age": -0.0755,
        "sbp_age": -0.0255,
        "tchol_age": -0.0281,
        "hdl_age": 0.0426,
        "diabetes_age": -0.0983,
        "baseline_survival": 0.9605,
    },
    "female": {
        "age": 0.4648,
        "smoking": 0.7744,
        "sbp": 0.3131,
        "diabetes": 0.8096,
        "tchol": 0.1002,
        "hdl": -0.2606,
        "smoking_age": -0.1088,
        "sbp_age": -0.0277,
        "tchol_age": -0.0226,
        "hdl_age": 0.0613,
        "diabetes_age": -0.1272,
        "baseline_survival": 0.9776,
    },
}

RECALIBRATION = {
    "male": {
        "low": (-0.5699, 0.7476),
        "moderate": (-0.1565, 0.8009),
        "high": (0.3207, 0.9360),
        "very_high": (0.5836, 0.8294),
    },
    "female": {
        "low": (-0.7380, 0.7019),
        "moderate": (-0.3143, 0.7701),
        "high": (0.5710, 0.9369),
        "very_high": (0.9412, 0.8329),
    },
}

MODEL_CITATION = (
    "SCORE2 working group and ESC Cardiovascular Risk Collaboration. "
    "Eur Heart J. 2021;42(25):2439-2454. Coefficients: Hageman et al. comment table (4 d.p.)."
)

REGIONS = ("low", "moderate", "high", "very_high")
