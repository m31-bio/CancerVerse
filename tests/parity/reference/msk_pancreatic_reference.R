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
#   Rscript tests/parity/reference/msk_pancreatic_reference.R > msk_pancreatic_cases.json

predict.score <- expression({
    score = -1.1733872 -
        0.0018564703 * SurgAge +
        0.052203014 * (Gender == "Male") +
        0.14916275 * (PortVein == "Yes") +
        0.90746165 * (Splenectomy == "Yes") +
        0.06340785 * (MarginResec == "Positive") -
        0.75934357 * (Head == "Other") +
        0.31532231 * (Diff == "Poor") -
        0.20496646 * (Diff == "Well") +
        0.3177352 * (PostMargin == "Positive") +
        0.23051721 * NumPosNodes -
        0.014400166 * max(NumPosNodes, 0)**3 +
        0.018000207 * max(NumPosNodes - 1, 0)**3 -
        0.0036000415 * max(NumPosNodes - 5, 0)**3 -
        0.0017790967 * NumNegNodes +
        0.22200163 * (BackPain == "Yes")  -
        0.53691787 * (TStage == "2") -
        0.38735092 * (TStage == "3") +
        0.3867342 * (TStage == "4") +
        0.04259022 * (WeightLoss == "Yes") +
        0.43940983 * MaxPathAxis -
        0.039121714 * max(MaxPathAxis - 2, 0)**3 +
        0.059533043 * max(MaxPathAxis - 3.2, 0)**3 -
        0.020411329 * max(MaxPathAxis - 5.5, 0)**3
    exp(score)
})

CASES <- list(
 list(33,"Male","No","No","Negative","Head","Moderate","Negative",0,0,"No","1","No",0.1),
 list(89,"Female","Yes","Yes","Positive","Other","Poor","Positive",39,83,"Yes","4","Yes",16),
 list(60,"Male","No","No","Negative","Head","Well","Negative",1,10,"No","2","No",2.0),
 list(70,"Female","Yes","No","Positive","Head","Poor","Negative",5,20,"Yes","3","Yes",3.2),
 list(55,"Male","No","Yes","Negative","Other","Moderate","Positive",8,5,"No","4","No",5.5),
 list(48,"Female","No","No","Negative","Head","Well","Negative",0,30,"No","1","Yes",1.5),
 list(78,"Male","Yes","Yes","Positive","Other","Poor","Positive",12,2,"Yes","2","No",7.0),
 list(65,"Female","No","No","Positive","Head","Moderate","Negative",3,15,"No","3","No",4.0)
)
out <- c()
for (cs in CASES) {
  d <- data.frame(SurgAge=cs[[1]], Gender=cs[[2]], PortVein=cs[[3]], Splenectomy=cs[[4]],
                  MarginResec=cs[[5]], Head=cs[[6]], Diff=cs[[7]], PostMargin=cs[[8]],
                  NumPosNodes=cs[[9]], NumNegNodes=cs[[10]], BackPain=cs[[11]],
                  TStage=cs[[12]], WeightLoss=cs[[13]], MaxPathAxis=cs[[14]],
                  stringsAsFactors=FALSE)
  sc <- eval(predict.score, d)
  out <- c(out, sprintf('  {"age": %g, "male": %s, "portal_vein": %s, "splenectomy": %s, "margin_positive": %s, "location": "%s", "differentiation": "%s", "posterior_margin_positive": %s, "positive_nodes": %d, "negative_nodes": %d, "back_pain": %s, "t_stage": "%s", "weight_loss": %s, "size_cm": %g, "surv_12mo_pct": %.10f, "surv_24mo_pct": %.10f, "surv_36mo_pct": %.10f}',
    cs[[1]], if (cs[[2]]=="Male") "true" else "false",
    if (cs[[3]]=="Yes") "true" else "false", if (cs[[4]]=="Yes") "true" else "false",
    if (cs[[5]]=="Positive") "true" else "false", cs[[6]], cs[[7]],
    if (cs[[8]]=="Positive") "true" else "false", cs[[9]], cs[[10]],
    if (cs[[11]]=="Yes") "true" else "false", cs[[12]],
    if (cs[[13]]=="Yes") "true" else "false", cs[[14]],
    100*0.6775**sc, 100*0.3457804**sc, 100*0.1976732**sc))
}
cat("{\n", '  "source": "riskcalc.org PancreaticCancer.../server.R, R ',
    paste0(R.version$major,".",R.version$minor), '",\n  "cases": [\n',
    paste(out, collapse=",\n"), "\n  ]\n}\n", sep="")
