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

# Run the deployed CRC-PRO model exactly as riskcalc.org does.
#
# The `formula` expression below is copied VERBATIM from
#   https://github.com/ClevelandClinicQHS/riskcalc-website/blob/main/ColorectalCancer/server.R
# so this is the vendor's arithmetic, not our reading of it.
#
# NOTE the estrogen defect it contains: the expression tests
# (Estrogen == "Yes-previously"), which no UI choice can produce, so that
# coefficient never fires. Cases below deliberately include women with previous
# estrogen use so the parity test can pin the divergence.
#
#   Rscript tests/parity/reference/crc_pro_reference.R > crc_pro_cases.json

formula <- expression({
    if (Gender == "Female"){
        lp <- -5.9026635 +
            0.090012542 * AgeYr -
            4.4217156e-05 * max(AgeYr - 47, 0)**3 +
            9.2119076e-05 * max(AgeYr - 60, 0)**3 -
            4.7901919e-05 * max(AgeYr - 72, 0)**3 -
            0.24100367* (Ethnicity == "Hawaiian")+
            0.014010715   * (Ethnicity == "Japanese")-
            0.39669678    * (Ethnicity == "Latino")-
            0.34056094    * (Ethnicity == "White")+
            0.07443905    * YearsEdu -
            0.00062546554 * max(YearsEdu -  7, 0)**3 +
            0.0017200302  * max(YearsEdu - 14, 0)**3 -
            0.0010945647  * max(YearsEdu - 18, 0)**3 -
            0.24500762    * (Estrogen == "Yes-currently")-
            0.044320489   * (Estrogen == "Yes-previously")+
            0.23328937    * (Diabetes == "Yes")+
            0.062703176   * PackYears -
            0.002446026   * max(PackYears, 0)**3 +
            0.003038396   * max(PackYears - 1.25, 0)**3 -
            0.00059134632 * max(PackYears - 6.375, 0)**3 -
            1.023614e-06  * max(PackYears - 27.5125, 0)**3 +
            0.31589053    * (FamilyCRC == "Yes")-
            0.1665365     * (Multivitamin == "Yes") +
            0.0075233925  * (Weight * 0.45359237) / ((Height * 0.0254)    ^    2) +
            6.7918662e-05 * max((Weight * 0.45359237) / ((Height * 0.0254)    ^    2) - 20.371336, 0)**3 -
            0.00011039091 * max((Weight * 0.45359237) / ((Height * 0.0254)    ^    2) - 25.508027, 0)**3 +
            4.2472244e-05 * max((Weight * 0.45359237) / ((Height * 0.0254)    ^    2) - 33.722266, 0)**3 -
            0.046383323   * (PainMed == "Yes, but not currently")-
            0.236997      * (PainMed == "Yes, currently")-
            0.08856241    * Alcohol +
            0.62375456    * max(Alcohol, 0)**3 -
            0.7191129     * max(Alcohol - 0.10740682, 0)**3+
            0.095358349   * max(Alcohol - 0.8099724, 0)**3
        100 - 100 *	0.9901043 ** exp(lp)
    } else {
        lp <- -6.6419738 +
            0.091669179 * AgeYr -
            3.7411814e-05 * max(AgeYr - 47, 0)**3 +
            7.794128e-05  * max(AgeYr - 60, 0)**3 -
            4.0529466e-05 * max(AgeYr - 72, 0)**3 +
            0.16092241    * (Ethnicity == "Hawaiian")+
            0.25353936    * (Ethnicity == "Japanese")-
            0.13659953    * (Ethnicity == "Latino")-
            0.16728044    * (Ethnicity == "White")+
            0.00022581331 * PackYears +
            1.1341047e-05 * max(PackYears, 0)**3 -
            1.3522018e-05 * max(PackYears - 6.375, 0)**3 +
            2.1809706e-06 * max(PackYears - 39.525,0)**3 +
            0.28379769    * Alcohol -
            0.21424251    * max(Alcohol, 0)**3 +
            0.22570057    * max(Alcohol - 0.14457189, 0)**3 -
            0.011458065   * max(Alcohol - 2.8477722, 0)**3 +
            0.018020786   * (Weight * 0.45359237) / ((Height * 0.0254)       ^       2)+
            9.4715899e-05 * max((Weight * 0.45359237) / ((Height * 0.0254)       ^       2) -22.047175, 0)**3 -
            0.00015791645 * max((Weight * 0.45359237) / ((Height * 0.0254)       ^       2) - 25.941735, 0)**3 +
            6.3200548e-05 * max((Weight * 0.45359237) / ((Height * 0.0254)       ^       2) - 31.778341, 0)**3 +
            0.072052428   * YearsEdu -
            0.00060634342 * max(YearsEdu - 7, 0)**3 +
            0.0016674444  * max(YearsEdu -14, 0)**3 -
            0.001061101   * max(YearsEdu - 18, 0)**3 -
            0.032284161   * (Aspirin == "Yes - Not Currently")-
            0.20960315    * (Aspirin == "Yes")+
            0.24250922    * (FamilyCRC == "Yes")-
            0.19175375    * (Multivitamin == "Yes")+
            0.073141733   *  TotalMeat -
            0.0043503766  * max(TotalMeat - 0.59081962, 0)**3 +
            0.0065250851  * max(TotalMeat - 2.0822052, 0)**3 -
            0.0021747085  * max(TotalMeat - 5.0656345, 0)**3 +
            0.11020556    * (Diabetes == "Yes")-
            0.090669913   * Activity +
            0.0093816671  * max(Activity - 0.10714286, 0)**3 -
            0.011850527   * max(Activity - 0.82142857, 0)**3 +
            0.0024688598  * max(Activity - 3.5357143,  0)**3
        100 - 100 * 0.9846654 ** exp(lp)
    }
})

CASES <- list(
 list("Female", 120, 64, 55, "White",    0,  0.0, 16, "No",  "No",  "No",  "No",  "No",                    "No",                     0.0, 0.0),
 list("Female", 180, 66, 70, "Japanese", 30, 2.0, 12, "Yes", "No",  "Yes", "Yes", "Yes, currently",        "Yes-currently",          0.0, 0.0),
 list("Female", 220, 62, 80, "Latino",   50, 12.0, 6, "No",  "No",  "Yes", "No",  "Yes, but not currently","Yes, but not currently", 0.0, 0.0),
 list("Female",  75, 60, 45, "Hawaiian",  0, 0.0, 20, "Yes", "No",  "No",  "Yes", "No",                    "No",                     0.0, 0.0),
 list("Female", 350, 80, 85, "Black",    25, 6.0, 18, "Yes", "No",  "Yes", "No",  "Yes, currently",        "Yes-currently",          0.0, 0.0),
 list("Female", 150, 68, 60, "White",     8, 0.5, 14, "No",  "No",  "No",  "Yes", "Yes, but not currently","Yes, but not currently", 0.0, 0.0),
 list("Male",   170, 70, 55, "White",     0, 0.0, 16, "No",  "No",  "No",  "No",  "No",                    "No",                     1.0, 1.0),
 list("Male",   200, 72, 70, "Japanese", 40, 3.0, 12, "Yes", "Yes", "Yes", "Yes", "No",                    "No",                     3.0, 0.2),
 list("Male",    75, 60, 45, "Hawaiian",  0, 0.0, 20, "No",  "Yes - Not Currently", "Yes", "No", "No",     "No",                     0.0, 4.0),
 list("Male",   350, 80, 85, "Latino",   50, 12.0, 6, "Yes","Yes", "No",  "Yes", "No",                     "No",                     5.0, 0.0),
 list("Male",   190, 68, 62, "Black",    12, 1.5, 18, "No", "No",  "Yes", "No",  "No",                     "No",                     2.0, 2.5),
 list("Male",   240, 74, 78, "White",    22, 0.8, 10, "Yes","Yes", "No",  "Yes", "No",                     "No",                     0.6, 0.1)
)
out <- c()
for (cs in CASES) {
  d <- data.frame(Gender=cs[[1]], Weight=cs[[2]], Height=cs[[3]], AgeYr=cs[[4]],
                  Ethnicity=cs[[5]], PackYears=cs[[6]], Alcohol=cs[[7]], YearsEdu=cs[[8]],
                  FamilyCRC=cs[[9]], Aspirin=cs[[10]], Multivitamin=cs[[11]], Diabetes=cs[[12]],
                  PainMed=cs[[13]], Estrogen=cs[[14]], TotalMeat=cs[[15]], Activity=cs[[16]],
                  stringsAsFactors=FALSE)
  p <- eval(formula, d)
  out <- c(out, sprintf('  {"male": %s, "weight_lb": %g, "height_in": %g, "age": %g, "ethnicity": "%s", "pack_years": %g, "alcohol": %g, "years_education": %g, "family_history": %s, "aspirin": "%s", "multivitamin": %s, "diabetes": %s, "nsaid": "%s", "estrogen": "%s", "red_meat": %g, "activity": %g, "risk_pct": %.10f}',
    if (cs[[1]]=="Male") "true" else "false", cs[[2]], cs[[3]], cs[[4]], cs[[5]], cs[[6]], cs[[7]], cs[[8]],
    if (cs[[9]]=="Yes") "true" else "false", cs[[10]],
    if (cs[[11]]=="Yes") "true" else "false", if (cs[[12]]=="Yes") "true" else "false",
    cs[[13]], cs[[14]], cs[[15]], cs[[16]], p))
}
cat("{\n", '  "source": "riskcalc.org ColorectalCancer/server.R, run under R ',
    paste0(R.version$major, ".", R.version$minor), '",\n', '  "cases": [\n',
    paste(out, collapse=",\n"), "\n  ]\n}\n", sep="")
