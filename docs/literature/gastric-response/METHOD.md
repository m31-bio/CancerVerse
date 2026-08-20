# How this shortlist was built

Written down so the next empty cell can be done the same way, and so anyone can
tell which parts of the table are facts and which are judgements.

---

## The order of operations

**1 · Search wide before ranking anything.** The target was 12–20 papers; 28
came back. This matters because the gastric cell had previously been recorded as
having *no published equation*, twice, by searches that stopped early. A search
that stops when it finds a plausible answer will keep finding the same wrong
answer.

Scope fixed in advance, in `candidates.yaml` under `meta.endpoint_scope`:
pathological complete response, major/good pathological response, and
radiological (RECIST) response, after neoadjuvant chemotherapy,
chemoradiotherapy or chemo-immunotherapy, in gastric or GEJ adenocarcinoma.
Fixing the scope first is what stops the shortlist from drifting toward whatever
happens to be well indexed.

**2 · Record what a human had to read the paper to know.** Per paper: endpoint,
predictors, **input modality**, sample sizes, whether validation was internal or
external, discrimination, and **what the paper actually prints**, a complete
model, coefficients without an intercept, an integer points system, odds ratios,
or a picture. These are hand-written in `candidates.yaml` and are never inferred
by a script.

Two of those fields do nearly all the work:

- **`inputs`** decides whether the model is implementable here at all. A CT
  radiomics model with a magnificent AUC is not a candidate for a library whose
  inputs are clinical values.
- **`usable`** decides whether it can emit a probability. Coefficients without
  an intercept rank patients; they do not produce a number. This is not a
  technicality, it is what held the colorectal cell for three months.

**3 · Add the part that is a lookup, by script.** `scripts/rank_literature.py`
resolves each paper in OpenAlex by DOI, falling back to PMID, and adds citation
count, publication year, journal, and citations per year. Re-runnable:

    python scripts/rank_literature.py docs/literature/gastric-response --write

**4 · Go back to the sources for the finalists.** For the top five, the exact
table each parameter sits in was located and the numbers read out verbatim, into
[`PROVENANCE.md`](PROVENANCE.md). This step overturned three things the
shortlist had recorded from abstracts, see below. **Do not skip it.** An
abstract is a claim about a paper, not the paper.

---

## What is ranked, and what deliberately is not

Papers are ordered by **citations per year**, and that ordering answers exactly
one question: *which of these has been read*. On a shortlist mixing a 2018 paper
with a 2026 one, raw citation count is mostly an age measurement, so per-year is
the fairer of the two. It still flatters recent work in fast-moving areas, and
imaging is a fast-moving area.

**It is not a quality score and must not be read as one.** In this cell the
citation ranking and the usability ranking come out close to *inverted*: the top
of the list is CT radiomics and deep learning that withhold their weights, and
the implementable papers sit in the bottom half. Read the ranking beside the
`inputs` and `usable` columns or it will point you at the wrong paper.

### On impact factor

Clarivate's JIF is proprietary and is **not fetched**. The tempting substitute,
OpenAlex's `2yr_mean_citedness`, is unusable for ranking, `fetch_impact.py`
documents the failure in detail. Journals that deposit large volumes of
conference abstracts have the metric diluted to nonsense (Journal of Clinical
Oncology: 174,155 works, 2-year mean 1.65, against a real JIF near 45), while
journals that deposit few come out plausible. Inconsistently wrong is worse than
absent, because it looks like a number.

So `candidates.yaml` carries a `jif` field that is null everywhere. If a real
JIF is wanted it has to be typed in by hand from Journal Citation Reports, which
needs an institutional subscription. The ranking never guesses it.

**In this cell it would not have helped anyway.** The two finalists. PMID
33937020 and PMID 41883960, are in *the same journal*, Frontiers in Oncology.
Impact factor cannot separate them, and neither can citations: the runner-up was
published months ago and has one. When the shortlist narrows to papers of
similar standing, the bibliometrics stop discriminating and the decision returns
to what the papers actually contain. Which is the right place for it.

---

## Four things the re-read overturned

Kept here rather than quietly corrected, because the failure mode is the point:
each was a claim taken from an abstract that the full text does not support.

1. **PMID 40755776 is not a seven-centre external validation.** The patients came
   from seven centres and were then randomly split 7:3. The paper itself calls
   the result an external validation cohort. It is internal, which is why its
   validation AUC (0.934) exceeds its training AUC (0.862), a pattern that
   should always prompt a second look.

2. **PMID 36631788's external cohort does not appear in the paper.** It was on
   the shortlist as the strongest clinical-only design because of an external
   C-index of 0.760 on n=108. Table 1 contains only a training set of 307 and a
   validation set of 153, from a `set.seed` random split of 460. The cohort
   behind the 0.760 has no stated size and no stated source.

3. **PMID 33937020 has no nomogram figure.** It had been recorded as a points
   system whose probability axis was locked in a figure. There is no such
   figure, the paper's three figures are two Kaplan–Meier panels and a ROC
   curve. The mapping was never estimated, so it is absent rather than
   inaccessible. That distinction decides whether there is a task to hand to a
   human, and here there is not.

4. **PMID 33937020's "external" cohort is at the same hospital.** Its numbers
   are all correct, 202 / 102 / 124 and AUC 0.84 / 0.73 / 0.82 survive the
   check. But every author is at Shanghai Ruijin, only one hospital is named,
   and the paper's own limitations section says "This was a single-center
   clinical study". The 124 were enrolled prospectively in a later time window,
   after the model was locked. That is prospective *temporal* validation, which
   is a real and useful thing, the chemotherapy regimens changed between the
   eras, but it is not what "external" is normally taken to mean.

Three of those four are the same error: **a validation claim taken from an
abstract that the cohort description does not support.** Whatever else this
process does, it has to include reading the Methods section of every finalist.

---

## The rule that came out of it

Sort by what the paper *prints*, then by evidence, then by citations. Never the
other way round. A model that cannot be computed is not a candidate at any
citation count, and this shortlist is the clearest available demonstration:
the single best-evidenced paper in it. PMID 39637859, 1,208 development
patients, two external cohorts, a prospective cohort, and the only public code
repository, is unusable here, because it takes CT volumes and whole-slide
pathology rather than variables.
