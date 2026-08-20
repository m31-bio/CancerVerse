# Reference values for tests/parity/test_optum_lung_lasso_parity.py
#
# Route 1: the vendor's own code. This loads the fitted model with
# PatientLevelPrediction::loadPlpModel and scores it with
# PatientLevelPrediction::predictPlp — the same two calls the study package
# makes — so the whole predict path is the vendor's: applyTidyCovariateData
# (covariate deletion and normalisation by normFactors) followed by
# predictCyclops (join on covariateId, dot product, logistic link).
#
# Run:
#   Rscript tests/parity/reference/optum_lung_lasso_reference.R
#
# It writes optum_lung_lasso_cases.json next to itself. The JSON goes to a file
# rather than to stdout because PatientLevelPrediction logs its progress there
# through ParallelLogger, which no suppression option here reliably silences.
#
# Requires: install.packages(c("PatientLevelPrediction", "Andromeda",
#                              "FeatureExtraction", "Cyclops", "jsonlite"))
# and a clone of the study package. Set LUNG_CANCER_PROGNOSTIC to an existing
# clone, or let the script clone the pinned commit into a temporary directory.
#
# The cases deliberately include ids the model does not carry — one never in
# the covariate set at all, one dropped as infrequent, one dropped as the
# redundant reference band, and one whose beta is exactly zero. Each must leave
# the score untouched, and each takes a different route through the R pipeline
# to get there. Case "count value 3" feeds a non-binary value: every covariate
# in this model has a normalisation factor of 1, so PLP multiplies rather than
# clamps, and the Python must do the same.

suppressPackageStartupMessages({
  library(PatientLevelPrediction)
  library(Andromeda)
  library(jsonlite)
})

COMMIT <- "61c526eaba3f3130b2ba3a45c5f46759fcf4994c"
REPO <- "https://github.com/ohdsi-studies/lungCancerPrognostic"

repoDir <- Sys.getenv("LUNG_CANCER_PROGNOSTIC")
if (repoDir == "") {
  repoDir <- file.path(tempdir(), "lungCancerPrognostic")
  system2("git", c("clone", "--quiet", REPO, shQuote(repoDir)))
  system2("git", c("-C", shQuote(repoDir), "checkout", "--quiet", COMMIT))
}
modelDir <- file.path(repoDir, "inst", "models", "full_model")

plpModel <- PatientLevelPrediction::loadPlpModel(modelDir)
coefs <- plpModel$model$coefficients
betas <- coefs$betas[coefs$covariateIds != "(Intercept)"]
ids <- as.numeric(coefs$covariateIds[coefs$covariateIds != "(Intercept)"])
nz <- betas != 0
posIds <- ids[nz & betas > 0]
negIds <- ids[nz & betas < 0]
byMag <- ids[nz][order(-abs(betas[nz]))]

cases <- list(
  list(name = "intercept only", ids = numeric(0), values = numeric(0)),
  list(name = "current smoker", ids = c(3639)),
  list(name = "never smoker", ids = c(1639)),
  list(name = "former smoker, age 65-69, white",
       ids = c(2639, 13003, 8527004)),
  list(name = "ten largest by magnitude", ids = byMag[1:10]),
  list(name = "all positive coefficients", ids = posIds),
  list(name = "all negative coefficients", ids = negIds),
  list(name = "every non-zero covariate", ids = ids[nz]),
  list(name = "zero-beta candidate only (262923)", ids = c(262923)),
  list(name = "male, whose beta is the smallest kept", ids = c(8507001)),
  list(name = "covariate dropped as infrequent (8715802)", ids = c(8715802)),
  list(name = "redundant reference age band 50-54 (10003)", ids = c(10003)),
  list(name = "current smoker plus an id outside the covariate set",
       ids = c(3639, 987654321987)),
  list(name = "count value 3 on the smoking covariate",
       ids = c(3639), values = c(3)),
  list(name = "plausible record: former smoker, 60-64, white, COPD, PVD",
       ids = c(2639, 12003, 8527004, 255573210, 321052210))
)

rows <- do.call(rbind, lapply(seq_along(cases), function(i) {
  cid <- cases[[i]]$ids
  if (length(cid) == 0) return(NULL)
  val <- cases[[i]]$values
  if (is.null(val)) val <- rep(1, length(cid))
  data.frame(rowId = i, covariateId = as.numeric(cid), covariateValue = val)
}))

allIds <- unique(rows$covariateId)
covariateRef <- data.frame(
  covariateId = allIds,
  covariateName = as.character(allIds),
  analysisId = allIds %% 1000,
  conceptId = floor(allIds / 1000)
)
analysisRef <- data.frame(
  analysisId = unique(covariateRef$analysisId),
  analysisName = "unused", domainId = "unused",
  startDay = -365, endDay = 0, isBinary = "Y", missingMeansZero = "Y"
)

covariateData <- Andromeda::andromeda(
  covariates = rows, covariateRef = covariateRef, analysisRef = analysisRef
)
class(covariateData) <- "CovariateData"
plpData <- list(covariateData = covariateData)
class(plpData) <- "plpData"

population <- data.frame(rowId = seq_along(cases))
attr(population, "metaData") <- list(
  populationSettings = list(riskWindowEnd = 1095)
)

invisible(capture.output(
  prediction <- PatientLevelPrediction::predictPlp(plpModel, plpData,
                                                   population, timepoint = 1095)
))
prediction <- prediction[order(prediction$rowId), ]

out <- lapply(seq_along(cases), function(i) {
  cid <- cases[[i]]$ids
  val <- cases[[i]]$values
  if (is.null(val)) val <- rep(1, length(cid))
  list(
    name = cases[[i]]$name,
    covariates = if (length(cid) == 0) {
      structure(list(), names = character(0))
    } else {
      setNames(as.list(val), format(cid, scientific = FALSE, trim = TRUE))
    },
    linear_predictor = prediction$rawValue[i],
    risk = prediction$value[i]
  )
})

args <- commandArgs(trailingOnly = TRUE)
outFile <- if (length(args) > 0) args[1] else {
  here <- dirname(sub("^--file=", "", grep("^--file=", commandArgs(), value = TRUE)))
  file.path(if (length(here) == 0) "." else here, "optum_lung_lasso_cases.json")
}
writeLines(
  jsonlite::toJSON(out, auto_unbox = TRUE, digits = 16, pretty = TRUE),
  outFile
)
message("wrote ", outFile)
