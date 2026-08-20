# Run the Extended PBCG model as its authors published it.
#
# The coefficient matrix and the `risk()` function below are Additional file 2
# of:
#
#   Neumair M, Kattan MW, Freedland SJ, et al. (Ankerst DP, senior author).
#   Accommodating heterogeneous missing data patterns for prostate cancer
#   risk prediction. BMC Med Res Methodol. 2022;22(1):200.
#   doi:10.1186/s12874-022-01674-x
#
# That article is CC BY 4.0, which permits use, adaptation and redistribution
# including commercially, with attribution. This file is therefore safe to keep
# in the repository -- unlike the six PolyForm-Noncommercial reference scripts
# it replaces. See docs/THIRD_PARTY_CODE.md.
#
# The matrix itself is not reproduced here; it is loaded from the JSON the
# package ships, so there is exactly one copy of those 8,192 numbers in this
# repository and the R and Python paths cannot drift apart.
#
#   Rscript tests/parity/reference/pbcg_extended_reference.R > pbcg_extended_cases.json

suppressMessages(library(jsonlite))

here <- dirname(sub("--file=", "", grep("--file=", commandArgs(), value = TRUE)))
if (length(here) == 0 || here == "") here <- "tests/parity/reference"
d <- fromJSON(file.path(here, "..", "..", "..", "src", "cancerverse_baseline",
                        "prostate", "detection", "data",
                        "pbcg_extended_2022.json"))
coef_ac <- as.matrix(d$rows)
colnames(coef_ac) <- d$columns

# ---- verbatim from Additional file 2 ---------------------------------------
risk = function(age, psa, race, priorbiopsy, dre, famhist.1, famhist.2,
                famhist.bca, prosvol, ari.use, hispanic, priorpsa) {
  psa <- log(psa, 2)
  if (!is.na(prosvol)) { prosvol <- log(prosvol, 2) }
  test <- c(age, psa, race, priorbiopsy, dre, famhist.1, famhist.2,
            famhist.bca, prosvol, ari.use, hispanic, priorpsa)
  a = is.na(race); b = is.na(priorbiopsy); c = is.na(dre)
  d = is.na(famhist.1); e = is.na(famhist.2); f = is.na(famhist.bca)
  g = is.na(prosvol); h = is.na(ari.use); i = is.na(hispanic)
  j = is.na(priorpsa)
  sel <- is.na(coef_ac[, "race"]) == a &
    is.na(coef_ac[, "priorbiopsy"]) == b &
    is.na(coef_ac[, "dre"]) == c &
    is.na(coef_ac[, "famhist.1"]) == d &
    is.na(coef_ac[, "famhist.2"]) == e &
    is.na(coef_ac[, "famhist.bca"]) == f &
    is.na(coef_ac[, "prosvol"]) == g &
    is.na(coef_ac[, "ari.use"]) == h &
    is.na(coef_ac[, "hispanic"]) == i &
    is.na(coef_ac[, "priorpsa"]) == j
  risk.high <- sum(coef_ac[sel, -1] * test, na.rm = T) + coef_ac[sel, 1]
  exp(risk.high) / (1 + exp(risk.high)) * 100
}
# ---- end verbatim ----------------------------------------------------------

# Cases chosen to exercise the sub-model selection rather than one model:
# every count of supplied optional predictors from 0 to 10, both extremes of
# each binary, and prostate volumes either side of the log2 transform.
NA_ <- NA_real_
cases <- list(
  list(65, 5.0,  NA_,NA_,NA_,NA_,NA_,NA_,NA_,NA_,NA_,NA_),
  list(50, 1.0,  0,  NA_,NA_,NA_,NA_,NA_,NA_,NA_,NA_,NA_),
  list(75, 20.0, 1,  1,  NA_,NA_,NA_,NA_,NA_,NA_,NA_,NA_),
  list(60, 3.5,  0,  0,  1,  NA_,NA_,NA_,NA_,NA_,NA_,NA_),
  list(68, 8.2,  1,  0,  1,  1,  NA_,NA_,NA_,NA_,NA_,NA_),
  list(55, 2.1,  0,  1,  0,  0,  1,  NA_,NA_,NA_,NA_,NA_),
  list(70, 12.0, 1,  1,  1,  1,  1,  1,  NA_,NA_,NA_,NA_),
  list(62, 4.4,  0,  0,  0,  0,  0,  0,  25, NA_,NA_,NA_),
  list(58, 6.7,  1,  0,  1,  0,  1,  0,  60, 1,  NA_,NA_),
  list(72, 15.5, 0,  1,  0,  1,  0,  1,  100,0,  1,  NA_),
  list(65, 5.0,  1,  0,  1,  1,  0,  0,  40, 0,  0,  1),
  list(45, 0.5,  0,  0,  0,  0,  0,  0,  15, 0,  0,  0),
  list(85, 50.0, 1,  1,  1,  1,  1,  1,  200,1,  1,  1)
)

out <- lapply(cases, function(k) {
  v <- do.call(risk, k)
  list(age = k[[1]], psa = k[[2]], race = k[[3]], prior_biopsy = k[[4]],
       dre_abnormal = k[[5]], famhist_1 = k[[6]], famhist_2 = k[[7]],
       famhist_bca = k[[8]], prostate_volume = k[[9]], ari_use = k[[10]],
       hispanic = k[[11]], prior_psa = k[[12]], percent = v)
})
cat(toJSON(out, auto_unbox = TRUE, digits = 15, na = "null", pretty = TRUE))
