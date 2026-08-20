"""BCSC breast density model, the 2008 algorithm, complete and self-consistent.

Source
------
Tice JA, Cummings SR, Smith-Bindman R, Ichikawa L, Barlow WE, Kerlikowske K.
Using Clinical Factors and Mammographic Breast Density to Estimate Breast
Cancer Risk: Development and Validation of a New Predictive Model. Ann
Intern Med. 2008;148(5):337-347. PMID 18316752, PMC2674327.

Transcribed 2026-08-17 from the article, "Appendix Figure.
The Breast Cancer Surveillance Consortium breast density model algorithm"
(the NIH Public Access manuscript's Page 9-10), plus its two tables of race-
and age-specific adjustment factors and its two prose-stated risk-factor
multipliers.

Every table here comes from that single Appendix Figure and is meant to be
used together, do NOT mix these baseline-incidence/mortality coefficients
with the 2015 update's (see `bcsc_v2_bbd_extension_coefficients.py`), which
were fitted on different SEER years (2000-2010 vs this paper's 1998-2002)
against a different, more granular hazard-ratio model. They happen to look
similar but are not interchangeable.

This is what the BCSC's own site (tools.bcsc-scc.ucdavis.edu/BC5yearRisk_V2)
calls "version 1.0" of its invasive-breast-cancer risk calculator. The
registry id `bcsc_v2` is therefore a misnomer, kept because it is wired into
the module path, the entrypoint, the test module and the parameter rows. The
site's own `intro.htm` names version 2.0 as the 2015 benign-breast-disease
refinement (see `bcsc_v2_bbd_extension_coefficients.py` for what that
refinement still needs), five-year AND ten-year, neither of
which this module has. `intro.htm` cites both this 2008 paper and the 2015
one as its references because the deployed v2.0 calculator is built from
both; this module implements only the 2008 half.

Model shape
-----------
Given a starting age `a`, race/ethnicity `r`, BI-RADS density category, and
(optionally) family history and personal breast-biopsy history:

  1. Compute the annual invasive-incidence I(x, r) and non-breast-cancer
     mortality D(x, r) for the five years x = a .. a+4 (both third/exponential
     forms fitted to SEER/Vital Statistics, in percent, see the unit note
     below).
  2. Run the recursion for the proportion of women still at risk, P(x, r),
     and sum I(x, r) * P(x, r) over the five years to get a race-specific
     average 5-year risk, unconditioned on density.
  3. Standardize that average down to what a BI-RADS-2 (scattered
     fibroglandular densities) woman of the same age and race would have,
     using AGE_RACE_DENSITY_ADJUSTMENT.
  4. Multiply by the density-category relative hazard (DENSITY_RELATIVE_HAZARD),
     which differs before/after age 65.
  5. If known, multiply by the family-history and breast-biopsy multipliers.
     If unknown, the paper's own rule is to skip that multiplication (factor
     of 1), not to impute an average.

Unit note (read this before touching the arithmetic)
------------------------------------------------------
The paper's prose labels I(x, r) and D(x, r) as "per 100 000" women, but the
polynomial as printed evaluates to numbers of order 0.1-1 at the ages this
model is used for (e.g. I(50, white) = 0.224 from the coefficients below).
That is two orders of magnitude below any real breast-cancer incidence rate
if taken as literally per 100,000 (0.224/100,000 women/year is not a
plausible rate), but exactly the right order of magnitude as a *percent*
(0.224% = 224 per 100,000, which matches published SEER rates for a
50-year-old White woman). The nearly-identical polynomial in the 2015 update
of this same model (Tice 2015, Appendix Table A3) is explicitly labeled "per
100 women" for numerically similar coefficients. We treat this paper's
label as an error carried from an earlier draft and use "per 100" (i.e.
divide by 100 to get a probability) throughout, exactly as the 2015 paper's
own explicit formula does. This reading was checked against the paper's own
Table 5 worked examples in `bcsc.py`'s tests and reproduces them to within
the expected error from Table 5 being a race-mixed population average.
"""

# Third-order polynomial coefficients for annual invasive-incidence, in
# percent, I(X, r) = a*X**3 + b*X**2 + c*X + d. Fitted to 1998-2002 SEER
# rates by race/ethnicity. American Indian/Alaskan Native was excluded by
# the paper itself for inconsistent SEER rates.
BASELINE_INCIDENCE = {
    "white": (-0.000007231, 0.001129372, -0.044330046, 0.520553050),
    "black": (-0.000004654, 0.000689680, -0.023186530, 0.218993144),
    "asian": (-0.000003314, 0.000421460, -0.009405533, 0.004344518),
    "hispanic": (-0.000003928, 0.000585266, -0.020678768, 0.210555571),
}

# Exponential fit for annual non-breast-cancer mortality, in percent,
# D(X, r) = n * exp(m * X). Fitted to 2002 US Vital Statistics (total death
# rate minus breast-cancer death) by race/ethnicity.
MORTALITY = {
    "white": (0.003695745, 0.08844949),
    "black": (0.011685888, 0.077263338),
    "asian": (0.01333534, 0.09479173),
    "hispanic": (0.002435331, 0.091388373),
}

RACE_GROUPS = tuple(BASELINE_INCIDENCE)

# Relative hazard of each BI-RADS density category, relative to category 2
# (scattered fibroglandular densities, the reference). Two separate sets:
# strength of the density association was significantly greater below 65.
DENSITY_RELATIVE_HAZARD = {
    "under_65": {1: 0.48107, 2: 1.00, 3: 1.5506, 4: 2.0119},
    "65_or_over": {1: 0.65706, 2: 1.00, 3: 1.3881, 4: 1.4499},
}

DENSITY_AGE_CUTOFF = 65.0

# Age- and race/ethnicity-specific factors that standardize the
# race-specific average incidence (which implicitly averages over all
# densities) down to what the BI-RADS-2 reference group's incidence would
# be, given each age/race stratum's own distribution of density.
AGE_RACE_DENSITY_ADJUSTMENT = {
    "white": {"35-44": 0.7182, "45-54": 0.7565, "55-64": 0.8246, "65-74": 0.9069, "75+": 0.9134},
    "black": {"35-44": 0.7470, "45-54": 0.7810, "55-64": 0.8486, "65-74": 0.9201, "75+": 0.9334},
    "asian": {"35-44": 0.6341, "45-54": 0.6742, "55-64": 0.7530, "65-74": 0.8866, "75+": 0.9127},
    "hispanic": {"35-44": 0.7535, "45-54": 0.7950, "55-64": 0.8780, "65-74": 0.9615, "75+": 0.9865},
}

# Simple multiplicative adjustments, applied only if the factor is known.
# "If family history and breast biopsy status are unknown, no further
# calculations are done", i.e. the multiplier is 1, not an imputed average.
FAMILY_HISTORY_MULTIPLIER = {False: 0.938, True: 1.454}
BIOPSY_HISTORY_MULTIPLIER = {False: 0.906, True: 1.495}

MODEL_CITATION = (
    "Tice JA, Cummings SR, Smith-Bindman R, Ichikawa L, Barlow WE, "
    "Kerlikowske K. Using Clinical Factors and Mammographic Breast Density "
    "to Estimate Breast Cancer Risk: Development and Validation of a New "
    "Predictive Model. Ann Intern Med. 2008;148(5):337-347."
)


def age_band(age: float) -> str:
    """The 10-year band `AGE_RACE_DENSITY_ADJUSTMENT` is keyed by."""
    if age < 45:
        return "35-44"
    if age < 55:
        return "45-54"
    if age < 65:
        return "55-64"
    if age < 75:
        return "65-74"
    return "75+"
