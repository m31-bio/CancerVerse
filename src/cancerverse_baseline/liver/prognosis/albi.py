"""ALBI grade, albumin-bilirubin liver function (Johnson et al., JCO 2015).

Equation source
---------------
Johnson PJ, Berhane S, Kagebayashi C, et al. "Assessment of Liver Function in
Patients With Hepatocellular Carcinoma: A New Evidence-Based Approach. The ALBI
Grade." J Clin Oncol. 2015;33(6):550-558. doi:10.1200/JCO.2014.57.9151

    ALBI = 0.66 * log10(bilirubin [umol/L]) - 0.085 * albumin [g/L]

    grade 1: ALBI <= -2.60
    grade 2: -2.60 < ALBI <= -1.39
    grade 3: ALBI > -1.39

ALBI replaces Child-Pugh's subjective items (ascites, encephalopathy) with two
objective labs, so unlike Child-Pugh it is fully reproducible from numbers alone.

Coefficient correction, 2026-08-05
----------------------------------
This module shipped `-0.0852` for the albumin coefficient. That was WRONG. It
came from a search-result summary rather than the paper, in violation of this
project's own rule that a coefficient enters code only from a source actually
read. The primary text (PMC4322258) prints:

    "linear predictor = (log10 bilirubin x 0.66) + (albumin x -0.085)"

Three independent sources agree on -0.085: the primary paper, MDCalc's
published formula, and the aMAP paper which embeds ALBI as a term. The error
shifted scores by roughly +0.006 to +0.009, small, but enough to flip a grade
for anyone sitting near the -2.60 or -1.39 boundary.
"""

from __future__ import annotations

import math

AXIS = "prognosis"
MODEL_ID = "albi"

BILIRUBIN_COEF = 0.66
ALBUMIN_COEF = -0.085
GRADE_1_MAX = -2.60
GRADE_2_MAX = -1.39

# 1 mg/dL bilirubin = 17.1 umol/L; 1 g/dL albumin = 10 g/L.
BILIRUBIN_MG_DL_TO_UMOL_L = 17.1
ALBUMIN_G_DL_TO_G_L = 10.0

MODEL_CITATION = (
    "Johnson PJ et al. J Clin Oncol. 2015;33(6):550-558. "
    "doi:10.1200/JCO.2014.57.9151 (ALBI grade)."
)


def albi_score(*, bilirubin_umol_l: float, albumin_g_l: float) -> float:
    """Continuous ALBI score. Inputs are SI units."""
    if bilirubin_umol_l <= 0:
        raise ValueError(f"bilirubin must be > 0 umol/L, got {bilirubin_umol_l}")
    if albumin_g_l <= 0:
        raise ValueError(f"albumin must be > 0 g/L, got {albumin_g_l}")
    return BILIRUBIN_COEF * math.log10(bilirubin_umol_l) + ALBUMIN_COEF * albumin_g_l


def albi_grade(score: float) -> int:
    """Map a continuous ALBI score to grade 1-3."""
    if score <= GRADE_1_MAX:
        return 1
    if score <= GRADE_2_MAX:
        return 2
    return 3


def albi_predict(
    *,
    bilirubin_umol_l: float | None = None,
    albumin_g_l: float | None = None,
    bilirubin_mg_dl: float | None = None,
    albumin_g_dl: float | None = None,
) -> dict:
    """
    ALBI score and grade. Accepts SI (umol/L, g/L) or US (mg/dL, g/dL) units.

    Notes
    -----
    ALBI grades liver function, not tumour burden, it is a prognostic
    stratifier used alongside staging (BCLC), not a survival probability.
    """
    if bilirubin_umol_l is None:
        if bilirubin_mg_dl is None:
            raise ValueError("provide bilirubin_umol_l or bilirubin_mg_dl")
        bilirubin_umol_l = bilirubin_mg_dl * BILIRUBIN_MG_DL_TO_UMOL_L
    elif bilirubin_mg_dl is not None:
        raise ValueError("provide bilirubin in one unit only")

    if albumin_g_l is None:
        if albumin_g_dl is None:
            raise ValueError("provide albumin_g_l or albumin_g_dl")
        albumin_g_l = albumin_g_dl * ALBUMIN_G_DL_TO_G_L
    elif albumin_g_dl is not None:
        raise ValueError("provide albumin in one unit only")

    score = albi_score(bilirubin_umol_l=bilirubin_umol_l, albumin_g_l=albumin_g_l)
    grade = albi_grade(score)
    return {
        "score": score,
        "grade": grade,
        "risk": None,  # ALBI is a graded stratifier, not a probability
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "liver",
        "bilirubin_umol_l": bilirubin_umol_l,
        "albumin_g_l": albumin_g_l,
        "citation": MODEL_CITATION,
        "notes": "Grade 1/2/3 at -2.60 and -1.39; objective replacement for Child-Pugh",
    }
