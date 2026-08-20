# What a model must clear to enter the library

Five criteria. They were applied informally from the start, written down inside
two disease dossiers on 2026-08-14, and promoted here on 2026-08-18 after they
turned out to be the reason three cells are still empty, which is a decision
worth making in one place rather than three times in three `blocker` fields.

`test_gap_cells_name_what_they_rejected` enforces the record-keeping half: a
cell may be empty, but not silently.

---

## The criteria

1. **A complete equation.** Coefficients *and* the constant that turns them
   into a probability. Odds ratios alone rank patients and cannot state a risk.
2. **Inputs this library takes.** Routine clinical variables. Not radiomics
   features, not send-out biomarker panels, not contrast kinetics, not
   questionnaire items a health record does not hold.
3. **External validation, or a development cohort large enough to stand in for
   it.** Cross-validation on the development cohort is not external validation.
4. **A licence permitting the use we intend.** See `docs/COMMERCIAL_USE_AUDIT.md`
   and the per-model `license_basis` fields.
5. **For a model displacing an incumbent: a head-to-head comparison** against
   that incumbent on shared patients.

---

## Criterion 3 is what is actually blocking the library

The three empty cells, ovarian, pancreatic and head & neck **response**, each
have a named candidate that was found, read, and rejected. None was rejected on
performance:

| Cell | Candidate | AUC | Rejected on |
|---|---|---|---|
| ovarian · response | CRS 3 nomogram after NACT (Front Oncol 2020) | **0.82** | **3** — n=106, single centre, **24 events**, no external cohort |
| pancreatic · response | CEUS nomogram (Cancer Imaging 2024) | **0.852** | **2** — contrast-enhanced ultrasound kinetics |
| head & neck · response | Induction-chemo nomogram, hypopharynx (Front Oncol 2020) | **0.860** | **3** — 3-fold CV on one cohort, one subsite, one centre |

Every one of those AUCs is higher than several models this library already
ships. What excludes them is the evidence behind the number, not the number.

The ovarian candidate is the sharpest case: four predictors fitted on
twenty-four events, with the paper's own conclusion asking for the validation it
does not have. Admitting it would give the response axis a cell and give any
comparison against it no meaning.

---

## Why all three empty cells are on one axis

```
detection   12/12 diseases
prognosis   12/12
response     9/12
```

This is not chance. Treatment-response prediction has two structural
difficulties the other axes do not:

- **It often needs measurements taken during or after treatment**, post-NACT
  CA-125, contrast kinetics, interim imaging. Detection and prognosis are
  answered from what is already recorded.
- **Its cohorts are inherently smaller.** Only patients who received that
  treatment and have an assessable endpoint count. Four predictors on
  twenty-four events is the norm on this axis, not an outlier.

### Decided 2026-08-18: imaging stays out of scope, and these cells stay open

The question this section used to leave open, whether to widen criterion 2 for
the response axis, was put to the team and **answered: not for now.** Recorded
here because a decision written down as an open question gets re-debated, and
because the consequence is visible on the coverage page and should not look
like an oversight.

The consequence is precise: **ovarian, pancreatic and head & neck response
remain empty, and are expected to.** Every candidate added to that literature
since 2020 is imaging-derived. Re-searching on a schedule will keep returning
the same rejections.

What was weighed, because it is not one decision but three:

| Kind of imaging model | Example | Cost to adopt | What we would get |
|---|---|---|---|
| **Deep learning, weights published** | Sybil (lung, MIT + downloadable weights) | **low** — DICOM in, risk out, no feature engineering | a genuine published baseline we did not build |
| **Radiomics nomogram** | the ovarian and head & neck candidates | **very high** | coefficients sit on features whose values depend on segmentation, extractor version, preprocessing and scanner. Not reproducible as published — only retrainable |
| **Contrast readings** | the pancreatic CEUS nomogram | medium | three radiologist-reported numbers, if the study was performed |

The middle row is self-defeating and is the reason the answer is not simply
"yes": a radiomics model we retrain is **no longer an independent published
baseline**, it is our model built on someone's architecture. That is the same
trap as using published foundation-model weights, and it fails the purpose a
baseline serves.

**What would reopen this:** a decision to adopt the first row only, published
weights, run as published, no retraining, which is a narrower question than
"accept imaging" and does not touch the three cells above. It is live for lung,
where Sybil exists, and it needs to know what form the platform's imaging takes
(DICOM, report text, or neither).

Criterion 3, whether the evidence bar should differ by axis, was **not** put
to the team and remains genuinely open.

---

## Rejections are recorded, not remembered

A `status: gap` entry must name what was rejected and why. "No published
equation found" is not a finding; it is the absence of one, and this project has
been wrong with that sentence five separate times (see
`test_no_cell_is_recorded_as_never_published`).

Each gap entry therefore carries:

- the date the literature was searched
- the named candidates, with citations
- the criterion each one failed
- what would change the answer

The last of those is what makes a gap actionable. `pancreatic · response` will
not be unblocked by searching again; it will be unblocked by a decision about
criterion 2, or by someone publishing a routine-variable model.
