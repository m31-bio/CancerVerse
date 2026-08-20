# Where the numbers would come from

For the gastric response cell, checked directly against the sources on
2026-08-14. One row per finalist: the exact item the parameters sit in, whether
that item is text or pixels, and what is missing.

The point of this page is that "we got it from the paper" is not an answer.
Every number this library ships has to be traceable to a specific table in a
specific document, so that someone else can open that document and disagree.

---

## Summary

| # | Paper | PMID | Parameters sit in | Text or pixels? | Human OCR needed? |
|---|---|---|---|---|---|
| 1 | Xu 2021, Front Oncol | 33937020 | Table 3 (β) + Table 4 (points) | **HTML text** | No |
| 2 | Liu 2023, BMC Cancer | 36631788 | Table 3 (β) | **HTML text** | No |
| 3 | Hou 2026, Front Oncol | 41883960 | Table 2 (β, SE, OR, **intercept**) | **HTML text** | No |
| 4 | Chen 2025, Front Immunol | 40755776 | Table 2 (OR only) | **HTML text** | No |
| 5 | Zhang 2026, Cancer Manag Res | 41924230 | Table 2 (OR only) | **HTML text** | No |

**No OCR is required for any of the five.** All are open-access with complete
PMC deposits, and every coefficient table is a real HTML `<table>`, the numbers
were read out as text, not from an image.

That is the good news and it is not the useful news. The useful news is below:
for four of the five, the piece that is missing is *also not readable by a
human*, because it was either never estimated or exists only as an axis on a
nomogram picture. Handing those PDFs to a person to read would not produce the
missing number. So there is **nothing here to hand over**, this is a modelling
problem, not an access problem.

---

## 1 · Xu 2021: PMID 33937020 · PMC8082104

**Locus.** Two tables, both machine-readable:

- Table 3, *"Multivariate analysis: variables correlated with TRG in the
  training set."*, columns `Variables | B | P | OR | 95% CI`
- Table 4, *"Risk Score of Prediction Model for TRG."*, the integer points

**Read out verbatim.** β: CA19-9 1.725, CA72-4 1.511, differentiation 2.005,
LNmax 2.073. Points: CA19-9 ≤10.90 U/mL → 5, CA72-4 ≤3.19 U/mL → 4, well
differentiated → 7, LNmax ≥1.535 cm → 7. Range 0–23, cutoff 13.

**What is missing.** The points→probability mapping, and it does not exist.
This paper has **no nomogram figure at all**, its three figures are two
Kaplan–Meier panels and a ROC curve. The only mapping printed is score → risk
group at 13 points, with observed pCR rates of 0% and 22.35%.

> Nothing to hand over. The quantity was never estimated, so re-reading the PDF
> cannot recover it.

Also in Table 3: signet-ring cell carcinoma, OR 33,985,914, P 0.998, complete
separation. The authors dropped it from the score, correctly.

---

## 2 · Liu 2023: PMID 36631788 · PMC9832661

**Locus.** Table 3, *"Result of multivariable analysis in the training set. As
revealed by lasso analysis excluding tumor size variable, five prediction
factors were incorporated into the eventual model, which were differentiation
degree, tumor location, Clinical T stage, Clinical N stage and Smoking
history"*. Machine-readable.

**Read out verbatim.** location −1.561, differentiation 1.103, cT stage 1.361,
cN stage 2.040, smoking history 1.129. The minus sign is U+2212, not ASCII,
worth knowing before a parser silently drops it.

**What is missing, two things, not one.**

1. No intercept. Ranks patients; cannot state a probability.
2. **No reference levels.** Table 3 gives bare variable names. Checked against
   the Table 2 cell counts, four of the five coefficients are consistent with
   the favourable level being the indexed one, and `location` has the opposite
   sign under that same coding. The direction is not recoverable from the text.

Both missing pieces live in the Fig. 3 nomogram image and nowhere else.

**This paper also lost its main selling point on re-reading.** It was on the
shortlist as the strongest clinical-only design because of an external cohort of
108 with C-index 0.760. Table 1 contains only training (307) and validation
(153), from a `set.seed` random split of 460. The cohort behind the 0.760 is
given no size and no source anywhere in the paper.

---

## 3 · Hou 2026: PMID 41883960 · PMC13008680

**Locus.** Table 2, *"Multivariate logistic regression analysis of predictors of
major pathological response (MPR) following NICT in patients with LAGC."*,
columns `Variable | B | SE | Wald | OR with CI | P`. Machine-readable. The
binarisation cutoffs are in the Results prose rather than a table.

**Read out verbatim.**

| Variable | B | SE | OR (95% CI) | P |
|---|---|---|---|---|
| **(Intercept)** | **3.081** | 1.179 | 21.785 (2.492–263.329) | 0.009 |
| Tumour bed diameter | −1.393 | 0.549 | 0.248 (0.079–0.697) | 0.011 |
| CEA | −1.321 | 0.527 | 0.267 (0.090–0.727) | 0.012 |
| CA19-9 | −1.897 | 0.557 | 0.150 (0.047–0.423) | <0.001 |
| NLR | −1.330 | 0.664 | 0.265 (0.068–0.957) | 0.045 |
| SII | −1.558 | 0.637 | 0.210 (0.056–0.702) | 0.014 |
| PNI | 0.512 | 0.505 | 1.669 (0.617–4.541) | 0.310 |

Cutoffs (Results prose): tumour bed 3.75 cm, CEA 1.765 ng/mL, CA19-9 18.390
U/mL, NLR 2.422, SII 597.483. All five binarised at these Youden points.

`exp(B)` reproduces every printed OR exactly, intercept included. The table is a
coherent fitted model, not a transcription.

**What is missing.** Nothing, arithmetically. Three things, substantively:

1. **The intercept belongs to the seven-term fit, including PNI.** The Figure 2
   nomogram uses five predictors and drops PNI. Applying 3.081 to a
   five-predictor model is not the fitted model.
2. **The coding direction contradicts the paper's own baseline table.** All five
   biomarker βs are negative, and the Results text attaches them to the *low*
   level ("CEA < 1.765 ng/mL, OR 0.26"). But Table 1 shows the MPR group had
   *lower* CEA (median 1.520 vs 2.900), lower CA19-9, NLR, SII, and a smaller
   tumour bed. A negative β on the low level contradicts that. It is consistent
   only if the indexed level is the *high* one.
3. Text and table ORs disagree slightly (text 0.22 / 0.26 / 0.148 / 0.194
   against table 0.248 / 0.267 / 0.150 / 0.210). Table 2 is internally
   consistent, so Table 2 wins.

> **This is the one thing worth handing over**, and it is a judgement call, not
> an OCR job: (2) cannot be settled from the paper, because the paper is
> self-contradictory. Either we read Figure 2's nomogram to see which direction
> the axes run, or we write to the authors. Shipping it unresolved ships a model
> that is exactly backwards.

---

## 4 · Chen 2025: PMID 40755776 · PMC12313473

**Locus.** Table 2, *"Uni- and multivariate logistic regression analysis for
pathological complete response after NICT in the training set."* ORs only,
there is no `B` column at all. Machine-readable.

**Read out verbatim** (multivariate, reference levels explicit as `1.000`):
age ≥70 → 3.030 (1.327–6.918); non-CR radiological response → 0.092
(0.033–0.257); tumour bed diameter per cm → 0.613 (0.469–0.801); signet-ring
→ 0.108 (0.014–0.838); CEA after NICT ≥4.25 → 0.351 (0.136–0.908).

Explicit reference levels are more than papers 2 and 3 manage.

**What is missing.** βs are recoverable as ln(OR); the constant is not. The only
points→probability statement is the Figure 1 caption — *"total points, ranging
from 0 to 220, and the associated risk value, ranging from 0.1 to 0.9"*, so the
mapping is pixels on a figure axis. Supplementary Table 1 is demographics.

**Correction to what we had recorded.** This is not a seven-centre external
validation. Patients came from seven centres and were then *"randomly allocated
into the training cohort and the validation cohort at a ratio of 7:3"*. The
paper calls the result external. It is an internal split, which is why its
validation AUC (0.934) exceeds its training AUC (0.862).

---

## 5 · Zhang 2026: PMID 41924230 · PMC13035740

**Locus.** Table 2, *"Univariate and Multivariate Analysis of Variables Related
to MPR in Training and Validation Sets."* ORs only, no `B` column.
Machine-readable.

**Read out verbatim** (training multivariate): lower location 2.90 (1.35–6.22);
moderate/high differentiation 3.43 (1.77–6.63); MSI-H 6.63 (0.99–44.49); SIRI
2.02 (1.02–3.97); LDH per U/L 1.02 (1.01–1.03). Optimal threshold 0.576.

**The calculator, and why the colorectal route fails here.** The Shiny app at
`prediction-123.shinyapps.io/Gastric_MPR_Predictor/` is live. A cold fetch
returns the shinyapps.io interstitial (HTTP 202); a warm fetch returns the real
app, which carries a **"Model Information"** panel rendered server-side into the
initial HTML:

    Model Type:            Logistic Regression
    Predictors:            siri, ldh, Differentiation, Location
    Optimal Threshold:     0.576 (Youden Index)
    Model Performance:     AUC = 0.807 (95%CI: 0.751-0.863)
    Training Sample Size:  227

That is a *summary of* the model, not the model. **No coefficients, no
intercept, anywhere in the HTML.** This is the distinction worth recording next
to `EXTRACTION.md`'s colorectal case: DynNom's "Model Summary" tab prints the
fitted object and hands over everything; a hand-rolled Shiny panel like this one
prints prose about the fit and hands over nothing. Recovering this model would
mean probing the websocket patient by patient. Route B, not Route A.

Also: the deployed model and Table 2 are different models. The calculator takes
four predictors; the Table 2 fit additionally carries gender, MSI and MLR.
