"""THE table. Defined once, rendered four ways.

The spreadsheet, the README, the coverage page and the Obsidian vault all show
the same table. They used to each build their own, and they drifted — different
column sets, different wording, one of them stale. So the columns and the row
values live here, and every renderer imports them.

    from model_table import COLUMNS, build_rows, AXIS_LABEL, DISEASE_LABEL

If you want a new column, add it here once.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "models.yaml"

AXES = ("detection", "response", "prognosis")
AXIS_LABEL = {"detection": "Prediction", "response": "Response",
              "prognosis": "Prognosis"}
#: Disease names, not organ names. "Breast" is an organ; "Breast cancer" is
#: what the models predict. The only non-cancer row says so plainly.
DISEASE_LABEL = {
    "breast": "Breast cancer",
    "cervical": "Cervical cancer",
    "colorectal": "Colorectal cancer",
    "cvd": "Cardiovascular disease",
    "esophageal": "Esophageal cancer",
    "gastric": "Gastric cancer",
    "head_neck": "Head & neck cancer",
    "liver": "Liver cancer",
    "lung": "Lung cancer",
    "ovarian": "Ovarian cancer",
    "pancreatic": "Pancreatic cancer",
    "prostate": "Prostate cancer",
}
OPEN_SOURCE_LABEL = {
    "available": "public code",
    "web_only": "web calculator only",
    "none": "paper only",
}

#: What a dash in the coverage table means. Every renderer says this, and it is
#: defined here so all four say the same thing.
#:
#: Two earlier captions are retired: one asserted the literature was empty for
#: that cell, the other softened it to "found yet" but still framed the absence
#: as a fact about publishing. On 2026-08-06 the last cells still making that
#: claim were searched properly, and every one turned out to have a published
#: equation. No cell in the 36 has an empty literature -- only cells where the
#: equation is not reproducible from what we can read, and each of those now
#: records which specific thing is missing. Two tests hold this line:
#: `test_no_cell_is_recorded_as_never_published` and
#: `test_absences_are_described_as_ours_not_the_literatures`, the second of
#: which is why this comment paraphrases the old wording instead of quoting it.
GAP_CELL_LABEL = "not implemented"
GAP_CAPTION = (
    "A dash means we have not implemented that cell. It does not mean the "
    "literature is empty: every one of the 36 cells has a published candidate, "
    "and each unfilled cell records the specific thing that blocks it -- a "
    "missing intercept, an unreachable supplement, inputs we do not take, or a "
    "model that is not a closed-form equation at all."
)

#: The canonical column order. Every renderer shows exactly these.
COLUMNS = [
    "Disease",
    "Question",
    "Model",
    "Architecture",
    "Architecture detail",
    "Core formula",
    "Year",
    "Discrimination (AUC / C-index)",
    "Developed on",
    "Public repository",
    "Source",
    "Where the equation sits",
    "Verified?",
    "How it was verified",
    "Re-run the check",
    "Top predictor",
]

#: Extra columns the spreadsheet adds after the canonical set. Kept separate so
#: it is obvious which part is the shared table and which part is spreadsheet-only.
SPREADSHEET_EXTRAS = [
    "Reference data captured by", "Fixture", "Where the equation came from",
    "Citation", "How hard it was to get", "Parameters", "Scope / caveats",
    "Our code",
]
# `repro_tier` is deliberately NOT here. It grades how far an UNIMPLEMENTED
# cell is from being reproducible, so on a table of implemented models it is
# near-constant (25 of 30 were "A") and reads as a quality score, which it is
# not. It stays in the registry, where the gap cells use it.


def flat(x) -> str:
    return " ".join(str(x or "").split())


def load_models() -> list[dict]:
    return yaml.safe_load(REGISTRY.read_text())["models"]


def verified_how(m: dict, limit: int = 300) -> str:
    """The route, not the whole essay. First sentence, which is always the
    route in this registry."""
    note = flat(m.get("parity_note"))
    if not note:
        return "—"
    first = note.split(". ")[0]
    if len(first) < 40 and ". " in note:
        first = ". ".join(note.split(". ")[:2])
    if len(first) > limit:
        first = first[: limit - 1].rsplit(" ", 1)[0] + "…"
    return first


def rerun_command(m: dict) -> str:
    ev = m.get("evidence") or {}
    if not ev.get("test"):
        return ""
    fn = ev.get("test_function")
    return f"pytest {ev['test']}" + (f"::{fn}" if fn else "")


def equation_location(m: dict) -> str:
    """Where in the paper the equation actually is.

    Naming the paper is not enough to check our work against it. Ten papers
    were read on 2026-08-06 to fill this in and NOT ONE numbered its
    equations -- equation numbering is a physics convention, while clinical
    prediction papers put the model in a Table and the prose around it. So
    this is almost always a section heading, a table, or a supplementary
    item, and `numbered` stays false.

    A leading "NOT IN THE PAPER" is not a gap: it is the finding. Nine models
    here were never published as a closed form at all, and their only citable
    location is the vendor source file the coefficients came from.
    """
    loc = m.get("equation_location") or {}
    where = flat(loc.get("where"))
    if not where:
        return ""
    num = loc.get("numbered")
    if num:                       # no paper has done this yet; handle it anyway
        return f"Equation {num} — {where}"
    if not loc.get("verified"):
        return where + "  [not re-read against the source]"
    return where


def build_rows(models: list[dict] | None = None,
               top_predictor: dict | None = None) -> list[dict]:
    """One dict per implemented model, keyed by COLUMNS + SPREADSHEET_EXTRAS."""
    models = models if models is not None else load_models()
    top_predictor = top_predictor or {}
    out = []
    for m in models:
        if m.get("status") != "implemented":
            continue
        ev = m.get("evidence") or {}
        out.append({
            "Disease": DISEASE_LABEL.get(m.get("disease"), m.get("disease", "")),
            "Question": AXIS_LABEL.get(m.get("axis"), m.get("axis", "")),
            "Model": flat(m.get("title")),
            "Architecture": m.get("architecture_family", ""),
            "Architecture detail": flat(m.get("architecture")),
            # NOT flattened: the formula is a displayed equation and its line
            # structure is the readability. Renderers must keep it.
            "Core formula": str(m.get("core_formula") or "").rstrip(),
            "Year": m.get("year", ""),
            "Discrimination (AUC / C-index)":
                flat(m.get("discrimination"))
                or "we have not read this from the paper yet",
            "Developed on": flat(m.get("development_cohort")) or "not recorded yet",
            "Public repository": m.get("public_repo") or "",
            "Source": m.get("source_url") or "",
            "Where the equation sits": equation_location(m),
            "Verified?": "Yes" if m.get("parity_status") in {"checked", "matched"} else "No",
            "How it was verified": verified_how(m),
            "Re-run the check": rerun_command(m),
            "Top predictor": top_predictor.get(m["id"], ""),
            # spreadsheet extras
            "Reference data captured by": ev.get("script", ""),
            "Fixture": ev.get("fixture", ""),
            "Where the equation came from": flat(m.get("equation_source")),
            "Citation": flat(m.get("citation")),
            "How hard it was to get":
                OPEN_SOURCE_LABEL.get(m.get("open_source"), m.get("open_source", "")),
            "Parameters": m.get("n_parameters") or "not counted",
            "Scope / caveats": flat(m.get("scope_note")),
            "Our code": m.get("our_code") or m.get("code", ""),
            # not a column; renderers need it for grouping and links
            "_id": m["id"],
            "_disease_key": m.get("disease"),
            "_axis_key": m.get("axis"),
            "_open_source": m.get("open_source"),
            "_vault": m.get("vault", ""),
        })
    order = {v: i for i, v in enumerate(AXIS_LABEL.values())}
    out.sort(key=lambda r: (r["Disease"], order.get(r["Question"], 9)))
    return out


def grouped(rows: list[dict]) -> dict:
    """{disease_key: {axis_key: [row, ...]}} for the merged-cell renderers."""
    from collections import defaultdict

    by: dict = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["_disease_key"]][r["_axis_key"]].append(r)
    return by


def feature_top_predictors() -> dict:
    """Run the sensitivity sweep, tolerating its absence."""
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import feature_importance as fi
    except Exception as exc:                                   # pragma: no cover
        print(f"  (feature sweep unavailable: {exc})")
        return {}
    top = {}
    for model_id in list(fi.SPEC) + list(fi.CATEGORICAL_NOTE):
        try:
            res = fi.sweep(model_id)
        except Exception:
            continue
        if res is None:
            top[model_id] = fi.CATEGORICAL_NOTE.get(model_id, ("—", ""))[0]
        elif res["features"]:
            top[model_id] = res["features"][0]["feature"]
    return top
