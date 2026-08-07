# Reference values for tests/parity/test_r_reference_parity.py
# Run:  Rscript tests/parity/reference/score2_reference.R
# Requires: install.packages("RiskScorescvd")   (MIT)
#
# NOTE: RiskScorescvd::SCORE2 ends in `return(round(x, 1))` — it rounds to one
# decimal place. Compare with tolerance 0.05, not to machine precision.
suppressMessages(library(RiskScorescvd))
cases <- list(
  list(r="Low",       a=50, g="male",   s=1, sbp=140, d=0, tc=6.0, hdl=1.0),
  list(r="Moderate",  a=50, g="male",   s=1, sbp=140, d=0, tc=6.0, hdl=1.0),
  list(r="High",      a=65, g="female", s=0, sbp=130, d=0, tc=5.5, hdl=1.4),
  list(r="Very high", a=45, g="female", s=1, sbp=160, d=0, tc=7.0, hdl=0.9)
)
for (c in cases) {
  v <- SCORE2(Risk.region=c$r, Age=c$a, Gender=c$g, smoker=c$s,
              systolic.bp=c$sbp, diabetes=c$d, total.chol=c$tc,
              total.hdl=c$hdl, classify=FALSE)
  cat(sprintf("%s %.1f\n", gsub(" ", "_", tolower(c$r)), as.numeric(v)))
}
