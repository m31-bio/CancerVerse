# Oesophageal cancer: paper dossier

Five papers were assessed and three are implemented, filling all three axes.
**Neither `chau_eg` nor `shapiro_ncrt` has been parity-checked.** No
independent implementation of either exists to run them against, so their
constants were transcribed from the paper and checked against it. That is the
most important thing this dossier records.

Bibliometrics: `bibliometrics.json`, resolved via OpenAlex 2026-08-17.

---

## The papers

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---:|---:|---:|:--:|:--:|---|
| **Chau et al — prognostic index** ([10.1200/JCO.2004.01.020](https://doi.org/10.1200/JCO.2004.01.020)) | response | 2004 | J Clin Oncol | **533** | 24.2 | ✗ | ✅ **Tables 3 and 4** | ✅ **flagship** as `chau_eg` — **transcription checked; no independent implementation exists to run it against** |
| **Kunzmann et al — points model** ([10.1016/j.cgh.2018.03.014](https://doi.org/10.1016/j.cgh.2018.03.014)) | detection | 2018 | Clin Gastroenterol Hepatol | 62 | 7.8 | ✗ | ✅ **Table 2** | ✅ **flagship** as `kunzmann`, parity-checked |
| **Shapiro et al — nCRT nomogram** ([10.1002/bjs.10142](https://doi.org/10.1002/bjs.10142)) | prognosis | 2016 | Br J Surg | 35 | 3.5 | ✗ | ✅ **Fig. 1 — the whole model** | ✅ **flagship** as `shapiro_ncrt` — **transcription checked; no independent implementation exists to run it against** |
| AUGIS Survival Predictor | prognosis | — | Ann Surg Oncol | — | — | ✗ | ✗ **random survival forest** | ✗ **catalog** — nothing to transcribe |
| *(response, curative setting)* | response | — | — | — | — | — | — | ✗ **gap** — re-searched 2026-08-17, both routes fail |

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Parity |
|---|---:|---|---|
| `kunzmann` | 62 | **Table 2**, "Risk factors associated with oEAC in a stepwise logistic regression and the points assigned for the points based model". | ✅ checked |
| `chau_eg` | **533** | **Table 3** ("Multivariate Baseline Prognostic Model") for four hazard ratios with 99% CIs, and **Table 4** for the logistic model. | ⚠️ **not_checked** |
| `shapiro_ncrt` | 35 | **Fig. 1**, "Nomogram for overall survival as developed in 626 patients", p. 1043 — three predictor point scales plus a total-points axis. **The entire model is the figure.** | ⚠️ **not_checked** |

Two of three flagships carry `parity_status: not_checked` and `license:
restricted`. Both were implemented in the last few days. This is the least
verified cell-set in the library and the dossier should say so plainly rather
than let three green "implemented" labels imply otherwise.

---

## Detection: a points model that runs on primary-care data

`kunzmann` reports **AUROC 0.80 (0.77–0.82)**, 0.79 internally validated, and
is `ehr_availability: routine`, built on UK primary care in people aged 50+.

Its scope note is a hard boundary, not a caveat:

> **ADENOCARCINOMA only, not squamous cell carcinoma.** A different disease,
> different risk factors.

Oesophageal adenocarcinoma and squamous cell carcinoma share an organ and
almost nothing else: different aetiology, different geography, different risk
profile. A model fitted for one is not conservative for the other; it is
answering a different question. Running this model on an unselected oesophageal
cohort would mix the two.

Its article is **CC BY-NC**, with a `license_basis` recording the reasoning:
the same treatment as the other noncommercially licensed sources here.

---

## Response: one cell, two questions, and only one of them is answerable

`chau_eg` answers **how long a patient is likely to survive on first-line
palliative chemotherapy** for locally advanced or metastatic disease. Four
prognostic factors, from Table 3, at the *start* of treatment.

That is a treatment-setting prognosis, not a treatment-benefit estimate. It
informs a decision (whether to start palliative chemotherapy, and what to tell
the patient) without estimating what the chemotherapy *adds*, because there is
no comparison arm. Same shape as HAP in liver.

### The curative-setting question is a real gap, re-searched twice

`esophageal_response_gap` was re-searched on **2026-08-17**, both routes, and
the note supersedes a 2026-08-06 note which had itself corrected an earlier
claim about the literature. The registry records that **both routes fail for
different reasons**, which is the useful form of a negative result, because it
tells the next person which route to retry if circumstances change.

Route 1 is the curative-setting question: pathological complete response after
neoadjuvant chemoradiotherapy, the same question `wang_larc_pcr` answers for
rectal cancer. That it is answerable there and not here is a fact about the
literature, not about the disease.

---

## Prognosis: the whole model is a figure, and the figure is enough

`shapiro_ncrt` predicts overall survival after CROSS-regimen neoadjuvant
chemoradiotherapy **followed by resection**. The registry is precise about what
Fig. 1 contains:

> the entire model: three predictor point scales plus a total-points axis

No table, no supplement, no deployment. Everything needed is drawn.

**c-index 0.63** at internal validation (0.62 and 0.63 cross-validating between
the two centres), **0.61 for OS and 0.64 for PFS** on external validation in 975
patients. Modest, and externally validated, which most models in this library
are not.

Two limits that shape when it can be used:

- **Two of its three inputs are post-resection.** It is not a pre-treatment
  model; it answers a question asked after surgery.
- It applies to the **CROSS regimen** specifically.

### The better model in this cell cannot be transcribed

`esophageal_prognosis_catalog` records the AUGIS Survival Predictor (*Ann Surg
Oncol*, PMC9831040) as the strongest model found, and why it is not here:

> It is a **random survival forest**. There is no coefficient table because the
> model is a few thousand decision trees. Nothing to transcribe, and no closed
> form to reproduce.

This joins ovarian's KELIM (nonlinear population-PK), pancreatic's PancPRO
(Mendelian carrier model), and the CEUS/radiomics models in gastric, cervical
and pancreatic response. Six cells across the library are now blocked by
**model class** rather than by access, and that count is worth tracking
separately, and no email closes any of them.

---

## What this disease shows that the others do not

| Axis | Flagship | Cites | /yr | Discrimination | Parity | Licence |
|---|---|---:|---:|---|---|---|
| detection | Kunzmann | 62 | 7.8 | AUROC 0.80 | ✅ | CC BY-NC |
| response | Chau index | **533** | 24.2 | — | ⚠️ **none** | restricted |
| prognosis | Shapiro | 35 | 3.5 | c 0.63 | ⚠️ **none** | restricted |

Every other dossier here can say "parity-checked" for its flagships. This one
cannot, for two of three, and the reason is simply that they landed days ago.
That is a normal state for work in progress and an abnormal one to publish
without marking. A library whose claim is verifiability should be loudest
about the cells where verification has not happened yet.

The second point is about the **model-class boundary**. This is the third
disease where the strongest available model is one this library structurally
cannot take: a random forest here, a PK model in ovarian, a Mendelian
calculator in pancreatic. The boundary is a real design choice: models that
can be evaluated from published constants, but it now excludes a specific and
growing class of the best work.

---

## Open items

1. **`chau_eg` and `shapiro_ncrt` both need parity checks.** Neither has an
   external implementation to diff against, so both would be route 5,
   re-derived from the paper, with a worked example if either paper contains
   one. Shapiro's nomogram can be *measured*, the way the gastric, ovarian and
   pancreatic figures were, which would be a stronger check than re-reading it.
2. **Both are `license: restricted`.** They have `license_basis` entries; the
   underlying question, reading coefficients out of a paper that grants no
   reuse licence, is the same one outstanding for `cibula_arrm`, and should be
   decided once for the class.
3. **The curative-setting response gap** has been searched twice to exhaustion.
   It should not be searched a third time without new information; the blocker
   text names what would change the answer.
4. **AUGIS would need a model-class decision**, not a retrieval effort. Same
   decision as KELIM and PancPRO, and the three should be taken together.

---

## How this dossier was built

The method is the eight steps in `docs/diseases/cvd/README.md`. Three did the
work here:

- **Step 5. Score usability separately from influence.** Chau is eight times
  more cited than Shapiro and fifteen times more than Kunzmann, and is the least
  verified of the three.
- **Step 6. Write down the negative results with their reasons.** The response
  gap records *two* routes and *two different* reasons they fail, which is what
  makes it actionable rather than discouraging.
- **Step 8. Check whether "has code" means "has a model".** Inverted here:
  AUGIS has a model and no transcribable form, which is a different failure from
  having code that cannot be licensed.
