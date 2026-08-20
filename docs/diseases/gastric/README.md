# Gastric cancer: paper dossier

Six entries, three shipped, one per axis. This is the disease where **"the
paper does not print the equation" happened three separate times and got three
different answers**, recovered from a vendor, replaced by stratification, and
avoided by choosing on computability. Nothing else in the library shows all
three side by side.

Bibliometrics: `bibliometrics.json`, resolved via OpenAlex 2026-08-17.

---

## The papers

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---:|---:|---:|:--:|:--:|---|
| **Kattan et al — MSK gastric nomogram** ([10.1200/JCO.2003.01.626](https://doi.org/10.1200/JCO.2003.01.626)) | prognosis | 2003 | J Clin Oncol | **409** | 17.8 | ⚠️ riskcalc.org only | ✗ **nomogram figure only** | ✅ **flagship** as `msk_gastric` — **agrees with its own figure**, see below |
| **Ohata et al — ABC method** ([10.1136/gut.2004.058552](https://doi.org/10.1136/gut.2004.058552)) | detection | 2005 | Gut | 405 | **19.3** | ✗ | ✅ **Methods, both definitions** | ✅ **flagship** as `abc_method` |
| **Xu et al — TRG risk score** ([10.3389/fonc.2021.641135](https://doi.org/10.3389/fonc.2021.641135)) | response | 2021 | Front Oncol | 16 | 3.2 | ✗ | ✅ **Table 4** | ✅ **flagship** as `xu_gastric_trg_score` |
| MSK postoperative DSS nomogram (portal) | prognosis | — | portal | — | — | ✗ web only | ✗ | ✗ **catalog** — superseded, kept as a record |
| TNM / AJCC stage grouping | prognosis | — | guideline | — | — | ✗ | ✗ **staging tables, not an equation** | ✗ **catalog**, `repro_tier: D` |
| *(response cell, before 2026-08-14)* | response | — | — | — | — | — | — | ✗ **closed** — see `docs/literature/gastric-response/` |

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Read by us? |
|---|---:|---|---|
| `abc_method` | 405 | **Methods**, two subsections: "Serum pepsinogen level" defines atrophy (PG I ≤ 70 ng/mL **and** PG I/II ≤ 3.0); "Classification by anti-*H. pylori* antibody and serum pepsinogen status" defines groups A–D. | ✅ |
| `xu_gastric_trg_score` | 16 | **Table 4**, "Risk Score of Prediction Model for TRG" — four point assignments. The betas behind them are **Table 3**. | ✅ |
| `msk_gastric` | **409** | **Not the paper.** *J Clin Oncol* 2003;21(19) prints a nomogram figure and no equation. Coefficients from the deployed R at `ClevelandClinicQHS/riskcalc-website/GastricCancer`, with S₀ at 5 years (0.579053) and 9 years (0.5089101). | ⚠️ verified against the figure — see below |

---

## Prognosis: the vendor-sourced model that checks out

`msk_gastric` has the same provenance problem as `msk_ovarian`, the paper
prints a figure, the numbers live only in someone's deployment, and the
opposite result.

On 2026-08-14 the deployed model was measured against the published Fig. 2.
The scale came from the **Depth axis**, so the age comparison is independent of
the term under test:

- Depth-derived scale **36.60** points per LP unit against **36.61** from the
  age axis itself, a **0.03%** difference
- age agrees at every printed label to within **0.4 points** on a 0–100 axis
- the implementation reproduces the **non-monotonic shape** without being told
  to: minimum at 60, with ages 40 and 70 landing within 0.3 points of each
  other, exactly as the figure prints them

That last point is the one that matters. The age term is a restricted cubic
spline with knots at 48, 67 and 80, taken from the vendor's R. Nothing about
transcribing those numbers encodes "the curve should bottom out at 60 and be
near-symmetric around it". The figure says it does; our implementation says it
does; neither was fitted to the other.

**Why this entry exists at all.** A measurement that only ever finds
disagreement cannot be told apart from a broken measurement. `msk_ovarian`
fails the same check by 17 points, and that result is only interpretable
because this one, and the pancreatic one, pass. The cells that agree are
recorded as deliberately as the one that does not.

**One honest limit:** we enforce `AGE_RANGE (25, 96)` from the development
cohort while the figure draws its axis from 20 to 100. There are two ages the
published figure will read and we refuse.

**The superseded entry is kept on purpose.** `msk_gastric_dss` records why this
cell took so long: the primary is figure-only, and the equation was eventually
recovered from a vendor's published source rather than from any paper. Deleting
it would delete the explanation.

---

## Detection: a flagship with no discrimination statistic, and that is not a gap

`abc_method` reports **no AUC and no concordance index**. The registry says so
in the discrimination field rather than leaving it blank, and the evidence it
carries instead is stratification:

| Group | Annual gastric-cancer incidence |
|---|---|
| A | 0.04 %/y |
| B | 0.06 %/y |
| C | 0.35 %/y |
| D | 0.60 %/y |

Log-rank p < 0.0001. A fifteen-fold spread from A to D, from two serological
tests, *H. pylori* antibody and serum pepsinogen, and no imaging.

This is a different kind of evidence from a c-index, not a weaker version of
one. The model's claim is that four groups have separable incidence, and the
table is that claim. Recording "n/a as a c-index" and then the rates is more
honest than computing a concordance from published group rates and presenting
it as the paper's.

**Two scope limits that travel with it:**

- **The absolute rates are Japanese-cohort rates.** The *ordering* transfers;
  the numbers do not. A group-D patient elsewhere is high-risk relative to
  group A, not 0.60%/y.
- **It is invalid after *H. pylori* eradication.** Seroreversion moves patients
  between groups without changing their risk, so the classification stops
  meaning what it meant. This is a scope note that will bite in any modern
  cohort, where eradication is common.

---

## Response: chosen out of 28 papers on one criterion

The response cell was a `gap` until 2026-08-14. Closing it is documented in
full at `docs/literature/gastric-response/`, the shortlist, the ranking
method, and per-paper provenance for all 28 candidates.

`xu_gastric_trg_score` won on a criterion the others fail: **it is computable
exactly as published.** The four point values, the 0–23 range and the 13-point
cutoff are all printed in text and tables. Predicted outcome is Ryan TRG 0,
pathological complete response, after preoperative chemotherapy.

Reported discrimination: **AUC 0.84 (0.77–0.91) training, 0.73 (0.55–0.91)
internal validation, 0.82 (0.71–0.92) prospective cohort.** No c-index and no
calibration analysis appear anywhere in the paper.

**Three limits belong beside any number this produces**, and the registry
carries them:

1. **Single-centre**, with no external cohort.
2. **The rounding rule cannot be reconstructed.** The paper maps odds ratios
   5.615 / 4.531 / 7.426 / 7.945 onto points 5 / 4 / 7 / 7 and never states how.
   We implement the published points, not a re-derivation, because the points
   are what the paper actually asserts.
3. **The 13-point cutoff's provenance is unstated.** Whether it was the
   operating threshold behind the reported AUCs is not said.

**What was rejected, and why it is worth knowing:** the runner-up (PMID
41883960) would have given a probability rather than a risk group, which is the
more useful output. It was not chosen because **its coding direction
contradicts its own Table 1**, and its evidence is weaker (n = 113, no external
cohort). The decision was to take the computable risk group over a probability
that cannot be trusted to point the right way.

---

## What this disease shows that the others do not

Three cells, three different failures of the literature to publish a usable
model, and three different resolutions:

| Cell | What the paper withheld | How it was resolved |
|---|---|---|
| prognosis | the equation — figure only | **recovered from the vendor's deployed source**, then verified against the figure |
| detection | any discrimination statistic | **replaced by stratification**: the incidence table *is* the evidence |
| response | nothing — 27 of 28 candidates withheld something | **avoided**: chosen on computability rather than on performance |

The third is the one worth generalising. Selecting a model on "can we compute
it exactly as published" rather than on the highest reported AUC produced a
cell that is verifiable, at the cost of a lower headline number and a single
centre. Every other selection rule in this library eventually runs into a paper
that reports well and publishes nothing.

| Axis | Flagship | Cites | /yr | What decided it |
|---|---|---:|---:|---|
| detection | ABC method | 405 | 19.3 | two serological tests, no imaging; stratification is the evidence |
| response | Xu TRG score | 16 | 3.2 | **computability**, out of 28 candidates |
| prognosis | MSK gastric | **409** | 17.8 | the only published option, and it survives measurement against its own figure |

---

## Open items

1. **The 20–25 and 96–100 age bands are unreachable.** The published figure
   reads them; our enforced range does not. Either widen the range with a note
   that the splines are unanchored there, or record the refusal as intended.
2. **`abc_method` needs a non-Japanese incidence anchor** before its absolute
   rates are shown to anyone. The ordering is what transfers, and a report that
   prints 0.60 %/y without that caveat will be read as a local figure.
3. **`xu_gastric_trg_score`'s cutoff provenance** could be settled by one email
   to the authors, along with the rounding rule. Neither has been asked.
4. **`gastric_prognosis_catalog` is `repro_tier: D`:** TNM staging tables,
   "not an equation, in the sources we checked". That last clause is a hedge
   worth resolving: AJCC does publish survival by stage, and whether that
   counts as a model for this library's purposes has not been decided.

---

## How this dossier was built

The method is the eight steps in `docs/diseases/cvd/README.md`. Three did the
work here:

- **Step 4. Do not report an impact factor.** *J Clin Oncol* and *Gut* are
  both first-rank journals in their fields and their papers here are 409 and
  405 citations, four apart. Any ranking that separated them would be noise.
- **Step 6. Write down the negative results with their reasons.**
  `abc_method` has no c-index; that is recorded as a property of the paper, not
  as a missing field.
- **Step 8. Check whether "has code" means "has a model".** Inverted twice
  over in this disease: `msk_gastric` has code and no published equation, and
  its code turned out to be faithful; the response cell had 28 papers with
  equations and only one that could be computed as printed.
