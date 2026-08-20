# Colorectal cancer: paper dossier

Six papers were assessed and three are implemented, **filling all three axes**. The spine of this
disease is one obstacle appearing in every cell: **the paper publishes the
coefficients and withholds the constant that turns them into a probability.**
It happened three times and was resolved three different ways, and the third
way is a 2021 paper simply not doing it.

Bibliometrics: `bibliometrics.json`, resolved via OpenAlex 2026-08-17.

---

## The papers

| Paper | Axis | Year | Journal | Cites | /yr | code | formula | In the library? |
|---|---|---|---:|---:|---:|:--:|:--:|---|
| **Kattan et al — CRC-PRO** ([10.3122/jabfm.2014.01.130040](https://doi.org/10.3122/jabfm.2014.01.130040)) | detection | 2014 | J Am Board Fam Med | **67** | 5.6 | ⚠️ riskcalc.org for S₀ | ⚠️ **coefficients yes, baseline no** | ✅ **flagship** as `crc_pro`, but `not_ehr` |
| **Weiser et al — MSK rectal calculator** ([10.1001/jamanetworkopen.2021.33457](https://doi.org/10.1001/jamanetworkopen.2021.33457)) | prognosis | 2021 | JAMA Netw Open | 31 | **6.2** | ✗ | ✅ **full — supplement eTable + eFigure** | ✅ **flagship** as `msk_rectal`, parity-checked |
| **Wang et al — LARC pCR nomogram** ([10.1002/cam4.7301](https://doi.org/10.1002/cam4.7301)) | response | 2024 | Cancer Medicine | 8 | 4.0 | ⚠️ deployed calculator | ⚠️ **six ORs yes, intercept no** | ✅ **flagship** as `wang_larc_pcr` |
| NCI CRC Risk Assessment | detection | — | — | — | — | ✗ | — | ✗ **catalog** — superseded by CRC-PRO |
| MSK colon nomograms (3rd-gen DFS, SEER OS) | prognosis | — | portal | — | — | ✗ web only | ✗ **figure only** | ✗ **catalog**, `repro_tier: C` |
| *(response cell, before 2026-08-14)* | response | — | — | — | — | — | — | ✗ **closed** — kept as the record |

---

## Where every shipped parameter actually came from

| Model | Cites | Parameters came from | Complete in the paper? |
|---|---:|---|---|
| `msk_rectal` | 31 | **Supplement 1** — the eTable "Parameter Estimates for Cox Regression Models Predicting RFS and OS", and the eFigure "Predictive Equations for Incomplete Responders". | ✅ **yes, entirely** |
| `wang_larc_pcr` | 8 | **Table 4** for the multivariable odds ratios, Results 3.3 for the points formula. **The intercept came from the deployed calculator.** | ⚠️ all but one number |
| `crc_pro` | 67 | **Table 5A** (men) and **5B** (women) for the coefficients. **The baseline survival — 0.9846654 men, 0.9901043 women — is not in the paper**; it comes from the vendor's R. | ⚠️ all but the baseline |

---

## The recurring obstacle, and three resolutions

**`wang_larc_pcr`: blocked on one number for three months.** The registry
entry for the old gap is kept rather than deleted, because how it was closed is
the useful part. Everything was published: pre-CRT CEA 0.944, histopathology
4.608, T stage 0.793, N stage 0.727, MRI EMVI 0.352, TNT 2.264, and the points
formula, **except the intercept and the points-to-probability axis**. Six
coefficients and no way to turn them into a number. It was closed on
2026-08-14 by recovering the missing constant from the authors' own deployed
calculator, not by email.

**`crc_pro`: the baseline survival was never published.** Coefficients are in
Tables 5A/5B and can be read by anyone. S₀ cannot. It is taken from the vendor
R, which is PolyForm Noncommercial, which is why this model's reference script
is among the six withheld from the company repository.

There is a second, subtler gap in the same model that is worth stating because
it changes what "re-source from the paper" would cost: **the spline knot
locations are not published either.** The paper says three knots (four for
pack-years in women) and never gives their positions. Coefficients without
knots are weights without the features they weight. Recovering CRC-PRO from its
paper alone is therefore not possible even in principle, whatever is done about
the baseline.

**`msk_rectal`: nothing was withheld.** JAMA Network Open, 2021, CC BY, and
Supplement 1 carries the Cox parameter estimates *and* the assembled linear
predictors *and* the baseline survival at 0, 60, 120 and 180 months. It is the
counterexample that shows the pattern is a publishing choice, not a property of
oncology nomograms. A 2021 open-access paper published what the 2003 and 2004
MSK papers did not.

*(One thing it did leave ambiguous: whether the eFigure or the hosted
calculator governs. That was settled in favour of the eFigure, the paper, and recorded as a defect the project found in its own earlier reading.)*

---

## Detection: the flagship cannot be computed from a health record

`crc_pro` is the only implemented model in the library marked
**`ehr_availability: not_ehr`**, and the reason is its inputs:

> red meat in **ounces per day**, alcohol in **drinks per day**, education in
> **years**, weight in **pounds**, height in **inches**, pack-years

These are Multi-Ethnic Cohort questionnaire items. No health record holds ounces
of red meat per day. The model is correctly implemented, parity-checked against
the vendor's R to 4.5 × 10⁻¹¹ percentage points, validated ranges enforced:
and it cannot be run on the data this library exists to run on.

**Discrimination:** cross-validated C 0.681 (men), 0.679 (women).

### The model that would fix this is blocked by its licence

The catalog entry for `nci_crc` records it plainly:

> **QCancer-10 still validates better externally (AUC 0.67–0.70 men, 0.63–0.66
> women) but publishes no open source, so it cannot be verified.**

QCancer-10 is built on UK primary-care records and its variables are, by
design, ones a health record already holds. Independent validation in UK
Biobank found it among the best-performing models for incident colorectal
cancer, and noted it "includes variables available within routine electronic
health records and would not require additional data collection".

Its algorithms were promised as open source under LGPL v3 in the 2015 *BMJ
Open* paper. As of 2026-08-14 that release has not happened: `qcancer.org/10yr/`
carries **"ALL RIGHTS RESERVED"** and an explicit prohibition on using the site
"to develop or test software", which forbids even the parity check that every
other model here gets.

So this cell holds a model that is verifiable and unrunnable, while the model
that is runnable is unverifiable. That is not a gap in the literature; it is a
licence.

---

## Response: the newest cell in the library, and the narrowest

`wang_larc_pcr` predicts **pathological complete response** after neoadjuvant
chemoradiotherapy in locally advanced rectal cancer. C-index **0.73 (0.70–0.75)**
training, **0.78 (0.72–0.83)** external validation; the deployed fit reports
C 0.737 and Brier 0.151.

Its scope note carries a trap worth repeating:

> All six inputs are **pre-CRT** values. Feeding post-treatment (yp) staging in
> is a different question.

The model is staged *before* treatment, in patients who go on to complete
chemoradiotherapy and proceed to surgery. Used with post-treatment staging it
would answer nothing, and the inputs have names that make the mistake easy.

---

## Prognosis: complete responders are not in the model

`msk_rectal` gives recurrence-free and overall survival after chemoradiotherapy
and surgery. C-index **0.70 (0.65–0.76)** RFS and **0.73 (0.65–0.80)** OS
internally; **0.71 and 0.72** externally, at Siteman Cancer Center. Development
cohort 710 patients, MSK, 1998–2014.

Three limits, all enforced in code:

1. **Incomplete pathological responders only.** Complete responders are
   estimated by Kaplan–Meier in the source tool, not by this equation.
2. **RFS and OS use different ypT reference groups.** ypT0/T1 versus
   ypT0/T1/T2. Two endpoints, two baselines, in one model.
3. **Predictions only at the published S₀ grid:** 0, 60, 120, 180 months.
   Interpolation is refused rather than silently offered.

Parity was established against MSK's own hosted deployment: 12 patients
spanning both ypT reference groups and both binary covariates, **24 published
probabilities matched** within the tool's 1-percentage-point display
resolution.

---

## What this disease shows that the others do not

| Axis | Flagship | Cites | /yr | The missing constant | How it was resolved |
|---|---|---:|---:|---|---|
| detection | CRC-PRO | 67 | 5.6 | baseline survival **and** spline knots | taken from the vendor's R |
| response | Wang LARC pCR | 8 | 4.0 | the intercept | recovered from the authors' calculator |
| prognosis | MSK rectal | 31 | 6.2 | **none** | the paper published everything |

Three cells, one obstacle, and the third row is the point. Every other dossier
in this project explains why a constant was unavailable; this one has a cell
where the same research tradition, seventeen years later and under an
open-access licence, simply printed it. The obstacle is editorial, not
technical.

The second lesson is narrower and sharper: **the colorectal detection cell is
the clearest case in the library of verifiability and usability being in direct
conflict.** CRC-PRO can be checked and cannot be run. QCancer-10 can be run and
cannot be checked. Choosing between them is not a modelling decision.

---

## Open items

1. **CRC-PRO cannot be freed from the vendor even in principle.** The knots
   are unpublished, not just the baseline. If this cell is to leave PolyForm,
   it needs a different model, not a re-sourcing effort.
2. **QCancer-10's promised LGPL release should be chased.** Hippisley-Cox and
   Coupland, *BMJ Open* 2015;5:e007825, states the algorithms "will be released
   as Open Source Software under the GNU lesser GPL v3". Eleven years later,
   `qcancer.org/10yr/` says all rights reserved. One email would establish
   whether the release is coming.
3. **`wang_larc_pcr`'s intercept came from a deployment, not the paper.** The
   email to the corresponding authors (Ying Huang; Yincong Guo) is no longer
   needed to unblock the cell, but it would still convert this model from
   deployment-sourced to paper-sourced, which no other response model here is.
4. **The MSK colon nomograms remain figure-only**, `repro_tier: C`. Colon and
   rectum are different diseases clinically, and this library currently has
   rectal prognosis and no colon prognosis.

---

## How this dossier was built

The method is the eight steps in `docs/diseases/cvd/README.md`. Three did the
work here:

- **Step 5. Score usability separately from influence.** CRC-PRO is the
  most-cited paper in the disease and the only implemented model in the entire
  library that cannot be computed from a health record.
- **Step 6. Write down the negative results with their reasons.** The
  unpublished spline knots are recorded here because without them the obvious
  remedy, "read it from the paper instead", is impossible, and someone would
  otherwise spend a day discovering that.
- **Step 8. Check whether "has code" means "has a model".** QCancer-10 is the
  inverse case: it has neither code nor a licence permitting a check, while
  being the better model on external validation.
