#!/usr/bin/env python3
"""Render the shared table into the Obsidian vault.

    python scripts/build_vault_table.py [output_path]

The vault had per-model notes but no index you could read across, so it was the
one place the table did not exist. Same columns as the README, the spreadsheet
and the coverage page — all four come from scripts/model_table.py.

Obsidian-specific: model names are `[[wikilinks]]` to their notes, so the table
is a navigation surface, not just a summary.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from model_table import (  # noqa: E402
    AXES,
    AXIS_LABEL,
    COLUMNS,
    DISEASE_LABEL,
    GAP_CELL_LABEL,
    build_rows,
    feature_top_predictors,
    grouped,
    load_models,
)

OUT_DEFAULT = ROOT / "vault" / "40_matrix" / "Model-Table.md"


def _wikilink(row: dict) -> str:
    """[[Note-Name|Display]] if the note exists in the registry, else plain."""
    vault = row.get("_vault") or ""
    if not vault:
        return row["Model"]
    stem = Path(vault).stem
    return f"[[{stem}\\|{row['Model']}]]"


def _cell(col: str, row: dict) -> str:
    v = str(row.get(col, "")).replace("|", "\\|")
    if col == "Model":
        return f"**{_wikilink(row)}**"
    if col == "Public repository":
        if not v:
            return f"— *{row['How hard it was to get']}*"
        return f"[{v.rstrip('/').split('/')[-1]}]({v})"
    if col == "Source":
        label = (v.replace("https://doi.org/", "doi:")
                  .replace("https://pubmed.ncbi.nlm.nih.gov/", "PMID ").rstrip("/"))
        return f"[{label}]({v})"
    if col == "Core formula":
        # a markdown table cell cannot hold a real line break, so the displayed
        # equation is folded onto one line with <br> and kept monospaced
        raw = str(row.get(col, "")).replace("|", "\\|")
        if not raw.strip():
            return "—"
        lines = [f"<code>{ln.replace(' ', '&nbsp;')}</code>"
                 for ln in raw.splitlines() if ln.strip()]
        return "<br>".join(lines)
    if col == "Re-run the check":
        return f"`{v}`" if v else "—"
    if col == "Year":
        return f"**{v}**"
    if col in ("Discrimination (AUC / C-index)", "Developed on"):
        return f"*{v}*" if v.startswith("we have not read") or v.endswith("not recorded yet") else v
    if col == "Architecture":
        return f"**{v}**"
    if col == "Verified?":
        return "**Yes**" if v == "Yes" else "No"
    return v or "—"


def build() -> str:
    models = load_models()
    rows = build_rows(models, feature_top_predictors())
    by = grouped(rows)
    impl = [m for m in models if m.get("status") == "implemented"]
    checked = [m for m in impl if m.get("parity_status") in {"checked", "matched"}]
    with_repo = [m for m in impl if m.get("public_repo")]

    L = [
        "---",
        "type: index",
        "generated: true",
        "---",
        "",
        "# Model table",
        "",
        "**Generated — do not edit by hand.** `python scripts/build_vault_table.py`",
        "",
        "The same table as the README, the spreadsheet and `coverage.html`; all four",
        "render `scripts/model_table.py`, so they cannot disagree. Model names link to",
        "their notes.",
        "",
        f"{len(impl)} models across {len({m['disease'] for m in impl})} diseases · "
        f"{len(checked)} verified · {len(with_repo)} with public code.",
        "",
        "| " + " | ".join(COLUMNS) + " |",
        "|" + "---|" * len(COLUMNS),
    ]

    for did in sorted(DISEASE_LABEL, key=lambda k: DISEASE_LABEL[k]):
        first = True
        for axis in AXES:
            entries = by.get(did, {}).get(axis, [])
            disease = f"**{DISEASE_LABEL[did]}**" if first else ""
            if not entries:
                L.append(f"| {disease} | {AXIS_LABEL[axis]} | *— {GAP_CELL_LABEL}* |"
                         + " |" * (len(COLUMNS) - 3))
                first = False
                continue
            for k, r in enumerate(entries):
                cells = [disease if k == 0 else "",
                         AXIS_LABEL[axis] if k == 0 else ""]
                cells += [_cell(c, r) for c in COLUMNS[2:]]
                L.append("| " + " | ".join(cells) + " |")
                first = False

    L += [
        "",
        "## How to read two columns",
        "",
        "**Public repository** links the code we diffed against, where one exists.",
        f"{len(with_repo)} of {len(impl)} models have one. A dash is not a gap in our",
        "work — it says the model was only ever published as a paper or a hosted",
        "calculator, and names which.",
        "",
        "**Source** links the publication. Every model has one, and it is the thing to",
        "check us against. Where the equation we implement came from something other",
        "than that paper — a supplement figure, a vendor's deployed code — the",
        "model's own note says so.",
        "",
        "## Related",
        "",
        "- [[Baseline-Matrix]] — the coverage grid",
        "- [[Disease-Index]] — by disease",
        "- `docs/VERIFICATION.md` — what was checked, against what, with what result",
        "- `docs/CANDIDATE_MODELS.md` — models we could add or upgrade to",
    ]
    return "\n".join(L) + "\n"


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DEFAULT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build())
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
