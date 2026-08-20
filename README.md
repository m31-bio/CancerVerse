# CancerVerse

**Published clinical risk equations, reimplemented in Python, and independently verified.**

`42 models` · `12 diseases` · `33/36 cells` · `32/42 verified` · `Apache-2.0`

Clinical risk models are scattered across paywalled PDFs, supplement images, dead
Flash calculators and hosted web forms. This repository collects them as running,
tested Python, with the provenance of every coefficient recorded, and with evidence
that each implementation reproduces an independent source.

```python
import cancerverse_baseline as mb

mb.predict("albi", bilirubin_umol_l=20.0, albumin_g_l=40.0)
# {'score': -2.54, 'grade': 2, 'registry_id': 'albi',
#  'citation': 'Johnson PJ et al. J Clin Oncol. 2015;33(6):550-558', ...}

[m.id for m in mb.list_models(disease="liver")]
# ['amap', 'hap', 'albi']

mb.model_info("crc_pro").required_inputs
# ('male', 'age', 'ethnicity', 'weight_lb', 'height_in', ...)

# one patient record, several models, each given only what it accepts
mb.predict_many(["albi", "amap"], age=55, male=True, platelets=200,
                bilirubin_umol_l=15.0, albumin_g_l=42.0)
```

Every result carries the model's `scope`. Running a model is not the same as
being entitled to believe it. There is deliberately no "run everything"
convenience; see `cancerverse_baseline/api.py` for why.

---

> ### ⚠️ Not for clinical use
>
> This is a research artifact. It is **not a medical device**, has not been cleared or
> approved by any regulator, and must not be used to make decisions about a patient's
> care. Each model carries its own population and scope; applying one outside that
> scope produces a number that looks valid and is not.

---

## Coverage

**42 models across 12 diseases**, every disease asked the same
three questions. A dash means we have not implemented that cell. It does not mean the literature is empty: every one of the 36 cells has a published candidate, and each unfilled cell records the specific thing that blocks it, a missing intercept, an unreachable supplement, inputs we do not take, or a model that is not a closed-form equation at all.

### [The coverage table](https://m31-bio.github.io/CancerVerse/coverage.html)

One row per disease and question, with the flagship for each: where the model
applies and what it is misread as, the equation and where in the paper it sits,
how it was verified, and the command that re-runs that check.

It is `coverage.html` in this repository, served by GitHub Pages so that the
rendered page and the file cannot differ. The file view shows HTML as source,
which is why the link goes to the page.

**42 models across 12 diseases. 32 of 42 verified against a source we did not write.**

"Verified" means the output was compared against a source we did not write: a
published reference implementation, a second independent statement of the rule, the
paper's own worked example, or the vendor's live calculator.

The evidence is per model, in that page: **How it was verified** names the
route and the source, and **Re-run the check** gives the exact pytest command that
reproduces it. [`docs/MODEL_SPREADSHEET.xlsx`](docs/MODEL_SPREADSHEET.xlsx) carries
the same columns plus each model's scope and caveats.

## Install

```bash
uv sync --group dev      # creates .venv and installs everything
uv run pytest -q         # no network required
```

`uv` handles the Python version, the virtualenv and the lockfile in one
tool, and `uv.lock` pins every version.
This project uses pip, conda and requirements.txt nowhere at all.

Python 3.10+. The equations themselves are plain arithmetic
with no dependencies; the library needs **PyYAML** to read the registry,
which is where every model's provenance lives.

Models live under `src/cancerverse_baseline/<disease>/<question>/`, mirroring the table.

## What kind of models these are

42 models, 10 architecture families, every one a
**fixed-coefficient statistical model**, carrying a handful of numbers estimated once
and printed in a paper. No learned representations, no training at prediction time.

| Architecture | Models |
|---|---|
| Points table | 14 |
| Logistic regression | 12 |
| Survival (Cox) | 7 |
| Survival (parametric) | 2 |
| Linear score + cut-offs | 2 |
| Derived composition | 1 |
| Competing-risk absolute-risk model | 1 |
| Categorical rule | 1 |
| Multiplicative index | 1 |
| Decision tree | 1 |

## Licensing and provenance

The Python in `src/` is ours, under **Apache-2.0**.

The *models* are not. Each is a published equation belonging to its authors, cited in
the code, in `registry/models.yaml`, and in the table above. Where a hosted calculator
carries its own terms. MSK's nomograms are research-and-education, non-commercial,
**we implement from the open-access publication, not from the hosted tool**.

Third-party reference implementations used for verification are **not vendored here**
(two are GPL). `collected/MANIFEST.yaml` pins each by version, source and license;
`scripts/fetch_references.py` retrieves them on demand. Nothing in `src/` imports them.

`registry/models.yaml` is the single source of truth. This README, the spreadsheet and
the roadmap are all generated from it, and CI checks that the numbers agree, so a figure
here cannot drift from the repo.

## Contributing

Most valuable first:

1. **A correction.** If a coefficient here disagrees with its source, open an issue with
   the citation and the exact table. Nothing helps more.
2. **A model for an open cell.** See [`docs/ROADMAP.md`](docs/ROADMAP.md).
3. **A verification route** for anything we reached by a weaker one.

New models need: the equation source (specific table or figure), a registry row, an
implementation, unit tests, and a verification route. A model without one can still be
merged, but it is marked `not_checked` and the reason is recorded.
