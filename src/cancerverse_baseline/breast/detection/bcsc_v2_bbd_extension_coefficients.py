"""Partial coefficients for the 2015 benign-breast-disease (BBD) refinement
of the BCSC v2 model (Breast Cancer Surveillance Consortium, "BCSC BBD").

NOT YET A WORKING MODEL, and NOT what ``bcsc_v2_predict`` uses (that module
implements the complete 2008 base algorithm instead, see
``bcsc_v2_coefficients.py``). This file holds only the pieces of the 2015
refinement that are printed in the open-access-eligible paper itself, kept
here as a documented future enhancement: replacing the 2008 base algorithm's
binary "ever had a biopsy" input with a full 5-level benign-breast-disease
classification (nonproliferative / proliferative without atypia /
proliferative with atypia / LCIS / none), plus a 10-year horizon. It must
not be wired into ``cancerverse_baseline.predict`` until the missing piece below is
filled in.

Source
------
Tice JA, Miglioretti DL, Li CS, Vachon CM, Gard CC, Kerlikowske K. Breast
Density and Benign Breast Disease: Risk Assessment to Identify Women at High
Risk of Breast Cancer. J Clin Oncol. 2015;33(28):3137-3143.
doi:10.1200/JCO.2015.60.8869. PMID 26282663, PMC4582144.

Transcribed 2026-08-14 from the article (Appendix, online
only). Every number below is copied character-for-character from:

  Appendix Table A3, baseline invasive-breast-cancer incidence, third-order
                        polynomial in age, one (alpha, beta, gamma, delta)
                        tuple per race/ethnicity
  Appendix Table A4, baseline DCIS incidence, same polynomial form, used
                        for the competing-risk adjustment
  Appendix Table A5, all-cause (minus breast-cancer) mortality, exponential
                        fit M(X) = eta * exp(theta * X)

The Appendix gives the closed forms these tables feed:

  I(X, r)   = alpha_r*X**3 + beta_r*X**2 + gamma_r*X + delta_r   (Table A3)
  D(X, r)   = alpha_r*X**3 + beta_r*X**2 + gamma_r*X + delta_r   (Table A4)
  M(X, r)   = eta_r * exp(theta_r * X)                            (Table A5)

What is still missing
----------------------
The model multiplies I(X, r) and D(X, r) by a standardized hazard ratio
HR(X, r, Z) that folds in BI-RADS density, family history and benign breast
disease (Z), estimated from a Cox model with age-by-risk-factor interactions.
The paper states this explicitly (Appendix, paragraph before Table A1):

  "The standardized hazard ratios are contained in SAS format (SAS
  Institute, Cary, NC) files provided with the public-use macro, which is
  available at https://tools.bcsc-scc.org/BC5yearRisk/sourcecode.htm."

Table 2 in the main text gives HR point estimates (with 95% CI) at four
illustrative ages only, 40, 50, 60 and 70, for race/ethnicity, family
history, BI-RADS density and benign breast disease, each with a p-value for
its interaction with age and with age-squared. That confirms the true
function is continuous and quadratic in age, but four rounded point
estimates cannot be inverted into exact coefficients. THOSE FOUR POINTS ARE
NOT TRANSCRIBED HERE AS CODE ON PURPOSE, to avoid anyone mistaking them for
the model. The full HR(X, r, Z) table only exists in the SAS macro, which is
behind the same password-gated request as the v3 (BCSC 2024) source,
tracked in registry/models.yaml, id `bcsc_v2`, field `future_enhancement`.

Until that arrives, this module cannot produce a risk estimate: I(X, r) and
D(X, r) are baseline rates for a woman at *average* risk for her age and
race/ethnicity, and average-risk is exactly what HR(X, r, Z) adjusts away
from.
"""

# Third-order polynomial coefficients for baseline invasive breast cancer
# incidence per 100 women, I(X, r) = a*X**3 + b*X**2 + c*X + d.
# Appendix Table A3.
BASELINE_INVASIVE_INCIDENCE = {
    "white_non_hispanic": (-0.000007162, 0.001111136, -0.043528999, 0.514780021),
    "black_non_hispanic": (-0.000004332, 0.000644475, -0.021243209, 0.195808387),
    "asian": (-0.000003002, 0.000372751, -0.007182055, -0.025628846),
    "american_indian": (-0.000005880, 0.000861287, -0.032530311, 0.373493536),
    "hispanic": (-0.000004211, 0.000628530, -0.022484578, 0.234323344),
}

# Same polynomial form, for baseline DCIS incidence per 100 women, used only
# to remove DCIS-diagnosed women from the at-risk population year over year.
# Appendix Table A4.
BASELINE_DCIS_INCIDENCE = {
    "white_non_hispanic": (-0.000002094, 0.000284086, -0.009292718, 0.080659188),
    "black_non_hispanic": (-0.000002706, 0.000403385, -0.016548963, 0.207686538),
    "asian": (-0.000001496, 0.000185804, -0.004747568, 0.016457265),
    "american_indian": (0.000000191, -0.000049665, 0.004730528, -0.102520406),
    "hispanic": (-0.000001403, 0.000195157, -0.006832187, 0.067237073),
}

# Exponential fit for all-cause (non-breast-cancer) mortality per 100 women,
# M(X, r) = eta * exp(theta * X). Appendix Table A5.
MORTALITY = {
    "white_non_hispanic": (0.004741239, 0.082473361),
    "black_non_hispanic": (0.008976903, 0.077540550),
    "asian": (0.001324086, 0.091167044),
    "american_indian": (0.016491843, 0.067539660),
    "hispanic": (0.002253560, 0.088334802),
}

RACE_GROUPS = tuple(BASELINE_INVASIVE_INCIDENCE)

MODEL_CITATION = (
    "Tice JA, Miglioretti DL, Li CS, Vachon CM, Gard CC, Kerlikowske K. "
    "Breast Density and Benign Breast Disease: Risk Assessment to Identify "
    "Women at High Risk of Breast Cancer. J Clin Oncol. 2015;33(28):3137-3143."
)
