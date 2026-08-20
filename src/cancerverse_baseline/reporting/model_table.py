"""THE table. Defined once, rendered four ways.

The spreadsheet, the README and the coverage page all show
the same table. They used to each build their own, and they drifted, different
column sets, different wording, one of them stale. So the columns and the row
values live here, and every renderer imports them.

    from model_table import COLUMNS, build_rows, AXIS_LABEL, DISEASE_LABEL

If you want a new column, add it here once.
"""

from __future__ import annotations

from pathlib import Path

#: The repository root, for the renderers that write files into it. Derived
#: from the package's own location: this module used to sit in `scripts/` and
#: compute it as `parents[1]`, which silently became `src/cancerverse_baseline/` when
#: the file moved.
ROOT = Path(__file__).resolve().parents[3]

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
#: equation. No cell in the 36 has an empty literature, only cells where the
#: equation is not reproducible from what we can read, and each of those now
#: records which specific thing is missing. Two tests hold this line:
#: `test_no_cell_is_recorded_as_never_published` and
#: `test_absences_are_described_as_ours_not_the_literatures`, the second of
#: which is why this comment paraphrases the old wording instead of quoting it.
GAP_CELL_LABEL = "not implemented"
GAP_CAPTION = (
    "A dash means we have not implemented that cell. It does not mean the "
    "literature is empty: every one of the 36 cells has a published candidate, "
    "and each unfilled cell records the specific thing that blocks it, a "
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
    "Runs on EHR data?",
    "Developed on",
    "Public repository",
    "Reference",
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
    """Delegate to the package's own loader.

    This module used to resolve `registry/models.yaml` itself, which meant the
    repository had two ways of finding the same file and only one of them knew
    how to work from an installed package.
    """
    from cancerverse_baseline.registry import load_models as _load

    return _load()


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
    equations, equation numbering is a physics convention, while clinical
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
    # An equation NUMBER, e.g. 3, giving "Equation 3. Table 2, ...". Anything
    # else is a mis-filled field and must not be pasted into the sentence: ten
    # entries had put the LOCATION here, six as the bare boolean `true` and
    # four as a string, and this column rendered "Equation True. TABLE 2, page
    # 266..." and "Equation Table 3. Table 3, ...". That shipped in the README,
    # the spreadsheet until 2026-08-19. The location
    # already has a home in `where`; this field only ever adds a number.
    num = loc.get("numbered")
    if isinstance(num, bool):
        num = None
    if num is not None and str(num).strip() and str(num).strip().rstrip(".").isdigit():
        return f"Equation {num} — {where}"
    if not loc.get("verified"):
        return where + "  [not re-read against the source]"
    return where


EHR_LABEL = {
    "routine": "Yes, routine EHR fields",
    "specialty": "Partly, needs pathology, imaging or a send-out assay",
    "not_ehr": "No, needs questionnaire or patient-reported items",
}


def ehr_availability(m: dict) -> str:
    """Whether a health record can supply this model's REQUIRED inputs.

    The question people ask is "are these models too old?", and the answer is
    that age barely matters: ALBI (2015) needs two labs, GRACE (2003) needs
    what an admission already documents, and CRC-PRO (2014) needs ounces of red
    meat per day. What decides deployability is where the inputs live.

    Optional inputs are excluded deliberately. pbcg_extended names race, family
    history and prostate volume but requires only age and PSA, fitting a
    separate sub-model for each pattern of the rest, so missing data picks a
    model instead of forcing an imputation, and the model is `routine`.
    """
    tier = m.get("ehr_availability")
    if not tier:
        return ""
    label = EHR_LABEL.get(tier, tier)
    note = flat(m.get("ehr_note"))
    return f"{label}. {note}" if note else label


def linked_reference(row: dict) -> str:
    """The APA reference with its title turned into a hyperlink.

    A reference list in a paper gives the citation once and hyperlinks the
    title. The table had grown a `Paper` column, a `Reference (APA)` column and
    a `Source` column, which between them printed the title twice and the DOI
    twice in the same row.
    """
    import html

    ref = row.get("Reference") or ""
    title = row.get("_paper_title") or ""
    url = row.get("_source_url") or ""
    if not ref:
        return ""
    esc = html.escape(ref)
    if title and url and title in ref:
        # anchor exactly the title, leaving authors, journal and DOI as text
        et, eu = html.escape(title), html.escape(url)
        return esc.replace(et, f'<a href="{eu}">{et}</a>', 1)
    return esc


def planned_replacements() -> dict[str, dict]:
    """implemented model id -> the catalog entry lined up to replace it.

    Read from the registry rather than listed here, so recording a candidate
    is what makes it appear in every table at once.
    """
    return {m["candidate_for"]: m for m in load_models()
            if m.get("candidate_for") and m.get("status") != "implemented"}


def model_cell(m: dict, planned: dict | None = None) -> str:
    """The model this cell stands for, which is not always the one running.

    Where a replacement has been chosen, the replacement is named first,
    because that is the model the work is committed to and a table headed by a
    superseded one misrepresents the plan. The model actually executing today
    is named underneath as the interim, so nothing is hidden, a reader can
    always tell which of the two produced a number.
    """
    title = flat(m.get("title"))
    repl = (planned or {}).get(m.get("id"))
    if not repl:
        return title
    year = m.get("year")
    # `blocker_kind` says what stands in the way, which a reader needs. The
    # entry's `next_action` used to be printed beside it and is not the
    # reader's business: it is our queue, it is stripped from the published
    # registry, and printing it here carried the text into every generated
    # artefact where that stripping could not reach.
    return (f"{flat(repl.get('title'))}\n"
            f"[{flat(repl.get('blocker_kind') or 'not yet implemented')}]\n"
            f"Interim: {title}"
            + (f" ({year})" if year else ""))


def clinical_question(model: dict) -> str:
    """The clinical decision a model answers, within its disease and axis.

    A (disease, axis) cell is usually one question asked once, and for 35 of
    the 36 cells it is. `cvd/prognosis` is not: GRACE estimates mortality after
    an acute coronary syndrome while CHA2DS2-VASc and ATRIA estimate stroke
    risk in atrial fibrillation. Different patients, different decisions, and
    no reason to prefer one over the other, they are not alternatives, they
    are answers to different things.

    That mattered because `role` allows one flagship per cell. With all three
    in one cell, two of the three had to be labelled `alternative` to GRACE,
    which said something false: ATRIA is not a worse GRACE, it is the better of
    the two AF scores. The label could not express that, so the recommendation
    ended up in prose while the machine-readable field said otherwise.

    So the cell key gains a third component. Models that omit
    `clinical_question` fall back to their axis label, which leaves every cell
    that never had the problem exactly as it was.

    Surveyed 2026-08-14 across all 36 cells: cvd/prognosis is the only one that
    needs this today. The four other cells holding more than one implemented
    model, cvd/detection, lung/detection, ovarian/detection,
    prostate/detection, hold genuine alternatives for a single question
    (regional recalibration, or a different input set for the same decision),
    and are deliberately left alone.
    """
    return str(model.get("clinical_question") or AXIS_LABEL.get(
        model.get("axis"), model.get("axis", "")))


def build_rows(models: list[dict] | None = None,
               top_predictor: dict | None = None) -> list[dict]:
    """One dict per implemented model, keyed by COLUMNS + SPREADSHEET_EXTRAS."""
    models = models if models is not None else load_models()
    top_predictor = top_predictor or {}
    _planned = planned_replacements()
    out = []
    for m in models:
        if m.get("status") != "implemented":
            continue
        ev = m.get("evidence") or {}
        out.append({
            "Disease": DISEASE_LABEL.get(m.get("disease"), m.get("disease", "")),
            "Question": AXIS_LABEL.get(m.get("axis"), m.get("axis", "")),
            "Model": model_cell(m, _planned),
            "Architecture": m.get("architecture_family", ""),
            "Architecture detail": flat(m.get("architecture")),
            # NOT flattened: the formula is a displayed equation and its line
            # structure is the readability. Renderers must keep it.
            "Core formula": str(m.get("core_formula") or "").rstrip(),
            "Year": m.get("year", ""),
            "Discrimination (AUC / C-index)":
                flat(m.get("discrimination"))
                or "we have not read this from the paper yet",
            "Runs on EHR data?": ehr_availability(m),
            "Developed on": flat(m.get("development_cohort")) or "not recorded yet",
            "Public repository": m.get("public_repo") or "",
            # One cell, the way a reference list does it: the APA entry, with
            # the title inside it carrying the link. A separate "Paper" column
            # printed the title a second time, and the DOI a third.
            "Reference": flat(m.get("citation_apa")),
            # kept out of COLUMNS but still on the row, because renderers need
            # them to place the anchor inside the reference string
            "_paper_title": flat(m.get("paper_title")),
            "_source_url": m.get("source_url") or "",
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
            "_question_key": clinical_question(m),
            "_open_source": m.get("open_source"),
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


def questions_in(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    """[(clinical_question, [row, ...])] preserving the order they appear.

    Renderers that show one model per question group with this rather than
    taking the axis whole. Ordering is by first appearance so the flagship of
    the cell's original question stays first, and a question added later does
    not silently reorder the page.
    """
    order: list[str] = []
    seen: dict[str, list[dict]] = {}
    for r in rows:
        q = r.get("_question_key") or ""
        if q not in seen:
            seen[q] = []
            order.append(q)
        seen[q].append(r)
    return [(q, seen[q]) for q in order]


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
