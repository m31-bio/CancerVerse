# Pancreatic cancer: paper dossier

Five entries, two shipped. The two shipped models sit at opposite ends of
everything that matters: **AUROC 0.87 from four routine values, and c-index
0.62 from operative pathology.** Both are the right choice for their cell, and
the reason is the same one: each is the only published option that can be
computed at all.

Bibliometrics: `bibliometrics.json`, resolved via OpenAlex 2026-08-17.

---

## The papers

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---:|---:|---:|:--:|:--:|---|
| **Sharma et al — END-PAC** ([10.1053/j.gastro.2018.05.023](https://doi.org/10.1053/j.gastro.2018.05.023)) | detection | 2018 | Gastroenterology | 382 | **47.8** | ✗ | ✅ **Table 1** | ✅ **flagship** as `endpac` |
| **Brennan et al — MSK pancreatic nomogram** ([10.1097/01.sla.0000133125.85489.07](https://doi.org/10.1097/01.sla.0000133125.85489.07)) | prognosis | 2004 | Ann Surg | 368 | 16.7 | ⚠️ riskcalc.org only | ✗ **nomogram figure only** | ✅ **flagship** as `msk_pancreatic` — **agrees with its own figure** |
| PancPRO / CAPS high-risk criteria | detection | — | — | — | — | ✗ | ✗ **not a linear predictor** | ✗ **catalog** — Mendelian carrier model |
| Resectability staging | prognosis | — | portal | — | — | ✗ web only | ✗ | ✗ **catalog** — superseded |
| *(response)* | response | — | — | — | — | — | — | ✗ **gap** — searched, and the reason is the inputs |

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Read by us? |
|---|---:|---|---|
| `endpac` | 382 | **Table 1**, "Enriching New-onset Diabetes for Pancreatic Cancer (END-PDAC) score parameters". | ✅ **re-checked mechanically 2026-08-18** — 39 facts, all agree |
| `msk_pancreatic` | 368 | **Not the paper.** *Ann Surg* 2004 prints a nomogram (Fig. 2) and no equation. Coefficients from the deployed R at `ClevelandClinicQHS/riskcalc-website`. | ⚠️ verified against the figure — see below |

**A naming trap worth recording:** the model is END-PAC everywhere except its
own parameter table, which calls it **END-PDAC**. Anyone searching the paper
for "END-PAC score parameters" will not find the table.

**And the abstract has now been wrong twice about this model.** The `<0` versus
`<=0` low-risk boundary was the first, caught in 2026-08-06 by re-deriving the
paper's own group proportions. The second surfaced on 2026-08-18: the validation
specificity at the ≥3 cut is **85% in the abstract and 82% in the Results**, same
cohort, same cut-off, unreconciled. We had quoted the abstract; we now quote the
Results, on the same reasoning as the first correction. Neither number is used in
any computation. END-PAC returns a score and a band, never a probability, so what changed is documentation. The pattern is the point: for this paper, the
Results have been right both times.

---

## Detection: the strongest model in the disease, and it is not a screen

`endpac` reports **AUROC 0.87** in discovery, from four routinely available
quantities, and it is `ehr_availability: routine`, the only pancreatic model
that runs without specialty data.

Its scope note is the whole point of it and must travel with every number:

> Adults with **glycemically-defined new-onset diabetes** (validation in
> ≥50-year-olds). **Enriches an already-selected group; NOT a general-population
> screen.**

Pancreatic cancer's base rate makes general-population screening hopeless, and
END-PAC does not attempt it. It takes a group already at raised risk (people
who have just developed diabetes, which pancreatic cancer can cause, and sorts
within it. An AUROC of 0.87 in that setting is a different claim from 0.87 in
an unselected population, and the difference is the entire clinical design.

### A head-to-head that does not exist yet

CanPredict (pancreatic), Clift et al., *Br J Cancer* 2024;130(12):1969–1978:
addresses **the same enriched population**: new-onset diabetes, Harrell's C
0.802, developed on 253,766 people with type 2 diabetes of whom 767 developed
pancreatic cancer. It is the only other model built for this exact question.

**The two have never been compared.** END-PAC's paper predates it; CanPredict's
does not cite a head-to-head. That comparison is available to us and is not
available in the literature, which makes it worth doing rather than waiting
for.

---

## Prognosis: the third riskcalc model, and the third one measured

`msk_pancreatic` shares its provenance problem with `msk_gastric` and
`msk_ovarian`: the paper prints a figure, the numbers live only in a
deployment. Measured against the published Fig. 2 on 2026-08-14:

| Predictor | Figure | Ours | Difference |
|---|---:|---:|---:|
| Splenectomy *(the calibrator)* | 61.7 | 61.7 | — |
| Head vs Other | 51.5 | 51.6 | **+0.1** |
| Differentiation well→poor | 35.3 | 35.4 | **+0.1** |
| T stage | 62.0 | 62.8 | +0.8 |
| Positive nodes 0→39 | 68.8 | 67.8 | −0.9 |

Maximum deviation **0.9 points**, against a ruler whose own systematic error is
**0.4**. The figure's Points axis measures 100.4 where it should read 100,
because a line's end caps count into its extent. The positive-node spline was
separately checked point by point and agrees to **0.1** across the sharply
bending 0–1–2–3–4 segment.

**The three riskcalc models together are the only reason any of them can be
interpreted:**

| Model | Result | Scale taken from |
|---|---|---|
| `msk_gastric` | agrees, 0.4 pts | Depth axis |
| `msk_pancreatic` | agrees, 0.9 pts | Splenectomy |
| `msk_ovarian` | **disagrees, 17 pts** | residual disease |

Two independent agreements make the third result a finding rather than a
suspicion about the method.

### A false start that is recorded rather than hidden

The first attempt to calibrate this figure tried to detect the tick marks on
Head.vs.Other, got a **zero span**, and printed a full column of confident
nonsense, differences up to −63.5 points, before it was caught. The script
now asserts a positive span rather than dividing by it.

The fix was not better tick detection. On a binary axis **the span is the
line**, and the line's extent was already being measured reliably. An earlier
note in the registry said human eyes would be needed here; they were not. The
obstacle was the method.

### Its discrimination is not in its own paper either

`msk_pancreatic` reports **c-index 0.62**, and that figure comes from an
external validation published a year later (*JCO* 2005, n = 555) against 0.59
for AJCC stage, p = 0.004; a second independent cohort gives 0.61 (*Br J Surg*
2009). **The development paper reports no numeric figure at all.**

0.62 against a staging system's 0.59 is a small margin, and it is the honest
one. It belongs beside any use of this model, and beside END-PAC's 0.87 as a
reminder that the two numbers are not comparable: different cells, different
populations, different endpoints.

---

## Two model-class boundaries in one disease

Neither open cell here is blocked by a paywall, a missing constant, or a field
the platform lacks. Both are blocked by **what kind of model the literature
offers**:

**`pancpro`, detection.** PancPRO is a **Mendelian carrier model**. It
computes carrier probability from a pedigree by Bayesian inheritance
calculation, and there is no linear predictor to transcribe. The registry says
it "needs a BayesMendel port, not an LP". That is a real port, not a
transcription, and it would be the first model in the library of that class.

### Re-searched 2026-08-18, and the answer changed shape

Two new candidates, both rejected, and rejecting them is what made the real
obstacle visible.

**Koo J, Choi G, Cheon J, et al.** *Predicting Chemotherapy Response in Patients
With Advanced or Metastatic Pancreatic Cancer Using Machine Learning.* JCO Clin
Cancer Inform. 2025. [doi:10.1200/CCI-25-00124](https://doi.org/10.1200/CCI-25-00124),
PMID 41329903. Directly on-question, and **smaller than the candidate already on
file**: n=191 across two Korean centres, no external validation. Fails
criterion 3.

**Dekker EN, van Klaveren D, et al.; TAPS Consortium.** *CA19-9 response after
induction FOLFIRINOX for locally advanced pancreatic cancer.* BJS.
2025;112(2):znaf011. Five referral centres, n=213, and **not a model**.

### What this cell is actually compared against

The routine-variable answer in pancreatic cancer is not an equation. It is two
CA19-9 thresholds, and they are in clinical use:

> **CA19-9 decrease > 80%  AND  post-induction CA19-9 < 50 U/mL**

| | 3-year overall survival | What the authors advise |
|---|---:|---|
| Meets it, WHO PS 0 | **~40%** | consider surgical exploration |
| Fails it | **<20%** | be *more reluctant* to explore |
| *(reference: non-metastatic at restaging, not selected for exploration)* | 11.8% | — |

The paper publishes Cox hazard ratios for three factors and contour plots drawn
for surgeons. No nomogram, no AUC, no C-index, no external validation. The
decision language is *"be more reluctant"*, not *"this patient's response
probability is 0.63"*.

**It fails criterion 1, and not because it is incomplete.** It was never meant
to be a model. Searching for a fitted routine-variable response model in this
disease will keep returning threshold papers, because thresholds are how the
field answers this question.

**Two ways forward, and the choice changes what "baseline" means here.**

1. **Implement the rule as a binary baseline.** It has multicentre support,
   published survival separation and actual clinical adoption. The cost is that
   it emits a *group*, not a probability, so calibration, Brier and
   decision-curve net benefit are uncomputable for it, exactly as for `albi` and
   `lipi`.
2. **Accept that this cell's comparator is a clinical convention, not an
   equation.** Our model would be competing against "did CA19-9 fall by 80%",
   which is arguably the more honest comparison and does not fit the shape of a
   row in a baseline table.

Neither has been chosen. Leaving it open is recorded rather than left implicit,
because the second option would change how this cell is reported to a
collaborator.

**The response cell.** Searched 2026-08-06, and the "not searched exhaustively"
label was removed: candidates exist. The strongest genuine response model is a
**contrast-enhanced ultrasound nomogram** for neoadjuvant chemotherapy efficacy
in borderline-resectable disease, and its inputs are **CEUS kinetics, not
routine clinical variables**, the same obstacle as the radiomics models in the
gastric and cervical response cells.

These join ovarian's KELIM (a nonlinear population-PK model) as gaps that an
email cannot close. They are worth counting separately from the other kind.

---

## What this disease shows that the others do not

| Axis | Flagship | Cites | /yr | Discrimination | Inputs |
|---|---|---:|---:|---|---|
| detection | END-PAC | 382 | **47.8** | **AUROC 0.87** | **routine** — four values |
| response | *(gap)* | — | — | — | CEUS kinetics — not routine |
| prognosis | MSK pancreatic | 368 | 16.7 | **c-index 0.62** | specialty — operative pathology |

The two shipped models are 0.87 and 0.62, and both are correct choices. The
gap between them is not a quality difference between two research groups; it is
the difference between **sorting within an enriched group using cheap data**
and **predicting survival in a disease that kills most patients within two
years**. A library that ranked its cells by headline discrimination would
misread this disease entirely.

The recurring pattern across three dossiers now: **the model's own paper
frequently does not report its own discrimination.** ALBI printed it inside
figures; HAP put it in a supplementary `.doc`; MSK pancreatic never printed a
number and it had to come from someone else's validation. Three diseases,
three different places the statistic was not.

---

## Open items

1. **Run END-PAC against CanPredict (pancreatic).** Same enriched population,
   same question, never compared. The comparison is ours to make.
2. **`msk_pancreatic`'s 0.62 needs to be stated wherever the model is used.**
   It beats AJCC by 0.03. That is a real result and a small one.
3. **PancPRO would need a BayesMendel port**, a decision about model classes,
   not a retrieval task. Same shape as the ovarian KELIM question, and the two
   should be decided together rather than one at a time.
4. **The END-PDAC / END-PAC naming discrepancy** should be noted anywhere the
   parameter table is cited, or the next person to check our transcription will
   fail to find it.

---

## How this dossier was built

The method is the eight steps in `docs/diseases/cvd/README.md`. Three did the
work here:

- **Step 5. Score usability separately from influence.** Both shipped papers
  are ~370–380 citations and rank identically on influence. They differ by
  0.25 in discrimination and by an entire tier in data cost.
- **Step 6. Write down the negative results with their reasons.** Both open
  cells are blocked by model class, not by access, and saying so prevents
  someone re-running the search.
- **Step 7. Only compare discrimination measured on the same cohort.**
  END-PAC's 0.87 and MSK's 0.62 appear in the same table above with their cells
  and inputs beside them precisely so they are not read as a ranking.
