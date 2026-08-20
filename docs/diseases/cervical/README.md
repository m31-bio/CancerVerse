# Cervical cancer: paper dossier

Every paper this library has considered for cervical cancer, on all three axes,
with what each one actually gives you and how much the field has read it.

Bibliometrics are in `bibliometrics.json`, fetched from OpenAlex on 2026-08-14
by `scripts/fetch_impact.py`. Regenerate rather than retype.

Status: **3 of 3 axes filled.** Detection, prognosis and response are all
implemented and parity-checked.

---

## The papers

`code` = a runnable artifact exists (repo, package, or a live calculator that
exposes its own fit). `formula` = enough is printed to compute an answer:
coefficients **and** whatever turns them into a number (intercept, or a
baseline survival S₀(t)). Half a formula is marked as half.

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---|---:|---:|:--:|:--:|---|
| **Wu et al — Development of models for cervical cancer screening** ([10.1186/s12916-021-02078-2](https://doi.org/10.1186/s12916-021-02078-2)) | detection | 2021 | BMC Medicine | 17 | 3.4 | ✗ | ✅ **full** | ✅ **implemented** as `cervical_cin_risk`, parity-checked |
| **Cibula et al — The annual recurrence risk model (ARRM)** ([10.1016/j.ejca.2021.09.008](https://doi.org/10.1016/j.ejca.2021.09.008)) | prognosis | 2021 | European Journal of Cancer | 39 | 7.8 | ✅ live | ✅ **full** | ✅ **implemented** as `cibula_arrm`, parity-checked |
| **Moore et al — Prognostic factors for response to cisplatin-based chemotherapy** ([10.1016/j.ygyno.2009.09.006](https://doi.org/10.1016/j.ygyno.2009.09.006)) | response | 2010 | Gynecologic Oncology | **161** | **9.5** | ✗ | ✅ **full** | ✅ **implemented** as `moore_criteria`, parity-checked |
| Tewari et al — prospective validation of the Moore criteria, GOG 240 ([10.1158/1078-0432.CCR-15-1346](https://doi.org/10.1158/1078-0432.CCR-15-1346)) | response | 2015 | Clinical Cancer Research | 75 | 6.8 | ✗ | n/a | Not a new model — cited as `moore_criteria`'s prospective validation |
| Wang et al — A Prognostic Nomogram for Cervical Cancer after Surgery from SEER ([10.7150/jca.26220](https://doi.org/10.7150/jca.26220)) | prognosis | 2018 | Journal of Cancer | **107** | **13.4** | ✗ | ⚠️ **half** | ✗ — no S₀(t) |
| Yoo et al — Nomogram prediction for overall survival ([10.1038/bjc.2012.340](https://doi.org/10.1038/bjc.2012.340)) | prognosis | 2012 | British Journal of Cancer | **100** | 7.1 | 💀 dead | ✗ **none** | ✗ — coefficients never printed |
| Zhang et al — Nomogram models for the prognosis of cervical cancer: a SEER-based study ([10.3389/fonc.2022.961678](https://doi.org/10.3389/fonc.2022.961678)) | prognosis | 2022 | Frontiers in Oncology | 25 | 6.2 | ✗ | ⚠️ **half** | ✗ — no S₀(t) |
| Development and validation of prognostic nomographs, SEER Asian population ([10.1038/s41598-024-57609-7](https://doi.org/10.1038/s41598-024-57609-7)) | prognosis | 2024 | Scientific Reports | 7 | 3.5 | ✗ | ⚠️ **half** | ✗ — no S₀(t) |
| ASCCP risk-based management | detection | — | consensus tables | — | — | ✗ | ✗ **none** | ✗ — a lookup table, not an equation |
| (radiomics / deep-learning nomograms) | response | various | various | — | — | ✗ | n/a | ✗ — need imaging features this library does not take |

💀 = Yoo's calculator at `ccc.ac.at/gcu` is dead; it now redirects to the
cancer-centre homepage. Six models in this library were verified by reading a
live calculator. That route expires without notice, and this is the warning.

---

## How the prognosis cell was closed

It was open because four candidates all failed the same way, and it closed
because a fifth paper failed differently.

Yoo 2012, Wang 2018, Zhang 2022 and the 2024 SEER Asian-population model are
all `rms::cph` + `nomogram()` fits, and **none publishes a numeric baseline
survival S₀(t)**. Three of them print complete multivariable hazard-ratio
tables with reference categories, genuinely more than Yoo gives, and it still
is not enough, because

    S(t) = S₀(t) ^ exp(Xβ)

needs both halves. With β alone you can rank patients and cannot state a
probability, and the probability is the output. The points-to-probability step
exists only as a drawn axis inside a figure. That is a property of the
**tooling**: `nomogram()` renders that axis as a graphic and never requires the
author to print S₀(t) anywhere. The gap was structural and shared across the
literature, which is why a fifth nomogram paper would not have helped.

**ARRM is not a nomogram, so it never needs S₀(t).** It converts its βs into an
integer 0–100 points score, bands the score into five groups, and reports each
band's *observed* Kaplan-Meier outcome. There is no baseline hazard anywhere in
it. The lesson generalises to the other eleven diseases: when every candidate
for a cell fails identically, the thing to search for is a model of a different
**form**, not a better model of the same form.

### What it cost

The points schedule was the easy half. Table 2 prints fourteen levels with a β
and an integer points value each. Two things had to be recovered:

1. **The β-to-points divisor, which the paper never states.** Methods says the
   score was "weighted to the maximum sum of 100 points". Taken literally that
   is 100 ÷ (sum of the largest β in each predictor) = 100/5.231 = 19.1168, and
   all thirteen published point values reproduce under `round(β × 19.1168)`
   with no exceptions. Same technique this library used for the Kunzmann
   divisor.
2. **The band → outcome grid, which exists only as Fig. 3.** Twelve of its
   numbers appear in prose and the rest are pixels. The ESGO calculator ships
   the entire 4,343-row derivation cohort to the browser, so the grid was
   re-derived by running the estimator over that cohort. All twelve printed
   values reproduce, ten of them exactly; the two that differ are 0.1 low, in
   different bands and different quantities, which is rounding rather than
   bias. Six counts the paper states about its own cohort reproduce exactly,
   which is what ties the deployment to the publication.

⚠️ **The licence question this opened is not settled.** The points schedule is a
coefficient table and coefficients are facts. The outcome grid is derived from
patient-level data the calculator ships, which is a different question, see
`docs/COMMERCIAL_USE_AUDIT.md`. Note also that the article is **not** open
access: Europe PMC reports `isOpenAccess: N` with no licence, and OpenAlex
reports green OA, meaning readable via repository deposit with no reuse grant.

---

## Which paper is "best", and why the answer changes with the question

The prognosis candidates are close on influence and far apart on usability:

| | Wang 2018 | Yoo 2012 | **Cibula 2021 (implemented)** |
|---|---|---|---|
| Citations | **107** | 100 | 39 |
| Citations/year | **13.4** | 7.1 | 7.8 |
| Journal | Journal of Cancer | British Journal of Cancer | **European Journal of Cancer** |
| Coefficients printed | ✅ all, with reference levels | ✗ univariate only | ✅ all, with reference levels |
| Can produce an answer | ✗ needs S₀(t) | ✗ | ✅ points → band → observed outcome |
| Society endorsement | ✗ | ✗ | ✅ ESGO |
| **Usable here** | **no** | **no** | **yes** |

**Wang 2018 still wins on raw citations** and is still not implementable.
Cibula wins on rate among the three, wins outright on journal and endorsement,
and above all is the only one that can return a number. The same inversion
holds in the detection cell, where **Wu 2021 is the least-cited candidate and
is the one in the library**, because it is the only one that published a
complete equation.

That is the single most useful thing in this dossier: for a reimplementation
library, *what a paper printed* beats *how many people cited it*, every time.

---

## How the response cell was closed

It was open for a search reason, not an evidence reason: every candidate found
for "response to treatment" was a radiomics or deep-learning nomogram for
response to neoadjuvant chemoradiation in newly diagnosed disease, and that
class genuinely needs imaging features this library does not take. That
finding was correct and stays correct.

The escape was to change the **endpoint**, the same move that closed
prognosis. **Moore et al 2010** (Gynecologic Oncology, **161 citations, 9.5/yr,
the most-cited paper in this dossier by a wide margin**) answers a different
question: response to cisplatin-based chemotherapy in *advanced, recurrent, or
metastatic* disease. It counts five binary risk factors, race, performance
status, disease site, prior radiosensitizer, recurrence timing, bands the
count 0–1 / 2–3 / 4–5, and publishes response rate and median PFS/OS for every
band in both a development cohort (GOG 110/169/179, n=428) and an external one
(GOG 149). It was then **prospectively validated** as a tertiary endpoint of
the phase III GOG 240 trial (Tewari et al 2015), "the first prospectively
validated scoring system in cervical cancer".

### The model is a count, not a regression, and that is what the paper published

Table 3 gives five adjusted odds ratios (0.49 to 0.61). None of them enters the
implementation's arithmetic, because the paper says outright that it declined
to use them: *"Given that the five risk factors identified conferred
comparable weights and there were no interactions across them, a simple
prognostic index was developed by combining the number of risk factors."* The
sweep in `scripts/feature_importance.py` confirms this in code rather than
leaving it as a claim: flipping any one of the five factors moves the count by
exactly 1, all five swings equal, the only model in this library where that
is true by the source's own design rather than by coincidence.

### Two inputs required a judgement call; one of them is unresolved

- **Performance status and the recurrence interval** are accepted as their raw
  values (GOG/ECOG 0–4; months from diagnosis to first recurrence) and
  dichotomised internally at the paper's own cut-points, the same way
  `cibula_arrm` bands a continuous tumour diameter rather than asking the
  caller to pre-band it.
- **Disease site is the one genuine gap.** Table 1/2 record three levels,
  pelvic, distant, combined (13.1% of the development cohort), but Table 3
  tests a binary "Pelvic vs. Non-pelvic" and the paper never states in prose
  which side "combined" falls on. The implementation reads the label literally
  (combined counts as non-pelvic) and flags every case where that inference is
  used. A different, equally defensible reading would move 56 patients across
  the factor. **Not settled, flagged in `notes` on every call, not silently
  resolved.**

### ⚠️ The first risk factor is race

Table 3 tests "Race: Black vs. Non-black" (OR 0.49, the strongest point
estimate of the five, though its CI overlaps every other factor's). The
paper's own Results and Discussion instead say "African-American" throughout,
the source itself is not consistent about which word names the variable, and the Discussion addresses the finding directly, weighing access-to-care against
biological hypotheses without resolving between them.

This is stated explicitly in `scope_note`, not left for a reader to discover,
on the same basis this library already established for `pbcg_extended`: a race
coefficient the authors report is a fact about their cohort, not a claim about
biology, and `pbcg_extended`'s own African-ancestry term is the standing
reminder why, it *flips sign* between two of that model's own sub-models (OR
0.68, p=0.08 in the full model vs OR 1.26, p=0.0005 in the six-factor one).

### Neither cell needed a new search technique twice

Prognosis closed by finding a model of a different **form** (not a nomogram).
Response closed by finding a model of a different **endpoint** (not response to
primary treatment). Both are the same lesson from two directions: when every
candidate for a cell fails identically, re-read what specifically it was
asked to predict, or how it was asked to produce an answer, before concluding
the literature has nothing.

---

## How this dossier was built

The method, so it can be repeated for the other eleven diseases:

1. **Enumerate every paper the registry touches for the disease**, on all three
   axes and at every status, `implemented`, `catalog`, and `gap`. Rejected
   candidates matter as much as accepted ones; a `gap` entry's `tier_note` and
   `blocker` are where the previous search's findings live.
2. **Resolve each to a DOI, then to OpenAlex** for citation count and journal.
   `scripts/fetch_impact.py` does this. Prefer DOI over PMID: PMID lookup is
   what put a linguistics paper in this library's registry under the
   dutasteride model. Get author lists from Crossref rather than typing them,
   a hand-typed list for the ARRM entry invented eight co-authors who are not
   on the paper.
3. **Report citations *and* citations-per-year.** Raw counts are confounded
   with age, a 1989 paper has had thirty-seven years to accumulate them and a
   2024 paper two. Neither number alone ranks anything honestly.
4. **Do not report an impact factor.** Clarivate's JIF is proprietary and
   cannot be read. The open substitute (`2yr_mean_citedness`) is *inconsistently*
   wrong: journals that deposit conference abstracts have their means diluted to
   nonsense. Journal of Clinical Oncology reads 1.65 against a real JIF near 45,
   because 174,155 indexed "works" include tens of thousands of ASCO abstracts.
   Journals that deposit few abstracts come out plausible. A metric that is
   wrong only sometimes is worse for ranking than no metric, so journal standing
   is left as a qualitative column here.
5. **Score usability separately from influence, and let them disagree.** The
   two questions are "who read this" and "what did it print". For a
   reimplementation library only the second decides whether a model can ship.
6. **Write down the negative results with their reasons.** "No model exists" and
   "four models exist and all four omit the same constant" are different
   findings that lead to different next actions, and only the second one tells
   you what to ask for, here, a model of a different form.
7. **Check the licence separately from the access.** Being readable on PMC is
   not a licence. ARRM is on PMC and is not open access; the determination that
   let it be implemented is about coefficients being facts, and it is written
   down rather than remembered.

### The bar a model must clear to enter the library

Applied to every candidate above, and the reason most were rejected:

- a **complete** equation, coefficients *and* whatever turns them into an
  answer, whether that is an intercept, a baseline survival, or a published
  band-to-outcome table
- inputs this library takes: routine clinical variables, not imaging-derived
  radiomics features
- external validation, or a development cohort large enough to stand in for it
- a licence permitting the use we intend (see `docs/COMMERCIAL_USE_AUDIT.md`)
