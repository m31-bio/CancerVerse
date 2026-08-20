# Gastric cancer: response axis

The literature behind one empty cell, written down so the choice made from it
can be argued with.

Searched 2026-08-14. **28 papers**, 2018–2026, every PMID verified against
Europe PMC. The structured version is [`candidates.yaml`](candidates.yaml);
citation counts are refreshed by

    python scripts/rank_literature.py docs/literature/gastric-response --write

which writes [`ranked.csv`](ranked.csv). The method, and why it is ordered the
way it is, is in [`METHOD.md`](METHOD.md).

---

## The finding, in one line

The cell was never empty for lack of publications. It is empty because **the
papers with the best evidence do not print their model, and the paper that
prints its model in full has the weakest evidence.**

Nothing in the set has both a complete equation and an external cohort.

**Chosen: [Xu 2021, PMID 33937020](https://pmc.ncbi.nlm.nih.gov/articles/PMC8082104/)**,
registry id `xu_gastric_trg_score`, now showing in the coverage table. It is
the only one of the 28 that is computable exactly as published. It buys that by
giving up the probability: it outputs a risk group. Runner-up
[PMID 41883960](https://pmc.ncbi.nlm.nih.gov/articles/PMC13008680/) is the only
paper that can emit a probability and the only one whose coding direction
contradicts its own baseline table. That trade is open, see
[`PROVENANCE.md §3`](PROVENANCE.md).

---

## What is actually recoverable

Papers are grouped by what they print, because that, not the AUC, is what
decides whether a model can be implemented at all. **Bold** marks a paper with
a usable equation or public code.

### Complete model, probability computable

| Paper | PMID | Inputs | n | Validation | AUC | What is printed |
|---|---|---|---|---|---|---|
| **Xu 2021, Front Oncol** ← chosen | 33937020 | clinical + LN size on CT | 202 + 226 | internal split + **prospective, same centre** | 0.84 / 0.73 / **0.82** | integer points with a published cutoff — needs no intercept |
| **Hou 2026, Front Oncol** | 41883960 | routine clinical | 113 | bootstrap only | 0.848 | β, SE, OR, CI **and the intercept (3.081, SE 1.179)** |
| **BMC Cancer 2023** | 38012547 | pre/post-NAC CT ratios | 97 | **none** | 0.955 | full formula with intercept, but printed signs are inconsistent |

### Coefficients without an intercept: ranks patients, cannot state a probability

| Paper | PMID | Inputs | n | Validation | AUC |
|---|---|---|---|---|---|
| Liu 2023, BMC Cancer | 36631788 | routine clinical | 307 + 153 | internal split; the "external" cohort is never defined | C 0.842 / 0.806 / 0.760 |
| Neo-CRAG 2024, Cancer Med | 38523553 | routine clinical | 221 | bootstrap | 0.777 |
| Am J Cancer Res 2025 | 40371150 | CT measurements + serum | 304 + 208 | internal | 0.813 / 0.846 |
| Sci Rep 2025 | 41057487 | CT + ultrasound | 75 | 10-fold CV | 0.952 apparent |

This is the same failure mode that held the colorectal cell for three months.
See `colorectal_response_gap` in the registry: everything needed to rank
patients was published, the one constant needed to state a probability was not.

### Public code

| Paper | PMID | Repository | Why it still does not fit |
|---|---|---|---|
| **Cell Rep Med 2024 (iSCLM)** | 39637859 | `github.com/PengGao-cmu/iSCLM` | Takes CT volumes and whole-slide pathology, not variables. Best-evidenced model in the set — 1,208 development, two external cohorts, a 132-patient prospective cohort, AUC 0.846 prospectively, and unusable in a library whose inputs are clinical values. |

### Live calculator

| Paper | PMID | Calculator |
|---|---|---|
| **Cancer Manag Res 2026** | 41924230 | `prediction-123.shinyapps.io/Gastric_MPR_Predictor/` — Shiny, so the DynNom route that closed the colorectal cell may apply |

### Odds ratios only, or a nomogram figure and nothing else

PMIDs 40755776 (seven centres pooled then split 7:3, its own text calls that
external validation; AUC 0.934, and it prints no model), 32476803, 38196541, 40597721,
39995833, 41178868, 41417299, 35340629, 35280802, 38796795, 34141620, 40351845,
30210220, 40350424, 40128827, 34604085, 41062745, 37527475, 39001507.

---

## Ordered by how much each paper has been read

Citations per year, from OpenAlex, 2026-08-14. This ordering answers *"which of
these has been read"* and nothing else, read it beside the modality column,
because the top of this list is dominated by models this library cannot run.

| # | Paper | Year | Cites | /yr | Inputs | Equation? |
|---|---|---|---|---|---|---|
| 1 | eClinicalMedicine 2022 | 2022 | 180 | 36.0 | radiomics + DL | figure |
| 2 | Cell Rep Med 2024 (iSCLM) | 2024 | 28 | 9.3 | CT + WSI + DL | **code** |
| 3 | Chin J Cancer Res 2018 | 2018 | 74 | 8.2 | radiomics | none |
| 4 | J Transl Med 2025 | 2025 | 16 | 8.0 | delta-radiomics | figure |
| 5 | Front Oncol 2021 | 2021 | 31 | 5.2 | radiomics | figure |
| 6 | World J Gastroenterol 2020 | 2020 | 29 | 4.1 | clinical | OR only |
| 7 | Front Oncol 2022 | 2022 | 20 | 4.0 | radiomics | figure |
| 8 | Abdom Radiol 2024 | 2024 | 11 | 3.7 | radiomics + DL | figure |
| 11 | **Xu 2021, Front Oncol** | 2021 | 16 | 2.7 | clinical | **points** |
| 12 | **Liu 2023, BMC Cancer** | 2023 | 9 | 2.2 | clinical | β |
| 17 | Neo-CRAG 2024, Cancer Med | 2024 | 5 | 1.7 | clinical | β |
| 19 | **Hou 2026, Front Oncol** | 2026 | 1 | 1.0 | clinical | **intercept** |

Full 28-row ordering in [`ranked.csv`](ranked.csv).

The gap between rows 1–8 and rows 11–19 is the whole problem in one table. The
citation ranking and the usability ranking are close to **inverted**: what the
field reads is imaging models that withhold their weights, and what we can
implement is small single-centre papers nobody cites.

---

## A result worth keeping even though we will not implement it

PMID 35280802 is the only paper in the set that reports its own failure. Its CT
radiomics signature held at AUC 0.72–0.78 across chemotherapy regimens and fell
to **0.50, chance, in the apatinib + SOX cohort**. That is direct evidence
that response signatures are regimen-specific, and it is the reason not to treat
any single response model here as portable across treatment eras.

The companion observation, from PMID 41062745: its clinical-only submodel
reached AUC 0.824 / 0.813 / 0.804 against 0.903 / 0.899 / 0.895 for the full
radiomics model. About 0.09 AUC is what the entire segmentation pipeline buys.
In PMID 35340629 the same comparison goes the other way (clinical-only
0.518–0.626), so this does not generalise, but it is worth knowing that a
clinical-only gastric response model is not obviously hopeless.

---

## Caveats carried forward

- **Supplements not reached** for PMIDs 34141620 (S6, radscore formula),
  38796795 (S2, coefficients), 36631788 (possible intercept) and 40128827
  (possible coefficient table). Recorded at what the main text prints, which
  may understate them. Use `/paper-access` to resolve.
- **PMID 32476803**: several printed 95% CI lower bounds equal their point
  estimate (CEA 1.57 [1.57–2.01]). A reporting artefact in the source; those
  CIs are not usable.
- **PMID 38012547**: the printed logistic formula has internally inconsistent
  exponent signs, likely a typesetting sign loss. Must be checked against the
  PDF before anyone implements it.
- **PMID 41062745**: a printed external AUC (0.719) falls outside its own CI
  (0.721–0.986). Source error, unresolved.
- **PMID 37527475** predicts PET metabolic response, not pathological response.
  Kept in the list and flagged rather than dropped.
