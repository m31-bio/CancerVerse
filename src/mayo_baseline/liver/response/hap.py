"""HAP score — prognosis and TACE candidacy in hepatocellular carcinoma.

Equation source
---------------
Kadalayil L, Benini R, Pallan L, et al. "A simple prognostic scoring system for
patients receiving transarterial embolisation for hepatocellular cancer."
Ann Oncol. 2013;24(10):2565-2570. PMID 23857958.

One point each, verified from the primary paper:

    albumin           < 36 g/L
    bilirubin         > 17 umol/L
    alpha-fetoprotein > 400 ng/mL
    dominant tumour   > 7 cm

    grade  points   median OS (derivation cohort)
    A      0        27.6 months
    B      1        18.5 months
    C      2         9.0 months
    D      >2        3.6 months

Note the grade boundaries: A/B/C are exact point counts, but D is ">2", so
scores of 3 and 4 both fall in D. That asymmetry is the paper's, not ours.

Axis placement
--------------
Registered on `response` because its clinical use is selecting who benefits
from TACE (and, via ART/ABCR, whether to repeat it). It is equally a
prognostic score — the derivation paper frames it as prognosis. Filed under
response because that is the cell it unblocks; see also [[ALBI]] on the
prognosis axis, which grades liver function rather than TACE benefit.

Caveats
-------
The published median survivals are the derivation cohort's (UK patients).
External validation in European and Asian cohorts supported discrimination
but produced different absolute survivals, and prompted the mHAP / mHAP-II /
mHAP-III modifications, which are not implemented here. The albumin threshold
is printed as "<36 g/dl" in some renderings of the abstract; 36 g/dL is not a
physiological albumin concentration and the intended unit is g/L, which is
what this module requires.
"""

from __future__ import annotations

AXIS = "response"
MODEL_ID = "hap"

ALBUMIN_CUTOFF_G_L = 36.0       # < 36 g/L scores 1
BILIRUBIN_CUTOFF_UMOL_L = 17.0  # > 17 umol/L scores 1
AFP_CUTOFF_NG_ML = 400.0        # > 400 ng/mL scores 1
TUMOUR_SIZE_CUTOFF_CM = 7.0     # > 7 cm scores 1

# Unit conversions, for callers working in US units.
BILIRUBIN_MG_DL_TO_UMOL_L = 17.1
ALBUMIN_G_DL_TO_G_L = 10.0

MEDIAN_OS_MONTHS = {"A": 27.6, "B": 18.5, "C": 9.0, "D": 3.6}

MODEL_CITATION = (
    "Kadalayil L et al. Ann Oncol. 2013;24(10):2565-2570 (HAP score). PMID 23857958."
)


def hap_grade(points: int) -> str:
    """Map 0-4 points to HAP grade. Note D is '>2', so it absorbs both 3 and 4."""
    if points == 0:
        return "A"
    if points == 1:
        return "B"
    if points == 2:
        return "C"
    return "D"


def hap_predict(
    *,
    albumin_g_l: float | None = None,
    bilirubin_umol_l: float | None = None,
    afp_ng_ml: float,
    dominant_tumour_size_cm: float,
    albumin_g_dl: float | None = None,
    bilirubin_mg_dl: float | None = None,
) -> dict:
    """
    HAP score and grade for a patient being considered for TACE.

    Accepts SI units (albumin g/L, bilirubin umol/L) or US units
    (albumin g/dL, bilirubin mg/dL) — supply exactly one form of each.
    """
    if albumin_g_l is None:
        if albumin_g_dl is None:
            raise ValueError("provide albumin_g_l or albumin_g_dl")
        albumin_g_l = albumin_g_dl * ALBUMIN_G_DL_TO_G_L
    elif albumin_g_dl is not None:
        raise ValueError("provide albumin in one unit only")

    if bilirubin_umol_l is None:
        if bilirubin_mg_dl is None:
            raise ValueError("provide bilirubin_umol_l or bilirubin_mg_dl")
        bilirubin_umol_l = bilirubin_mg_dl * BILIRUBIN_MG_DL_TO_UMOL_L
    elif bilirubin_mg_dl is not None:
        raise ValueError("provide bilirubin in one unit only")

    for name, value in (
        ("albumin_g_l", albumin_g_l),
        ("bilirubin_umol_l", bilirubin_umol_l),
        ("afp_ng_ml", afp_ng_ml),
        ("dominant_tumour_size_cm", dominant_tumour_size_cm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be > 0, got {value}")

    components = {
        "albumin": 1 if albumin_g_l < ALBUMIN_CUTOFF_G_L else 0,
        "bilirubin": 1 if bilirubin_umol_l > BILIRUBIN_CUTOFF_UMOL_L else 0,
        "afp": 1 if afp_ng_ml > AFP_CUTOFF_NG_ML else 0,
        "tumour_size": 1 if dominant_tumour_size_cm > TUMOUR_SIZE_CUTOFF_CM else 0,
    }
    points = sum(components.values())
    grade = hap_grade(points)
    return {
        "score": points,
        "grade": grade,
        "risk": None,  # point score, not a probability
        "median_os_months": MEDIAN_OS_MONTHS[grade],
        "components": components,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "liver",
        "citation": MODEL_CITATION,
        "notes": "HAP A-D; median OS is the UK derivation cohort's, not transferable",
    }
