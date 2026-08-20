# Commercial use audit: which models rest on code we cannot freely use

**This is not legal advice.** It is a record of what was fetched, what those
sources actually say, and where the provenance of each model's numbers comes
from, assembled so that a lawyer reading it does not have to reconstruct it,
and so that an engineer can act on the parts that are not in doubt. Every
genuinely ambiguous point is flagged for a human decision rather than resolved
here.

Audited 2026-08-14 against `registry/models.yaml` (70 entries: 31 implemented,
31 catalog, 8 gap).

**This whole document was written under one assumption: that M31's use has to
clear a bar suitable for unrestricted commercial redistribution.** On
2026-08-17 M31 said the project's actual use is shifting to an academic/
research posture. That does not change anything written below, it changes
what several of these verdicts *mean*, because a number of the restrictions
below are purpose-gated ("noncommercial purpose", "educational and/or research
purposes", "personal and non-commercial use") rather than flatly prohibited.
`docs/ACADEMIC_USE_LICENSE_REVIEW.md` re-reads every purpose-gated source
against its own verbatim text, fetched fresh that day, and states plainly
which verdicts move and which do not. Read that document alongside this one;
it does not replace it.

---

## The answer, up front

**No: "it came from riskcalc.org" does not mean "we cannot use it."** Six
models in this library took coefficients from riskcalc.org. Exactly **one** of
them (`pbcg`, the 2018 prostate calculator) was ever a real commercial problem,
and it was already fixed on 2026-08-07 by re-sourcing the model to its own
paper's CC BY 4.0 supplement (`pbcg_extended`). The other **five**,
`dutasteride`, `crc_pro`, `msk_gastric`, `msk_ovarian`, `msk_pancreatic`, are
usable as implemented, because what was taken from riskcalc.org was fitted
coefficients, and this library implements them in independently written Python.
What is *not* usable **as Apache-2.0** is the vendor's R code, and six files in
`tests/parity/reference/` copy that code verbatim. Those files were quarantined
from the public repository until 2026-08-18; they now ship, each carrying a
notice that this repository's licence does not reach it. See "Two decisions
taken 2026-08-18" below, the change is that PolyForm gates on purpose, not on
who is using it, and this project's use is academic research only.

Counting the whole picture rather than just riskcalc.org, as of 2026-08-17 and
**after fixing two gaps in the check itself** (see below, the scan used to
miss nested fields entirely, and separately never checked the `license:
restricted` value on its own): **12 of 42 implemented models touch an upstream
that is noncommercially licensed, restricted, or otherwise not open access.**
None is blocked outright. Three carry a copied-code exposure that is contained
and removable, most rest on a noncommercially-licensed or closed-access
*article* rather than code, one used a restricted website only to verify
which of two internally-inconsistent published artifacts a model actually
matches, and **one, `iota_adnex`, needs a human decision.** All nine now
carry a written determination; the three the fixed check newly surfaced
(`msk_rectal`, `hap`, `kunzmann`) were undocumented for three days and were
closed out on 2026-08-17, see "The check itself was blind" below.

Recounted 2026-08-18. The headline had drifted to a stale denominator: it said
37 implemented models while the registry held 40, so three models added after
the last audit were outside the count entirely, and three more were inside it
but named nowhere in this document. Of the six, `chau_eg` and `shapiro_ncrt`
are `license: restricted`, both closed-access articles with no repository
copy, and both already carry a `license_basis` and a `license_url`, which is
why `scripts/audit_public_repo.py` still reported COMPLIANT throughout: the
enforcement never lapsed, only the prose did. The other four (`bcsc_v2`,
`wang_larc_pcr`, `xu_gastric_trg_score`, `ukb_hnc`) are `license: open` and
need no determination.

The lesson is the same one the "blind check" section records, one level up: a
count typed into prose is a second copy of a number the registry already
computes, and it rots without failing. The denominator is now pinned by
`test_audit_headline_matches_the_registry`.

| | count |
|---|---|
| Implemented models | **42** |
| Sourced from riskcalc.org | **6** (5 implemented + 1 retired to catalog) |
| riskcalc.org models actually blocked for commercial use | **0** |
| Implemented models touching any noncommercial/restricted/closed-access upstream | **9** |
| Implemented models with no restricted upstream at all | **28** |
| Flagged, with a written determination on file | **9** (`pbcg_extended`, `atria_stroke_2013`, `amap`, `iota_adnex`, `cibula_arrm`, `moore_criteria`, `msk_rectal`, `hap`, `kunzmann`) |
| Flagged with NO determination | **0** |
| Needing a legal decision before shipping | **1** (`iota_adnex`) — `cibula_arrm`'s derived outcome grid was **determined 2026-08-18**, see below |

---

## Two decisions taken 2026-08-18

Both follow from M31's statement that the project's use is academic research
only. Recorded here rather than in a chat log, because a determination nobody
wrote down is one that gets re-litigated.

### The seven PolyForm reference scripts now ship

They were withheld from the published repository on the reasoning that "a
company repository is not a noncommercial purpose". That sentence tested the
wrong thing. PolyForm Noncommercial 1.0.0 gates on the PURPOSE of the use —
"any noncommercial purpose is a permitted purpose", and says nothing about
who is doing the using. Academic research is a permitted purpose, so the files
may be redistributed.

**Licence mixing is a separate question and did not go away.** The destination
carries an Apache-2.0 LICENSE, and nobody may relicense someone else's work by
putting it in their tree. So the enforcement moved rather than lapsing:

  * each of the seven carries a `LICENCE NOTICE` header stating that this
    repository's licence does not cover it;
  * `NOTICE` lists all seven under "Files NOT covered by this repository's
    Apache-2.0 licence", generated from the same list the sync script enforces
    rather than retyped;
  * `scripts/sync_public_repo.py` asserts all seven are present AND that each
    carries its notice, verified on 2026-08-18 by removing one notice and
    confirming the sync aborts.

**A gap this surfaced, which was older and worse than the thing being fixed:**
`LICENSE` and `NOTICE` were never in the sync list at all. Both had been placed
in the destination by hand in early August and had drifted since, and nothing
detected it because the audit checks only that a LICENSE *exists*, not that it
matches. Shipping mixed-licence files while leaving the file that explains them
behind would have been worse than shipping neither. Both are now mirrored.

### The ESGO-derived outcome grid in `cibula_arrm` is in scope

Previously the one item this document refused to call resolved. The ground is
statutory rather than contractual: UK Copyright and Rights in Databases
Regulations 1997 reg. 20, implementing Directive 96/9/EC art. 9, exempts fair
dealing with a substantial part of a database's contents where it "is extracted
for the purpose of illustration for teaching or research and not for any
commercial purpose, and the source is indicated". All three conditions hold.
That exception is written for research organisations, which is why it, and not
ESGO's own wording, carries the decision.

**What this does not dispose of.** ESGO's site terms say "personal and
non-commercial use only", and *personal* is narrower than *academic*. A
statutory exception is a defence to a database-right claim, not a rewriting of
website terms someone accepted by use; the two can diverge. The determination
rests on the statute and holds while the academic-use premise holds.

Asking Cibula's group for the outcome grid directly would make the question
moot and remains the cheapest fix.

---

## The principle this turns on

`docs/CONVENTIONS.md` already states it, and it is the reason the answer is not
simply "all six are dead":

> Coefficients printed in a peer-reviewed article's supplement are published
> scientific fact; a vendor's terms on its own hosted calculator do not reach
> them.

A fitted regression coefficient is a measurement of a dataset, not an authored
expression, and facts are not subject to copyright (*Feist Publications v.
Rural Telephone*, 499 U.S. 340). An `.R` file that computes with those
coefficients **is** authored expression, and a licence reaches it.

So there are three materially different acts in this repo, and they must not be
collapsed:

1. **Reading a source to recover published constants**, then writing Python from
   them. Not constrained by the source's licence.
2. **Executing a source to capture comparison outputs** into a JSON fixture. The
   output of running a program is not a derivative work of that program, but    the *act of running it* can still be governed by terms that restrict purpose
   rather than copying (MSK's disclaimer is exactly this shape).
3. **Copying the source's code into this repository.** This is what a
   noncommercial licence forbids, and it is what six files in
   `tests/parity/reference/` do.

The distinction is the whole audit. Act 1 is why five riskcalc.org models
survive; act 3 is why six files needed a determination of their own; act 2 is
where the existing documentation has a gap.

Act 3 was resolved on 2026-08-18 and the resolution sharpened the distinction
rather than dissolving it. Copying the vendor's code IS the act a licence
reaches, that never changed. What changed is the recognition that PolyForm
permits that act for a noncommercial purpose, so the question was never "may we
copy it" but "for what". The one thing purpose does NOT fix is the licence the
copy travels under, which is why each file now carries its own notice instead
of inheriting this repository's.

---

## Per-model table

Verdict key: **clear** = no restricted upstream, or the restriction does not
reach what we took. **contained** = a restricted upstream was involved, the
exposure is identified and bounded, and the model itself is usable.
**decide** = needs a human.

Note on "contained": until 2026-08-18 this meant *quarantined*, the restricted
material was kept out of the published tree. For the seven PolyForm reference
files it now means something different: they ship, under their own licence
notice rather than this repository's. The exposure is bounded by labelling
instead of by absence. Every other "contained" row still means what it always
did.

### The riskcalc.org group (the six the question is about)

| Model | Disease · axis | Where the coefficients came from | Upstream licence | Verdict | How to remove the exposure |
|---|---|---|---|---|---|
| `pbcg_extended` | prostate · detection | Additional file 2 of Ankerst 2022, BMC Med Res Methodol — the authors' own published 1,024×13 matrix, not a deployment | **CC BY 4.0** (verified) | **clear** | n/a — this *is* the removal, done |
| `pbcg` (2018) | prostate · detection | riskcalc.org `PBCG/R_code_PBCG_risk_calculator.R` | PolyForm Noncommercial 1.0.0 | **contained** — demoted to `catalog` 2026-08-07 | Already superseded by `pbcg_extended`. But see the discrepancy below: `src/.../pbcg.py` still ships |
| `dutasteride` | prostate · response | 315 coefficients machine-extracted from riskcalc.org `ProstateCancerConsideringDutasteride/server.R` | PolyForm Noncommercial 1.0.0 | **contained**, with one open question | No independent source exists — the REDUCE analyses never printed the equation. See "the dutasteride question" below |
| `crc_pro` | colorectal · detection | Model spec from the open-access paper (PMC4219857, Tables 5A/5B); **baseline survival only from riskcalc.org** | PolyForm Noncommercial 1.0.0 | **contained** | Mostly removable: coefficients are in the paper. The baseline survival is not printed anywhere — request it from the authors |
| `msk_gastric` | gastric · prognosis | riskcalc.org `GastricCancer/server.R` — the 2003 JCO paper prints only a nomogram figure | PolyForm Noncommercial 1.0.0 | **contained** | Not removable from published text. Digitising the nomogram figure is possible but lossy; asking Kattan's group for the coefficients is the real route |
| `msk_ovarian` | ovarian · prognosis | riskcalc.org `OvarianCancer.../server.R` — 2008 Gynecol Oncol prints no equation | PolyForm Noncommercial 1.0.0 | **contained** | As above |
| `msk_pancreatic` | pancreatic · prognosis | riskcalc.org `PancreaticCancer.../server.R` — 2004 Ann Surg prints no equation | PolyForm Noncommercial 1.0.0 | **contained** | As above |

Note that these are **MSK models hosted by Cleveland Clinic**. The licence that
applies is PolyForm on the `ClevelandClinicQHS/riskcalc-website` repository, not
MSK's own nomogram disclaimer, different vendor, different instrument.

### Restricted upstreams that are *not* riskcalc.org

These are not covered by `docs/THIRD_PARTY_CODE.md`, which asserts "every other
implemented model is unaffected." That claim is too strong.

| Model | Disease · axis | Where the coefficients came from | Upstream licence | Verdict | How to remove the exposure |
|---|---|---|---|---|---|
| `iota_adnex` | ovarian · detection | BMJ 2014;349:g5920, supplementary Appendix D — all 44 coefficients printed | **CC BY-NC 3.0** (verified) — commercial use *not* permitted | **decide** | Nothing to remove by re-sourcing: this *is* the primary publication. See "ADNEX" below |
| `amap` | liver · detection | J Hepatol 2020;73(6):1368-1378 — formula printed in the text | **CC BY-NC-ND** per the registry; **I could not verify this** (ScienceDirect returned 403) | **contained** | The formula is four coefficients stated in the abstract-level text; a fact, not expression. Verify the licence, then close |
| `msk_rectal` | colorectal · prognosis | JAMA Netw Open 2021 Supplement 1 eFigure — the paper, not the tool | Paper: **CC BY** (verified, Europe PMC) — no restriction on the coefficients at all. **Tool: MSK disclaimer, "not for any commercial purposes"** (verified) | **clear on the equation**, with a separate gap | The equation needs nothing removed — it is already fully open. The *fixture* was captured by POSTing to MSK's hosted tool. See "the MSK fixture gap" below |
| `hap` | liver · response | Ann Oncol 2013;24(10):2565-2570, Table 3 — points and grade boundaries printed | **CC BY-NC** (verified, Europe PMC) | **contained** | Table 3 is a fact (Feist); `canonical_impl` is `paper_only`, nothing to re-source |
| `kunzmann` | esophageal · detection | Clin Gastroenterol Hepatol 2018, Table 2 — points and odds ratios printed, read from the QUB green-OA manuscript because the publisher copy 403s | **CC BY-NC-ND** (verified, OpenAlex `best_oa_location`) | **contained** | Table 2 is a fact (Feist); the ND term matters only if the manuscript PDF itself were redistributed, which it is not |
| `albi` | liver · prognosis | J Clin Oncol 2015 — formula printed | Paper. MDCalc used only to cross-check | **clear** | n/a |
| `capra` | prostate · prognosis | J Urol 2005 Table 1 — points table printed | Paper. MDCalc used only to cross-check | **clear** | n/a |
| `cha2ds2_vasc` | cvd · prognosis | Chest 2010 — points table printed | Paper. MDCalc used only to cross-check | **clear** | n/a |

MDCalc's terms are genuinely restrictive: "All other uses, including commercial
use … must be approved by MDCalc", but the three models above take their point
tables from their own papers. MDCalc was a second opinion, and it earned its
keep: `mdcalc_extract.py` is what caught ALBI carrying `-0.0852` where the paper
prints `-0.085`. Cross-checking a number against a website is not taking
anything from that website.

### The clear eighteen

No restricted upstream. `hap` and `kunzmann` were on this list until
2026-08-17 and are not any more, see "The check itself was blind" below;
both rest on noncommercially-licensed articles and now sit in the restricted
table above, on the same Feist basis as `amap` and `atria_stroke_2013`.
Eighteen implemented models remain: `erspc_rc3`, `prevent`, `score2`,
`cvd_statin_benefit`, `grace`, `bcrat`, `predict_breast`,
`predict_breast_response`, `plcom2012`, `lipi`, `lipi_prognosis`,
`abc_method`, `rmi`, `roma`, `cervical_cin_risk`, `endpac`, `ang2010_rpa`, and
`pbcg_extended` (listed above).

Their reference implementations, where they have one, are permissive or
copyleft-but-not-redistributed:

| Source | Models | Licence | Verified by fetching |
|---|---|---|---|
| `WintonCentre/predictv30r` | `predict_breast` ×2 | **MIT + file LICENSE** | `DESCRIPTION` on `master`, v0.3.2 |
| `martingmayer/preventr` | `prevent` | **MIT + file LICENSE** | `DESCRIPTION` on `main`, v0.12.0 |
| CRAN `RiskScorescvd` | `score2` | **MIT + file LICENSE** | CRAN package page |
| CRAN `BCRA` | `bcrat` | **GPL-2 \| GPL-3** (expanded from GPL ≥ 2) | CRAN package page |
| `resplab/PLCOm2012` | `plcom2012` | **GPL-3** | `DESCRIPTION` on `master` |

GPL constrains *distribution*, not use. `BCRA` and `PLCOm2012` are fetched on
demand and never redistributed, which is what keeps them compatible with this
repo's Apache-2.0, and costs nothing, because they are verification tools
rather than dependencies. `NOTICE` states this correctly.

### Catalog and gap entries

Not implemented, so nothing is exposed today. Flagged here so the exposure is
known *before* someone implements them:

- `bcsc`, the BCSC source-code page states no licence and restricts the model
  to "populations of women or … population-level analyses"; individual-risk code
  must be requested from the consortium. **Do not implement without asking.**
- `msk_gastric_dss`, `msk_prostate_post_rp`, `hn_msk_catalog`,
  `colorectal_prognosis_catalog` — MSK-hosted, disclaimer excludes commercial
  use. Equations are figure-only in the papers, so implementing them means
  going to the tool. **Restricted.**
- `optum_lung_lasso`, `ohdsi-studies/lungCancerPrognostic` declares **Apache
  License 2.0** at line 33 of `DESCRIPTION` (verified). There is no root
  `LICENSE` file, so GitHub's API reports no licence, do not trust that signal.
  **Clear for commercial use with attribution.**
- `erspc_rc45`, `swop_rc1/2/5/6`. SWOP. The site states only
  "© 2026 · SWOP – The Prostate Cancer Research Foundation, Reeuwijk"; no terms
  of use page exists (`/disclaimer` returns 404). The RC3 constants used by
  `erspc_rc3` are independently printed in the World J Urol 2012 appendix, which
  is the citation used. **Unclear for the others; clear for RC3.**

---

## What is actually vendored into this repo, versus merely referenced

This is where the real exposure lives, and it is small and specific.

### Vendored: six files copy PolyForm-licensed code verbatim

Their own headers say so: "copied VERBATIM from
`github.com/ClevelandClinicQHS/riskcalc-website`". These reproduce the vendor's
`formula`/`predict.*` expressions so that parity is a comparison against the
vendor's arithmetic rather than a self-test:

    tests/parity/reference/pbcg_reference.R          213 lines
    tests/parity/reference/dutasteride_reference.R   894 lines
    tests/parity/reference/crc_pro_reference.R       123 lines
    tests/parity/reference/msk_gastric_reference.R    98 lines
    tests/parity/reference/msk_ovarian_reference.R    44 lines
    tests/parity/reference/msk_pancreatic_reference.R 63 lines
    tests/parity/reference/dutasteride_extract.py    182 lines   (extractor, not a copy)

**These files are present here.** They are
excluded from the public repo by `NONCOMMERCIAL_REFERENCE` in
`scripts/sync_public_repo.py`, which asserts they cannot reach it and fails
loudly rather than skipping silently. That control is real and it works, but it
governs *publication*, not *possession*. If the concern is a company holding
noncommercially-licensed code at all, syncing does not address it; deleting the
six files does, at the cost of being unable to regenerate fixtures without
re-obtaining the source.

Operationally this costs nothing: the test suite never runs them. Parity tests
assert against captured JSON (`crc_pro_cases.json` and siblings), which are
outputs.

### Not vendored: everything else

- `pbcg_extended_reference.R`. CC BY 4.0, the authors' own Additional file 2.
  Safe to keep, and its header says why.
- `bcrat_reference.R`, `predict_reference.R`, `score2_reference.R`, a dozen
  lines each of *our* code calling an installed package. Not copies.
- `collected/`, the five reference R packages are pinned in
  `collected/MANIFEST.yaml` and fetched on demand by
  `scripts/fetch_references.py`. Never mirrored to the public repo
  (`VENDORED` in the sync script, re-checked independently by
  `scripts/audit_public_repo.py`).
- `mdcalc_extract.py`, `msk_rectal_fetch.py`, `amap_fetch.py`,
  `swop_rc3_swf_extract.py`, `cervical_s1_extract.py`, our own scrapers. They
  contain no third-party code.
- `src/`, plain Python written from published equations. Nothing in `src/`
  imports, links against, or derives from any third-party implementation.

---

## Four things that need a decision

### 0. `cibula_arrm`: a new shape of question: derived from shipped data

and it is **not resolved**. It is listed first because it is
the only item here where the difficulty is not "whose licence covers this" but
"which of two different things did we take, and are they governed the same way".

The model has two halves and they came from two artifacts.

**The points schedule, the same question already answered elsewhere, and it is
clear.** Thirteen βs and thirteen integers, read from Table 2 of Cibula et al.,
Eur J Cancer 2021;158:111-122. Coefficients are measurements; Feist governs.
Same reading as `atria_stroke_2013`, `iota_adnex` and `amap`, all of which are
implemented on that basis and documented.

One correction to a natural assumption: **this article is not open access.**
Europe PMC reports `isOpenAccess: N` with `license: null`, and OpenAlex reports
`oa_status: green`, readable through a repository deposit, which grants no
reuse rights at all. Crossref lists only Elsevier's TDM user licence. It is on
PMC, and being on PMC is not a licence. Anyone extending this entry should not
reason from the PMC URL.

**The outcome grid, a genuinely different question, and open.** The band →
survival grid is Fig. 3, a graphic; only twelve of its numbers appear anywhere
as text. The rest were recovered by re-running the ESGO calculator's own
estimator over the **4,343-row patient-level derivation cohort that the
calculator ships to every browser that loads it**
(`data/data.min.js`, 56,985 bytes, sha256 `fc05acf9…`). The pages carry
"©2023 All rights reserved".

Why this is not the same question as the coefficient tables:

- What was taken is not a published table of results. It is a **derived
  statistic computed over someone else's dataset**. Feist protects the facts in
  a compilation; it does not speak to running an analysis over a compilation.
- The EU *sui generis* database right (Directive 96/9/EC) reaches exactly this,
  extraction of a substantial part of a database, regardless of whether the
  individual records are copyrightable. This is the same doctrine that keeps the
  dutasteride question open at item 2, but the fact pattern is worse: there the
  extracted items are coefficients, here they are patient records.
- The counter-argument is real and should be put to counsel rather than adopted
  here: the twelve published values are the parity target and they reproduce, so
  what the module ships is arguably a *reconstruction of the paper's own Fig. 3*
  rather than a use of the dataset. The dataset was the instrument, not the
  product.

**Interim position, recorded so it is not mistaken for a ruling:** treat the
twelve values Cibula et al print in prose as clear on the same basis as any
other published number, and treat the remaining grid entries as undetermined.
The registry entry's `license_basis` says exactly this, and
`src/cancerverse_baseline/cervical/prognosis/data/cibula_arrm_2021.json` carries the
same notice beside the artifact hashes. Nothing about this cell should be
described as settled until counsel has seen it.

Cheapest route to an actual answer, and it may make the whole question moot:
**ask the authors for the grid.** It is one table, they published the model to
be used, ESGO endorses it, and a reply would replace a derived artifact with a
supplied one.

### 1. `iota_adnex`: the one genuine unknown

The ADNEX coefficients come from Appendix D of Van Calster et al., BMJ
2014;349:g5920. I fetched the PMC copy: the article is **© Van Calster et al
2014, Creative Commons Attribution Non Commercial (CC BY-NC 3.0)**, which
"permits others to distribute, remix, adapt, build upon this work
non-commercially." Commercial use is explicitly not permitted.

The Feist argument that rescues the riskcalc.org models applies here too, 44
fitted coefficients in an appendix are measurements, and CC BY-NC governs the
article's expression, not the facts in it. On that reading `iota_adnex` is fine.

Two things make me unwilling to close it on that reading alone:

- ADNEX is not a dormant academic model. The IOTA calculators were withdrawn
  under the EU Medical Device Regulation and are being brought back as certified
  medical devices by **Gynaia**, a spin-out of KU Leuven, UZ Leuven and the IOTA
  consortium. There is an active commercial licensing regime around this
  specific model, and a licence a vendor grants elsewhere is not something a
  copyright analysis of the paper will surface.
- `src/cancerverse_baseline/ovarian/detection/adnex.py` is new and uncommitted. This is
  the cheapest possible moment to get an answer, before it is depended on.

The registry already carries `license: restricted` on this entry, so this is not
a surprise to the repo, but `docs/THIRD_PARTY_CODE.md` does not mention it, and
someone reading that document would conclude the library is clean apart from
riskcalc.org. **Take this to counsel.**

### 2. The dutasteride question: unchanged and still open

315 coefficients extracted mechanically from a PolyForm-licensed repository,
shipped as package data
(`src/cancerverse_baseline/prostate/response/data/dutasteride_coefficients.json`, an
installed-wheel artifact per `pyproject.toml`). Under US law the individual
numbers are facts. The EU *sui generis* database right (Directive 96/9/EC) can
protect a substantial extraction from a database even where the individual items
are not copyrightable, and whether 315 coefficients is a "substantial part" of
that repository is not a question this document can answer.

`docs/THIRD_PARTY_CODE.md` already flags this correctly. It remains the largest
single unresolved item, and there is no alternative source, the REDUCE trial
analyses never printed the equation.

### 3. The MSK fixture gap: not currently covered by anything

MSK's prediction-tool disclaimer, at
`https://www.mskcc.org/nomograms/disclaimer`, reads:

> Users agree to use the prediction tools for educational and/or research
> purposes only, and not for any commercial purposes, including the
> distribution, licensing, or sale of their content to any other person or
> entity, whether alone or in combination with other materials, or the
> incorporation of any of the prediction tools into any commercial product.

`docs/CONVENTIONS.md` characterises this accurately. Note that it is **not** on
`/legal-disclaimer` or `/terms-use` (which 404s), both of those were checked
first and neither carries the restriction.

`tests/parity/reference/msk_rectal_fetch.py` submits 12 constructed patients to
MSK's live tool and captures its outputs into `msk_rectal_cases.json`. Both
files sync to the public repository; neither is in `NONCOMMERCIAL_REFERENCE`.

This is a different shape of exposure from the riskcalc.org one, and the
existing machinery does not see it. Nothing was *copied*, the equation comes
from the JAMA Netw Open supplement, and running a tool does not make its output
a derivative work. But MSK's terms restrict the **purpose** of use, and a
company running their tool to validate a company product is a colourable
"commercial purpose" regardless of what copyright says about the outputs. The
same shape applies to `amap_fetch.py` against CUHK's calculator.

This is low severity, twelve queries against a public web form, but it is
unflagged, and "we did not think about it" is a worse answer than "we thought
about it and it is fine."

---

## The check itself was blind, and fixing it surfaced three more (now closed)

The noncommercial-source rule in
`scripts/audit_public_repo.py` §3e walked each registry entry's **top-level**
fields and tested `isinstance(v, str)`. Anything nested inside a sub-dict or a
list was never examined, and the fields most likely to record a vendor's terms
are exactly the nested ones (`canonical_impl.license`,
`equation_location.verified`, `upstream[].note`).

`cibula_arrm` walked straight through it. Its calculator's
"©2023 All rights reserved" sits in `canonical_impl.license`, a string inside a
dict, and the check that exists to catch precisely that reported clean. It
happened to be compliant anyway, which is the only reason this was a near miss
rather than a repeat of the ADNEX failure.

The scan now recurses. Running the fixed version flags **three implemented
models that were previously invisible and that have no written determination**:

| Model | Where the term is | What it says |
|---|---|---|
| `msk_rectal` | `canonical_impl.license` | `research-only-noncommercial` — MSK's hosted tool restricts use to education/research. The entry's own note argues the implementation follows the open-access paper, not the tool; that argument is not in `license_basis` where the rule looks for it. |
| `hap` | `equation_location.verified` | source article PMC4023407 is **CC BY-NC** |
| `kunzmann` | `equation_location.verified` | Queen's University Belfast green-OA accepted manuscript is **CC-BY-NC-ND** |

All three carry `license: open` with no `license_url`. That is the **exact
defect already corrected on `amap`**, one record answering the licence question
twice, with the audit believing the wrong half, so this is a known failure mode
recurring, not a new one.

None of the three is necessarily a problem: the Feist reading that covers the
other noncommercial sources very likely covers these too, and `msk_rectal`'s
note already contains the reasoning. What is missing is the reasoning *in the
field the rule reads*, plus the URL that states the licence. One
`license_basis` + `license_url` pair each.

**Closed 2026-08-17.** Left undocumented for three days on the reasoning that
this work was scoped to cervical cancer and these three are colorectal, liver
and oesophageal, flagged rather than fixed so the finding would not be lost.
Asked for directly and closed the same way `amap` was: `msk_rectal` keeps
`license: open` because its actual coefficient source (JAMA Netw Open) is
independently verified **CC BY**, fully open, no Feist argument even needed,
what changed is only that its separate tool-purpose exposure (see "the MSK
fixture gap" below) is now stated beside it rather than left implicit. `hap`
and `kunzmann` moved from `license: open` to `license: noncommercial_source`,
each with a `license_basis` citing an independently fetched confirmation
(Europe PMC for `hap`'s CC BY-NC; OpenAlex's `best_oa_location` for
`kunzmann`'s CC-BY-NC-ND, since the publisher copy 403s and there is no PMC
deposit) and a `license_url` pointing at that source. All three verdicts rest
on Feist v. Rural Telephone, the same basis already used for `atria_stroke_2013`
and `amap`: a points table and a set of odds ratios are facts, not
copyrightable expression. `test_noncommercial_basis_matches_the_licence_field`
in `tests/test_registry.py` is what caught the obvious next mistake, leaving
`license: open` while `license_basis` named a noncommercial source, the exact
defect this file already documents on `amap`, and forced the label change
before this could ship in the same contradictory state.

Note the audit script still cannot run end-to-end locally, it exits earlier
at `gh api` against the published repo, so this closure was verified by
running its §3e logic standalone, not by a clean full-script pass.

### A second gap, found the same day by the same near miss

The nested-scan fix above still would not have caught `moore_criteria`. Its
source article (PMC4470610) is not open access at all, no CC term, no
"PolyForm", no "all rights reserved" phrase anywhere in the entry, just a
closed, default-copyright article, so none of `nc_term`'s words appear
anywhere in it, nested or not. `cibula_arrm`, added the same day with the
identical `license: restricted` value, was ONLY caught because its
`canonical_impl` happens to quote the calculator's "All rights reserved"
notice. Two models in an identical licence position should not have their
audit outcome depend on which one happened to phrase its own notes with a
matching word.

Fixed by adding `m.get("license") in ("noncommercial_source", "restricted")`
as its own trigger, independent of the wording scan. Re-running the full check
confirms this was a near miss rather than a third undocumented model: both
`cibula_arrm` and `moore_criteria` already carry `license_basis` and
`license_url`, so the fix changes what the check watches, not the count of
undocumented entries, still the same three (`msk_rectal`, `hap`, `kunzmann`)
above. Recorded here so the pattern is visible: this is the second time in one
session the audit was strengthened only after a new entry happened to expose
its blind spot, which is a reason to treat the check as provisional rather than
as a settled gate.

## Discrepancies found in the existing documentation

The repo's third-party machinery is good and mostly accurate. Three things are
not:

1. **`docs/THIRD_PARTY_CODE.md` §1 says "Every other implemented model is
   unaffected."** Not true. `iota_adnex` rests on a CC BY-NC article, `amap` on
   a CC BY-NC-ND one, and `msk_rectal`'s fixture was captured from a tool whose
   terms exclude commercial use. None of the three is necessarily a problem;
   all three are omissions from a document whose purpose is to be complete.

2. **`docs/THIRD_PARTY_CODE.md` says of the 2018 PBCG: "retained in the working
   repository as catalog and does not ship."** It does ship.
   `src/cancerverse_baseline/prostate/detection/pbcg.py` exists, is inside
   `packages = ["src/cancerverse_baseline"]` in `pyproject.toml`, and is not excluded
   by the sync. By this repo's own reasoning that is *fine*, it is our Python
   written from facts, not vendor code, but the sentence as written is wrong,
   and it is the kind of wrong that gets quoted back later.

3. **`scripts/audit_public_repo.py` does not check the seven PolyForm files at
   all.** The sync script enforces `NONCOMMERCIAL_REFERENCE`; the audit script's
   six checks (private paths, vendored packages, PDFs, licence presence, NOTICE
   completeness, manifest URLs) do not include it. The audit exists precisely
   because "the sync would have caught it" is an assurance rather than an exit
   code, and it has a hole where the most consequential rule should be.

   **Still open on 2026-08-18, and the rule it should check has inverted.** It
   was "these seven must be ABSENT"; it is now "these seven must be PRESENT and
   each must carry its `LICENCE NOTICE`". The sync script enforces the new form;
   the audit still checks neither. Anyone adding this check should write the new
   rule, not the one this paragraph originally described.

---

## What to do next, cheapest first

1. **Add a seventh check to `scripts/audit_public_repo.py` for the seven
   PolyForm files.** Ten lines. It closes the gap between what the sync
   enforces and what the audit verifies. Write the CURRENT rule: each of the
   seven must be present in the published tree AND must contain its
   `LICENCE NOTICE` header. (Until 2026-08-18 the rule was the opposite,
   that they must be absent, so an implementer copying the old wording would
   build a check that fails on a compliant tree.)
2. **Fix the two inaccurate sentences in `docs/THIRD_PARTY_CODE.md`**, the
   "every other model is unaffected" claim and the "does not ship" claim.
3. **Verify the aMAP article licence.** ScienceDirect returned 403 to me; a
   browser or an institutional session will get it. If it is CC BY-NC-ND, add it
   to the same table as ADNEX.
4. **Decide on `msk_rectal_fetch.py` and `amap_fetch.py`.** Either accept the
   purpose-of-use question explicitly and write down why, or stop shipping the
   fetchers and keep only the captured fixtures. Note that the fixtures are the
   part the tests need; the fetchers are not.
5. **Take `iota_adnex` to counsel**, before `adnex.py` is committed and depended
   on. Ask specifically: does CC BY-NC on the development paper reach 44
   coefficients printed in its appendix, and does the Gynaia/KU Leuven licensing
   regime around ADNEX create a separate obligation?
6. **Take the dutasteride database-right question to counsel** in the same
   conversation. It is the same lawyer and the same hour.
7. **Write to Kattan's group** for the `msk_gastric`, `msk_ovarian`,
   `msk_pancreatic` coefficients and to the CRC-PRO authors for the baseline
   survival. If they answer, four models move from "contained" to "clear" and
   four of the six PolyForm files can be deleted outright. This is the only item
   that actually *removes* exposure rather than documenting it, and it is the
   slowest.

---

## What I verified by fetching, and what I did not

**Fetched and read today (2026-08-14):**

- `https://raw.githubusercontent.com/ClevelandClinicQHS/riskcalc-website/main/LICENSE`
  PolyForm Noncommercial License 1.0.0. Confirmed.
- `https://raw.githubusercontent.com/WintonCentre/predictv30r/master/DESCRIPTION`,
  `License: MIT + file LICENSE`, v0.3.2. (The `LICENSE` file itself is the
  bare R two-line stub: "2022 / University of Cambridge".)
- `https://raw.githubusercontent.com/martingmayer/preventr/main/DESCRIPTION`,
  `License: MIT + file LICENSE`, v0.12.0. (`LICENSE` stub: "YEAR: 2024 /
  COPYRIGHT HOLDER: preventr authors".)
- `https://cran.r-project.org/package=RiskScorescvd`, `MIT + file LICENSE`.
- `https://cran.r-project.org/package=BCRA`, `GPL-2 | GPL-3 [expanded from:
  GPL (≥ 2)]`.
- `https://raw.githubusercontent.com/resplab/PLCOm2012/master/DESCRIPTION`,
  `License: GPL-3`.
- `https://raw.githubusercontent.com/ohdsi-studies/lungCancerPrognostic/master/DESCRIPTION`,
  `License: Apache License 2.0`, reported at line 33.
- `https://www.mskcc.org/nomograms/disclaimer`, the commercial-use restriction,
  quoted verbatim above.
- `https://pmc.ncbi.nlm.nih.gov/articles/PMC4198550/` (ADNEX, BMJ 2014) —
  © Van Calster et al 2014, **CC BY-NC 3.0**, commercial use not permitted.
- `https://pmc.ncbi.nlm.nih.gov/articles/PMC9306143/` (Ankerst 2022, extended
  PBCG) — **CC BY 4.0**, commercial use permitted; Additional file 2 confirmed
  present, containing R code for all 1,024 models.
- `https://www.mdcalc.com/terms`: "All other uses, including commercial use …
  must be approved by MDCalc and will be subject to a license at the discretion
  of MDCalc."
- `https://tools.bcsc-scc.ucdavis.edu/BC5yearRisk_V2/sourcecode.htm`, no formal
  licence stated; use framed as population-level; individual-risk code must be
  requested.
- `https://www.prostatecancer-riskcalculator.com/`, copyright line only, no
  terms of use.

**Fetched and failed, which is itself a finding:**

- `https://www.mskcc.org/terms-use`. **404**.
- `https://www.prostatecancer-riskcalculator.com/disclaimer`. **404**. SWOP
  publishes no terms-of-use page.
- `https://www.mskcc.org/legal-disclaimer`, resolves, but carries only a
  medical disclaimer. The commercial restriction is **not** there; it is at
  `/nomograms/disclaimer`. Anyone checking the obvious URL would conclude MSK
  imposes no restriction, and would be wrong.
- `https://www.bmj.com/content/349/bmj.g5920`. **403**. The licence was
  obtained from the PMC copy instead.
- `https://www.sciencedirect.com/science/article/pii/S0168827820304797` (aMAP) —
  **403**. Its CC BY-NC-ND status is **unverified**; taken from the registry.

**Taken from the registry without independent verification:**

- The aMAP article licence (above).
- Which coefficients came from which paper section, for the twenty clear models.
  I checked `equation_source` and the module docstrings for consistency; I did
  not re-read the papers.
- `af_stroke_lr_2026` (catalog): `github.com/Jesse-cwl/Stroke-Prediction-in-AF`.
  Registry records the split, the *article* is CC BY-NC-ND, the *repository* is
  MIT, and notes that neither settles it, because the fitted coefficients are
  in neither. I did not fetch either. Nothing is implemented from it.
- The PolyForm licence on the `master` branch of `riskcalc-website`. I confirmed
  `main` only.
