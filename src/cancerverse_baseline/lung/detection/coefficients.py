"""Published PLCOm2012 coefficient table.

Source: Tammemägi MC et al. "Selection Criteria for Lung-Cancer Screening."
N Engl J Med. 2013;368(8):728-736, Table 2 (author manuscript, PMC3929969).

Table 2 footnote defines the coding exactly:
  - categorical terms enter as beta x {0,1}
  - continuous terms enter as beta x (value - centering value)
  - smoking intensity enters as beta x ((cigarettes_per_day / 10) ** -1 - 0.4021541613)
  - risk = exp(logit) / (1 + exp(logit)), a 6-year probability
"""

INTERCEPT = -4.532506

AGE = 0.0778868
AGE_CENTER = 62.0

# Self-reported race/ethnic group; White is the reference group.
# American Indian / Alaskan Native is printed as exactly 0 in Table 2.
RACE = {
    "white": 0.0,
    "black": 0.3944778,
    "hispanic": -0.7434744,
    "asian": -0.466585,
    "american_indian_alaskan_native": 0.0,
    "native_hawaiian_pacific_islander": 1.027152,
}

# Six ordinal levels: 1 = < high-school graduate, 2 = high-school graduate,
# 3 = some training after high school, 4 = some college, 5 = college graduate,
# 6 = postgraduate or professional degree.
EDUCATION = -0.0812744
EDUCATION_CENTER = 4.0
EDUCATION_LEVELS = (1, 2, 3, 4, 5, 6)

BMI = -0.0274194
BMI_CENTER = 27.0

COPD = 0.3553063
PERSONAL_CANCER_HISTORY = 0.4589971
FAMILY_HISTORY_LUNG_CANCER = 0.587185

# Current smoker vs. former smoker (former is the reference).
SMOKING_STATUS_CURRENT = 0.2597431

# Non-linear transform of average cigarettes per day.
SMOKING_INTENSITY = -1.822606
SMOKING_INTENSITY_CENTER = 0.4021541613

SMOKING_DURATION = 0.0317321
SMOKING_DURATION_CENTER = 27.0

SMOKING_QUIT_TIME = -0.0308572
SMOKING_QUIT_TIME_CENTER = 10.0

MODEL_CITATION = (
    "Tammemägi MC et al. N Engl J Med. 2013;368(8):728-736, Table 2 "
    "(PLCOm2012 modified logistic-regression model). PMC3929969."
)

# Risk thresholds reported in the development paper (PLCO control smokers),
# kept for reference, they are selection cut-points, not part of the equation.
THRESHOLD_NLST_EQUIVALENT_VOLUME = 0.013455  # matches NLST-eligible screening volume
THRESHOLD_SENSITIVITY_90 = 0.00948
THRESHOLD_SENSITIVITY_80 = 0.016082
