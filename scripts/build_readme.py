#!/usr/bin/env python3
"""Generate README.md, including the master coverage table, from the registry.

The README's headline numbers and its big table are the things most likely to be
read, quoted, and to go stale. Nothing here is typed by hand.

    python scripts/build_readme.py [output_path]
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "models.yaml"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_table import (  # noqa: E402
    AXES,
    AXIS_LABEL,
    COLUMNS,
    DISEASE_LABEL,
    GAP_CAPTION,
    GAP_CELL_LABEL,
    build_rows,
    feature_top_predictors,
    grouped,
)


def _flat(x) -> str:
    return " ".join(str(x or "").split())


def _cell(text: str, limit: int | None = None) -> str:
    """Escape for a markdown table cell."""
    t = _flat(text).replace("|", "\\|")
    if limit and len(t) > limit:
        t = t[: limit - 1].rsplit(" ", 1)[0] + "…"
    return t or "—"


def _verified_how(m: dict) -> str:
    """One clause naming the route, not the whole essay."""
    note = _flat(m.get("parity_note"))
    if not note:
        return "—"
    # first sentence, which is always the route in this registry
    first = note.split(". ")[0]
    if len(first) < 40 and ". " in note:
        first = ". ".join(note.split(". ")[:2])
    return _cell(first, 300)


def _esc(s: str) -> str:
    """Escape for HTML, keeping the line breaks a displayed equation needs."""
    import html

    return html.escape(s)


def _render(col: str, r: dict) -> str:
    """One cell. Links are rendered as links — a bare URL in a table is a URL
    the reader has to copy."""
    if col == "Core formula":
        raw = str(r.get(col, "")).rstrip()
        return f"<pre>{_esc(raw)}</pre>" if raw else "&mdash;"
    v = _cell(r.get(col, ""))
    if v == "—" and col in ("Public repository", "Top predictor"):
        return "&mdash;"
    if col == "Public repository":
        return f'<a href="{v}">{v.split("/")[-1] or "repo"}</a>'
    if col == "Source":
        label = v.replace("https://doi.org/", "doi:").replace(
            "https://pubmed.ncbi.nlm.nih.gov/", "PMID ").rstrip("/")
        return f'<a href="{v}">{label}</a>'
    if col == "Re-run the check":
        return f"<code>{v}</code>" if v != "—" else "&mdash;"
    if col == "Year":
        return f"<b>{v}</b>"
    if col in ("Discrimination (AUC / C-index)", "Developed on"):
        return f"<em>{v}</em>" if v.startswith("we have not read") or v.endswith("not recorded yet") else v
    if col == "Model":
        return f"<b>{v}</b>"
    if col == "Architecture":
        return f"<b>{v}</b>"
    if col == "Verified?":
        return "<b>Yes</b>" if r["Verified?"] == "Yes" else "No"
    return v


def _repro(m: dict) -> str:
    """Where to go and re-run the check. A claim with no address is not evidence."""
    ev = m.get("evidence") or {}
    if not ev.get("test"):
        return ""
    fn = ev.get("test_function")
    bits = [f'<code>pytest {ev["test"]}' + (f"::{fn}" if fn else "") + "</code>"]
    if ev.get("script"):
        bits.append(f'data captured by <code>{ev["script"]}</code>')
    return "<br><br>" + "<br>".join(bits)


def _requires_python() -> str:
    """The supported version, read from pyproject so it cannot drift.

    It already had: the README claimed 3.11+ while the packaging metadata said
    >=3.10.
    """
    import re

    text = (ROOT / "pyproject.toml").read_text()
    m = re.search(r'requires-python\s*=\s*"([^"]+)"', text)
    spec = m.group(1) if m else ">=3.10"
    return spec.replace(">=", "") + "+"


def build(models: list[dict]) -> str:
    impl = [m for m in models if m.get("status") == "implemented"]
    checked = [m for m in impl if m.get("parity_status") in {"checked", "matched"}]
    fams = Counter(m.get("architecture_family") for m in impl)

    rows = build_rows(models, feature_top_predictors())
    by = grouped(rows)

    L: list[str] = []
    A = L.append

    A("# CancerVerse")
    A("")
    A("**Published clinical risk equations, reimplemented in Python — and independently verified.**")
    A("")
    # The cell count used to live only in docs/MODEL_SOURCE_TABLE.md, which was
    # deleted as redundant: every other figure in its summary was already here,
    # usually in better form. This one was not, so it moves up rather than out.
    from mayo_baseline.registry.load import progress_report
    cells = progress_report()
    A(f"`{len(impl)} models` · `12 diseases` · "
      f"`{cells['n_cells_implemented']}/{cells['n_cells_nominal']} cells` · "
      f"`{len(checked)}/{len(impl)} verified` · `Apache-2.0`")
    A("")
    A("Clinical risk models are scattered across paywalled PDFs, supplement images, dead")
    A("Flash calculators and hosted web forms. This repository collects them as running,")
    A("tested Python — with the provenance of every coefficient recorded, and with evidence")
    A("that each implementation reproduces an independent source.")
    A("")
    A("```python")
    A("import mayo_baseline as mb")
    A("")
    A("mb.predict(\"albi\", bilirubin_umol_l=20.0, albumin_g_l=40.0)")
    A("# {'score': -2.54, 'grade': 2, 'registry_id': 'albi',")
    A("#  'citation': 'Johnson PJ et al. J Clin Oncol. 2015;33(6):550-558', ...}")
    A("")
    A("[m.id for m in mb.list_models(disease=\"liver\")]")
    A("# ['amap', 'hap', 'albi']")
    A("")
    A("mb.model_info(\"crc_pro\").required_inputs")
    A("# ('male', 'age', 'ethnicity', 'weight_lb', 'height_in', ...)")
    A("")
    A("# one patient record, several models, each given only what it accepts")
    A("mb.predict_many([\"albi\", \"amap\"], age=55, male=True, platelets=200,")
    A("                bilirubin_umol_l=15.0, albumin_g_l=42.0)")
    A("```")
    A("")
    A("Every result carries the model's `scope` — running a model is not the same as")
    A("being entitled to believe it. There is deliberately no \"run everything\"")
    A("convenience; see `mayo_baseline/api.py` for why.")
    A("")
    A("---")
    A("")
    A("> ### ⚠️ Not for clinical use")
    A(">")
    A("> This is a research artifact. It is **not a medical device**, has not been cleared or")
    A("> approved by any regulator, and must not be used to make decisions about a patient's")
    A("> care. Each model carries its own population and scope; applying one outside that")
    A("> scope produces a number that looks valid and is not.")
    A("")
    A("---")
    A("")

    # ---------------------------------------------------------------- the table
    A("## Coverage")
    A("")
    A("Every disease is asked the same three questions. " + GAP_CAPTION)
    A("")
    # An HTML table, not a markdown one, because markdown pipe tables cannot
    # merge cells. Each disease is ONE cell spanning its three questions, and
    # each question is one cell spanning its models — otherwise the eye reads
    # three unrelated rows instead of one disease asked three questions.
    # GitHub renders this; note markdown syntax does not apply inside it, so
    # emphasis and code are written as tags.
    A("<table>")
    A("<thead><tr>" + "".join(f"<th>{c}</th>" for c in COLUMNS) + "</tr></thead>")
    A("<tbody>")

    for did in sorted(DISEASE_LABEL, key=lambda k: DISEASE_LABEL[k]):
        span = sum(max(1, len(by.get(did, {}).get(a, []))) for a in AXES)
        first = True
        for axis in AXES:
            entries = by.get(did, {}).get(axis, [])
            dcell = (f'<td rowspan="{span}" valign="top"><b>{DISEASE_LABEL[did]}</b></td>'
                     if first else "")
            acell = (f'<td rowspan="{max(1, len(entries))}" valign="top">'
                     f'{AXIS_LABEL[axis]}</td>')
            if not entries:
                A(f"<tr>{dcell}{acell}"
                  f'<td colspan="{len(COLUMNS) - 2}">'
                  f"<em>&mdash; {GAP_CELL_LABEL}</em></td></tr>")
                first = False
                continue
            for k, r in enumerate(entries):
                cells = [dcell if k == 0 else "", acell if k == 0 else ""]
                for col in COLUMNS[2:]:
                    cells.append(f'<td valign="top">{_render(col, r)}</td>')
                A("<tr>" + "".join(cells) + "</tr>")
                first = False

    A("</tbody>")
    A("</table>")
    A("")
    A(f"**{len(impl)} models across {len(by)} diseases. "
      f"{len(checked)} of {len(impl)} verified against a source we did not write.**")
    A("")
    A("\"Verified\" means the output was compared against a source we did not write — a")
    A("published reference implementation, a second independent statement of the rule, the")
    A("paper\'s own worked example, or the vendor\'s live calculator.")
    A("")
    A("The evidence is per model, in the table above: **How it was verified** names the")
    A("route and the source, and **Re-run the check** gives the exact pytest command that")
    A("reproduces it. [`docs/MODEL_SPREADSHEET.xlsx`](docs/MODEL_SPREADSHEET.xlsx) carries")
    A("the same columns plus each model\'s scope and caveats.")

    A("")

    # ------------------------------------------------------------------ install
    A("## Install")
    A("")
    A("```bash")
    A("uv sync --group dev      # creates .venv and installs everything")
    A("uv run pytest -q         # no network required")
    A("```")
    A("")
    A("`uv` handles the Python version, the virtualenv and the lockfile in one")
    A("tool, and `uv.lock` pins every version.")
    A("This project uses pip, conda and requirements.txt nowhere at all.")
    A("")
    # Read from pyproject rather than typed here. The README said 3.11+ while
    # pyproject said >=3.10, and a version claim that contradicts the packaging
    # metadata sends people to install the wrong interpreter.
    A(f"Python {_requires_python()}. The equations themselves are plain arithmetic")
    A("with no dependencies; the library needs **PyYAML** to read the registry,")
    A("which is where every model's provenance lives.")
    A("")
    A("Models live under `src/mayo_baseline/<disease>/<question>/`, mirroring the table.")
    A("")

    # ----------------------------------------------------------- architectures
    A("## What kind of models these are")
    A("")
    A(f"{len(impl)} models, {len(fams)} architecture families — every one a")
    A("**fixed-coefficient statistical model**, carrying a handful of numbers estimated once")
    A("and printed in a paper. No learned representations, no training at prediction time.")
    A("")
    A("| Architecture | Models |")
    A("|---|---|")
    for fam, n in fams.most_common():
        A(f"| {fam} | {n} |")
    A("")

    # --------------------------------------------------------------- licensing
    A("## Licensing and provenance")
    A("")
    A("The Python in `src/` is ours, under **Apache-2.0**.")
    A("")
    A("The *models* are not. Each is a published equation belonging to its authors, cited in")
    A("the code, in `registry/models.yaml`, and in the table above. Where a hosted calculator")
    A("carries its own terms — MSK's nomograms are research-and-education, non-commercial —")
    A("**we implement from the open-access publication, not from the hosted tool**.")
    A("")
    A("Third-party reference implementations used for verification are **not vendored here**")
    A("(two are GPL). `collected/MANIFEST.yaml` pins each by version, source and license;")
    A("`scripts/fetch_references.py` retrieves them on demand. Nothing in `src/` imports them.")
    A("")
    A("`registry/models.yaml` is the single source of truth. This README, the spreadsheet and")
    A("the roadmap are all generated from it, and CI checks that the numbers agree — a figure")
    A("here cannot drift from the repo.")
    A("")

    # ------------------------------------------------------------ contributing
    A("## Contributing")
    A("")
    A("Most valuable first:")
    A("")
    A("1. **A correction.** If a coefficient here disagrees with its source, open an issue with")
    A("   the citation and the exact table. Nothing helps more.")
    A("2. **A model for an open cell** — see [`docs/ROADMAP.md`](docs/ROADMAP.md).")
    A("3. **A verification route** for anything we reached by a weaker one.")
    A("")
    A("New models need: the equation source (specific table or figure), a registry row, an")
    A("implementation, unit tests, and a verification route. A model without one can still be")
    A("merged — but it is marked `not_checked` and the reason is recorded.")
    return "\n".join(L) + "\n"


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "README.md"
    models = yaml.safe_load(REGISTRY.read_text())["models"]
    out.write_text(build(models))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
