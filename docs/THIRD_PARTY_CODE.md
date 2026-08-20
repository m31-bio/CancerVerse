# Third-party code: what we use, and under which licence

**REVERSED 2026-08-18. The seven files this document was written to explain are
now IN this repository.** Everything below describes why they were withheld and
remains an accurate record of that reasoning, but the reasoning turned on one
sentence that tested the wrong thing, and the conclusion has changed. Read this
paragraph and §3 together; the rest stands.

What changed, in order:

1. The rule was "a company repository is not a noncommercial purpose". PolyForm
   Noncommercial 1.0.0 does not say that. It says "**any** noncommercial purpose
   is a permitted purpose", and gates on the PURPOSE of the use rather than on
   who is doing the using.
2. This project's use is academic research only. Under PolyForm's own words that
   is a permitted purpose, so the files may be both used and redistributed.
3. **What did not change is licence mixing.** This repository carries an
   Apache-2.0 LICENSE, and nobody may relicense someone else's work by placing
   it in their tree. So each of the seven now carries a notice at the top saying
   this repository's licence does not cover it, `NOTICE` lists them, and
   `scripts/sync_public_repo.py` asserts the notice is present, the same
   enforcement strength as the absence rule it replaces, pointed at a different
   requirement.

If the academic-use premise ever stops holding, these seven come out again.

Nothing here is legal advice. It is a record of what was checked and what was
decided, so that a lawyer reading it does not have to reconstruct it.

---

## 1. Which models

Six models took their coefficients from calculators deployed at **riskcalc.org**, plus one
extraction tool. **One is now resolved**, see the first row, leaving five.

| Model | Cell | What was taken |
|---|---|---|
| ~~`pbcg`~~ | prostate · detection | **RESOLVED 2026-08-07** — replaced by `pbcg_extended`, whose complete 1,024-model coefficient set is Additional file 2 of its own paper under **CC BY 4.0**. Same consortium, four years newer, and commercially usable.  |
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

`https://github.com/ClevelandClinicQHS/riskcalc-website`, the public source of
the calculators hosted at riskcalc.org, published by Cleveland Clinic's
Quantitative Health Sciences department.

All six have a genuine peer-reviewed development paper, verified in PubMed:

| Model | Paper | Does the paper print the equation? |
|---|---|---|
| `pbcg` | Ankerst DP et al, *Eur Urol* 2018 | partially |
| `dutasteride` | REDUCE trial analyses | no |
| `crc_pro` | Kattan MW et al, *J Am Board Fam Med* 2014, PMC4219857 | coefficients yes (Table 5A/5B); **baseline survival no** |
| `msk_gastric` | Kattan MW et al, *J Clin Oncol* 2003, PMID 14512396 | no — a nomogram figure and a c-index, nothing else |
| `msk_ovarian` | Chi DS et al, *Gynecol Oncol* 2008;108(1):191-194, PMID 17950784 | no |
| `msk_pancreatic` | Brennan MF et al, *Ann Surg* 2004, PMID 15273554 | no |

These are **published models**, not unpublished ones. Printing a nomogram
figure instead of a coefficient table was normal practice for a four-page
oncology article in that era. The deployed source is where the numbers survive
in machine-readable form.

## 3. Why the files were withheld, and why they are here now

`ClevelandClinicQHS/riskcalc-website` is licensed **PolyForm Noncommercial
1.0.0**:

> Any noncommercial purpose is a permitted purpose.

That is a copyleft-adjacent restriction of a different kind from the GPL: the
GPL permits commercial use and constrains distribution terms, whereas PolyForm
Noncommercial constrains the **purpose**.

**Note, an earlier version of this section was wrong about
what the licence tests.** It said "a company repository is not a noncommercial
purpose," which tests the entity, not the purpose. PolyForm's own text does
not draw that line: "any noncommercial purpose is a permitted purpose" applies
regardless of who is doing the using, and a separate clause gives an
additional, unconditional safe harbor to specific entity types ("charitable
organization, educational institution, public research organization...
regardless of the source of funding") without saying that is the *only* route
to a permitted purpose. Whether a company's specific, present-day use of this
source is itself a noncommercial purpose. PolyForm's own disqualifier is use
"without any anticipated commercial application", is a business-fact
question this document cannot answer from the licence text alone. See
`docs/ACADEMIC_USE_LICENSE_REVIEW.md`, written the same day this was found,
for the full re-read against the licence's verbatim text and what it does and
does not settle.

The distinction that matters, and the reason only seven files were ever the
question rather than six models being dropped:

**Coefficients are facts.** A fitted regression coefficient is a measurement of
a dataset, not an authored expression. Facts are not subject to copyright
(*Feist Publications v. Rural Telephone*, 499 U.S. 340). Our Python
implementations are independently written from those numbers and stay.

**The R files are expression.** Six reference scripts copy the vendor's
`formula` expressions verbatim, their own headers say so, to reproduce the
vendor's arithmetic exactly. That is copying code, and it is what the licence
reaches. Feist does not help here and was never claimed to:

    tests/parity/reference/crc_pro_reference.R
    tests/parity/reference/pbcg_reference.R
    tests/parity/reference/dutasteride_reference.R
    tests/parity/reference/msk_gastric_reference.R
    tests/parity/reference/msk_ovarian_reference.R
    tests/parity/reference/msk_pancreatic_reference.R
    tests/parity/reference/dutasteride_extract.py

**These seven now ship (2026-08-18), and the reason is that copying is not the
test, purpose is.** PolyForm reaches this code, and PolyForm permits "any
noncommercial purpose". Academic research is one. What the licence still
forbids is presenting the code as Apache-2.0, so each file carries a notice
saying this repository's licence does not cover it, and the sync script asserts
that notice is there. Two distinct questions that the withholding rule had
collapsed into one:

  * *May we copy and redistribute it?*, yes, for a noncommercial purpose.
  * *May we put it under our own licence?*, no, and that is unrelated to
    purpose. It stays PolyForm wherever it goes.

**One question is genuinely open and should go to counsel.** The dutasteride
model uses 315 coefficients extracted mechanically from that source. Under US
law the individual numbers are facts, but the EU *sui generis* database right
(Directive 96/9/EC) can protect a substantial extraction from a database even
where the individual items are not copyrightable. Whether 315 coefficients is a
"substantial part" of that repository is not a question this document can
answer. The file ships as package data today because the model does not run
without it.

## 4. What these files do, and what withholding them cost

They are tools for regenerating fixtures. **The test suite never runs them.**
Parity tests compare against captured JSON values, `crc_pro_cases.json` and
its siblings, which are outputs, and the output of running a program is not a
derivative work of that program.

    uv run pytest -q        # 1,840 tests, none of them invoke R

So withholding them cost nothing to the test suite, which is why it was an easy
rule to keep. What it did cost was the ability to REGENERATE a fixture from the
vendor's own arithmetic. That is not a small thing: running the vendor's
unmodified code is what made those parity checks independent rather than a
second transcription by us, and for five models it is the only such check that
exists. Restoring the files restores that.

The registry records, per model, which file produced which fixture, in
`evidence.script`.

## 5. Other third-party sources, for completeness

| Source | Models | Licence | Status |
|---|---|---|---|
| ClevelandClinicQHS/riskcalc-website | 6 | **PolyForm Noncommercial 1.0.0** | coefficients used; the 7 reference scripts now ship, each under its own PolyForm notice — NOT under this repository's Apache-2.0. See §3 |
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

The enforcement did not weaken when the rule inverted on 2026-08-18; it moved
to the new requirement.

`scripts/sync_public_repo.py` previously asserted that none of the seven files
could reach the published tree. It now asserts two things instead: that **all
seven are present**, and that **each carries its `LICENCE NOTICE` header**. A
file that lost its notice fails the sync, exactly as an unwithheld file used
to. The list itself lives in that module and is imported by
`scripts/build_notice.py` rather than retyped, so `NOTICE` cannot drift out of
step with what is actually shipped.

`scripts/audit_public_repo.py` checks the published tree independently.

`tests/test_registry.py`'s evidence test no longer needs to treat these seven
as a deliberate absence, they are present, so a missing reference file is
once again unambiguously a broken pointer.
