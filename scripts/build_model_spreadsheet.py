#!/usr/bin/env python3
"""Build the master model spreadsheet from registry/models.yaml.

    python scripts/build_model_spreadsheet.py

Emits, all from the single source of truth:

    docs/MODEL_SPREADSHEET.xlsx   five sheets (see below)
    docs/MODEL_SPREADSHEET.csv    the Models sheet, flat, for anyone

Sheets
    Models          one row per model, everything we know about it
    Coverage        12 diseases x 3 questions, so gaps read at a glance
    Key features    which predictor actually drives each model, measured
    Gaps            open cells and the candidates found for them
    Summary         the counts, with their denominators explained

The predecessor of this script hard-coded its rows, which is how it came to
claim BCRAT was unverified months after it had been verified. Nothing here is
typed by hand.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "models.yaml"
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

sys.path.insert(0, str(ROOT / "scripts"))
from model_table import (  # noqa: E402
    AXES,
    AXIS_LABEL,
    DISEASE_LABEL,
    SPREADSHEET_EXTRAS,
    build_rows,
)
from model_table import (
    COLUMNS as CORE_COLUMNS,
)

#: The shared table, then the spreadsheet-only extras.
COLUMNS = CORE_COLUMNS + SPREADSHEET_EXTRAS

# Candidates found 2026-08-06 on riskcalc.org. See docs/CANDIDATE_MODELS.md.
RISKCALC = "https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/"
CANDIDATES = {
    ("cvd", "response"): (None,
        "Derivable as a risk difference on PREVENT/SCORE2 x a trial relative risk "
        "reduction; no single published equation. A modelling decision, not a search."),
    ("ovarian", "response"): (None,
        "KELIM is a nonlinear population-PK model, not closed-form."),
}

# --------------------------------------------------------------------- data --
def load() -> list[dict]:
    return yaml.safe_load(REGISTRY.read_text())["models"]


def _flat(x) -> str:
    return " ".join(str(x or "").split())


def feature_table() -> tuple[dict, list[dict]]:
    """Run the sensitivity sweep. Returns (top predictor per model, all rows)."""
    try:
        import feature_importance as fi
    except Exception as exc:                                   # pragma: no cover
        print(f"  (feature sweep unavailable: {exc})")
        return {}, []

    top, rows = {}, []
    for model_id in list(fi.SPEC) + list(fi.CATEGORICAL_NOTE):
        try:
            res = fi.sweep(model_id)
        except Exception as exc:
            print(f"  (sweep failed for {model_id}: {exc})")
            continue
        if res is None:
            feat, why = fi.CATEGORICAL_NOTE.get(model_id, ("—", ""))
            top[model_id] = feat
            rows.append({"model": model_id, "feature": feat, "swing": None,
                         "share": None, "unit": "", "note": why})
            continue
        unit = "percentage points of risk" if fi.SPEC[model_id][3] == 100 else "points"
        if res["features"]:
            top[model_id] = res["features"][0]["feature"]
        for r in res["features"]:
            rows.append({"model": model_id, "feature": r["feature"],
                         "swing": round(r["swing"], 3), "share": r["share"],
                         "unit": unit, "note": ""})
    return top, rows


def summary(models: list[dict], rows: list[dict]) -> list[tuple[str, object]]:
    impl = [m for m in models if m.get("status") == "implemented"]
    checked = [m for m in impl if m.get("parity_status") in {"checked", "matched"}]
    src = Counter(m.get("open_source") for m in impl)
    fams = Counter(r["Architecture"] for r in rows)
    filled = {(m["disease"], m["axis"]) for m in impl}

    # Derive the reachable denominator from the registry rather than hardcoding
    # it. It has already been wrong once (24 when it should have been 26).
    from cancerverse_baseline.registry.load import progress_report
    rep = progress_report()
    reachable = rep["n_cells_reachable"]
    unreachable = rep["n_cells_unreachable"]

    L: list[tuple[str, object]] = [
        ("COVERAGE", ""),
        ("Diseases with at least one model", f"{len({m['disease'] for m in impl})} / 12"),
        ("Disease x question cells filled", f"{len(filled)} / 36 nominal"),
        ("...of the cells we believe are reachable", f"{len(filled)} / {reachable}"),
        ("Models implemented", len(impl)),
        ("", ""),
        ("VERIFICATION", ""),
        ("Verified against an independent source", f"{len(checked)} / {len(impl)}"),
        ("Verification rate", f"{len(checked) / len(impl):.0%}"),
        ("Every check re-runnable offline", "yes — fixtures are committed"),
        ("", ""),
        ("HOW HARD THEY WERE TO GET", ""),
        ("Had a runnable reference implementation", src["available"]),
        ("Had only a hosted web calculator", src["web_only"]),
        ("Had nothing but the paper", src["none"]),
        ("", ""),
        ("ARCHITECTURES", f"{len(fams)} families"),
    ]
    for fam, n in fams.most_common():
        L.append((f"    {fam}", n))
    L += [
        ("", ""),
        ("A NOTE ON THE DENOMINATOR", ""),
        ("Why not 36?",
         f"For {unreachable} of the 36 cells we have not found a published equation. "
         "That is a statement about our search, not about the literature: it was "
         "12 until 2026-08-06, when a scan of one website's published source turned "
         "up equations for four cells the earlier survey had written off. "
         "Correcting it moved progress DOWN, because the survey had been wrong. "
         "Each open cell records its own blocker in registry/models.yaml; see "
         "the Gaps sheet."),
    ]
    return L


# ------------------------------------------------------------------ writers --
def write_csv(rows: list[dict]) -> Path:
    p = DOCS / "MODEL_SPREADSHEET.csv"
    with p.open("w", newline="", encoding="utf-8-sig") as fh:
        # build_rows carries private "_"-prefixed keys for the renderers.
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return p


def write_xlsx(models, rows, feats, top) -> Path:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import DataBarRule
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    INK, ACCENT = "16211F", "0F6E5C"
    HEAD = Font(bold=True, color="FFFFFF", size=10.5)
    FILL = PatternFill("solid", fgColor=INK)
    SUB = PatternFill("solid", fgColor="E4F0EC")
    OKF = PatternFill("solid", fgColor="E3F2E1")
    NOF = PatternFill("solid", fgColor="FDECEA")
    GAPF = PatternFill("solid", fgColor="FDF3E0")
    THIN = Side(style="thin", color="D0D7DE")
    BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
    WRAP = Alignment(vertical="top", wrap_text=True)
    TOPL = Alignment(vertical="top")

    def header(ws, labels):
        ws.append(labels)
        for c in ws[1]:
            c.font, c.fill, c.alignment, c.border = HEAD, FILL, WRAP, BORDER
        ws.row_dimensions[1].height = 34

    def widths(ws, spec, default=18):
        for i in range(1, ws.max_column + 1):
            ws.column_dimensions[get_column_letter(i)].width = spec.get(
                ws.cell(1, i).value, default)

    wb = Workbook()

    # ---- Models -----------------------------------------------------------
    ws = wb.active
    ws.title = "Models"
    header(ws, COLUMNS)
    for r in rows:
        ws.append([r[c] for c in COLUMNS])
    # the formula is a displayed equation; monospace it so its alignment holds
    fcol = COLUMNS.index("Core formula") + 1
    for row in ws.iter_rows(min_row=2, min_col=fcol, max_col=fcol):
        row[0].font = Font(name="Menlo", size=9)
    vcol = COLUMNS.index("Verified?") + 1
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment, c.border = WRAP, BORDER
        cell = row[vcol - 1]
        cell.fill = OKF if cell.value == "Yes" else NOF
        cell.font = Font(bold=True, color=ACCENT if cell.value == "Yes" else "9A3412")
    widths(ws, {
        "Disease": 15, "Question": 12, "Model": 40, "Architecture": 20,
        "Architecture detail": 60, "Core formula": 54, "Parameters": 11,
        "Verified?": 10, "How it was verified": 80, "Re-run the check": 62,
        "Reference data captured by": 40, "Fixture": 38,
        "Where the equation came from": 66, "Citation": 44,
        "Reference implementation available?": 28, "Top predictor": 24,
        "Scope / caveats": 50, "Our code": 44,
    })
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = ws.dimensions

    # ---- Coverage ---------------------------------------------------------
    ws2 = wb.create_sheet("Coverage")
    header(ws2, ["Disease", *AXIS_LABEL.values()])
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["Disease"]][r["Question"]].append(r)
    for disease in sorted(DISEASE_LABEL.values()):
        line = [disease]
        for axis in AXIS_LABEL.values():
            entries = by.get(disease, {}).get(axis, [])
            if not entries:
                line.append("— no model")
            else:
                line.append("\n".join(
                    f"{e['Model']}\n[{'verified' if e['Verified?'] == 'Yes' else 'NOT verified'}]"
                    for e in entries))
        ws2.append(line)
    for row in ws2.iter_rows(min_row=2):
        for c in row:
            c.alignment, c.border = WRAP, BORDER
            if isinstance(c.value, str) and c.value.startswith("—"):
                c.fill = GAPF
        row[0].font = Font(bold=True)
    ws2.column_dimensions["A"].width = 18
    for col in "BCD":
        ws2.column_dimensions[col].width = 46
    for i in range(2, ws2.max_row + 1):
        ws2.row_dimensions[i].height = 62

    # ---- Key features -----------------------------------------------------
    ws3 = wb.create_sheet("Key features")
    header(ws3, ["Model", "Disease", "Predictor", "Swing across its clinical range",
                 "Unit", "Share of this model's total swing", "Note"])
    dis_of = {r["Model"]: r["Disease"] for r in rows}
    id_to_title = {m["id"]: _flat(m.get("title")) for m in models}
    for f in feats:
        title = id_to_title.get(f["model"], f["model"])
        ws3.append([title, dis_of.get(title, ""), f["feature"], f["swing"],
                    f["unit"], f["share"], f["note"]])
    for row in ws3.iter_rows(min_row=2):
        for c in row:
            c.alignment, c.border = TOPL, BORDER
        row[3].number_format = "0.00"
        row[5].number_format = "0%"
        row[2].alignment = WRAP
        row[6].alignment = WRAP
    if ws3.max_row > 1:
        ws3.conditional_formatting.add(
            f"F2:F{ws3.max_row}",
            DataBarRule(start_type="num", start_value=0, end_type="num",
                        end_value=1, color=ACCENT, showValue=True))
    widths(ws3, {"Model": 40, "Disease": 15, "Predictor": 32,
                 "Swing across its clinical range": 16, "Unit": 24,
                 "Share of this model's total swing": 18, "Note": 70})
    ws3.freeze_panes = "A2"
    ws3.auto_filter.ref = ws3.dimensions

    # ---- Gaps -------------------------------------------------------------
    ws4 = wb.create_sheet("Gaps")
    header(ws4, ["Disease", "Question", "Status", "Candidate found",
                 "Notes", "Source"])
    impl_cells = {(m["disease"], m["axis"])
                  for m in models if m.get("status") == "implemented"}
    tier = {}
    for m in models:
        if m.get("status") in {"gap", "catalog"}:
            tier.setdefault((m.get("disease"), m.get("axis")),
                            m.get("repro_tier"))
    for did in sorted(DISEASE_LABEL, key=lambda k: DISEASE_LABEL[k]):
        for axis in AXES:
            if (did, axis) in impl_cells:
                continue
            cand, note = CANDIDATES.get((did, axis), (None, ""))
            # No cell resolves to tier D any more (see model_table.GAP_CAPTION),
            # but keep the branch: if one ever does, it must say so loudly rather
            # than silently reading as an ordinary open cell.
            unreachable = tier.get((did, axis)) == "D"
            status = "REGRESSION: marked never-published" if unreachable \
                else "open — not implemented"
            if cand:
                status += " · CANDIDATE FOUND"
            ws4.append([DISEASE_LABEL[did], AXIS_LABEL[axis], status,
                        cand or "", note,
                        RISKCALC + cand.split(" ")[0] if cand else ""])
    for row in ws4.iter_rows(min_row=2):
        for c in row:
            c.alignment, c.border = WRAP, BORDER
        if "CANDIDATE" in str(row[2].value):
            for c in row:
                c.fill = SUB
    widths(ws4, {"Disease": 15, "Question": 12, "Status": 34,
                 "Candidate found": 46, "Notes": 62, "Source": 60})
    ws4.freeze_panes = "A2"

    # ---- Summary ----------------------------------------------------------
    ws5 = wb.create_sheet("Summary")
    header(ws5, ["Metric", "Value"])
    for k, v in summary(models, rows):
        ws5.append([k, v])
        if k and not k.startswith("    ") and v == "":
            for c in ws5[ws5.max_row]:
                c.font, c.fill = Font(bold=True, color=ACCENT), SUB
    for row in ws5.iter_rows(min_row=2):
        for c in row:
            c.alignment = WRAP
    ws5.column_dimensions["A"].width = 46
    ws5.column_dimensions["B"].width = 62

    # ---- Glossary ---------------------------------------------------------
    ws6 = wb.create_sheet("Glossary")
    header(ws6, ["Column", "What it means"])
    GLOSSARY = [
        ("Disease", "The disease the model is about, not the organ."),
        ("Question", "Prediction (will they get it?), Response (will treatment "
                     "help?), Prognosis (what is the outlook?). These are the "
                     "three questions every disease is asked."),
        ("Architecture", "What class of model it is. All of these are "
                         "fixed-coefficient statistical models — a handful of "
                         "numbers estimated once and printed in a paper. None "
                         "is a neural network."),
        ("Core formula", "The equation, as it would be set in the paper. "
                         "Caveats live in Scope / caveats, not here."),
        ("Year", "Publication year of the model, cross-checked against its own "
                 "citation."),
        ("Discrimination (AUC / C-index)",
         "How well the model separates who has the outcome from who does not. "
         "1.0 is perfect, 0.5 is a coin flip; most clinical models sit at "
         "0.65-0.85. Blank where we have not read the number from the paper — "
         "it enters this table only from a source actually read, so a blank "
         "means we have not read it, not that the model was never evaluated."),
        ("Developed on", "The cohort the model was fitted on. Useful mainly "
                         "for judging whether it transports to your patients."),
        ("Public repository", "A public repo containing the model's CODE, "
                              "where one exists. A hosted calculator is not a "
                              "repository and is not counted here."),
        ("Source", "The publication. Every model has one, and it is the thing "
                   "to check us against."),
        ("Verified?", "Whether our output was compared against something we "
                      "did not write. Not 'the tests pass' — our own tests "
                      "cannot tell us we read a paper correctly."),
        ("How it was verified", "Which of six routes was used. Full account "
                                "with exact numbers in docs/VERIFICATION.md."),
        ("Re-run the check", "A command you can paste. The comparison runs "
                             "offline against a committed fixture."),
        ("Top predictor", "Which input moves the output most, measured by "
                          "sweeping each input across its clinical range. Not "
                          "the largest coefficient — age often has a small "
                          "coefficient and still dominates, because it ranges "
                          "over fifty years."),
        ("How hard it was to get", "Whether the model arrived as runnable "
                                   "code, as a hosted calculator we had to "
                                   "reverse, or as a paper we had to "
                                   "transcribe."),
        ("Parameters", "Roughly how many fitted numbers the model carries, for "
                       "contrast with modern architectures. A transformer "
                       "carries 10^9 to 10^12."),
        ("Scope / caveats", "The population the model was built for. Applying "
                            "one outside its scope produces a number that "
                            "looks valid and is not."),
        ("", ""),
        ("A note on blanks",
         "Blank cells in this workbook mean we have not established the value, "
         "not that no value exists. That distinction matters here: four cells "
         "recorded as having no published equation turned out to have one."),
    ]
    for k, v in GLOSSARY:
        ws6.append([k, v])
    for row in ws6.iter_rows(min_row=2):
        for c in row:
            c.alignment = WRAP
        row[0].font = Font(bold=True)
    ws6.column_dimensions["A"].width = 32
    ws6.column_dimensions["B"].width = 96

    p = DOCS / "MODEL_SPREADSHEET.xlsx"
    wb.save(p)
    return p


def main() -> int:
    models = load()
    print("running the feature sweep...")
    top, feats = feature_table()
    rows = build_rows(models, top)
    for p in (write_csv(rows), write_xlsx(models, rows, feats, top)):
        print(f"wrote {p.relative_to(ROOT)}")
    print(f"\n{len(rows)} implemented models, {len(feats)} feature rows")
    for k, v in summary(models, rows):
        if v != "" and not k.startswith("    ") and k.isupper() is False:
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
