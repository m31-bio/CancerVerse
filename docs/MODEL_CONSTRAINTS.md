# Flagship model constraints

What each flagship model may and may not be applied to, and, separately,
what its code actually stops you from doing. The two are not the same, and the
gap between them is the point of this document.

Scope: the 34 `role: flagship, status: implemented` entries in
`registry/models.yaml`. Two flagship rows are `catalog` (`nci_crc`, `pancpro`)
and five are `gap`; those have no code and are covered by their `blocker`
fields instead.

Method: every module read in full on 2026-08-18, then every model called
through `cancerverse_baseline.predict` with out-of-range inputs to see what it
rejects. The "enforced" column is what the code did, not what the docstring
says it does.

---

## 1. The eight kinds of constraint

A model can be inapplicable in more ways than an age range, and the ways are
worth naming separately because different ones are caught by different checks.

| # | Kind | Example in this library |
|---|---|---|
| 1 | **Population / setting** — who was in the development cohort, and at what point in their care | `msk_rectal`: incomplete pathological responders only; complete responders go to a different estimator |
| 2 | **Demographic range** — age, sex, race/ethnicity levels, region of calibration | `prevent`: 30–79 at 10 years, 30–59 at 30 years |
| 3 | **Disease subtype** — histology, receptor/marker status, anatomic site | `kunzmann`: adenocarcinoma only, never squamous |
| 4 | **Stage / treatment timing** — pre-op vs post-op, which line of therapy, which regimen | `cibula_arrm`: all five inputs are surgical pathology, so it cannot be run pre-operatively |
| 5 | **Required vs optional inputs, and the missing-data policy** | `pbcg_extended`: age + PSA mandatory, the other ten select one of 1,024 sub-models, nothing imputed |
| 6 | **Value domain and units** — fitted ranges, spline anchors, unit conventions | `msk_pancreatic`: size 0.1–16 **cm** although the hosted tool's label says mm |
| 7 | **Outcome and horizon** — what is predicted, over what window, on what scale | `ukb_hnc`: 7-year incident C00–C14 and C30–C31, with laryngeal C32 deliberately excluded |
| 8 | **Known invalidating conditions** — states in which the model is wrong rather than merely uncertain | `abc_method`: invalid after *H. pylori* eradication, because seroreversion moves high-atrophy patients into the low-risk groups |

---

## 2. Constraint cards, by disease

Each card: population, hard constraints, input policy, and what the code
enforces. `✓` = the code raises; `—` = documented but not enforced.

### Prostate

**`pbcg_extended`, detection (high-grade prostate cancer on biopsy)**
- Population: men **referred for biopsy** (PBCG, ten international cohorts). Not screening in an unreferred population.
- Outcome: **high-grade only**, Gleason grade group ≥ 2. It does not report risk of any cancer; the 2018 predecessor did.
- Required: `age`, `psa` ✓. Ten optional predictors select one of 1,024 fitted sub-models; nothing is imputed.
- Domain: PSA > 0 ✓ and prostate volume > 0 ✓ (both enter as log₂). No age range and no PSA ceiling of any kind.
- Trap: the **African-ancestry coefficient changes sign** across sub-models (protective in 412, harmful in 100, a count obtained by tallying the published coefficient matrix, not a figure the paper reports). Which sub-model a patient lands in is decided by which optional fields the caller filled in, so supplying *more* data can flip that term. Not a population effect.

**`capra`, prognosis (recurrence after radical prostatectomy)**
- Population: **pre-operative**, localised disease. CAPRA-S (post-op) is a different model and is not implemented.
- Hard constraint: **T1 / T2 / T3a only** ✓. T3b and T4 raise. This is the one clinical-stage gate anywhere in the library that is enforced by a category check rather than a range.
- Required: PSA, both Gleason patterns, T stage, % positive cores, age, all mandatory.
- Domain: PSA > 0 ✓, Gleason patterns 1–5 ✓, % cores 0–100 ✓, age > 0 ✓ only, no upper age bound and no PSA ceiling.
- Output: a 0–10 point score and a band. `risk` is None, but the reason previously given here ("mapping score to survival needs cohort-specific outcome tables that are not shipped") was misleading. **The paper does publish those tables**: Table 3 gives crude recurrence rates by score and Table 4 gives 3- and 5-year recurrence-free survival for every score level ("Recurrence-free survival at 5 years ranged from 85% for a CAPRA score of 0-1 … to 8% for a score of 7-10"). They are not shipped because nobody transcribed them, which is a gap in this library, not a limitation of the source.
- **The 0–2 / 3–5 / 6–10 risk bands are not in the paper.** Cooperberg 2005 defines no categorical low/intermediate/high grouping; it reports outcomes by score, grouping as 0-1 … 7-10 where it groups at all. The tercile banding this module returns (and `capra.py`'s `LOW_MAX` / `INTERMEDIATE_MAX`) is conventional in later CAPRA literature but is not sourced to the citation the module names, which points at "PMC2948569 Table 1".

**`dutasteride`, response (chemoprevention, 9 outcomes × 2 arms)**
- Population: REDUCE, men with a **prior negative 6- to 12-core biopsy in the past 6 months**. Note the provenance: **that phrase is not in the modelling paper.** Nguyen 2012 delegates eligibility entirely to the primary REDUCE trial report (Andriole 2010, *NEJM*) and contains no core-count, no time window, and no age range of its own. The wording comes from the deployed riskcalc.org calculator.
- Per-outcome applicability bounds, enforced ✓ (returns `None`, not an error, matching the tool's "Not Applicable"). **These come from the deployed calculator's R source, not from the paper.** Nguyen 2012 reports cohort means only (PSA 5.9, %free PSA 16.7, BMI 27.3) and states no input domains anywhere:

  | outcome | age | PSA | cores | %free PSA | BMI | IPSS | Qmax | volume |
  |---|---|---|---|---|---|---|---|---|
  | high-grade / any PCa / HGPIN | 50–75 | 2–10 | 6–12 | 0–64 | 15–50 | — | — | 0–80 |
  | AUR / BPH progression | 50–75 | 2–88 | — | — | — | 0–25 | 0–100 | 0–80 |
  | gynecomastia | 50–75 | — | — | — | 15–50 | — | — | — |
  | erectile dysfunction | 50–75 | — | — | — | — | — | — | — |
  | UTI | — | — | — | — | — | — | 0–100 | — |

  A patient can therefore be answerable for some outcomes and not others.
- Structural asymmetries reproduced, not smoothed: **ASAP has no off-treatment arm** (difference is `None`), and **HGPIN on dutasteride is a constant 3.838831%** for everyone in scope.
- Four of the nine outcomes have concordance at or below chance in at least one arm; the paper says so.

### Cardiovascular

**`prevent`, detection (5 outcomes × 2 horizons × 5 variants)**
- Age: the paper states **one** range for the whole model: "adults aged 30 to 79 years without known ASCVD or HF at baseline", and never narrows it by horizon. Our code nonetheless enforces **30–79 at 10 years and 30–59 at 30 years** ✓, refusing a 65-year-old's 30-year risk outright. **That is stricter than both the paper and the reference implementation**: `preventr` treats age > 59 at the 30-year horizon as a warning ("Estimating 30-year risk in people > 59 years of age is questionable", `estimate_risk.R:1326`) and still returns an estimate. The restriction is defensible (a 30-year horizon from age 79 runs to 109) but it is *our* judgement, not a published bound, and it is the one place in this library where we refuse an answer the canonical implementation gives.
- Sex required ✓ (100 coefficient sets are sex-specific).
- Variant is auto-selected by which optional labs are supplied (0 → base, exactly 1 → that single-predictor model, 2–3 → full, each missing lab scored via its own indicator). That is the published rule, not an imputation choice.
- **BMI moves only the heart-failure outcome.** For total CVD / ASCVD / CHD / stroke the BMI coefficients are exactly 0 in all 40 relevant sets. A caller who supplies BMI expecting their CVD risk to change gets no change, correctly.
- Regional: US calibration. Use `score2` for a European patient, that is a question of where the patient is, not which model is better.
- **Gap:** no bound on cholesterol, HDL, SBP, BMI, eGFR or HbA1c. See §3.

**`grace`, prognosis (in-hospital mortality in ACS)**
- **Version-critical.** This is the **2003 points nomogram for in-hospital mortality**. It is *not* the Fox BMJ 2006 6-month post-discharge score and *not* GRACE 2.0. A guideline citing GRACE 2.0 expects different numbers.
- Population: an acute coronary syndrome admission.
- Band boundaries are **upper-inclusive**, disambiguated by the paper's own worked examples, not by the printed labels. SBP exactly 100 scores 53, not 43. Coded literally the model is wrong at one of the most common systolic readings there is.
- Domain: Killip 1–4 ✓; SBP / HR / age / creatinine each > 0 ✓; nothing else. Risk is clamped at the published table ends (≤ 60 points → 0.2%, ≥ 250 → 52%).
- Units: creatinine in **mg/dL**.

**`atria_stroke_2013`, prognosis (stroke in atrial fibrillation)**
- Population: **atrial fibrillation**, anticoagulation decision. It is filed as flagship for the CVD prognosis cell only because a cell allows one default, it answers a different question from GRACE. Pick by population, never by the label.
- Age enters through an **age × prior-stroke interaction**, not an age term plus a stroke flag. Two disjoint score ranges result: 0–12 without prior stroke, 7–15 with one.
- Output: a band (≤5 low / 6 moderate / ≥7 high). **No per-point annual rate is shipped.** That is a repository decision, not a limitation of the source: Table 4 does publish event rates per point score. The stated reason (external validations disagree at point level) is our judgement and is not something the paper says.
- Domain: age ≥ 0 ✓ only.

**`cvd_statin_benefit`, response (LDL-lowering absolute benefit)**
- **Not a published model.** It is guideline arithmetic composing a CTT 2010 trial effect onto a baseline risk that the caller supplies. Registry marks it `derived_not_published`.
- The horizon, endpoint and population are **whatever the baseline risk model's were**, that is why it takes the baseline as an argument rather than computing it.
- Four assumptions travel with every result and are returned in the payload: constant proportional effect; a ~5-year trial effect carried to a 10-year horizon; CTT's major-vascular-events endpoint approximating the baseline model's; and a CI covering the trial effect only, not baseline uncertainty (usually the larger source).
- Domain: baseline risk in [0,1] ✓, exactly one LDL unit ✓, outcome in the two published ones ✓.

### Breast

**`bcsc_v2`, detection (5-year invasive breast cancer)**
- Age: our code enforces **35–79** ✓, but only the **lower** bound is the paper's. Tice 2008 says "We included 1 095 484 women age 35 years or older…" and states no upper limit; its own results tables run to the **80–84** age band, which is evidence against a 79 ceiling rather than for one. The upper bound is this library's addition and currently refuses a patient the paper reports on.
- Race: **white / black / asian / hispanic** ✓. American Indian / Alaska Native was excluded from the paper for inconsistent SEER rates, so there is no fifth group and no fallback.
- Density: BI-RADS **1–4** ✓, with 2 as the reference the model was standardised to.
- Outcome: **invasive** breast cancer, **5 years only**. There is no 10-year extension for this version.
- Missing-data policy: `family_history=None` / `biopsy_history=None` mean *skip the multiplier*, per the paper, not impute an average.
- Sex: women. No parameter, no check.

**`predict_breast` / `predict_breast_response`, prognosis + response (PREDICT v2.2)**
- One model in two cells; the response cell re-exports the prognosis module.
- **ER status is structural, not a coefficient.** ER-positive and ER-negative use *different fractional-polynomial transforms* for age and size, and ER-negative collapses grade to a binary. `er_positive` is mandatory.
- **Ki-67 is used only when ER-positive.** Supplying it for ER-negative disease does nothing.
- Trastuzumab applies only when `her2 == 1`; extended endocrine therapy affects **years 11–15 only** and is a **separate treatment arm** in the reference, not an automatic consequence of `hormone`.
- **Radiotherapy is gated off** (`r.enabled = 0` in v2.2) and mirrored as such.
- Horizon: **1–15 years** ✓.
- Domain: grade ∈ {1,2,3,9} ✓, her2/ki67 ∈ {0,1,9} ✓, chemo generation ∈ {0,2,3} ✓, screen_detected ∈ {0,1,2} ✓; age > 0, size > 0, nodes ≥ 0 ✓ only.
- **Gap:** `screen_detected` defaults to `0` ("clinically detected"), not to `2` ("unknown", imputed 0.204). See §3.

### Lung

**`plcom2012`, detection (6-year lung cancer)**
- Population: **ever-smokers only**, enforced indirectly ✓ by requiring cigarettes/day > 0 and duration > 0. Never-smokers cannot be scored, correctly.
- Consistency check: `current_smoker=True` requires `quit_years == 0` ✓.
- Race: six fixed groups ✓ with aliasing. Education 1–6 ✓.
- Horizon: **6 years, unscreened natural history**, no low-dose CT effect.
- **Gap:** this repo records the development cohort as PLCO smokers aged 55–74 (see §3.3 on the provenance of that figure); the code enforces no age bound at all. Note the vendored reference implementation `collected/PLCOm2012/R/plcom2012.R` enforces none either.

**`lipi` / `lipi_prognosis`, response + prognosis**
- Population: **advanced NSCLC**, the response cell for immune-checkpoint-inhibitor outcomes.
- LDH is compared to the **reporting lab's own upper limit of normal**, both the value and its ULN are mandatory ✓. There is no universal cutoff.
- dNLR = neutrophils / (leukocytes − neutrophils); supply the ratio or the two counts, not both ✓, and leukocytes must exceed neutrophils ✓.
- Output: a 0–2 score and a three-level group. **No probability, and no c-index anywhere in the paper**, its evidence is separation (median OS 34 / 10 / 3 months).

### Colorectal

**`crc_pro`, detection (10-year colorectal cancer)**
- **Two entirely different models by sex**, with different predictor sets, not one model with a sex term. Women get NSAIDs and oestrogen; men get red meat, physical activity and aspirin.
- Ranges all enforced ✓: age **45–85**, weight 75–350 **lb**, height 60–80 **in**, pack-years 0–50, alcohol 0–12 drinks/day, education 6–20 years, activity 0–4 h/day, red meat 0–5 oz/day.
- **Units are imperial.** The spline knots assume the app's own lb/in → BMI conversion.
- Ethnicity: **Hawaiian / Japanese / Latino / White / Black** ✓, Multi-Ethnic Cohort only, **Black is the reference level**.
- Deployed-calculator defect corrected here: the hosted tool cannot reach its own "previous oestrogen use" coefficient, so previous use scores like none. This module implements the paper (all three levels live); `emulate_deployed_defect=True` reproduces the tool for parity.
- **Gap:** sex-mismatched predictors are accepted and silently ignored. See §3.

**`wang_larc_pcr`, response (pCR after neoadjuvant chemoradiotherapy)**
- Population: **locally advanced rectal cancer, staged BEFORE chemoradiotherapy**, in patients who go on to complete nCRT and surgery. All six inputs are pre-CRT values; feeding yp staging in is a different model.
- CEA bounded to **0–24 ng/mL** ✓, the authors' own slider range and the paper's explicit "≥ 24" floor. Outside is refused, not extrapolated.
- **Direction reversal:** `risk` here is the probability of a *good* outcome. Higher is better. `p_pcr` is provided under its own name for that reason.
- **T stage is not monotone and cT2 is the reference**, cT3 scores *more* likely to achieve pCR than cT2. Reproduced, not tidied.
- Development: two Chinese centres. Transportability untested beyond them.

**`msk_rectal`, prognosis (RFS and OS after CRT + surgery)**
- Population: **incomplete pathological responders only**. Complete responders are handled by a Kaplan–Meier estimate in the source tool and are outside this equation.
- **The two endpoints use different ypT reference groups.** RFS against ypT0/T1, OS against ypT0/T1/T2. Applying the RFS coding to OS silently misprices every ypT2 patient.
- `age` is **required for OS and unused for RFS** ✓.
- Horizon: **only 0 / 60 / 120 / 180 months** ✓, the published S0 grid. Interpolation is refused rather than invented.
- Reproduced oddity: **OS can come out below RFS** for an older patient, because only the OS model carries age. MSK's own tool does this too.

### Liver

**`amap`, detection (5-year HCC in chronic hepatitis)**
- Population: **chronic hepatitis** (11 global cohorts). Not general-population HCC screening.
- Units are strict: bilirubin µmol/L, albumin g/L, platelets ×10³/mm³ ✓, both labs accept SI or US form but exactly one of each ✓.
- Output: a **0–100 stratifier and a band** (<50 low / 50–60 medium / ≥60 high). `risk` is deliberately `None`: the paper prints an S0 but whether the linear predictor is mean-centred is unresolved, and getting that wrong is a ~1.4× hazard multiplier.
- **Unresolved:** the custodial CUHK calculator sits 2–3 points above the published formula at every probe point. This module implements the published formula and leaves `parity_status` accordingly.
- Domain: all four inputs > 0 ✓; no age bound.

**`albi`, prognosis (liver function grade)**
- **Grades liver function, not tumour burden.** It is used alongside BCLC staging, not instead of it.
- Output: score and grade 1/2/3. No probability.
- Units: µmol/L and g/L, or the US forms, exactly one of each ✓.
- Domain: both > 0 ✓ only. Albumin 200 g/L is accepted.

**`hap`, response (pre-TACE prognosis / candidacy)**
- Population: HCC patients **being considered for transarterial chemoembolisation**.
- **Albumin must be g/L, deliberately.** The paper prints "< 36 g/dl" in four separate places; that is a unit error by a factor of ten, and every independent restatement uses g/L. The module requires g/L on purpose.
- Grade **D absorbs both 3 and 4 points**; the paper's boundary is "> 2", and that asymmetry is the paper's.
- Median OS figures are the **UK derivation cohort's** and do not transfer; external validation produced different absolutes and prompted mHAP / mHAP-II / mHAP-III, none implemented.

### Gastric

**`abc_method`, detection (serological groups A–D)**
- Population: **asymptomatic Japanese health-checkup endoscopy attendees** (mean age 48.9, 68% male).
- **Invalid after *H. pylori* eradication**, seroreversion moves persistently high-atrophy patients into groups A/B. `prior_eradication=True` flags this in `notes`; it does **not** refuse to score.
- **Assay-specific** (Biomerica GAP-IgG; the PG I ≤ 70 and PG I/II ≤ 3.0 cutoff pair). Does not transfer across assays without a bridging study.
- Absolute rates are Japanese rates. **The ordering transfers, the numbers do not.**
- Group ordering is not monotone in either test alone. **Group D (seronegative *with* atrophy) is the highest-risk group**. That interaction is the method.
- Group B is not statistically distinguishable from A (HR 1.1, 95% CI 0.4–3.4).

**`xu_gastric_trg_score`, response (complete regression after preoperative chemo)**
- Population: **locally advanced gastric adenocarcinoma receiving neoadjuvant chemotherapy**; endpoint is Ryan TRG 0 at resection.
- **Higher score = more likely to achieve complete regression.** The paper calls > 13 the "high-risk" group and that group has the *better* outcome; this module refuses that label and names the groups `high_likelihood` / `low_likelihood`.
- **A larger lymph node scores toward complete response**, inverted relative to the usual reading of nodal burden, deliberate, and the first thing to check if the model fails to transport.
- The cut-off is unambiguous: only twelve of twenty-four totals are reachable and **a score of exactly 13 cannot occur**.
- Output: a group, **not a probability**. The paper's 0% in the low group is 0 events, not a probability of zero.
- Evidence is thin: single centre, 30 TRG=0 events, ~5 events per variable, no calibration ever assessed.

**`msk_gastric`, prognosis (DSS after R0 resection)**
- Population: **after R0 resection** for gastric carcinoma.
- Ranges enforced ✓: age **25–96**, positive nodes **0–23**, negative nodes **0–146**, size **0.1–21 cm**. Horizon **5 or 9 years only** ✓.
- **Depth of invasion is an ordinal entered as a number 1–7 and then splined**, in the order mucosa → submucosa → propria muscularis → subserosa → suspected serosal → definite serosal → adjacent organ. Reordering the levels silently changes every prediction.
- Reference levels carry no term: **female, Lauren diffuse, antrum/pyloric**. Diffuse is the reference even though it is the worst-prognosis Lauren type, so both other types carry negative coefficients.
- **Negative nodes protect, strongly** (−0.047 per node, count running to 146), stage migration, not an error.

### Oesophageal

**`kunzmann`, detection (oesophageal adenocarcinoma)**
- **Adenocarcinoma only, never squamous.** Different disease, different risk factors. Applying it where ESCC predominates is a category error.
- Age **≥ 50** ✓, the developed range. No upper bound.
- Population: **UK Biobank volunteers aged 50+**, not primary care: "355,034 individuals (all older than 50 years) without a prior history of cancer enrolled in the UK Biobank prospective cohort study". An earlier draft of this document said "UK primary care", copying the module docstring; both were wrong and the registry was right. The distinction is a transportability one: UK Biobank's healthy-volunteer bias means its absolute risks do not carry to an unselected primary-care list.
- Output: 0–15 points with a **referral threshold of ≥ 8**. No probability.
- Male sex alone carries 4.0 of the 15 available points, half the referral threshold.

**`chau_eg`, response (survival on first-line palliative chemotherapy)**
- Population: **locally advanced or metastatic** oesophago-gastric cancer **at the start of first-line fluorouracil-based palliative chemotherapy**. Says nothing about resectable disease.
- **Histology was 88% adenocarcinoma and 4.6% squamous.** This is *not* a model for oesophageal squamous cell carcinoma.
- **Treatment era is 1992–2001** (ECF, FAMTX, MCF, PVI FU ± mitomycin C), predates trastuzumab, predates checkpoint inhibitors entirely.
- The **response half of the paper is deliberately not implemented**: Table 4 is a different model (only three of four factors survive; liver metastasis does not predict response at all) with no intercept and no per-band response rate.
- Output: a 0–4 count and a three-level band. No probability.
- Domain: performance status 0–4 ✓, ALP ≥ 0 ✓.
- The authors state the index "requires validation"; **no completed external validation is claimed**.

**`shapiro_ncrt`, prognosis (OS after nCRT + surgery)**
- Population: oesophageal or junctional carcinoma treated with **CROSS-regimen nCRT followed by resection**. Two of three inputs are post-resection pathology, so **it cannot be run pre-operatively** and says nothing about whether to operate.
- **Staging editions are mixed and enforced by level name** ✓: `cN` is UICC TNM **6th edition and binary** (cN0/cN1 only, not the modern N0–N3); `ypT` and `ypN` are **7th edition**. Feeding 8th-edition categories or a three-level cN raises.
- **Four of thirteen reachable scores have no published survival** and return `None` (5, 7, 9, 11, every ypN2 patient, 9.6% of the derivation cohort). A Cox fit reproduces the printed axis to 0.36 pp and would fill the gap convincingly, which is exactly why it is not used.
- Discrimination is **weak**, c-index 0.63 internal, 0.61 external, and should be quoted whenever the model is.
- Squamous histology is well represented here (22.2%), unlike `chau_eg`. The two oesophageal models differ in applicability by histology; do not carry the `chau_eg` caveat across.

### Ovarian

**`iota_adnex`, detection (five-category adnexal mass classification)**
- Population: women with **at least one adnexal mass, examined by an experienced ultrasound operator and selected for surgery**. It estimates what a mass *is*, not whether one is present, and is **not a screening model**.
- **CA-125 is mandatory here** ✓, although it is optional in clinical use of ADNEX: Appendix D publishes only the with-CA-125 formula, and the without-CA-125 variant is a separately fitted model the supplement does not give.
- **`oncology_centre` is a predictor and is not a patient characteristic**, it encodes referral filtering. A prediction is only interpretable if it matches where the scan was actually done.
- Domain: CA-125 > 0 ✓ and lesion diameter > 0 ✓ (both enter as log₂); solid diameter ≥ 0 ✓ and **must not exceed lesion diameter** ✓.
- Output: a distribution over **five** diagnoses: benign, borderline, stage I invasive, stage II–IV invasive, secondary metastatic. "Malignant" does not distinguish a borderline tumour from a stage III cancer, and the surgery differs.
- **Gap:** `oncology_centre` defaults to `False`. See §3.

**`msk_ovarian`, prognosis (5-year survival after primary surgery)**
- Population: **bulky stage IIIC** ovarian carcinoma, **after primary surgery**.
- Ranges enforced ✓: age **22–87**, pre-operative platelets **113–1078** ×10³/µL. Horizon fixed at 5 years.
- **The residual-disease reference is the middle category, 0.5–1 cm.** Two categories carry negative coefficients and two positive. A reader expecting "no residual disease" to be the reference will misread every coefficient.
- **`histology_yes` has no recoverable meaning.** The hosted tool labels it only "Tumor Histology / Yes–No"; the paper's series is serous carcinoma but the code does not say so. Read Chi 2008 before clinical use.
- Internal validation only, no external cohort.

### Cervical

**`cervical_cin_risk`, detection (CIN2+/CIN3+)**
- Population: **Chinese screening population**. Outcome is **CIN2+/CIN3+ at colposcopy**, not invasive cancer incidence over time.
- **Cytology must be Bethesda**, one of seven levels ✓, with **NILM as the reference**.
- Four nested variants ✓: `base`, `e6`, `genotyping`, `full`. Each raises if you supply an input it does not use, or omit one it needs, no silent fallback.
- **Genotype groups are the paper's pooled sets** (33/58, 59/56/66, 39/68/35) ✓ and are not interchangeable with other groupings.
- Age carries a small **negative** coefficient. Conditional on hrHPV and cytology, older women in this screening population were at slightly lower CIN risk. Do not correct the sign.
- Domain: age > 0 ✓ only.

**`moore_criteria`, response (cisplatin-based chemotherapy)**
- Population: **advanced, recurrent or metastatic** cervical carcinoma **starting cisplatin-based chemotherapy** (GOG 110/169/179/149). It is *not* a model for response to primary chemoradiation in newly diagnosed non-metastatic disease.
- **One of the five inputs is race** (Black vs non-Black, per Table 3). Reproduced as published; flagged in `notes` on every result that uses it; a cohort-specific association, not a mechanism.
- **`disease_site` has an unresolved level.** The source records pelvic / distant / combined but the tested factor is binary pelvic vs non-pelvic, and the paper never says where "combined" (13.1% of the cohort) went. This module reads the label literally and files combined as non-pelvic, flagging every case where that inference fired.
- Two inputs are collapsed here at the paper's own cut-points: performance status > 0, and **months from original diagnosis to first recurrence** ≤ 12, note that is from diagnosis, not from the start of the chemotherapy being evaluated.
- Output: a 0–5 count and a three-band index. **No probability.** Table 3's logistic model has no printed intercept anywhere.
- Domain: performance status 0–4 ✓, months ≥ 0 ✓.

**`cibula_arrm`, prognosis (annual recurrence risk after primary surgery)**
- Population: **early-stage cervical cancer treated by primary surgery**. All five inputs are surgical pathology, so it **cannot be run before an operation** and **does not apply to patients treated with definitive chemoradiation**, who never produce a specimen. Tumour diameter is the pathologic measurement, not the imaged one.
- **The annual risk is conditional, not cumulative**, the year-3 figure is the risk for a patient already recurrence-free for two years.
- **Two predictors pool "not assessed" with "negative"**: positive pelvic nodes and LVSI. A patient who never had a lymphadenectomy scores exactly like a node-negative one. That is the published model, built to be usable where the work-up is incomplete, but **a missing field here is silently optimistic**. Passing `None` is allowed, does what the paper does, and says so in `notes` every time.
- **Grade does not work that way** ✓. Table 2 has no "not assessed" level for it, missing grade was multiply imputed during fitting, and an unknown grade raises rather than defaulting to 1.
- The 76–100 band holds 13 patients, 12 of whom recurred; years 4 and 5 return `None` because there is nobody left in the band, not because there is no risk.

### Pancreatic

**`endpac`, detection (pancreatic cancer in new-onset diabetes)**
- Population: adults with **glycemically-defined new-onset diabetes**. It enriches an already-selected group, **not a general-population screen**. Validation work is in ≥ 50-year-olds.
- **The glucose pair is enforced** ✓: the reading one year before must be < 126 mg/dL and the reading at diabetes onset ≥ 126 mg/dL. Without this an out-of-scope pair (say, a *fall* from diabetic to normal) silently yields a score far outside the published 1–4 range.
- The glucose term is a **difference of category indices, not of mg/dL**. A rise from 95 to 130 is category 1 → 4, i.e. A = 3.
- **Weight loss is positive.** Losing ≥ 6 kg scores +6; gaining ≥ 6 kg scores −6. A sign error inverts the model.
- Bands partition the score line exhaustively: ≥ 3 high, 1–2 intermediate, **≤ 0** low. The abstract's "< 0" is a typo; the Results text and the group proportions (which sum to exactly 100% in both cohorts) settle it.
- Domain: glucose > 0 ✓, age > 0 ✓. No age floor despite the ≥ 50 validation.

**`msk_pancreatic`, prognosis (DSS after resection)**
- Population: **after resection for adenocarcinoma of the pancreas**.
- Ranges enforced ✓: age **33–89**, positive nodes **0–39**, negative nodes **0–83**, size **0.1–16 cm**. Horizon **12 / 24 / 36 months only** ✓.
- **Units:** size is **centimetres**. The hosted tool's label says "Maximum Path Axis (mm)", which is not credible at a 16-unit ceiling with spline knots at 2, 3.2 and 5.5. A user entering "8" meaning 8 mm would be scored as an 8 cm tumour.
- **T stage is not monotone**: against a T1 reference, T2 is −0.537 and T3 is −0.387, both *better* than T1, while T4 is +0.387. Reproduced as published.
- **Splenectomy is the largest single term** (+0.907), a marker of extended resection for locally advanced disease, not a treatment effect.
- **Gap:** 12 of 14 predictors have silent defaults. See §3, this is the most serious finding in this audit.

### Head and neck

**`ukb_hnc`, detection (7-year head and neck cancer risk)**
- Outcome: incident **ICD-10 C00–C14 and C30–C31 within 7 years** of baseline. **Laryngeal cancer (C32) is excluded by design**, the authors dropped it because screening for laryngeal cancer needs different expertise and it is not visible on routine oral examination. A caller who wants all head and neck sites is asking a different question.
- Population: **UK Biobank, aged 40–69 at entry**.
- **The Townsend Deprivation Index is a UK area-level measure with no US equivalent**, quintiled with 1 = least deprived. Exercise days per week and five-a-day intake are questionnaire items. Three of eight predictors have no routine EHR source.
- **BMI is protective** (OR 0.96 per unit) and **alcohol is non-monotonic**, previous drinkers carry OR 3.26 while current drinkers carry 1.42 with a CI spanning 1 (the sick-quitter pattern). Deprivation is non-monotonic too. Do not correct these.
- Domain: age in (0, 120) ✓, BMI in (5, 100) ✓, plausibility bounds, not the developed 40–69 range.
- The "external" validation is a geographic subset of the same dataset, not an independent cohort.

**`ang2010_rpa`, prognosis (HPV / smoking / stage risk groups)**
- Population: **oropharyngeal** cancer; RTOG 0129 enrolled **stage III–IV** disease.
- Two operationalisations, selectable ✓. `definition="ang2010"` (default) is the literal primary reading: HPV-negative, low-smoking, **T2/T3** → intermediate, so T1 → high. `definition="fakhry"` follows the external validation's "< T4", so T1 → intermediate. **They differ for exactly one cell.**
- The smoking split is **10 pack-years** and is applied to both branches either way; the primary text says ">10 pack-years" on one branch and "nonsmokers" on the other, and Fakhry's validation settles it.
- Output: a group plus its published 3-year OS. No individual probability, and **no AUC or c-index is reported anywhere in the paper**.
- Domain: N stage N0–N3 ✓, T stage T1–T4 ✓, pack-years ≥ 0 ✓.

---

## 3. Where code and paper diverge

These are the constraints a model is documented to have but does not enforce.
Ranked by how much a wrong answer would be trusted.

### 3.1 `msk_pancreatic`: 12 of 14 predictors silently default

The signature requires only `age` and `male`. Everything else has a default,
and the defaults are a **specific fictional patient**: `size_cm=3.0`,
`t_stage='1'`, `positive_nodes=0`, `negative_nodes=0`,
`differentiation='moderate'`, `location='head'`, all boolean findings `False`.

```
predict("msk_pancreatic", age=60, male=True, months=12)          -> S = 0.665
same patient with real pathology (4.5 cm, T3, 6+ nodes, poor,
margin positive)                                                  -> S = 0.437
```

A caller who omits the pathology gets a confident 67% rather than an error.
Contrast `pbcg_extended`, which selects a sub-model fitted without the missing
field, and `dutasteride`, which returns `None` outside its bounds. Both are
the right pattern; this model is the outlier.

Recommendation: make the twelve default to `None` and raise, or route them
through an explicit `assume_defaults=True`.

### 3.2 `prevent`: no bound on any input except age

Age is enforced per horizon, and `sdi_decile` 1–10 and `uacr` > 0. Nothing
else is. Total cholesterol 1000 mg/dL, HDL 500, SBP 400, BMI 200, eGFR 500 and
HbA1c 40% are all accepted and score.

The canonical implementation the registry already names, `preventr`, MIT,
vendored at `collected/preventr/`, enforces all of them. Its table is
`collected/preventr/R/helpers.R:369-413`, applied by `check_range` at
`helpers.R:417` and called per variable at `helpers.R:475-576`:

| input | preventr bound | enforced here |
|---|---|---|
| age (PREVENT) | 30–79 | ✓ (and 30–59 at the 30-year horizon) |
| total cholesterol | **130–320** mg/dL (3.36–8.28 mmol/L) | — |
| HDL | **20–100** mg/dL (0.52–2.59 mmol/L) | — |
| SBP | **90–180** mm Hg | — |
| BMI | **18.5–39.9** kg/m² | — |
| eGFR | **15–140** mL/min/1.73 m² | — |
| HbA1c | **4.5–15** % | — |
| UACR | **0.1–25000** mg/g | > 0 only |

Two of these have a stated provenance in the source itself. The BMI bound
carries the comment `# Table 1, footnote re: excluding people based on BMI`,
i.e. it is the development cohort's own exclusion, not a display convenience.
The creatinine and height/weight bounds are deliberately left open with the
comment that "imposition of further restriction would be somewhat arbitrary
given valid input is ultimately determined by eGFR, not creatinine"; so the
absence of a bound there is a considered decision, and the presence of one on
the eight above is too.

Note the SBP ceiling is **180**, not 200. An earlier draft of this document
guessed 200; the vendored source says otherwise. Read the file, do not recall
the number.

This is the most-used model in the library and the one whose inputs come
straight from a lab feed, where a unit error or a sentinel value is most
likely. Recommendation: mirror the eight bounds and pin them in a test the way
`AGE_RANGE` is pinned.

### 3.2b What the other vendored reference implementations do

`prevent` is the only model whose gap is against its own reference
implementation. The other three vendored references impose **no input bounds at
all**, so on this point our code matches them and any gap is against the paper,
not against the canonical code:

| vendored reference | validation present? |
|---|---|
| `collected/preventr/R/helpers.R` | **yes** — the eight-row table above |
| `collected/predictv30r/R/benefits22.R` (PREDICT v2.2) | none — no bound on age, size or nodes anywhere in the package |
| `collected/PLCOm2012/R/plcom2012.R` | none — the function is the linear predictor and nothing else |
| `collected/BCRA` | (BCRAT, not a flagship — `bcsc_v2` replaced it) |

That distinction matters for triage. A missing bound that the reference
implementation *does* impose is a defect. A missing bound that no reference
imposes is a policy decision this library gets to make, and should make
explicitly rather than by omission.

### 3.3 Development-range age limits that are documented but not enforced

Every row below is now sourced to a section and a verbatim sentence in the
original paper, full citations in `docs/MODEL_CONSTRAINTS_SOURCES.md`. Two
rows changed once actually checked against the text: `capra`'s paper states a
mean age (62), not a range, so "adult men" is corrected to say that plainly
rather than imply a bound the paper never gives; `cervical_cin_risk`'s
screening-cohort age range is stated explicitly (25–65) and was previously
missing here. The "enforced" column is first-hand: what the function did when
called with out-of-range values on 2026-08-18.

| model | what the paper actually says | source | enforced by the code |
|---|---|---|---|
| `plcom2012` | "an age between 55 and 74 years was an entry criterion [in PLCO and NLST]... predictive performance of the PLCOm2012 outside this age range is uncertain" | Tammemägi 2013, NEJM, Results | no age bound at all |
| `endpac` | age reported as mean ± SD in Table 1, not as a range; validation cohort described as "adults" with new-onset diabetes | Sharma 2018, *Gastroenterology*, Table 1 | age > 0 only |
| `ukb_hnc` | "Continuous variables, such as age, were modelled as continuous" — UK Biobank recruits aged 40–69 at enrolment (Methods > Data source) | McCarthy 2020, *Int J Oncol*, Methods | (0, 120) plausibility only |
| `capra` | cohort's **mean** age was 62; the paper gives no age range or eligibility bound on age at all | Cooperberg 2005, *J Urol*, Methods > Patient cohort | age > 0 only |
| `grace` | no age range stated in the retrievable abstract; age enters as "OR 1.7 per 10 years," continuous | Granger 2003, *Arch Intern Med*, Results (abstract) | age > 0 only |
| `atria_stroke_2013` | "We included all patients ≥18 years old with either 2 or more outpatient AF diagnoses..." — a floor, not a range | Singer 2013, *JAHA*, Methods | age ≥ 0 only |
| `pbcg_extended` | age is mandatory but the paper states no eligibility bound on it anywhere | Neumair 2022, *BMC Med Res Methodol*, Methods | no age bound at all |
| `cervical_cin_risk` | "Women eligible for the screening cohorts were additionally aged 25 to 65" | Wu 2021, *BMC Medicine*, Methods | age > 0 only |
| `amap` | age enters "in year[s]"; no eligibility bound on age stated in the retrievable text | Fan 2020, *J Hepatol*, p.1371 | age > 0 only |
| `iota_adnex` | no age range located in the retrievable text; the paper restricts by mass and pathway, not by age | Van Calster 2014, *BMJ* | no age bound at all |
| `msk_rectal` | "the median age was 57.8 years (range, 18.0-91.9 years)" — a cohort description, not a stated eligibility bound | Weiser 2021, *JAMA Netw Open*, Results > Cohorts | age > 0, and only on the OS endpoint |

Seven models do enforce an age range: `prevent` (30–79 at 10 years, 30–59 at
30), `bcsc_v2` (35–79), `crc_pro` (45–85), `msk_gastric` (25–96),
`msk_ovarian` (22–87), `msk_pancreatic` (33–89), and `kunzmann` (≥ 50 floor,
no ceiling).

**Two of those seven enforce a bound their paper does not state**, which is the
mirror image of the problem this section is about and was found only by going
back to the sources:

- `prevent`, the paper gives one range, 30–79, for both horizons. The 30–59
  ceiling at the 30-year horizon is ours; `preventr` warns there and still
  answers, we refuse. See the card in §2.
- `bcsc_v2`. Tice 2008 states a lower bound ("age 35 years or older") and no
  upper one, and reports results in an 80–84 band. Our 79 ceiling refuses a
  patient the paper covers.

Neither is necessarily wrong as a policy, extrapolating a spline or a 30-year
horizon past its fitted support is a real hazard, but both are this library's
judgement presented, until now, as if they were the paper's.

Not every one of these needs a hard gate, a points score with banded age is
degraded rather than undefined outside its range, whereas a spline is
genuinely unanchored. But the distinction should be a recorded decision per
model rather than an accident of who wrote which module.

### 3.4 Silent defaults that pick a side

| model | argument | default | effect |
|---|---|---|---|
| `iota_adnex` | `oncology_centre` | `False` | P(malignant) 6.5% vs 12.4% for the same mass — nearly a doubling, and it is a **site** property the caller must know |
| `iota_adnex` | `ascites`, `acoustic_shadows`, `papillary_structures`, `more_than_10_locules` | benign side | four ultrasound findings default to absent |
| `predict_breast` | `screen_detected` | `0` = clinically detected | the reference's "unknown" code is `2` (imputed 0.204); defaulting to `0` systematically differs from the tool when detection mode is unknown |
| `crc_pro` | `activity_hours_per_day` | `0.0` | zero activity is the **worst** level, not "unknown" |
| `crc_pro` | `red_meat_oz_per_day` | `0.0` | zero red meat is the **best** level, so the two defaults push in opposite directions |
| `crc_pro` | `estrogen`, `nsaid`, `aspirin` | `'no'` | never-use, not unknown |
| `plcom2012` | `quit_years` | `0.0` | a former smoker with unknown quit time is scored as if they had just stopped |

`cibula_arrm` is the well-handled case: its `None` defaults reproduce the
paper's own pooling *and* the result says so in `notes` every time they fire.
That is the pattern the others should follow.

### 3.5 Sex-restricted models with no sex gate

`crc_pro` takes `male` and fits two different models, but passing a
women's-model field (`estrogen`, `nsaid`) with `male=True`, or a men's-model
field (`aspirin`, `red_meat_oz_per_day`, `activity_hours_per_day`) with
`male=False`, is **accepted and silently ignored**. A caller who mapped their
columns wrong gets a plausible number with no signal.

The implicitly sex-specific models, `pbcg_extended`, `capra`, `dutasteride`
(men); `bcsc_v2`, `predict_breast`, `iota_adnex`, `msk_ovarian`,
`cervical_cin_risk`, `moore_criteria`, `cibula_arrm` (women), have no sex
parameter at all, which is defensible, but nothing records the restriction in
a machine-readable field either.

### 3.6 A stale claim in two places

`registry/models.yaml`'s `amap.scope_note` and
`tests/test_liver_detection_amap.py:63-64` both still say Johnson 2015 uses
`-0.0852` for the ALBI albumin coefficient and that aMAP "rounds" it to
`-0.085`. `src/cancerverse_baseline/liver/detection/amap.py` says explicitly that this
claim "was wrong": the ALBI module had a mistranscribed value, since
corrected, and the two are now consistent because the source is. Both modules
use `-0.085`, so no number is affected; only the note is stale.

---

## 4. Structural constraints worth stating once

Things that are true of several models and are easy to read past.

**Sixteen of the 34 return `risk: None`**, just under half. `albi`, `amap`,
`ang2010_rpa`, `atria_stroke_2013`, `capra`, `chau_eg`, `cibula_arrm`,
`cvd_statin_benefit`, `endpac`, `hap`, `kunzmann`, `lipi`, `lipi_prognosis`,
`moore_criteria`, `shapiro_ncrt`, `xu_gastric_trg_score` return a score,
grade, band, published group outcome or absolute benefit instead. Each does so
deliberately, in most cases because the paper published no intercept and no
baseline hazard, so no individual probability is recoverable. A consumer that
treats `risk` as always-numeric breaks on half the library.

**Two invert the usual reading of "high".** `wang_larc_pcr` returns a numeric
`risk` that is the probability of pathological complete response, so a high
number is a *favourable* prediction (`p_pcr` is provided under its own name to
make that unambiguous at the call site). `xu_gastric_trg_score` has no
probability, but the paper's "high-risk" group is the one with the better
outcome, 76.75% vs 53.45% 3-year survival, so this module refuses that label
and names the groups `high_likelihood` / `low_likelihood`.

**Three restrict the prediction horizon to a published grid, not a range.**
`msk_rectal` (0/60/120/180 months), `msk_pancreatic` (12/24/36 months),
`msk_gastric` (5/9 years). Interpolation is refused, not silently performed.

**Four have a treatment-era or regimen constraint, not just a disease one.**
`chau_eg` (1990s fluorouracil combinations, pre-trastuzumab, pre-ICI);
`dutasteride` (REDUCE protocol); `shapiro_ncrt` (CROSS regimen specifically);
`predict_breast` (chemo generation 2 or 3, radiotherapy gated off).

**Two carry a race or ancestry term that the authors themselves discuss
without resolving.** `pbcg_extended`'s African-ancestry coefficient flips sign
across sub-models; `moore_criteria`'s race factor is one of five equally
weighted items. Both are reproduced as published and flagged at the call site.
Neither should be read as a statement about mechanism.

**One is not a published model.** `cvd_statin_benefit` is a composition, marked
`derived_not_published`, and its assumptions are returned in the payload.

**Two occupy two cells each.** `predict_breast` / `predict_breast_response` and
`lipi` / `lipi_prognosis` re-export one module rather than duplicating an
equation; their constraints are identical across both cells.
