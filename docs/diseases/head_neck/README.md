# Head and neck cancer: paper dossier

Every paper this library has considered for head and neck cancer, on all three
axes, with what each one actually gives you and how much the field has read it.

Bibliometrics are in `bibliometrics.json`, fetched from OpenAlex on 2026-08-17
by `scripts/fetch_impact.py`. Regenerate rather than retype.

Status: **2 of 3 axes filled**, as of 2026-08-17. Detection was a gap for the
whole life of the project until that day. Response is still open and the reason
is unusually clear-cut, see below.

This disease has the widest citation spread of any cell in the library: its two
flagships are 6,581 citations apart.

---

## The papers

`code` = a runnable artifact exists (repo, package, or a live calculator that
exposes its own fit). `formula` = enough is printed to compute an answer:
coefficients **and** whatever turns them into a number.

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---|---:|---:|:--:|:--:|---|
| **Ang et al — RTOG 0129 RPA** ([10.1056/NEJMoa0912217](https://doi.org/10.1056/NEJMoa0912217)) | prognosis | 2010 | **NEJM** | **6,581** | **411.3** | ✗ | ✅ **full** (a 3-branch tree) | ✅ **flagship** as `ang2010_rpa` |
| **McCarthy et al — UK Biobank HNC risk** ([10.3892/ijo.2020.5123](https://doi.org/10.3892/ijo.2020.5123)) | detection | 2020 | Int J Oncol | **10** | **1.7** | ✗ | ✅ **full** — ORs *and* intercept | ✅ **flagship** as `ukb_hnc`, added 2026-08-17 |
| INHANCE risk models ([10.1093/aje/kwz259](https://doi.org/10.1093/aje/kwz259)) | detection | 2019 | Am J Epidemiol | 28 | 3.5 | ✗ | ⚠️ **unreachable** | ✗ — Web Tables 4–5 cannot be obtained; also needs SEER rates |
| Smith 2024 (Glasgow) | detection | 2024 | — | — | — | ✗ | ⚠️ **half** | ✗ — no intercept; author contact drafted |
| Fakhry et al — RPA external validation ([10.1002/cncr.32025](https://doi.org/10.1002/cncr.32025)) | prognosis | 2019 | Cancer | — | — | ✗ | n/a | used to **resolve two ambiguities** in Ang's wording |
| MRI radiogenomics (PubMed 37985290) | response | 2024 | Acad Radiol | — | — | ✗ | n/a | ✗ — radiomics + transcriptomics |
| Serum NMR metabolomics (PubMed 39062797) | response | 2024 | Int J Mol Sci | — | — | ✗ | n/a | ✗ — research assay |
| Ex vivo functional assay (PubMed 36672427) | response | 2023 | Cancers | — | — | ✗ | n/a | ✗ — needs live tissue |
| Hypopharyngeal induction-chemo nomogram | response | 2020 | Front Oncol | — | — | ✗ | ✅ full | ✗ — 3-fold CV, one subsite, one centre |
| TNM staging | prognosis | — | — | — | — | ✗ | ✅ full | ✗ **catalog** — a staging system, not a model |

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Read by us? |
|---|---:|---|---|
| `ang2010_rpa` | **6,581** | **Results section, verbatim prose** — the decision tree is a sentence, not a table. 3-year OS and hazard ratios extracted from the same paper at implementation time. | ✅ from PMC2943767 |
| `ukb_hnc` | 10 | **Table III** — eight odds ratios in the body, and **the intercept in the caption**. | ✅ read 2026-08-17 from the article |

Both are `no_independent_reference_implementation`: their constants are
transcribed from a paper and checked against it, and no third party has
implemented either, so there is nothing to run them against. That is a weaker
claim than L4 parity and both are labelled as such rather than as "checked".

---

## Detection: closed on 2026-08-17, and the model is weak

This cell was a gap for the whole life of the project. Three candidates were
examined in the end and only the third could be implemented:

| | INHANCE (2019) | Smith (2024) | **UK Biobank (2020)** |
|---|---|---|---|
| Citations | 28 | — | **10** |
| Coefficients | Web Tables 4–5 | printed | ✅ Table III |
| **Intercept** | in the same unreachable zip | ✗ **missing** | ✅ **in the caption** |
| Other blocker | needs vendored SEER incidence rates | — | — |
| **In the library** | ✗ | ✗ | **flagship** |

**The cell was closed by a table caption.** Every model needs a constant to turn
coefficients into a probability, and this one printed it in the caption of
Table III rather than in a row:

> "Model Intercept Coefficient −9.54 (95% confidence interval, −11.2 − −7.88;
> P<0.001)."

Two earlier passes over this literature never saw the paper; a third saw it and
could not open it. The intercept being in a caption is not a small detail, it is
the difference between a gap and a flagship, and it is exactly what
`af_stroke_lr_2026` and Smith 2024 are both missing.

### Say plainly that it is not a good model

Flagship by default, not by contest, it is the only implementable candidate
found. Weigh it accordingly:

- **C-statistic 0.64, and the "external" validation is not external.** It is
  "the North West Cohort from the UK Biobank", a geographic subset of the same
  dataset. Development gives 0.69. The honest label is internal-geographic, and
  this is the weakest validation design of any flagship in the library.
- **No bootstrapping**, justified in the paper by cohort size.
- **Three of eight predictors have no US source.** The Townsend Deprivation
  Index is a UK area-level measure with no equivalent, the same problem
  recorded for PREVENT's SDI decile. Exercise days per week and five-a-day
  intake are questionnaire items. That is why `ehr_availability` is `not_ehr`.
- **Laryngeal cancer is excluded from the outcome** (ICD-10 C32), because
  screening for it "requires different expertise". A caller wanting all head and
  neck sites is asking a different question.

For scale: `crc_pro` ships at 0.681/0.679, so 0.64–0.69 is inside the band this
project already accepts for a lifestyle-based detection model. That is the
argument for keeping it, and it is not a strong one.

### Two coefficients that look like bugs

Both are in the paper and both are asserted in the test suite, so a future
"correction" fails loudly:

- **BMI is protective** (OR 0.96 per unit). Higher BMI, lower risk, in this
  cohort.
- **Alcohol is non-monotonic and current drinking is not significant.** Previous
  drinkers 3.26 (1.32–8.04); current drinkers 1.42 with a CI spanning 1
  (0.62–3.21). The sick-quitter pattern, people who stopped because they were
  already unwell, so the largest alcohol effect attaches to the category that
  has stopped. Deprivation is non-monotonic too: Q4 (1.81) above Q5 (1.66).

---

## Prognosis: 6,581 citations, and the equation is a sentence

**Ang 2010 is the most-cited paper in this dossier by a factor of 658**, and one
of the most-cited in the whole library. It is the paper that established HPV
status as an independent prognostic factor in oropharyngeal cancer, and the
three risk groups it defines are what the de-escalation trials are built on.

Separation is wide and the confidence intervals do not overlap:

| RPA group | 3-year OS | 95% CI | HR vs low |
|---|---:|---|---:|
| Low | **93.0%** | 88.3–97.7 | 1 |
| Intermediate | 70.8% | 60.7–80.8 | 3.54 |
| High | **46.2%** | 34.7–57.7 | 7.16 |

**No c-index is reported and that is correct**, it returns one of three groups,
not a probability, so there is nothing to calibrate and a concordance statistic
would summarise three distinct values. Same reasoning as `albi`, `lipi` and
`abc_method`.

### The equation is prose, and it is ambiguous

There is no table. The decision tree exists as one sentence in the Results:

> "Patients with HPV-positive tumors were considered to be at low risk, with the
> exception of smokers with a high nodal stage (i.e., N2b to N3), who were
> considered to be at intermediate risk; patients with HPV-negative tumors were
> considered to be at high risk, with the exception of nonsmokers with tumors of
> stage T2 or T3, who were considered to be at intermediate risk."

That sentence leaves two things unstated, and the module ships both readings
behind a `definition` argument:

1. **What "nonsmokers" means.** The HPV-positive branch says ">10 pack-years";
   the HPV-negative branch says "nonsmokers", undefined.
2. **Where T1 falls.** Only "T2 or T3" is named; T1 is silent.

Fakhry et al. (Cancer 2019, PMC6594017) operationalises both branches as the
same ≤10 pack-year split and the HPV-negative exception as "<T4", which includes
T1. That external validation is what settles it, an unusual and useful case
where the ambiguity in a hugely-cited paper is resolved not by asking the
authors but by reading how someone else reproduced it.

---

## Response: still open, and the reason is a property of the field

Re-searched 2026-08-17. Nothing better than the previously recorded candidate,
and the pattern across the new candidates is consistent enough to state as a
finding rather than a coincidence:

| Candidate | Why rejected |
|---|---|
| MRI radiogenomics (Acad Radiol 2024) | radiomics ML classifiers **plus** transcriptomics |
| Serum NMR metabolomics (Int J Mol Sci 2024) | research assay |
| Ex vivo functional assay (Cancers 2023) | requires live tumour tissue and a lab protocol |
| Hypopharyngeal induction-chemo nomogram (Front Oncol 2020) | AUC 0.860, but 3-fold CV on one cohort, one subsite, one centre |

**Head and neck treatment-response prediction is being pursued almost entirely
through imaging features, omics and tissue assays.** A closed-form model on
routine clinical variables is not what the field is building, so repeating this
search is unlikely to help.

### The one untried route was tried on 2026-08-19, and it failed

This dossier used to end here, saying the **endpoint move that closed the
cervical response cell**, asking about response in the advanced or recurrent
setting rather than to primary treatment, was the one route not yet tried.
It has now been tried. It does not work, and that is worth more than another
sweep of the primary-treatment literature.

**First, the incumbent is still unvalidated, checked, not assumed.** Every
article citing the hypopharyngeal nomogram was pulled: **six citations, none an
external validation.** Distant-metastasis prediction, an AI scoping review,
radiomics for recurrence, the MRI radiogenomics paper already rejected above,
CT radiomics for PFS, a matched-pair survival analysis. Criterion 3 fails today
for the same reason it failed in August 2026, and now that is a finding.

**Second, the advanced/recurrent literature answers a different question.**

| Candidate | Shape | Why it fails |
|---|---|---|
| Inflammatory-marker index, nivolumab in R/M HNSCC (*Oncology* 2025, PMID 39566473) | prints a closed form on routine bloods — `WBC + 2×lymph% + 12×monocytes + 27×albumin` | it estimates **overall survival**, not response; n=61, one centre; part of the analysis needs flow cytometry |
| Multicentre R/M HNSCC immunotherapy, China (*Front Immunol* 2026, PMID 41716388) | n=105, three hospitals | endpoints are **OS and PFS**; its strongest predictor is PD-L1 CPS, an immunohistochemistry result |

The R/M literature answers with **survival endpoints and PD-L1**, not with
validated response models on routine variables. The move that rescued cervical
does not rescue this cell.

**Third, a new best-on-inputs candidate, and the closest anything has come.**
*Nomogram Prediction of Response to Neoadjuvant Chemotherapy Plus Pembrolizumab
in Locally Advanced Hypopharyngeal SCC*, [J Otolaryngol Head Neck Surg
2025](https://doi.org/10.1177/19160216251318255) (PMID 39921555, PMC11807280,
CC BY-NC). Endpoint is **ORR by RECIST 1.1**, the right endpoint. Inputs are
pretreatment **lymphocytes, red blood cells and basophils**: a plain CBC,
cleaner than any candidate on file including the incumbent. Reported C-index
and AUC both **0.925**.

It fails criterion 3, single institution, n=129, no external validation, and
the nomogram was built on the **47** who received pembrolizumab rather than on
all 129. But two things make the headline number worse than the missing
validation:

- The C-index interval is **0.848–1.002**. An upper bound above 1 is impossible
  for a concordance statistic, so the interval came from an unbounded normal
  approximation, and 0.925 from three LASSO-selected predictors on ~47 patients
  should be read as optimistic, not as a result.
- The paper reports fitting a **Cox** model to predict **ORR**. Cox is for
  time-to-event; ORR is binary. Either the reporting is loose or the model is
  mismatched to its own endpoint.

Same posture as ovarian's platinum-resistance nomogram, whose C-index of 0.975
this project already records as a reason for suspicion rather than enthusiasm.

**Fourth, the field says it about itself.** *Eur Radiol Exp* 2026 (PMC12932746)
opens: *"There is no satisfactory model for predicting the therapeutic response
to chemotherapy of nasopharyngeal carcinoma."* That paper's own answer is
synthetic-MRI histogram features plus tumour-stroma ratio, which fails criterion
2 here, but the sentence is a straight corroboration from inside the specialty.

**What is left.** Two routes, neither reachable by searching harder:

1. **Someone externally validates PMC7761343 or PMID 39921555.** Both are
   plausible and both are outside our control, and either would close the cell
   immediately, because the inputs already pass.
2. **The imaging criterion is widened.** Put to the team on 2026-08-18 and
   declined.

There is no third route. This cell is open by decision and by the state of the
literature, not by an unfinished search.

---

## What this disease shows that the others do not

Prostate showed influence and usability coming apart because of a **licence**.
Cervical showed it because the best-read paper **omitted a constant**. Head and
neck shows a third thing: **the two flagships of one disease can be 658×
apart in readership and both be the right choice.**

| | `ang2010_rpa` | `ukb_hnc` |
|---|---:|---:|
| Citations | 6,581 | 10 |
| Citations/year | 411.3 | 1.7 |
| Why it is the flagship | it defined the field | it was the only one with an intercept |

Neither was chosen on citations. The first would have won that contest anyway;
the second would have lost it to a paper this library cannot run.

---

## Open items

1. **Response is the only remaining gap.** Try the advanced/recurrent endpoint
   before concluding the cell cannot be filled.
2. **`ukb_hnc` needs a Townsend decision** before it can be scored on US data.
   The target platform's nearest analogue to an area-level deprivation index is a
   differently-scaled Vizient vulnerability index, which would mean refitting
   that term rather than substituting it.
3. **INHANCE stays reachable in principle.** Web Tables 4–5 from the journal or
   the authors, then a decision about vendoring SEER incidence rates, that    dependency keeps it BCRAT-sized.

---

## How this dossier was built

The method is shared with `docs/diseases/cervical/`, `cvd/` and `prostate/`; see
the CVD dossier for the full eight steps. Two did the work here:

- **Step 4. Do not report an impact factor.** Ang 2010 is in NEJM and the UK
  Biobank model is in a mid-tier oncology journal. Journal standing would have
  said everything about which paper is famous and nothing about which one this
  library could implement, and the answer to the second question was the
  mid-tier journal, on a technicality about where a constant was printed.
- **Step 8. Check whether "has code" means "has a model".** Neither of these
  has code. Both are implementable anyway, because both printed enough. Code and
  implementability are independent, and this cell is the cleanest example of it
  in the library.
