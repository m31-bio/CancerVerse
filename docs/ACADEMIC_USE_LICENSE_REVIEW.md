# Re-reviewing third-party licences under an academic-use posture

Written 2026-08-17, after M31 stated the project's use is academic research
only. This document does not replace `docs/COMMERCIAL_USE_AUDIT.md` or
`docs/THIRD_PARTY_CODE.md`, it re-reads every restriction those documents
found, against every source's ACTUAL text, fetched fresh today rather than
recalled from either document. Where a fresh fetch disagrees with what those
documents said, that is noted explicitly.

**The premise every verdict below rests on:** M31 has stated that the
project's use is academic research only. That is taken here as the operating
premise and is not re-argued, but it is stated in one place, at the top,
because if it ever stops being true then most of the verdicts below revert to
what `docs/COMMERCIAL_USE_AUDIT.md` already says, and a reader needs to know
which single fact to check rather than re-reading every row.

**Nothing here is legal advice.** Every source quoted below was fetched
2026-08-17 and the URL is given so it can be re-checked.

**The one structural finding, stated before the details.** Almost every
restriction in this library is gated on **purpose**, it names what the work
may be used FOR, and those all resolve the same way once the purpose is
academic research: they permit it, in their own words. One restriction is
gated on an **act**: it forbids a specific thing however worthy the purpose.
Reading every restriction as "now cleared" would be exactly as wrong as the
old document's habit of reading every restriction as blocking, and QCancer is
the case that proves the distinction is real rather than pedantic, it grants
research use in one sentence and forbids software testing in the next. Three
other conditions (the ND clause, EHRSHOT credentialing, ESGO's "personal"
wording) also survive the shift untouched.

Summary of where each source lands, detailed below:

| Verdict | Sources |
|---|---|
| **Clears** — permitted by the source's own words | riskcalc.org (PolyForm) · the five CC BY-NC / CC BY-NC-ND articles · MDCalc · MSK's hosted tool |
| **Clears, with a non-purpose condition remaining** | ESGO ("personal" is narrower than "academic") · foundation-model weights (credentialing, ND) |
| **Still barred** | QCancer, and not for a commercial reason |

---

## The one thing that does not change, stated first because it is the thing
## most likely to get skipped over

**This project's own outbound licence is Apache-2.0, and that is not
changing.** Apache-2.0 grants anyone who receives this repository a
permissive, commercial-use-included licence to *this project's own code*.
That grant is unaffected by what M31 itself intends to do with the project —
Apache-2.0 does not become narrower because the grantor's own use is academic.

So there are two separate questions, and this document is about only the
first:

1. **Is M31's own use of a restricted third-party source compliant with that
   source's terms?** This is what changes under an academic-use posture, and
   it is what this document re-examines.
2. **What can someone who receives this Apache-2.0 repository do with it?**
   Unaffected by M31's intent. If the repository is ever distributed to
   someone who is not bound by the same academic/research characterization,
   that recipient has a full commercial licence to M31's own code from
   M31, and separately inherits whatever obligations attach to the
   third-party material still inside it. The academic-use framing answers
   question 1. It answers question 2 only insofar as it also constrains WHO
   the repository is actually given to and on what terms, which is a
   distribution decision, not a licence-text question, and this document
   cannot make it.

---

## Sources actually re-checked today, verbatim, with the fetch method

### PolyForm Noncommercial 1.0.0: the riskcalc.org group

Fetched from `https://polyformproject.org/licenses/noncommercial/1.0.0`,
2026-08-17. The operative clauses:

> **Noncommercial Purposes.** Any noncommercial purpose is a permitted
> purpose.
>
> **Personal Uses.** Personal use for research, experiment, and testing for
> the benefit of public knowledge, personal study, private entertainment,
> hobby projects, amateur pursuits, or religious observance, without any
> anticipated commercial application, is use for a permitted purpose.
>
> **Noncommercial Organizations.** Use by any charitable organization,
> educational institution, public research organization, public safety or
> health organization, environmental protection organization, or government
> institution is use for a permitted purpose regardless of the source of
> funding or obligations resulting from the funding.

**This is not what `docs/THIRD_PARTY_CODE.md` currently says the licence
says.** That document states flatly: "A company repository is not a
noncommercial purpose." That sentence tests the wrong thing. PolyForm's gate
is **purpose**, not **entity type**: "any noncommercial purpose is a
permitted purpose" carries no exception for who is doing the using. The
"Noncommercial Organizations" clause is a separate, additional safe harbor for
specific entity types (and M31, a company, does not obviously fall in that
list regardless of its research posture), but it is not the only route to a
permitted purpose, and the general clause above it is the one that actually
governs a company's noncommercial use.

**What this changes, if M31's actual use of the six riskcalc.org-derived
files qualifies as a noncommercial purpose:** `crc_pro`, `dutasteride`,
`msk_gastric`, `msk_ovarian`, `msk_pancreatic`, and the retired `pbcg` were all
quarantined from the public mirror specifically because `docs/THIRD_PARTY_CODE.md`
concluded a company's use could not be noncommercial. If that conclusion was
wrong, because the actual test is purpose, not entity, then the quarantine's
premise needs re-examination, not just its footnote.

> **** M31 confirmed the use is academic research only and
> decided to reinstate the files. They ship, each under its own PolyForm notice
> rather than under this repository's licence. See item 1 under "What follows
> from this" at the end of this document.

**What this does NOT resolve on its own:** whether M31's specific,
present-day use of these six files, holding fitted coefficients (already
covered separately by Feist, unaffected either way) and keeping the six
verbatim R reference scripts, is genuinely "a
noncommercial purpose... without any anticipated commercial application" in
the sense PolyForm means. Research conducted by a company that will feed a
future commercial product sits in a genuinely unsettled zone under language
like this. **This is the fact this document cannot supply.**

### The dutasteride database-right question: now has a directly relevant exception

`docs/THIRD_PARTY_CODE.md` flags the 315 dutasteride coefficients as resting
on an unresolved question: whether extracting them is a "substantial part" of
riskcalc.org's database under the EU *sui generis* database right (Directive
96/9/EC), which can protect a database even where individual facts are not
copyrightable.

Fetched today from `https://www.legislation.gov.uk/uksi/1997/3032/regulation/20`,
the UK's Copyright and Rights in Database Regulations 1997, regulation 20,
which implements Article 9 of Directive 96/9/EC:

> Database right in a database which has been made available to the public in
> any manner is not infringed by fair dealing with a substantial part of its
> contents if—
> (a) that part is extracted from the database by a person who is apart from
> this paragraph a lawful user of the database,
> (b) it is extracted **for the purpose of illustration for teaching or
> research and not for any commercial purpose**, and
> (c) the source is indicated.

This is a research/teaching exception written directly into database-right
law, not something inferred from a general-purpose noncommercial clause. Three
conditions, and this project already satisfies the shape of two without any
new work: (a) riskcalc.org's calculators are public and accessed by ordinary
lawful means, and (c) every registry entry names its source in more detail
than this exception requires. **Condition (b): "not for any commercial
purpose", is exactly the same open business-fact question as above, applied
to a specifically dutasteride-shaped legal question rather than a general one.**

The same exception, on the same reasoning, bears on `cibula_arrm`'s derived
outcome grid, see the ESGO section below, where it is the more load-bearing
of the two questions rather than a secondary note.

### MDCalc: albi, capra, cha2ds2_vasc

Fetched from `https://www.mdcalc.com/terms`, 2026-08-17 (the URL in
`docs/COMMERCIAL_USE_AUDIT.md`, `mdcalc.com/about/terms`, 404s; this is the
current path):

> You may view the Website Content from the Services, solely for your
> **clinical or academic use**, to generate individual results...
>
> No license is required for **noncommercial use** of the ratings and/or
> Website Content. All other uses, including commercial use (including, but
> not limited to, using or embedding ratings into any other product or
> service, for any purpose) must be approved by MDCalc...

This is the cleanest source in the whole review. MDCalc names "academic use"
explicitly, as its own category, requiring no licence. `albi`, `capra`, and
`cha2ds2_vasc` only ever used MDCalc to cross-check point values already
printed in their own source papers, already the `clear` verdict in
`docs/COMMERCIAL_USE_AUDIT.md`, and now resting on the strongest textual
footing of anything in either document. **No open question here.**

### MSK's hosted rectal-cancer calculator: msk_rectal

Previously verified text, re-confirmed unchanged today at
`https://www.mskcc.org/nomograms/disclaimer`:

> Users agree to use the prediction tools for **educational and/or research
> purposes only**, and not for any commercial purposes...

`docs/COMMERCIAL_USE_AUDIT.md` calls the exposure here "low severity but
unflagged": twelve verification queries against MSK's tool, used to settle
which of two internally-inconsistent published artifacts (an eFigure vs. an
eTable in the same JAMA Netw Open supplement) the deployed model actually
matches, not to obtain content the open-access paper does not already
provide. If that activity is what a reasonable reading of "educational and/or
research purposes" covers, and settling an internal inconsistency in a
published model, for the purpose of implementing that model correctly, reads
as squarely inside that description — **this gap closes.** The remaining
question is the same business-fact one as above, asked here in its most
favorable form: this specific use already looks like research on its face,
independent of M31's broader posture.

### The CUHK MDAC aMAP calculator: amap's verification queries

Fetched from `https://mdac.cuhk.edu.hk/disclaimer`, 2026-08-17. In full:

> The contents of the CUHK website is subject to change without notice. The
> University accepts no liability for any loss or damage howsoever arising
> from any use or misuse of or reliance on any information on this website.

No purpose restriction of any kind, no "noncommercial", no "research", no
"commercial use requires a licence." This is a liability disclaimer, not a use
licence. **Unaffected by the academic-use question either way**, and was
already low-risk: `amap`'s coefficients come from the CC BY-NC-ND paper
(covered separately by Feist), and CUHK's tool is used only to cross-check
outputs, the same shape as MDCalc.

### ESGO's calculator terms: cibula_arrm's derived outcome grid

This is the item `docs/COMMERCIAL_USE_AUDIT.md` explicitly refused to call
resolved, and it is the one where today's fetch matters most.

The calculator page's own footer links to
`https://www.esgo.org/terms-and-conditions`, fetched today:

> [Website content is] protected by intellectual property rights, including,
> but not limited to, copyright, trade mark rights and **database rights**.
> All such rights are reserved. You may store on your personal computer or
> print copies of extracts from these pages for your **personal and
> non-commercial use only**... You must not use any part of the materials on
> our Site for **commercial purposes** without obtaining a licence to do so
> from us or our licensors.

Two things this confirms and one thing it does not resolve:

- **ESGO is explicitly asserting database rights over this content.** That
  was this project's own hypothesis when the outcome grid was first flagged
  as derived-from-shipped-data; the site's own terms confirm the right being
  asserted is exactly the one in question, not a copyright-on-expression
  argument that Feist would answer.
- **The UK/EU database-right research exception (quoted above under
  dutasteride) reaches this directly and by design**, it exists specifically
  for extracting from a database "for the purpose of illustration for
  teaching or research and not for any commercial purpose," which is a closer
  textual match to what happened here (re-running a published estimator over
  a cohort the calculator ships, to recover a result the source paper only
  drew as a figure) than almost anything else in this review.
- **What ESGO's own terms do NOT clearly cover is organizational research
  use**, because the phrase is "personal and non-commercial use," and
  "personal" is narrower language than PolyForm's or MDCalc's. Whether a
  company's research team extracting data for a published-model
  reimplementation counts as "personal" use under ESGO's terms is a real
  question this document cannot answer by reading the sentence again.

**Net effect:** the database-right theory that would resolve this, the UK/EU
teaching-or-research exception, is now backed by verified statutory text
rather than by an unresolved reference to "the EU sui generis database right"
in general terms. That is real progress. It is still gated on the same
business fact as everything else in this document, and ESGO's own "personal"
wording is a second, independent reason not to treat this as settled. The
cheapest route already on record in `docs/diseases/cervical/README.md`,
asking Cibula's group directly for the outcome grid, remains the cleanest way
to make this question moot rather than argued.

### QCancer: the one that does NOT clear, and the reason matters

Fetched from `https://qcancer.org/10yr/`, 2026-08-17. The whole notice, because
the two halves have to be read against each other:

> ALL RIGHTS RESERVED. Materials on this web site are protected by copyright
> law. Access to the materials on this web site for the **sole purpose of
> personal educational and research use only**... Any unauthorised use or
> distribution for commercial purposes is expressly forbidden... **In
> particular, use of this website as a web service, or to develop or test
> software, is expressly forbidden.**

Read the first sentence alone and QCancer looks like the easiest clearance in
this document, it names educational and research use as the permitted
purpose, which is exactly M31's stated posture. Read the last sentence and it
is the only source here that stays barred.

**The ban is on the act, not the purpose.** "To develop or test software" is
forbidden however academic the reason. Checking one of our implementations
against QCancer's calculator is software testing by the plainest reading of
those words, so the activity this project would actually want it for is the
specific activity the notice singles out.

Two consequences worth stating because they are counter-intuitive:

- **A research framing does not reach this**, and neither would being a
  university. This restriction would bar an academic group exactly as it bars
  M31, which is the tell that it is a different kind of clause from everything
  else in this review.
- **There is nothing to ask for that a "we're academic now" email would fix.**
  Every other blocked item here is either resolved by the purpose shift or is
  a process (credentialing, a licence request). This one needs a negotiated
  licence from Endeavour Predict CIC, which is a materially different request.

QCancer is not used and was never implemented, so nothing has to change today.
It is written up at this length because it is the counter-example that keeps
the rest of this document honest: the shift to academic use is not a universal
solvent.

### Foundation-model weights: from barred to obtainable

Not currently used, and the plan does not depend on them, but their status
changed enough to be worth recording.

**Delphi-2M**, fetched from the project's own README badges,
`https://raw.githubusercontent.com/gerstung-lab/delphi/main/README.md`:
Code **MIT**, Weights **CC BY-NC-ND 4.0**. The NC half clears under academic
research use. **The ND half does not**, it bars distributing a modified copy
of the licensed work, which would block releasing fine-tuned weights however
the tuning was done. Using them for internal research is a different act from
publishing a derivative, and only the first clears.

**CLMBR-T-base and MOTOR**, fetched from
`https://huggingface.co/StanfordShahLab/clmbr-t-base`: licensed
`cc-by-nc-4.0`, plus agreement to the EHRSHOT Credentialed Health Data
License and "a verified CITI training certificate." That licence
(`https://shahlab.stanford.edu/ehrshot_license`) states Stanford's intent to
make data available "**for research and educational purposes** to qualified
requestors," and binds the licensee to use the data "for the sole purpose of
lawful use in **scientific research** and no other."

So academic research is not merely permitted here, it is the *only* permitted
purpose, a stronger fit than anything else in this review. What remains is
**access-gated, not purpose-gated**: CITI certification and a signed
agreement. That is a process with a cost, not a prohibition, and it converts
these weights from "cannot use" to "can use if we do the paperwork."

Note this is a contract as well as a copyright licence. Breaching it is a
data-use-agreement problem with Stanford, which is a different kind of
exposure from copyright infringement and does not go away because the
underlying content might be facts.

**The plan does not change.** Retraining the permissive training code on our
own data was chosen because published weights confound architecture with
pretraining corpus, making a like-for-like comparison impossible, a
scientific reason, not a licensing one. That reason survives intact.

---

## What changes and what does not, at a glance

| Source | Models | Changed by today's fetch? |
|---|---|---|
| Feist facts (CC BY-NC / CC BY-NC-ND articles) | `amap`, `atria_stroke_2013`, `hap`, `iota_adnex`, `kunzmann` | No — already clear regardless of use posture. If M31's use is confirmed noncommercial, these articles' own CC BY-NC terms would ALSO permit using the full text, not just the facts Feist protects — a stronger footing than before, but not a change in verdict. |
| GPL/MIT reference packages | `bcrat` (BCRA), `plcom2012`, `score2`, `predict_breast`×2, `prevent` | No — distribution-based reasoning (fetched on demand, never redistributed) is orthogonal to commercial-vs-academic use. |
| PolyForm Noncommercial (riskcalc.org) | `crc_pro`, `dutasteride`, `msk_gastric`, `msk_ovarian`, `msk_pancreatic` | **Yes, materially.** The licence's own gate is purpose, not entity — `docs/THIRD_PARTY_CODE.md`'s "a company repository is not a noncommercial purpose" overstates what the text says. Whether M31's actual use qualifies as noncommercial purpose is the open business fact. |
| MDCalc | `albi`, `capra`, `cha2ds2_vasc` | Strengthened, not changed — already clear, now on an explicit "academic use" clause. |
| MSK hosted tool | `msk_rectal` | **Yes, substantially closes the previously-flagged gap** — its own disclaimer names "educational and/or research purposes," and the actual use (settling an internal inconsistency) reads as squarely inside that. |
| CUHK MDAC calculator | `amap` (verification only) | No — no purpose restriction exists to be affected either way. |
| ESGO calculator | `cibula_arrm` (derived outcome grid) | **Yes, but not resolved.** The UK/EU database-right research exception now has verified statutory text behind it and reaches this case well; ESGO's own "personal and non-commercial" wording is narrower than that exception and does not obviously cover organizational research use. |
| Apache-2.0 vendor sources | `optum_lung_lasso` | No — already fully permissive. |
| No stated licence, dead tool | `erspc_rc3` | No — already low-risk; constants also printed in the cited paper. |
| Foundation-model weights | Delphi-2M, CLMBR-T-base, MOTOR (none used) | **Yes — from barred to obtainable.** Academic research is the named permitted purpose for all three; EHRSHOT makes it the *only* one. Conditions remain: CITI certification, signed agreements, and ND on Delphi-2M's weights bars releasing a tuned version. |
| QCancer | none (not implemented) | **No — still barred, and not for a commercial reason.** Its notice permits "personal educational and research use" and separately forbids using the site "to develop or test software," which is the act a parity check performs. |

---

## What follows from this, and what is still open

**The premise is settled and is not re-argued here.** M31 has stated the use is
academic research only. Every "clears" verdict above follows from that plus the
source's own words.

**Three things follow immediately.**

1. ~~**The six quarantined reference scripts can be reconsidered.**~~
   **They are reinstated.** The `crc_pro`, `pbcg`,
   `dutasteride`, `msk_gastric`, `msk_ovarian` and `msk_pancreatic` reference
   scripts (plus `dutasteride_extract.py`, seven files in all) were withheld on
   the reasoning in `docs/THIRD_PARTY_CODE.md` that "a company repository is not
   a noncommercial purpose", which tested the wrong thing. They now ship, and
   the ability to regenerate every fixture from the vendor's own arithmetic is
   restored; that is what made those parity checks independent rather than a
   second transcription by us.
   **What the decision did not dissolve, and how it is handled:** purpose
   permits the copying, but it does not let the copy travel under this
   repository's Apache-2.0 licence. Each file carries a `LICENCE NOTICE` header
   saying so, `NOTICE` lists all seven, and `scripts/sync_public_repo.py`
   asserts both presence and notice, the absence rule inverted rather than
   lapsed. Reinstating this also surfaced an older gap: `LICENSE` and `NOTICE`
   had never been in the sync list at all, so the file explaining the mixed
   licensing would not have shipped with the files it explains. Both are
   mirrored now.
2. **Two legal questions became narrower rather than remaining open-ended.**
   The dutasteride extraction and the ESGO outcome grid were both filed as "the
   EU sui generis database right might reach this, and we cannot say." They are
   now "does the reg. 20 research exception apply", which has three stated
   conditions, two of which are already met (lawful access; source indicated in
   more detail than required). That is a question counsel can answer in one
   opinion covering both.
3. **Foundation-model weights move onto the table** if they are ever wanted,
   see above. The retraining plan does not change, for scientific reasons.

**What is still genuinely open, and should not be reported as resolved.**

- **ESGO's own wording is "personal and non-commercial use."** "Personal" is
  narrower than "academic," and whether an organisation's research team fits
  it is not answerable by re-reading the sentence. The statutory research
  exception is the stronger argument here; the contractual term is the weaker
  one. The cheapest fix remains the one already on record in
  `docs/diseases/cervical/README.md`: ask Cibula's group for the outcome grid
  directly and make the question moot.
- **QCancer stays barred**, and no framing of purpose changes that.
- **The Apache-2.0 distribution question is untouched.** This document is
  about what M31 may do with third-party sources. It says nothing about what a
  recipient of this Apache-2.0 repository may do. Apache-2.0 does not narrow
  because the grantor's own use is academic, so anyone who receives this gets
  full commercial rights to M31's own code and separately inherits whatever
  attaches to third-party material still inside it. **Who this repository is
  given to, and on what terms, is a distribution decision that no licence-text
  reading can make.**

Deck: `slides/license-academic-use-2026-08-17.pptx`, built by
`scripts/build_license_audit_slide.py`.
