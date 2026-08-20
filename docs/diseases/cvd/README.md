# Cardiovascular disease: paper dossier

Every paper this library has considered for cardiovascular disease, on all
three axes, with what each one actually gives you and how much the field has
read it.

Bibliometrics are in `bibliometrics.json`, fetched from OpenAlex on 2026-08-14
by `scripts/fetch_impact.py`. Regenerate rather than retype.

Status: **3 of 3 axes filled**, and one cell, stroke risk in atrial
fibrillation, has four competing papers, which is why this dossier exists.
That cell is the clearest example in the library of influence and usability
pointing at different papers.

---

## The papers

`code` = a runnable artifact exists (repo, package, or a live calculator that
exposes its own fit). `formula` = enough is printed to compute an answer:
coefficients **and** whatever turns them into a number (intercept, or a
baseline survival S₀(t)). Half a formula is marked as half.

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---|---:|---:|:--:|:--:|---|
| **Khan et al — AHA PREVENT equations** ([10.1161/CIRCULATIONAHA.123.067626](https://doi.org/10.1161/CIRCULATIONAHA.123.067626)) | detection | 2023 | Circulation | 1,059 | **353.0** | ✗ | ✅ **full** | ✅ **implemented** as `prevent`, checked vs Table S25 |
| **SCORE2 working group** ([10.1093/eurheartj/ehab309](https://doi.org/10.1093/eurheartj/ehab309)) | detection | 2021 | European Heart Journal | 1,720 | **344.0** | ✗ | ✅ **full** | ✅ **implemented** as `score2` |
| **CTT Collaboration — LDL lowering meta-analysis** ([10.1016/S0140-6736(10)61350-5](https://doi.org/10.1016/S0140-6736(10)61350-5)) | response | 2010 | The Lancet | **6,516** | **407.2** | ✗ | ✅ **full** | ✅ **implemented** as `cvd_statin_benefit` (derived composition) |
| **Granger et al — GRACE** ([10.1001/archinte.163.19.2345](https://doi.org/10.1001/archinte.163.19.2345)) | prognosis | 2003 | Arch Intern Med | 2,372 | 103.1 | ✗ | ✅ **full** | ✅ **implemented** as `grace`, checked |
| **Fox et al — GRACE 2.0** ([10.1136/bmjopen-2013-004425](https://doi.org/10.1136/bmjopen-2013-004425)) | prognosis | 2014 | BMJ Open | 440 | 33.8 | ✗ | ✗ **none** | ✗ **rejected 2026-08-18** — the version guidelines recommend, and its coefficients are not published anywhere reachable. See below |
| Eagle et al — GRACE 6-month post-discharge ([10.1001/jama.291.22.2727](https://doi.org/10.1001/jama.291.22.2727)) | prognosis | 2004 | JAMA | 1,598 | 69.5 | ✗ | ? **not opened** | ✗ — a different endpoint (6-month post-discharge, not in-hospital). Citations checked, full text not read |
| **Lip et al — CHA₂DS₂-VASc** ([10.1378/chest.09-1584](https://doi.org/10.1378/chest.09-1584)) | prognosis (AF) | 2010 | CHEST | **6,781** | **398.9** | ✗ web only | ✅ **full** | ✅ **implemented** as `cha2ds2_vasc`, checked vs MDCalc |
| **Singer et al — ATRIA stroke score** ([10.1161/JAHA.113.000250](https://doi.org/10.1161/JAHA.113.000250)) | prognosis (AF) | 2013 | J Am Heart Assoc | 409 | 31.5 | ✗ web only | ✅ **full** | ✅ **implemented** as `atria_stroke_2013` — transcription checked vs Table 3, `no_independent_reference_implementation` |
| Gage et al — CHADS₂ ([10.1001/jama.285.22.2864](https://doi.org/10.1001/jama.285.22.2864)) | prognosis (AF) | 2001 | JAMA | **4,855** | 194.2 | ✗ | ✅ **full** | ✗ **catalog** — complete, but 0.69, below both above |
| Lin et al — Interpretable LR/XGB ([10.1038/s41746-026-02470-3](https://doi.org/10.1038/s41746-026-02470-3)) | prognosis (AF) | 2026 | npj Digital Medicine | 2 | 2.0 | ✅ **MIT repo + Zenodo** | ⚠️ **half** | ✗ **catalog** — best AUC, no intercept |
| Hijazi et al — ABC-stroke ([10.1093/eurheartj/ehw054](https://doi.org/10.1093/eurheartj/ehw054)) | prognosis (AF) | 2016 | European Heart Journal | 438 | 39.8 | ✗ | ⚠️ **half** | ✗ **rejected** — needs GDF-15, hs-troponin, NT-proBNP |
| HAS-BLED / MAGGIC | prognosis | — | — | — | — | ✗ | ✅ full | ✗ **catalog** — different questions (bleeding, HF mortality) |
| Framingham risk scores | detection | — | — | — | — | ✗ | ✅ full | ✗ **catalog** — superseded by PREVENT |

Note on `af_stroke_lr_2026`: it is the **only paper in this dossier with real
code**, and that code still does not make it usable. See below, that is the
most instructive row in the table.

---

## Why GRACE 1.0 (2003) and not GRACE 2.0 (2014)

Asked directly on 2026-08-18, against this project's three criteria, citations
first, journal standing second, publicly implementable parameters as the
decisive factor. The third criterion looked like it would overturn the choice.
It confirmed it instead.

| | GRACE 1.0 · Granger 2003 | GRACE 2.0 · Fox 2014 |
|---|---|---|
| Citations | **2,371** (98.8/yr) | 440 (33.8/yr) |
| Journal | Arch Intern Med (now JAMA Intern Med) | BMJ Open |
| Open access | closed | **gold, CC BY-NC** |
| Parameters published? | **yes — the complete points nomogram, Figure 4** | **no** |

GRACE 2.0 is the better model on the authors' own account, "better
discrimination and is easier to use than the previous score", derived in
32,037 patients across 14 countries and externally validated in FAST-MI. It is
also what the guidelines recommend. And it cannot be implemented from anything
published.

The reason is specific: 2.0 replaced 1.0's categorical bands with **restricted
cubic splines**, three knots for age and systolic blood pressure at the 10th,
50th and 90th centiles, four for pulse and creatinine at the 5th, 35th, 65th
and 95th. The paper prints hazard ratios "for selected intervals, to provide a
sense of how associations change over covariate ranges", which is illustrative
and not the model, and then points the reader at an external file for the
coefficients themselves. Every route it names was probed on 2026-08-18:

    outcomes-umassmed.org/grace/files/GRACE_RiskModel_Coefficients.pdf
        HTTP 200, and Content-Type text/html, body starts "<html>".
        The PDF is gone and the server answers with a page instead of a 404,
        so a check that trusted the status code would record it as reachable.
    gracescore.co.uk                DNS does not resolve
    outcomes.org/grace              200, but a portal page

The knot positions are centiles of the derivation distribution, and those
centiles are not printed either. So there is no path from published material to
a working GRACE 2.0.

**This is not a case of us picking the older paper.** It is a case of the
guideline-recommended model not publishing its parameters, while the
superseded one publishes them completely. Worth stating plainly because the
obvious future question, "shouldn't we upgrade to 2.0?", has an answer, and
it is not "we haven't got round to it".

### Two traps this turned up

**Do not parity-check `grace` against `RiskScorescvd::GRACE`.** That CRAN
package is MIT-licensed, already vendored in this repository, and already the
reference implementation for `score2`, so reaching for its GRACE function is
the obvious next move, and it would be wrong twice over. Its header says it
implements "GRACE 2.0 for 6 months outcome", a different version and a
different endpoint from ours. And its formula is linear in every continuous
variable (`xb = -7.7035 + 0.0531*age + 0.0087*HR - 0.0168*SBP + 0.1823*creatinine
+ ...`), while Fox 2014's whole contribution is that 2.0 is **non-linear**. So it
is neither Granger's 1.0 nor Fox's 2.0. Agreement would be a coincidence;
disagreement would prove nothing.

**Figure 4 contains an arithmetic error, and we do not reproduce it.** Its first
worked example lists `20 + 53 + 15 + 58 + 7 + 0 + 28 + 14` and states the total
is 196. Those components sum to **195**. Our implementation returns 195 and
15.50%, against the paper's 196 and "about 16%". The components reproduce
exactly and the slip does not. The second worked example
(`0 + 58 + 3 + 41 + 1 = 103`, ~0.9%) is correct and we return 103 and 0.89%.

---

## Where every shipped parameter actually came from

The question this section answers: **for each model in the library, which file
or which numbered table did the numbers come from, and has anyone here read
it?** Ordered by citations, most-read first.

| Model | Cites | Parameters came from | Read by us? |
|---|---:|---|---|
| `cha2ds2_vasc` | **6,781** | **Table 2** (p. 266), "The 2009 Birmingham Schema Expressed as a Point-Based Scoring System, With the Acronym CHA₂DS₂-VASc". Chest 2010;137(2):263-272. | ✅ **read 2026-08-14** |
| `cvd_statin_benefit` | 6,516 | CTT 2010 **abstract**, verbatim: RR 0.78 (0.76–0.80) per 1.0 mmol/L for major vascular events; RR 0.90 (0.87–0.93) all-cause mortality. Composed with a baseline risk from another model — not a published model itself. | ✅ abstract read |
| `grace` | 2,372 | **Figure 4** — the whole model: five per-predictor point tables, the "Other Risk Factors" box, and the points→in-hospital-mortality lookup. Results, "Predictors of mortality". Arch Intern Med 2003;163(19):2345-2353. | ✅ **READ TWICE, two routes** — 2026-08-14 off a CDN image, 2026-08-18 off a article with a real text layer. **56/56 values matched at zero tolerance** |
| `score2` | 1,720 | **Supplementary material online, Methods** — not the main text. Coefficients, baseline survival and the four risk-region recalibration constants all live there. | ✅ read 2026-08-06 (PMC8248998) |
| `prevent` | 1,059 | **Supplemental appendix**, all 100 coefficient sets (5 variants × 2 horizons × 5 outcomes × 2 sexes). Base 10-year worked example is **Table S25**. Circulation 2024. | ⚠️ **not re-read** |
| `atria_stroke_2013` | 409 | **Table 3**, "ATRIA Stroke Risk Model Point Scoring System" (two age columns + six 1-point rows). Bands from **Table 4**. PMC3698792, open access. | ✅ **read 2026-08-14, transcribed twice** |

Two of the six are weaker than they look.

- **`cha2ds2_vasc` was the worst-provenanced model in this cell and the most
  used, now closed.** Its eight point values had only ever been checked
  against MDCalc, a secondary source, because the article is paywalled.
  `mdcalc_extract.py` says in its own docstring that this is "corroboration,
  not proof", and it was recorded that way. On **2026-08-14 the PDF was
  Table 2 read directly: all eight
  values agree exactly**, and the C-statistic of 0.606 was confirmed in the
  same read. The MDCalc route now stands as an independent second source
  rather than the only one, which is the strongest position any model in this
  cell is in.
- **`grace` is now the most thoroughly re-read model in this cell, and getting
  there corrected a recorded fact about the source.** It was the cell's most
  exposed model for the reason given here until 2026-08-17: Figure 4 is a
  nomogram carrying the entire model, and it had been read ONCE, off a raster
  image pulled from JAMA's CDN. Two things came out of re-reading it.
  First, **that CDN URL now returns HTTP 403**, a verification route that
  worked on 2026-08-14 expired within four days, the same way Yoo 2012's
  calculator died on the cervical cell.
  Second, and more useful: the article supplied on 2026-08-18 carries a
  **real text layer** for Figure 4, so the nomogram extracts as text rather
  than being read off pixels. The 2026-08-14 note claiming this article "renders
  Tables 1-5 as images too, there is no machine-readable table anywhere in it"
  was true of that copy and **not true of the article**. The premise that made
  GRACE the weak link was itself wrong.
  All 56 values re-read and matched at zero tolerance: 4 Killip bands, 7 SBP,
  7 heart rate, 8 age, 7 creatinine, 3 other risk factors, and all 20 cells of
  the mortality lookup.
- **`prevent`** remains marked "identified while implementing; NOT re-read
  against the source in the 2026-08-06 pass"; see the 2026-08-14 provenance
  note, which did locate its coefficients in the supplement (Tables S12.A-J of
  the xlsx, not the appendix) but is a location check rather than a re-read of
  every one of the 100 coefficient sets.
- **`atria_stroke_2013` has the best provenance in the cell** despite being the
  least-cited implemented model here. Open access, numbered table, read
  directly, transcribed twice, every cell asserted in a test. Note that is a
  TRANSCRIPTION check, not parity: no third party has implemented ATRIA, so it
  carries `no_independent_reference_implementation`. Best provenance in the
  cell and still not L4.

Influence and provenance are close to inverted here, and the reason is
mechanical: the most-cited scores are old and paywalled, and the open-access
ones are newer and less read.

---

## The atrial-fibrillation cell: four papers, and the ranking inverts

All four answer the same question, should this AF patient be anticoagulated,
and all four have been scored against each other in at least one shared cohort,
so the discrimination figures below are comparable rather than each paper's own
self-report.

| | CHA₂DS₂-VASc | CHADS₂ | **ATRIA** | Lin 2026 |
|---|---|---|---|---|
| Citations | **6,781** | 4,855 | 409 | 2 |
| Citations/year | **398.9** | 194.2 | 31.5 | 2.0 |
| C-statistic (ATRIA cohort) | 0.70 | 0.69 | **0.73** | — |
| AUC (Lin cohorts) | 0.61–0.67 | — | — | **0.88** |
| Complete formula | ✅ | ✅ | ✅ | ⚠️ missing intercept |
| Inputs routine | ✅ | ✅ | ✅ (+ urinalysis, eGFR) | ✅ |
| **Usable here** | ✅ | ✅ | ✅ | ✗ |

**The most-cited paper is the worst-discriminating one.** CHA₂DS₂-VASc is the
single most-cited paper in this entire library, 6,781 citations, more than the
CTT meta-analysis in *The Lancet*, and it discriminates at 0.606 in its own
derivation cohort and 0.70 in ATRIA's. ATRIA beats it on the same patients and
has been read one-sixteenth as much.

The reason is not that ATRIA is worse. It is that CHA₂DS₂-VASc is written into
the guidelines, and a score that decides a drug gets cited every time anyone
writes about that drug. Citation count here measures *institutional adoption*,
not accuracy. This is the same inversion the cervical dossier found, arrived at
from the opposite direction: there the most-cited paper was unusable, here it is
usable but outperformed.

### Which one to use: ATRIA

**ATRIA is the recommended score for stroke risk in atrial fibrillation.** It
is the best model that can be run today, on three independent grounds:

1. **Discrimination.** 0.73 against CHA₂DS₂-VASc's 0.70, head-to-head, both
   scored on the same patients rather than each reporting its own cohort.
2. **Provenance.** Ten values read directly from Table 3 of an open-access
   paper and transcribed twice. (CHA₂DS₂-VASc has since been verified against
   its own Table 2 as well, so this is no longer a point of difference between
   them, both are now primary-sourced.)
3. **Completeness.** Nothing missing, no author to email, shipped and
   parity-checked.

Its only extra cost over CHA₂DS₂-VASc is two routine values: a urinalysis flag
and an eGFR.

**The registry now says this too.** It did not at first: both AF scores were
recorded as `alternative` to GRACE, because a cell allowed one flagship and
GRACE held cvd/prognosis for a different clinical question, mortality after
acute coronary syndrome. That forced the machine-readable field to disagree
with the prose recommendation.

`cvd/prognosis`
now resolves to two questions, each with its own flagship: **GRACE** for ACS
mortality, **ATRIA** for AF stroke, with CHA₂DS₂-VASc the alternative on the
second. A survey of all 36 cells found this is the only one that needed it,
the other four multi-model cells hold genuine alternatives for a single
question. See `reporting.clinical_question`.

**CHA₂DS₂-VASc is kept and stays callable**, and citation count is the reason:
6,781 against 409, a 16× gap, the most-cited paper in the library. Use it when
the answer has to be guideline-concordant, or legible to a reviewer who expects
the familiar score. That is a real requirement and it is why the model stays.
It is not an accuracy argument, on accuracy it loses.

If Lin 2026 stays blocked, this is the resting position and the cell is
complete: **ATRIA as the recommended score, CHA₂DS₂-VASc alongside it for
guideline concordance.**

One correction worth recording, since it is easy to misremember: **ATRIA is
2013, not 2010.** CHA₂DS₂-VASc is 2010 in print (2009 online, which is why
OpenAlex reports 2009). CHADS₂ is 2001. The three AF scores span twelve years,
not one.

### Why ATRIA was chosen for the library

Best available discrimination among models that can actually be run today:

- **0.73 vs 0.70**, head-to-head in ATRIA's own cohort, all three scores on the
  same patients. Not three numbers lifted from three separate papers.
- **Nothing missing.** Table 3 is a complete integer point table; Table 4 gives
  the rate bands. No intercept, no baseline hazard, no author to email.
- **Two extra predictors, both routine**, proteinuria (a urinalysis flag) and
  eGFR<45/ESRD (routine chemistry). Not a biomarker panel.
- **Open access**, CC BY-NC.

It ships as an `alternative`, not the flagship, because CHA₂DS₂-VASc is what
guidelines say and swapping the default would misdescribe practice. Both are
implemented; `flagship_note` on the ATRIA entry says when to pick which.

### Why ABC-stroke was rejected despite better numbers than ATRIA's on paper

ABC-stroke reports 0.68 against CHA₂DS₂-VASc's 0.62, a wider margin than
ATRIA's 0.73 vs 0.70. It was still rejected, for two independent reasons:

1. **Not head-to-head.** Those are derivation-cohort figures. ATRIA's are all
   from one cohort with all three scores computed on the same patients.
   Comparing 0.68-from-one-paper against 0.73-from-another is the error this
   library exists to avoid.
2. **Needs GDF-15, high-sensitivity troponin and NT-proBNP.** Send-out
   biomarker assays. Fails the routine-EHR criterion that makes ATRIA and the
   Lin model attractive for platform deployment in the first place.

### Why Lin 2026 is not in the library, despite being the best model here

AUC 0.88 against CHA₂DS₂-VASc's 0.61–0.62, head-to-head across three cohorts,
the largest margin any candidate has shown. It has an MIT-licensed repository
and a Zenodo archive. And it cannot be run.

**Having the code is not having the model.** The repository holds the training
pipeline, not a fitted artifact: no serialised model file, and the derivation
data (NTUH-iMD) cannot be shared, so the notebooks cannot be re-run to
reproduce the fit. What the code *did* give us is evidence to read constants
out of, a retained output cell prints the nine odds ratios to six decimals, so
every coefficient is recoverable as ln(OR). The intercept is absent because the
notebook fits it and then drops it one character before printing:

```python
'Odds Ratio (OR)': np.exp(model_multi.params[1:]),  # Exclude constant term
```

One number, and the search for it is exhausted: no preprint, no peer-review
file, no earlier git revision, no fuller Zenodo version. Full record in
`registry/models.yaml` under `af_stroke_lr_2026`.

**If that intercept arrives, ATRIA is superseded.** The two are not in
competition; ATRIA is what ships while the better model is blocked.

---

## What would close the remaining gap

In order of cost:

1. **Pull frames from the dashboard demo video** (supplementary MOESM2 of Lin
   2026). Worked examples at two different ages would pin the age scaler and
   finish the deployed model without contacting anyone. This library has
   already recovered constants from a case-level figure once, the intercept of
   Lin's sklearn model (≈ −2.99) came from three such plots.
2. **Email the corresponding author** of Lin 2026 for the intercept of the
   statsmodels fit in notebook 01. One number.
3. **A GARFIELD-AF or external ATRIA validation** that scores ATRIA, CHA₂DS₂-VASc
   and Lin's model on one shared cohort would settle the ordering properly.
   None currently exists. Lin 2026 tested only against CHA₂DS₂-VASc.

---

## How this dossier was built

The method, so it can be repeated for the other eleven diseases. Steps 1–6 are
shared with `docs/diseases/cervical/README.md`; 7 and 8 were added here.

1. **Enumerate every paper the registry touches for the disease**, on all three
   axes and at every status, `implemented`, `catalog`, and `gap`. Rejected
   candidates matter as much as accepted ones.
2. **Resolve each to a DOI, then to OpenAlex** for citation count and journal.
   `scripts/fetch_impact.py --all --json docs/diseases/<disease>/bibliometrics.json`
   does this. It resolves from `source_url` or from an `upstream[].doi`, so a
   paper cited only by a PMC URL comes back empty. ATRIA and Lin 2026 both did
   until a `doi:` was added to their `upstream` entries. Prefer DOI over PMID.
3. **Report citations *and* citations-per-year.** Raw counts are confounded with
   age. CHADS₂ has 4,855 citations to ATRIA's 409, and is 12 years older.
4. **Do not report an impact factor.** Clarivate's JIF is proprietary. The open
   substitute (`2yr_mean_citedness`) is *inconsistently* wrong. CHEST reads
   0.67 because 85,323 indexed "works" include tens of thousands of conference
   abstracts. A metric that is wrong only sometimes is worse than none for
   ranking, so journal standing stays a qualitative column.
5. **Score usability separately from influence, and let them disagree.**
6. **Write down the negative results with their reasons.**
7. **Only compare discrimination figures measured on the same cohort.** Every
   score in the AF cell publishes its own C-statistic against its own
   comparator, and stacking those numbers into one table would have ranked
   ABC-stroke above ATRIA. The ATRIA paper scores all three of ATRIA, CHADS₂ and
   CHA₂DS₂-VASc on one set of patients, and that is the only reason those three
   numbers sit in one column here. Where a paper has not been scored
   head-to-head, its figure goes in a separate row, not the same one.
8. **Check whether "has code" means "has a model".** `open_source: available`
   is not the same as runnable. Ask three questions of any repository: is there
   a serialised fitted artifact; is the training data available; and if neither,
   do the retained notebook outputs or figures contain the constants. Lin 2026
   answers no, no, and *partly*, which is why it is catalogued with a
   `code_status` field saying exactly that, rather than being marked usable.

### The bar a model must clear to enter the library

- a **complete** equation, coefficients *and* the constant that turns them
  into a probability
- inputs this library takes: routine clinical variables, not send-out biomarker
  panels or radiomics features
- external validation, or a development cohort large enough to stand in for it
- a licence permitting the use we intend (see `docs/COMMERCIAL_USE_AUDIT.md`)
- for a model displacing an incumbent: a **head-to-head** comparison against
  that incumbent on shared patients
