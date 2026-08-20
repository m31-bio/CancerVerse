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

# Run the deployed PBCG model exactly as riskcalc.org does.
#
# The `risk` function below is copied VERBATIM from
#   https://github.com/ClevelandClinicQHS/riskcalc-website/blob/main/PBCG/R_code_PBCG_risk_calculator.R
# so this is the vendor's arithmetic, not our reading of it.
#
# `risk_raw` is the SAME function with only the two round() calls removed, so
# the parity test can compare unrounded probabilities. The tool's own rounding
# derives high grade as 100 - no - low, which piles every rounding error onto
# the high-grade estimate; that behaviour is tested separately.
#
#   Rscript tests/parity/reference/pbcg_reference.R > pbcg_cases.json

# psa: enter prostate-specific antigen in ng/mL
# age: enter age in years
# race: enter 1 for African Ancestry, 0 otherwise
# priorbiopsy: enter 1 if there has been one or more prior biopsies (all negative for prostate cancer), 0 otherwise
# dre: enter 1 if digital rectal examination is abnormal (suspicious for prostate cancer), 0 otherwise
# famhistory: enter 1 if there is a first-degree family history of prostate cancer, 0 otherwise

# psa, age and race are mandatory, priorbiopsy, dre and famhistory are allowed missing

risk = function(psa, age, race, priorbiopsy, dre, famhistory) {

  ##### create persons data set
  data=c(1, log(psa,2), age, race)
  # is priorbiopsy known?
  a = as.numeric(is.na(priorbiopsy)==FALSE)
  if(a==1){data=c(data, priorbiopsy)}
  # is dre known?
  b = as.numeric(is.na(dre)==FALSE)
  if(b==1){data=c(data, dre)}
  # is famhistory known?
  c = as.numeric(is.na(famhistory)==FALSE)
  if(c==1){data=c(data, famhistory)}

  ##### choose correct model
  # psa, age, race, priorbiopsy, dre, famhistory
  if(a==1 & b==1 & c==1){
    no.low=c(-2.44052108 , 0.13617244 , 0.01780617 , 0.78721039 , -0.83613721 , 0.04612721 , 0.33233636)
    no.high=c(-6.36851856 , 0.79996510 , 0.05566536 , 0.61596975 , -1.27437249 , 0.85780143 , 0.61003848)
  }
  # psa, age, race, priorbiopsy, dre
  if(a==1 & b==1 & c==0){
    no.low=c(-2.29687989 , 0.13785591 , 0.01758914 , 0.63876791 , -0.86200471 , 0.07193350)
    no.high=c(-6.06621401 , 0.76053930 , 0.05509847 , 0.51701373 , -1.38390751 , 0.83442202)
  }
  # psa, age, race, priorbiopsy, famhistory
  if(a==1 & b==0 & c==1){
    no.low=c(-2.64840984 , 0.13125283 , 0.02044166 , 0.81792881 , -0.98610357 , 0.31447017)
    no.high=c(-6.70538152 , 0.77635003 , 0.06542705 , 0.52401464 , -1.43681965 , 0.55443478)
  }
  # psa, age, race, dre, famhistory
  if(a==0 & b==1 & c==1){
    no.low=c(-2.16147411 , 0.07409519 , 0.01322988 , 0.76131045 , 0.05397516 , 0.29246219)
    no.high=c(-5.99897055 , 0.70727793 , 0.04992968 , 0.56485952 , 0.89154384 , 0.56910873)
  }
  # psa, age, race, priorbiopsy
  if(a==1 & b==0 & c==0){
    no.low=c(-2.49050385 , 0.12961272 , 0.02020429 , 0.67674970 , -0.97275826)
    no.high=c(-6.41089002 , 0.74110558 , 0.06476911 , 0.42814591 , -1.50274350)
  }
  # psa, age, race, dre
  if(a==0 & b==1 & c==0){
    no.low=c(-2.01851079 , 0.06745424 , 0.01263369 , 0.63938472 , 0.08562844)
    no.high=c(-5.68203352 , 0.65059244 , 0.04883786 , 0.49214793 , 0.87421554)
  }
  # psa, age, race, famhistory
  if(a==0 & b==0 & c==1){
    no.low=c(-2.39161580 , 0.06129651 , 0.01600515 , 0.81132928 , 0.27501639)
    no.high=c(-6.42320154 , 0.67779036 , 0.06092178 , 0.50429130 , 0.50805684)
  }
  # psa, age, race
  if(a==0 & b==0 & c==0){
    no.low=c(-2.23794923 , 0.05343098 , 0.01553627 , 0.69593716)
    no.high=c(-6.13292904 , 0.62979529 , 0.06002002 , 0.43816016)
  }

  ##### predicting probabilities
  S1=no.low%*%data
  S2=no.high%*%data
  risk.no=1/(1+exp(S1)+exp(S2))*100
  risk.low=exp(S1)/(1+exp(S1)+exp(S2))*100
  # risk.high=100-risk.no-risk.low

  ##### Outcome
  risk.no=round(risk.no)
  risk.low=round(risk.low)
  risk.high=100-risk.no-risk.low

  ##### Outcome
  risk.outcome=cbind(risk.no,risk.low,risk.high)

  ##### Add Dimnames to Vector
  dimnames(risk.outcome)=list(NULL, c('Chance of No Cancer', 'Risk of Low Grade Cancer', 'Risk of High Grade Cancer'))

  return(risk.outcome)
}

# psa: enter prostate-specific antigen in ng/mL
# age: enter age in years
# race: enter 1 for African Ancestry, 0 otherwise
# priorbiopsy: enter 1 if there has been one or more prior biopsies (all negative for prostate cancer), 0 otherwise
# dre: enter 1 if digital rectal examination is abnormal (suspicious for prostate cancer), 0 otherwise
# famhistory: enter 1 if there is a first-degree family history of prostate cancer, 0 otherwise

# psa, age and race are mandatory, priorbiopsy, dre and famhistory are allowed missing

risk_raw = function(psa, age, race, priorbiopsy, dre, famhistory) {

  ##### create persons data set
  data=c(1, log(psa,2), age, race)
  # is priorbiopsy known?
  a = as.numeric(is.na(priorbiopsy)==FALSE)
  if(a==1){data=c(data, priorbiopsy)}
  # is dre known?
  b = as.numeric(is.na(dre)==FALSE)
  if(b==1){data=c(data, dre)}
  # is famhistory known?
  c = as.numeric(is.na(famhistory)==FALSE)
  if(c==1){data=c(data, famhistory)}

  ##### choose correct model
  # psa, age, race, priorbiopsy, dre, famhistory
  if(a==1 & b==1 & c==1){
    no.low=c(-2.44052108 , 0.13617244 , 0.01780617 , 0.78721039 , -0.83613721 , 0.04612721 , 0.33233636)
    no.high=c(-6.36851856 , 0.79996510 , 0.05566536 , 0.61596975 , -1.27437249 , 0.85780143 , 0.61003848)
  }
  # psa, age, race, priorbiopsy, dre
  if(a==1 & b==1 & c==0){
    no.low=c(-2.29687989 , 0.13785591 , 0.01758914 , 0.63876791 , -0.86200471 , 0.07193350)
    no.high=c(-6.06621401 , 0.76053930 , 0.05509847 , 0.51701373 , -1.38390751 , 0.83442202)
  }
  # psa, age, race, priorbiopsy, famhistory
  if(a==1 & b==0 & c==1){
    no.low=c(-2.64840984 , 0.13125283 , 0.02044166 , 0.81792881 , -0.98610357 , 0.31447017)
    no.high=c(-6.70538152 , 0.77635003 , 0.06542705 , 0.52401464 , -1.43681965 , 0.55443478)
  }
  # psa, age, race, dre, famhistory
  if(a==0 & b==1 & c==1){
    no.low=c(-2.16147411 , 0.07409519 , 0.01322988 , 0.76131045 , 0.05397516 , 0.29246219)
    no.high=c(-5.99897055 , 0.70727793 , 0.04992968 , 0.56485952 , 0.89154384 , 0.56910873)
  }
  # psa, age, race, priorbiopsy
  if(a==1 & b==0 & c==0){
    no.low=c(-2.49050385 , 0.12961272 , 0.02020429 , 0.67674970 , -0.97275826)
    no.high=c(-6.41089002 , 0.74110558 , 0.06476911 , 0.42814591 , -1.50274350)
  }
  # psa, age, race, dre
  if(a==0 & b==1 & c==0){
    no.low=c(-2.01851079 , 0.06745424 , 0.01263369 , 0.63938472 , 0.08562844)
    no.high=c(-5.68203352 , 0.65059244 , 0.04883786 , 0.49214793 , 0.87421554)
  }
  # psa, age, race, famhistory
  if(a==0 & b==0 & c==1){
    no.low=c(-2.39161580 , 0.06129651 , 0.01600515 , 0.81132928 , 0.27501639)
    no.high=c(-6.42320154 , 0.67779036 , 0.06092178 , 0.50429130 , 0.50805684)
  }
  # psa, age, race
  if(a==0 & b==0 & c==0){
    no.low=c(-2.23794923 , 0.05343098 , 0.01553627 , 0.69593716)
    no.high=c(-6.13292904 , 0.62979529 , 0.06002002 , 0.43816016)
  }

  ##### predicting probabilities
  S1=no.low%*%data
  S2=no.high%*%data
  risk.no=1/(1+exp(S1)+exp(S2))*100
  risk.low=exp(S1)/(1+exp(S1)+exp(S2))*100
  # risk.high=100-risk.no-risk.low

  ##### Outcome  (round() calls removed for the parity comparison)
  risk.high=100-risk.no-risk.low

  ##### Outcome
  risk.outcome=cbind(risk.no,risk.low,risk.high)

  ##### Add Dimnames to Vector
  dimnames(risk.outcome)=list(NULL, c('Chance of No Cancer', 'Risk of Low Grade Cancer', 'Risk of High Grade Cancer'))

  return(risk.outcome)
}


# psa, age, race(1=African ancestry), priorbiopsy, dre, famhistory (NA = unknown)
CASES <- list(
  list(4.0,  62, 0,  0,  0,  0),
  list(1.2,  55, 1,  1,  0,  1),
  list(15.0, 70, 0,  0,  1,  0),
  list(2.5,  48, 1, NA, NA, NA),
  list(8.0,  75, 0,  1, NA,  1),
  list(0.6,  50, 0, NA,  1, NA),
  list(30.0, 80, 1,  0,  1,  1),
  list(5.5,  65, 0,  1,  1, NA),
  list(3.1,  58, 1, NA,  0,  1),
  list(12.0, 68, 0, NA, NA,  0),
  list(6.7,  72, 1,  1, NA, NA),
  list(0.9,  45, 0,  0, NA, NA)
)
j <- function(x) if (is.na(x)) "null" else if (x == 1) "true" else "false"
out <- c()
for (cs in CASES) {
  rr <- risk_raw(cs[[1]], cs[[2]], cs[[3]], cs[[4]], cs[[5]], cs[[6]])
  rd <- risk(cs[[1]], cs[[2]], cs[[3]], cs[[4]], cs[[5]], cs[[6]])
  out <- c(out, sprintf(
'  {"psa": %g, "age": %g, "african_ancestry": %s, "prior_biopsy": %s, "dre_abnormal": %s, "family_history": %s, "no_cancer_pct": %.10f, "low_grade_pct": %.10f, "high_grade_pct": %.10f, "rounded": [%d, %d, %d]}',
    cs[[1]], cs[[2]], if (cs[[3]] == 1) "true" else "false",
    j(cs[[4]]), j(cs[[5]]), j(cs[[6]]),
    rr[1], rr[2], rr[3], rd[1], rd[2], rd[3]))
}
cat("{\n", '  "source": "riskcalc.org PBCG/R_code_PBCG_risk_calculator.R, R ',
    paste0(R.version$major, ".", R.version$minor), '",\n  "cases": [\n',
    paste(out, collapse = ",\n"), "\n  ]\n}\n", sep = "")
