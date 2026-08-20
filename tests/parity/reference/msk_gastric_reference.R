# ---------------------------------------------------------------------------
# LICENCE NOTICE -- THIS FILE IS NOT COVERED BY THIS REPOSITORY'S LICENCE.
#
# The arithmetic below is copied verbatim from
#   https://github.com/ClevelandClinicQHS/riskcalc-website
# which is licensed **PolyForm Noncommercial 1.0.0**, NOT Apache-2.0.
#
# The repository's own LICENSE (Apache-2.0) does not, and cannot, apply to it:
# nobody may relicense someone else's work by putting it in their tree. This
# file may be used only for a noncommercial purpose, which PolyForm defines as
# "any noncommercial purpose" regardless of who is using it.
#
# It is present because this project's use is academic research only. If that
# ever stops being true, this file must come out again -- and so must the five
# others listed in NOTICE beside it.
#
# Withheld from the public mirror until 2026-08-18 on the reasoning that a
# company repository could not have a noncommercial purpose. That reasoning
# tested the wrong thing: PolyForm gates on PURPOSE, not on who is using it.
# See docs/THIRD_PARTY_CODE.md and docs/ACADEMIC_USE_LICENSE_REVIEW.md.
# ---------------------------------------------------------------------------

# Run the deployed MSK gastric nomogram exactly as riskcalc.org does.
#
# The two expressions below are copied VERBATIM from
#   https://github.com/ClevelandClinicQHS/riskcalc-website/blob/main/GastricCancer/server.R
# so this file is the vendor's own arithmetic, not our reading of it. That is
# what makes the comparison a parity check rather than a self-test.
#
#   Rscript tests/parity/reference/msk_gastric_reference.R > msk_gastric_cases.json

predict.5yr.formula <- expression({lp <- -2.3678975 +
    0.227464 * (Gender == "Male") -
    0.011606041 * AgeYr +
    3.4469803e-05 * pmax(AgeYr - 48, 0)**3 -
    8.4848746e-05 * pmax(AgeYr - 67, 0)**3 +
    5.0378943e-05 * pmax(AgeYr - 80, 0)**3 +
    0.23855249 * (PrimarySite == "Body or Middle One Third") +
    0.7131089 * (PrimarySite == "Gastroesophageal Junction") +
    0.14158861 * (PrimarySite == "Proximal or Upper One Third") -
    0.19097534 * (Lauren == "Intestinal") -
    0.075717935 * (Lauren == "Mixed") +
    0.0097446167 * Size +
    0.34360148 * NumPosNodes -
    0.0096735309 * pmax(NumPosNodes, 0)**3 +
    0.010640884 * pmax(NumPosNodes - 1, 0)**3 -
    0.00096735309 * pmax(NumPosNodes - 11, 0)**3 -
    0.047258944 * NumNegNodes +
    4.5172072e-05 * pmax(NumNegNodes - 5, 0)**3 -
    7.2275315e-05 * pmax(NumNegNodes - 17, 0)**3 +
    2.7103243e-05 * pmax(NumNegNodes - 37, 0)**3 +
    0.6913717 * Depth -
    0.024435477 * pmax(Depth - 2, 0)**3 +
    0.048870953 * pmax(Depth - 4, 0)**3 -
    0.024435477 * pmax(Depth - 6, 0)**3;
100 * 0.579053^(exp(lp))})

predict.9yr.formula <- expression({lp <- -2.3678975 +
    0.227464 * (Gender == "Male") -
    0.011606041 * AgeYr +
    3.4469803e-05 * pmax(AgeYr - 48, 0)**3 -
    8.4848746e-05 * pmax(AgeYr - 67, 0)**3 +
    5.0378943e-05 * pmax(AgeYr - 80, 0)**3 +
    0.23855249 * (PrimarySite == "Body or Middle One Third") +
    0.7131089 * (PrimarySite == "Gastroesophageal Junction") +
    0.14158861 * (PrimarySite == "Proximal or Upper One Third") -
    0.19097534 * (Lauren == "Intestinal") -
    0.075717935 * (Lauren == "Mixed") +
    0.0097446167 * Size +
    0.34360148 * NumPosNodes -
    0.0096735309 * pmax(NumPosNodes, 0)**3 +
    0.010640884 * pmax(NumPosNodes - 1, 0)**3 -
    0.00096735309 * pmax(NumPosNodes - 11, 0)**3 -
    0.047258944 * NumNegNodes +
    4.5172072e-05 * pmax(NumNegNodes - 5, 0)**3 -
    7.2275315e-05 * pmax(NumNegNodes - 17, 0)**3 +
    2.7103243e-05 * pmax(NumNegNodes - 37, 0)**3 +
    0.6913717 * Depth -
    0.024435477 * pmax(Depth - 2, 0)**3 +
    0.048870953 * pmax(Depth - 4, 0)**3 -
    0.024435477 * pmax(Depth - 6, 0)**3;
100 * 0.5089101^(exp(lp))})

# Depth level order, from the app's factor() call. The number is what enters
# the model, so the ORDER is part of the specification.
DEPTHS <- c('Mucosa', 'Submucosa', 'Propia Muscularis', 'Subserosa',
            'Suspected serosal invasion', 'Definite serosal invasion',
            'Adjacent organ involvement')

cases <- list(
  list(60, "Male",   "Antrum or Piloric",           "Intestinal", 3.0,  0,  20, 3),
  list(45, "Female", "Gastroesophageal Junction",   "Diffuse",    6.5,  5,  10, 6),
  list(75, "Male",   "Body or Middle One Third",    "Mixed",      2.0,  1,  30, 2),
  list(30, "Female", "Proximal or Upper One Third", "Intestinal", 10.0, 12,  4, 7),
  list(88, "Male",   "Antrum or Piloric",           "Diffuse",    1.0,  0,  0, 1),
  list(52, "Female", "Body or Middle One Third",    "Intestinal", 4.5,  3,  17, 4),
  list(67, "Male",   "Gastroesophageal Junction",   "Mixed",      8.0, 23, 146, 5),
  list(25, "Female", "Antrum or Piloric",           "Mixed",      0.1,  0,  5, 1),
  list(96, "Male",   "Proximal or Upper One Third", "Diffuse",   21.0, 11,  37, 7),
  list(59, "Female", "Body or Middle One Third",    "Diffuse",    5.0,  2,  46, 4),
  list(48, "Male",   "Antrum or Piloric",           "Intestinal", 7.0,  8,  18, 6),
  list(80, "Female", "Gastroesophageal Junction",   "Intestinal", 3.3,  4,  38, 3)
)

out <- c()
for (cs in cases) {
  d <- data.frame(AgeYr = cs[[1]], Gender = cs[[2]], PrimarySite = cs[[3]],
                  Lauren = cs[[4]], Size = cs[[5]], NumPosNodes = cs[[6]],
                  NumNegNodes = cs[[7]], Depth = cs[[8]],
                  stringsAsFactors = FALSE)
  p5 <- eval(predict.5yr.formula, d)
  p9 <- eval(predict.9yr.formula, d)
  out <- c(out, sprintf(
    '  {"age": %g, "male": %s, "primary_site": "%s", "lauren": "%s", "size_cm": %g, "positive_nodes": %d, "negative_nodes": %d, "depth_code": %d, "depth": "%s", "dss_5yr_pct": %.10f, "dss_9yr_pct": %.10f}',
    cs[[1]], if (cs[[2]] == "Male") "true" else "false", cs[[3]], cs[[4]],
    cs[[5]], cs[[6]], cs[[7]], cs[[8]], DEPTHS[cs[[8]]], p5, p9))
}
cat("{\n", '  "source": "riskcalc.org GastricCancer/server.R, run under R ',
    paste0(R.version$major, ".", R.version$minor), '",\n', '  "cases": [\n',
    paste(out, collapse = ",\n"), "\n  ]\n}\n", sep = "")
