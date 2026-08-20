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

# Copied VERBATIM from riskcalc.org's server.R, so this is the vendor's
# arithmetic rather than our reading of it.
#
#   Rscript tests/parity/reference/msk_ovarian_reference.R > msk_ovarian_cases.json

predict.5yr <- expression({
    lp <- -1.7686247 +
        0.014563065 * SurgAge +
        0.000020997108 * max(SurgAge - 44, 0)**3 -
        0.000043394022 * max(SurgAge - 60, 0)**3 +
        0.000022396915 * max(SurgAge - 75, 0)**3 -
        0.053519323 * (TumorGrade == "3") -
        0.18814327 * (TumorHist == "Yes") +
        0.00063621499 * PreOpPlatelet +
        0.57912923 * (Ascites == "Yes") +
        0.5518022 * (ResidDiam == "1-2 cm") -
        0.3062644 * (ResidDiam == '<0.5 cm') +
        0.6219986 * (ResidDiam == '>2 cm') -
        0.54064543 * (ResidDiam == 'No Gross Residual')
    100 * 0.4284861 ^ exp(lp)
})

CASES <- list(
 list(22, "1-2", "No",  113, "No",  "No Gross Residual"),
 list(45, "3",   "Yes", 300, "Yes", "<0.5 cm"),
 list(60, "1-2", "Yes", 450, "No",  "0.5-1 cm"),
 list(75, "3",   "No",  800, "Yes", "1-2 cm"),
 list(87, "3",   "Yes", 1078,"Yes", ">2 cm"),
 list(52, "1-2", "No",  200, "Yes", "0.5-1 cm"),
 list(68, "3",   "Yes", 550, "No",  ">2 cm"),
 list(38, "1-2", "Yes", 160, "No",  "1-2 cm")
)
out <- c()
for (cs in CASES) {
  d <- data.frame(SurgAge=cs[[1]], TumorGrade=cs[[2]], TumorHist=cs[[3]],
                  PreOpPlatelet=cs[[4]], Ascites=cs[[5]], ResidDiam=cs[[6]],
                  stringsAsFactors=FALSE)
  out <- c(out, sprintf('  {"age": %g, "grade": "%s", "histology_yes": %s, "platelets": %g, "ascites": %s, "residual": "%s", "surv_5yr_pct": %.10f}',
    cs[[1]], cs[[2]], if (cs[[3]]=="Yes") "true" else "false", cs[[4]],
    if (cs[[5]]=="Yes") "true" else "false", cs[[6]], eval(predict.5yr, d)))
}
cat("{\n", '  "source": "riskcalc.org OvarianCancer.../server.R, R ',
    paste0(R.version$major,".",R.version$minor), '",\n  "cases": [\n',
    paste(out, collapse=",\n"), "\n  ]\n}\n", sep="")
