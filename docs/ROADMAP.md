# Roadmap

**Generated from `registry/models.yaml`, do not edit by hand.**
Regenerate with `python scripts/build_roadmap.py`.

42 models implemented; 32 verified against an independent source.

## Open cells

Disease × question pairs where a published equation exists and we have not
implemented one yet. Nothing is excluded: the exclusion this line used
to describe, cells with no published equation at all, no longer has
any members, so every one of the 36 counts.

| Disease | Question | What is known |
|---|---|---|
| Head & neck cancer | response | SEARCHED 2026-08-06; the 'not searched exhaustively' label no longer applies. The strongest candidate is a pretreatment nomogram for response to induction chemotherapy in locally advanced hypopharyngeal carcinoma (Front Oncol 2020, PMC7761343) on four predictors, age, T stage, haemoglobin, platelets AUC 0.860 (0.780-0.940). CT radiomics nomograms for laryngeal cancer also exist. |
| Ovarian cancer | response | RE-CHECKED 2026-08-18 against each candidate's own source, superseding the 2026-08-17 search (which was itself the first real search this entry ever had, it previously carried one undated line about KELIM). Every rejection below is confirmed, two of them with detail the earlier pass did not have. (1) CRS 3 NOMOGRAM after neoadjuvant chemotherapy. Front Oncol 2020;10:560888, PMC7571668, 6 citations. Still the closest fit on inputs: four routine values (post-NACT CA-125, percent decrease in CA-125, post-NACT HE4, post-NACT haemoglobin) predicting chemotherapy response score 3 in tubo-ovarian high-grade serous carcinoma. CONFIRMED from the full text: n=106, CRS 3 in 24 (22.6%), Hosmer-Lemeshow P=0.272, four predictors on 24 events, about six events per predictor, below any accepted rule of thumb. TWO THINGS THE EARLIER NOTE MISSED. First, the paper reports its discrimination TWICE and inconsistently: the Abstract says "area under the curve = 0.82" while the Results say "the AUC value of this nomogram was 0.85 (95% CI 0.75-0.95)". Neither is wrong to quote, and anyone citing one should know the other exists. Second, and decisive, the paper does not merely lack external validation, it states that it could not do either kind: "the sample size of this work is only moderate, and it is difficult to conduct reliable internal and external validation", closing with "More studies are warranted to validate this model". A model whose authors say its internal validation is unreliable cannot be shipped as a flagship on the strength of its internal validation. A fresh Europe PMC sweep on 2026-08-18 found no external validation of it by anyone. (2) PLATINUM-RESISTANCE NOMOGRAM. World J Surg Oncol 2024;22(1):76, PMC10956367. Unchanged and still rejected outright on inputs: six of its eleven predictors are immunohistochemistry scores (CXCL1, CXCL2, IL6, ABCC1, LRP, BCL2). That is a tissue assay panel, the same obstacle as the radiomics models in the gastric, cervical and pancreatic response cells. Its reported C-index of 0.975 with external AUC 0.949, from eleven LASSO-selected predictors at one centre, is a reason for suspicion rather than for enthusiasm. (3) KELIM, the CA-125 elimination rate constant. Rejected before as "a nonlinear population-pharmacokinetic model, no closed form to transcribe". That was right and it was never actually tested against the deployed tool, which is the check that rescued erspc_rc3 from a dead Flash calculator and wang_larc_pcr from a Shiny app. It has now been run, and it fails for a stronger reason than "not printed". The calculator at biomarker-kinetics.org ships NO model to the browser. Its two JavaScript files are pure interface code; the computation is a 2.9 MB WebAssembly binary (assets/components/wasm_components_bg.wasm, compiled Rust) with a server-side compute API at api.biomarker-kinetics.org behind it. So there are exactly two ways to obtain the model: decompile the binary, or probe the API. NEITHER IS THE SAME ACT AS THIS LIBRARY'S EXISTING RECOVERIES, and the difference is the whole point. When erspc_rc3's constants came out of SWF bytecode, the same constants were printed in the source paper's appendix, so the recovery was corroboration of a published fact. Here nothing equivalent is published, so a decompiled binary would be the SOLE source, taking compiled expression rather than reading a fact, which is the wrong side of the Feist line this library's whole licensing position rests on (see docs/COMMERCIAL_USE_AUDIT.md). "KELIM" and "Biomarker Kinetics" are both claimed as trademarks, and the site's terms of use expressly disclaim any guarantee "that the use of the Results does not infringe the intellectual property rights of a third Party". Separately and independently: the input is a TIME SERIES of CA-125 values with dates, and the output requires per-patient Bayesian estimation against population parameters. No model in this library takes a time series, so even a lawfully obtained KELIM would not fit the API. Its prognostic value is real and continues to be validated, which is precisely why it is worth stating clearly that it is a tool we cannot reimplement rather than a model we have not found. |
| Pancreatic cancer | response | SEARCHED 2026-08-06; the 'not searched exhaustively' label no longer applies. Candidates exist. The strongest true response model is a contrast-enhanced ultrasound nomogram for neoadjuvant chemotherapy efficacy in borderline-resectable and locally advanced disease (Cancer Imaging 2024, doi:10.1186/s40644-024-00662-2), AUC 0.852 primary and 0.854 validation, on three predictors: taller-than-wide shape, time to peak enhancement, and peak tumour/normal ratio. Also found: a nine-variable chemotherapy-response nomogram for advanced and metastatic disease, C-statistic 0.74. |

## Unverified models

| Model | Blocked by |
|---|---|
| `cvd_statin_benefit` | derived_not_published |
| `atria_stroke_2013` | no_independent_reference_implementation |
| `bcsc_v2` | no_independent_reference_implementation |
| `xu_gastric_trg_score` | no_independent_reference_implementation |
| `chau_eg` | no_independent_reference_implementation |
| `shapiro_ncrt` | no_independent_reference_implementation |
| `iota_adnex` | no_independent_reference_implementation |
| `endpac` | no_independent_reference_implementation |
| `ukb_hnc` | no_independent_reference_implementation |
| `ang2010_rpa` | no_independent_reference_implementation |

## Standing work

- **Re-check flagship designations** where a cell now holds more than one
  model (cardiovascular detection has PREVENT and SCORE2; ovarian detection
  has RMI and ROMA). Which is the default deserves a fresh look.
- **Decide how to report the cells with no published equation** rather than
  carrying them as permanent to-dos. There are
  0 of them.

## Cells with more than one model

6 of 33. Each has one default; the others are
peers with a recorded reason to prefer them in some situations. Two of
these are not really contests at all, see the notes.

### Breast cancer · detection

- `bcsc_v2`. **default**. Replaces `bcrat` here, 2026-08-17. BCRAT's two hardest inputs, age at menarche and age at first live birth, are among the fields the target platform does not hold, so it cannot run on that data at all. This model instead asks for BI-RADS breast density (a field a screening centre already records), plus family history and biopsy history, each optional. this said "yes/no/unknown", which reads as an accepted value and is not one, passing the string "unknown" raises KeyError. Unknown is expressed by OMITTING the argument, which leaves the patient at the reference group rather than scoring them as a "no" (1.311% against 1.114% for a 55-year-old at density 2). That distinction matters on real EHR data, where both fields are frequently absent. Its concordance (0.66, Table 4 of the paper) is also modestly higher than BCRAT's pooled AUC (~0.60). THE VERSION LABEL WAS WRONG AND IS CORRECTED HERE, 2026-08-17. This entry used to be titled 'version 2.0' and cited the BCSC site's intro.htm as the authority for that. The page says the opposite. Fetched and read in full: "This is version 2.0 of the invasive breast cancer risk calculator" appears on a page that also says "In 2015, the BCSC risk calculator has been updated to include benign breast disease diagnoses and to estimate both five-year and ten-year breast cancer risk". So version 2.0 IS the 2015 update. What this module implements is Tice 2008, five-year risk only, with biopsy history as a bare yes/no, which is the calculator's version 1.0. Three independent checks agree, and each is cheap to redo. (1) The v2.0 software manifest on sourcecode.htm lists `bxresult_fmt.sas7bdat`, a biopsy-RESULT format table; this model has no biopsy-result axis at all. (2) v2.0 is described everywhere as five- AND ten-year; this model is five-year only. (3) The v3 lookup table's `biopsy_result` takes the six BBD levels (2 no prior biopsy, 3 benign unclassified, 4 non-proliferative, 5 proliferative without atypia, 6 proliferative with atypia, 7 LCIS) that v2 introduced, and none of them can be produced from this model's inputs. The registry id `bcsc_v2` is deliberately NOT renamed in the same edit: it is wired into `cancerverse_baseline.breast.detection.bcsc_v2`, its entrypoint, its test module and its parameter rows, and a rename is a separate change that should be made on purpose rather than as a side effect of a documentation fix. See `bcsc_v2_bbd_2015` for the real version 2.0, which is not implemented.
- `bcrat`. alternative. Kept implemented as the alternative rather than retired to catalog, which is what `rmi`, `roma`, `cha2ds2_vasc` and `erspc_rc3` all do after being superseded. It was briefly `status: catalog`, and the cost of that was concrete: `mb.predict("bcrat", ...)` raised, BCRAT left `list_models()` entirely, and the library's independently-checked count fell from 31/41 to 30/40, a breaking API change and a drop in verified coverage, in exchange for a tidier registry field. BCRAT is `parity_status: checked` against CRAN `BCRA` to 3.7e-07 percentage points and remains the comparator every paper in this field reports against. Why it is NOT the flagship: it needs age at menarche and age at first live birth, and the target platform holds neither, so on that data it returns nothing at all, 3,395 citations and no computable answer. Its concordance is also 0.58, barely above chance, against BCSC's 0.66. The swap trades a model verified against someone else's implementation for one that can actually run, and being runnable is the point.

### Cardiovascular disease · detection

- `prevent`. **default**. Default. Newest (2024), largest development base, race-free by design, and it predicts five outcomes over two horizons rather than one. Choose SCORE2 instead for a European patient: the two are regional standards recalibrated to their own populations, so this is a question of where the patient is, not which model is better.
- `score2`. alternative. Prefer for European patients. It is the ESC standard and carries explicit recalibration for four European risk regions, which PREVENT does not. Not a lesser model, a differently targeted one.

### Cardiovascular disease · prognosis

- `grace`. **default**. Default for the cell, but read the note: this cell holds TWO unrelated clinical questions and GRACE answers only the first. GRACE estimates in-hospital mortality after an acute coronary syndrome. The other three implemented-or-catalogued scores here. ATRIA, CHA2DS2-VASc, CHADS2, estimate stroke risk in atrial fibrillation. Different patients, different questions; the cell 'cardiovascular prognosis' is simply too coarse to hold one answer, and `role` has only one flagship slot to give. So GRACE holding `flagship` says nothing about the AF question. For that one the recommended score is atria_stroke_2013, decided 2026-08-14 on discrimination (0.73 vs CHA2DS2-VASc's 0.70, head-to-head), provenance (an open-access numbered table read directly, against MDCalc scraping) and completeness. CHA2DS2-VASc stays callable for guideline concordance, being 16x more cited. That decision is recorded in ATRIA's own flagship_note because the role field cannot carry it.
- `atria_stroke_2013`. **default**. Flagship for "Stroke risk in atrial fibrillation", decided 2026-08-14. Note the cell: cvd/prognosis carries TWO clinical questions, and GRACE is the flagship of the other one (mortality after acute coronary syndrome). They do not compete, and neither is an alternative to the other, see reporting.clinical_question for why the cell key has a third component. Why ATRIA over CHA2DS2-VASc, on three independent grounds. Discrimination: 0.73 against 0.70, head-to-head, both scored on the same patients in ATRIA's own cohort rather than each reporting its own. Provenance: ten values read directly from Table 3 of an open-access paper and transcribed twice. Completeness: nothing missing, no author to email. Its only extra cost is two routine values, a urinalysis flag and an eGFR. CHA2DS2-VASc stays implemented as the alternative on this question because it is 16x more cited (6,781 against 409) and is what the guidelines say, so an answer that has to be guideline-concordant, or legible to a reviewer who expects it, needs it. Use it for that, not because it is more accurate; it is not. af_stroke_lr_2026 would beat both at 0.88 but is blocked on a missing intercept. If it lands, it supersedes this.
- `cha2ds2_vasc`. alternative. The alternative on "Stroke risk in atrial fibrillation". Since 2026-08-14 the flagship of that question is atria_stroke_2013, which discriminates better (0.73 against 0.70, head-to-head on the same patients). Prefer ATRIA. Keep this one where the answer must be guideline-concordant, or legible to a reader expecting the familiar score, it is 16x more cited, and that is the reason to use it, not accuracy. Historical note, because the label used to say something else: this was previously recorded as an alternative to GRACE, which was never true in any real sense. GRACE answers mortality after acute coronary syndrome, a different question about different patients. It was labelled that way only because a cell allowed one flagship and cvd/prognosis holds two questions. The cell key now carries the question too, so the label finally matches the clinical reality.

### Lung cancer · detection

- `plcom2012`. **default**. Default for lung detection, and it stays the default even though optum_lung_lasso is newer, larger and fitted on records rather than questionnaires. PLCOm2012 decides screening eligibility in national guidelines, so it is what a clinician is answerable to and what any new lung model is measured against. The two answer different questions and neither replaces the other: this one needs pack-years, years since quitting and education level, which are survey fields, so it cannot be run over a panel without asking the patient.
- `optum_lung_lasso`. alternative. Deliberately NOT the flagship. It has the larger development cohort by two orders of magnitude and the better claim to work on data a hospital already holds, and it is still the wrong default: PLCOm2012 is written into screening guidelines, and a library whose lung default disagreed with the guideline would be answering a question nobody asked. This one is carried alongside as the EHR-native comparator, the thing a deployed model is actually competing with, and as the honest answer to "what can you run over the whole panel tonight".

### Ovarian cancer · detection

- `iota_adnex`. **default**. Default for ovarian detection since 2026-08-07, replacing RMI (1990). A 2026 prospective head-to-head on the same patients gives ADNEX 0.93 with CA-125 against RMI 0.88. It also returns five diagnoses rather than one score and a cut-off, which is the difference that matters clinically: a borderline tumour and a stage III cancer imply different surgery, and 'malignant' does not distinguish them.
- `rmi`. alternative. Kept as an alternative rather than removed: RMI needs only an ultrasound score, menopausal status and CA-125, so it still runs where the individual ultrasound features ADNEX wants were not recorded. ADNEX is the default, 0.93 against 0.88 on the same patients.
- `roma`. alternative. Prefer where HE4 is available and no ultrasound score is: ROMA needs no imaging. It is also assay-specific (Architect CA125 II, HE4 EIA) and its cut-offs do not transfer between platforms, which is the main reason it is not the default. Was previously marked 'catalog' with no reason recorded, which understated it, it is implemented and verified.

### Prostate cancer · detection

- `pbcg_extended`. **default**. Default for prostate detection since 2026-08-07, replacing the 2018 PBCG. The reason is licensing before recency: the 2018 coefficients were only machine-readable from riskcalc.org, whose source is PolyForm Noncommercial 1.0.0 and therefore unusable commercially. This version's full coefficient set is CC BY 4.0. It is also newer, covers 1,024 missing-data patterns instead of 8, and takes ten optional predictors instead of three.
- `erspc_rc3`. alternative. Prefer where the European calibration is the relevant one, or where prostate volume is measured and PBCG's over-prediction in non-White groups is a concern. Its coefficients are also the ones recoverable from SWOP's own calculator, so it is the better-provenanced of the two.
- `pbcg`. alternative. RETIRED as flagship 2026-08-07 and RESTORED to implemented/alternative 2026-08-18. The retirement rested on one sentence in docs/THIRD_PARTY_CODE.md, "a company repository is not a noncommercial purpose", which tested the wrong thing. PolyForm Noncommercial 1.0.0 gates on PURPOSE, not on entity: "any noncommercial purpose is a permitted purpose", with no exception for who is doing the using. M31 confirmed the project's use is academic research only, so the premise the retirement rested on no longer holds. See docs/ACADEMIC_USE_LICENSE_REVIEW.md. Two things that note used to say were also simply untrue, and are recorded here so the correction is not silent: it said "the implementation and its parity test are not published", while src/cancerverse_baseline/prostate/detection/pbcg.py has been published on GitHub since 2026-08-07. What was withheld was the vendor's R reference script, tests/parity/reference/pbcg_reference.R, not our own implementation, and that now ships too, under its own PolyForm notice. Why it is still NOT the flagship: `pbcg_extended` covers the same cell with coefficients published CC BY 4.0 as its own paper's supplement, four years newer, from the same consortium. That is a better source, independent of the licensing question. PBCG stays implemented because it is parity_status: checked, repro_tier A, and predicts three outcomes rather than one, and because retiring a verified model to `catalog` removes it from the public API entirely, which is a breaking change made for tidiness.

## Models with no recorded discrimination

4 of 42. An AUC or C-index enters this registry only
from a paper actually read, the same rule as every coefficient, so these
are blank rather than filled from a search summary.

| Model | Year | Paper to read |
|---|---|---|
| `rmi` | 1990 | https://doi.org/10.1111/j.1471-0528.1990.tb02448.x |
| `chau_eg` | 2004 | https://doi.org/10.1200/jco.2004.08.154 |
| `roma` | 2009 | https://doi.org/10.1016/j.ygyno.2008.08.031 |
| `score2` | 2021 | https://doi.org/10.1093/eurheartj/ehab309 |

## How to help

See the Contributing section of the README. The single most valuable thing
you can send is a correction: if a coefficient here disagrees with its
source, open an issue with the citation and the exact table.
