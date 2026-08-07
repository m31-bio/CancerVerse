# Reference values for tests/parity/test_r_reference_parity.py
# Run:  Rscript tests/parity/reference/bcrat_reference.R
# Requires: install.packages("BCRA")
suppressMessages(library(BCRA))
d <- data.frame(
  ID = 1:4,
  T1 = c(50, 45, 65, 40), T2 = c(55, 50, 70, 45),
  N_Biop = c(0, 1, 2, 0), HypPlas = c(99, 0, 1, 99),
  AgeMen = c(13, 11, 14, 12), Age1st = c(25, 30, 98, 22),
  N_Rels = c(0, 1, 2, 0), Race = c(1, 1, 1, 1)
)
r <- absolute.risk(d)
for (i in seq_len(nrow(d))) cat(sprintf("case%d %.6f\n", i, r[i]))
