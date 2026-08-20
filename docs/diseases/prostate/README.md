# Prostate cancer: paper dossier

Every paper this library has considered for prostate cancer, on all three axes,
with what each one actually gives you and how much the field has read it.

Bibliometrics are in `bibliometrics.json`, fetched from OpenAlex on 2026-08-14
by `scripts/fetch_impact.py`. Regenerate rather than retype.

Status: **3 of 3 axes filled**, all three flagships implemented and
parity-checked. This is the only disease in the library where all three
flagships were chosen for a reason *other than* being the best-read paper,
twice on licensing, once because nothing else exists.

---

## The papers

`code` = a runnable artifact exists (repo, package, or a live calculator that
exposes its own fit). `formula` = enough is printed to compute an answer:
coefficients **and** whatever turns them into a number.

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---|---:|---:|:--:|:--:|---|
| **Ankerst et al — Extended PBCG** ([10.1186/s12874-022-01674-x](https://doi.org/10.1186/s12874-022-01674-x)) | detection | 2022 | BMC Med Res Methodol | 3 | 0.8 | ✅ **CC BY 4.0 supplement** | ✅ **full** | ✅ **flagship** as `pbcg_extended`, parity-checked |
| Ankerst et al — PBCG ([10.1016/j.eururo.2018.05.003](https://doi.org/10.1016/j.eururo.2018.05.003)) | detection | 2018 | European Urology | **136** | **17.0** | ⚠️ riskcalc.org only | ✅ full | ✗ **catalog** — licence, see below |
| **Roobol et al — ERSPC RC3** ([10.1007/s00345-011-0804-y](https://doi.org/10.1007/s00345-011-0804-y)) | detection | 2012 | World J Urol | 118 | 7.9 | ✗ web only (dead Flash) | ✅ **full** | ✅ **alternative** as `erspc_rc3`, parity-checked |
| SWOP RC1/2/5/6, ERSPC RC4/5 | detection | — | — | — | — | ✗ web only | ✅ full | ✗ **catalog** — same family, different populations |
| PCPT Risk Calculator 2.0 | detection | — | — | — | — | ✗ | ✗ | ✗ **catalog** — superseded by PBCG |
| **Nguyen et al — REDUCE metagram** ([10.3389/fonc.2012.00138](https://doi.org/10.3389/fonc.2012.00138)) | response | 2012 | Frontiers in Oncology | **1** | **0.1** | ✅ riskcalc.org R source | ✗ **none in the paper** | ✅ **flagship** as `dutasteride`, parity-checked |
| **Cooperberg et al — UCSF-CAPRA** ([10.1097/01.ju.0000158155.33890.e7](https://doi.org/10.1097/01.ju.0000158155.33890.e7)) | prognosis | 2005 | J Urol | **772** | **36.8** | ✗ web only | ✅ **full** | ✅ **flagship** as `capra`, parity-checked |
| MSK prostate nomograms (post-RP) | prognosis | — | portal | — | — | ✗ web only | ✗ | ✗ **catalog** — portal, no published equation |

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Read by us? |
|---|---:|---|---|
| `capra` | **772** | **Table 1**, "The UCSF-CAPRA scoring system". J Urol 2005;173(6):1938-1942 (PMC2948569). | ✅ |
| `erspc_rc3` | 118 | **Appendix**, under "Formulas used to calculate volume classes and the DRE ERSPC RC risks" — the linear predictor is printed in full. | ✅ read from PMC3321270 |
| `pbcg_extended` | 3 | **Additional file 2** (`12874_2022_1674_MOESM2_ESM.txt`) — the full 1,024 × 13 coefficient matrix and the `risk()` function, CC BY 4.0. | ✅ read and executed |
| `dutasteride` | 1 | **Not the paper at all.** 315 coefficients across 17 Cox sub-models, machine-extracted from the deployed calculator's R source. Discrimination *is* in the paper, Table 4. | ✅ extracted, parity-checked |

Three of the four are primary-sourced from an artifact anyone can re-open. The
fourth is the interesting one and is discussed below.

### How far riskcalc.org can be trusted as a source: measured, 2026-08-14

`dutasteride` is the only shipped model here whose coefficients exist nowhere
but a vendor's deployment, so the question "is that source faithful?" is not
rhetorical for this disease. It was answered elsewhere in the library and the
answer transfers.

Three other models take their coefficients from the same repository
(`ClevelandClinicQHS/riskcalc-website`) and their papers *do* print a nomogram.
Each nomogram was measured: axis labels located by ink position rather than
read by character recognition, the figure's own Points axis used as the only
ruler, and the scale for our implementation taken from a predictor independent
of the one being compared.

| Model | What was compared | Agreement |
|---|---|---|
| `msk_gastric` | age spline, scale from the Depth axis | **0.4 points** on a 0–100 axis |
| `msk_pancreatic` | four predictors, scale from Splenectomy | **0.9 points**, against a ruler whose own error is 0.4 |
| `msk_ovarian` | age spline, scale from residual disease | **17 points** — does not agree |

So the source is mostly faithful and **not unconditionally so**. Two cells
reproduce their published figure to a fraction of a point; one does not, and
its disagreement grows monotonically with age until the implied total exceeds
the figure's own axis by 10%.

**What this means for `dutasteride`, stated plainly because it is unfavourable
to it:** the same check cannot be run here. The REDUCE paper prints no
nomogram, no figure, no coefficient table, nothing to measure against. Parity
against the deployment is the *only* verification this model can have, and the
ovarian result shows that parity against a deployment is not the same as
agreement with what the authors published. Nothing suggests the REDUCE
deployment is wrong. Nothing could show that it is right, either.

That asymmetry is the reason this section exists in a dossier whose other three
models are fine.

---

## Detection: the flagship is the least-read paper in the cell, twice over

| | Extended PBCG (2022) | PBCG (2018) | ERSPC RC3 (2012) |
|---|---|---|---|
| Citations | **3** | **136** | 118 |
| Citations/year | 0.8 | **17.0** | 7.9 |
| **AUC, same validation set** | **75.7** (74.4–77.1) | **66.9** (65.4–68.5) | — |
| Coefficients published | ✅ CC BY 4.0 supplement | ⚠️ only via riskcalc.org | ✅ paper appendix |
| Licence on the coefficients | **CC BY 4.0** | **PolyForm Noncommercial** | open (paper) |
| Missing-data patterns | **1,024** | 8 | none — all 3 required |
| **In the library** | **flagship** | catalog | alternative |

**Read the AUC row first.** Both figures come from the 2022 paper, scored on the
same withheld European cohort of 5,540 biopsies, not two papers each reporting
its own. The 2022 paper states it verbatim: the 2018 tool "based on only 6 of
the 12 risk factors used here obtained a CIL of −5.9 (95% CI −7.1, −4.7), and an
AUC of 66.9 (95% CI 65.4, 68.5), which is 10 points lower than any of the
methods incorporating the additional risk factors."

So the flagship is **~9 AUC points better** than the paper with 45× its
citations. That was not known when it was adopted, it was chosen on licensing,
and it means the licensing argument was never the whole case.

**The most-cited paper in this cell is not in the library, and the reason it was
originally excluded was a licence.** PBCG 2018 (136 citations, 17.0/yr) is a
real model. Its coefficients are only machine-readable from riskcalc.org, whose
source is **PolyForm Noncommercial 1.0.0**, which forbids exactly the use a
company repository makes of it. The 2022 extension publishes its complete
coefficient matrix as a **CC BY 4.0** journal supplement, so it can ship. It has
3 citations.

That is a 45× citation gap, and the decision was made on which file the authors
put the numbers in.

**Reading the AUCs afterwards showed the decision was right for a second,
stronger reason**, 75.7 against 66.9 head-to-head. Worth being honest about the
order: the licence decided it, and the performance evidence arrived later and
happened to agree. Had it disagreed, the licence would still have been binding,
and the registry would have had to say so.

The 2022 version is better structurally too, 1,024 missing-data sub-models
instead of 8, ten optional predictors instead of three, and no imputation
anywhere: a record missing family history is scored by the model *fitted without
it*. For EHR deployment that behaviour matters more than either paper's citation
count.

One caveat on the shipped variant: the available-cases method was chosen for
**calibration**, not discrimination. Table 2 gives it the best CIL by a wide
margin (−2.9 against imputation's −13.3) while its AUC of 75.7 is the *lowest*
of the six methods tried, which span 75.4–77.4. The choice costs at most 1.7 AUC
points and buys a model that is not systematically wrong about absolute risk.

**ERSPC RC3 is kept as an alternative rather than discarded**, and not out of
completeness. External validation found PBCG improved calibration in White men
but **over-predicted in Black and other groups** at most thresholds. Two models
with different failure modes are more useful than one, and the choice between
them is a property of the cohort, not of the papers.

### The dead-calculator warning

ERSPC RC3's coefficients were recovered by decompiling SWOP's own **Flash**
calculator (`/2011/swf/c03dre.swf`). Flash is end-of-life, so the tool cannot
be run and no output can be obtained, but the SWF still serves, and its
ActionScript stores literals as IEEE-754 doubles. All six constants were
recovered, worst deviation 2.2e-06.

That verified the *model* rather than one output, which is stronger. It is also
a warning: six models in this library were verified by reading a live
calculator, and that route expires without notice.

---

## Response: one citation, and it is still the right choice

**The REDUCE metagram has 1 citation.** Not a lookup error, confirmed against
Crossref on 2026-08-14, which reports the same figure for
`10.3389/fonc.2012.00138`. Frontiers in Oncology, 2012, Nguyen/Isariyawongse/
Yu/Kattan.

It is the flagship anyway, because **the alternative is an empty cell.** This
axis was recorded as a gap ("no published closed-form response equation found")
until 2026-08-06, when that turned out to be wrong: the REDUCE models are
published with full coefficients in riskcalc.org's source. The gap entry now
records its own correction.

What makes it worth having: it reports **nine outcomes across two arms,
including three harms**, erectile dysfunction, gynecomastia, urinary tract
infection. A chemoprevention model that reports only benefit is not answering
the clinical question, and this one does not.

### But read Table 4 before using the harm outcomes

The paper reports a concordance index per outcome per arm, 18 figures, not one:

| Outcome | Placebo | Dutasteride |
|---|---:|---:|
| BPH symptoms | **0.70** | 0.60 |
| High-grade PCa | **0.69** | **0.71** |
| Acute urinary retention | 0.66 | 0.62 |
| Any PCa | 0.62 | 0.61 |
| Erectile dysfunction | 0.59 | 0.60 |
| UTI | 0.55 | 0.51 |
| HGPIN | 0.53 | **0.47** |
| Gynecomastia | 0.52 | 0.52 |
| ASAP | **0.48** | 0.53 |

**Two figures are below 0.5:** HGPIN under dutasteride (0.472) and ASAP under
placebo (0.485), which is worse than a coin toss. The authors say so
themselves, verbatim: *"Several of the nomograms (e.g., those for UTI,
gynecomastia, HGPIN, ASAP) demonstrate poor discrimination and are based on
those models that contained a large proportion of non-predictive variables."*

The uncomfortable shape of this: the two endpoints worth having the model for,
high-grade cancer (0.69/0.71) and BPH symptoms (0.70), discriminate
reasonably. **The harms, which are the reason a chemoprevention tool is more
honest than a benefit-only one, are the ones that discriminate worst.** Use the
benefit outcomes; treat the harm outcomes as indicative at best.

**The catch, stated plainly:** the paper contains no closed form. All 315
coefficients across 17 Cox sub-models were machine-extracted from the deployed
calculator's R source, which is **PolyForm Noncommercial**, the same licence
that disqualified PBCG 2018. The extraction script is therefore excluded from
the public sync (`NONCOMMERCIAL_REFERENCE` in `scripts/sync_public_repo.py`),
and the captured fixtures are what the test suite compares against.

This is the one cell in prostate where the licensing question is **not**
settled by the flagship choice. It is recorded rather than resolved.

---

## Prognosis: the one uncomplicated cell

**UCSF-CAPRA, 772 citations, 36.8/yr, the most-cited paper in this dossier and
also the right choice.** No licence problem, no missing constant: Table 1 prints
the whole scoring system, five predictors on a 0–10 scale.

Two limits worth knowing:

- **Concordance index 0.66.** Modest, and recorded as such rather than
  omitted. It remains the standard preoperative score.
- **Preoperative only.** CAPRA-S (postoperative, *Cancer* 2011) is a different
  model and is not implemented.

The MSK post-radical-prostatectomy nomograms are catalogued but not
implemented: they live on a portal with no published equation, the same
structural problem as four cervical prognosis papers.

---

## What this disease shows that the others do not

Across three axes the flagship was chosen on citations **zero times out of
three**:

| Axis | Flagship | Cites | Best-read paper in the cell | Why the flagship won |
|---|---|---:|---|---|
| detection | Extended PBCG | 3 | PBCG 2018 (136) | licence — CC BY vs PolyForm NC |
| response | REDUCE metagram | 1 | *it is the only one* | nothing else is published |
| prognosis | UCSF-CAPRA | 772 | itself | genuinely both |

Compare cardiovascular disease, where the most-cited paper in the AF cell
(CHA₂DS₂-VASc, 6,781) is implemented but *outperformed*, and cervical, where the
most-cited prognosis paper is unusable for want of a baseline survival.

Three diseases, three different reasons for influence and usability to come
apart:

- **cervical.** The best-read paper omits a constant
- **cvd.** The best-read paper is complete but discriminates worse
- **prostate.** The best-read paper is complete *and* good, and its licence
  forbids the use

The third is the one a reader is least likely to anticipate, and it is the one
that decides what this library can ship.

---

## Open items

1. ~~`pbcg_extended` has no discrimination recorded~~ **Closed.**
   AUC 75.7 (74.4–77.1) external, 66.9 (65.4–68.5) for PBCG 2018 on the same
   set, internal cross-validation median 80 (74–84). Read from PMC9306143.
2. ~~`dutasteride` likewise~~ **Closed.** Table 4, all 18 figures
   recorded in the registry, including the two below 0.5.
3. **CAPRA-S** would fill a real gap: post-prostatectomy recurrence is a
   different decision from preoperative risk, and the cell key now supports two
   questions in one axis (see `reporting.clinical_question`).
4. **`dutasteride` cannot be checked against its own publication and never
   will be**, the paper prints no nomogram and no coefficient table, so the
   measurement that cleared `msk_gastric` and `msk_pancreatic`, and failed
   `msk_ovarian`, has nothing to run against here. The two ways to close it
   are to ask Cleveland Clinic QHS whether the deployed REDUCE fit is the one
   the paper describes, or to find a validation study that reprints the linear
   predictor. Neither has been tried. Until one is, this model's verification
   ceiling is lower than every other flagship in the library, and the dossier
   should say so rather than let `parity-checked` imply otherwise.

---

## How this dossier was built

The method is shared with `docs/diseases/cervical/` and `docs/diseases/cvd/`;
see the CVD dossier for the full eight steps. Two of them did the work here:

- **Step 5. Score usability separately from influence, and let them
  disagree.** In this disease they disagree in every cell.
- **Step 8. Check whether "has code" means "has a model".** Both PBCG 2018 and
  the REDUCE metagram have runnable code. For one that was not enough to ship
  it; for the other it was the only reason it could be shipped at all. The
  difference is the licence on the file, which no citation count reveals.
