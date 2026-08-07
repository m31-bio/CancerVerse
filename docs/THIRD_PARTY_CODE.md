# Third-party code: what we use, and what we do not distribute

Seven files that exist in the working repository are **not** in this one. They
transcribe arithmetic from a source licensed for noncommercial use only, and
this repository belongs to a company. This document says exactly which models
are affected, where their numbers came from, why the files are withheld, and
how to regenerate them.

Nothing here is legal advice. It is a record of what was checked and what was
decided, so that a lawyer reading it does not have to reconstruct it.

---

## 1. Which models

Six models take their coefficients from calculators deployed at
**riskcalc.org**, plus one extraction tool:

| Model | Cell | What was taken |
|---|---|---|
| `pbcg` | prostate · detection | 8 multinomial coefficient sets, one per missing-data pattern |
| `dutasteride` | prostate · response | 315 coefficients across 17 Cox sub-models |
| `crc_pro` | colorectal · detection | two sex-specific Cox models with spline knots, and the baseline survival, which the paper never printed |
| `msk_gastric` | gastric · prognosis | Cox linear predictor and S₀ at 5 and 9 years |
| `msk_ovarian` | ovarian · prognosis | Cox linear predictor and S₀ at 5 years |
| `msk_pancreatic` | pancreatic · prognosis | Cox linear predictor and S₀ at 12, 24, 36 months |

Every other implemented model is unaffected. Thirteen come from papers alone;
the rest use MIT-licensed reference packages (`preventr`, `predictv30r`,
`RiskScorescvd`), a GPL CRAN package used but not redistributed (`BCRA`), or a
published points table.

## 2. Where they came from

`https://github.com/ClevelandClinicQHS/riskcalc-website` — the public source of
the calculators hosted at riskcalc.org, published by Cleveland Clinic's
Quantitative Health Sciences department.

All six have a genuine peer-reviewed development paper, verified in PubMed:

| Model | Paper | Does the paper print the equation? |
|---|---|---|
| `pbcg` | Ankerst DP et al, *Eur Urol* 2018 | partially |
| `dutasteride` | REDUCE trial analyses | no |
| `crc_pro` | Kattan MW et al, *J Am Board Fam Med* 2014, PMC4219857 | coefficients yes (Table 5A/5B); **baseline survival no** |
| `msk_gastric` | Kattan MW et al, *J Clin Oncol* 2003, PMID 14512396 | no — a nomogram figure and a c-index, nothing else |
| `msk_ovarian` | Abu-Rustum NR et al, *Gynecol Oncol* 2008, PMID 17950784 | no |
| `msk_pancreatic` | Brennan MF et al, *Ann Surg* 2004, PMID 15273554 | no |

These are **published models**, not unpublished ones. Printing a nomogram
figure instead of a coefficient table was normal practice for a four-page
oncology article in that era. The deployed source is where the numbers survive
in machine-readable form.

## 3. Why the files are not in this repository

`ClevelandClinicQHS/riskcalc-website` is licensed **PolyForm Noncommercial
1.0.0**:

> Any noncommercial purpose is a permitted purpose.

That is a copyleft-adjacent restriction of a different kind from the GPL: the
GPL permits commercial use and constrains distribution terms, whereas PolyForm
Noncommercial constrains the **purpose**. A company repository is not a
noncommercial purpose.

The distinction that matters, and the reason only seven files are withheld
rather than six models being dropped:

**Coefficients are facts.** A fitted regression coefficient is a measurement of
a dataset, not an authored expression. Facts are not subject to copyright
(*Feist Publications v. Rural Telephone*, 499 U.S. 340). Our Python
implementations are independently written from those numbers and stay.

**The R files are expression.** Six reference scripts copy the vendor's
`formula` expressions verbatim — their own headers say so — to reproduce the
vendor's arithmetic exactly. That is copying code, and it is what the licence
reaches. So those files are withheld:

    tests/parity/reference/crc_pro_reference.R
    tests/parity/reference/pbcg_reference.R
    tests/parity/reference/dutasteride_reference.R
    tests/parity/reference/msk_gastric_reference.R
    tests/parity/reference/msk_ovarian_reference.R
    tests/parity/reference/msk_pancreatic_reference.R
    tests/parity/reference/dutasteride_extract.py

**One question is genuinely open and should go to counsel.** The dutasteride
model uses 315 coefficients extracted mechanically from that source. Under US
law the individual numbers are facts, but the EU *sui generis* database right
(Directive 96/9/EC) can protect a substantial extraction from a database even
where the individual items are not copyrightable. Whether 315 coefficients is a
"substantial part" of that repository is not a question this document can
answer. The file ships as package data today because the model does not run
without it.

## 4. What this costs, which is nothing operationally

The withheld files are tools for regenerating fixtures. **The test suite never
runs them.** Parity tests compare against captured JSON values —
`crc_pro_cases.json` and its siblings — which are outputs, and the output of
running a program is not a derivative work of that program.

    uv run pytest -q        # 792 tests, none of them invoke R

To regenerate a fixture, obtain the vendor source yourself under its own terms
and re-derive the reference script. The registry records, per model, which file
produced which fixture, in `evidence.script`.

## 5. Other third-party sources, for completeness

| Source | Models | Licence | Status |
|---|---|---|---|
| ClevelandClinicQHS/riskcalc-website | 6 | **PolyForm Noncommercial 1.0.0** | code withheld; coefficients used |
| WintonCentre/predictv30r | `predict_breast` ×2 | MIT | fetched on demand, not vendored |
| martingmayer/preventr | `prevent` | MIT | fetched on demand, not vendored |
| CRAN `RiskScorescvd` | `score2` | MIT | fetched on demand, not vendored |
| CRAN `BCRA` | `bcrat` | GPL (≥2) | fetched on demand, **never redistributed** |
| SWOP calculator | `erspc_rc3` | website, no stated licence | constants recovered from a retired Flash calculator; the same constants are printed in the paper's appendix, which is the citation used |
| MSK hosted calculator | `msk_rectal` | research and educational use, **not commercial** | used only to obtain comparison outputs; the equation itself comes from the paper's Supplement 1 |
| MDCalc | `albi`, `capra`, `cha2ds2_vasc` | website | used only to cross-check point tables already printed in the papers |

`collected/MANIFEST.yaml` pins the fetchable ones;
`scripts/fetch_references.py` retrieves them.

## 6. How this is enforced

`scripts/sync_public_repo.py` asserts that none of the seven files can reach
this repository, and fails loudly rather than silently skipping them.
`scripts/audit_public_repo.py` checks the published tree independently. The
evidence test in `tests/test_registry.py` knows these seven are withheld, so a
deliberate absence does not read as a broken pointer — and any *other* missing
reference file still fails.
