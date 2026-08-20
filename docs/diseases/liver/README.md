# Liver cancer: paper dossier

Six papers, three shipped. What makes this disease worth a dossier of its own:
**the most-cited model here, by a factor of seven, is the flagship of a cell it
does not actually answer**, and that was discovered by reading what the code
returns, not by reading the citation count.

Bibliometrics: `bibliometrics.json`, resolved via OpenAlex 2026-08-17. Citation
counts are reported beside citations-per-year throughout, because ALBI is
eleven years old and aMAP is five.

---

## The papers

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---:|---:|---:|:--:|:--:|---|
| **Johnson et al — ALBI grade** ([10.1200/JCO.2014.57.9151](https://doi.org/10.1200/JCO.2014.57.9151)) | prognosis | 2015 | J Clin Oncol | **2,813** | **234.4** | ✗ web only | ✅ inline in Results | ✅ **flagship** as `albi`, parity-checked |
| **Kadalayil et al — HAP score** ([10.1093/annonc/mdt247](https://doi.org/10.1093/annonc/mdt247)) | response | 2013 | Ann Oncol | 380 | 29.2 | ✗ | ✅ **Table 3** | ✅ **flagship** as `hap`, parity-checked |
| **Fan et al — aMAP** ([10.1016/j.jhep.2020.07.025](https://doi.org/10.1016/j.jhep.2020.07.025)) | detection | 2020 | J Hepatol | 361 | **60.2** | ✗ | ✅ display equation | ✅ **flagship** as `amap`, parity-checked |
| **Farinati et al — ITA.LI.CA** ([10.1371/journal.pmed.1002006](https://doi.org/10.1371/journal.pmed.1002006)) | prognosis | 2016 | PLOS Medicine | 143 | 14.3 | ✗ | ✅ **Table 3, complete** | ✗ **catalog** — blocked on *data*, see below |
| BCLC staging | prognosis | — | guideline | — | — | ✗ | ✗ | ✗ **catalog** — reference standard, lost the head-to-head |
| ABCR / ART (TACE retreatment) | response | — | — | — | — | ✗ | ⚠️ from validation papers only | ✗ **catalog** — not primary-sourced |

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Read by us? |
|---|---:|---|---|
| `albi` | **2,813** | **Results**, the multivariable Cox paragraph, printed inline: `linear predictor = (log10 bilirubin × 0.66) + (albumin × −0.085)`. Not a table, not a figure. | ✅ |
| `hap` | 380 | **Table 3**, "Calculation of the Hepatoma arterial-embolisation prognostic (HAP) score", p. 2568 — four point assignments and four grade boundaries. | ✅ |
| `amap` | 361 | **Results**, "Derivation of the HCC risk score" — a display equation in prose. | ✅ |

All three are primary-sourced from the article itself. No model in this disease
takes a coefficient from a vendor deployment, which distinguishes it from
prostate, gastric, ovarian and pancreatic.

### Two of the three are noncommercially licensed: the highest share in the library

| Model | Article licence | Where that is stated |
|---|---|---|
| `amap` | **CC BY-NC-ND 4.0** | [ORA record](https://ora.ox.ac.uk/objects/uuid:de233595-872f-425d-aff8-6b4291bca49d); Europe PMC reports `isOpenAccess "N"` |
| `hap` | **CC BY-NC** | Europe PMC, `license "cc by-nc"` for `10.1093/annonc/mdt247` |
| `albi` | open | — |

Both carry a `license_basis` in the registry giving the reasoning: what was
taken is a coefficient table, coefficients are facts, and facts are not
copyrightable (*Feist v. Rural Telephone*). The determination is written down
rather than assumed, and `test_noncommercial_basis_matches_the_licence_field`
fails the build if `license` and `license_basis` ever disagree, which they did
here once, silently, before that test existed.

**aMAP's was the case that produced the test.** Its `license` field read `open`
while `equation_source`, in the same entry, already said CC BY-NC-ND. One
record, two answers, and an audit that reads only the short field believes the
reassuring one.

---

## Prognosis: the most-cited model in the disease is not a survival model

ALBI has **2,813 citations, 234 a year**, more than the other five papers
combined, several times over. It is the flagship of liver · prognosis. And:

```python
albi_predict(bilirubin_umol_l=20, albumin_g_l=38)
→ {'score': -2.371, 'grade': 2, 'risk': None, ...}
```

`risk` is `None`, and that is correct. **ALBI is a liver-function grade, not a
survival model.** It was built to replace Child-Pugh's subjective components,
and its authors fitted a Cox model only to choose the two coefficients before
cutting the result into three grades. What was published is a grade. There is
no baseline survival function anywhere in the paper, and none could be, because
the paper is not about survival.

That matters for what can be measured. Against a model that emits S(t|x):

| Metric | Computable for ALBI? |
|---|---|
| Concordance / C-index | ✅, but on the **continuous score**, not the 3-level grade, where ties dominate |
| Separation between risk groups, hazard ratio | ✅ — this is the model's actual published claim |
| Calibration (observed vs predicted survival) | ❌ no predicted survival to compare against |
| Brier, integrated Brier | ❌ both need a probability |
| **Decision curve analysis / net benefit** | ❌ needs a probability at a threshold |

The last row is the one that costs something: net benefit is the primary
clinical-impact measure in the Phase 2 evaluation plan, and this cell cannot
produce it from the published model.

### Its discrimination is not extractable either

The registry records `n/a in extractable form` for `albi`, and that is a
negative result that was checked twice rather than assumed: Harrell's C and
Somers' D **were** computed by the authors, and printed only inside Figures
1A–1H. The full text was grepped independently for `Harrell`, `Somers`,
`concordance` and `AUC` to confirm the statistic is genuinely unreachable
rather than merely unread.

### The replacement, and why it is blocked on data rather than on the paper

`italica`, the ITA.LI.CA integrated prognostic score, is recorded as
`candidate_for: albi`. Its case:

- **C-index 0.72 training, 0.71 internal, 0.78 external (Taiwan)**
- beat **BCLC, CLIP, JIS, MESIAH and HKLC** head-to-head, on the same patients
- a 2021 overview in *Cancers* re-checked the field and still found it the best
  discriminator
- **Table 3 is complete**: one point per ITA.LI.CA stage increment (0–5),
  Child-Pugh 5 / 6–7 / 8–9 / >10 → 0/1/2/3, ECOG 0 / 1–2 / 3–4 → 0/1/3, and
  2 points for AFP > 1,000 µg/L

It is not blocked on the literature. It is blocked on **inputs the platform
does not hold**: ECOG performance status appears nowhere in the field
crosswalk, and Child-Pugh needs INR and hepatic encephalopathy grade, which are
also absent. Bilirubin, albumin, ascites and AFP are already in the Minimal cut.

**BCLC was considered and deliberately not chosen.** It is the guideline
standard and the obvious safe pick, but it needs the same inputs, performance
status, liver function, tumour stage, and lost the head-to-head. Same cost,
worse discrimination. It is carried as the standard-of-care reference rather
than as the comparator to beat.

**What ITA.LI.CA does not fix:** it publishes no baseline survival function
either. Table 3 gives the parametric model's estimates and Table S2 median
survival by quartile, but nothing that yields S(t|x). Under a design where the
baseline hazard is fitted locally that is not disqualifying, the score is the
model, and the baseline hazard is a property of the cohort, but it should not
be discovered later.

---

## Detection: the newest flagship in the disease, and it embeds the oldest

`amap` (2020) is the only model here developed in the last decade, and the only
one with a C-index that transfers: **0.82–0.87 across aetiologies and
ethnicities**, from eleven prospective studies.

It also **embeds ALBI as a single term**, which produces a rounding detail
worth knowing before someone treats it as a bug:

> aMAP rounds ALBI's albumin coefficient to **−0.085** where Johnson 2015 uses
> **−0.0852**, and each model keeps its own published rounding.

Two models in the same disease, one nested inside the other, disagreeing in the
fourth decimal, because the authors of the second rounded. Reconciling them
would make our `amap` disagree with its own paper.

Its inputs are four routine values, age, sex, albumin, bilirubin, platelets,
so it is `ehr_availability: routine`, the least demanding flagship in the
disease.

---

## Response: a score for a decision, from a table that took work to read

`hap` predicts survival after transarterial chemoembolisation, from four
dichotomies: albumin < 36 g/L, bilirubin > 17 µmol/L, AFP > 400 ng/mL, dominant
tumour > 7 cm. Grades A–D.

Two things about it:

**Its discrimination is in a supplementary file, not the article.** The main
text states only that HAP "had the highest AUROC" with pairwise P-values and
never prints a value. The figures in the registry,
1-year 0.79 (0.69–0.88) training, 0.67 (0.58–0.76) validation, were read from
**Supplementary Table S4**, recovered from a `.doc` attachment. A paper that
says "highest" without saying "how much" is a paper whose numbers exist and are
one retrieval step away.

**It is prognosis under a treatment, not treatment benefit.** HAP estimates how
a patient does after TACE. It does not estimate what TACE *added*, because
there is no comparison arm. It occupies the response cell because the decision
it informs is a treatment decision, but it should not be scored with
benefit metrics, a distinction the Phase 2 evaluation plan makes explicitly.

`abcr_art` would be the model that actually addresses retreatment, and it is
catalogued rather than implemented for a reason recorded in the registry: its
coefficients are known only from **validation papers, not the primary
derivation**. The project's rule is that a coefficient enters code only from a
source actually read, and a validation study restating someone else's model is
a lead, not a source.

---

## What this disease shows that the others do not

Three diseases, three ways for influence and usability to come apart:

- **prostate.** The best-read paper is complete *and* good, and its licence
  forbids the use
- **cvd.** The best-read paper is complete but discriminates worse
- **liver.** The best-read paper, by a factor of seven, **answers a different
  question than the cell it occupies**

The third is not a licence problem or a performance problem. ALBI is an
excellent liver-function grade, correctly implemented, correctly parity-checked,
and correctly the most-cited paper here. It simply is not a survival model, and
nothing in a citation count, a licence field or a parity test would ever have
said so. What said so was running it and looking at what came back.

| Axis | Flagship | Cites | /yr | Why it holds the cell |
|---|---|---:|---:|---|
| detection | aMAP | 361 | 60.2 | genuinely both — newest, best-transferring, routine inputs |
| response | HAP | 380 | 29.2 | the only primary-sourced option; ABCR/ART is validation-sourced |
| prognosis | ALBI | **2,813** | **234.4** | **placeholder** — ITA.LI.CA is chosen and waiting on data |

---

## Open items

1. **`italica` needs four fields from the platform:** ECOG performance status,
   INR, hepatic encephalopathy grade, and the tumour staging detail the
   ITA.LI.CA stage needs (largest nodule diameter, nodule count, macroscopic
   vascular invasion, extrahepatic spread). Not yet requested.
2. **`italica`'s Table 3 points have not been checked against the typeset
   table.** They were read from the PMC rendering. Under this project's rule
   they must be verified against the PDF before they enter code.
3. **The prognosis cell cannot produce net benefit** until ITA.LI.CA lands, and
   even then only with a locally fitted baseline hazard. Worth stating in any
   evaluation plan that promises decision curve analysis for every cell.
4. **`abcr_art` is unresolved, not rejected.** Finding the primary derivation
   for ABCR would give this disease a genuine retreatment-decision model, which
   HAP is not.
5. **No model here has been checked against a published nomogram**, because no
   paper in this disease prints one, every equation is in text or a table. The
   measurement that cleared `msk_gastric` and `msk_pancreatic`, and failed
   `msk_ovarian`, has nothing to run against here and is not needed.

---

## How this dossier was built

The method is the eight steps in `docs/diseases/cvd/README.md`. Three did the
work here:

- **Step 5. Score usability separately from influence, and let them
  disagree.** In this disease the disagreement is not about quality. ALBI is
  both the most influential and the best-executed model in the cell; it answers
  a different question.
- **Step 6. Write down the negative results with their reasons.** ALBI's
  discrimination is unreachable, and that was confirmed by grepping the full
  text for four different terms rather than by failing to find it once.
- **Step 8. Check whether "has code" means "has a model".** Inverted here:
  every model in this disease has a *published equation* and none has code.
  What needed checking was whether a published equation means a published
  *model*, and for the prognosis cell it does not.
