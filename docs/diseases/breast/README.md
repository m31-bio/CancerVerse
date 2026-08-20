# Breast cancer: paper dossier

Seven entries, three shipped. This is the disease where the library **replaced
its most-cited model:** BCRAT, the Gail model, 3,395 citations, the highest
count anywhere in this project, and where the genuinely hard part turned out
to be **working out which version of the replacement is which**.

Bibliometrics: `bibliometrics.json`, resolved via OpenAlex 2026-08-17.

---

## The papers

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---:|---:|---:|:--:|:--:|---|
| **Gail et al — BCRAT** ([10.1093/jnci/81.24.1879](https://doi.org/10.1093/jnci/81.24.1879)) | detection | 1989 | JNCI | **3,395** | 91.8 | ✅ CRAN `BCRA` (GPL) | ✅ tables + integration | ✗ **catalog** — `superseded_by: bcsc_v2` |
| **Tice et al — BCSC density model** ([10.7326/0003-4819-148-5-200803040-00004](https://doi.org/10.7326/0003-4819-148-5-200803040-00004)) | detection | 2008 | Ann Intern Med | 550 | 30.6 | ✗ | ✅ **Appendix Figure** | ✅ **flagship** as `bcsc_v2` |
| **Candido dos Reis et al — PREDICT v2.2** ([10.1186/s13058-017-0852-3](https://doi.org/10.1186/s13058-017-0852-3)) | prognosis **and** response | 2017 | Breast Cancer Res | 266 | 29.6 | ✅ **MIT** (`WintonCentre/predictv30r`) | ✗ **not in the paper** | ✅ **flagship** of both cells |
| **Gard et al — BCSC v3** ([10.1200/JCO.22.02470](https://doi.org/10.1200/JCO.22.02470)) | detection | 2024 | J Clin Oncol | 26 | 8.7 | ⚠️ gated | ⚠️ paywalled | ✗ **catalog** — licence question open |
| Tice et al — BCSC v2.0 (benign breast disease) | detection | 2015 | J Clin Oncol | — | — | ⚠️ gated | ⚠️ | ✗ **catalog** — added 2026-08-17 |
| MSK / adjuvant breast tools | prognosis | — | portal | — | — | ✗ web only | ✗ | ✗ **catalog** |

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Read by us? |
|---|---:|---|---|
| `bcsc_v2` | 550 | **Appendix Figure**, "The Breast Cancer Surveillance Consortium breast density model algorithm", NIH Public Access manuscript pages 9–10 — the I(x,r) and D(x,r) polynomials, the two hazard tables, and the two multipliers stated in its closing prose. | ✅ **all 57 constants re-read and checked 2026-08-18** |
| `predict_breast` / `_response` | 266 | **Not the paper.** The MIT-licensed reference implementation `WintonCentre/predictv30r`, `R/benefits22.R`, and specifically the **unexported** function. | ✅ |

`predict_breast` is one of only two models in the library taken from a
reference implementation rather than a publication, and the only one where the
implementation is **MIT-licensed**, so unlike the riskcalc family, nothing here
has to be withheld from the company repository.

---

## Detection: replacing the most-cited model in the project

**BCRAT is not wrong. It is unrunnable here, and it never discriminated well.**

| | BCRAT (1989) | **BCSC v1.0 / Tice 2008** |
|---|---|---|
| Citations | **3,395** (91.8/yr) | 550 (30.6/yr) |
| Discrimination | **concordance 0.58** (0.56–0.60) | **c-statistic 0.66** (0.65–0.67) |
| Calibration | **expected/observed 0.94** (0.89–0.99) | — |
| Needs | age at menarche, **age at first live birth** | **BI-RADS breast density** |
| Runs on our data | ❌ `not_ehr` | ✅ `routine` |

The registry states the reason for the swap without hedging:

> the replacement **is not about age**: BCRAT needs age at menarche and age at
> first live birth, neither of which the platform holds, while BCSC asks for
> BI-RADS breast density, which a screening centre already records as a
> structured field.

**BCRAT's 0.58 deserves its own sentence.** That is barely above chance for
ranking individuals, and the model is nonetheless a landmark, because
*calibration* is what it was built for and what it does: expected over observed
0.94 in the Nurses' Health Study. A model can be near-useless for deciding who
is at higher risk and still correctly state how many cancers a population will
have. BCRAT is the clearest case in this library of those two properties coming
apart, and reporting only one of its numbers would misrepresent it either way.

**One simplification in our BCRAT is deliberate and documented:** six published
Asian-American subgroups are collapsed to a single `asian` stratum using Chinese
SEER rates as a proxy. It is recorded in the module and repeated here because a
reader must not use that stratum for a specific Asian-American subgroup.

### The version-labelling error, found 2026-08-17

The BCSC calculator has **three** versions. This registry carried **two of them,
under the wrong names**, and nobody noticed until the labels themselves were
checked:

| Version | Paper | Adds | Status here |
|---|---|---|---|
| **v1.0** | Tice 2008, *Ann Intern Med* | the density model, 5-year risk | ✅ **implemented** as `bcsc_v2` |
| **v2.0** | Tice 2015, *J Clin Oncol* | benign breast disease classification, 10-year horizon | ✗ catalog as `bcsc_v2_bbd_2015` — **added today** |
| **v3** | Gard 2024, *J Clin Oncol* | BMI, family history, age at first live birth | ✗ catalog as `bcsc` |

The implemented model's registry id is `bcsc_v2` and it is the calculator's
**version 1.0**. That is now recorded rather than corrected, because the id
appears in test names, fixtures and the parameters registry, but anyone reading
"v2" should read "Tice 2008, the density model".

**This is what the dossier method is for.** No test could have caught it: every
model was internally consistent, correctly cited, and correctly implemented.
What was wrong was the *map*, which paper corresponds to which product
version, and that only becomes visible when the papers are enumerated side by
side.

### v3 is an open licence question, not an access problem

The 2026-08-07 password request to the Statistical Coordinating Center is
recorded as **the wrong channel**. The blocker text says the access problem is
resolved and the **licence question is still open**, which is a different and
more careful statement than "we are waiting for a reply".

Worth noting the direction, because it is counterintuitive: **v3 reports
AUC 0.646, lower than the 0.665 of the version it extends.** Recency is not the
reason to prefer it. The reason is that v3 was developed on 1,455,493 women
across six BCSC registries with 30,266 invasive cancers, 2000–2017, and that
it has **no independent external validation**, only five-fold cross-validation,
which the authors list as their first limitation.

---

## Prognosis and response: one model, two cells, and an unexported function

`predict_breast` and `predict_breast_response` are PREDICT Breast v2.2, handled
by **re-export** rather than duplication, the same pattern as LIPI in lung.

The distinction is real: the prognosis cell asks what happens to this patient,
the response cell asks what adjuvant treatment *adds*. PREDICT answers the
second by evaluating the first twice, with and without the treatment term, so
there is no separate published equation for benefit, and none needed.

**Discrimination**, external validation of v2: AUC **0.752** all cases,
**0.760** ER-positive, **0.696** ER-negative.

Two implementation details recorded because they are the kind that get
"corrected" by a later reader:

1. **Radiotherapy terms are present but gated off** in the reference
   (`r.enabled = 0`), and we mirror that exactly rather than enabling a pathway
   the reference disables.
2. The source is the **unexported** function in `R/benefits22.R`. The exported
   one is a different version.

v3.x is not implemented.

---

## What this disease shows that the others do not

| Axis | Flagship | Cites | /yr | Discrimination | Runs on our data |
|---|---|---:|---:|---|---|
| detection | BCSC v1.0 (Tice 2008) | 550 | 30.6 | c 0.66 | ✅ routine |
| detection *(retired)* | BCRAT | **3,395** | 91.8 | **c 0.58**, calibration 0.94 | ❌ `not_ehr` |
| prognosis | PREDICT v2.2 | 266 | 29.6 | AUC 0.752 | specialty |
| response | PREDICT v2.2 *(re-export)* | 266 | 29.6 | — | specialty |

Five diseases now, five ways for standing and usability to come apart:

- **prostate.** The best-read paper's **licence** forbids the use
- **liver.** The best-read paper **answers a different question**
- **ovarian.** The *least*-read paper holds a cell and **disagrees with its own
  figure**
- **lung.** The best-read paper's **inputs do not exist in a health record**
- **breast.** The best-read paper in the **entire project** is retained as a
  catalog entry because its inputs are unavailable *and* it ranks individuals
  barely better than chance

Breast adds a sixth failure mode that is not about any single paper: **the
version map**. Three papers, one product, three version numbers, and a registry
that had two of them mislabelled. Citation counts, licences and parity checks
are all properties of individual papers. Nothing in this project's tooling looks
at the *relationships between* papers, and that is exactly where this error
lived.

---

## Open items

1. **`bcsc_v2` is `parity_status: not_checked`, `repro_tier: B`**, and that is
   now a precise statement rather than a vague one. On 2026-08-18 all **57**
   constants were re-read from the Appendix Figure and every one agrees to the
   last printed digit, so the transcription is checked. What is still missing is
   a *second implementation*: the BCSC's own SAS macro runs this same algorithm
   and is password-gated, so nobody else's code has produced our numbers. Those
   are different claims and the registry keeps them apart, `nomogram_check:
   agrees` for the first, `parity_blocker: no_independent_reference_implementation`
   for the second.
2. **v2.0 (Tice 2015) needs the SAS macro** behind
   `BC5yearRisk_V2/app2/DownloadRequest.aspx`, verified 2026-08-17 that the
   form still exists and still gates the software. It would upgrade the
   implemented model from a binary "ever had a biopsy" input to a full
   benign-breast-disease classification, and add a ten-year horizon.
3. **v3's licence question is open** and is not the same as its access
   question. Someone should decide whether a gated SAS macro with a copyright
   notice and no open-source licence can be read for coefficients under the
   same reasoning used for the noncommercial article sources.
4. **The `bcsc_v2` id means v1.0.** Either rename with a migration, or leave it
   and rely on this dossier. The current state is documented but confusing, and
   documented-but-confusing has a short half-life.

---

## How this dossier was built

The method is the eight steps in `docs/diseases/cvd/README.md`. Three did the
work here:

- **Step 1. Enumerate every paper the registry touches, at every status.**
  This is the step that found the version-labelling error. Reading any one entry
  would not have.
- **Step 5. Score usability separately from influence.** BCRAT leads the
  entire project on citations and is retired from active use.
- **Step 6. Write down the negative results with their reasons.** BCRAT's
  concordance of 0.58 is recorded next to its calibration of 0.94, because
  either number alone is a misrepresentation.
