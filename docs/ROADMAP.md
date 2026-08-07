# Roadmap

**Generated from `registry/models.yaml` — do not edit by hand.**
Regenerate with `python scripts/build_roadmap.py`.

30 models implemented; 29 verified against an independent source.

## Open cells

Disease × question pairs where a published equation exists and we have not
implemented one yet. Nothing is excluded: the exclusion this line used
to describe -- cells with no published equation at all -- no longer has
any members, so every one of the 36 counts.

| Disease | Question | What is known |
|---|---|---|
| Cervical cancer | prognosis | SEARCHED 2026-08-06; the 'have not been surveyed here' label no longer applies. Yoo et al, British Journal of Cancer 2012 (doi:10.1038/bjc.2012.340, PMID 22871885) is a genuine nomogram for overall survival across FIGO IA-IV on six covariates: FIGO stage, tumour size, age, histologic subtype, lymph node ratio, parametrial involvement. Concordance 0.723 optimism-corrected. Numerous SEER-based cervical nomograms also exist, with C-indices around 0.78-0.79. |
| Cervical cancer | response | CANDIDATES FOUND, but the ones located are radiomics and deep-learning nomograms for response to neoadjuvant chemotherapy, which need imaging-derived features rather than the routine clinical variables this library takes. Corrected 2026-08-06: the earlier note said no published equation existed. Searching properly found several. They are not implemented because of what they ARE, not because they are absent -- see below. That is a different kind of gap and should be described as one. |
| Colorectal cancer | response | CANDIDATES FOUND. Wang et al, Cancer Medicine 2024 (PMID 38819440) is the strongest: a dynamic nomogram for pathological complete response after neoadjuvant therapy in locally advanced rectal cancer, training n=1579 with an EXTERNAL validation cohort n=246, C-index 0.73 (0.70-0.75) internal and 0.78 (0.72-0.83) external. Predictors: pre-CRT CEA, histopathology, pre-CRT T and N stage, MRI EMVI, total neoadjuvant therapy. Corrected 2026-08-06: the earlier note said no published equation existed. Searching properly found several. They are not implemented because of what they ARE, not because they are absent -- see below. That is a different kind of gap and should be described as one. This one arguably DOES clear the bar and is the best next candidate in the repo. |
| Esophageal cancer | prognosis | SEARCHED 2026-08-06; the 'have not been surveyed here' label no longer applies. The best model found is strong: the AUGIS Survival Predictor (Ann Surg Oncol, PMC9831040), built on 6399 patients who underwent oesophagectomy in England and Wales 2012-2018, 5-year time-dependent AUC 83.9% (82.6-84.9), against 82.3% for Cox regression and 74.5% for TNM staging alone. Publicly deployed at uoscancer.shinyapps.io/AugisSurv. |
| Esophageal cancer | response | CANDIDATES FOUND. Liu et al, Cancer Medicine 2024 (PMC10935883) publishes a six-variable logistic nomogram for pathological complete response after neoadjuvant chemoradiotherapy in oesophageal squamous cell carcinoma, with odds ratios given and C-index 0.743 (0.686-0.800), n=293 single centre. Also a haematological-biomarker nomogram, C-index 0.75. Corrected 2026-08-06: the earlier note said no published equation existed. Searching properly found several. They are not implemented because of what they ARE, not because they are absent -- see below. That is a different kind of gap and should be described as one. The bar these do not clear is external validation and cohort size: 293 patients at one centre, against the thousands-to-millions behind the models we ship. |
| Gastric cancer | response | CANDIDATES FOUND. Several, including a nomogram from the Neo-CRAG phase III trial and a Chinese multicentre nomogram for pathological complete response after neoadjuvant chemotherapy plus immunotherapy. Corrected 2026-08-06: the earlier note said no published equation existed. Searching properly found several. They are not implemented because of what they ARE, not because they are absent -- see below. That is a different kind of gap and should be described as one. Most of the recent ones are radiomics or deep-learning nomograms needing CT-derived features we do not have as inputs, which is the real obstacle here. |
| Head & neck cancer | detection | CANDIDATE FOUND, and a strong one. The INHANCE Consortium published a general-population head-and-neck cancer risk model (Am J Epidemiol, doi:10.1093/aje/kwz259) giving 20-year absolute risk from age, sex, race, smoking, alcohol, sexual history and oral HPV; Smith et al, Head & Neck 2024 (doi:10.1002/hed.27834) adds an externally validated model. The previous note said no established general-population model was found. That was wrong -- it had not been searched for. |
| Head & neck cancer | response | SEARCHED 2026-08-06; the 'not searched exhaustively' label no longer applies. The strongest candidate is a pretreatment nomogram for response to induction chemotherapy in locally advanced hypopharyngeal carcinoma (Front Oncol 2020, PMC7761343) on four predictors -- age, T stage, haemoglobin, platelets -- AUC 0.860 (0.780-0.940). CT radiomics nomograms for laryngeal cancer also exist. |
| Ovarian cancer | response | KELIM is a nonlinear population-PK model, not closed-form |
| Pancreatic cancer | response | SEARCHED 2026-08-06; the 'not searched exhaustively' label no longer applies. Candidates exist. The strongest true response model is a contrast-enhanced ultrasound nomogram for neoadjuvant chemotherapy efficacy in borderline-resectable and locally advanced disease (Cancer Imaging 2024, doi:10.1186/s40644-024-00662-2), AUC 0.852 primary and 0.854 validation, on three predictors: taller-than-wide shape, time to peak enhancement, and peak tumour/normal ratio. Also found: a nine-variable chemotherapy-response nomogram for advanced and metastatic disease, C-statistic 0.74. |

## Unverified models

| Model | Blocked by |
|---|---|
| `cvd_statin_benefit` | derived_not_published |

## Standing work

- **Re-check flagship designations** where a cell now holds more than one
  model (cardiovascular detection has PREVENT and SCORE2; ovarian detection
  has RMI and ROMA). Which is the default deserves a fresh look.
- **Decide how to report the cells with no published equation** rather than
  carrying them as permanent to-dos. There are
  0 of them.

## Cells with more than one model

4 of 26. Each has one default; the others are
peers with a recorded reason to prefer them in some situations. Two of
these are not really contests at all — see the notes.

### Cardiovascular disease · detection

- `prevent` — **default**. Default. Newest (2024), largest development base, race-free by design, and it predicts five outcomes over two horizons rather than one. Choose SCORE2 instead for a European patient: the two are regional standards recalibrated to their own populations, so this is a question of where the patient is, not which model is better.
- `score2` — alternative. Prefer for European patients. It is the ESC standard and carries explicit recalibration for four European risk regions, which PREVENT does not. Not a lesser model -- a differently targeted one.

### Cardiovascular disease · prognosis

- `grace` — **default**. Default for the cell, but read the note: GRACE and CHA2DS2-VASc do not compete. GRACE estimates in-hospital mortality after an acute coronary syndrome. CHA2DS2-VASc estimates stroke risk in atrial fibrillation. Different patients, different questions; the cell 'cardiovascular prognosis' is simply too coarse to hold one answer.
- `cha2ds2_vasc` — alternative. Not an alternative to GRACE in any real sense -- it is the answer to a different question (stroke risk in atrial fibrillation, not mortality after acute coronary syndrome). Labelled this way only because the cell allows one default. Pick by population, never by this label.

### Ovarian cancer · detection

- `rmi` — **default**. Default, and the reason is availability rather than accuracy: RMI needs only ultrasound, menopausal status and CA-125, all routinely available, and is the RCOG-endorsed triage rule. ROMA needs an HE4 assay many centres do not run.
- `roma` — alternative. Prefer where HE4 is available and no ultrasound score is: ROMA needs no imaging. It is also assay-specific (Architect CA125 II, HE4 EIA) and its cut-offs do not transfer between platforms, which is the main reason it is not the default. Was previously marked 'catalog' with no reason recorded, which understated it -- it is implemented and verified.

### Prostate cancer · detection

- `pbcg` — **default**. Default. It separates high-grade (Gleason 7+) from any cancer, which is the question a biopsy decision actually turns on, and it fits eight sub-models so an incomplete record still gets a model rather than an imputed value. Discrimination is better too (AUC 75.5% internal). The caveat is real and is why ERSPC RC3 is kept: external validation found PBCG over-predicts in Black and other groups.
- `erspc_rc3` — alternative. Prefer where the European calibration is the relevant one, or where prostate volume is measured and PBCG's over-prediction in non-White groups is a concern. Its coefficients are also the ones recoverable from SWOP's own calculator, so it is the better-provenanced of the two.

## Models with no recorded discrimination

16 of 30. An AUC or C-index enters this registry only
from a paper actually read — the same rule as every coefficient — so these
are blank rather than filled from a search summary.

| Model | Year | Paper to read |
|---|---|---|
| `bcrat` | 1989 | https://pubmed.ncbi.nlm.nih.gov/2593165/ |
| `rmi` | 1990 | https://doi.org/10.1111/j.1471-0528.1990.tb02448.x |
| `msk_pancreatic` | 2004 | https://doi.org/10.1097/01.sla.0000133125.85489.07 |
| `abc_method` | 2005 | https://doi.org/10.1136/gut.2004.055400 |
| `msk_ovarian` | 2008 | https://doi.org/10.1016/j.ygyno.2007.09.019 |
| `roma` | 2009 | https://doi.org/10.1016/j.ygyno.2008.08.031 |
| `cvd_statin_benefit` | 2010 | https://pubmed.ncbi.nlm.nih.gov/21067804/ |
| `ang2010_rpa` | 2010 | https://doi.org/10.1056/NEJMoa0912217 |
| `dutasteride` | 2013 | https://pubmed.ncbi.nlm.nih.gov/23768723/ |
| `hap` | 2013 | https://pubmed.ncbi.nlm.nih.gov/23857958/ |
| `albi` | 2015 | https://doi.org/10.1200/JCO.2014.57.9151 |
| `predict_breast` | 2017 | https://doi.org/10.1186/s13058-017-0852-3 |
| `predict_breast_response` | 2017 | https://doi.org/10.1186/s13058-017-0852-3 |
| `lipi` | 2018 | https://pubmed.ncbi.nlm.nih.gov/29327044/ |
| `lipi_prognosis` | 2018 | https://pubmed.ncbi.nlm.nih.gov/29327044/ |
| `score2` | 2021 | https://doi.org/10.1093/eurheartj/ehab309 |

## How to help

See the Contributing section of the README. The single most valuable thing
you can send is a correction: if a coefficient here disagrees with its
source, open an issue with the citation and the exact table.
