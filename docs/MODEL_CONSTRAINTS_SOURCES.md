# Where each flagship constraint comes from


For every load-bearing constraint claim in `docs/MODEL_CONSTRAINTS.md`, this
document gives the section, the page where the retrieved format actually
shows one, and the verbatim sentence. Sourced 2026-08-18 by one agent per
model, each following a PMC → Europe PMC → publisher retrieval ladder;
every quote below was then handed to a second, independent agent whose only
job was to re-fetch the same paper and try to refute it, catch a wrong
section, a misquoted sentence, or an invented page number. 29 of 34 models
cleared that adversarial pass outright (six quotes below were corrected after
the pass caught a real problem, and are marked).

**The remaining 5 models were finished on 2026-08-18 and all 34 are now
covered.** `cervical_cin_risk`, `cibula_arrm`, `msk_pancreatic`, `ukb_hnc` and
`ang2010_rpa` had 80 constraint claims sourced but not re-checked. Each source was re-fetched
independently and every one of those 80 quotes was matched against it as a
string, after normalising typography (curly quotes, en dashes, ≤/≥, non-
breaking spaces) and stripping citation markers. **80 of 80 matched.** Two
needed a look rather than a pass:

  * `cervical_cin_risk`'s four model-variant names are not in the article at
    all, they are column headers in Additional file 1 Table S1. Confirmed
    instead against `tests/parity/reference/cervical_table_s1.json`, the
    machine-readable extraction of that supplement already committed here,
    whose top-level keys are exactly `Base model`, `Base Model+E6`,
    `Base Model+Genotyping`, `Base Model+E6+Genotyping`.
  * `ukb_hnc`'s BMI quote read `(OR =0.96; ...)` against the publisher's
    `(OR=0.96; ...)`, a stray space, now corrected. The substance was right
    and is confirmed twice in the source, once in the Results sentence and
    once in Table III (`Body Mass Index 0.96 0.011 0.93 0.99`).

That check is an independent re-fetch and a verbatim match, not an adversarial
re-reading: it proves each quote appears in its paper, and does not by itself
prove the SECTION attributed to it is the right one.

**Every link below was re-checked by hand on 2026-08-18, after an earlier
draft of this document shipped links that were truncated mid-URL or pointed
at machine-only API endpoints instead of a page a person can open.** Three
were found broken on that recheck and are noted where it matters:
`msk_pancreatic`'s direct PDF link 404s (the PMC article page's own
"Download PDF" button is the way in instead); `ukb_hnc`'s original source
(a University of Liverpool repository file) refused two independent connection
attempts and has been replaced with the publisher's own page, confirmed
working; `kunzmann`'s repository link 301-redirects to a different host,
now given directly. Every entry below leads with **Full text:**, a link a
person can actually open, followed by **DOI:**, the permanent identifier.

**On page numbers, read this before asking why most entries have none.**
Only two of the 34 papers were retrieved in a form that has page numbers at
all. `amap` was read from the typeset article (pages 1369–1377 of
*J Hepatol* 2020;73(6):1368–1378) and `msk_pancreatic` from the PMC-hosted
Lippincott PDF (pages 293–298 of *Ann Surg* 2004;240(2)); those entries carry
a page number appended to the section, e.g. `DISCUSSION · p. 297`.

Every other paper came back as HTML or as PMC / Europe PMC JATS XML. Those
formats preserve section headings and lose pagination entirely, so there is no
page number to report and none is shown. An earlier draft printed
`no pagination in retrieved format` on all 160 such entries; that was a
non-answer repeated 160 times, and the section heading, often three levels
deep, e.g. `Methods > Statistical analyses > Model development`, already
locates the quote more precisely than a page number would. The honest options
were to say nothing or to invent a page from the citation's page range, and
inventing one produces a number that looks checkable and is not.

**What is deliberately not here.** About a third of the constraint bullets in
`MODEL_CONSTRAINTS.md` are not quotations from the paper at all, they come
from the deployed calculator's source code, from this repository's own
module docstrings, or are this repository's inference from data the paper
presents without stating the conclusion in prose. `docs/CONVENTIONS.md`
already draws that line for the equation source; the same line applies to
constraints, and claims on the wrong side of it are not forced into a quote
they do not have.

**Mechanical re-check, 2026-08-18.** Beyond the agent-vs-agent pass above,
every published quote was afterwards matched character-for-character against
the source text fetched independently. Europe PMC full-text XML for the open
papers, the NCBI abstract record for the closed ones, comparing
whitespace-insensitively after unescaping HTML entities and folding typographic
variants (thin spaces, en-dashes, `≥` vs `>or=`, Lancet's mid-dot decimals).
**Of the 151 quotes reachable that way, 145 matched exactly.** All six
remainders were inspected by hand and none was a misquotation: five differ only
in how the transcriber rendered a citation marker inside the sentence (`[12,13]`
written as `[,]`, a superscript `^1` dropped), and the sixth was the
cervical_cin_risk supplement entry now corrected above. The 41 quotes from the
five closed-access papers all matched their authoritative NCBI abstract
verbatim, and every one of them is attributed to an Abstract section, no quote
from those papers claims to come from a body section the retrieval could not
reach.

**Verification key.** ✓✓ confirmed against an independent second fetch of the
source. For 29 models that was an adversarial pass, a second agent trying to
refute the quote. For the five finished on 2026-08-18 (`cervical_cin_risk`,
`cibula_arrm`, `msk_pancreatic`, `ukb_hnc`, `ang2010_rpa`) it was a verbatim
string match against a fresh fetch, which is a weaker instrument: it proves the
sentence is in the paper, not that the section attributed to it is right. Both
are marked ✓✓ because both rest on a second, independent retrieval; the
distinction is stated here rather than hidden in a symbol.
No mark: sourced, not independently re-verified — **there are none left.**


## Prostate

### `pbcg_extended`: Extended PBCG (high-grade prostate cancer on biopsy)

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC9306143/
- DOI: https://doi.org/10.1186/s12874-022-01674-x
- Note: Additional file 1 (Table S1 + Fig. S1, age distribution): https://static-content.springer.com/esm/art%3A10.1186%2Fs12874-022-01674-x/MediaObjects/12874_2022_1674_MOESM1_ESM.docx

**Population is men referred for prostate biopsy, drawn from the Prostate Biopsy Collaborative Group across ten international cohorts.** ✓✓
- Section: Methods
- Quote: “The study was based on risk factor and outcome data collected from January 2006 to December 2019 from trans-rectal systematic 10–12 core biopsies from 10 PBCG cohorts spanning North America and Europe used for training and one PBCG European cohort used for validation (Figs. 1, 2, and S1).”

**The model is for a biopsy-referred population, not for screening in an unreferred population.** ✓✓
- Section: Methods
- Quote: “Included data came from patients who had received a prostate biopsy following a PSA test under local standard-of-care and may be seen as representative of patients in North America, including Puerto Rico, and Europe.”

**Outcome is high-grade / clinically significant prostate cancer, defined as Gleason grade group >= 2 found on biopsy.** ✓✓
- Section: Methods
- Quote: “Clinically significant prostate cancer was defined as Gleason grade group ≥ 2 on biopsy [13].”

**Age and PSA are mandatory inputs; the other ten predictors are optional.** ✓✓
- Section: Methods
- Quote: “For users of the developed risk calculator, two risk factors were mandatory: PSA and age. Ten risk factors were optional: DRE, prostate volume, prior negative biopsy, 5-alpha-reductase-inhibitor use, prior PSA screen (yes/no), African ancestry, Hispanic ethnicity, first- and second-degree prostate cancer- and first-degree breast cancer-family history.”

**The pattern of supplied optional predictors selects one of 1,024 fitted sub-models.** ✓✓
- Section: Results
- Quote: “To implement the prediction tool online, we fit 1,024 models to allow for all possible missing risk factor patterns among 10 risk factors in order to use the maximum prostate biopsies possible from the 10 PBCG cohorts. R code for all 1024 models is available at the Cleveland Clinic Risk Calculator library, https://riskcalc.org/ExtendedPBCG/, as well as in the Additional file 2.”

**Nothing is imputed at prediction time; a record missing predictors is scored by the model fitted on records having exactly the supplied set.** ✓✓
- Section: Methods
- Quote: “The available cases algorithm pooled individual level data from the training cohorts with information on the variables that the end-user had available, fit a main effects logistic regression model for clinically significant prostate cancer to the training data, and used the coefficients in a tailored prediction model for the target patient.”

**Sub-model sample sizes: the smallest (PSA + age) is fitted on 12,703 biopsies from 10 cohorts, the full 12-factor model on only 1,334 biopsies from 3 cohorts.** ✓✓
- Section: Results
- Quote: “The smallest model only contains PSA and age, utilizing all 12,703 biopsies from the 10 PBCG cohorts since these two risk factors were measured for all individuals. The largest model contains all 12 risk factors and was constructed from only 1,334 biopsies from 3 PBCG cohorts, as these were the only complete cases.”

**Histology / subtype / anatomic site restriction, and biopsy modality.** ✓✓
- Section: Abstract > Methods
- Quote: “Ten North American and European cohorts from the Prostate Biopsy Collaborative Group (PBCG) were used for fitting a risk prediction tool for clinically significant prostate cancer, defined as Gleason grade group ≥ 2 on standard TRUS prostate biopsy.”

**Explicit exclusion criteria.** ✓✓
- Section: Methods
- Quote: “MRI biopsies as well as prostate biopsies from patients with prostate cancer were excluded.”

**Explicit inclusion criteria.** ✓✓
- Section: Methods
- Quote: “The 10 cohorts used for training the model followed the PBCG prospective protocol in data collection, whereas the external validation cohort supplied retrospective data from a single institution that performs a high annual number of prostate biopsies to the PBCG [2, 3].”

**Stage or treatment-timing restriction.** ✓✓
- Section: Discussion
- Quote: “Men typically receive multiple PSA screening tests, the PBCG used the PSA most recent to but prior to the prostate biopsy.”

### `dutasteride`: Dutasteride chemoprevention

*open access / full text*
- Full text: https://www.frontiersin.org/journals/oncology/articles/10.3389/fonc.2012.00138/full

**Development population is the REDUCE trial biopsy cohort: 6729 men who had at least one biopsy or prostate surgery, split into dutasteride (N=3305) and placebo (N=3424) arms.** ✓✓
- Section: Materials and methods
- Quote: “Data from 6729 patients from the REDUCE trial who had at least one biopsy or prostate surgery were included in this study (Andriole et al., 2010). This cohort was split into two sub-groups: (1) patients who received dutasteride (N = 3305) and (2) patients who received placebo (N = 3424).”

**Population is men with a prior NEGATIVE prostate biopsy (the repo card's 'prior negative ... biopsy' scope).** ✓✓
- Section: Discussion
- Quote: “The REDUCE metagram can theoretically provide estimates of outcomes relevant to dutasteride treatment that are tailored to a man at risk for developing PCa (i.e., older men with elevated PSA and a history of previous negative biopsy).”

**Sex restriction: the model applies to men only.** ✓✓
- Section: Discussion
- Quote: “we have created a comprehensive prediction tool that can simultaneously predict the potential benefits and adverse effects of dutasteride treatment and help determine the appropriateness of chemoprevention for men at high risk for PCa”

**Histology / subtype restriction: outcome definitions are histologic and mutually conditioned, high-grade PCa is Gleason sum >=7; HGPIN counts only when no previous or concurrent ASAP or PCa; ASAP counts only in the absence of PCa.** ✓✓
- Section: Materials and methods
- Quote: “The pathological endpoints included PCa, high grade prostate cancer (HGPCa) that was defined as Gleason score sum ≥7, high grade prostatic intraepithelial neoplasia (HGPIN), and atypical small acinar proliferation (ASAP). In this study, HGPIN was counted as an independent endpoint only if there was no previous or concurrent ASAP or PCa. Similarly, ASAP was counted only in the absence of PCa.”

**Anatomic site restriction: prostate.** ✓✓
- Section: Materials and methods
- Quote: “Data from 6729 patients from the REDUCE trial who had at least one biopsy or prostate surgery were included in this study”

**Stage / treatment-timing restriction: the models are built at BASELINE, before dutasteride is started, in men without known prostate cancer (a prior negative biopsy), i.e. a chemoprevention decision point rather than a treatment-of-cancer decision.** ✓✓
- Section: Discussion
- Quote: “Furthermore, the nomograms for BPH-related outcomes (e.g., AUR, BPH-related surgery, and UTI) demonstrated reduced accuracy in the dutasteride cohort, likely due to modification of the value of baseline prostate-related markers by the drug itself. This shortcoming could be addressed by the construction of nomograms that incorporate post-treatment values for markers like urinary flow rate or prostate volume.”

**Stated units for every continuous input.** ✓✓
- Section: Results > Table 2 (Patient characteristics)
- Quote: “Prostate volume (cc)”

**Outcome definition: nine endpoints, each predicted twice (on and off dutasteride), giving 18 nomograms.** ✓✓
- Section: Abstract > Results
- Quote: “A total of 18 nomograms assessing the risks of cancer, high grade cancer, high grade prostatic intraepithelial neoplasia (HGPIN), atypical small acinar proliferation (ASAP), erectile dysfunction (ED), acute urinary retention (AUR), gynecomastia, urinary tract infection (UTI) and BPH-related surgery either on or off dutasteride were created.”

**HGPIN on dutasteride is a CONSTANT for everyone in scope (3.838831% in the repo), not a function of predictors.** ✓✓
- Section: Results
- Quote: “For the final metagram, these suboptimal nomograms were replaced by the overall cumulative incidence probabilities of the endpoint in question.”

**Four of the nine outcomes have concordance at or below chance in at least one arm, and the paper says so.** ✓✓
- Section: Results
- Quote: “Several of the nomograms (e.g., those for UTI, gynecomastia, HGPIN, ASAP) demonstrate poor discrimination and are based on those models that contained a large proportion of non-predictive variables. Values of less than 0.5 reflect poor discrimination by a given nomogram and are an artifact of random assignment of risk scores to patients.”

**Stated conditions under which the model is invalid or should not be relied on.** ✓✓
- Section: Discussion
- Quote: “Taken together, these considerations emphasize that nomogram predictions must be interpreted as such; they are not perfect and may not be applicable to all men at risk for PCa. By themselves, nomograms cannot make treatment recommendations nor can they take the place of patient counseling.”

**Model form constraint: continuous and ordinal predictors enter through restricted cubic splines, so extrapolation beyond the fitted range is not meaningful.** ✓✓
- Section: Materials and methods
- Quote: “Restricted cubic splines were implemented for continuous or ordinal variables to accommodate potential non-linear relationships.”

### `capra`: UCSF-CAPRA

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC2948569/
- DOI: https://doi.org/10.1097/01.ju.0000158155.33890.e7

**Population is preoperative and confined to clinically localized disease (repo card bullet 1, first half).** ✓✓
- Section: Methods > Patient cohort
- Quote: “We included patients diagnosed between 1992 and 2001 with clinically localized disease (clinical stage T1c-3a, N0/x, M0/x) who did not receive neoadjuvant or adjuvant radiation or hormonal therapy (N=2154).”

**Hard constraint: T1 / T2 / T3a only; T3b and T4 must raise an error.** ✓✓ *(corrected after verification)*
- Section: Discussion
- Quote: “Clinical T stage as assessed by digital rectal exam was not a significant predictor of outcome in our model except in the case of palpable extracapsular extension (stage cT3a) which raises the score by 1.”

**The code accepts any T1 or T2 substage (T1a, T1b included) as 0 points, matching Table 1's 'T1/T2' row.** ✓✓
- Section: Methods > Development of the UCSF Cancer of the Prostate Risk Assessment (UCSF-CAPRA)
- Quote: “T-stage as T1c, T2a, T2b, T2c, T3a”

**All five inputs (PSA, both Gleason patterns, T stage, % positive cores, age) are mandatory - none may be missing.** ✓✓
- Section: Methods > Patient cohort
- Quote: “We excluded patients with unknown PSA, Gleason score, clinical T-stage, or PPB.”

**Domain check on PSA is only 'PSA > 0 ng/mL'.** ✓✓
- Section: Methods > Patient cohort; Discussion
- Quote: “We also limited the analysis to patients with at least a sextant biopsy, PSA ≥2 ng/ml at diagnosis, and at least two follow-up PSAs or evidence of additional treatment more than 6 months after RP.”

**Domain check on Gleason patterns is 1-5 for both primary and secondary.** ✓✓
- Section: Methods > Development of the UCSF Cancer of the Prostate Risk Assessment (UCSF-CAPRA)
- Quote: “Gleason as 1-2/1-2, 1-2/3, 3/1-2, 3/3, 1-3/4-5, 4-5/1-3, 4-5/4-5”

**Domain check on percent positive cores is 0-100%.** ✓✓
- Section: Methods > Development of the UCSF Cancer of the Prostate Risk Assessment (UCSF-CAPRA)
- Quote: “PPB as <15%, 15-25%, 26-33%, 34-50%, 51-66%, 67-79%, ≥80%”

**Domain check on age is only 'age > 0'; age 0.5 and age 150 both produce a score.** ✓✓
- Section: Methods > Development of the UCSF Cancer of the Prostate Risk Assessment (UCSF-CAPRA)
- Quote: “age as <50, 50-54, 55-59, 60-64, 65-69, ≥70”

**Sex restriction: male only.** ✓✓
- Section: Abstract > Materials and Methods; Methods > The disease registry
- Quote: “We studied 1,439 men who had undergone radical prostatectomy and were followed in the CaPSURE database (a longitudinal, community-based disease registry of prostate cancer patients) diagnosed between 1992 and 2001 were included.”

**Histology / subtype / anatomic site restriction: prostate adenocarcinoma, biopsy-proven.** ✓✓
- Section: Methods > The disease registry
- Quote: “CaPSURE™ (Cancer of the Prostate Strategic Urologic Research Endeavor) is a longitudinal, observational database of men with biopsy-proven prostate adenocarcinoma, recruited from 40 primarily community-based urology practices across the United States.”

**Stage and treatment-timing restriction: score is computed before radical prostatectomy, in men who go on to RP as primary treatment and receive no neoadjuvant or adjuvant radiation or hormonal therapy.** ✓✓
- Section: Methods > Patient cohort; Abstract > Materials and Methods
- Quote: “who did not receive neoadjuvant or adjuvant radiation or hormonal therapy (N=2154)”

**Explicit inclusion criteria.** ✓✓
- Section: Methods > Patient cohort
- Quote: “As of July 2003, 10,018 patients were enrolled in CaPSURE. 4128 of these elected RP as primary treatment for their prostate cancer. We included patients diagnosed between 1992 and 2001 with clinically localized disease (clinical stage T1c-3a, N0/x, M0/x) who did not receive neoadjuvant or adjuvant radiation or hormonal therapy (N=2154).”

**Explicit exclusion criteria.** ✓✓
- Section: Methods > Patient cohort; rationale repeated in Discussion
- Quote: “We excluded patients with unknown PSA, Gleason score, clinical T-stage, or PPB. We also limited the analysis to patients with at least a sextant biopsy, PSA ≥2 ng/ml at diagnosis, and at least two follow-up PSAs or evidence of additional treatment more than 6 months after RP. 1439 patients meeting these criteria constituted our analytic dataset.”

**Stated units for every continuous input.** ✓✓
- Section: Methods > Variable definitions; Table 1 and Table 2 row labels
- Quote: “The prostate specific antigen (PSA) value used was the highest PSA value recorded in the nine months prior to diagnosis. 2002 clinical TNM stage was the highest reported from 1 month prior to 3 months after the date of diagnosis. Gleason scores were recorded from the diagnostic biopsy site with the highest total and highest primary scores. Percent positive biopsies (PPB) was calculated from detailed reported biopsy data.”

**Outcome definition.** ✓✓
- Section: Methods > Variable definitions
- Quote: “Disease recurrence after radical prostatectomy (RP) was defined as two consecutive PSA values ≥0.2 ng/ml at any time postoperatively or any additional treatment more than six months after RP. The date of recurrence was defined as the earlier of the second PSA ≥0.2 ng/ml or the date additional treatment was initiated. If disease recurrence did not occur, the patient's follow-up time was censored at the date of the last recorded PSA.”

**Prediction horizon.** ✓✓
- Section: Methods > Predictive performance of the CAPRA; Results
- Quote: “Life table and Kaplan-Meier analysis were used to determine the probability of DFS at 3 and 5 years for each CAPRA score level.”

**Output is a 0-10 integer point score.** ✓✓
- Section: Results
- Quote: “Points for each variable are totaled to yield a final CAPRA score of 0-10.”

**Any stated condition under which the model is invalid or must not be relied on.** ✓✓
- Section: Abstract > Conclusions; Conclusions
- Quote: “The UCSF-CAPRA score is a straightforward yet powerful preoperative risk assessment tool. It must be externally validated in future studies.”


## Cardiovascular

### `prevent`: AHA PREVENT

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC10910659/
- DOI: https://doi.org/10.1161/CIRCULATIONAHA.123.067626

**Age range of the development / validation cohort is 30-79 years.** ✓✓
- Section: Methods > Study Population
- Quote: “Individual-level participant data were included for adults aged 30 to 79 years without known ASCVD or HF at baseline.”

**Sex restriction: none, both sexes included, but the equations are sex-specific and sex is a required input (100 coefficient sets are sex-stratified).** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “For model development, sex-specific associations between risk factors (predictors) and total CVD (and each CVD subtype or outcomes) were estimated using Cox proportional hazards models adjusting for competing risk of non-CVD death.”

**Histology / subtype / anatomic site restriction (cardiology analogue: which CVD subtypes the equations cover).** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “Additional risk prediction equations were also developed for each CVD subtype: ASCVD (PREVENT-ASCVD) and HF (PREVENT-HF) and for each component of ASCVD (CHD and stroke).”

**Stage / treatment-timing restriction: primary prevention only, no known ASCVD or heart failure at baseline. The model is not valid for secondary prevention.** ✓✓
- Section: Methods > Study Population
- Quote: “Individual-level participant data were included for adults aged 30 to 79 years without known ASCVD or HF at baseline.”

**Explicit inclusion criteria (dataset level): US-based, measured key risk factors, minimum 95th-percentile follow-up of 5 years.** ✓✓
- Section: Methods > Study Population
- Quote: “For the current analysis, datasets were eligible for inclusion if they were US-based, had measured data on key risk factors of interest (systolic blood pressure [SBP], total cholesterol [TC], high density lipoprotein cholesterol [HDL-C], body mass index [BMI], and estimated glomerular filtration rate [eGFR]), and a minimum 95th percentile follow-up of 5 years.”

**Explicit exclusion criteria: missing predictor data, and extreme values of SBP, TC and HDL-C (SBP <90 or >200 mm Hg, TC <130 or >320 mg/dL, HDL-C <20 or >100 mg/dL).** ✓✓
- Section: Methods > Study Population
- Quote: “Individuals with missing data on predictors or extreme clinical ranges for SBP, TC, HDL-C, or BMI were excluded given the non-linear association with CVD and non-CVD death or pre-existing guideline-based clinical recommendations for treatment at these extreme values. For SBP, TC, and HDL-C, the cutoffs for exclusion were based on those utilized for the development of the PCEs (SBP<90 or >200 mm Hg, TC <130 or >320 mg/dL, and HDL-C <20 or >100 mg/dL).”

**Explicit exclusion criterion for BMI: <18.5 or >=40.0 kg/m2.** ✓✓
- Section: Methods > Study Population
- Quote: “For BMI, the excluded range was based on that utilized for the development of the Pooled Cohort Equations to Prevent Heart Failure (PCP-HF) models33 (<18.5 or ≥40.0 kg/m2).”

**Stated units for every continuous input.** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “For SBP, coefficients were modeled per 20 mm Hg for < and ≥110 mm Hg; for eGFR per -15 mL/min/1.73 m2 for < and ≥ 60 mL/min/1.73 m2; for BMI per 5 kg/m2 for < and ≥ 30 kg/m2.”

**Outcome definition: total CVD = composite of fatal and non-fatal ASCVD and HF; ASCVD = CHD (MI and fatal CHD) plus stroke.**
- Section: Methods > Outcome Ascertainment: Total CVD, CVD Subtypes, and Mortality
- Quote: “The primary outcome was incident total CVD, which was defined as a composite of fatal and non-fatal ASCVD and HF events.2, 34 ASCVD included coronary heart disease (CHD: myocardial infarction and fatal CHD) and stroke as a composite outcome similar to the PCEs.2”

**Prediction horizons: 10 years and 30 years, with competing-risk adjustment.** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “Absolute risk calculations accounting for non-CVD death as a competing cause were subsequently performed by combining the age- and sex-specific hazards of CVD and non-CVD death (each calculated from their baseline hazard, relative hazards, and risk factor levels) to estimate 10-year, and 30-year cumulative risk. These time horizons were selected as they have been employed previously in risk prediction models1, 2 and are currently recommended by the 2019 AHA/AHA Primary Prevention Guidelines1 to guide clinician-patient discussions.”

**BMI moves only the heart-failure outcome; BMI coefficients are zero for total CVD / ASCVD / CHD / stroke.** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “Given observational data demonstrating a robust independent association between obesity and incident HF, but not ASCVD, BMI was included as a predictor only in the HF-specific and death models; in contrast, given the limited association between cholesterol values and incident HF in prior studies, cholesterol was not included as a predictor in HF-specific and death models.54, 55”

**HbA1c enters with a diabetes interaction (separate slopes for diabetic and non-diabetic patients), as implemented by hba1c_dm / hba1c_no_dm.** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “In the equations with HbA1c, an interaction term with diabetes status was included.”

**SDI is entered as decile categories 1-3 / 4-6 / 7-10, and was derived only from a zip-code linkage available in a subset of datasets.** ✓✓
- Section: Methods > Measurement of Traditional and Novel Predictors
- Quote: “Analyses with SDI as a predictor were restricted to available OLDW datasets (36 datasets).”

**Regional restriction: US calibration; use SCORE2 for a European patient.** ✓✓
- Section: Methods > Study Population
- Quote: “For the current analysis, datasets were eligible for inclusion if they were US-based”

**Race-free by design: race and ethnicity are not predictors and must not be supplied.** ✓✓
- Section: Methods > Measurement of Traditional and Novel Predictors
- Quote: “Race and ethnicity variables are social constructs and, thus, were not considered as predictors in risk modeling to eliminate propagation of race-based risk algorithms and clinical care as recommended.35”

**eGFR must be computed with the CKD-EPI 2021 creatinine equation.** ✓✓
- Section: Methods > Measurement of Traditional and Novel Predictors
- Quote: “In all datasets, eGFR was calculated using the Chronic Kidney Disease Epidemiology Collaboration (CKD-EPI) 2021 creatinine equation,39 using standardized or calibrated serum creatinine.40”

**Development / validation cohort composition and size (registry records "46 datasets, 3,281,919 individuals").** ✓✓
- Section: Abstract > Methods
- Quote: “The derivation sample included individual-level participant data from 25 datasets (N=3,281,919) between 1992-2017.”

**Stated condition under which the model is invalid or unreliable.** ✓✓
- Section: Discussion > Limitations
- Quote: “Third, models were developed using age as the time scale. While this enables the flexibility of modeling longer-term estimates without requiring all datasets to have long-term follow-up, this may result in over-estimation of 30-year risk.”

**Equation source: the 100 coefficient sets live in Supplemental Tables S12.A-S12.J.** ✓✓
- Section: Results > Predicted 10- and 30-Year CVD Risk
- Quote: “Regression models were developed for translation and implementation of each of the models to estimate 10- and 30-year predicted risk for each outcome, which provided excellent approximations of predicted risk of CVD (R2 ≥ 0.99 for 10-year risk estimates and ≥0.97 for 30-year risk estimates) (Supplemental Table S12, A–J; and implemented on the AHA website at https://professional.heart.org/prevent).”

**Worked example anchoring the repo's parity test (registry cites Supplemental Table S25).** ✓✓
- Section: Results > Predicted 10- and 30-Year CVD Risk
- Quote: “For example, the estimated 10-year CVD, ASCVD, and HF risk for a 50-year old woman with the following risk factor profile (TC of 240 mg/dL, HDL-C of 55 mg/dL, no statin use, treated SBP of 160 mmHg, no diabetes, no smoking, BMI of 35 kg/m2, and eGFR 90 ml/min/1.73m2) was 5.4%, 3.6%, and 2.5%, respectively; if smoking, the predicted risk was estimated at 9.3%, 6.0%, and 4.7%, respectively.”

### `cvd_statin_benefit`: LDL-lowering absolute benefit

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC2988224/
- DOI: https://doi.org/10.1016/S0140-6736(10)61350-5

**The rate ratio for major vascular events is 0.78 (95% CI 0.76-0.80) per 1.0 mmol/L LDL-C reduction, as hard-coded in RATE_RATIO['major_vascular_events'].** ✓✓
- Section: Summary > Findings
- Quote: “similar proportional reductions in major vascular events per 1·0 mmol/L LDL cholesterol reduction were found in all types of patient studied (rate ratio [RR] 0·78, 95% CI 0·76–0·80; p<0·0001), including those with LDL cholesterol lower than 2 mmol/L on the less intensive or control regimen.”

**The rate ratio for all-cause mortality is 0.90 (95% CI 0.87-0.93) per 1.0 mmol/L LDL-C reduction, as hard-coded in RATE_RATIO['all_cause_mortality'].** ✓✓
- Section: Summary > Findings
- Quote: “Across all 26 trials, all-cause mortality was reduced by 10% per 1·0 mmol/L LDL reduction (RR 0·90, 95% CI 0·87–0·93; p<0·0001), largely reflecting significant reductions in deaths due to coronary heart disease (RR 0·80, 99% CI 0·74–0·87; p<0·0001) and other cardiac causes (RR 0·89, 99% CI 0·81–0·98; p=0·002)”

**CARD BULLET 3a, 'constant proportional effect' across baseline risk, which is what licenses multiplying the rate ratio onto an individual's baseline risk.** ✓✓
- Section: Discussion (final paragraph); also Summary > Findings and Results
- Quote: “Each 1 mmol/L LDL cholesterol reduction reduces the risk of occlusive vascular events by about a fifth, irrespective of baseline cholesterol concentration, which implies that a 2–3 mmol/L reduction would reduce risk by about 40–50%.”

**The effect compounds multiplicatively as RR raised to the LDL reduction (RR^delta), not linearly, the arithmetic the module implements.** ✓✓
- Section: Discussion (second paragraph)
- Quote: “which implies that, at least within the range of LDL cholesterol studied to date, a 2 mmol/L reduction would reduce the risk by about 40% (since the combination of risk ratios of 0·78×0·78 yields a risk ratio of about 0·6), and a 3 mmol/L reduction could reduce the risk by about 50%.”

**CARD BULLET 3b / scope_note, the trial effect is a ~5-year effect (median follow-up 4.8-5.1 years), which the repo then carries to a 10-year horizon.** ✓✓
- Section: Results (opening paragraphs)
- Quote: “the weighted median follow-up duration among survivors was 5·1 years (2·1 years for patients with acute coronary syndrome and 5·8 years for those with stable disease).”

**CARD BULLET 3c. CTT's endpoint is major vascular events, defined as coronary death, MI, revascularisation and stroke.** ✓✓
- Section: Methods > Study eligibility and outcomes
- Quote: “As in the first cycle of meta-analyses,^1 a major vascular event was defined as the first occurrence of any major coronary event, coronary revascularisation, or stroke.”

**Explicit INCLUSION criteria of the meta-analysis.** ✓✓
- Section: Methods > Study eligibility and outcomes
- Quote: “Trials were eligible for inclusion if: the main effect of the intervention was to lower LDL cholesterol; no other differences in risk factor modification were intended; and at least 1000 participants were to be recruited with at least 2 years' scheduled treatment duration.”

**Explicit EXCLUSIONS / data unavailable.** ✓✓
- Section: Results (second paragraph)
- Quote: “Individual participant data were unavailable from three eligible trials involving 11”

**STANDARD DIMENSION, sex restriction.** ✓✓
- Section: Results (subgroup paragraph)
- Quote: “In particular, there was a highly significant proportional risk reduction of 25% (99% CI 18–31; p<0·0001) per 1·0 mmol/L reduction in LDL cholesterol in participants with no previous history of vascular disease, as well as significant reductions of 17% (99% CI 10–24; p<0·0001) among women and of 16% (99% CI 3–27; p=0·002) in people older than 75 years at entry (figure 3).”

**STANDARD DIMENSION, stage / disease-severity / treatment-timing restriction.** ✓✓
- Section: Methods > Study eligibility and outcomes; Results (first two paragraphs)
- Quote: “only procedures resulting from recurrent ischaemia^23 or occurring more than 30 days after randomisation^24 (depending on the trial) were included.”

**STANDARD DIMENSION, stated units for every continuous input (the module accepts LDL reduction in mmol/L or mg/dL and converts at 38.67 mg/dL per mmol/L).** ✓✓
- Section: Results (baseline-LDL paragraph); Discussion (final paragraph)
- Quote: “Indeed, even among those reaching 1·8 mmol/L (70 mg/dL) or lower with a standard statin regimen, further reduction yielded definite benefit (RR 0·63, 99% CI 0·41–0·95; p=0·004; not shown separately in figure 4).”

**STANDARD DIMENSION, any stated condition under which the effect estimate is invalid or should not be extrapolated.** ✓✓
- Section: Discussion (second and third paragraphs); Summary > Interpretation
- Quote: “These findings suggest that the absolute reduction in cardiac mortality produced by lowering of LDL cholesterol with statin therapy in a given population depends chiefly on the absolute risk of death due to coronary occlusion.”

**The paper itself converts a proportional effect into an absolute benefit, and states for whom that absolute benefit is worth having, the closest the paper comes to sanctioning the module's arithmetic.** ✓✓
- Section: Discussion (haemorrhagic stroke paragraph)
- Quote: “the absolute size of the potential hazard would be about 50 times smaller (perhaps a few extra haemorrhagic strokes annually per 10”

### `grace`: GRACE 2003 in-hospital mortality

***closed access, abstract only***
- Full text: https://pubmed.ncbi.nlm.nih.gov/14581255/
- DOI: https://doi.org/10.1001/archinte.163.19.2345
- Note: abstract/MEDLINE record only, no open full text located

**Version-critical: this is the 2003 points nomogram for IN-HOSPITAL mortality, not the Fox BMJ 2006 6-month post-discharge score and not GRACE 2.0.** ✓✓
- Section: Abstract > Objective; Abstract > Conclusions
- Quote: “To develop a simple model to assess the risk for in-hospital mortality for the entire spectrum of ACS treated in general clinical practice.”

**Population: an acute coronary syndrome admission.** ✓✓
- Section: Abstract > Methods
- Quote: “A multivariable logistic regression model was developed using 11 389 patients (including 509 in-hospital deaths) with ACS with and without ST-segment elevation enrolled in the Global Registry of Acute Coronary Events (GRACE) from April 1, 1999, through March 31, 2001.”

**ACS subtype / anatomic-site restriction: the model covers the entire ACS spectrum, both with and without ST-segment elevation, i.e. no subtype restriction.** ✓✓
- Section: Abstract > Methods; Abstract > Conclusions
- Quote: “patients (including 509 in-hospital deaths) with ACS with and without ST-segment elevation”

**Stated unit for creatinine: mg/dL (multiply by 88.4 for umol/L).** ✓✓
- Section: Abstract > Results
- Quote: “serum creatinine level (OR, 1.2 per 1-mg/dL [88.4- micro mol/L] increase)”

**Stated unit for systolic blood pressure: mm Hg.** ✓✓
- Section: Abstract > Results
- Quote: “systolic blood pressure (OR, 1.4 per 20-mm Hg decrease)”

**Stated unit for heart rate: beats per minute.** ✓✓
- Section: Abstract > Results
- Quote: “heart rate (OR, 1.3 per 30-beat/min increase)”

**Stated unit for age: years.** ✓✓
- Section: Abstract > Results
- Quote: “age (odds ratio [OR], 1.7 per 10 years)”

**The model has exactly eight predictors: Killip class, SBP, heart rate, age, creatinine, cardiac arrest at admission, ST-segment deviation, elevated cardiac enzymes.** ✓✓
- Section: Abstract > Results
- Quote: “The following 8 independent risk factors accounted for 89.9% of the prognostic information: age (odds ratio [OR], 1.7 per 10 years), Killip class (OR, 2.0 per class), systolic blood pressure (OR, 1.4 per 20-mm Hg decrease), ST-segment deviation (OR, 2.4), cardiac arrest during presentation (OR, 4.3), serum creatinine level (OR, 1.2 per 1-mg/dL [88.4- micro mol/L] increase), positive initial cardiac enzyme findings (OR, 1.6), and heart rate (OR, 1.3 per 30-beat/min increase).”

**Outcome definition and prediction horizon: death during the index hospitalisation (in-hospital mortality); no time horizon beyond discharge.** ✓✓
- Section: Abstract > Objective; Abstract > Methods
- Quote: “To develop a simple model to assess the risk for in-hospital mortality”

**Development and validation cohort sizes and enrolment window (a treatment-era / timing constraint).** ✓✓
- Section: Abstract > Methods
- Quote: “Validation data sets included a subsequent cohort of 3972 patients enrolled in GRACE and 12 142 in the Global Use of Strategies to Open Occluded Coronary Arteries IIb (GUSTO-IIb) trial.”

**Discrimination: c-statistic 0.83 derivation, 0.84 confirmation GRACE, 0.79 GUSTO-IIb.** ✓✓
- Section: Abstract > Results
- Quote: “The discrimination ability of the simplified model was excellent with c statistics of 0.83 in the derived database, 0.84 in the confirmation GRACE data set, and 0.79 in the GUSTO-IIb database.”

### `atria_stroke_2013`: ATRIA stroke risk score

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC3698792/
- DOI: https://doi.org/10.1161/JAHA.113.000250

**Population is atrial fibrillation, and the model's purpose is the anticoagulation decision.** ✓✓
- Section: Abstract > Background
- Quote: “More accurate and reliable stroke risk prediction tools are needed to optimize anticoagulation decision making in patients with atrial fibrillation (AF).”

**Age enters through an age x prior-stroke interaction, not an age term plus a separate prior-stroke flag.** ✓✓
- Section: Methods > Statistical Analyses > Model derivation and internal validation in the original ATRIA cohort
- Quote: “On the basis of univariate analysis results in the derivation cohort, we also tested an additional interaction term of age by prior stroke.”

**Two disjoint score ranges result: 0-12 without prior stroke, 7-15 with one.** ✓✓
- Section: Results > Construction of the ATRIA Risk Score > Table 3 footnote
- Quote: “Possible point scores range from 0 to 12 for those without a prior stroke and from 7 to 15 for those with a prior stroke.”

**Output banding is <=5 low / 6 moderate / >=7 high, and these are the paper's own boundaries rather than a value the repo chose.** ✓✓
- Section: Results > Comparison of the ATRIA, CHADS2 and CHA2DS2-VASc Risk Scores
- Quote: “The ATRIA score was collapsed into low (0 to 5 points), moderate (6 points), and high (7 to 15 points) risk categories to fit annualized event rates of <1%, 1% to <2%, and ≥2% per year, respectively.”

**Age range of the development / validation cohort.** ✓✓
- Section: Methods > Cohort Assembly
- Quote: “We included all patients ≥18 years old with either 2 or more outpatient AF diagnoses (ICD‐9 code 427.31) or 1 outpatient AF diagnosis with ECG validation.”

**Histology / subtype / anatomic-site restriction - i.e. which kind of AF the score applies to.** ✓✓
- Section: Abstract > Methods and Results
- Quote: “The derivation ATRIA cohort consisted of 10 927 patients with nonvalvular AF contributing 32 609 person‐years off warfarin and 685 thromboembolic events (TEs).”

**Stage or treatment-timing restriction - the score estimates stroke risk in the ABSENCE of anticoagulation.** ✓✓
- Section: Methods > Cohort Assembly
- Quote: “We used only person‐time off warfarin to develop our stroke risk model.”

**Explicit inclusion criteria.** ✓✓
- Section: Methods > ATRIA-CVRN Cohort
- Quote: “The ATRIA‐CVRN study cohort is made up of 33 247 patients from Kaiser Permanente Northern California and also Kaiser Permanente Southern California aged 21 or older with incident atrial fibrillation (AF) or atrial flutter first diagnosed between January 2006 and June 2009 with confirmation by ECG or physician diagnosis in the electronic medical record.”

**Explicit exclusion criteria.** ✓✓
- Section: Methods > ATRIA-CVRN Cohort
- Quote: “Unlike the ATRIA cohort, the ATRIA‐CVRN cohort did not exclude patients with mitral stenosis or a history of a valve replacement in the mitral or aortic positions; such patients account for 1.5% of the ATRIA‐CVRN cohort.”

**Stated units for every continuous input.** ✓✓
- Section: Methods > Statistical Analyses > Model derivation and internal validation in the original ATRIA cohort
- Quote: “Age was categorized as <65, 65 to 74, 75 to 84, or ≥85 years old, and total white blood cell count was categorized as <8000, 8000 to 9999, or ≥10 000 per microliter. eGFR was dichotomized at ≥45 versus <45 mL/min per 1.73 m2 or ESRD.”

**Outcome definition.** ✓✓
- Section: Methods > Outcome Event Identification
- Quote: “Ischemic stroke was defined as sudden onset of a neurologic deficit lasting >24 hours and not attributable to other identifiable causes.13 Other thromboembolic events were considered valid if they met the following criterion: sudden occlusion of an artery to a visceral organ or extremity documented by imaging, surgery, or pathology and not attributable to concomitant atherosclerosis or other etiology.”

**Prediction horizon.** ✓✓
- Section: Methods > Outcome Event Identification
- Quote: “ATRIA cohort members were followed from their index date through September 2003.”

**Data-quality caveat on the proteinuria input: a large share of person-time had no measurement and was imputed as normal.** ✓✓
- Section: Methods > Statistical Analyses > Model derivation and internal validation in the original ATRIA cohort
- Quote: “The follow‐up periods that did not have a preceding laboratory measurement going back as far as 5 years were considered normal (ie, WBC<8000/μL, eGFR ≥60 mL/min per 1.73 m2, and no proteinuria). These imputed normal values accounted for 3.5% of the person‐years for WBC, 2.8% of the person‐years for eGFR, and 22.2% of the person‐years for proteinuria.”

**The repo's head-to-head discrimination claim: C-statistic 0.73 vs 0.70 for CHA2DS2-VASc and 0.69 for CHADS2, all scored in the same ATRIA cohort.** ✓✓
- Section: Results > Comparison of the ATRIA, CHADS2 and CHA2DS2-VASc Risk Scores
- Quote: “For the full range of point scores, the c‐index was 0.73 (95% CI, 0.71 to 0.75) for the ATRIA score, 0.69 (95% CI, 0.67 to 0.71) for the CHADS2 score, and 0.70 (95% CI, 0.68 to 0.72) for the CHA2DS2‐VASc score (Table 5, column B).”


## Breast

### `bcsc_v2`: BCSC breast density model

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC2674327/
- DOI: https://doi.org/10.7326/0003-4819-148-5-200803040-00004

**Lower age bound: the development cohort was restricted to women age 35 years or older.** ✓✓
- Section: Methods > Study Population
- Quote: “We included 1 095 484 women age 35 years or older who had had at least 1 mammogram with breast density measured by using the Breast Imaging Reporting and Data System (BI-RADS) classification system in any of the 7 mammography registries participating in the National Cancer Institute–funded Breast Cancer Surveillance Consortium (BCSC) (available at http://breastscreening.cancer.gov) (29).”

**Age range actually represented in the development/validation cohort.** ✓✓
- Section: Results > Table 1. Baseline Patient Characteristics
- Quote: “At the time of their earliest mammogram in the BCSC, 46% of women in our study were younger than age 50 years (Table 1).”

**Race: the model supports white / black / asian / hispanic only; American Indian / Alaska Native was excluded for inconsistent SEER rates (repo card bullet 2).** ✓✓
- Section: Methods > Model Development
- Quote: “Age-specific incidence rates for the Native American and Alaskan Native group were inconsistent in SEER, so we excluded this group from further analyses.”

**Density: BI-RADS categories 1-4 are the accepted input values.** ✓✓
- Section: Methods > Breast Density
- Quote: “Community radiologists at each site classified breast density on screening mammograms as part of routine clinical practice by using the American College of Radiology BI-RADS density categories (32): almost entirely fat (category 1), scattered fibroglandular densities (category 2), heterogeneously dense (category 3), and extremely dense (category 4).”

**Density: BI-RADS 2 is the reference category the model was standardised to.** ✓✓
- Section: Methods > Breast Density
- Quote: “The BI-RADS category 2 was used as the reference group for breast density because it formed the largest group.”

**The density relative hazards split at age 65 (a constraint the repo card does not state but the code implements via DENSITY_AGE_CUTOFF).** ✓✓
- Section: Methods > Model Development
- Quote: “The strength of the breast density association with breast cancer was greater for women younger than age 65 years (P for interaction < 0.001). Thus, separate models were fitted for women younger than age 65 years and for women age 65 years or older.”

**Outcome is INVASIVE breast cancer; DCIS is not an outcome.** ✓✓
- Section: Methods > Model Development
- Quote: “Women entered the model 6 months after the index mammogram and were censored at the time of death, diagnosis of ductal carcinoma in situ, or the end of follow-up.”

**Horizon: 5 years only; there is no 10-year extension for this version.** ✓✓
- Section: Abstract > Conclusion
- Quote: “A breast cancer prediction model that incorporates routinely reported measures of breast density can estimate 5-year risk for invasive breast cancer.”

**Missing-data policy: family_history=None / biopsy_history=None mean skip the multiplier, not impute an average.** ✓✓
- Section: Appendix Figure. The Breast Cancer Surveillance Consortium breast density model algorithm (closing paragraph)
- Quote: “The adjusted incidence is then multiplied by the hazard ratio based on the woman's mammographic density. If family history and breast biopsy status are unknown, no further calculations are done. If a woman has no first-degree relatives with breast cancer, the estimated incidence is multiplied by 0.938; if she has at least 1 first-degree relative, it is multiplied by 1.454.”

**Sex: women only. No parameter, no check.** ✓✓
- Section: Abstract > Patients
- Quote: “1 095 484 women undergoing mammography who had no previous diagnosis of breast cancer.”

**Explicit inclusion criteria.** ✓✓
- Section: Methods > Study Population
- Quote: “We included 1 095 484 women age 35 years or older who had had at least 1 mammogram with breast density measured by using the Breast Imaging Reporting and Data System (BI-RADS) classification system in any of the 7 mammography registries participating in the National Cancer Institute–funded Breast Cancer Surveillance Consortium (BCSC) (available at http://breastscreening.cancer.gov) (29).”

**Explicit exclusion criteria.** ✓✓
- Section: Methods > Study Population
- Quote: “We excluded women who had a diagnosis of breast cancer before their first eligible mammography examination. Because our goal was to develop a model of long-term risk for invasive breast cancer, we excluded women with cancer diagnosed in the first 6 months of follow-up to minimize the number of cases of cancer included in the model that were diagnosed on the basis of the mammogram used for risk assessment. Women were also excluded if they had breast implants.”

**Stated units for every continuous input.** ✓✓
- Section: Appendix Figure. The Breast Cancer Surveillance Consortium breast density model algorithm
- Quote: “The breast cancer incidence (per 100 000) for women age X years was modeled as follows:”

**Outcome definition and prediction horizon.** ✓✓
- Section: Discussion (summary paragraph)
- Quote: “In summary, we developed a risk prediction model that incorporates breast density to estimate a woman's 5-year risk for invasive breast cancer.”

**Any stated condition under which the model is invalid.** ✓✓
- Section: Discussion
- Quote: “No single model can address all needs in breast cancer risk assessment. For example, our breast density model does not adequately capture risk in women with a very strong family history of breast cancer and other diseases associated with hereditary breast cancer syndromes, such as ovarian cancer, prostate cancer, sarcomas, and thyroid disease. These patients should be identified and referred to genetic counselors for detailed pedigree analysis and for genetic testing when appropriate.”

**Model inputs are limited to five factors; other risk factors (notably BMI, and all Gail reproductive variables) are deliberately absent.** ✓✓
- Section: Methods > Measurement of Risk Factors
- Quote: “We selected 2 risk factors in addition to breast density for inclusion in the model on the basis of simplicity (yes or no) and a high attributable risk: history of breast cancer in a first-degree relative and history of a breast biopsy. Body mass index was later considered for addition to the model, but it was excluded to maintain parsimony and because it had minimal effect on model discrimination (the increase in the concordance statistic [c-statistic] was only 0.003).”

**Development/validation design and the sample the performance figures apply to.** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “We developed the model by using a random sample of 60% of the women and validated it in the remaining 40%.”

### `predict_breast`: PREDICT Breast v2.2 (prognosis)

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC5440946/
- DOI: https://doi.org/10.1186/s13058-017-0852-3

**ER status is structural, not a coefficient: ER-positive and ER-negative are fitted as separate models, so er_positive is a mandatory input.** ✓✓
- Section: Methods > Patient data > Statistical methods
- Quote: “Separate models were derived for ER-positive and ER-negative breast cancer.”

**Histology / subtype / anatomic site restriction: invasive breast cancer.** ✓✓
- Section: Methods > Patient data > Model development data
- Quote: “The primary analysis was based on data from patients with invasive breast cancer diagnosed in East Anglia, UK, between 1999 and 2003 identified by ECRIC.”

**Stage / treatment-timing restriction: surgically treated early breast cancer, adjuvant setting.** ✓✓
- Section: Methods > Patient data > Model development data
- Quote: “Patients who did not undergo surgery, patients with incomplete local therapy (wide local excision without radiotherapy) and patients with fewer than four nodes excised with a diagnosis of node-negative disease were excluded from the analyses, leaving a study population of 5738 individuals.”

**Explicit inclusion and exclusion criteria for the development cohort.** ✓✓
- Section: Methods > Patient data > Model development data
- Quote: “Information obtained from ECRIC included age at diagnosis, number of lymph nodes sampled and number of lymph nodes positive, tumour size, histological grade, ER status, mode of detection (screening vs. clinical), information on local therapy (wide local excision, mastectomy, radiotherapy), and type of adjuvant systemic therapy (chemotherapy, endocrine therapy, both). Exact chemotherapy regimens are unknown, but the majority of patients with breast cancer in the ECRIC population received first- or second-generation chemotherapy during this time period. Patients who did not undergo surgery, patients with incomplete local therapy (wide local excision without radiotherapy) and patients with fewer than four nodes excised with a diagnosis of node-negative disease were excluded from the analyses, leaving a study population of 5738 individuals. Of these 1977 (34%) had less than 10 years of potential follow-up.”

**Outcome definition and prediction horizon.** ✓✓
- Section: Methods > Patient data > Model development data
- Quote: “Vital status was ascertained at the end of June 2013, and all analyses were censored on 31 December 2012 to allow for delay in reporting of vital status. Breast cancer-specific mortality was defined as deaths where breast cancer was listed as the cause of death on part 1a, 1b or 1c of the death certificate.”

**Known residual miscalibration that should travel with the model as a caution.** ✓✓
- Section: Results > Model calibration
- Quote: “In contrast, PREDICT v2 slightly over-predicted the number of breast cancer deaths in women diagnosed under the age of 30 years (48 predicted vs. 34 observed, P = 0.047). Both PREDICT v1 and v2 tended to under-estimate breast cancer mortality in women with small ER-positive tumours and over-estimate mortality in women with larger ER-positive tumours.”

**Development cohort identity and validation strategy (registry cohort refitted with updated survival time; tested in three independent datasets).** ✓✓
- Section: Background
- Quote: “We have therefore re-fitted the PREDICT prognostic model using the original cohort of cases from East Anglia with updated survival time to take into account age at diagnosis and to smooth out the survival function for tumour size and node status. The fit of the model has been tested in three independent data sets that have also been used to validate the original version of PREDICT.”

### `predict_breast_response`: PREDICT Breast v2.2 (response)

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC5440946/
- DOI: https://doi.org/10.1186/s13058-017-0852-3

**ER status is structural, not a coefficient: ER-positive and ER-negative use different fractional-polynomial transforms, so er_positive is mandatory.** ✓✓
- Section: Methods > Patient data > Statistical methods
- Quote: “Separate models were derived for ER-positive and ER-negative breast cancer.”

**Adjuvant chemotherapy and hormone therapy effects are external (trial-derived), not fitted in this cohort.** ✓✓
- Section: Methods > Patient data > Statistical methods
- Quote: “The effects of adjuvant chemotherapy and adjuvant hormone therapy were constrained to the effects reported for standard anthracycline-based chemotherapy and adjuvant tamoxifen from an updated analysis of the Early Breast Cancer Trialists Collaborative Group [15].”

**Screen-detection is a predictor for ER-positive disease only (module sets ER-negative screen beta to 0).** ✓✓
- Section: Results
- Quote: “For ER-positive disease, age at diagnosis, tumour size, number of positive nodes, tumour grade and mode of detection were significant.”

**Histology / anatomic site restriction: invasive breast cancer.** ✓✓
- Section: Methods > Patient data > Model development data
- Quote: “The primary analysis was based on data from patients with invasive breast cancer diagnosed in East Anglia, UK, between 1999 and 2003 identified by ECRIC.”

**Stage / treatment-timing restriction: surgically treated early breast cancer, adjuvant setting.** ✓✓
- Section: Methods > Patient data > Validation samples
- Quote: “Patients diagnosed between 1990 and 2000 with unilateral stages I–III breast cancer without a previous cancer diagnosis (except non-melanoma skin cancer), for whom complete data on tumour size, nodal status, receipt of adjuvant systemic therapy, and follow-up were available, were included.”

**Explicit inclusion and exclusion criteria for the development cohort.** ✓✓
- Section: Methods > Patient data > Model development data
- Quote: “Patients who did not undergo surgery, patients with incomplete local therapy (wide local excision without radiotherapy) and patients with fewer than four nodes excised with a diagnosis of node-negative disease were excluded from the analyses, leaving a study population of 5738 individuals.”

**Stated units for every continuous input.** ✓✓
- Section: Results (Table 1)
- Quote: “Tumour size, mm”

**Outcome definition and prediction horizon.** ✓✓
- Section: Methods > Patient data > Model development data
- Quote: “Breast cancer-specific mortality was defined as deaths where breast cancer was listed as the cause of death on part 1a, 1b or 1c of the death certificate.”

**Stated conditions under which the model is invalid or unreliable.** ✓✓
- Section: Results > Model calibration
- Quote: “In contrast, PREDICT v2 slightly over-predicted the number of breast cancer deaths in women diagnosed under the age of 30 years (48 predicted vs. 34 observed, P = 0.047).”

**Follow-up completeness caveat on the 10-year estimate.** ✓✓
- Section: Methods > Patient data > Model development data
- Quote: “Of these 1977 (34%) had less than 10 years of potential follow-up.”


## Lung

### `plcom2012`: PLCOm2012

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC3929969/
- DOI: https://doi.org/10.1056/NEJMoa1211776

**Population: ever-smokers only; the model is not defined for never-smokers.** ✓✓
- Section: DISCUSSION
- Quote: “PLCOM2012 excluded persons who had never smoked. Additional unique predictors and models are required for prediction of lung-cancer risk among persons who have never smoked, and such models have not been developed. Generally, lung-cancer risk among persons who have never smoked is so low that low-dose CT screening of such persons is not currently warranted.”

**Age range of the development and validation cohort: 55-74 years; performance outside it is uncertain.** ✓✓
- Section: DISCUSSION
- Quote: “In both the PLCO and the NLST, an age between 55 and 74 years was an entry criterion. Therefore, the predictive performance of the PLCOM2012 outside this age range is uncertain, although most lung cancers occur in persons in this age range.”

**Histology / subtype / anatomic-site restriction on the predicted outcome.** ✓✓
- Section: METHODS > STUDY DESIGN
- Quote: “All histologically confirmed lung cancers that were diagnosed from study entry through 6 years of follow-up were included.”

**Outcome definition and prediction horizon: 6-year probability of a lung-cancer diagnosis.** ✓✓
- Section: Abstract > METHODS
- Quote: “risk was the probability of a diagnosis of lung cancer during the 6-year study period”

**Race/ethnicity: six fixed self-reported groups.** ✓✓
- Section: Table 2, footnote double-dagger
- Quote: “Race or ethnic group was self-reported.”

**Education is an ordinal 1-6 variable with fixed level definitions, centered on level 4.** ✓✓
- Section: Table 2, footnote section-sign
- Quote: “Education was measured in six ordinal levels: less than high-school graduate (level 1), high-school graduate (level 2), some training after high school (level 3), some college (level 4), college graduate (level 5), and postgraduate or professional degree (level 6).”

**Stated units for every continuous input (age, BMI, cigarettes/day, smoking duration, quit time).** ✓✓
- Section: Table 2, footnote dagger
- Quote: “Age was centered on 62 years, education was centered on level 4, body-mass index was centered on 27, duration of smoking was centered on 27 years, and smoking quit time was centered on 10 years.”

**The smoking-intensity input takes a specific nonlinear transform, (cpd/10)^-1 centered on 0.4021541613.** ✓✓
- Section: Table 2, footnote *
- Quote: “For smoking intensity, calculate the contribution of the variable to the model by dividing by 10, exponentiating by the power −1, centering by subtracting 0.4021541613, and multiplying this number by the beta coefficient of the variable.”

**Stated condition under which the model is invalid or unvalidated: outside the 55-74 age range.** ✓✓
- Section: DISCUSSION
- Quote: “Therefore, the predictive performance of the PLCOM2012 outside this age range is uncertain, although most lung cancers occur in persons in this age range.”

**Stated condition under which the model is invalid or unvalidated: population socioeconomic composition / generalizability.** ✓✓
- Section: DISCUSSION
- Quote: “The socioeconomic status of the PLCO study population was higher than that of the general population. 27 Although this might theoretically limit generalizability, because most of the predictors appear to have a biologic relationship with lung cancer that is independent of socioeconomic status, the model may still perform well. The PLCOM2012 should be evaluated in different populations and clinical and public health settings in well-designed prospective studies.”

**Development cohort size and composition as recorded by the repo: '80,375 ever-smokers in the control and intervention groups of the PLCO Cancer Screening Trial; validation set 37,332'.** ✓✓
- Section: Abstract > METHODS; Table 2 title; Table 3
- Quote: “We developed and validated the model (PLCOM2012) with data from the 80,375 persons in the PLCO control and intervention groups who had ever smoked.”

**Predictor values are questionnaire-reported at a single baseline, not measured or abstracted.** ✓✓
- Section: METHODS > STUDY DESIGN
- Quote: “Data on predictor variables were collected with the use of epidemiologic questionnaires administered at study entry.”

**The model applies to current AND former smokers (both, not one or the other), with smoking status as a binary predictor.** ✓✓
- Section: Introduction (final paragraph before METHODS)
- Quote: “The aims of the current study were to modify and update our lung-cancer model for current and former smokers to make it directly applicable to NLST data.”

**A risk threshold above which a person is 'positive' / eligible for screening.** ✓✓
- Section: Table 4, footnote double-dagger
- Quote: “According to the PLCOM2012 criteria, positivity was defined as a probability of lung cancer that was greater than 1.3455% over a period of 6 years.”

**This model is subject to a published correction.** ✓✓
- Section: Front matter (PMC article header, above the Abstract)
- Quote: “This article has been corrected. See the correction in volume 369 on page 394.”

### `lipi`: LIPI (response)

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC5885829/
- DOI: https://doi.org/10.1001/jamaoncol.2017.4771

**Population is advanced NSCLC, specifically patients receiving immune checkpoint inhibitors (the 'response' cell).** ✓✓
- Section: Methods > Patients
- Quote: “We conducted a multicentric retrospective study of a cohort of 466 patients with advanced NSCLC receiving treatment with PD-1/PD-L1 inhibitors in a variety of settings covering routine clinical care, expanded access, and compassionate-use programs, as well as clinical trials (nivolumab, pembrolizumab, atezolizumab, durvalumab, and durvalumab-ipilimumab).”

**LDH is compared against the reporting lab's own upper limit of normal; there is no universal cutoff.** ✓✓
- Section: Methods > Patients
- Quote: “The cutoff for dNLR was greater than 3 (according to the cutoff from the largest published study with ICIs in patients with cancer), and the ULN for LDH was defined according the limit of each center.”

**dNLR = neutrophils / (leukocytes - neutrophils), i.e. the denominator is the non-neutrophil white count, not the lymphocyte count.** ✓✓
- Section: Introduction
- Quote: “derived neutrophil to lymphocyte ratio (dNLR; absolute neutrophil count/[white blood cell concentration − absolute neutrophil count])”

**Output is a 0-2 integer score mapping to three ordinal groups (good / intermediate / poor).** ✓✓
- Section: Methods > Patients
- Quote: “The LIPI was developed on the basis of dNLR greater than 3 and LDH greater than ULN, characterizing 3 groups (good, 0 factors; intermediate, 1 factor; poor, 2 factors).”

**The model's evidence is group separation: median OS 34 / 10 / 3 months for good / intermediate / poor.** ✓✓
- Section: Abstract > Results
- Quote: “Median OS for poor, intermediate, and good LIPI was 3 months (95% CI, 1 month to not reached [NR]), 10 months (95% CI, 8 months to NR), and 34 months (95% CI, 17 months to NR), respectively, and median PFS was 2.0 (95% CI, 1.7-4.0), 3.7 (95% CI, 3.0-4.8), and 6.3 (95% CI, 5.0-8.0) months (both P < .001).”

**Age range of the development / validation cohort.** ✓✓
- Section: Abstract > Results
- Quote: “median age at diagnosis was 62 (range, 29-86) years”

**Histology / subtype / anatomic site restriction.** ✓✓
- Section: Abstract > Results
- Quote: “270 (58%) had adenocarcinoma and 159 (34%) had squamous histologic subtype”

**Stage and treatment-timing restriction.** ✓✓
- Section: Results > Pooled LIPI Population
- Quote: “The median number of prior lines of therapy administered before ICI therapy was 1 (range, 0-11).”

**Explicit exclusion criteria.** ✓✓
- Section: Results > Lung Immune Prognostic Index (LIPI)
- Quote: “Thirty-seven patients without baseline LDH or dNLR were excluded from the LIPI analysis.”

**Timing window for the baseline laboratory inputs.** ✓✓
- Section: Methods > Patients
- Quote: “Complete blood cell counts, LDH, and albumin levels at baseline before ICI treatment (within 30 days before the first treatment) were extracted from electronic medical records.”

**Stated units for every continuous input.** ✓✓
- Section: Results > Pooled LIPI Population
- Quote: “Median LDH was 248.5 U/L (interquartile range, 189-350 U/L; to convert to microkatals per liter, multiply by 0.0167)”

**Outcome definition.** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “Disease control rate (DCR) was defined as complete plus partial response plus stable disease, and overall response rate as complete plus partial response. Overall survival was calculated from the date of first immunotherapy administration until death due to any cause. Progression-free survival (PFS) was calculated from the date of first immunotherapy administration until disease progression or death due to any cause.”

**Any stated condition under which the model is invalid.** ✓✓
- Section: Discussion
- Quote: “On the other hand, LIPI was not associated with outcome in patients treated with chemotherapy only, providing support that it might be a predictor of benefit from ICI, a hypothesis that requires prospective validation.”

### `lipi_prognosis`: LIPI (prognosis)

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC5885829/
- DOI: https://doi.org/10.1001/jamaoncol.2017.4771

**Population: advanced NSCLC, in patients receiving PD-1/PD-L1 immune checkpoint inhibitors.** ✓✓
- Section: Methods > Patients
- Quote: “We conducted a multicentric retrospective study of a cohort of 466 patients with advanced NSCLC receiving treatment with PD-1/PD-L1 inhibitors in a variety of settings covering routine clinical care, expanded access, and compassionate-use programs, as well as clinical trials (nivolumab, pembrolizumab, atezolizumab, durvalumab, and durvalumab-ipilimumab).”

**The score itself: dNLR > 3 and LDH > ULN, giving three groups (good 0 / intermediate 1 / poor 2).** ✓✓
- Section: Methods > Patients (final paragraph, immediately before 'Statistical Analysis')
- Quote: “The LIPI was developed on the basis of dNLR greater than 3 and LDH greater than ULN, characterizing 3 groups (good, 0 factors; intermediate, 1 factor; poor, 2 factors).”

**LDH is compared to the reporting lab's own upper limit of normal; there is no universal cutoff.** ✓✓
- Section: Methods > Patients (final paragraph)
- Quote: “The cutoff for dNLR was greater than 3 (according to the cutoff from the largest published study with ICIs in patients with cancer), and the ULN for LDH was defined according the limit of each center.”

**dNLR = neutrophils / (leukocytes - neutrophils), the 'derived' ratio, which needs no lymphocyte count.** ✓✓ *(corrected after verification)*
- Section: Introduction (second paragraph)
- Quote: “Novel potential biomarkers such as the neutrophil to lymphocyte ratio (NLR) and derived neutrophil to lymphocyte ratio (dNLR; absolute neutrophil count/[white blood cell concentration − absolute neutrophil count]) have been investigated to measure inflammatory status in various cancers, including NSCLC.”

**Separation evidence: median OS 34 / 10 / 3 months for good / intermediate / poor.** ✓✓
- Section: Abstract > Results (restated in Results > Test Set > Lung Immune Prognostic Index (LIPI))
- Quote: “Median OS for poor, intermediate, and good LIPI was 3 months (95% CI, 1 month to not reached [NR]), 10 months (95% CI, 8 months to NR), and 34 months (95% CI, 17 months to NR), respectively, and median PFS was 2.0 (95% CI, 1.7-4.0), 3.7 (95% CI, 3.0-4.8), and 6.3 (95% CI, 5.0-8.0) months (both P < .001).”

**Age range of the development / validation cohort.** ✓✓
- Section: Abstract > Results
- Quote: “median age at diagnosis was 62 (range, 29-86) years”

**Histology / subtype restriction.** ✓✓
- Section: Results > Pooled LIPI Population (subgroup paragraph)
- Quote: “regardless of histologic subtype”

**Treatment-timing restriction: the inputs are baseline, pre-treatment values.** ✓✓
- Section: Methods > Patients (second paragraph)
- Quote: “Complete blood cell counts, LDH, and albumin levels at baseline before ICI treatment (within 30 days before the first treatment) were extracted from electronic medical records.”

**Line-of-therapy restriction.** ✓✓
- Section: Results > Pooled LIPI Population
- Quote: “The median number of prior lines of therapy administered before ICI therapy was 1 (range, 0-11).”

**Stated exclusion: patients without a baseline LDH or dNLR are not scoreable.** ✓✓
- Section: Results > Test Set > Lung Immune Prognostic Index (LIPI)
- Quote: “Thirty-seven patients without baseline LDH or dNLR were excluded from the LIPI analysis.”

**Stated units for LDH.** ✓✓
- Section: Results > Pooled LIPI Population (and Table 1 footnote)
- Quote: “Median LDH was 248.5 U/L (interquartile range, 189-350 U/L; to convert to microkatals per liter, multiply by 0.0167)”

**Outcome definition.** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “Overall survival was calculated from the date of first immunotherapy administration until death due to any cause. Progression-free survival (PFS) was calculated from the date of first immunotherapy administration until disease progression or death due to any cause.”

**Condition under which the model does not apply: patients treated with chemotherapy alone.** ✓✓
- Section: Results > Chemotherapy Cohort
- Quote: “No correlation was observed in the control cohort between dNLR or LDH and OS or PFS.”

**Acknowledged failure mode: the poor group is not a reliable rule-out.** ✓✓
- Section: Limitations
- Quote: “Finally, some patients from the poor LIPI group achieved clinical benefit—possibly because automated neutrophil counts do not discriminate between the different subpopulations of neutrophils that could have protumor or antitumor functions.”

**Setting and geography of the development data.** ✓✓
- Section: Abstract > Design, Setting, and Participants
- Quote: “Multicenter retrospective study with a test (n = 161) and a validation set (n = 305) treated with programmed death 1/programmed death ligand 1 (PD-1/PD-L1) inhibitors in 8 European centers, and a control cohort (n = 162) treated with chemotherapy only.”


## Colorectal

### `crc_pro`: CRC-PRO

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC4219857/
- DOI: https://doi.org/10.3122/jabfm.2014.01.130040

**The model is two entirely different models by sex, not one model with a sex term.** ✓✓
- Section: Methods
- Quote: “Because of the potential differences in risk between men and women, we decided to create separate risk calculators for men and women to keep the models simple while allowing the greatest flexibility in the selection of variables without increasing the work required by the end user.”

**The two sexes have different predictor sets: women get NSAIDs and estrogen; men get red meat, physical activity and aspirin.** ✓✓
- Section: Abstract > Results
- Quote: “The final model for men contained age, ethnicity, pack-years of smoking, alcoholic drinks per day, body mass index, years of education, regular use of aspirin, family history of colon cancer, regular use of multivitamins, ounces of red meat intake per day, history of diabetes, and hours of moderate physical activity per day. The final model for women included age, ethnicity, years of education, use of estrogen, history of diabetes, pack-years of smoking, family history of colon cancer, regular use of multivitamins, body mass index, regular use of nonsteroidal anti-inflammatory drugs, and alcoholic drinks per day.”

**The paper is explicit that NSAIDs matter for women but not men (repo docstring presents this as a quotation).** ✓✓
- Section: Results
- Quote: “The regular use of NSAIDs was an important predictor for women but not for men, whereas a personal history of cancer was not an important predictor variable for either sex.”

**Ethnicity levels are Hawaiian / Japanese / Latino / White / Black.** ✓✓
- Section: Methods
- Quote: “primary race/ethnicity (black, Hawaiian, Japanese, Latino, or white)”

**Development population is the Multi-Ethnic Cohort only.** ✓✓ *(corrected after verification)*
- Section: Methods (Table 2, general note)
- Quote: “The Multiethnic Cohort study enrolled an ethnically diverse mix of residents from Hawaii and California between 1993 and 1996.”

**Estrogen (and NSAID, and aspirin) is a three-level variable: currently / previously / no.** ✓✓
- Section: Methods
- Quote: “regular aspirin use (currently, previously, or no); family history of colon cancer (dichotomous); estrogen use (currently, previously, or no)”

**Age range of the development cohort.** ✓✓
- Section: Introduction (untitled body text preceding Methods)
- Quote: “The MEC is a large, prospective survey of a diverse population of residents from California and Hawaii who are >45 years old.”

**Sex restriction.** ✓✓ *(corrected after verification)*
- Section: Methods (Table 2 A/B)
- Quote: “Table 2. A. Descriptive Statistics for Men by Colorectal Cancer Outcome in the Multiethnic Cohort Study (n = 80,062).”

**Explicit inclusion and exclusion criteria.** ✓✓
- Section: Methods
- Quote: “Individuals with a history of CRC or adenomatous polyps were excluded from the analysis, resulting in a final sample size of 180,630 patients, of whom 2762 developed CRC.”

**Stated units for every continuous input.** ✓✓
- Section: Methods; Table 2 footnotes; Table 4
- Quote: “daily alcohol intake (continuous); regular multivitamin usage (currently, previously, or no); hours of moderate or strenuous activity per day (continuous); primary race/ethnicity (black, Hawaiian, Japanese, Latino, or white); diabetes (dichotomous); years of education (continuous); pack-years of smoking (continuous); regular use of nonsteroidal anti-inflammatory drugs (NSAIDS) (currently, previously, or no); intake (in ounces) of red meat per day (continuous)”

**Outcome definition and prediction horizon (10-year colorectal cancer risk).** ✓✓
- Section: Results > Figure 1A legend
- Quote: “The 10-year risk of colorectal cancer (CRC) is identified where a line drawn straight down from the “total points” axis intersects the “10-year risk of CRC (%).””

**Interpretive caveat the paper attaches to the model: years of education has a non-monotonic (U-shaped / J-shaped) relationship with risk.** ✓✓
- Section: Results > Figure 1A legend
- Quote: “Please note that the “years of education” variable has a U-shaped relationship with the 10-year risk of CRC. That is, the lowest risk of CRC occurs at 8 years and increases as you move along the top of the axis from left to right until reaching the highest risk at 14 years, and then it decreases along the bottom of the axis as you move to the left from 14 to 16 years.”

**Validation status limiting applicability: internal cross-validation only, no external validation.** ✓✓
- Section: Abstract > Conclusion
- Quote: “This calculator seems to be accurate, is user friendly, and has been internally validated in a diverse population.”

### `wang_larc_pcr`: Wang 2024 pCR nomogram

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC11141331/
- DOI: https://doi.org/10.1002/cam4.7251

**Population is locally advanced rectal cancer staged BEFORE chemoradiotherapy, in patients who go on to complete nCRT and surgery.** ✓✓
- Section: 2. MATERIALS AND METHODS > 2.1. Patients
- Quote: “Inclusion criteria: (1) Patients with a pathologically confirmed diagnosis of rectal cancer; (2) clinical stage of cII or cIII (cT3–4 N0–2 M0) (Based on AJCC staging system, phase 8); (3) distance to the anal verge ≤15 cm; (4) received nCRT combined with total mesorectal excision (TME) and postoperative adjuvant chemotherapy if necessary; (5) complete clinicopathological features, imaging, follow‐up, and clinical data.”

**All six model inputs are pre-CRT (pre-treatment) values; post-treatment yp staging is a different question.** ✓✓
- Section: 3. RESULTS > 3.3. Nomogram for pCR
- Quote: “Final formula for the nomogram = 22.0 × Pre‐CRT N stage (N0 = 2, N1 = 1, N2 = 0) + 15.0 × Pre‐CRT T stage (T1 = 3, T2 = 2, T3 = 1, T4 = 0) + 70.0 × Pre‐CRT MRI_EMVI (Negative = 1, Positive = 0) + 55.0 × Total neoadjuvant therapy (Yes = 1, No = 0) + 100 × Histopathology (Adenocarcinoma = 1, Signet‐ring cell carcinoma/Mucinous adenocarcinoma = 0) + 3.85 × Pre‐CR CEA (≥24 = 0).”

**The intended moment of use is before treatment decisions are made.** ✓✓
- Section: 1. INTRODUCTION
- Quote: “This study aimed to address the factors associated with obtaining a pCR in LARC patients treated with nCRT and develop a web‐based dynamic nomogram for predicting pCR before making treatment decisions.”

**CEA has an explicit '≥ 24' floor in the published points formula.** ✓✓
- Section: 3. RESULTS > 3.3. Nomogram for pCR
- Quote: “3.85 × Pre‐CR CEA (≥24 = 0)”

**Development was two Chinese centres; transportability beyond them is untested.** ✓✓
- Section: 4. DISCUSSION (limitations paragraph)
- Quote: “Third, this study was limited to two large colorectal treatment centers in China, which is a regional limitation.”

**Histology / subtype restriction.** ✓✓
- Section: 2. MATERIALS AND METHODS > 2.1. Patients
- Quote: “(1) Patients with a pathologically confirmed diagnosis of rectal cancer;”

**Anatomic site restriction.** ✓✓
- Section: 2. MATERIALS AND METHODS > 2.1. Patients
- Quote: “(3) distance to the anal verge ≤15 cm;”

**Stage restriction.** ✓✓
- Section: 2. MATERIALS AND METHODS > 2.1. Patients
- Quote: “(2) clinical stage of cII or cIII (cT3–4 N0–2 M0) (Based on AJCC staging system, phase 8);”

**Explicit exclusion criteria.** ✓✓
- Section: 2. MATERIALS AND METHODS > 2.1. Patients
- Quote: “Patients with distant metastasis before or after nCRT and other malignant diseases were excluded.”

**Treatment restriction: the cohort received a specific nCRT regimen and surgery.** ✓✓
- Section: 2. MATERIALS AND METHODS > 2.3. Treatments
- Quote: “All enrolled patients underwent nCRT with either intensity‐modulated radiotherapy (IMRT) or three‐dimensional conformal radiotherapy (3DCRT) in the form of radiotherapy and oral capecitabine during the same period of radiotherapy. The dose of short‐course radiotherapy was 25 Gy/5 times, and the dose of long‐course radiotherapy was 45.0–50.4 Gy/25–28 times. Patients received neoadjuvant chemotherapy at the end of radiotherapy. Neoadjuvant chemotherapy regimen: mFolFox6 (calcium folinate 400 mg/m2, fluorouracil 2600 mg/m2, oxaliplatin 85 mg/m2) or Xelox (oxaliplatin 130 mg/m2, capecitabine 1000 mg/m2 bid). TME procedure was performed after nCRT.”

**Stated units for every continuous input.** ✓✓
- Section: 3. RESULTS > 3.2. Independent predictors for pCR > TABLE 4
- Quote: “Pre‐CRT CEA (ng/ml)”

**Outcome definition.** ✓✓
- Section: 2. MATERIALS AND METHODS > 2.2. Tumor response evaluation
- Quote: “Pathologic results were evaluated by two independent pathologists. The pCR was defined as no found tumor cells, complete tumor regression, and only fibroblasts remaining in the resected tumor tissue and regional lymph nodes. (i.e., ypT0N0).”

**Accrual window of the development data.** ✓✓
- Section: 2. MATERIALS AND METHODS > 2.1. Patients
- Quote: “We retrospectively analyzed 1825 patients with examination confirmed LARC from 2011 to 2022 at the Union Hospital of Fujian Medical University (Fuzhou, China; included as training cohort) and the Zhangzhou Hospital of Fujian Medical University (Zhangzhou, China; included as external validation cohort).”

**Cohort sizes and split used for development and external validation.** ✓✓
- Section: 2. MATERIALS AND METHODS > 2.5. Statistical analyses, model development, and validation
- Quote: “The endpoint of building the dynamic nomogram was pCR. Cases were allocated to the training cohort (Union Hospital, n = 1579) and external validation cohort (Zhangzhou Hospital, n = 246).”

### `msk_rectal`: MSK rectal calculator

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC8576585/
- DOI: https://doi.org/10.1001/jamanetworkopen.2021.33457
- Note: Supplement 1 (eFigure with the coefficients): retrieved as PDF via Europe PMC's supplementaryFiles endpoint, filename jamanetwopen-e2133457-s001.pdf

**Population: the equation applies to INCOMPLETE pathological responders only.** ✓✓
- Section: Methods > Development of Clinical Calculators
- Quote: “an a priori decision was made to obtain RFS and OS estimates from Kaplan-Meier curves using data from patients with complete pathological response and to create risk models for predicting RFS and OS using data from patients with incomplete pathological response.”

**Complete responders are handled by a Kaplan-Meier estimate, not by this equation, and are outside its scope.** ✓✓
- Section: Abstract > Main Outcomes and Measures
- Quote: “The final clinical calculators provided RFS and OS estimates derived from Kaplan-Meier curves for patients with complete pathological response and from risk models for patients with incomplete pathological response.”

**RFS is coded against a ypT0/T1 reference group (so ypT2, ypT3, ypT4 each get an indicator).** ✓✓
- Section: Results > Outcomes and Clinical Calculator Variables
- Quote: “The ypT1 category was grouped with the ypT0 category to create a more parsimonious RFS model (Figure 2A).”

**OS is coded against a DIFFERENT reference group, ypT0/T1/T2 (so only ypT3 and ypT4 get indicators), applying the RFS coding to OS misprices ypT2 patients.** ✓✓
- Section: Results > Outcomes and Clinical Calculator Variables
- Quote: “The ypT0, ypT1, and ypT2 categories were grouped together to create a more parsimonious OS model (Figure 2B).”

**Age is a covariate of the OS model only and is not in the RFS model.** ✓✓
- Section: Methods > Development of Clinical Calculators
- Quote: “For RFS and OS, the final Cox proportional hazards model included ypT category, number of positive lymph nodes, tumor location (distance from the anal verge of <5 cm vs ≥5 cm), presence of venous invasion, and presence of PNI. The OS model also included patient age.”

**Nominal prediction horizon of the calculators as described in the paper is 5 years.** ✓✓
- Section: Figure 2 legend (Nomogram of Risk Model for Predicting Recurrence-Free Survival and Overall Survival)
- Quote: “(4) draw a straight line from total points down to 5-year recurrence-free survival or 5-year overall survival.”

**Validation evidence does not extend to the longer horizons the S0 grid permits, discrimination was assessed only to 80 months (RFS) and 60 months (OS).** ✓✓
- Section: Methods > Statistical Analysis
- Quote: “The concordance index was calculated using inverse probability weights for up to 80 months for RFS and up to 60 months for OS.”

**ypT0 is a valid input to the RFS equation (its reference group is labelled ypT0/T1), even though MSK's web form rejects ypT0 for an incomplete responder.** ✓✓
- Section: Methods > Development of Clinical Calculators
- Quote: “Because patients with complete pathological response (ypT0N0) after the receipt of neoadjuvant therapy had a substantially lower likelihood of recurrence and a higher rate of survival compared with other patients,”

**Development cohort: 710 patients, MSK, treated 1998-2014; externally validated at Siteman Cancer Center.** ✓✓
- Section: Methods > Patients and Treatments
- Quote: “Patients in the MSK cohort received chemoradiotherapy followed by surgery and planned adjuvant chemotherapy between January 1, 1998, and December 31, 2014.”

**Age range of the development / validation cohorts.** ✓✓ *(corrected after verification)*
- Section: Results > Cohorts
- Quote: “Among all patients, the median age was 57.8 years (range, 18.0-91.9 years); 863 patients (61.6%) were male, and 537 patients (38.4%) were female, with tumors at a median distance of 6.7 cm (range, 0-15.0 cm) from the anal verge (Table).”

**Histology / anatomic-site restriction: rectal adenocarcinoma within 15 cm of the anal verge.** ✓✓
- Section: Methods > Patients and Treatments
- Quote: “Prospectively maintained institutional databases were queried for patients with pretreatment rectal adenocarcinoma within 15 cm of the anal verge that was diagnosed as AJCC stage II or III disease via endorectal ultrasonography or magnetic resonance imaging who received treatment between January 1, 1998, and December 31, 2017.”

**Stage and staging-modality restriction: AJCC clinical stage II or III, staged by endorectal ultrasonography or MRI.** ✓✓
- Section: Methods > Patients and Treatments
- Quote: “that was diagnosed as AJCC stage II or III disease via endorectal ultrasonography or magnetic resonance imaging”

**Treatment-timing / treatment-sequence restriction: neoadjuvant chemoradiotherapy, then surgery (total mesorectal excision), with planned adjuvant chemotherapy.** ✓✓
- Section: Methods > Patients and Treatments
- Quote: “The surgical procedure for all patients was total mesorectal excision.”

**Explicit exclusion criteria.** ✓✓
- Section: Methods > Patients and Treatments
- Quote: “Patients with metastatic disease and those with cancer that was being managed by a watch-and-wait strategy (which was rare during the study period) were excluded.”

**Stated units for the continuous inputs: age in years, distance from anal verge in centimetres, positive lymph nodes as a count.** ✓✓
- Section: Table. Patient and Disease Characteristics
- Quote: “DTAV, median (range), cm”

**Distance from the anal verge enters the model as a dichotomy at 5 cm, not as a continuous variable.** ✓✓
- Section: Methods > Development of Clinical Calculators
- Quote: “tumor location (distance from the anal verge of <5 cm vs ≥5 cm)”

**Definition of the venous-invasion input.** ✓✓
- Section: Figure 2 legend (Nomogram of Risk Model for Predicting Recurrence-Free Survival and Overall Survival)
- Quote: “Venous invasion includes small lymphatic and venous invasion, large intramural venous invasion, and large extramural venous invasion.”

**Outcome definitions for the two endpoints.** ✓✓
- Section: Methods > Characteristics and Outcomes
- Quote: “The outcome measures were RFS and OS. Recurrence-free survival was defined as the period from the date of surgery to the date of recurrence or death, and patients alive without recurrence were censored at the last follow-up. Overall survival was defined as the period from the date of surgery to the date of death associated with any cause, and patients alive were censored at the last follow-up.”

**Observed range of the positive-lymph-node input in the cohorts (the covariate the module splines with knots at 0, 1, 3).** ✓✓
- Section: Results > Cohorts
- Quote: “number of positive lymph nodes (median, 2 nodes [range, 1-18 nodes] in the MSK training set, 2 nodes [range, 1-22 nodes] in the MSK validation set, 2 nodes [range, 1-9 nodes] in the SCC chemoradiotherapy group, and 2 nodes [range, 1-8 nodes] in the SCC short-course radiotherapy with consolidation chemotherapy group)”


## Liver

### `amap`: aMAP score

*open access / full text*
- Full text: https://ora.ox.ac.uk/objects/uuid:de233595-872f-425d-aff8-6b4291bca49d/files/rjm214p37t
- DOI: https://doi.org/10.1016/j.jhep.2020.07.025
- Note: Elsevier version-of-record PDF, deposited open access in the Oxford University Research Archive; cross-checked against the Glasgow Caledonian accepted-manuscript copy

**Population is chronic hepatitis, developed and validated across 11 global prospective cohorts / RCTs (repo card bullet 1).** ✓✓
- Section: Patients and methods (opening paragraph) · p. 1369
- Quote: “This study was based on 11 prospective observational cohorts or randomised controlled trials (RCTs) involving patients with chronic HBV (CHB; n = 7), chronic HCV (n = 3) and non-viral hepatitis (NVH; n = 1).”

**Not general-population HCC screening, the development population was tertiary-hospital, largely treated patients with active disease (repo card bullet 1, second sentence).** ✓✓
- Section: Discussion > limitations paragraph · p. 1376
- Quote: “First, the patients were recruited from tertiary hospitals and were especially likely to have active disease before treatment. It is likely that more patients would belong to the low-risk category in a primary care setting, which would further increase the NPV of the score.”

**Bilirubin must be supplied in µmol/L (repo card bullet 2).** ✓✓
- Section: Results > Derivation of the HCC risk score (units sentence immediately after the aMAP formula); also Methods > Albumin–bilirubin score calculation · p. 1372
- Quote: “where age is in year, bilirubin in lmol/l, albumin in g/l and platelets in 103/mm3.”

**Albumin must be supplied in g/L (repo card bullet 2).** ✓✓
- Section: Results > Derivation of the HCC risk score (units sentence); Methods > Albumin–bilirubin score calculation; Table 1 row label · p. 1371
- Quote: “where bilirubin is in lmol/L and albumin in g/L.”

**Platelets must be supplied in ×10^3/mm^3 (equivalently ×10^9/L) (repo card bullet 2).** ✓✓
- Section: Results > Derivation of the HCC risk score (units sentence); Table 1 row label · p. 1372
- Quote: “platelets in 103/mm3”

**Age is in years (repo card bullet 2, implicit in the units list).** ✓✓
- Section: Results > Derivation of the HCC risk score (units sentence) · p. 1372
- Quote: “where age is in year”

**Output is a 0–100 stratifier (repo card bullet 3).** ✓✓
- Section: Results > Derivation of the HCC risk score · p. 1372
- Quote: “and then the score range was standardised to 1–100:”

**Risk bands are <50 low / 50–60 medium / ≥60 high (repo card bullet 3).** ✓✓
- Section: Results > HCC risk stratification based on the aMAP score · p. 1372
- Quote: “The X-tile plots were used to generate 2 optimal cut-off values (50 and 60) to separate the training cohort into low-, medium- and high-risk groups (Fig. S4).”

**The paper prints a 5-year baseline survival S0, which would permit a continuous risk (repo card bullet 3).** ✓✓
- Section: Results > Derivation of the HCC risk score · p. 1372
- Quote: “The 5-year baseline survival function of the aMAP Risk Score was:”

**Sex restriction.** ✓✓
- Section: Results > Derivation of the HCC risk score (formula); Table 1 row 'Male, n (%)'; Table 2 covariate 'Sex (male vs. female)' · p. 1371
- Quote: “Sex (male vs. female)”

**Histology / subtype / anatomic-site restriction.** ✓✓
- Section: Methods > Cirrhosis and HCC assessment · p. 1371
- Quote: “The diagnoses of cirrhosis and HCC were based on standard histological and/or compatible radiological ﬁndings.”

**Stage / treatment-timing restriction.** ✓✓
- Section: Patients and methods > CHB patients (closing paragraph of the CHB cohort descriptions) · p. 1369
- Quote: “In the above 7 CHB cohorts/trials, patients with decompensated cirrhosis, HCC, liver transplantation, or co-infection(s) with hepatitis D, HCV or HIV were excluded. The laboratory results collected at enrolment were used for the analysis.”

**Explicit inclusion and exclusion criteria (analysis-level).** ✓✓
- Section: Methods > Statistical analysis · p. 1371
- Quote: “Patients in each cohort who had a follow-up time of less than 6 months or had been found to have HCC within 6 months were excluded from the analysis.”

**Outcome definition and prediction horizon.** ✓✓
- Section: Methods > Statistical analysis (horizon); Methods > Cirrhosis and HCC assessment (outcome definition) · p. 1371
- Quote: “The patients from the centre with the largest sample size (Nanfang Hospital, Guangzhou, China) in the Search-B CHB cohort were used as the training cohort to derive a score for predicting HCC within 5 years.”

**A stated condition under which the model is invalid.** ✓✓
- Section: Discussion (paragraph on the ALBI/platelet components, immediately preceding the limitations paragraph) · p. 1376
- Quote: “However, the total bilirubin level could be inﬂuenced by certain diseases, such as haemolysis and inherited enzyme defects. Therefore, it is recommended that the aMAP score is not suitable for predicting HCC risk among patients with non-liver diseases that could signiﬁcantly affect the bilirubin level.”

**Ethnicity and aetiology limits on generalisability (a second invalidity-adjacent condition).** ✓✓
- Section: Discussion > limitations paragraph, fourth limitation · p. 1377
- Quote: “Fourth, most patients in this study were Asians and Caucasians with viral hepatitis. Therefore, the performance of the aMAP score in patients of other ethnicities (e.g. African) and other aetiologies (e.g. NAFLD, primary biliary cirrhosis, etc.) requires further investigation.”

**Reduced discrimination in the cirrhosis subgroup (a stated performance caveat).** ✓✓
- Section: Discussion > limitations paragraph, third limitation · p. 1377
- Quote: “Third, the discriminatory ability of the aMAP score was suboptimal in the case of patients with cirrhosis, a situation common to existing HCC risk scores.”

### `hap`: HAP score

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC4023407/
- DOI: https://doi.org/10.1093/annonc/mdt247

**Population: HCC patients being considered for transarterial chemoembolisation (the score is a pre-treatment / candidacy score for TACE-TAE patients).** ✓✓
- Section: discussion
- Quote: “In summary, we have defined a simple and clinically relevant prognostic index requiring the measurement of two tumour variables and two liver variables, specifically for patients undergoing TACE.”

**The pre-treatment / "pre-selection" timing of the inputs: the score is meant to be computed before embolisation, not from post-embolisation response.** ✓✓
- Section: discussion
- Quote: “Prognostic indicators that rely on some form of post-embolisation assessment have also been defined, but these are not helpful in pre-selection of patients [,].”

**Albumin threshold is < 36 g/L; the paper's printed "g/dl" is a unit error, and it is uniform across four places in the paper.** ✓✓
- Section: methods and materials > statistical analysis
- Quote: “The cut-offs used were bilirubin 17 μmol/l, albumin 36 g/dl which are, respectively, the upper and lower limits of the normal range; AFP: 400 ng/ml since this has been used as a diagnostic cut-off, and 7 cm for tumour size.”

**Grade D is "> 2" points, so it absorbs both 3 and 4 points; A/B/C are exact counts 0/1/2.** ✓✓
- Section: results > developing the prognostic score
- Quote: “The HAP score was defined as the sum of these scores, and patients were classified into low- (HAP A), intermediate-(HAP B), high-(HAP C) or very high-(HAP D) risk groups with HAP scores of 0, 1, 2 or >2 points, respectively (Table ).”

**The four point assignments: 1 point each for albumin < 36 (g/L per repo), bilirubin > 17 umol/L, AFP > 400 ng/mL, dominant tumour > 7 cm.** ✓✓
- Section: Abstract > Results
- Quote: “Patients were assigned one point if albumin <36 g/dl, bilirubin >17 μmol/l, AFP >400 ng/ml or size of dominant tumour >7 cm.”

**Median OS by grade (27.6 / 18.5 / 9.0 / 3.6 months) belongs to the derivation cohort and does not transfer.** ✓✓
- Section: results > developing the prognostic score > Figure 1 legend
- Quote: “For the training dataset, the median overall survival (OS) times were 27.6 months (95% CI16 to not estimable), 18.5 months (95% CI15.5–30.4), 9.0 months (95% CI 6.9–15.4) and 3.6 months (95% CI 1.7–8.5) for HAP A, B, C and D, respectively. For the validation set, OS median values were 25.5 (95%CI 13.7–32.8), 18.1 (95% CI 9.9 to not estimable), 8.9 (95% CI 6.8–16.1) and 5.9 (95% CI 2.8–12.7) months, respectively.”

**Histology / subtype / anatomic site restriction: hepatocellular carcinoma only, diagnosed by histology or by imaging under EASL criteria.** ✓✓
- Section: methods and materials > study population
- Quote: “HCC was diagnosed by histology or imaging according to European Association for the Study of the Liver criteria and patients who had surgery or transplantation were excluded.”

**Explicit inclusion criteria.** ✓✓
- Section: methods and materials > study population
- Quote: “We reviewed 114 sequential patients with HCC treated with TAE/TACE at the Royal Free Hospital and University College Hospital between 1997 and 2010, including patients from a recently reported clinical trial []. HCC was diagnosed by histology or imaging according to European Association for the Study of the Liver criteria and patients who had surgery or transplantation were excluded.”

**Explicit exclusion criteria.** ✓✓
- Section: results > patients
- Quote: “Main-branch portal vein thrombosis was an exclusion criterion for TAE/TACE in both institutions, but segmental portal vein involvement was more common in the validation dataset.”

**Outcome definition and prediction horizon.** ✓✓
- Section: methods and materials > statistical analysis
- Quote: “Overall survival (OS) was measured from the date of first TACE/TAE until death or the date of last follow-up.”

**Missing-data limit: the score was not computable for a substantial fraction of the very cohorts it was derived and validated in.** ✓✓
- Section: results > developing the prognostic score
- Quote: “The HAP score could be calculated for 91 patients in the training set and 151 in the validation set (supplementary Table S2, available at Annals of Oncology online).”

**Candidacy / treatment-selection use (the repo files HAP on the response axis as selecting who benefits from TACE).** ✓✓
- Section: discussion
- Quote: “In both the cohorts, a HAP score of C or D defined poor prognosis groups which are unlikely to have benefited from TACE and might now be better served with systemic therapy or supportive care.”

### `albi`: ALBI grade

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC4322258/
- DOI: https://doi.org/10.1200/JCO.2014.57.9151

**ALBI grades liver function, not tumour burden.** ✓✓
- Section: Results (paragraph introducing the linear predictor); also Patients and Methods > Statistical Methods
- Quote: “Although vascular invasion and tumor number had, as expected, an impact on survival in most of the strata, we confined our model to albumin and bilirubin because these, alone, were related to liver function.”

**Output is a score and a grade 1/2/3, not a probability.** ✓✓
- Section: Results (paragraph following Table 2)
- Quote: “Calculating the patient-level linear prediction (xb) and applying the cut points assigned each patient to one of three prognostic groups, now named the ALBI grade, 1 to 3.”

**Grade cutoffs are -2.60 and -1.39 on the continuous score.** ✓✓
- Section: Results (paragraph following Table 2)
- Quote: “The cut points were as follows: xb ≤ −2.60 (ALBI grade 1), more than −2.60 to ≤ −1.39 (ALBI grade 2), and xb more than −1.39 (ALBI grade 3).”

**Stated units for the continuous inputs are micromol/L for bilirubin and g/L for albumin.** ✓✓
- Section: Results (paragraph introducing the linear predictor)
- Quote: “the equation for the linear predictor was as follows: linear predictor = (log10 bilirubin × 0.66) + (albumin × −0.085), where bilirubin is in μmol/L and albumin in g/L.”

**Histology / subtype / anatomic site restriction: hepatocellular carcinoma (plus a cirrhosis-only specificity cohort).** ✓✓
- Section: Discussion
- Quote: “We have examined this group specifically for the aforementioned reason, not to suggest that it would have a role outside the area of HCC and chronic liver disease.”

**Stage restriction: all disease stages are represented, so the model is not stage-limited.** ✓✓
- Section: Patients and Methods (opening paragraph)
- Quote: “The centers were chosen to ensure the inclusion of patients of all disease stages and representative of a broad range of etiologies and geographical regions.”

**Treatment-timing restriction: inputs are pre-treatment labs drawn near diagnosis.** ✓✓
- Section: Patients and Methods > Table 1 footnote paragraph (immediately following Table 1)
- Quote: “All parameters investigated in the analysis were measured before any treatment and within 6 weeks of diagnosis.”

**Explicit exclusion criteria.** ✓✓
- Section: Discussion (third paragraph); also Patients and Methods > Centers > Europe and > United States
- Quote: “We specifically excluded patients who underwent liver transplantation because, in these patients, underlying (dys)function is effectively abrogated by the procedure.”

**Explicit inclusion criteria.** ✓✓
- Section: Patients and Methods > Patients Entered Onto Clinical Trials
- Quote: “The inclusion criteria are given in the published reports.”

**Outcome definition.** ✓✓
- Section: Patients and Methods > Table 1 footnote paragraph (immediately following Table 1)
- Quote: “Survival was measured from the date of diagnosis (first presentation with HCC) to date of death or last follow-up.”

**Any stated condition under which the model is invalid.** ✓✓
- Section: Discussion (fourth and fifth paragraphs)
- Quote: “not to suggest that it would have a role outside the area of HCC and chronic liver disease”

**Development and validation cohort composition (what the model was fitted on).** ✓✓
- Section: Patients and Methods > Statistical Methods; Abstract > Patients and Methods
- Quote: “The entire Japanese cohort (n = 2,599) was then randomly split into two groups, the training (n = 1,313) and validation sets (n = 1,286).”


## Gastric

### `abc_method`: ABC method

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC1774550/
- DOI: https://doi.org/10.1136/gut.2004.055400

**Population is asymptomatic Japanese health-checkup endoscopy attendees (repo card bullet 1, population half)** ✓✓
- Section: Methods > Enrolment; and Introduction (final paragraph); and Discussion
- Quote: “Between March 1995 and February 1997, participants in health examination programmes held by Kameda General Hospital and Makuhari Clinic who underwent upper endoscopy were consecutively enrolled.”

**Sex restriction** ✓✓
- Section: Results > Gastric cancer development; and Table 1; and Table 3
- Quote: “Among 6983 subjects analysed, 43 (37 men and six women) developed gastric cancer during the follow up period.”

**Explicit inclusion criteria** ✓✓
- Section: Methods > Enrolment
- Quote: “Patients were encouraged to undergo endoscopic examination annually to check for the development of gastric cancer, and 6983 revisited the programme for follow up endoscopy during the observation period.”

**Explicit exclusion criteria** ✓✓
- Section: Methods > Enrolment
- Quote: “Excluding those with gastric cancer, peptic ulcer, or a past history of surgical resection of the stomach, a total of 9293 participants were candidates for inclusion in this study.”

**Stage / treatment-timing restriction (acid suppression washout, no prior eradication)** ✓✓
- Section: Methods > Enrolment
- Quote: “Proton pump inhibitors or H2 blockers had not been prescribed within one month prior to the examination. None had undergone eradication therapy for H pylori.”

**Seroreversion mechanism: antibody falls as atrophy advances, which is why group D is antibody-negative (the mechanistic basis of the repo's eradication caveat and of the non-monotone ordering)**
- Section: Discussion (third paragraph)
- Quote: “It is generally known that the H pylori burden decreases dramatically in such situations,”

**Assay-specific: H. pylori antibody is the Biomerica GAP-IgG ELISA (repo card bullet 3, antibody half)** ✓✓
- Section: Methods > Serum H pylori antibody
- Quote: “Serum anti-H pylori antibody was measured using a commercial ELISA kit (GAP-IgG kit; Biomerica Inc., California, USA).”

**Assay-specific: pepsinogen is the Dainabot RIA bead kit, with the PG I <=70 ng/ml AND PG I/II <=3.0 cutoff pair (repo card bullet 3, pepsinogen half; also the repo's core formula)**
- Section: Methods > Serum pepsinogen level
- Quote: “Serum pepsinogen status was defined as “atrophic” when the criteria of both serum pepsinogen I level ⩽70 ng/ml and a pepsinogen I/II ratio (serum pepsinogen I (ng/ml)/serum pepsinogen II (ng/ml)) ⩽3.0 were simultaneously fulfilled, as proposed by Miki and colleagues.”

**Stated units for every continuous input** ✓✓
- Section: Methods > Serum pepsinogen level
- Quote: “a pepsinogen I/II ratio (serum pepsinogen I (ng/ml)/serum pepsinogen II (ng/ml)) ⩽3.0”

**Histology / subtype / anatomic site restriction on the outcome** ✓✓
- Section: Methods > Endoscopic and clinicopathological examinations
- Quote: “Histopathological assessment of gastric cancer was conducted using surgically resected or endoscopically biopsied samples, categorised as intestinal-type or diffuse-type, according to Lauren’s classification.”

**Stage restriction / spectrum of the detected outcome** ✓✓
- Section: Results > Gastric cancer development
- Quote: “All of the cancers were localised within the submucosa except for one invading the muscularis propria (group B).”

**Outcome definition** ✓✓
- Section: Abstract > Subjects and methods; and Methods > Enrolment
- Quote: “Incidence of gastric cancer was determined by annual endoscopic examination.”

**Prediction horizon** ✓✓
- Section: Results > Baseline characteristics of study subjects; and Discussion (fourth paragraph)
- Quote: “Each subject underwent 5.1 (0.05) sessions of endoscopy during a follow up period of 4.7 (0.04) years.”

**Group ordering is not monotone in either test alone; group D (seronegative WITH atrophy) is the highest-risk group (repo card bullet 5)** ✓✓
- Section: Discussion (fourth paragraph); and Discussion (third paragraph)
- Quote: “In addition, we are able to define a super high risk group for the development of gastric cancer (group D).”

**Group B is not statistically distinguishable from group A (HR 1.1, 95% CI 0.4-3.4) (repo card bullet 6)** ✓✓
- Section: Discussion (fourth paragraph)
- Quote: “showed the same low risk as group A without H pylori infection. Approximately 58% of those with H pylori infection could be regarded as having a negligible risk for at least five years.”

**Absolute rates are Japanese rates (repo card bullet 4, first half)** ✓✓
- Section: Discussion (second paragraph); and Discussion (conclusion)
- Quote: “It is likely that our subjects represent the healthy Japanese population, with fewer biases than hospitalised patients.”

**Cohort attrition / selection into the analysis set (an unstated applicability limit)** ✓✓
- Section: Abstract > Subjects and methods; and Methods > Enrolment
- Quote: “A total of 9293 participants in a mass health appraisal programme were candidates for inclusion in the present prospective cohort study: 6983 subjects revisited the follow up programme.”

**Age and sex are independent risk factors that the four-group score does not take as inputs** ✓✓
- Section: Results > Risk factors for gastric cancer and establishment of super high risk group; and Abstract > Results
- Quote: “Age, sex, and “group” significantly served as independent valuables by multivariate analysis.”

**Per-group annual incidence rates 0.04 / 0.06 / 0.35 / 0.60 %/y as implemented in ANNUAL_INCIDENCE** ✓✓
- Section: Abstract > Results; and Results > Antibody-pepsinogen status and gastric cancer development > Table 2
- Quote: “The annual incidence of gastric cancer was 0.04% (95% confidence interval (CI) 0.02–0.09), 0.06% (0.03–0.13), 0.35% (0.23–0.57), and 0.60% (0.34–1.05) in groups A, B, C, and D, respectively.”

### `xu_gastric_trg_score`: Xu 2021 TRG risk score

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC8082104/
- DOI: https://doi.org/10.3389/fonc.2021.607640

**Population is gastric adenocarcinoma receiving preoperative (neoadjuvant) chemotherapy followed by gastrectomy, with TRG assessable and pretreatment data available.** ✓✓
- Section: Materials and Methods > Patient Selection and Study Design
- Quote: “The inclusion criteria were as follows: 1. patients were pathologically confirmed as having gastric adenocarcinoma; 2. patients had successfully undergone PCT before surgery; 3. gastrectomy was performed after PCT; 4. TRG can be assessed; and 5. pretreatment clinicopathological data can be collected. Samples were excluded if the patient did not meet the inclusion criteria.”

**Repo card says 'locally advanced' gastric adenocarcinoma. The paper's actual stage restriction is cT4N+Mx, which explicitly ADMITS distant metastasis.** ✓✓
- Section: Results > Characteristics of the Study Population
- Quote: “All patients’ clinical stages at diagnosis were cT4N+Mx, which indicated that these tumors have invaded the serosal layer of the stomach and have regional lymph node metastasis, with or without distant metastasis.”

**Age range of the development and validation cohorts.** ✓✓
- Section: Results > Characteristics of the Study Population
- Quote: “In the retrospective cohort, the study population comprised 224 male and 80 female patients. The median age was 61 years (range: 21-80 years).”

**Histology / subtype restriction: adenocarcinoma only.** ✓✓
- Section: Materials and Methods > Patient Selection and Study Design
- Quote: “All gastric cancer patients were confirmed by endoscopic biopsy.”

**Treatment-timing restriction: the score uses PRETREATMENT values, and chemotherapy is roughly three cycles before gastrectomy.** ✓✓
- Section: Results > Characteristics of the Study Population
- Quote: “All patients had received an average of three cycles of PCT before gastrectomy. The main regimens of PCT were EOX (Epirubicin plus Oxaliplatin and Capecitabine) and taxane-containing chemotherapy.”

**Regimen composition differs between the derivation era and the prospective validation era (repo scope_note: EOX/taxane retrospectively, SOX/FLOT prospectively).** ✓✓
- Section: Results > Characteristics of the Study Population
- Quote: “The main regimens of PCT were SOX (S-1 plus Oxaliplatin) and FLOT (Fluorouracil plus Leucovorin, Oxaliplatin, and Docetaxel).”

**Outcome definition: Ryan TRG grade 0, complete pathological response of the primary tumour, assessed on the resection specimen.** ✓✓
- Section: Materials and Methods > Assessment System for Tumor Regression Grade
- Quote: “TRG of the primary tumor is divided into four categories: grade 0 (complete response: no viable cancer cells), grade 1 (moderate response: single cells or small groups of cancer cells), grade 2 (minimal response: residual cancer outgrown by fibrosis) and grade 3 (poor response: minimal or no tumor cells killed; extensive residual cancer). All histological slides were reexamined by the same pathologist to confirm the TRG grade.”

**Stated units for every continuous input.** ✓✓
- Section: Results > Derivation of a Prediction Model for TRG = 0; Table 4 'Risk Score of Prediction Model for TRG'
- Quote: “CA199 ≤10.90 U/mL, CA724 ≤3.19 U/mL, well differentiation and LNmax ≥1.535 cm were assigned 5, 4, 7, and 7 points, respectively”

**LNmax must be measured on multi-detector-row CT - a modality constraint absent from the repo card.** ✓✓
- Section: Materials and Methods > Data Collection and Statistical Analysis
- Quote: “LNmax was measured using multi-detector-row computed tomography (MDCT).”

**Higher score means MORE likely to achieve complete regression; the paper's '>13 = high-risk' label attaches to the group with the BETTER outcome.** ✓✓
- Section: Results > Derivation of a Prediction Model for TRG = 0
- Quote: “The optimal cut-off point for TRG in the prediction model was 13 points resulting from ROC curve analysis. The patients were divided into a low-risk (≤13 points) and a high-risk (>13 points) TRG group. TRG = 0 was discovered in 0% and 22.35% of the patients in the low-risk and high-risk TRG groups, respectively. The higher the score is, the more likely it indicates TRG = 0.”

**A larger lymph node scores TOWARD complete response - the direction is deliberate, novel, and acknowledged by the authors as unexplained.** ✓✓
- Section: Discussion
- Quote: “To our knowledge, this is the first report showing the value of LNmax for predicting TRG = 0 after PCT in gastric cancer. We speculate that patients with large regional lymph nodes have strong immunity against infection and tumor cell invasion.”

**Development cohort: 428 patients at Shanghai Ruijin Hospital - 304 retrospective (July 2009 - November 2018), split 2:1 into 202 training and 102 internal validation.** ✓✓
- Section: Materials and Methods > Patient Selection and Study Design; Results > Characteristics of the Study Population
- Quote: “Gastric cancer patient data from Shanghai Ruijin Hospital were retrospectively collected from July 2009 to November 2018. All gastric cancer patients were confirmed by endoscopic biopsy.”

**The prospective cohort was collected AFTER the model was locked (repo: 'enrolled prospectively ... after the model was locked'), December 2018 - June 2020, under the same criteria.** ✓✓
- Section: Materials and Methods > Patient Selection and Study Design
- Quote: “After the prediction model was established, we prospectively collected and recorded data from AGC patients from December 2018 to June 2020. The inclusion and exclusion criteria were the same as the criteria in the retrospective cohort mentioned above. The prediction model was verified in this prospective external validation group.”

**Repo claim that the 'external validation group' is really single-centre prospective TEMPORAL validation, not geographic.** ✓✓
- Section: Discussion (limitations paragraph)
- Quote: “This study had some limitations. This was a single-center clinical study, and the sample size was not very large. Patients in this study were enrolled over a large time span (2009-2018) and had different chemotherapy regimens.”

### `msk_gastric`: MSK gastric nomogram

***closed access, abstract only***
- Full text: https://pubmed.ncbi.nlm.nih.gov/14512396/
- DOI: https://doi.org/10.1200/JCO.2003.01.240
- Note: abstract/MEDLINE record only, no open full text located; the equation itself comes from the deployed calculator's R source, not the paper

**Population: the model applies to patients after an R0 resection for gastric carcinoma.** ✓✓
- Section: Abstract > Conclusion
- Quote: “A nomogram was developed to predict 5-year disease-specific survival after R0 resection for gastric cancer.”

**Prediction horizon of 5 years.** ✓✓
- Section: Abstract > Purpose
- Quote: “We developed and internally validated a nomogram that combines these factors to predict the probability of 5-year gastric cancer-specific survival on the basis of 1,039 patients treated at a single institution.”

**Sex restriction.** ✓✓
- Section: Abstract > Methods
- Quote: “Nomogram predictor variables included age, sex, primary site (distal one-third, middle one-third, gastroesophageal junction, and proximal one-third), Lauren histotype (diffuse, intestinal, mixed), number of positive lymph nodes resected, number of negative lymph nodes resected, and depth of invasion.”

**Histology / subtype / anatomic site restriction.** ✓✓
- Section: Abstract > Methods
- Quote: “Lauren histotype (diffuse, intestinal, mixed), number of positive lymph nodes resected, number of negative lymph nodes resected, and depth of invasion.”

**Stage or treatment-timing restriction.** ✓✓
- Section: Abstract > Purpose
- Quote: “Few published studies have addressed individual patient risk after R0 resection for gastric cancer.”

**Development cohort size and setting: 1,039 patients at a single institution.** ✓✓
- Section: Abstract > Purpose
- Quote: “on the basis of 1,039 patients treated at a single institution”

**Outcome definition: the predicted end point is death from gastric cancer (disease-specific survival), with deaths from other causes not counted as events.** ✓✓
- Section: Abstract > Methods
- Quote: “Death as a result of gastric cancer was the predicted end point.”


## Oesophageal

### `kunzmann`: Kunzmann points model

*open access / full text*
- Full text: https://pureadmin.qub.ac.uk/ws/portalfiles/portal/147669984/OAC_traditional_risk_prediction_FINAL.pdf
- DOI: https://doi.org/10.1016/j.cgh.2018.03.014
- Note: Queen's University Belfast accepted-manuscript repository copy (Green OA); confirmed 2026-08-18 to be a genuine PDF whose embedded metadata carries the paper's own DOI (10.1016/j.cgh.2018.03.014). The original pure.qub.ac.uk address 301-redirects here.

**Adenocarcinoma only, never squamous - the model is for oesophageal ADENOCARCINOMA and applying it where ESCC predominates is a category error.** ✓✓
- Section: METHODS > Outcome assessment
- Quote: “Primary EACs (ICD/10 C15, with ICD-O 8140–8573) diagnosed between 6 months (due to potential diagnostic delays) and 5 years from baseline was the main outcome of interest. Secondary outcomes included all primary upper gastrointestinal cancers (ICD/10 C15 and C16); esophageal cancer (ICD-10 C15, regardless of histology); gastric cancer (ICD-10 C16, regardless of histology) and; esophageal squamous cell carcinoma (ICD-10 C15, ICD-O 8050–8082) diagnosed between 6 months and 5 years from baseline.”

**Age >= 50 is the developed range; the module refuses ages below 50.** ✓✓
- Section: METHODS > Study design
- Quote: “Included in the present study were individuals aged ≥50 years (as upper gastrointestinal cancers are rare aged <50), without a history of cancer (excluding non-melanoma skin cancer) at or before baseline or within 6 months following baseline (to exclude diagnostic delays) and with complete information on relevant risk factors.”

**Output is a 0-15 point score.** ✓✓
- Section: Table and Figure legends > Figure 2
- Quote: “Figure 2. Nomogram for assigning points (out of a total of 15) to help identify individuals at a higher risk of oEAC within 5-years.”

**Referral threshold of >= 8 points.** ✓✓
- Section: Results > EAC risk-prediction model: points-based model
- Quote: “A cut-off threshold of 8+ points with the highest Youden’s index (0.48), had a sensitivity of 77.5%, a specificity of 70.5%, a positive predictive value of 0.16% (Figure 1C) and would mean 612 referrals for further screening for every EAC predicted, with 29.5% (104,723 individuals) of the cohort (59.7% of men and 3.5% of women) deemed high-risk.”

**Male sex alone carries 4.0 of the 15 available points - half the referral threshold.** ✓✓
- Section: METHODS > Statistical analysis
- Quote: “For example, the coefficient for men was 1.64 and the smallest coefficient in the model was 0.40 (BMI of 25-<30kg/m2), so men were assigned 4 points (1.64/0.40, then rounded to nearest 0.5).”

**Stage or treatment-timing restriction.** ✓✓
- Section: METHODS > Outcome assessment
- Quote: “Information on tumour stage was not available.”

**Explicit inclusion and exclusion criteria.** ✓✓
- Section: Results > Participants
- Quote: “There were 502,640 participants in the UK Biobank, of whom 117,891 (23.5%) were excluded as they were aged under 50 years, 30,665 (6.1%) were excluded due to a history of cancer (or cancer within 6 months of baseline), and 4,060 were excluded due to missing data (0.8%). This left 355,034 (70.7%) for inclusion in the final study cohort, among whom 220 individuals were diagnosed with EAC within 5 years.”

**Outcome definition and prediction horizon.** ✓✓
- Section: METHODS > Outcome assessment
- Quote: “Primary EACs (ICD/10 C15, with ICD-O 8140–8573) diagnosed between 6 months (due to potential diagnostic delays) and 5 years from baseline was the main outcome of interest.”

**Any stated condition under which the model is invalid.** ✓✓
- Section: DISCUSSION > Conclusion
- Quote: “In summary, a list of established risk factors including age, sex, BMI, smoking status and esophageal conditions could aid risk-prediction of EAC. These factors are consistent with previous risk-prediction studies, though the points attributed and positive predictive values for specific cut offs require external validation.”

**Generalisability limit of the development cohort (healthy-volunteer selection).** ✓✓
- Section: DISCUSSION > Strengths & limitations
- Quote: “The generalisability of the UK Biobank to the general population has been criticised due to the healthy participant effect22. Further studies could validate the findings of the current study using electronic clinical record databases, where symptom history may be better captured, as this would better reflect the level of information available to clinicians and be more generalizable.”

**Handling of Barrett's oesophagus / oesophagitis - whether people already under endoscopic surveillance invalidate the score.** ✓✓
- Section: DISCUSSION > Strengths & limitations
- Quote: “The medical history data provided information on Barrett’s esophagus or esophagitis, rather than on either condition alone. Individuals with Barrett’s esophagus or esophagitis remained in the primary analyses, as esophagitis offers a potentially useful source of EAC risk prediction. A sensitivity analysis in which individuals with Barrett’s esophagus or esophagitis were excluded did not alter the results, suggesting any potential detection bias due to endoscopic surveillance in some Barrett’s esophagus patients was minimal.”

**Definition of the `esophageal_condition` input (reflux / Barrett's etc.).** ✓✓
- Section: Results > EAC risk-prediction model: coefficient-based model
- Quote: “the final coefficient-based model for predicting EAC development within 5 years included age at baseline, sex, BMI, smoking status and history of diagnosis or treatment for esophageal conditions (Table 2)”

**The points table values themselves (age 0/1.5/2.5/3.5, male 4.0, BMI 0/1.0/1.5/2.5, smoking 0/2.0/3.5, oesophageal condition 1.5).** ✓✓
- Section: Results > EAC risk-prediction model: points-based model
- Quote: “A points-based model assigned additional points based on age (55-60 years: 1.5; 60-65 years: 2.5; 65+ years: 3.5), sex (males: 4), smoking status (former: 2; current: 3.5), BMI (>25-30: 1; 30-<35: 1.5; 35+: 2.5) and history of esophageal conditions or treatment (1.5) (Table 2 & Figure 2).”

**The divisor used to build the points: the repo asserts the Methods say 0.40, the Table 2 footnote says 0.41, and only 0.40 reproduces all ten published points.** ✓✓
- Section: METHODS > Statistical analysis
- Quote: “Points-based models were created from the coefficient-based model by dividing the coefficient of each variable by the smallest coefficient in the model and rounding to the nearest 0.5 to allow ease of calculation without a computer and easier to interpret cut-offs28. For example, the coefficient for men was 1.64 and the smallest coefficient in the model was 0.40 (BMI of 25-<30kg/m2), so men were assigned 4 points (1.64/0.40, then rounded to nearest 0.5).”

### `chau_eg`: Chau index

***closed access, abstract only***
- Full text: https://ascopubs.org/doi/10.1200/JCO.2004.08.154
- DOI: https://doi.org/10.1200/JCO.2004.08.154
- Note: publisher page shows the structured abstract only; Methods/Results/Discussion are paywalled

> **Closed access.** ASCO/JCO returns only the structured abstract to automated retrieval; Methods, Results tables and Discussion are paywalled. The fuller reading in `docs/MODEL_CONSTRAINTS.md` (site-of-primary breakdown, response-model rejection, "requires validation" statement) rest on the full text (see the module docstring, `read in full 2026-08-17`), which automated retrieval cannot reach, so those specific claims are **not independently re-verifiable from a public source** and are not repeated below with a false page/section. What the public abstract *does* support is quoted.

**Population is locally advanced or metastatic esophago-gastric cancer (a stage restriction: advanced disease only).** ✓✓
- Section: Abstract > Purpose
- Quote: “To identify baseline prognostic factors and assess whether pretreatment quality of life (QoL) predicts survival in patients with locally advanced or metastatic esophago-gastric cancer.”

**Treatment era of the development cohort is 1992-2001.** ✓✓
- Section: Abstract > Patients and Methods
- Quote: “Between 1992 and 2001, 1,080 patients were enrolled into three randomized, controlled trials assessing fluorouracil-based combination chemotherapy.”

**Explicit inclusion criteria.** ✓✓
- Section: Abstract > Patients and Methods
- Quote: “All patients were required to complete the European Organization for Research and Treatment of Cancer core QoL questionnaire before random assignment.”

**Stated units and cut-point for alkaline phosphatase: >= 100 U/L.** ✓✓
- Section: Abstract > Results
- Quote: “and alkaline phosphatase ≥ 100 U/L (HR, 1.41; 99% CI, 1.14 to 1.76)”

**Output form: a 0-4 count of four unweighted binary factors, banded good (0) / moderate (1-2) / poor (3-4); no probability is produced.** ✓✓
- Section: Abstract > Results
- Quote: “A prognostic index was constructed dividing patients into good (no risk factor), moderate (one or two risk factors) or poor (three or four risk factors) risk groups.”

**Outcome definition and prediction horizon: overall survival, reported at one year by risk group.** ✓✓
- Section: Abstract > Results
- Quote: “One-year survival for good, moderate, and poor risk groups were 48.5%, 25.7%, and 11%, respectively, and the survival differences among these groups were highly significant”

### `shapiro_ncrt`: Shapiro nomogram

***closed access, abstract only***
- Full text: https://academic.oup.com/bjs/article-abstract/103/8/1039/6136451
- DOI: https://doi.org/10.1002/bjs.10142
- Note: publisher page shows the abstract only; full text is paywalled

> **Closed access.** *Br J Surg* returns only the abstract to automated retrieval. The Fig. 1 points-to-survival axis, the UICC staging-edition mismatch and the four unlabelled scores in `docs/MODEL_CONSTRAINTS.md` rest on the full text, read at 300/600 dpi (module docstring). Not independently re-verifiable from a public source; not repeated below with a false page/section.

**Population: patients with oesophageal or oesophagogastric junctional carcinoma treated with neoadjuvant chemoradiotherapy (nCRT) followed by surgical resection.** ✓✓
- Section: Abstract > Conclusion
- Quote: “In patients with oesophageal or oesophagogastric cancer treated with nCRT plus surgery, overall survival can best be estimated using a prediction model based on cN, ypT and ypN categories.”

**Model inputs are cN, ypT and ypN categories; two of the three are post-resection pathology, so the model cannot be run pre-operatively.** ✓✓
- Section: Abstract > Results
- Quote: “The final prognostic model included cN, ypT and ypN categories, and had moderate discrimination (c-index at internal validation 0·63).”

**Explicit inclusion criteria.** ✓✓
- Section: Abstract > Methods
- Quote: “Patients treated with nCRT plus surgery were included.”

**Development cohort size.** ✓✓
- Section: Abstract > Results
- Quote: “Some 626 patients who underwent nCRT plus surgery were included.”

**Outcome definition: overall survival.** ✓✓
- Section: Abstract > Methods
- Quote: “Multivariable Cox modelling was used to identify prognostic factors for overall survival.”

**Discrimination is weak: c-index 0.63 at internal validation.** ✓✓
- Section: Abstract > Results
- Quote: “The final prognostic model included cN, ypT and ypN categories, and had moderate discrimination (c-index at internal validation 0·63).”

**The authors themselves state the model correlates only moderately with observed survival and that better prognostic factors are needed.** ✓✓
- Section: Abstract > Conclusion
- Quote: “Predicted survival according to this model showed only moderate correlation with observed survival, emphasizing the need for new prognostic factors to improve survival prediction.”


## Ovarian

### `iota_adnex`: IOTA ADNEX

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC4198550/
- DOI: https://doi.org/10.1136/bmj.g5920

**Population: women with at least one adnexal mass who were examined by ultrasound and then selected for surgery.** ✓✓
- Section: Methods > Patients
- Quote: “We included consecutive patients with at least one adnexal mass judged not to be a physiological cyst, who were examined with transvaginal ultrasound by a principal investigator and later selected for surgical intervention.”

**It estimates what a mass is, not whether one is present, so it is not a screening model and does not apply to masses managed expectantly.** ✓✓
- Section: Discussion > Strengths and weaknesses of this study
- Quote: “This could also be regarded as a limitation, because the model is based on patients who were selected for surgery. Hence we cannot be certain that the test performance of the ADNEX model would be maintained if applied to a population of tumours, of which some were selected for expectant management.”

**CA-125 is optional in clinical use of ADNEX (the deployed calculator runs without it).** ✓✓
- Section: Results > Implementation of ADNEX and illustrative example
- Quote: “The applications allow risk calculation even without information on serum CA-125 level, despite the decrease in performance.”

**oncology_centre is a model predictor, not a patient characteristic; it encodes referral filtering, so a prediction is only interpretable if it matches where the scan was done.** ✓✓
- Section: Methods > Statistical analysis
- Quote: “We included the variable “type of centre” because the risk of a malignant tumour is likely to be higher in oncology centres than in other centres, even after adjustment for the characteristics of patients and tumours.”

**Definition of an oncology centre (what oncology_centre = 1 means).** ✓✓
- Section: Methods > Statistical analysis
- Quote: “Oncology centres were defined as tertiary referral centres with a specific gynaecology oncology unit.”

**CA-125 and maximum lesion diameter enter the model as log base 2.** ✓✓
- Section: Results > Model development, temporal validation, and updating > Table 5 footnote
- Quote: “*This variable is log transformed (log with base 2) such that the odds ratio represents the effect for each doubling of the value.”

**Domain guard: solid component diameter must be >= 0 and must not exceed the lesion diameter.** ✓✓
- Section: Results > Model development, temporal validation, and updating > Table 5 footnote
- Quote: “†This variable represents the maximal diameter of the largest solid component divided by the maximal diameter of the lesion (range 0% to 100%), with 0% indicating that there is no solid tissue and 100% indicating that the maximal diameter of the largest solid component equals the maximal diameter of the lesion.”

**Output is a distribution over five diagnoses: benign, borderline, stage I invasive, stage II-IV invasive, secondary metastatic.** ✓✓
- Section: Methods > Data collection and reference standard
- Quote: “The final diagnosis was divided into five tumour types: benign, borderline, stage I invasive, stage II-IV invasive, and secondary metastatic cancer.”

**Sex restriction: women only.** ✓✓
- Section: Methods > Design and setting
- Quote: “We carried out an international multicentre prospective cohort study of women with at least one adnexal mass that required surgery, as judged by a clinician.”

**Anatomic site / lesion type restriction: ovarian, para-ovarian and tubal masses.** ✓✓
- Section: Abstract > Participants
- Quote: “Women with an ovarian (including para-ovarian and tubal) mass and who underwent a standardised ultrasound examination before surgery.”

**Stage restriction.** ✓✓
- Section: Methods > Data collection and reference standard
- Quote: “The reference standard was the histopathological diagnosis of the mass after surgical removal by laparotomy or laparoscopy as considered appropriate by the surgeon, and the stage of malignant tumours using the classification of the International Federation of Gynecology and Obstetrics (FIGO).”

**Explicit inclusion and exclusion criteria, including the treatment-timing restriction that the mass be removed within 120 days of the ultrasound.** ✓✓
- Section: Methods > Patients
- Quote: “Exclusion criteria were refusal for transvaginal ultrasonography, pregnancy at the time of presentation, and surgical removal of the mass more than 120 days after the ultrasound examination.”

**Stated units for every continuous input.** ✓✓
- Section: Methods > Statistical analysis
- Quote: “We selected four clinical variables—age (years), serum CA-125 level (U/mL), family history of ovarian cancer (yes/no), and type of centre (oncology centre v other hospitals), and six ultrasound variables—the maximum diameter of the lesion (mm), proportion of solid tissue (that is, the maximum diameter of the largest solid component divided by the maximum diameter of the lesion), presence of more than 10 cyst locules (yes/no), number of papillary projections (0, 1, 2, 3, >3), presence of acoustic shadows (yes/no), and presence of ascites (yes/no).”

**papillary_structures is a capped count 0-4 where 4 means MORE THAN THREE, not the raw number.** ✓✓
- Section: Methods > Statistical analysis
- Quote: “number of papillary projections (0, 1, 2, 3, >3)”

**Outcome definition and prediction horizon.** ✓✓
- Section: Abstract > Objectives
- Quote: “Objectives To develop a risk prediction model to preoperatively discriminate between benign, borderline, stage I invasive, stage II-IV invasive, and secondary metastatic ovarian tumours.”

**Stated condition under which the model may not hold: the ultrasound must follow IOTA terms, definitions and measurement technique (all study operators were experienced).** ✓✓
- Section: Discussion > Implications for clinical practice
- Quote: “We expect that the performance of the ADNEX model will be maintained in the hands of non-expert ultrasound examiners on condition that the examiners are familiar with the IOTA terms and definitions and use the IOTA examination and measurement techniques (see the IOTA consensus statement20).”

**Condition on the CA-125 assay: which assays the model was calibrated against.** ✓✓
- Section: Methods > Data collection and reference standard
- Quote: “We used second generation immunoradiometric assay kits for CA-125 II from Roche Diagnostics, Centocor, Cis-Bio, Abbott Laboratories, Bayer Diagnostics, bioMérieux, DiaSorin, Siemens, and Beckman Coulter. All kits used the OC125 antibody.”

**Which mass to score when the patient has more than one.** ✓✓
- Section: Methods > Patients
- Quote: “If more than one mass was detected, we used the mass with the most complex morphology on the ultrasound scan. When we observed masses with similar morphology, we used the largest or the one most easily accessible by ultrasound.”

**Development cohort: 'IOTA phase 3 pooled data, 3,506 women with an adnexal mass' (registry/models.yaml development_cohort, repeated in the module SCOPE string and in the card's population bullet).** ✓✓
- Section: Methods > Statistical analysis
- Quote: “We developed a prediction model using data from the women included in IOTA phases 1, 1b, and 2 (n=3506) and validated the model on data from the women included in phase 3 (n=2403).”

**Equation source: Appendix D of the supplement, the retrained pooled model.** ✓✓
- Section: Results > Model development, temporal validation, and updating
- Quote: “The ADNEX model formula is given in supplementary appendix D.”

### `msk_ovarian`: MSK ovarian nomogram

***closed access, abstract only***
- Full text: https://pubmed.ncbi.nlm.nih.gov/17950784/
- DOI: https://doi.org/10.1016/j.ygyno.2007.09.020
- Note: abstract/MEDLINE record only, no open full text located

**Population is bulky stage IIIC ovarian carcinoma, assessed after primary surgery.** ✓✓
- Section: Abstract > Results
- Quote: “A total of 424 evaluable patients with bulky stage IIIC EOC underwent primary surgery at our institution during the study period of 1/89 to 12/03.”

**Anatomic site and histology class restriction: epithelial ovarian carcinoma.** ✓✓
- Section: Abstract > Objective
- Quote: “To date, only one prediction model has been reported for patients with epithelial ovarian carcinoma (EOC).”

**Stage restriction: stage IIIC only.** ✓✓
- Section: Abstract > Objective
- Quote: “The objective of this study was to develop a more accurate survival nomogram for patients with bulky stage IIIC EOC.”

**Treatment-timing restriction: prediction is made after primary cytoreductive surgery, and the whole cohort received postoperative platinum-based chemotherapy.** ✓✓
- Section: Abstract > Results
- Quote: “All patients received postoperative platinum-based systemic chemotherapy.”

**Outcome definition: disease-specific (EOC-specific) survival, estimated by Kaplan-Meier and modelled with Cox proportional hazards.** ✓✓
- Section: Abstract > Patients and methods
- Quote: “Disease-specific survival was estimated by the Kaplan-Meier method. Cox proportional hazards regression was used for multivariate analysis, which was the basis for the nomogram.”

**Prediction horizon is fixed at 5 years.** ✓✓
- Section: Abstract > Conclusion
- Quote: “Utilizing six readily accessible predictor variables, our nomogram more accurately predicted 5-year disease-specific survival for bulky stage IIIC EOC than the previously published model.”

**Internal validation only, no external cohort.** ✓✓
- Section: Abstract > Results
- Quote: “Using the six predictor variables, a nomogram was constructed and internally validated using bootstrapping. It was shown to have excellent calibration with a bootstrap corrected concordance index of 0.67, which was more accurate in predicting survival at this stage than the previously published model (concordance index=0.53).”

**The six model inputs are age, tumour grade, histologic type, preoperative platelet count, ascites and residual disease.** ✓✓
- Section: Abstract > Patients and methods
- Quote: “Nomogram predictor variables included age, tumor grade, histologic type, preoperative platelet count, ascites, and residual disease after primary cytoreduction.”

**Temporal and institutional scope of the development cohort: a single institution, 1/89 to 12/03.** ✓✓
- Section: Abstract > Results
- Quote: “A total of 424 evaluable patients with bulky stage IIIC EOC underwent primary surgery at our institution during the study period of 1/89 to 12/03.”

**Development cohort size is 465 patients (as recorded in the repo's registry discrimination_source).** ✓✓ *(corrected after verification)*
- Section: Abstract > Results
- Quote: “A total of 424 evaluable patients with bulky stage IIIC EOC underwent primary surgery at our institution during the study period of 1/89 to 12/03.”


## Cervical

### `cervical_cin_risk`: Cervical CIN2+/CIN3+ models

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC8414700/
- DOI: https://doi.org/10.1186/s12916-021-02078-2
- Note: Additional file 1 (Tables S1-S3): https://static-content.springer.com/esm/art%3A10.1186%2Fs12916-021-02078-2/MediaObjects/12916_2021_2078_MOESM1_ESM.xlsx

**Population is a Chinese screening population.** ✓✓
- Section: Methods > Study population > Cross-sectional population
- Quote: “Participants were recruited from five hospitals in China between 2014 and 2015 and included women attending routine cervical cancer screening programs, outpatients referred for colposcopy, and inpatients planning treatment for CIN2+.”

**The development sample is enriched with disease, so absolute predicted risks are not calibrated to a general screening population.** ✓✓
- Section: Background (final paragraph)
- Quote: “Models were constructed and evaluated in a cross-sectional population enriched with CIN and cervical cancer.”

**Outcome is CIN2+ or CIN3+, a dichotomous histologic endpoint, not invasive cancer incidence.** ✓✓
- Section: Methods > Statistical analyses > Model development
- Quote: “CIN2+ or CIN3+, the outcome of interest, was dichotomous.”

**Outcome is ascertained at colposcopy/biopsy (histology), not by follow-up for cancer.** ✓✓
- Section: Methods > Study population > Cross-sectional population
- Quote: “Cervical biopsies were conducted using a protocol as previously described [14]. Local pathologists provided the primary diagnosis, and a panel of five pathologists from each center underwent a diagnostic blind review for consensus.”

**Prediction horizon: the model is cross-sectional (prevalent disease at the time of the test), not a time-to-event model.** ✓✓
- Section: Methods > Statistical analyses > External validation in screening cohorts
- Quote: “Three-year cumulative risks of CIN2+ were estimated by hrHPV and cytology co-testing negative and predicted-negative populations.”

**Cytology must be reported on the Bethesda system.** ✓✓
- Section: Methods > Laboratory tests
- Quote: “Results were reported using the Bethesda 2014 nomenclature.”

**Cytology is a seven-level categorical: NILM, ASC-US, ASC-H, AGC, LSIL, HSIL/AIS, SCC/ADC.** ✓✓
- Section: Methods > Statistical analyses > Model development
- Quote: “cytology was a seven-level covariate: negative for intraepithelial lesion or malignancy (NILM), ASC-US, low-grade squamous intraepithelial lesion (LSIL), atypical squamous cells cannot exclude high-grade lesion (ASC-H), atypical glandular cell (AGC), high-grade squamous intraepithelial lesion/adenocarcinoma in situ (HSIL/AIS), and squamous cell carcinoma/adenocarcinoma (SCC/ADC).”

**Four nested logistic variants exist: base, +E6, +genotyping, +both.** ✓✓
- Section: Additional file 1, Table S1, block header cells A4, A14, A25, A44
- Not a quotation: these are four separate cell labels in the supplement's
  spreadsheet, read individually and listed here. They are `Base model`,
  `Base Model+E6`, `Base Model+Genotyping` and `Base Model+E6+Genotyping`.
  An earlier version joined them with slashes and presented the result inside
  quotation marks, which implied a sentence that does not exist in the paper.

**Genotype groups are the paper's pooled sets (33/58, 59/56/66, 39/68/35) and are not interchangeable with other groupings.** ✓✓
- Section: Methods > Laboratory tests
- Quote: “The Onclarity HPV is a PCR assay for the detection of six individual HPV genotypes (16, 18, 31, 45, 51, and 52) and three groups of types (33/58, 59/56/66, and 39/68/35).”

**Age range of the development / validation cohorts.** ✓✓
- Section: Methods > Study population
- Quote: “Women eligible for the screening cohorts were additionally aged 25 to 65.”

**Sex restriction.** ✓✓
- Section: Methods > Study population
- Quote: “Women were eligible if they had an intact cervix and no prior history of CIN.”

**Histology / subtype / anatomic site restriction.** ✓✓
- Section: Methods > Statistical analyses > Model development
- Quote: “HSIL and AIS, as well as SCC and ADC, were separately combined because limited cases were available for these levels.”

**Stage or treatment-timing restriction.** ✓✓
- Section: Methods > Study population
- Quote: “Women who were pregnant, had a hysterectomy, or received treatment for cervical diseases were excluded.”

**Explicit inclusion and exclusion criteria.** ✓✓
- Section: Methods > Study population
- Quote: “This study included three populations, one cross-sectional population and two screening cohorts. Women were eligible if they had an intact cervix and no prior history of CIN. Women eligible for the screening cohorts were additionally aged 25 to 65. Women who were pregnant, had a hysterectomy, or received treatment for cervical diseases were excluded.”

**Stated units for every continuous input.** ✓✓
- Section: Results > Study population characteristics
- Quote: “The average ages (years ± standard deviation) of women were 47.79±9.78, 45.22±7.76, and 42.80±8.85”

**hrHPV input definition and coding.** ✓✓
- Section: Methods > Statistical analyses > Model development
- Quote: “hrHPV testing was dichotomous (any type of the 14 hrHPV types positive vs. all of the 14 hrHPV types negative)”

**E6 input definition, and the population in which the E6 variants were validated.** ✓✓
- Section: Methods > Statistical analyses > Model development, and Discussion
- Quote: “Additional covariates were also added to the base model, including E6 oncoprotein (dichotomous, either HPV16/18 positive vs. both HPV16&18 negative)”

### `moore_criteria`: Moore criteria

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC4470610/
- DOI: https://doi.org/10.1016/j.ygyno.2009.09.006

**Population is advanced/recurrent/metastatic cervical carcinoma being started on cisplatin-based combination chemotherapy, pooled from GOG 110, 169 and 179 (development) with GOG 149 as external validation.** ✓✓
- Section: Abstract > Methods
- Quote: “Four-hundred twenty-eight patients with advanced cervical cancer who received a cisplatin-containing combination in three Gynecologic Oncology Group (GOG) protocols (110, 169 and 179) were evaluated for baseline clinical characteristics and multivariate analysis was conducted to identify factors independently prognostic predictive of response using a Logistic regression model. A predictive model was developed and externally validated using an independent GOG protocol (149) data.”

**The cohort is restricted to disease beyond curative surgery or radiotherapy, i.e. it is NOT a model for response to primary chemoradiation in newly diagnosed non-metastatic disease.** ✓✓
- Section: METHODS
- Quote: “Between June 1990 and September 2002, the GOG conducted, in sequence, four phase III for the treatment of cervical cancer that was beyond curative treatment with either surgery or radiation therapy.”

**Histology / subtype restriction: three of the four contributing protocols admitted squamous cell carcinoma only; GOG 179 also admitted adenocarcinoma.** ✓✓
- Section: METHODS
- Quote: “Eligibility for GOG protocols 110, 149, and 169 was limited to patients with squamous cell carcinomas. Acknowledging no apparent difference in the objective response rates in phase II trials between squamous cell carcinomas and adenocarcinomas of the cervix, eligibility for GOG protocol 179 included patients with both histological types.”

**The race factor is a cohort-specific association the authors discuss without resolving between access-to-care and biological explanations, and race alone must not be used to exclude a patient.** ✓✓
- Section: DISCUSSION
- Quote: “It cannot be over-emphasized that the predictive model defines high-risk patients by the accumulation of independent prognostic factors; black women would not be excluded from trials involving cisplatin-based chemotherapy on the basis of race alone.”

**The recurrence-timing factor is measured from the original diagnosis to the FIRST recurrence, with a cut-point of one year (<= 12 months), and is distinct from the interval to starting protocol chemotherapy.** ✓✓
- Section: RESULTS (first paragraph); Table 3; Abstract > Results
- Quote: “The median interval from diagnosis to 1 st recurrence was 11.6 months and median interval from 1 st protocol chemotherapy was 3.9 months ( Table 1 ).”

**Prior radiosensitizer means chemotherapy given concurrently with radiation as part of primary therapy, distinct from later recurrence chemotherapy.** ✓✓
- Section: METHODS
- Quote: “One important difference in the protocol populations was the number of patients who had previously received chemotherapy (concurrent to radiation therapy) as part of their primary therapy. The frequency of prior chemotherapy increased from 25% for GOG 110 to 24% for GOG 169 to 58% for GOG 179.”

**The five factors are counted, not weighted by their odds ratios; the published model is a 0-5 count.** ✓✓
- Section: METHODS (final paragraph)
- Quote: “Given that the five risk factors identified conferred comparable weights and there were no interactions across them, a simple prognostic index was developed by combining the number of risk factors and the population was classified into three groups: low-risk, mid-risk and high-risk.”

**Band definition: low risk 0-1 factors, mid risk 2-3, high risk 4-5.** ✓✓
- Section: Table 4 ("Validation of Prognostic Model") footnote; RESULTS
- Quote: “Low risk: 0–1 risk factor; mid risk: 2–3 risk factors; and high risk: 4–5 risk factors.”

**Explicit inclusion and exclusion criteria for the analysis cohort.** ✓✓
- Section: METHODS
- Quote: “The study population for this retrospective analysis was derived from the database of patients who received a cisplatin-containing combination in these studies.”

**Age range of the development and validation cohorts.** ✓✓
- Section: RESULTS (first paragraph); Table 1
- Quote: “Among the 428 eligible patients who enrolled in GOG protocols 110, 169 and 179 that were included for analysis, the median age was 47 years (range 21–84 years) and 64% of them were Caucasians, 71% had a performance status of 1–2.”

**Stated conditions under which the model is invalid or must not be applied.** ✓✓
- Section: DISCUSSION (final paragraph)
- Quote: “We advise caution pending further study, and certainly before applying this model to patient management outside the context of clinical trials. The model was derived from a retrospective multivariate analysis of platinum-based regimens, and thus the appropriateness of extrapolating these data to non-platinum-containing regimens, or cisplatin in combination with biologic agents, must be questioned.”

**Retrospective, pooled-trial derivation (a design constraint on how the model may be read).** ✓✓
- Section: METHODS; DISCUSSION
- Quote: “The study population for this retrospective analysis was derived from the database of patients who received a cisplatin-containing combination in these studies.”

**Internal goodness-of-fit and the external-validation cohort used to check calibration.** ✓✓
- Section: RESULTS
- Quote: “The internal validity of this prognostic model was satisfied (P=0.624 for HL test) ( Figure 1 ).”

### `cibula_arrm`: ARRM

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC9406128/
- DOI: https://doi.org/10.1016/j.ejca.2021.09.008

**Population is early-stage cervical cancer treated by primary surgery, with curative intent.** ✓✓
- Section: Introduction (aim sentence) and Methods > Study design and participants
- Quote: “The aim of our study was to develop a comprehensive model that will allow for surveillance tailoring based on prognostic factors in early-stage cervical cancer patients that were referred for surgical treatment with curative intent.”

**Stage restriction: TNM T1a-T2b, assessed preoperatively (AJCC cervix uteri staging).** ✓✓
- Section: Methods > Study design and participants
- Quote: “(ii) TNM stage T1a-T2b (based on the preoperative assessment; American Joint Committee on Cancer – Cervix Uteri Cancer Staging);”

**Full explicit inclusion criteria, including that surgery is the primary management and that fertility-sparing surgery and surgery after neoadjuvant chemotherapy are inside the population.** ✓✓
- Section: Methods > Study design and participants
- Quote: “Patients were retrospectively included if they met the following inclusion criteria: (i) histologically confirmed cervical cancer treated between 2007 and 2016; (ii) TNM stage T1a-T2b (based on the preoperative assessment; American Joint Committee on Cancer – Cervix Uteri Cancer Staging); (iii) primary surgical management, including fertility-sparing procedures/surgical treatment following neoadjuvant chemotherapy; (iv) and at least one year of follow-up data availability (patient underwent surgery ≥1 years before last or follow-up visit or was not lost to follow-up during the first year post-surgery). Patients were eligible irrespective of adjuvant treatment, neoadjuvant chemotherapy, tumour type, lymph node status, or lymph node staging.”

**Full explicit exclusion criteria, in particular, patients treated with definitive radiotherapy/chemoradiation are excluded, so the model does not apply to them.** ✓✓
- Section: Methods > Study design and participants
- Quote: “Patients were not eligible if they had precancer disease (including CIN 3 neoplasia), they were treated with definitive radiotherapy/chemoradiation, primary surgical treatment was abandoned intra-operatively, or they were lost to follow-up within the first-year post-surgery.”

**Tumour diameter is the pathologic measurement, not the imaged one.** ✓✓
- Section: Methods > Data collection
- Quote: “Regarding disease characteristics, we collected data about the type and size of the tumour (pathologically confirmed), depth of stromal invasion, pathologic TNM stage, number, and size of removed/positive lymph nodes, parametrial involvement, lymphovascular space invasion, and grade.”

**The annual recurrence risk is conditional, not cumulative: the year-N figure applies to a patient already recurrence-free through year N-1.** ✓✓
- Section: Methods > Data analyses
- Quote: “The annual risk of recurrence was assessed by conditional survival analysis. The conditional survival was estimated by calculating the survival probabilities with different landmark starting points: zero-year, one year, two years, three years, and four years. Only the patients who survived until the beginning of the interval were included for the estimation of recurrence probability in the certain year derived as 1 minus 1-year survival.”

**Risk points are derived from the betas weighted to a maximum sum of 100, and banded into 0, 1-25, 26-50, 51-75, 76-100.** ✓✓
- Section: Methods > Data analyses
- Quote: “A risk score was derived from regression coefficients (β) of the final model, which were weighted to the maximum sum of 100 points. The results of the model were expressed by Kaplan-Meier curves based on a stratified risk score (25-point intervals with the exception of the first category corresponding to the absence of risk predictors: 0, 1–25, 26–50, 51–75, 76–100).”

**Grade has no 'not assessed' level; missing grade was handled by multiple imputation during fitting rather than by a pooled reference category.** ✓✓
- Section: Methods > Data analyses
- Quote: “Missing values of grade (27.6% patients), which were, according to the univariable analysis, expected to be a significant predictor in multivariable analyses, were for multivariable analysis imputed on the basis of other predictors (age, number of positive pelvic lymph nodes, tumour diameter, LVSI, histotype, pT, adjuvant therapy). In total, five different data sets were created by multiple imputation and, therefore, the subsequent results had to be pooled.”

**The 76-100 point band holds 13 patients, 12 of whom recurred, and the landmark analysis for it stops at year three.** ✓✓
- Section: Results > Annual recurrence risk model (ARRM)
- Quote: “The landmark analysis for the group with the highest risk (76–100 points) was only performed until year three of follow-up, due to the limited number of cases (13 patients) and high recurrence rate in the first three years (cumulatively, 12 recurrences). The analysis ceased to be reliable after this point. The probability of recurrence in years one and two equalled 53.8% (95% CI: 26.7%; 80.9%) and 66.7% (95% CI: 28.9%; 100%), respectively.”

**Years 4 and 5 for the highest band are not reported because nobody is left in the band, not because the risk is zero.** ✓✓
- Section: Results > Annual recurrence risk model (ARRM) > Fig. 3 legend
- Quote: “ARRM (annual recurrence risk model): Landmark analysis of the annual probability of recurrence after surgery. N/A: not analysed.”

**Histology / subtype restriction: any cervical carcinoma histotype, entered as one of five modelled categories.** ✓✓
- Section: Methods > Data collection
- Quote: “Histological types of the tumours were classified according to WHO classification and were consequently clustered into six main groups: adenocarcinoma, adenosquamous cancer, squamous cell carcinoma, neuroendocrine cancer, and a cluster of others.”

**Treatment-timing restriction: the clock starts at surgery, and at least one year of post-surgical follow-up was required for entry.** ✓✓
- Section: Methods > Data analyses (time origin) and Methods > Study design and participants (follow-up requirement)
- Quote: “The length of the follow-up period was calculated from the surgery date to the last recorded follow-up visit.”

**Outcome definition and prediction horizon.** ✓✓
- Section: Methods > Data analyses (endpoint) and Results > Annual recurrence risk model (ARRM) (horizon)
- Quote: “The relationship between patient, tumour, and treatment characteristics and the analysed endpoint (disease-free survival) was evaluated by univariable and multivariable Cox proportional hazard models and described by hazard ratios, their 95% confidence intervals, and statistical significance.”

**Any stated condition under which the model is invalid.** ✓✓
- Section: Results > Annual recurrence risk model (ARRM); corroborated in Discussion (limitations)
- Quote: “The analysis ceased to be reliable after this point.”

**Setting restriction not claimed by the repo card: development was confined to high-volume tertiary centres of excellence meeting seven entry requirements, on four continents.** ✓✓
- Section: Methods > Study design and participants
- Quote: “The SCCAN study consortium consisted of 20 tertiary centres of excellence with a large volume of cervical cancer cases located in Europe, Asia, North America, or Latin America. In order for a centre to join the trial, the following requirements had to be fulfilled: (i) a minimum of 100 patients eligible for the trial; (ii) one of the modern imaging modalities routinely used in clinical staging (magnetic resonance imaging MRI, expert ultrasound, computed tomography, or positron emission tomography–computed tomography); (iii) all cases discussed by a multidisciplinary team; (iv) surgery performed by a surgeon with experience in gynae-oncology; (v) pathology performed by pathologist with experience in gynae-oncology; (vi) institutional follow-up performed by physicians; and (vii) availability of an institutional prospectively collected database of cases.”

**Development cohort as stated in the registry: 4,343 patients treated 2007-2016 at 20 centres, 528 recurrences.** ✓✓
- Section: Results > Cohort characteristics
- Quote: “We analysed the data from 4,343 patients with histologically confirmed cervical cancer who underwent primary treatment between January 2007 and December 2016.”

**Reported discrimination: Harrell's C 0.735 (95% CI 0.713; 0.757) and ten-fold cross-validated AUC 0.732, as asserted in the module docstring.** ✓✓
- Section: Results > Prognostic model development and validation
- Quote: “The Harrell’s concordance statistic factor (C-statistics) of the resulting model is 0.735 (95% CI: 0.713; 0.757). After performing the ten-fold cross-validation within each imputed dataset, the average AUC of 0.732 was obtained.”


## Pancreatic

### `endpac`: END-PAC

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC6120785/
- DOI: https://doi.org/10.1053/j.gastro.2018.05.023

**Population is adults with glycemically-defined new-onset diabetes; the score enriches an already-selected high-risk group and is not a general-population screen.** ✓✓
- Section: Introduction
- Quote: “The only known high-risk group for sporadic pancreatic cancer is that of subjects ≥50 years of age with glycemically defined new-onset diabetes2.”

**The development and validation work is in people aged 50 years and over.** ✓✓
- Section: Results > Incidence of pancreatic cancer in new-onset diabetes
- Quote: “Between January 1st, 2000 and December 31st, 2015, there were 1561 Olmsted County residents ≥50 years of age who first met the glycemically-defined new-onset diabetes criteria, of whom 16 (1.0%) developed pancreatic cancer with 3 years of meeting criteria for new-onset diabetes.”

**The glucose term is a difference of category INDICES, not a difference in mg/dL.** ✓✓
- Section: Discussion
- Quote: “A simple ΔBG is not as informative as ΔBG category used in the model (Table 3).”

**The 1-point-per-10-mg/dL glucose scoring belongs to a DIFFERENT model variant (model B), not to END-PAC.** ✓✓
- Section: Table 2 footnote (Comparison of performance characteristics of different classifier models for pancreatic cancer in new-onset diabetes)
- Quote: “^Δ FBG was calculated subtracting the blood glucose at −1 years from blood glucose at New-onset diabetes. For every 10 mg/dl difference, 1 point was assigned with highest point being 10 for anyone with a Δ FBG of ≥100 mg/dl.”

**The risk bands partition the score line exhaustively: ≥ 3 high, 1 or 2 intermediate, ≤ 0 low.**
- Section: Results > Risk stratification by END-PAC score in all new-onset diabetes subjects
- Quote: “When the distribution of scores were analyzed in all T2-NOD (n=1288) and PC-NOD (n=73), 56 PC-NOD (77%) had an END-PAC score of ≥3 compared to 248 T2-NOD (19%) (Figure 2A). Fifteen PC-NODs subjects (21%) had an END-PAC score of 1 or 2 compared to 408 T2-NOD subjects (32%). Two PC-NODs subjects (2%) had an END-PAC score ≤0 to 632 T2-NOD subjects (49%).”

**The Abstract's '<0' for the low-risk band is a typo; the Results text governs.** ✓✓
- Section: Abstract > Results
- Quote: “An END-PAC score <0 (in 49% of subjects) meant that patients had an extremely low-risk for pancreatic cancer.”

**Histology / subtype / anatomic-site restriction on the predicted cancer.** ✓✓
- Section: Discussion
- Quote: “All pancreatic cancer diagnoses were manually verified to exclude common mimics (such as IPMN, ampullary cancer, islet cell cancer) that otherwise constitute ~20% of unverified pancreatic cancer cohorts.”

**Explicit inclusion criteria (how new-onset diabetes was defined and who could be scored).** ✓✓
- Section: Patients and Methods > Cohorts assembled
- Quote: “All new-onset diabetes subjects in Olmsted County between January 1st, 2000 to December 31st, 2015 (n=1561) were identified using a glycemic definition of diabetes (Supplementary material, Table 1).”

**Outcome definition and prediction horizon.** ✓✓
- Section: Results > Validation of END-PAC Cohort
- Quote: “Of 1096 glycemically-defined new-onset diabetes subjects in the validation set, 9 pancreatic cancers were identified (0.82%). An END-PAC score of ≥3 identified 7 pancreatic cancers with a sensitivity of 78%, specificity of 82% and enriched the pancreatic cancer prevalence of 0.82% in the population-based cohort to 3.6% (4.4 fold) in END-PAC model-defined cohort, (predictiveness curve illustrated in Figure 1).”

**Any stated condition under which the model is invalid.** ✓✓
- Section: Discussion
- Quote: “While the model is easy to use, we believe physician and patient education will be required to appropriately apply the model only in true new-onset diabetes subjects as it is unclear how it will perform in long-standing diabetes or patients with unknown duration of diabetes.”

### `msk_pancreatic`: MSK pancreatic nomogram

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC1356406/
- DOI: https://doi.org/10.1097/01.sla.0000133125.85489.07
- Note: The page number given below (e.g. 297) is read from the PMC-served paginated PDF, reachable via that page's own 'Download PDF' toolbar button; the direct PDF URL is not stable enough to link here (it 404s when fetched cold).

**CARD BULLET - Population: after resection for adenocarcinoma of the pancreas** ✓✓
- Section: MATERIALS AND METHODS · p. 293
- Quote: “From a prospective database of patients resected with pancreatic ductal adenocarcinoma in a single institution between October 1983 and April 2000, we collected clinicopathological and operative data on 555 resected patients. All patients had pathology review to confirm pancreatic adenocarcinoma.”

**CARD BULLET - Horizon 12 / 24 / 36 months only** ✓✓
- Section: RESULTS > Figure 2 legend · p. 296
- Quote: “FIGURE 2. Nomogram for predicting 12-, 24-, and 36-month disease-specific survival probabilities.”

**CARD BULLET - Units: size is centimetres, and the hosted tool's 'mm' label is wrong** ✓✓
- Section: RESULTS · p. 294
- Quote: “For example, a poorly differentiated >4 cm lesion in the pancreatic head with negative surgical margins, but 10 positive lymph nodes, would garner 225 points or a less than 10% 36-month disease-specific survival probability. Similarly, a well-differentiated 1 cm lesion in the pancreatic head with negative margins and nodes would have a 50% 3-year disease-specific survival probability.”

**CARD BULLET - T stage is not monotone; reproduce as published, do not 'fix' the ordering** ✓✓
- Section: DISCUSSION · p. 297
- Quote: “Similarly, T stage does not appear to be logically ordered. There are ready explanations for this; T stage is inaccurately recorded, as definitive size measurements are difficult and the distinction between T3 and T4 is now (AJCC Cancer Staging Manual , 6th edition) one of resectability rather than size or invasion per se, whereas T3 was previously a comment on extrapancreatic extension (AJCC Cancer Staging Manual , 4th edition, 1992) and T4 was not included. Furthermore, T stage was not statistically significant in the Cox model. Note that statistically insignificant predictors were not omitted from the Cox regression model or resulting nomogram, because doing so actually tends to harm predictive accuracy.”

**STANDARD - Histology / subtype / anatomic site restriction** ✓✓
- Section: MATERIALS AND METHODS · p. 293
- Quote: “From a prospective database of patients resected with pancreatic ductal adenocarcinoma in a single institution between October 1983 and April 2000, we collected clinicopathological and operative data on 555 resected patients. All patients had pathology review to confirm pancreatic adenocarcinoma.”

**STANDARD - Treatment-timing restriction (when in the care pathway the model may be applied)** ✓✓
- Section: RESULTS · p. 294
- Quote: “The nomogram predicts the probability that the patient will survive pancreatic cancer for 1, 2, and 3 years from initial surgery, assuming he or she does not die of another cause first.”

**STANDARD - Explicit inclusion criteria** ✓✓
- Section: MATERIALS AND METHODS · p. 293
- Quote: “From a prospective database of patients resected with pancreatic ductal adenocarcinoma in a single institution between October 1983 and April 2000, we collected clinicopathological and operative data on 555 resected patients. All patients had pathology review to confirm pancreatic adenocarcinoma. Follow-up extended to March of 2002 with a primary end-point disease-specific survival.”

**STANDARD - Stated units: maximum path axis (tumour size)** ✓✓
- Section: RESULTS · p. 294
- Quote: “For example, a poorly differentiated >4 cm lesion in the pancreatic head with negative surgical margins, but 10 positive lymph nodes, would garner 225 points or a less than 10% 36-month disease-specific survival probability.”

**STANDARD - Outcome definition** ✓✓
- Section: Abstract > Results · p. 293
- Quote: “Based on a Cox model, we then developed a nomogram that predicts the probability that a patient will survive pancreatic cancer for 1, 2, and 3 years from the time of the initial resection, assuming that there is not death from an alternate cause.”

**STANDARD - Prediction horizon** ✓✓
- Section: Abstract > Methods · p. 293
- Quote: “We used a 1-, 2-, and 3-year follow-up, as the number of patients alive beyond 3 years is sufficiently limited to provide insufficient events.”

**STANDARD - Any stated condition under which the model is invalid** ✓✓
- Section: DISCUSSION · p. 297-298
- Quote: “There are limitations to any analysis of this type. There can never be enough predictive variables included in such a nomogram to give absolute predictions. Known variables may not be included because of the lack of numbers or observations, or there may be markers as yet unidentified that predict outcome.”

**MODULE NOTE 3 - Non-head tumours score better (-0.759 for 'other'); head is the reference** ✓✓
- Section: DISCUSSION · p. 297
- Quote: “Some items in the nomogram are not intuitively obvious, nor are they continuous variants, eg, a resected tail lesion is better than a resected head lesion. We expect that this is due to the observation that although overall survival of all body-tail lesions is worse than head lesions, resectability is also lower, such that when resection is possible, a more favorable cohort has been selected.”

**MODULE NOTE - Non-monotone tumour size effect (spline knots at 2, 3.2, 5.5 producing a folded size axis)** ✓✓
- Section: DISCUSSION · p. 297
- Quote: “Similarly, maximum path axis (“size”) does not have a monotonic effect due to similar criteria, ie, path size recorded predominately as >2 or >4 rather than actual measurements. There may well be a biologic reason why very large tumors do better. We have shown that a number of our 10-year survivors do have large tumors. Presumably, if one gets to a large tumor without metastasis, then the outcome is more favorable.”

**REPO CLAIM CHECK - registry discrimination_source: 'The development paper reports no numeric figure'** ✓✓
- Section: RESULTS · p. 294
- Quote: “The bootstrap-corrected concordance index is 0.64.”

**REPO CLAIM CHECK - registry discrimination_source: 'Annals of Surgery 2004 is paywalled with no PMC record'** ✓✓
- Section: n/a - retrieval fact · p. 293-298
- Quote: “PMCID: PMC1356406  PMID: 15273554”

**CONTEXT - Development cohort identity and internal-validation design** ✓✓
- Section: MATERIALS AND METHODS > Statistical Analysis · p. 294
- Quote: “Nomogram validation contained 2 components. First, the nomogram was subjected to bootstrapping, with 200 resamples, as a means of calculating a relatively unbiased measure of its ability to discriminate among patients, as quantified by the concordance index.”


## Head and neck

### `ukb_hnc`: UK Biobank head and neck model

*open access / full text*
- Full text: https://www.spandidos-publications.com/10.3892/ijo.2020.5123
- DOI: https://doi.org/10.3892/ijo.2020.5123
- Note: confirmed working 2026-08-18. The University of Liverpool repository copy (livrepository.liverpool.ac.uk/3109887) has the same text and was what the sourcing agent actually used, but it refused two independent connection attempts on re-check (ECONNREFUSED / ECONNRESET) and should not be relied on as a live link.

**Outcome is incident head and neck cancer defined by ICD-10 codes C00-C14 and C30-C31.** ✓✓
- Section: Materials and methods > Outcome
- Quote: “Cases were defined as patients with a diagnosis of HNC, as defined by International Statistical Classification of Diseases and Related Health Problems-10 codes C00-14 and C30-31 (16), and this was used as the outcome measure.”

**Laryngeal cancer (C32) is excluded from the outcome by design, because screening for laryngeal cancer needs different expertise and larynx is not visible on routine oral examination.** ✓✓
- Section: Materials and methods > Outcome
- Quote: “Laryngeal cancer was excluded when building this model, as screening for oral cancers and laryngeal cancers requires different expertise and laryngeal cancer would not be visible during routine oral examination.”

**Prediction horizon is 7 years from baseline recruitment; only incident cases within that window were used.** ✓✓
- Section: Materials and methods > Outcome
- Quote: “Some patients had a diagnosis of HNC prior to recruitment to the UK Biobank study and others developed the disease during or after the study period, and only incident cases of HNC (individuals who developed HNC in the 7 years following recruitment to the UK Biobank study) were included when developing the present risk model.”

**Development population is UK Biobank participants aged 40-69 at entry.** ✓✓
- Section: Materials and methods > Data source
- Quote: “The UK Biobank recruited over 500,000 individuals aged 40-69 years between 2006 and 2010, in 35 assessment centres.”

**Model was fitted on 397,179 complete cases: 232 incident HNC cases and 396,947 controls.** ✓✓
- Section: Tables > Table III (caption), and Materials and methods > Statistical analysis > Missing data
- Quote: “Model Intercept Coefficient -9.54 (95% confidence interval, -11.2 - -7.88; P<0.001). Based on 397,179 observations (n=232 cases and n=396,947 controls with no missing data available for complete cases analysis).”

**Explicit inclusion and exclusion criteria: incident cases only, controls with no registry-recorded HNC as of September 2016, and complete-case analysis (rows with any missing predictor dropped).** ✓✓
- Section: Materials and methods > Outcome; and Materials and methods > Statistical analysis > Missing data
- Quote: “Controls included all participants of the UK Biobank study who did not have a diagnosis of HNC recorded in the Cancer Registries data in September 2016 (15).”

**The 'external' validation is a geographic subset of the same UK Biobank dataset (North West of England), not an independent cohort.** ✓✓
- Section: Materials and methods > Validation dataset
- Quote: “For this reason, the cohort dataset was split geographically, into development and validation sets, to test the model’s performance in a cohort known to have a higher risk of HNC compared with the cohort used to develop the model (25,28).”

**Townsend Deprivation Index is quintiled 1-5 with 1 = least deprived, and quintile 1 is the reference category.** ✓✓
- Section: Materials and methods > Statistical analysis > Data handling
- Quote: “However, to facilitate clinical interpretation, the Townsend Deprivation Index (TDI) variable was categorised into recognised quintiles 1-5 to allow for more meaningful analysis and interpretation of results, with 1 representing least deprived (30).”

**The Townsend Deprivation Index is an AREA-LEVEL measure, not an individual one.** ✓✓
- Section: Materials and methods > Statistical analysis > Model development
- Quote: “TDI is measured over previously-defined Output Areas, which contain ~125 households (30).”

**Exercise is days per week of moderate exercise of at least 10 minutes, banded as 0 / 1-4 / 5 or more, with 0 days the reference.** ✓✓
- Section: Materials and methods > Statistical analysis > Data handling
- Quote: “Exercise was also categorised into “no exercise” or “moderate exercise for at least 10 minutes, 1-4 days per week” and “moderate exercise on 5 or more days of the week”, in line with current NHS guidelines on exercise (32).”

**Fruit and vegetable intake is portions per day, dichotomised at the NHS five-a-day guideline, with <5 per day the reference.** ✓✓
- Section: Materials and methods > Statistical analysis > Data handling
- Quote: “Fruit and vegetable intake was combined and categorised into “< five per day” and “≥ five per day”, in line with current NHS guidelines that everyone should eat at least five portions (400 g) of fruit and vegetables every day (31).”

**Age enters the model as a continuous, uncentred value in years.** ✓✓
- Section: Materials and methods > Statistical analysis > Data handling; and Results > Multivariate model; and Tables > Table III
- Quote: “Continuous variables, such as age, were modelled as continuous to prevent biological implausibility and inefficient use of data (29).”

**BMI is protective (OR 0.96 per unit), the sign is the paper's, not an error.** ✓✓
- Section: Results > Multivariate model; discussed at length in Discussion
- Quote: “Higher BMI also conferred a protective effect (OR=0.96; 95% CI, 0.93-0.99).”

**Alcohol is non-monotonic, previous drinkers carry OR 3.26 while current drinkers carry 1.42 with a CI spanning 1, and this is the sick-quitter pattern.** ✓✓
- Section: Discussion (interpretation); Tables > Table III (values)
- Quote: “The present study reveals previous consumption of alcohol appears to be a greater risk factor for HNC compared with current drinking. It is possible that those currently not drinking have stopped consuming alcohol for health-related reasons, for example alcoholic liver disease.”

**Any stated condition under which the model is invalid or should not be applied.** ✓✓
- Section: Discussion
- Quote: “In addition, the majority of participants within the UK Biobank were born in the UK or Republic of Ireland (93.3% of cases and 92.6% of controls), which may limit the application of the present model outside to these populations.”

**Bootstrapping / internal validation for optimism was not performed.** ✓✓
- Section: Materials and methods > Statistical analysis > Model development
- Quote: “Bootstrapping was not completed as the dataset is sufficiently large, with minimal risk of optimism in predictions due to a good number of events per variable (26,38,39).”

### `ang2010_rpa`: Ang 2010 RPA risk groups

*open access / full text*
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC2943767/
- DOI: https://doi.org/10.1056/NEJMoa0912217

**Population is oropharyngeal cancer only; the HPV analysis and the risk groups do not apply to other head and neck sites.** ✓✓
- Section: Methods > Laboratory Studies
- Quote: “The analysis of tumor HPV status was restricted to patients with oropharyngeal squamous-cell carcinoma because of the low prevalence of HPV among nonoropharyngeal squamous-cell carcinomas.”

**RTOG 0129 enrolled stage III-IV disease (so the risk groups were derived only in locally advanced, M0 patients).** ✓✓
- Section: Methods > Study Protocol
- Quote: “Eligibility criteria were the presence of untreated, pathologically confirmed, stage III or IV squamous-cell carcinoma of the oral cavity, oropharynx, hypopharynx, or larynx without distant metastases (M0)”

**The risk-group decision tree: HPV+ = low risk except smokers with N2b-N3 (intermediate); HPV- = high risk except nonsmokers with T2/T3 (intermediate).** ✓✓
- Section: Results > HPV Status and Survival
- Quote: “Patients with HPV-positive tumors were considered to be at low risk, with the exception of smokers with a high nodal stage (i.e., N2b to N3), who were considered to be at intermediate risk; patients with HPV-negative tumors were considered to be at high risk, with the exception of nonsmokers with tumors of stage T2 or T3, who were considered to be at intermediate risk.”

**The smoking split is 10 pack-years.** ✓✓
- Section: Results > HPV Status and Survival
- Quote: “Recursive-partitioning analysis showed that the HPV status of the tumor was the major determinant of overall survival, followed by the number of pack-years of tobacco smoking (≤10 vs. >10) and then nodal stage (N0 to N2a vs. N2b to N3), for HPV-positive tumors, or tumor stage (T2 or T3 vs. T4), for HPV-negative tumors”

**The paper's wording is genuinely ambiguous: '>10 pack-years' / 'smokers' on the HPV-positive branch but 'nonsmokers' on the HPV-negative branch, with 'nonsmokers' never defined.** ✓✓
- Section: Results > HPV Status and Survival
- Quote: “with the exception of smokers with a high nodal stage (i.e., N2b to N3), who were considered to be at intermediate risk; patients with HPV-negative tumors were considered to be at high risk, with the exception of nonsmokers with tumors of stage T2 or T3”

**Output is a risk group plus its published 3-year overall survival (93.0% / 70.8% / 46.2%), not an individual probability.** ✓✓
- Section: Figure 2 legend (Classification of the Study Patients into Risk-of-Death Categories and Kaplan-Meier Estimates of Overall Survival According to Those Categories)
- Quote: “The 3-year rates of overall survival were 93.0% (95% CI, 88.3 to 97.7) in the low-risk group, 70.8% (95% CI, 60.7 to 80.8) in the intermediate-risk group, and 46.2% (95% CI, 34.7 to 57.7) in the high-risk group.”

**Input domain: pack-years >= 0, and the unit is pack-years.** ✓✓
- Section: Table 1 footnote (marker ‖)
- Quote: “A pack-year is defined as the equivalent of smoking one pack of cigarettes per day for 1 year.”

**Age range of the development cohort.** ✓✓
- Section: Methods > Study Protocol (eligibility); Results > Characteristics of the Patients (Table 1, 'Age, yr')
- Quote: “age of 18 years or older; and adequate bone marrow, hepatic, and renal function”

**Histology / subtype restriction.** ✓✓
- Section: Methods > Study Protocol (eligibility); Methods > Laboratory Studies
- Quote: “untreated, pathologically confirmed, stage III or IV squamous-cell carcinoma”

**Treatment-timing / regimen restriction: the groups were derived in previously untreated patients receiving definitive concurrent high-dose cisplatin chemoradiotherapy.** ✓✓
- Section: Methods > Study Protocol
- Quote: “Patients were stratified on the basis of the tumor site (larynx vs. other), nodal stage (N0 vs. N1, N2a, or N2b vs. N2c or N3), and Zubrod’s performance status score (0 vs. 1) and were randomly assigned to receive high-dose cisplatin concurrently with either accelerated-fractionation radiotherapy (with the acceleration provided by means of concomitant boost radiotherapy) or standard-fractionation radiotherapy.”

**Explicit inclusion and exclusion criteria.** ✓✓
- Section: Methods > Study Protocol
- Quote: “Eligibility criteria were the presence of untreated, pathologically confirmed, stage III or IV squamous-cell carcinoma of the oral cavity, oropharynx, hypopharynx, or larynx without distant metastases (M0)”

**Definition of the HPV input (what hpv_positive=True must mean).** ✓✓
- Section: Methods > Laboratory Studies
- Quote: “An HPV-positive tumor was defined as a tumor for which there was specific staining of tumor-cell nuclei for HPV in either analysis.”

**Outcome definition and prediction horizon.** ✓✓
- Section: Methods > Study End Points
- Quote: “The primary end point was overall survival, defined as the time from randomization to death.”

**Stated condition under which the model is invalid / not yet usable.** ✓✓
- Section: Discussion
- Quote: “Should our risk model be validated in other cohorts, it will be important to incorporate tumor HPV status and tobacco exposure as nonanatomical determinants of risk classification and therapy selection for patients with oropharyngeal squamous-cell carcinoma.”


## Notable discrepancies and gaps this sourcing pass turned up


These are not constraint citations, they are things the sourcing/verification
pass found that this repository should know about, separate from the
constraints audit itself.

1. **`msk_ovarian`'s registry entry states the wrong cohort size.**
   `registry/models.yaml`'s `discrimination_source` field for `msk_ovarian`
   says the reported concordance index (0.67) was bootstrapped on
   "465 patients." The paper's own abstract (Chi et al., *Gynecol Oncol*
   2008;108(1)) states: "A total of 424 evaluable patients with bulky stage
   IIIC EOC underwent primary surgery at our institution during the study
   period of 1/89 to 12/03." 465 does not appear anywhere in the retrievable
   text. Recommend correcting the registry to 424, or sourcing 465 explicitly
   if it comes from an unread part of the Methods.

2. **`capra`'s T3a rule is stated in the Discussion, not the Methods.** The
   quote itself is exact: "Clinical T stage as assessed by digital rectal
   exam was not a significant predictor of outcome in our model except in
   the case of palpable extracapsular extension (stage cT3a) which raises the
   score by 1", but it sits in the Discussion section of Cooperberg et al.
   2005, not the Methods as an earlier note implied.

3. **`crc_pro`'s ethnicity-reference quote in the original sourcing pass was
   a splice.** The reflowed HTML table interleaves standard errors between
   labels; the corrected reading of the same cells is given above.

4. **`msk_rectal`'s age-range quote in the original sourcing pass spliced two
   sentences from two different sections.** The corrected sentence (Results >
   Cohorts) is given above and is the one to cite.

5. **`lipi_prognosis`'s dNLR-definition quote was attributed to the wrong
   paragraph of the Introduction.** Corrected above; the wording itself was
   already exact.

6. **`dutasteride`'s own development paper states none of its numeric
   applicability bounds.** Nguyen et al. 2012 (*Front Oncol*) delegates
   eligibility entirely to the primary REDUCE trial publication (Andriole
   2010, *NEJM*) and contains zero hits for "6- to 12", "past 6 months",
   any age range, or any inclusion/exclusion criteria. The bounds table in
   `docs/MODEL_CONSTRAINTS.md` and in `dutasteride.py`'s own docstring come
   from the deployed calculator (riskcalc.org), which is what the module
   docstring already says, flagged here only so the distinction is not lost
   in this document's per-model card, which otherwise reads as if the paper
   stated them.

7. **Three links in an earlier draft of this document were broken or
   truncated**, all now fixed above: `pbcg_extended`'s Additional file 1 URL
   was cut off mid-string by a `[:140]` slice in the rendering script (fixed
   generally, no URL in this document is truncated); `ukb_hnc`'s original
   University of Liverpool repository link refused two independent connection
   attempts on recheck; `msk_pancreatic`'s direct PDF link 404s cold (the PMC
   article page's own download button works; the raw URL does not).
