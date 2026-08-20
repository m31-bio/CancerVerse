# Cervical cancer: candidates for the response and prognosis cells

Search date 2026-08-14. This is a literature-search record, not an implementation.
Nothing in `registry/`, `src/` or `tests/` was touched.

Read `README.md` in this directory first: it records the four SEER nomogram
papers already ruled out. This pass deliberately looked **away** from
`rms::cph` + `nomogram()` papers, and both cells changed status as a result.

Bibliometrics are OpenAlex `cited_by_count`, fetched 2026-08-14 by the pattern
in `scripts/fetch_impact.py`. Citations-per-year uses `2026 − year + 1` as the
denominator. **Journal standing is qualitative only**, no impact factor is
reported here, for the reason set out in `scripts/fetch_impact.py`.

---

## Verdict: prognosis

**Fillable. The blocker was real and it is now gone.** The prior pass concluded
that cervical prognosis models are structurally unimplementable because the
literature is `rms::cph` nomograms that never print S₀(t). That is true of the
nomogram literature and it is not true of the field. The **Annual Recurrence
Risk Model (ARRM)** — Cibula et al, *European Journal of Cancer* 2021, from the
20-centre, 4343-patient SCCAN consortium, never needed S₀(t), because it is
not a nomogram. It publishes a complete integer points schedule alongside its β
coefficients in one real HTML table in PMC, bands the score into five risk
groups, and reports outcome per band. It is endorsed by ESGO, deployed at
`calculators.esgo.org`, and externally validated in *IJGC* 2025. Better still,
the deployed calculator is a static page that **ships the entire 4343-row
patient-level derivation dataset as `data/data.min.js`** and the exact
Kaplan–Meier + landmark algorithm as `scripts/main.js`. Re-running that
algorithm over that data reproduced every number the paper prints, to 0.1
percentage point. A sibling model by the same consortium, post-recurrence
disease-specific survival, *Gynecologic Oncology* 2022, has the same shape and
its own calculator with its own shipped dataset, and also reproduced. Two more
independent candidates (SUCCOR Risk, which prints an actual logistic intercept;
Beyond Sedlis, which enumerates its whole input space) are usable with caveats.

## Verdict: response

**Fillable, but not by the route that was searched before.** The earlier pass
ruled the response axis out as a class after finding only radiomics and
deep-learning nomograms for response to neoadjuvant chemotherapy. That finding
is confirmed and re-confirmed below, the neoadjuvant/chemoradiation response
literature for cervix really is imaging and biomarkers, and it is `not_ehr`.
The escape is to change the *endpoint*: response to **cisplatin-based
chemotherapy in advanced/recurrent/metastatic disease**. The **Moore criteria**
(Moore et al, *Gynecologic Oncology* 2010; pooled GOG 110/169/179, external
validation on GOG 149) are a five-factor count-the-risk-factors index whose
**Table 4 prints the estimated and observed response rate for every risk band,
in both the development and the external validation cohort**. It was then
*prospectively* validated as a tertiary endpoint of the phase III GOG 240 trial
(Tewari et al, *Clinical Cancer Research* 2015), which describes it as "the
first prospectively validated scoring system in cervical cancer". Inputs are
routine-to-specialty; none is a questionnaire, a symptom score, or a radiomics
feature.

---

## Prognosis: ranked

| # | Paper | Year | Journal | Cites | /yr | Inputs | `ehr_availability` | Coefficients — from exactly which artifact | Verdict |
|---|---|---:|---|---:|---:|---|---|---|---|
| 1 | **Cibula et al — The annual recurrence risk model (ARRM)** ([10.1016/j.ejca.2021.09.008](https://doi.org/10.1016/j.ejca.2021.09.008), PMC9406128) | 2021 | European Journal of Cancer — leading general oncology journal | 39 | 6.5 | max pathologic tumour diameter, histotype, grade, no. positive pelvic LN, LVSI | `specialty` — all five come off one surgical pathology report; nothing needs imaging-derived features | **Table 2** of PMC9406128: 14 β with SE, HR, *and* an integer "Risk points (max. 100)" column, every reference level named. Outcome grid: `https://calculators.esgo.org/cervical-cancer-recurrence-risk-calculator/data/data.min.js` (4343 rows) + `scripts/main.js` (algorithm) | **Implement.** Best candidate on every axis |
| 2 | **Cibula et al — Post-recurrence survival in patients with cervical cancer** ([10.1016/j.ygyno.2021.12.018](https://doi.org/10.1016/j.ygyno.2021.12.018), PMC9406127) | 2022 | Gynecologic Oncology — the specialty's principal journal | 33 | 6.6 | tumour size, LVSI (from primary); DFI1, age at recurrence, symptoms at recurrence, isolated/multifocal recurrence | `specialty` — pathology plus a recurrence work-up; DFI1 and age are `routine` | **Table 3** of PMC9406127: 6 β with SE, HR, and a "Points (max. 100)" column. Outcome grid: `https://calculators.esgo.org/cervical-cancer-post-recurrence-survival-prediction/data/data.min.js` (520 rows) | **Implement.** Complements #1 rather than competing with it |
| 3 | **Manzour et al — SUCCOR Risk** ([10.1245/s10434-022-11671-5](https://doi.org/10.1245/s10434-022-11671-5), PMC9246807) | 2022 | Annals of Surgical Oncology — strong surgical journal | 16 | 3.2 | previous cone biopsy (absent), MIS surgical approach, preoperative tumour size >2 cm | `specialty` — cone biopsy and surgical approach are coded procedures (`routine`); the >2 cm size is one reported radiology measurement, not a radiomics feature | **Table 3**: `Constant −3.441`, `Cone biopsy before surgery 1.040`, `Approach 0.699`, `Preoperative image size 0.564`. A **complete logistic equation with a printed intercept** | **Usable, with two caveats** — see notes |
| 4 | **Levinson et al — Beyond Sedlis** ([10.1016/j.ygyno.2021.06.017](https://doi.org/10.1016/j.ygyno.2021.06.017), PMC8405564) | 2021 | Gynecologic Oncology | 65 | 10.8 | histology (SCC vs AC), LVSI, depth of invasion, tumour size | `specialty` — pathology report | **Table 3** enumerates **all 18 covariate combinations × 2 histologies = 36 cells**, each with 3-year RFS (with CI) and a "nomogram recurrence risk". No S₀(t) is needed because the entire input space is printed | **Blocked on an internal contradiction** — see notes |
| 5 | **Phianpiset et al — Prognostic survival model following primary radical surgery** ([10.3390/cancers18071134](https://doi.org/10.3390/cancers18071134), PMC13072203) | 2026 | Cancers | 0 | 0.0 | tumour size, histology, no. positive LN, LVSI, platelet-to-lymphocyte ratio | `specialty` — pathology plus a CBC-derived ratio (`routine`) | **Table 2**: 6 β with HR/CI/p. **No S₀(t) printed.** Live Shiny app at `https://kcharoenkwan.shinyapps.io/Cervical_App/` | **Second-tier.** Needs a calculator probe first — see notes |
| — | Retro-EMBRACE OS nomogram ([10.1016/j.ijrobp.2021.04.022](https://doi.org/10.1016/j.ijrobp.2021.04.022)) | 2021 | Int J Radiation Oncology Biol Phys | 46 | 7.7 | image-guided brachytherapy cohort | not assessed | **Not opened.** Deprioritised once #1 closed the cell; it is a nomogram paper and therefore in the already-characterised failure class | Not pursued |
| — | Yoo 2012 · Wang 2018 · Zhang 2022 · Sci Rep 2024 | — | — | — | — | — | — | — | **Already ruled out** in `README.md`; nothing here changes that |

### Note on #1: what the artifacts contain, and the parity check that was run

The model factors cleanly into two halves, and both halves are readable.

**Half one, patient → points.** `Table 2` of PMC9406128, read verbatim from
the PMC HTML (not from a summary). Reference level first, then β / integer
points:

- Histotype: squamous cell = ref, 0 pts · adenocarcinoma 0.342, 7 · adenosquamous 0.598, 11 · neuroendocrine 1.741, 33 · other 1.145, 22
- Tumour diameter: <0.5 cm = ref, 0 · 0.5–1.99 cm 0.501, 10 · 2–3.99 cm 1.115, 21 · ≥4 cm 1.556, 30
- Grade: 1 = ref, 0 · 2 → 0.260, 5 · 3 → 0.457, 9
- Positive pelvic LN: 0/not assessed = ref, 0 · 1 → 0.255, 5 · 2 → 0.482, 9 · ≥3 → 0.939, 18
- LVSI: no/not assessed = ref, 0 · yes 0.538, 10

Bands: 0 · 1–25 · 26–50 · 51–75 · 76–100 points.

The ESGO calculator's `<option value="…">` attributes are **exactly** this
points schedule (0/7/11/33/22, 0/10/21/30, 0/5/9, 0/5/9/18, 0/10). That is an
independent second statement of the rule in the sense of `EXTRACTION.md`
Route C, and it agrees at zero tolerance.

**Half two, points band → outcome.** Only partly printed. The paper's text
gives the 26–50 band at years 1/3/5, the 51–75 band at years 1 and 5, the
76–100 band at years 1 and 2, and describes the two lowest bands only
qualitatively ("close to 0%", "oscillating close to 1%"); the full grid is
`Fig. 3`, a graphic. **The calculator supplies it numerically.** The page loads
`data/data.min.js`, a single `const dataRaw = [...]` of **4343 rows**, the
exact cohort size, each row being
`[fupYears, points, category, recurrence, rfiYears, cat1, cat2]` (the key map
is written out in `scripts/main.js`), with 528 event rows matching the 528
recurrences. `scripts/main.js` also contains the estimator: a plain
Kaplan–Meier, then `arrm[i] = (S(i−1) − S(i)) / S(i−1)` with year buckets
assigned by `Math.ceil(t)`.

Re-implementing that in Python over that data gives:

| Band | DFS y1 | y2 | y3 | y4 | y5 | ARRM y1 | y2 | y3 | y4 | y5 | n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 pts | 100.0 | 99.1 | 99.1 | 97.5 | 97.5 | 0.0 | 0.9 | 0.0 | 1.5 | 0.0 | 213 |
| 1–25 | 98.9 | 97.4 | 96.1 | 95.3 | 94.7 | 1.1 | 1.5 | 1.3 | 0.9 | 0.7 | 1844 |
| 26–50 | 94.8 | 90.2 | 87.4 | 86.1 | 85.2 | 5.2 | 4.9 | 3.1 | 1.5 | 1.0 | 1899 |
| 51–75 | 86.3 | 76.2 | 70.8 | 65.8 | 63.2 | 13.7 | 11.7 | 7.0 | 7.1 | 3.9 | 374 |
| 76–100 | 46.2 | 15.4 | 7.7 | 7.7 | 7.7 | 53.8 | 66.7 | 50.0 | 0.0 | 0.0 | 13 |

Against what the paper prints: 5-year DFS **97.5 / 94.7 / 85.2 / 63.3** (abstract)
vs computed **97.5 / 94.7 / 85.2 / 63.2**; 2-year DFS in the top band **15.4%**
vs **15.4%**; ARRM year-1 **5.2% / 13.7% / 53.8%** vs **5.2 / 13.7 / 53.8**;
ARRM year-5 for 26–50 **1.0%** vs **1.0**; for 51–75 **3.9%** vs **3.9**; year-2
for 76–100 **66.7%** vs **66.7**. Two cells differ by 0.1 pp (63.2 vs 63.3, and
3.1 vs the text's 3.2 at year 3 for the 26–50 band), which is one
Kaplan–Meier step's worth of tie-handling, not disagreement.

**So implementation is mechanical**: transcribe Table 2's points into a scorer,
band the total, and hard-code the 5 × 5 outcome grid above. No S₀(t) is
involved anywhere.

Two things to carry forward rather than assume:

- **Licence.** The calculator page carries "©2023 All rights reserved" and links
  to ESGO's Website Terms. The *points schedule and the risk bands* come from
  Table 2 of a PMC-hosted paper and are subject to that paper's terms; the
  *outcome grid* as tabulated above is derived from the calculator's shipped
  data. `docs/COMMERCIAL_USE_AUDIT.md` should rule on the second before it
  ships. Note the numbers can also be sourced from the paper's own text and
  `Fig. 3` if a cleaner provenance is wanted.
- **External validation exists**: Bogani/EIO Milan, *IJGC* 2025,
  [10.1016/j.ijgc.2025.101756](https://doi.org/10.1016/j.ijgc.2025.101756),
  411 patients, 5-year DFS 96.3% / 85.7% / 66.6% for bands 1–25 / 26–50 / 51–75
  against development values of 94.7 / 85.2 / 63.2. OpenAlex has 0 citations
  for it (2025) and Europe PMC has no PMCID, so it is abstract-level here, the
  full text was not read.

### Note on #2: the sibling model

`Table 3` of PMC9406127, read verbatim (reference level, β, points):

- Largest pathologic tumour size: <0.5 cm ref 0 · 0.5–1.9 cm 0.947, 20 · 2.0–3.9 cm 1.269, 27 · ≥4.0 cm 1.481, 31
- LVSI: no/NA ref 0 · yes 0.672, 14
- Time from surgery to recurrence: >1 yr ref 0 · <1 yr 0.516, 11
- Age at recurrence: <65 ref 0 · >65 0.543, 12
- Symptoms at diagnosis of recurrence: no ref 0 · yes/NA 0.788, 17
- Recurrence type: isolated ref 0 · multifocal 0.687, 15

Bands 0–33 / 34–66 / 67–100. The second ESGO calculator's option values are
0/20/27/31, 0/14, 0/11, 0/12, 0/17, 0/15, again an exact match. Its
`data/data.min.js` holds **520 rows** (the paper's cohort is 528; the 8-row
shortfall is unexplained and should be noted, not glossed). Re-running the same
estimator gives 5-year PR-DSS **81.8 / 44.7 / 12.7** against the paper's printed
**81.8% / 44.6% / 12.7%**.

Full computed grid (PR-DSS %, year 1→5): 0–33 → 98.1, 90.9, 90.9, 81.8, 81.8 ·
34–66 → 83.1, 64.7, 53.1, 46.4, 44.7 · 67–100 → 50.5, 23.8, 16.7, 12.7, 12.7.

"Symptoms at the diagnosis of recurrence" is a binary clinician note
(symptomatic vs found at routine surveillance), not a symptom questionnaire,
which is why this is `specialty` and not `not_ehr`. The paper pools missing
into the "Yes/NA" level, which is convenient for EHR use.

### Note on #3: SUCCOR Risk, and its two caveats

The full equation, from `Table 3`:

    logit P(relapse) = −3.441 + 1.040·(no previous cone biopsy)
                              + 0.699·(minimally invasive approach)
                              + 0.564·(preoperative tumour size > 2 cm)

Sanity check that was run: all-negative gives 3.1%, all-positive gives 24.3%,
against observed relapse rates of 3.4% in the low band and 21.3% in the high
band. Internally consistent.

Caveat one — **the paper contradicts itself on the intercept**. The Results text
says "an intercept of −3"; `Table 3` says `−3.441`. Per `EXTRACTION.md`, do not
pick the more official-looking sentence: the table is the precise artifact and
the text is a narrative rounding, and the arithmetic above only reconciles with
`−3.441`.

Caveat two — **the time horizon is undefined**. This is a logistic model of
"relapse" over a cohort with median 58 months follow-up, not a probability at a
stated time point. The integer index (`Score = 4·no-cone + 3·MIS + 2·size>2cm`,
bands 0–3 / 4–6 / 7–9, observed relapse 3.4% / 9.8% / 21.3%, 5-year DFS
97.2% / 88.0% / 80.5%) is the better-defined half. Also note one predictor is
the *surgical approach*, i.e. a treatment choice rather than a patient feature,
a legacy of the LACC trial, which is fine for an EHR (it is a procedure code)
but changes what the model means.

### Note on #4: Beyond Sedlis is blocked on a contradiction, not on a missing constant

This is the highest-cited candidate in the table (65, 10.8/yr) and it prints its
entire input space, so it deserves a precise blocker. `Table 3` gives, for each
of 36 covariate cells, both a 3-year RFS and a "nomogram recurrence risk", and
**the two columns disagree**, in the wrong direction. Example: SCC, LVSI-negative,
middle-third invasion, <2 cm. RFS 0.91 (so ≤9% recurrence) against a nomogram
risk of 18%. RFS counts recurrence *or* death, so it can only be the larger of
the two. Worse, the Discussion's own worked example. SCC, LVSI-negative, deep
invasion, 4 cm, "12.5 points → 25% risk of recurrence", matches neither the
`N/Deep/≥4 cm` row (nomogram 42%, RFS 0.66) nor the `N/Deep/2–4 cm` row
(nomogram 38%). Three statements, three answers.

The 3-year RFS column alone is complete and self-consistent and could be shipped
as a lookup. The nomogram column cannot be, until Figures 3 and 4 are rendered
at high resolution (`EXTRACTION.md` Route D) and the points-to-risk axis is read
directly. **Do not implement the nomogram column from the text.**

### Note on #5: what to ask the Phianpiset calculator

`Table 2` prints six β (tumour size 0.547; adenocarcinoma 0.703; adenosquamous
0.713; LVSI 0.482; positive nodes 0.089; PLR 0.0005, squamous = reference). Two
things are missing and one is suspicious.

- **No S₀(t).** The Methods say the model "was reconstructed to obtain the
  baseline survival function while retaining the pooled coefficients", so it
  exists in their fitted object and was simply not printed.
- **The degrees of freedom do not reconcile.** The Results state the final model
  "contained 7 degrees of freedom". Six single-df terms are printed (size 1 +
  histology 2 + LVSI 1 + nodes 1 + PLR 1 = 6). The Methods say continuous
  predictors with non-linear effects were fitted as restricted cubic splines. A
  per-centimetre HR of 1.73 across an input range the app allows to run to 15 cm
  is not credible as a linear term. So the functional form of tumour size is
  probably a spline or a log, and `Table 2` is showing one term of it.

The app is **live** (checked 2026-08-14; shinyapps.io answers HTTP 202 with a
loading shell, then 200 with worker id `_w_abf7cbb797d346e7bfcf97d070bc3d1a`).
Its inputs are `size` (numeric 0–15, step 0.1), `finalhisto`
(Adeno/Squamous/Adenosquamous), `rhlvsigr` (Negative/Positive), `nodepos`
(0–50), `plr` (1–1000), and a `calc` action button; outputs are `risk_text`,
`risk_badge` and `surv_plot`.

**Route A3 does not apply here.** It is not a `DynNom` app, the dependency list
is jquery/bootstrap/selectize only, and the "About the Model" tab
(`tab-6387-2`) is *static HTML* containing the C-index, calibration slope and
O/E ratio, and no coefficients. Confirmed by reading the served markup.

So this is Route B, and it is cheap: because β is printed, **one** probe recovers
the baseline exactly, via S₀(t) = S(t)^(1/exp(Xβ)). Probing a ladder of `size`
values with everything else held at reference then settles the functional-form
question from the shape of the response. Both open questions are answerable in
one scripted session. Given ARRM already closes the cell, this is second-tier
work, not urgent.

---

## Response: ranked

| # | Paper | Year | Journal | Cites | /yr | Inputs | `ehr_availability` | Coefficients — from exactly which artifact | Verdict |
|---|---|---:|---|---:|---:|---|---|---|---|
| 1 | **Moore et al — Prognostic factors for response to cisplatin-based chemotherapy in advanced cervical carcinoma** ([10.1016/j.ygyno.2009.09.006](https://doi.org/10.1016/j.ygyno.2009.09.006), PMC4470610) | 2009/2010 | Gynecologic Oncology | 161 | 8.9 | African-American race; performance status >0; pelvic disease; prior radiosensitiser (concurrent cisplatin); first recurrence ≤1 year from diagnosis | `specialty` — race, prior cisplatin and the recurrence interval are `routine`; performance status and pelvic-vs-distant disease site need a clinician assessment and a staging work-up. Nothing is a questionnaire or an imaging feature | **Table 4** prints the model's estimated *and* observed response rate for each band, in the development set *and* the external validation set. **Table 3** gives adjusted ORs only — no intercept | **Implement.** The published deliverable is the index, and the index is complete |
| 2 | **Tewari et al — Prospective validation of pooled prognostic factors (NRG/GOG, GOG 240)** ([10.1158/1078-0432.CCR-15-1346](https://doi.org/10.1158/1078-0432.CCR-15-1346), PMC4896296) | 2015 | Clinical Cancer Research | 75 | 6.2 | same five | same | Not a new model. Supplies the **prospective** validation numbers: low-risk response rate 57%, high-risk 18.5% (both in Results text) | **Cite as validation for #1** |
| — | Moore criteria in a diverse non-trial population ([10.1016/j.ygyno.2020.01.001](https://doi.org/10.1016/j.ygyno.2020.01.001)) | 2020 | Gynecologic Oncology | 2 | 0.3 | same | same | Real-world applicability check | Supporting evidence; abstract-level only, full text not read |
| ✗ | Radiomics / deep-learning response nomograms (CT, MRI, IVIM-DWI, delta-radiomics) | 2019–2024 | various | — | — | imaging-derived texture features | `not_ehr` | — | **Rejected as a class** (confirms the prior pass) |
| ✗ | Single-biomarker response predictors: PD-L1/TIL, XRCC1 and GGH polymorphisms, ALDH1, clusterin, CD44v6, mTOR, 15-gene classifier, vaginal microbiota, metabolomics | 1991–2022 | various | — | — | tissue assays, genotyping, sequencing | `not_ehr` | **Rejected.** Association studies, not multivariable equations, and the assays are not EHR fields |
| ✗ | Systemic immune-inflammation index and NACT response (PMC9092215, [10.3389/pore.2022.1610294](https://doi.org/10.3389/pore.2022.1610294)) | 2022 | Pathology Oncology Research | 21 | — | platelet/neutrophil/lymphocyte counts | would be `routine` | **Not read in full.** Framed in its abstract as a single-index-with-cut-off association study, not a multivariable equation | Not pursued — flagged in case a later pass wants it |

### Note on #1: the exact numbers and where they live

The rule, from the Methods and Results of PMC4470610: five binary risk factors,
"comparable weights and no interactions", so the index is simply **how many of
the five are present**. Bands: **low 0–1 · mid 2–3 · high 4–5**.

`Table 4` ("Validation of Prognostic Model"), read verbatim:

| Band | Est. response % (dev) | Obs. response % (dev) | Median PFS (mo) | Median OS (mo) | Pred. response % (ext) | Obs. response % (ext) | PFS | OS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Low | 50.6 | 47.3 | 6.34 | 11.10 | 50.9 | 42.6 | 6.87 | 11.93 |
| Mid | 29.4 | 31.4 | 4.60 | 9.17 | 29.0 | 29.4 | 4.44 | 7.59 |
| High | 13.0 | 9.8 | 2.79 | 5.49 | 13.5 | 14.3 | 3.38 | 5.58 |

Development = GOG 110 + 169 + 179 (428 enrolled, 409 with response data,
overall response 32%). External = GOG 149, which was not used in development.

**Be precise about what is and is not obtainable here.** `Table 3` gives only
adjusted odds ratios (0.49 / 0.60 / 0.58 / 0.52 / 0.61) with no intercept, so
the underlying *continuous* logistic model is **not** reproducible, the same
half-a-formula defect as the SEER nomograms. But that model is not what the
paper published. The paper published the count-based index, and for the index
`Table 4` is a complete numeric statement over its entire three-cell output
space. `Figure 1` ("predicted and observed response rate by number of risk
factors") would give the finer six-level 0–5 resolution and is a graphic; the
three-band table is the artifact to use.

This is the same shape as `xu_gastric_trg_score`, a scoring rule whose weights
and whose outcome lookup are both printed, with the added strength of a
prospective validation.

### Note on #2: why the validation matters more than its citation count

GOG 240 pre-specified validation of the Moore criteria as a tertiary endpoint
(n = 452). Results text: the low-risk cohort had 21.8 months OS and **57%**
response rate; the high-risk cohort 8.2 months OS and **18.5%** response
(p < 0.001 for both). The mid-band response rate appears in `Figure 1` only.
The paper's own claim: "the first prospectively validated scoring system in
cervical cancer", is unusually strong for this literature and is the reason
this candidate outranks anything else on the response axis.

---

## What was checked, and what it returned

Negative results and HTTP failures, so nobody repeats them.

**Deployed-calculator platforms**

- `riskcalc.org` (GitHub `ClevelandClinicQHS/riskcalc-website`), 184 calculator
  directories enumerated via the GitHub contents API. **Zero cervical cancer
  tools.** The only near-matches are `PatientsEligibleforCervicalSpineSurgery`
  (already on file as a false friend in `scripts/scan_riskcalc.py`) and
  `TransfusionAfterGynecologicSurgery`. Dead end, now settled.
- **MSK nomogram portal** (`mskcc.org/nomograms`), 14 disease sites listed
  (bladder, breast, colorectal, endometrial, gastric, GIST, liver, melanoma,
  prostate, rectal, renal, sarcoma, testicular, uterine leiomyosarcoma).
  **No cervix.** Dead end, now settled.
- **ESGO clinical calculators** (`esgo.org/calculators`) — **two** cervical
  tools, both hits: the recurrence risk calculator (ARRM) and the
  post-recurrence survival predictor. Both are static pages loading
  `./data/data.min.js`, `./scripts/d3.js`, `./scripts/main.js`, and both ship
  patient-level data client-side. This is `EXTRACTION.md` Route A1 at its most
  generous: not just the constants, the whole cohort.
- `kcharoenkwan.shinyapps.io/Cervical_App/`, live. Not `DynNom`; its
  "About the Model" tab is static and holds no coefficients. Route A3 fails;
  Route B applies (see above).

**Web archives**

- Wayback CDX for `ccc.ac.at/gcu*` and `www.ccc.ac.at/gcu*`, 40 captures
  returned (2013–2024), all German-language departmental, structure, contact and
  news pages of the Vienna CCC gynaecologic oncology unit. **No calculator path
  in any capture.** Yoo 2012's calculator is not recoverable this way, and the
  `README.md` entry for it should stay as it is.

**Publisher retrieval failures, and the mirrors that worked**

- `www.mdpi.com/2072-6694/18/7/1134` → **HTTP 403** (Akamai "Access Denied") via
  both WebFetch and `curl` with a browser UA. Recovered in full from
  **PMC13072203**.
- `www.nature.com/articles/s41598-024-72790-5` → **HTTP 303** to
  `idp.nature.com/authorize`. Recovered from **PMC11437206**.
- `pmc.ncbi.nlm.nih.gov/articles/?term=…` → **HTTP 404**; PMCID lookup by DOI
  through the Europe PMC REST API worked every time and is the better route.
- Everything else needed (PMC9406128, PMC9406127, PMC9246807, PMC8405564,
  PMC4470610, PMC4896296, PMC13072203) was open access and read directly.
  **No coefficient in this document is paywalled or inferred**, each was read
  out of the article HTML.

**Searches run, and what they showed**

- Europe PMC, `TITLE:"cervical cancer" … "complete response" … (nomogram OR
  prediction model)` — **0 hits**.
- Europe PMC, cervical + `"predicting"/"prediction"` + `"complete response"/
  "pathological response"/"chemosensitivity"` restricted to 2018–2026 —
  **2 hits, both MRI radiomics.**
- Europe PMC, cervical + neoadjuvant chemotherapy + response/predict, 92 hits,
  top 25 reviewed: radiomics, DWI/IVIM, PD-L1, XRCC1, ALDH1, CD44v6, clusterin,
  metabolomics, microbiota, a 15-gene classifier. **No multivariable clinical
  equation.**
- Europe PMC, cervical + chemoradiotherapy/radiotherapy + response, 205 hits,
  top 20 reviewed: DWI, FDG-PET, HIF-1α, macrophage polarisation, HPV
  multiplicity. Same conclusion.
- Europe PMC, cervical + `"tumor regression grade"`, 376 hits, essentially all
  oesophageal, rectal and gastric. **There is no cervical TRG model** of the
  `xu_gastric_trg_score` shape; the closest analogue on this axis is the Moore
  index, and it is better validated.
- Europe PMC, cervical + nomogram, 137 hits, top 25 reviewed. Dominated by
  radiomics nomograms for lymph-node metastasis / LVSI / parametrial invasion
  (i.e. the *detection* axis, and `not_ehr`), plus the SEER prognosis nomograms
  already ruled out.
- OpenAlex by DOI for every surviving candidate. One 404:
  `10.1016/j.ijgc.2025.101873` (a wrong DOI guessed from a search result); the
  correct DOI, `10.1016/j.ijgc.2025.101756`, was found through Europe PMC and is
  not yet indexed with citations.
- Crossref journal query on ISSN 0090-8258 filtered to volume 164, page 362,
  used to resolve the second ESGO calculator's citation stub
  ("Gynecologic Oncology 164 (2021): 362-369") to a DOI. Worked first try.

**One candidate that looked right and was not**

- Sci Rep 2024, "Comparative study of machine learning and statistical survival
  models … using SEER data" ([10.1038/s41598-024-72790-5](https://doi.org/10.1038/s41598-024-72790-5),
  PMC11437206). This was chased specifically because a **Weibull** model has its
  baseline *in* its parameters, which is the clean escape from the S₀(t)
  problem. It fits Weibull, Cox and random survival forests, and reports
  **hazard ratios only**. No shape, no scale, no intercept. So it fails for the
  same reason as the nomograms, by a different mechanism. Worth recording:
  *"parametric model" is not by itself a guarantee that the baseline is
  printed.*

---

## If someone wants to go further

In cost order, and none of it is required to close either cell:

1. **Probe the Phianpiset Shiny app** (Route B, one session) to recover its
   S₀(3y)/S₀(5y) and settle the tumour-size functional form. Adds a fifth
   independent prognosis model.
2. **Render Beyond Sedlis Figures 3 and 4 at 600 dpi** (Route D) and read the
   points-to-risk axis directly, which settles the Table 3 contradiction. That
   paper has the best citation rate of any candidate here (10.8/yr) and is the
   only one that is histology-specific.
3. **Read the ARRM external validation in full** (*IJGC* 2025), abstract only
   so far, no PMCID. Not blocking: ARRM's own
   development data reproduces exactly.
4. **Retro-EMBRACE** (IJROBP 2021, 46 cites) was never opened. It is the only
   candidate here for *definitive chemoradiation* patients rather than surgical
   ones, so it covers a population ARRM does not. Expect the nomogram defect,
   but it has not been checked.
