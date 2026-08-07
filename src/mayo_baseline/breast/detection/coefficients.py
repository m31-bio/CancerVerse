"""Published BCRAT (Gail model) coefficient and hazard tables.

Source
------
NCI DCEG `BCRA` R package, version 2.1.2 — the reference implementation of
the algorithm behind the public NCI Breast Cancer Risk Assessment Tool
(https://bcrisktool.cancer.gov/). Every number below is transcribed from:

  https://rdrr.io/cran/BCRA/src/R/relative.risk.R
  https://rdrr.io/cran/BCRA/src/R/absolute.risk.R
  https://rdrr.io/cran/BCRA/src/R/recode.check.R

retrieved 2026-08-05. The linear-predictor formula printed in
``relative.risk.R`` is:

    LP1 = NB*Beta1 + AM*Beta2 + AF*Beta3 + NR*Beta4 + AF*NR*Beta6 + log(R_Hyp)
    RR_Star1 = exp(LP1)                      # attained age < 50
    RR_Star2 = exp(LP1 + NB*Beta5)           # attained age >= 50

and ``absolute.risk.R`` combines it with the baseline hazards as
``lambda_j = lambda1[band]*(1-AR)*RR_Star[j] + lambda2[band]`` before
integrating one year at a time — see ``bcrat.py``.

Underlying development papers
------------------------------
Gail MH, Brinton LA, Byar DP, et al. Projecting individualized probabilities
of developing breast cancer for white females who are being examined
annually. J Natl Cancer Inst. 1989;81(24):1879-1886.

Costantino JP, Gail MH, Pee D, et al. Validation studies for models
projecting the risk of invasive and total breast cancer incidence.
J Natl Cancer Inst. 1999;91(18):1541-1548.

Race/ethnicity-specific recalibrations bundled into BCRAT: Gail MH et al.
JNCI 2007;99(23):1782-1792 (African-American, CARE); Matsuno RK et al.
JNCI 2011;103(12):951-961 (Asian-American, AABCS); Banegas MP et al. Breast
Cancer Res Treat 2017;164(2):391-401 (Hispanic, SFBCS).
"""

# Log relative-risk coefficients, in the order
# (NB, AM, AF, NR, NB x age>=50 interaction, AF x NR interaction).
BETA = {
    "white": (0.5292641686, 0.0940103059, 0.2186262218, 0.9583027845,
               -0.2880424830, -0.1908113865),
    "black": (0.1822121131, 0.2672530336, 0.0, 0.4757242578,
               -0.1119411682, 0.0),                       # AF dropped (CARE)
    "hispanic_us_born": (0.0970783641, 0.0, 0.2318368334, 0.1666854414,
                          0.0, 0.0),                       # AM dropped (SFBCS)
    "hispanic_foreign_born": (0.4798624017, 0.2593922322, 0.4669246218,
                               0.9076679727, 0.0, 0.0),
    "other": (0.5292641686, 0.0940103059, 0.2186262218, 0.9583027845,
              -0.2880424830, -0.1908113865),               # uses the white model
    "asian": (0.55263612260619, 0.07499257592975, 0.27638268294593,
              0.79185633720481, 0.0, 0.0),
}

# 1 - attributable risk, as (attained age < 50, attained age >= 50).
ONE_MINUS_AR = {
    "white": (0.5788413, 0.5788413),
    "black": (0.72949880, 0.74397137),
    "hispanic_us_born": (0.749294788397, 0.778215491668),
    "hispanic_foreign_born": (0.428864989813, 0.450352338746),
    "other": (0.5788413, 0.5788413),
    "asian": (0.47519806426735, 0.50316401683903),
}

# Composite invasive-breast-cancer incidence hazard lambda_1, one entry per
# five-year attained-age band 20-24, 25-29, ..., 85-89 (14 bands).
LAMBDA1 = {
    "white": (0.00001000, 0.00007600, 0.00026600, 0.00066100, 0.00126500,
              0.00186600, 0.00221100, 0.00272100, 0.00334800, 0.00392300,
              0.00417800, 0.00443900, 0.00442100, 0.00410900),          # SEER white 1983-87
    "black": (0.00002696, 0.00011295, 0.00031094, 0.00067639, 0.00119444,
              0.00187394, 0.00241504, 0.00291112, 0.00310127, 0.00366560,
              0.00393132, 0.00408951, 0.00396793, 0.00363712),          # SEER black 1994-98
    "hispanic_us_born": (0.0000166, 0.0000741, 0.0002740, 0.0006099,
                          0.0012225, 0.0019027, 0.0023142, 0.0028357,
                          0.0031144, 0.0030794, 0.0033344, 0.0035082,
                          0.0025308, 0.0020414),                        # SEER CA Hispanic 1995-2004
    "hispanic_foreign_born": (0.0000102, 0.0000531, 0.0001578, 0.0003602,
                               0.0007617, 0.0011599, 0.0014111, 0.0017245,
                               0.0020619, 0.0023603, 0.0025575, 0.0028227,
                               0.0028295, 0.0025868),                    # SEER CA Hispanic, foreign born
    "other": (0.00001000, 0.00007600, 0.00026600, 0.00066100, 0.00126500,
              0.00186600, 0.00221100, 0.00272100, 0.00334800, 0.00392300,
              0.00417800, 0.00443900, 0.00442100, 0.00410900),          # SEER white 1983-87
    "asian": (0.000004059636, 0.000045944465, 0.000188279352,
              0.000492930493, 0.000913603501, 0.001471537353,
              0.001421275482, 0.001970946494, 0.001674745804,
              0.001821581075, 0.001834477198, 0.001919911972,
              0.002233371071, 0.002247315779),                         # SEER18 Chinese 1998-02, used as the
                                                                          # shared Asian-subgroup proxy rate
}

# Competing (all-cause) mortality hazard lambda_2, same 14 bands.
LAMBDA2 = {
    "white": (0.00049300, 0.00053100, 0.00062500, 0.00082500, 0.00130700,
               0.00218100, 0.00365500, 0.00585200, 0.00943900, 0.01502800,
               0.02383900, 0.03883200, 0.06682800, 0.14490800),         # NCHS white 1985-87
    "black": (0.00074354, 0.00101698, 0.00145937, 0.00215933, 0.00315077,
               0.00448779, 0.00632281, 0.00963037, 0.01471818, 0.02116304,
               0.03266035, 0.04564087, 0.06835185, 0.13271262),         # NCHS black 1996-00
    "hispanic_us_born": (0.0003561, 0.0004038, 0.0005281, 0.0008875,
                          0.0013987, 0.0020769, 0.0030912, 0.0046960,
                          0.0076050, 0.0120555, 0.0193805, 0.0288386,
                          0.0429634, 0.0740349),                        # SEER CA Hispanic 1995-2004
    "hispanic_foreign_born": (0.0003129, 0.0002908, 0.0003515, 0.0004943,
                               0.0007807, 0.0012840, 0.0020325, 0.0034533,
                               0.0058674, 0.0096888, 0.0154429, 0.0254675,
                               0.0448037, 0.1125678),
    "other": (0.00049300, 0.00053100, 0.00062500, 0.00082500, 0.00130700,
               0.00218100, 0.00365500, 0.00585200, 0.00943900, 0.01502800,
               0.02383900, 0.03883200, 0.06682800, 0.14490800),
    "asian": (0.000210649076, 0.000192644865, 0.000244435215,
              0.000317895949, 0.000473261994, 0.000800271380,
              0.001217480226, 0.002099836508, 0.003436889186,
              0.006097405623, 0.010664526765, 0.020148678452,
              0.037990796590, 0.098333900733),                        # NCHS mortality Chinese 1998-02
}

# "Average woman of the same age" comparator BCRAT displays alongside the
# individual estimate: SEER/NCHS white 1992-96 rates, RR fixed at 1.
AVG_LAMBDA1_WHITE = (0.00001220, 0.00007410, 0.00022970, 0.00056490,
                     0.00116450, 0.00195250, 0.00261540, 0.00302790,
                     0.00367570, 0.00420290, 0.00473080, 0.00494250,
                     0.00479760, 0.00401060)
AVG_LAMBDA2_WHITE = (0.00044120, 0.00052540, 0.00067460, 0.00090920,
                     0.00125340, 0.00195700, 0.00329840, 0.00546220,
                     0.00910350, 0.01418540, 0.02259350, 0.03611460,
                     0.06136260, 0.14206630)

# Relative-risk multiplier for the histology of a benign biopsy.
R_HYPERPLASIA = {"no": 0.93, "yes": 1.82, "unknown": 1.00}

RACE_GROUPS = ("white", "black", "hispanic_us_born", "hispanic_foreign_born",
               "other", "asian")
_HISPANIC = ("hispanic_us_born", "hispanic_foreign_born")

AGE_SWITCH = 50.0
AGE_MIN, AGE_MAX = 20.0, 90.0

# NSABP P-1/STAR trial eligibility and USPSTF/NCCN chemoprevention discussion
# threshold: 5-year invasive breast cancer risk >= 1.66%.
CHEMOPREVENTION_THRESHOLD_5Y = 0.0166

UNKNOWN = 99.0
NULLIPAROUS = 98.0

MODEL_CITATION = (
    "Gail MH et al. J Natl Cancer Inst. 1989;81(24):1879-1886 (BCRAT / Gail "
    "model); NCI DCEG BCRA R package v2.1.2 (relative.risk.R, absolute.risk.R)."
)
