# Reference values for tests/parity/test_r_reference_parity.py
# Run:  Rscript tests/parity/reference/predict_reference.R
# Requires: remotes::install_github("WintonCentre/predictv30r")
#
# NOTE: benefits22 is UNEXPORTED and must be reached with ':::'.
# The exported benefits222 computes DISEASE-FREE survival, not overall
# survival, and will not match this project's model.
suppressMessages(library(predictv30r))
f <- predictv30r:::benefits22
r <- as.matrix(f(age.start=57, screen=0, size=29, grade=2, nodes=5, er=1,
                 her2=1, ki67=1, generation=3, horm=1, traz=1, bis=1,
                 radio=0, delay=0))
cat(sprintf("erpos_y10_surg %.6f\n",   r[10, "surg"]))
cat(sprintf("erpos_y10_hctb %.6f\n",   r[10, "hctb"]))
cat(sprintf("erpos_y15_hctb %.6f\n",   r[15, "hctb"]))
cat(sprintf("erpos_y15_h10ctb %.6f\n", r[15, "h10ctb"]))
r2 <- as.matrix(f(age.start=45, screen=1, size=15, grade=1, nodes=0, er=0,
                  her2=0, ki67=9, generation=2, horm=0, traz=0, bis=0,
                  radio=0, delay=0))
cat(sprintf("erneg_y10_surg %.6f\n", r2[10, "surg"]))
cat(sprintf("erneg_y10_c %.6f\n",    r2[10, "c"]))
