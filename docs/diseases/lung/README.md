# Lung cancer: paper dossier

Five entries, four shipped, three cells filled by **three papers**, because one
model occupies two of them. Two things make this disease worth its own dossier:
it holds the library's **cleanest natural experiment on where a model's training
data comes from**, and its highest-cited-per-year paper reports **no
discrimination statistic at all**.

Bibliometrics: `bibliometrics.json`, resolved via OpenAlex 2026-08-17.

---

## The papers

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---:|---:|---:|:--:|:--:|---|
| **Tammemägi et al — PLCOm2012** ([10.1056/NEJMoa1211776](https://doi.org/10.1056/NEJMoa1211776)) | detection | 2013 | **N Engl J Med** | **1,031** | 79.3 | ✗ | ✅ **Table 2** | ✅ **flagship** as `plcom2012`, but `not_ehr` |
| **Mezquita et al — LIPI** ([10.1001/jamaoncol.2017.4771](https://doi.org/10.1001/jamaoncol.2017.4771)) | response **and** prognosis | 2018 | JAMA Oncol | 970 | **121.2** | ✗ | ✅ a two-item definition | ✅ **flagship** of both cells as `lipi` / `lipi_prognosis` |
| **Chandran et al — Optum EHR LASSO** ([10.1158/1055-9965.EPI-22-0873](https://doi.org/10.1158/1055-9965.EPI-22-0873)) | detection | 2023 | Cancer Epidemiol Biomarkers Prev | 49 | 12.2 | ✅ **Apache-2.0, fitted model** | ✅ **279 coefficients** | ✅ **alternative** as `optum_lung_lasso` |
| TNM staging | prognosis | — | guideline | — | — | ✗ web only | ✗ | ✗ **catalog** |

*OpenAlex dates the Optum paper 2022 from its online-first posting; the citation
year is 2023, verified against the PubMed record (PMID 36576991,
Cancer Epidemiol Biomarkers Prev 2023;32(3):337-343).*

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Read by us? |
|---|---:|---|---|
| `plcom2012` | **1,031** | **Table 2**, "Modified Logistic-Regression Prediction Model (PLCOm2012) … for 36,286 Control Participants Who Had Ever Smoked" — coefficients and the model constant. | ✅ |
| `lipi` / `lipi_prognosis` | 970 | **Methods, "Patients"**, final paragraph — a two-item definition, not a fitted equation. The dNLR formula is in the Introduction. | ✅ |
| `optum_lung_lasso` | 49 | **`ohdsi-studies/lungCancerPrognostic` at `61c526ea`**, `inst/models/full_model/model.json` — the intercept and 16,633 betas, of which **279 are non-zero**. | ✅ downloaded and counted |

The third is the only model in the library whose parameters were obtained by
downloading a **serialised fitted artifact** rather than reading a table or a
figure. Intercept −8.8024; 279 non-zero of 16,634 rows, matching the paper's
stated 278 covariates plus intercept; `trainDetails` naming
`cdm_optum_ehr_v1705` and 4,777,606 patients, matching the paper's cohort.

---

## Detection: two models, one question, and the trade is data access

This cell is the library's clearest controlled comparison, because the two
models differ on almost nothing except **where their training data came from**.

| | **PLCOm2012** (2013) | **Optum EHR LASSO** (2023) |
|---|---|---|
| Journal | **N Engl J Med** | Cancer Epidemiol Biomarkers Prev |
| Citations | **1,031** (79.3/yr) | 49 (12.2/yr) |
| Developed on | **randomised trial** (PLCO) | **electronic health records** (Optum) |
| Reads | **questionnaire** | **routine record fields** |
| Cohort | 36,286 ever-smoking controls | **4,777,606** patients |
| Discrimination | **AUC 0.803 / 0.797** | AUC 0.76 internal, **0.81 external** (Mercy EHR), 0.72 (claims) |
| Runs on our data | ❌ **`not_ehr`** | ✅ **`routine`** |
| In the library | **flagship** | **alternative** |

**Why PLCOm2012 cannot be computed from a record**, in its own registry note:

> Education level, and pack-years **split into cigarettes per day, duration and
> years since quitting**. Most EHRs code smoking as a status, not as those three
> numbers.

**Why the Optum model can:** diagnoses, medications, laboratory results,
procedures, visits, devices, demographics and coded smoking status. **No
questionnaire item anywhere.** That is the entire reason it is carried.

### They are both flagships of something, and the registry says which

PLCOm2012 stays the flagship. It **defines screening eligibility in national
guidelines**, which makes it the threshold any new lung model is measured
against, a fact about clinical practice, not about AUC. The Optum model sits
**alongside** it as the EHR-native comparator, and its `tier_note` records the
distinction rather than leaving it to be inferred.

The comparison is not "which model is better". It is: **a model that scores
0.80 on questionnaire data and 0.00 on ours, versus one that scores 0.76–0.81
on ours.**

---

## Response and prognosis: one model, two cells, no duplication

`lipi` and `lipi_prognosis` are the same score. The registry handles this by
**re-export**, not duplication:

> one model occupies two cells; the prognosis cell **re-exports the response
> module** rather than duplicating the score

The distinction is real and worth keeping. LIPI was derived to predict outcomes
on immune-checkpoint inhibitors, a treatment-response question. It is also
validated as a plain prognostic stratifier in advanced NSCLC, independent of
what treatment is given. Two questions, one arithmetic, one implementation.

### It has no c-index, and that is a property of the paper

The registry records:

> n/a as a c-index. LIPI is a **3-group ordinal stratifier** and the paper
> reports no concordance or AUC anywhere. Its evidence is **separation**:
> median OS **34 / 10 / 3 months** for good / intermediate / poor (P < .001).

A 31-month spread between the best and worst groups, from **two routine values**
LDH against the local upper limit of normal, and a derived
neutrophil-to-lymphocyte ratio from a differential white count. `ehr_availability:
routine`.

This is the same shape as gastric's ABC method: a stratifier whose claim is
separation, evidenced by a table of outcomes rather than a discrimination
statistic. Recording "n/a as a c-index" and then the medians is more honest than
computing a concordance from published group medians and presenting it as the
paper's.

**LIPI is the highest-cited-per-year paper in this disease, 121.2, and it
publishes no discrimination statistic.** Citation rate carried no information
about what the paper reports.

---

## What this disease shows that the others do not

| Axis | Flagship | Cites | /yr | Developed on | Runs on our data |
|---|---|---:|---:|---|---|
| detection | PLCOm2012 | **1,031** | 79.3 | randomised trial | ❌ |
| detection *(alt)* | Optum LASSO | 49 | 12.2 | **EHR** | ✅ |
| response | LIPI | 970 | **121.2** | institutional cohorts | ✅ |
| prognosis | LIPI *(re-export)* | 970 | 121.2 | — | ✅ |

Across the dossiers so far, four different ways for a paper's standing and its
usability to come apart:

- **prostate.** The best-read paper is complete and good, and its **licence**
  forbids the use
- **liver.** The best-read paper **answers a different question** than its cell
- **ovarian.** The *least*-read paper holds a cell and **disagrees with its own
  figure**
- **lung.** The best-read paper is complete, correct, guideline-defining, and
  **its inputs do not exist in a health record**

The lung case is the one that most directly threatens this library's purpose. A
model published in the *New England Journal of Medicine*, cited a thousand
times, defining who gets screened in several countries, **cannot be run on the
data we have**, not because of a licence, a paywall or a missing constant, but
because it asks questions a clinician records as a status and the model needs as
three numbers.

---

## Open items

1. **NCI DCEG publishes ten lung models in one R package.** `lcmodels` implements
   Bach 2003, Spitz 2007, Cassidy 2008 (LLP), Hoggart 2012, **Tammemägi 2013,
   i.e. our PLCOm2012**: Marcus 2015 (LLPi), Wilson & Weissfeld 2015
   (Pittsburgh), Katki 2016 (**LCRAT / LCDRAT**), Katki 2018, and Cheung 2019
   (**LYFS-CT**). It ships under an NIH "Non-Proprietary Software Transfer
   Agreement" that states no restriction on commercial use or redistribution,
   read 2026-08-14, and worth one legal confirmation before relying on it.

   Two consequences: **our PLCOm2012 could be parity-checked against NCI's own
   implementation**, raising it from route 5 (re-derived from the paper) to
   route 1 (run the vendor's code); and nine further comparators become
   available at once, including **LYFS-CT, which estimates life-years gained
   from screening**, a decision quantity no baseline in the library currently
   produces.

2. **Sybil** (Mikhael et al., *JCO* 2023;41(12):2191-2200) is MIT-licensed with
   downloadable weights and reports 1-year AUC 0.92 / 0.86 / 0.94 across three
   cohorts. It reads **a single LDCT and nothing else**, no age, no smoking
   history, no clinical variable. Whether it belongs here depends on whether the
   platform holds imaging, which has not been established. **Sybil-Epi**, which
   combines its image features with clinical factors, is the multimodal
   comparator and is also MIT.

3. **The Optum model's covariateIds need mapping** to the platform's OMOP
   concepts before it can run, 279 of them. That is work, not a blocker, and it
   needs no correspondence with anyone.

---

## How this dossier was built

The method is the eight steps in `docs/diseases/cvd/README.md`. Three did the
work here:

- **Step 5. Score usability separately from influence, and let them
  disagree.** They disagree by a factor of twenty in citations and by a hard
  boundary in usability.
- **Step 6. Write down the negative results with their reasons.** LIPI's
  missing c-index is a property of the paper and is recorded as one.
- **Step 8. Check whether "has code" means "has a model".** The Optum entry is
  the case where it does, completely: a serialised fitted model under Apache-2.0,
  with the coefficient count verified against the paper's own text.
