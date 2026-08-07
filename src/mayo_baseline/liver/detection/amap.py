"""aMAP score — 5-year hepatocellular carcinoma risk in chronic hepatitis.

Equation source
---------------
Fan R, Papatheodoridis G, Sun J, et al. "aMAP risk score predicts hepatocellular
carcinoma development in patients with chronic hepatitis." J Hepatol.
2020;73(6):1368-1378. doi:10.1016/j.jhep.2020.07.025

Open access (CC BY-NC-ND). Formula transcribed from the paper's own statement of
it, with units confirmed against its baseline-characteristics table.

    ALBI = 0.66 * log10(bilirubin [umol/L]) - 0.085 * albumin [g/L]

    aMAP = ({ 0.06 * age
            + 0.89 * male
            + 0.48 * ALBI
            - 0.01 * platelets } + 7.4) / 14.77 * 100

    ranges 0-100;  low 0-50,  medium 50-60,  high 60-100

Units, from the paper's Table 1: bilirubin umol/L, albumin g/L, platelets
x10^3/mm^3 (equivalently x10^9/L), age in years.

Note the nesting: aMAP embeds the **ALBI score** (see [[ALBI]], which this repo
implements separately on the liver prognosis axis) as a single term. Both use
-0.085 on albumin, which is what Johnson 2015 actually prints. An earlier draft
of this note claimed the two differed (-0.085 here vs -0.0852 in ALBI) and
framed it as deliberate; that was wrong — the ALBI module had the mistranscribed
value, since corrected. The two are now consistent because the source is.

Performance context: cut-off 50 gave sensitivity 86.5% and NPV 99.5%; cut-off 60
gave high specificity. 5-year HCC incidence in the training cohort was 0.8%
(95% CI 0.3-1.3), 4.2% (2.6-5.7) and 19.9% (12.8-26.5) in the low-, medium- and
high-risk groups.

UNRESOLVED: the published formula disagrees with the custodial calculator
--------------------------------------------------------------------------
CUHK's Medical Data Analytics Centre — an aMAP collaborating site — hosts a
calculator at https://mdac.cuhk.edu.hk/calculators/amap/ . It does NOT
reproduce the formula above.

Probing its endpoint one variable at a time, every slope agrees with the paper
(age ~0.406 pts/yr vs 0.406 published; male ~6.0 vs 6.03; albumin -0.267
pts/(g/L) vs -0.276; platelets -0.0656 vs -0.0677 — all within integer-rounding
noise). But the calculator's output sits **2 to 3 points above** what the
published expression gives:

    age 50, male, bilirubin 15 umol/L, albumin 42 g/L, platelets 200
        published formula -> 53.82        CUHK calculator -> 56
    age 30, male, bilirubin 10, albumin 45, platelets 250
        published formula -> 41.10        CUHK calculator -> 44
    age 65, male, bilirubin 25, albumin 38, platelets 150
        published formula -> 64.88        CUHK calculator -> 68

The formula transcription here was verified by rendering the article page as an
image (the PDF text layer mangles the nested brackets), so this is not a
transcription error on our side. Either the calculator implements a later
refinement, or the published constants carry a typo.

This module implements the PUBLISHED formula, per this project's rule of
reproducing what was actually published. Consequently `parity_status` stays
`not_checked` rather than being forced to agree with the calculator. Resolving it
needs the authors (CUHK contact: Terry Yip).

Two further behaviours of the calculator, recorded so a future parity test does
not trip over them:
  - it rounds the score to an integer BEFORE banding, and treats exactly 60 as
    HIGH. We band on the raw float, so a raw 59.84 is medium here and high
    there.
  - it returns the risk-GROUP incidence, not a per-patient probability. Two
    patients scoring 65 and 72 both come back as 19.9%. That corroborates the
    decision below to return `risk: None` rather than a continuous 5-year risk.

The paper does print a 5-year baseline survival, S0(t) = exp(-H0(t)) = 0.984,
which would permit a continuous risk. We deliberately do NOT ship one: whether
the linear predictor is mean-centred is unresolved from the text, and getting
it wrong is a ~1.4x hazard multiplier. The custodial tool does not expose a
continuous risk either.
"""

from __future__ import annotations

import math

AXIS = "detection"
MODEL_ID = "amap"

AGE_BETA = 0.06
MALE_BETA = 0.89
ALBI_BETA = 0.48
PLATELET_BETA = -0.01

# Rescaling of the linear predictor onto 0-100.
RESCALE_OFFSET = 7.4
RESCALE_DIVISOR = 14.77

# ALBI coefficients as printed in Johnson 2015 and restated by aMAP.
ALBI_BILIRUBIN_BETA = 0.66
ALBI_ALBUMIN_BETA = -0.085

LOW_RISK_MAX = 50.0
MEDIUM_RISK_MAX = 60.0

BILIRUBIN_MG_DL_TO_UMOL_L = 17.1
ALBUMIN_G_DL_TO_G_L = 10.0

MODEL_CITATION = (
    "Fan R, Papatheodoridis G, Sun J, et al. J Hepatol. 2020;73(6):1368-1378. "
    "doi:10.1016/j.jhep.2020.07.025 (aMAP score)."
)


def risk_group(score: float) -> str:
    if score < LOW_RISK_MAX:
        return "low"
    if score < MEDIUM_RISK_MAX:
        return "medium"
    return "high"


def amap_predict(
    *,
    age: float,
    male: bool,
    platelets: float,
    bilirubin_umol_l: float | None = None,
    albumin_g_l: float | None = None,
    bilirubin_mg_dl: float | None = None,
    albumin_g_dl: float | None = None,
) -> dict:
    """
    aMAP score (0-100) and risk group for 5-year HCC development.

    `platelets` is in x10^3/mm^3 (equivalently x10^9/L). Bilirubin and albumin
    accept SI (umol/L, g/L) or US (mg/dL, g/dL) units — supply one form of each.
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

    if age <= 0:
        raise ValueError(f"age must be > 0, got {age}")
    if bilirubin_umol_l <= 0:
        raise ValueError(f"bilirubin must be > 0 umol/L, got {bilirubin_umol_l}")
    if albumin_g_l <= 0:
        raise ValueError(f"albumin must be > 0 g/L, got {albumin_g_l}")
    if platelets <= 0:
        raise ValueError(f"platelets must be > 0, got {platelets}")

    albi = (
        ALBI_BILIRUBIN_BETA * math.log10(bilirubin_umol_l)
        + ALBI_ALBUMIN_BETA * albumin_g_l
    )
    lp = (
        AGE_BETA * age
        + MALE_BETA * (1.0 if male else 0.0)
        + ALBI_BETA * albi
        + PLATELET_BETA * platelets
    )
    score = (lp + RESCALE_OFFSET) / RESCALE_DIVISOR * 100.0

    return {
        "score": score,
        "risk_group": risk_group(score),
        "risk": None,  # a 0-100 stratifier, not a probability
        "linear_predictor": lp,
        "albi_component": albi,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "liver",
        "citation": MODEL_CITATION,
        "notes": "0-100; low <50, medium 50-60, high >=60; embeds the ALBI score",
    }
