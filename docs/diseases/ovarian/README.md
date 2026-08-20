# Ovarian cancer: paper dossier

Six entries, four shipped. Two things make this disease worth its own dossier:
it is the **only cell in the library with three implemented models competing on
one question**, and it holds the **only model whose implementation is known to
disagree with the figure its authors published**.

Bibliometrics: `bibliometrics.json`, resolved via OpenAlex 2026-08-17.

---

## The papers

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---:|---:|---:|:--:|:--:|---|
| **Jacobs et al — RMI** ([10.1111/j.1471-0528.1990.tb02448.x](https://doi.org/10.1111/j.1471-0528.1990.tb02448.x)) | detection | 1990 | BJOG | **970** | 26.9 | ✗ | ✅ across four papers | ✅ **alternative** as `rmi`, superseded |
| **Moore et al — ROMA** ([10.1016/j.ygyno.2008.08.031](https://doi.org/10.1016/j.ygyno.2008.08.031)) | detection | 2009 | Gynecol Oncol | 875 | **48.6** | ✗ | ✅ inline, both indices | ✅ **alternative** as `roma` |
| **Van Calster et al — IOTA ADNEX** ([10.1136/bmj.g5920](https://doi.org/10.1136/bmj.g5920)) | detection | 2014 | BMJ | 510 | 42.5 | ✗ | ✅ **Appendix D of the supplement** | ✅ **flagship** as `iota_adnex` — transcription checked, `no_independent_reference_implementation` |
| **Chi et al — MSK ovarian nomogram** ([10.1016/j.ygyno.2007.09.020](https://doi.org/10.1016/j.ygyno.2007.09.020)) | prognosis | 2008 | Gynecol Oncol | 69 | 3.6 | ⚠️ riskcalc.org only | ✗ **nomogram figure only** | ✅ **flagship** as `msk_ovarian` — **disagrees with its own figure**, see below |
| Stage / residual-disease tools | prognosis | — | portal | — | — | ✗ web only | ✗ | ✗ **catalog** — superseded by the above |
| KELIM (CA-125 elimination kinetics) | response | — | — | — | — | ✗ | ✗ **not closed-form** | ✗ **gap** — a nonlinear population-PK model |

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Read by us? |
|---|---:|---|---|
| `iota_adnex` | 510 | **Supplement, Appendix D**, "The formula of the ADNEX model after retraining on the pooled data" — 44 coefficients, four linear predictors. | ✅ |
| `roma` | 875 | **"Statistical Analysis"**, both indices printed inline: premenopausal `PI = −12.0 + 2.38·LN(HE4) + 0.0626·LN(CA125)`; postmenopausal `PI = −8.09 + 1.04·LN(HE4) + 0.732·LN(CA125)`. | ✅ |
| `rmi` | 970 | **Four separate papers**, one per RMI version — Jacobs 1990, Tingulstad 1996 and 1999, Yamamoto 2009. | ✅ |
| `msk_ovarian` | 69 | **Not the paper.** The paper prints a nomogram (Fig. 1) and no equation. Coefficients from the deployed R at `ClevelandClinicQHS/riskcalc-website`. | ⚠️ see below |

### ADNEX: the main text is not enough, and that is easy to get wrong

`equation_location` records it explicitly:

> The main text's **Table 5 gives odds ratios only and is NOT sufficient**.

A reader who takes Table 5 for the model gets four linear predictors' worth of
odds ratios with no intercepts and no interaction terms. The 44 numbers that
constitute ADNEX are in Appendix D of the supplement, under a heading that
matters: *after retraining on the pooled data*. That retrained version is the
one the published performance refers to; the development-cohort version is a
different fit.

### ADNEX's article is CC BY-NC 3.0

Stated at [PMC4198550](https://pmc.ncbi.nlm.nih.gov/articles/PMC4198550/):
"Creative Commons Attribution Non Commercial (CC BY-NC 3.0) license". The
registry carries a `license_basis` recording the reasoning: coefficients are
facts, not copyrightable expression (*Feist v. Rural Telephone*), and a check
confirming the implementation quotes nothing from the paper but the appendix
title and the citation. Every line of prose in `adnex.py` is ours.

---

## Detection: three models, one question, and the most-cited is the one being retired

| | RMI (1990) | ROMA (2009) | **ADNEX (2014)** |
|---|---|---|---|
| Citations | **970** | 875 | 510 |
| Citations/year | 26.9 | **48.6** | 42.5 |
| Output | one number + cut-off | one number + cut-off | **five categories** |
| Inputs | ultrasound + CA-125 + menopause | **HE4 + CA-125** | ultrasound + CA-125 |
| **In the library** | alternative, `superseded_by: iota_adnex` | alternative | **flagship** |

**The output shape is the reason ADNEX won, not the AUC.** RMI returns one
number and a threshold; ADNEX returns a distribution over benign, borderline,
stage I invasive, stage II–IV invasive, and secondary metastatic. A borderline
tumour and a stage III cancer imply different surgery, and "malignant" does not
distinguish them. Reported discrimination: **AUC 0.943** benign vs any
malignant, 0.99 benign vs stage II–IV, **0.85 benign vs borderline**. The last
figure being the honest one, because separating borderline from benign is the
hard part and the number says so.

**ROMA is kept, and is assay-locked.** Its `scope_note` is a warning worth
repeating: cut-offs are specific to the Architect CA125II and HE4 EIA platforms
and **do not transfer**, and premenopausal discrimination is materially worse
(sensitivity 67–76%) than postmenopausal (92%). It is an alternative rather
than a rejection because it takes a different input set: no ultrasound, so it
answers the same question where ADNEX cannot be run.

**RMI is retained deliberately after being superseded.** It is the comparator
every ovarian triage paper reports against, so removing it would remove the
baseline against which ADNEX's advantage is stated.

---

## Prognosis: the only model in the library that disagrees with its own published figure

`msk_ovarian` is parity-checked against riskcalc.org's deployed R, exactly, to
the last decimal. On 2026-08-14 a second and different question was asked for
the first time: **does that deployment match the nomogram Chi et al. actually
published?**

Method: the figure's Points axis as the only ruler (linear by construction, max
residual **0.12 points**); axis labels located by ink centroid rather than
character recognition, and stable for every gap parameter from 3 to 13 px; the
scale for our implementation taken from **residual disease alone**, which is
independent of the term under test. The ten age labels were confirmed by eye.

| Predictor | Figure | Ours | Difference |
|---|---:|---:|---:|
| Ascites | 35 | 34.9 | **−0.1** |
| Histology | ~10 | 11.3 | +1.3 |
| Platelets 300→600 | 10 | 11.5 | +1.5 |
| **Age 75** | **60** (printed, no tilde) | **75.3** | **+15.3** |

The age gap grows monotonically to **+17 points**, and our implied maximum total
is **264.8** against the figure's own **240** axis: two independent signs of the
same excess. Everything else agrees.

**What this is not.** It is not a discrepancy between us and riskcalc; that
parity still holds exactly. It is between the deployed model and the published
figure. Nor is it a fault in the method: the same script agrees with the
gastric nomogram to 0.4 points and the pancreatic one to 0.9, both with
independently derived scales. Two agreements and one disagreement is what makes
the disagreement worth recording.

**Not established, and not asserted:** whether the deployment was refitted after
publication. riskcalc.org attributes the calculator to this paper but does not
say it is the same fit. Only Cleveland Clinic QHS or the authors can settle it,
and they have not been asked.

### A second thing the figure settled

The registry has long recorded that the hosted tool labels its histology input
only "Tumor Histology (Yes/No)", so **what "Yes" means is not recoverable from
the code**. The figure resolves it. The paper's own worked example reads
"serous carcinoma (0 points)" and "clear cell carcinoma (~10 points)", and our
`histology_yes` coefficient is **−0.188**, protective, therefore the 0-point
category. Scaled, that is **11.3 points against the printed ~10**.

So `histology_yes = serous`, on three consistent lines of evidence. It is
recorded here rather than in the code because it is an inference, not a
statement from the authors, and the argument should be visible to whoever
checks it.

### The citation count says nothing useful here

69 citations, 3.6 a year, the least-cited paper in this dossier by an order of
magnitude, and the only one whose implementation has a known defect against its
source. Neither fact predicts the other. What found the defect was measuring
the figure.

---

## Response: a genuine gap, and the reason is the model class

`ovarian_response_gap` is `status: gap`, and the note says why:

> KELIM is a nonlinear population-PK model, not closed-form.

CA-125 elimination kinetics during chemotherapy is a real and validated
predictor of response, but the model is a differential-equation system fitted by
nonlinear mixed-effects estimation. It has no linear predictor to transcribe and
no coefficient table to read. This is not a retrieval failure. The papers are
open and the method is fully described. It is a **model-class** boundary: the
library takes models it can evaluate from published constants, and this is not
one.

That distinction is worth keeping separate from the other kinds of gap in this
project, which are missing constants, unreachable supplements, or inputs the
platform does not hold. Those can be closed by an email. This one cannot.

---

## What this disease shows that the others do not

| Axis | Flagship | Cites | /yr | What decided it |
|---|---|---:|---:|---|
| detection | ADNEX | 510 | 42.5 | **output shape** — five categories, not a threshold |
| response | *(gap)* | — | — | the only candidate is not closed-form |
| prognosis | MSK ovarian | **69** | 3.6 | the only published option, and it disagrees with its own figure |

Three diseases, three different lessons:

- **prostate.** The best-read paper is complete and good, and its **licence**
  forbids the use
- **liver.** The best-read paper **answers a different question** than its cell
- **ovarian.** The best-read paper (RMI, 970) is **correct and superseded**,
  and the *least*-read one holds a cell while disagreeing with its own figure

Ovarian is the case where nothing about a paper's standing, high or low,
carried information about whether the implementation could be trusted. Only the
measurement did.

---

## Open items

1. **Write to Cleveland Clinic QHS** about the age term: is the deployed
   ovarian fit the one Chi et al. published, or a later refit? This is the
   single highest-value question in the disease and has not been asked.
2. **`histology_yes = serous` is an inference**, supported by three consistent
   lines of evidence but not confirmed by the authors. Same letter could ask.
3. **`msk_ovarian` has internal validation only.** Bootstrap-corrected
   c-index 0.67, against 0.53 for the previously published model for this
   stage, with **no external cohort**. That limit belongs in any reported
   comparison.
4. **The response cell needs a different kind of answer.** If the library ever
   admits models that are not closed-form, KELIM is the first candidate and the
   decision should be recorded as a policy change rather than a one-off.
5. **RMI's per-paper equation locations are not captured.** The registry says
   "Four separate papers … per-paper locations not captured". Every other
   shipped model in this disease records exactly where its numbers came from.

---

## How this dossier was built

The method is the eight steps in `docs/diseases/cvd/README.md`. Three did the
work here:

- **Step 3. Report citations *and* citations-per-year.** RMI leads on total
  citations and trails on rate; ROMA leads on rate. Neither ordering picked the
  flagship.
- **Step 5. Score usability separately from influence, and let them
  disagree.** Here they disagree in both directions at once: the most-cited
  model is retired, and the least-cited one holds a cell.
- **Step 7. Only compare discrimination measured on the same cohort.** ADNEX's
  0.943 and RMI's published figures are not from one validation set and are not
  stacked into one column. The head-to-head that does exist, ADNEX 0.93 with
  CA-125 against RMI's 0.88, same patients, is cited in the registry, not
  reconstructed here.
