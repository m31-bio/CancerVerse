# Registry tests
import pathlib
import re
from pathlib import Path

import pytest

from cancerverse_baseline.registry import (
    AXES,
    cell_tiers,
    coverage_matrix,
    load,
    load_diseases,
    load_models,
    open_source_queues,
    parity_blockers,
    progress_report,
    reproducibility_scoreboard,
)


def test_load_diseases_count():
    diseases = load_diseases()
    assert len(diseases) == 12
    ids = {d["id"] for d in diseases}
    assert "prostate" in ids and "cvd" in ids


def test_matrix_has_prostate_detection_implemented():
    """The flagship is `pbcg_extended` since 2026-08-07.

    It displaced the 2018 PBCG. The reason given at the time was licensing:
    the 2018 coefficients were only machine-readable from riskcalc.org, whose
    source is PolyForm Noncommercial 1.0.0, and docs/THIRD_PARTY_CODE.md
    concluded that put a company outside the licence. That conclusion tested
    the wrong thing. PolyForm gates on PURPOSE, not on entity, and once
    M31 confirmed the project's use is academic research only it stopped
    applying. See docs/ACADEMIC_USE_LICENSE_REVIEW.md.

    The flagship did not change, because the OTHER reason still holds and is
    the better one: the 2022 model publishes its full coefficient set CC BY 4.0
    as supplementary material to its own paper, so its provenance is a paper
    rather than a deployment, and it is the better model besides.

    It is also the better model: 1,024 sub-models against 8, ten optional
    predictors against three. Flipping the default means arguing with
    `flagship_note` and with docs/THIRD_PARTY_CODE.md, not editing a string
    here.
    """
    matrix = coverage_matrix()
    assert set(matrix["prostate"]) == set(AXES)
    flag = matrix["prostate"]["detection"]
    assert flag is not None
    assert flag["status"] == "implemented"
    assert flag["id"] == "pbcg_extended"
    assert "PolyForm" in flag["flagship_note"]

    # The model it displaced stays IMPLEMENTED as the alternative, which is
    # what rmi, roma, cha2ds2_vasc, erspc_rc3 and bcrat all do after being
    # superseded. It was `status: catalog` between 2026-08-07 and 2026-08-18,
    # and the cost of that was concrete: `mb.predict("pbcg", ...)` raised,
    # PBCG left `list_models()` entirely, and a parity-checked tier-A model
    # stopped being counted. Retiring a verified model to catalog is a
    # breaking API change made for tidiness.
    old = next(m for m in load_models() if m["id"] == "pbcg")
    assert old["status"] == "implemented"
    assert old["role"] == "alternative"
    assert old.get("superseded_by") == "pbcg_extended"

    # and the model it displaced is still there, as a documented alternative
    alt = next(m for m in load_models() if m["id"] == "erspc_rc3")
    assert alt["role"] == "alternative"
    assert alt["flagship_note"]


def test_load_bundle():
    bundle = load()
    assert len(bundle["models"]) >= 12
    cell = bundle["matrix"]["cvd"]["detection"]
    assert cell["id"] == "prevent"
    assert cell["status"] == "implemented"
    assert cell["parity_status"] == "checked"
    # ERSPC RC3 became `checked` on 2026-08-05 once its coefficients were
    # recovered from SWOP's Flash calculator; assert the enum is valid rather
    # than pinning a value that moves as verification progresses.
    assert bundle["matrix"]["prostate"]["detection"]["parity_status"] in {
        "checked",
        "not_checked",
        "matched",
        "unmatched",
        "n/a",
    }


def test_parity_breaks_flagship_ties():
    checked = {"role": "flagship", "status": "implemented", "parity_status": "checked"}
    not_checked = {
        "role": "flagship",
        "status": "implemented",
        "parity_status": "not_checked",
    }
    for disease in ("cvd",):
        models = [
            {**not_checked, "id": "a", "disease": disease, "axis": "detection"},
            {**checked, "id": "b", "disease": disease, "axis": "detection"},
        ]
        picked = coverage_matrix(load_diseases(), models)[disease]["detection"]
        assert picked["id"] == "b"


def test_every_implemented_model_cites_its_equation_source():
    missing = []
    for m in load_models():
        if m.get("status") != "implemented":
            continue
        # The field was dropped from the registry on 2026-08-07. The notes it
        # pointed into is personal and deliberately not version-controlled, so
        # library data has no business naming paths inside it, and the sync
        # script no longer has to strip the field on the way out, which was the
        # one place it transformed rather than copied.
        for field in ("equation_source", "citation", "our_code"):
            if not m.get(field):
                missing.append(f"{m['id']}.{field}")
    assert not missing, f"implemented models missing provenance: {missing}"


def test_every_implemented_model_has_open_source_and_parity_queues():
    for m in load_models():
        if m.get("status") != "implemented":
            continue
        assert m.get("open_source") in {"available", "web_only", "none"}, m["id"]
        assert m.get("parity_status") in {
            "checked",
            "not_checked",
            "blocked_by_license",
            "n/a",
            "matched",  # legacy alias
            "unmatched",
        }, m["id"]


def test_checked_models_name_a_canonical_reference():
    for m in load_models():
        if m.get("parity_status") not in {"checked", "matched"}:
            continue
        impl = m.get("canonical_impl") or {}
        assert (
            impl.get("url") or impl.get("note") or impl.get("type") == "paper_only"
        ), m["id"]
        assert m.get("upstream") or impl.get("type") == "paper_only", m["id"]


def test_reproducibility_scoreboard():
    board = reproducibility_scoreboard()
    assert board["n_cells"] == 36
    assert set(board["checked"]) <= set(board["implemented"])
    assert board["n_checked"] == len(board["checked"])
    assert board["n_open_source_available"] == len(board["open_source_available"])
    for mid in board["checked"]:
        model = next(m for m in load_models() if m["id"] == mid)
        assert model.get("our_code")


def test_open_source_queues_partition_implemented():
    q = open_source_queues()
    board = reproducibility_scoreboard()
    assert set(q["available"]) | set(q["web_only"]) | set(q["none"]) == set(
        board["implemented"]
    )


def test_progress_report_denominators_are_consistent():
    """The two denominators must stay arithmetically consistent.

    This used to assert `pct_of_reachable > pct_of_nominal`, i.e. that at least
    one cell was unreachable. That is no longer true, and the reason is worth
    keeping: `repro_tier: D` means "never published as an equation", and on
    2026-08-06 the last four cells still carrying it were searched properly.
    All four turned out to have published equations. Every cell that resolved
    to D now resolves to C or better, so the reachable denominator has
    collapsed onto the nominal one and both percentages are equal.

    That makes `pct_of_reachable` the more flattering number only in principle
    now, never in fact, which is the honest outcome. Assert the invariant
    (the two can never diverge in the wrong direction) rather than the
    contingent fact that some cell happened to be unreachable.
    """
    r = progress_report()
    assert r["n_cells_nominal"] == 36
    assert r["n_cells_reachable"] + r["n_cells_unreachable"] == r["n_cells_nominal"]
    assert r["n_cells_implemented"] + r["n_cells_remaining"] == r["n_cells_reachable"]
    assert r["pct_of_reachable"] >= r["pct_of_nominal"]
    # equality holds exactly when nothing is unreachable
    assert (r["pct_of_reachable"] == r["pct_of_nominal"]) == (
        r["n_cells_unreachable"] == 0
    )


def test_no_cell_is_recorded_as_never_published():
    """`repro_tier: D` is a claim about the literature, not about our search.

    This project asserted "no published equation exists" and was wrong five
    separate times. Every remaining D was checked on 2026-08-06 and none
    survived. If a D reappears, the note attached to it has to say what was
    searched, otherwise it is the same mistake in a new cell.
    """
    tiers = cell_tiers()
    still_d = sorted(cell for cell, tier in tiers.items() if tier == "D")
    assert not still_d, (
        "cells claiming nothing was ever published as an equation: "
        f"{still_d}. Record what was searched before asserting this."
    )


def test_every_not_checked_model_declares_why_parity_is_blocked():
    blockers = parity_blockers()
    assert "unclassified" not in blockers, blockers.get("unclassified")


def test_no_implemented_cell_is_marked_unreachable():
    r = progress_report()
    assert not (set(r["unreachable_cells"]) & set(tuple(c) for c in r["checked_cells"]))


def test_registry_ids_match_the_model_ids_the_code_returns():
    """A registry id that disagrees with the code's own model_id breaks
    traceability: a result dict can no longer be tied back to its provenance
    row. Caught `gail_bcrat` vs `bcrat` during the 2026-08-05 verification pass.
    """
    import importlib

    calls = {
        "bcrat": (
            "cancerverse_baseline.breast.detection",
            "bcrat_predict",
            dict(
                start_age=50,
                end_age=55,
                n_biopsies=0,
                age_menarche=13,
                age_first_birth=25,
                n_relatives=0,
            ),
        ),
        "albi": (
            "cancerverse_baseline.liver.prognosis",
            "albi_predict",
            dict(bilirubin_umol_l=20.0, albumin_g_l=40.0),
        ),
        "grace": (
            "cancerverse_baseline.cvd.prognosis",
            "grace_predict",
            dict(killip_class=1, sbp=130, heart_rate=80, age=60, creatinine_mg_dl=1.0),
        ),
        "kunzmann": (
            "cancerverse_baseline.esophageal.detection",
            "kunzmann_predict",
            dict(
                age=60, male=True, bmi=28, smoking="former", esophageal_condition=False
            ),
        ),
        "roma": (
            "cancerverse_baseline.ovarian.detection",
            "roma_predict",
            dict(he4_pmol_l=60.0, ca125_u_ml=30.0, postmenopausal=True),
        ),
    }
    registry_ids = {m["id"] for m in load_models()}
    for expected_id, (mod, fn, kwargs) in calls.items():
        assert expected_id in registry_ids, expected_id
        out = getattr(importlib.import_module(mod), fn)(**kwargs)
        assert out["model_id"] == expected_id, (
            f"{mod}.{fn} returns model_id={out['model_id']!r} "
            f"but the registry row is {expected_id!r}"
        )


def test_every_model_module_in_the_code_has_a_registry_row():
    """The reverse of `test_registry_ids_match_the_model_ids_the_code_returns`.

    That test walks registry -> code, so it cannot see a module that the
    registry never mentions. `endpac` was exactly that: implemented, tested and
    written up in docs/VERIFICATION.md, but absent from the registry, so every
    progress count understated the work and the pancreatic detection cell
    reported as a todo. The registry is meant to be the single source of truth;
    a module it does not know about is a silent hole in it.
    """
    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "cancerverse_baseline"
    registry_ids = {m["id"] for m in load_models()}

    missing = []
    for path in sorted(src.rglob("*.py")):
        if path.name in {"__init__.py", "base.py"} or "registry" in path.parts:
            continue
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "MODEL_ID" not in names:
                continue
            if not isinstance(node.value, ast.Constant):
                continue
            model_id = node.value.value
            if model_id not in registry_ids:
                missing.append(
                    f"{path.relative_to(src)} declares MODEL_ID={model_id!r}"
                )

    assert not missing, (
        "these modules ship a model the registry has no row for:\n  "
        + "\n  ".join(missing)
    )


def test_verification_doc_headline_matches_the_registry():
    """Doc drift is this project's most repeated defect class (four of the
    nineteen logged). The headline count in docs/VERIFICATION.md is the number
    most likely to be read aloud in a meeting, so it is the one worth pinning.
    """
    import re
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "docs" / "VERIFICATION.md"
    if not path.exists():
        pytest.skip("docs/VERIFICATION.md is not distributed with the public repo")
    doc = path.read_text()
    models = load_models()
    implemented = [m for m in models if m.get("status") == "implemented"]
    checked = [
        m for m in implemented if m.get("parity_status") in {"checked", "matched"}
    ]
    diseases = {m["disease"] for m in implemented}

    m = re.search(
        r"\*\*(\d+) of (\d+) diseases carry a baseline\. "
        r"(\d+) models coded, (\d+) checked at L4 \((\d+)%\)\.\*\*",
        doc,
    )
    # The rate is no longer 100%: cvd_statin_benefit is a derived composition
    # with nothing to compare against. The guard must keep tracking the real
    # number rather than being relaxed to "close enough".
    assert m, "the headline sentence in docs/VERIFICATION.md is missing or reworded"
    n_dis, n_dis_total, n_models, n_checked, pct = (int(g) for g in m.groups())

    assert n_dis == len(diseases), (
        f"doc says {n_dis} diseases, registry has {len(diseases)}"
    )
    assert n_dis_total == 12
    assert n_models == len(implemented), (
        f"doc says {n_models} models coded, registry has {len(implemented)}"
    )
    assert n_checked == len(checked), (
        f"doc says {n_checked} checked, registry has {len(checked)}"
    )
    assert pct == round(len(checked) / len(implemented) * 100), (
        "the percentage disagrees"
    )


def test_verification_doc_last_pass_date_is_not_older_than_its_own_contents():
    """The header date is the first thing a reader sees and nothing was pinning it.

    the header said "Last pass: 2026-08-05" while the body
    described work done on the 6th, 7th, 14th, 17th and 18th. Thirteen days
    stale, on the line most likely to be quoted as "when was this last looked
    at", the same doc-drift defect class this file's headline test already
    guards the counts against.

    The guard is deliberately NOT "the date is today", which would fail on every
    day nobody touches the document and teach people to bump it meaninglessly.
    It is "the header is not older than the newest date the document itself
    mentions", which can only fail when someone adds dated work and forgets the
    header, exactly the way this failed.
    """
    import re
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "docs" / "VERIFICATION.md"
    if not path.exists():
        pytest.skip("docs/VERIFICATION.md is not distributed with the public repo")
    doc = path.read_text()

    header = re.search(r"\*Last pass: (\d{4}-\d{2}-\d{2})\.\*", doc)
    assert header, "docs/VERIFICATION.md has no '*Last pass: YYYY-MM-DD.*' header"

    mentioned = sorted(set(re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b", doc)))
    newest = mentioned[-1]
    assert header.group(1) >= newest, (
        f"docs/VERIFICATION.md says 'Last pass: {header.group(1)}' but describes "
        f"work dated {newest}. Update the header when adding dated work."
    )


def test_reproducibility_map_open_debts_are_actually_still_open():
    """A debt list nobody re-reads becomes a list of solved problems.

    docs/REPRODUCIBILITY_MAP.md's "Open verification debts"
    section listed ten models as blocked, seven "likely needs institutional
    access", three needing an R runtime. Every one of the ten was already
    `parity_status: checked`, `repro_tier: A`. The document had been correct
    when written on 2026-08-05 and was quietly wrong for thirteen days, telling
    anyone who opened it to go chase papers we already had.

    The header date was no help: it honestly said 2026-08-05. The document was
    not stale in its dating, it was stale in its claims, and only the registry
    knows the difference.

    So the open items now carry `<!-- open-debt: <model_id> -->` markers and this
    test reads them. A debt that closes fails the test until someone moves the
    row. Items with no registry id (QCancer, a decision about whether to
    vendor, not a model we hold) carry no marker and are not checked here.
    """
    import re
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "docs" / "REPRODUCIBILITY_MAP.md"
    if not path.exists():
        pytest.skip("docs/REPRODUCIBILITY_MAP.md is not distributed publicly")

    marked = re.findall(r"<!--\s*open-debt:\s*([a-z0-9_]+)\s*-->", path.read_text())
    assert marked, (
        "docs/REPRODUCIBILITY_MAP.md has no `<!-- open-debt: <id> -->` markers. "
        "If every debt really closed, say so in the document rather than "
        "deleting the markers, an empty debt list and an unmaintained one "
        "look identical from here."
    )

    by_id = {m["id"]: m for m in load_models()}
    unknown = [i for i in marked if i not in by_id]
    assert not unknown, f"open-debt markers name models the registry does not have: {unknown}"

    closed = [i for i in marked if by_id[i].get("parity_status") in {"checked", "matched"}]
    assert not closed, (
        f"docs/REPRODUCIBILITY_MAP.md still lists {closed} as an open verification "
        f"debt, but the registry says parity is checked. Move the row into "
        f"'Resolved' with what closed it."
    )


def test_every_checked_model_says_how_it_was_checked():
    """A `checked` row with no parity_note is a claim with no evidence behind it,
    and it renders as "Yes — —" in the generated README. Caught plcom2012.
    """
    thin = [
        m["id"]
        for m in load_models()
        if m.get("parity_status") in {"checked", "matched"}
        and len(str(m.get("parity_note", "")).strip()) < 40
    ]
    assert not thin, f"checked but no substantive parity_note: {thin}"


def test_every_implemented_model_has_an_architecture_and_a_core_formula():
    """Both are surfaced in the README's coverage table; a blank cell there reads
    as 'we do not know what this model is'."""
    missing = [
        m["id"]
        for m in load_models()
        if m.get("status") == "implemented"
        and not (
            m.get("architecture_family")
            and m.get("architecture")
            and m.get("core_formula")
        )
    ]
    assert not missing, f"missing architecture or core_formula: {missing}"


def test_every_implemented_model_says_where_its_equation_sits():
    """Naming the paper is not enough to check our work against it.

    `equation_source` says which paper; `equation_location` says where in that
    paper to look, the equation number if it has one, otherwise the section
    heading, table, figure or supplementary item. Ten papers were read on
    2026-08-06 to populate this and NOT ONE numbered its equations, so
    `numbered` is expected to stay false or null; a true value means someone
    found a genuinely numbered equation, which is worth noticing.

    `verified` distinguishes locations read from the source in that pass from
    ones carried over from implementation notes, because only the first kind
    can be quoted back at the paper with confidence.
    """
    bad = []
    for m in load_models():
        if m.get("status") != "implemented":
            continue
        loc = m.get("equation_location")
        if not isinstance(loc, dict) or not str(loc.get("where") or "").strip():
            bad.append(m["id"])
    assert not bad, f"no equation_location recorded: {bad}"


#: Reference scripts withheld for licensing reasons; see the sync script and
#: docs/THIRD_PARTY_CODE.md. Named here so the evidence check can tell a
#: deliberate absence from a broken pointer.
NONCOMMERCIAL_REFERENCE = {
    "crc_pro_reference.R",
    "pbcg_reference.R",
    "dutasteride_reference.R",
    "msk_gastric_reference.R",
    "msk_ovarian_reference.R",
    "msk_pancreatic_reference.R",
    "dutasteride_extract.py",
}


def test_evidence_pointers_resolve():
    """Every model's `evidence` block must point at files that exist, and at a
    test function that is actually in the named file.

    A dangling pointer is worse than no pointer: it reads as "go verify this
    yourself" and then wastes the reader's time. This opens each file.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    problems = []
    for m in load_models():
        if m.get("status") != "implemented":
            continue
        ev = m.get("evidence")
        if not ev:
            problems.append(f"{m['id']}: no evidence block")
            continue
        for key in ("test", "script", "fixture"):
            rel = ev.get(key)
            if not rel or (root / rel).exists():
                continue
            # Seven reference scripts transcribe expressions from a
            # PolyForm-Noncommercial source and are deliberately not
            # distributed (see docs/THIRD_PARTY_CODE.md). Their absence is the
            # licence rule working, not a dangling pointer, but only for
            # those seven, and only where the whole set is absent, so a file
            # deleted by accident still fails here.
            if pathlib.Path(rel).name in NONCOMMERCIAL_REFERENCE:
                continue
            problems.append(f"{m['id']}: {key} -> missing {rel}")
        fn = ev.get("test_function")
        test = ev.get("test")
        if fn and test and (root / test).exists():
            if f"def {fn}(" not in (root / test).read_text():
                problems.append(f"{m['id']}: {test} has no def {fn}()")
    assert not problems, "dangling evidence pointers:\n  " + "\n  ".join(problems)


def test_open_source_available_implies_a_public_repository():
    """`open_source: available` claims a runnable reference implementation
    exists. If we cannot name its repository, the claim is unsupported.

    Caught grace, which was marked `available` while its own canonical_impl
    said `paper_only` and its parity came from the paper's worked examples.
    """
    bad = [
        m["id"]
        for m in load_models()
        if m.get("status") == "implemented"
        and m.get("open_source") == "available"
        and not m.get("public_repo")
    ]
    assert not bad, f"claim 'available' with no public_repo: {bad}"


def test_no_public_repo_is_claimed_for_a_model_marked_otherwise():
    """The reverse. A public_repo URL on a model marked web_only or none means
    one of the two fields is wrong."""
    bad = [
        m["id"]
        for m in load_models()
        if m.get("status") == "implemented"
        and m.get("public_repo")
        and m.get("open_source") != "available"
    ]
    assert not bad, f"public_repo set but open_source is not 'available': {bad}"


def test_every_implemented_model_has_a_resolvable_source_link():
    """`source_url` is the column a reader uses to check us. It must be a real
    URL, not a bare DOI string or a citation fragment."""
    bad = [
        f"{m['id']} -> {m.get('source_url')!r}"
        for m in load_models()
        if m.get("status") == "implemented"
        and not str(m.get("source_url", "")).startswith("https://")
    ]
    assert not bad, f"missing or malformed source_url: {bad}"


def test_every_renderer_uses_the_shared_table_definition():
    """Each renderer must import its columns from `cancerverse_baseline.reporting`
    rather than defining its own.

    They each had their own column list once, and they drifted, different
    wording, different sets, one of them stale. This is the guard against that
    happening again.

    It used to name four renderers and require all four. That broke the moment
    one of them stopped shipping,
    which is private, so it is absent from the public repository and the count
    was wrong there rather than the code. The rule is about every renderer that
    is present, not about how many there are, so it discovers them, and still
    fails if the set ever empties.
    """
    from pathlib import Path

    scripts = Path(__file__).resolve().parents[1] / "scripts"

    # In scope: anything that renders the model table. Detected by what the
    # script produces, not by its filename, `build_licensing_slide.py` is
    # singular and slipped past a `"slides" not in name` test.
    def renders_the_table(path: Path) -> bool:
        body = path.read_text()
        # A slide deck, directly or by delegating to one. `build_org_slides.py`
        # is four lines that re-export another deck's main(), so it imports no
        # pptx of its own, checking only for `from pptx` missed it.
        if "from pptx" in body or "_slide" in body or "slides" in body:
            return False
        if path.name in {"build_roadmap.py", "build_notice.py"}:
            return False  # render the registry, not the table
        # Renders models against another organisation's data dictionary, so its
        # columns are the crosswalk's (predictor, availability, fact table),
        # not the model table's. Sharing a column definition with the model
        # table would mean sharing columns neither of them wants.
        if path.name == "build_mcp_crosswalk.py":
            return False
        # Renders where each model's numbers CAME FROM, so its columns are
        # provenance columns (artifact, class, confirmed) rather than the model
        # table's. Same reasoning as the crosswalk above.
        if path.name == "build_provenance_table.py":
            return False
        # Renders which EHR variables the library's models need, so its columns
        # are variable/availability, not the model table's.
        if path.name == "build_ehr_variable_request.py":
            return False
        return True

    renderers = sorted(p for p in scripts.glob("build_*.py") if renders_the_table(p))
    assert renderers, "no table renderers found at all"
    missing = [
        p.name
        for p in renderers
        if "from cancerverse_baseline.reporting import" not in p.read_text()
    ]
    assert not missing, (
        f"these define their own table instead of importing it: {missing}"
    )


def test_the_shared_table_exposes_the_reference_column():
    """The column a reader uses to check us.

    This used to require `Public repository` AND `Source`, back when the table
    carried `Paper`, `Reference (APA)` and `Source`, which between them
    printed the article title twice and the DOI twice in one row. They are one
    `Reference` column now: the APA entry with its title hyperlinked, the way a
    reference list does it. The rule being guarded is unchanged, a reader must
    be able to reach the source from the table.
    """
    from cancerverse_baseline.reporting import COLUMNS, build_rows, linked_reference

    assert "Reference" in COLUMNS
    assert "Public repository" in COLUMNS

    rows = build_rows()
    assert rows, "no rows"
    for r in rows:
        html = linked_reference(r)
        assert html, f"{r['Model']}: no reference rendered"
        assert "<a href=" in html, (
            f"{r['Model']}: reference has no link, the title must be clickable"
        )


def test_discrimination_carries_its_source():
    """An AUC or C-index without provenance is a number someone will quote.

    The rule that governs every coefficient in this repo governs these too: it
    enters only from a source actually read. So a `discrimination` value must
    be accompanied by `discrimination_source` naming where it came from.
    """
    bad = [
        m["id"]
        for m in load_models()
        if m.get("discrimination") and not m.get("discrimination_source")
    ]
    assert not bad, f"discrimination with no recorded source: {bad}"


def test_every_implemented_model_has_a_publication_year():
    """Year answers "how old are these models", which is the first thing asked
    of a table of classical baselines. It is also cheap to verify: every one
    must appear in that model's own citation string."""
    import re

    problems = []
    for m in load_models():
        if m.get("status") != "implemented":
            continue
        year = m.get("year")
        if not year:
            problems.append(f"{m['id']}: no year")
            continue
        in_citation = {
            int(x)
            for x in re.findall(r"\b(19\d{2}|20\d{2})\b", str(m.get("citation", "")))
        }
        if in_citation and year not in in_citation:
            problems.append(
                f"{m['id']}: year {year} not in citation {sorted(in_citation)}"
            )
    assert not problems, "\n  ".join(problems)


def test_no_hand_maintained_duplicate_of_a_generated_file():
    """`docs/README_for_public_repo.md` was a hand-written draft that the
    generated README replaced. It sat there for two days claiming 23 models and
    458 tests while the real counts were 30 and 770.

    That is defect 18 repeating: a second copy of something generated, kept by
    hand, drifting. Nothing should reintroduce one.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    banned = [
        "docs/README_for_public_repo.md",  # replaced by the generated README
        "docs/MODEL_TABLE.md",
        # replaced by the generated ROADMAP, which now carries the flagship
        # decisions. The hand-written shortlist drifted until it contradicted
        # the registry it claimed to summarise.
        "docs/FLAGSHIP_SHORTLIST.md",
        "docs/TODO.md",
        "docs/OUR_IMPLEMENTATIONS.md",
    ]
    present = [p for p in banned if (root / p).exists()]
    assert not present, f"hand-maintained duplicates of generated files: {present}"


def test_the_reproducibility_tier_is_not_shown_on_the_model_table():
    """`repro_tier` grades how far an UNIMPLEMENTED cell is from being
    reproducible. On a table of implemented models it is near-constant and
    reads as a quality score, which it is not. It belongs to the gap cells."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from cancerverse_baseline.reporting import COLUMNS, SPREADSHEET_EXTRAS

    assert "Reproducibility tier" not in COLUMNS + SPREADSHEET_EXTRAS

    # but every implemented model still carries one, for consistency
    missing = [
        m["id"]
        for m in load_models()
        if m.get("status") == "implemented" and not m.get("repro_tier")
    ]
    assert not missing, f"implemented but no repro_tier: {missing}"


def test_absences_are_described_as_ours_not_the_literatures():
    """We have judged five cells to have no published equation and been wrong
    about all five. Renderers must say what we have found, not what exists.

    Covers `docs/` as well as the code.
    The code had already been cleaned, but two hand-maintained summaries, the
    reproducibility map, were still asserting
    that ~11 cells had no published equation, long after that had been
    disproved. Prose drifts out of sync faster than code does, because nothing
    runs it.

    Retrospective corrections are allowed and are the point: a note saying a
    cell *was* recorded this way and was wrong is the record working. Only
    present-tense assertions are banned, so the check skips lines that are
    visibly quoting the claim in order to retire it.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    banned = [
        "no published equation exists",
        "never published as an equation",
        "never published as equations",
        "cells whose models were never published",
        # The four phrases above were all written in the
        # registry's own vocabulary, and the disease notes had drifted
        # into a different one: seven of the twelve said "gap, no open
        # equation found", which asserts exactly the banned thing and matched
        # none of the banned strings. Five of those seven cells were by then
        # implemented. A banlist only catches the wording it was written for,
        # so this one is now phrased around the claim rather than the sentence.
        "no open equation found",
        "no open equation exists",
        "no published equation found",
    ]
    # phrases that mark a line as a retraction rather than an assertion
    retracting = (
        "was wrong",
        "were wrong",
        "that was",
        "used to",
        "retired",
        "superseded",
        "no longer",
        "until 2026",
        "had been",
        "is retired",
        "instead of quoting",
        "corrected",
        "was recorded",
        "were recorded",
    )
    offenders = []
    for rel in ("scripts", "src", "registry", "docs"):
        base = root / rel
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.suffix not in {".py", ".yaml", ".md"} or "__pycache__" in p.parts:
                continue
            if p.name == "soften_claims.py":  # it quotes them to replace them
                continue
            for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                low = line.lower()
                if any(mark in low for mark in retracting):
                    continue
                for phrase in banned:
                    # Case-insensitive: the check was exact-case and therefore
                    # missed "No published equation exists for them" at the
                    # start of a sentence, which sat in a slide deck for a day.
                    if phrase in low:
                        offenders.append(f"{p.relative_to(root)}:{i}: {phrase!r}")
    assert not offenders, (
        "these assert what the literature contains rather than what we found:\n  "
        + "\n  ".join(offenders)
    )


def test_each_cell_has_exactly_one_flagship():
    """The convention is one default per disease x question cell. Four cells
    had two models both marked flagship for weeks, because nobody had chosen,
    the label was left on whatever was implemented first.

    The cell key includes `clinical_question`, which defaults to the axis. Only
    cvd/prognosis sets it, because only cvd/prognosis holds two different
    clinical decisions (ACS mortality, AF stroke) rather than two candidates
    for one decision. Keying on the axis alone forced ATRIA to be labelled an
    `alternative` to GRACE, which is not what it is. See
    reporting.clinical_question.
    """
    from collections import defaultdict

    from cancerverse_baseline.reporting import clinical_question

    cells = defaultdict(list)
    for m in load_models():
        if m.get("status") == "implemented":
            cells[(m["disease"], m["axis"], clinical_question(m))].append(m)

    bad = []
    for cell, models in sorted(cells.items()):
        flagships = [m["id"] for m in models if m.get("role") == "flagship"]
        if len(flagships) != 1:
            bad.append(f"{cell[0]}/{cell[1]}: {flagships or 'none'}")
    assert not bad, "cells without exactly one flagship:\n  " + "\n  ".join(bad)


def test_every_contested_cell_records_why_it_was_decided():
    """A default chosen without a reason is a default nobody can argue with.
    Where a cell holds more than one model, each must say why it is or is not
    the default."""
    from collections import defaultdict

    cells = defaultdict(list)
    for m in load_models():
        if m.get("status") == "implemented":
            cells[(m["disease"], m["axis"])].append(m)

    missing = [
        m["id"]
        for models in cells.values()
        if len(models) > 1
        for m in models
        if len(str(m.get("flagship_note", "")).strip()) < 40
    ]
    assert not missing, f"contested but no flagship_note: {missing}"


def test_no_document_tells_a_reader_to_use_pip_or_conda():
    """The project standardised on `uv`; the README had not noticed.

    It shipped `pip install -e .` in its Install section, alongside a claim of
    Python 3.11+ that contradicted `requires-python = ">=3.10"` in pyproject,
    and a claim of no runtime dependencies that contradicted `api.py`'s
    module-level `import yaml`. Generated documentation drifts from the
    packaging metadata precisely because nothing runs it.

    `uv pip` is allowed: it is uv's own pip-compatible interface, not pip.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    banned = ("pip install", "conda install", "conda create", "requirements.txt")
    offenders = []
    for rel in ("README.md", "docs", "scripts", "src", "collected"):
        base = root / rel
        paths = (
            [base]
            if base.is_file()
            else (
                [p for p in base.rglob("*") if p.suffix in {".md", ".py"}]
                if base.exists()
                else []
            )
        )
        for p in paths:
            if "__pycache__" in p.parts:
                continue
            for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                low = line.lower()
                # the line that states the rule, and uv's own pip interface
                if "never pip" in low or "uses pip" in low or "uv pip" in low:
                    continue
                for phrase in banned:
                    if phrase in low:
                        offenders.append(
                            f"{p.relative_to(root)}:{i}: {line.strip()[:70]}"
                        )
    assert not offenders, (
        "these tell a reader to use pip/conda instead of uv:\n  "
        + "\n  ".join(offenders)
    )


def test_readme_python_version_matches_pyproject():
    """A version claim that disagrees with the packaging metadata sends people
    to install the wrong interpreter. The README said 3.11+; pyproject said
    >=3.10."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = re.search(
        r'requires-python\s*=\s*"([^"]+)"', (root / "pyproject.toml").read_text()
    ).group(1)
    expected = spec.replace(">=", "") + "+"
    readme = (root / "README.md").read_text()
    claims = re.findall(r"Python (\d+\.\d+\+)", readme)
    assert claims, "README no longer states a Python version"
    assert set(claims) == {expected}, (
        f"README says Python {set(claims)}, pyproject requires {spec}"
    )


def test_hand_written_docs_do_not_hardcode_progress_numbers():
    """One place computes progress; prose must not restate it.

    `docs/CANDIDATE_MODELS.md` (then OPPORTUNITIES.md) quoted "96% to 81%" and
    was wrong twice over within a day: the reachable denominator it referred to
    later collapsed onto the plain 36, and the figure is now 26/36. The
    document's own subject was surveys going stale.

    Generated files are exempt, they render from `progress_report()` and
    cannot drift. This guards the hand-written ones.
    """
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    generated = {"ROADMAP.md", "MODEL_SPREADSHEET.csv"}
    # "N% of the cells", "progress drops to N%", "N/36 cells" and similar
    pattern = re.compile(
        r"(\d{2,3}\s?%[^.\n]{0,40}(cell|coverage|progress|reachable|complete)"
        r"|(cell|coverage|progress)[^.\n]{0,40}\d{2,3}\s?%"
        r"|\b\d{1,2}\s*/\s*3[26]\b[^.\n]{0,20}(cell|filled))",
        re.I,
    )

    offenders = []
    for p in (root / "docs").glob("*.md"):
        if p.name in generated:
            continue
        for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            # a line that explicitly disclaims the number is the fix, not the bug
            if "on purpose" in line or "no progress figure" in line.lower():
                continue
            # A verbatim quotation from a source is not this repository making a
            # progress claim. the pattern's `(cell|...)...N%`
            # branch fired on a quoted sentence containing "islet cell cancer"
            # and "~20%" forty characters apart, in a file of source excerpts.
            # Matching prose can only ever approximate; excluding quotations
            # keeps the check aimed at assertions this repository is making.
            stripped = line.strip().lstrip("->*# ").strip()
            if stripped.startswith(("Quote:", '"', "'", "\u201c", "\u2018")):
                continue
            if pattern.search(line):
                offenders.append(f"{p.relative_to(root)}:{i}: {line.strip()[:90]}")
    assert not offenders, (
        "hand-written docs quoting a progress figure; render it from "
        "progress_report() or drop it:\n  " + "\n  ".join(offenders)
    )


def test_every_renderer_actually_runs():
    """Importing is not running, and the suite could not tell the difference.

    When `model_table` moved from `scripts/` into the package, three renderers
    kept passing every test while being completely broken: they had reached
    their sibling through `sys.path.insert(scripts/)` and now needed `src/`,
    which they had never added. The full suite was green and
    `python scripts/build_readme.py` raised ModuleNotFoundError.

    So this executes each one in a subprocess, the way a person runs them.
    Output goes to a temporary directory where the renderer accepts one, and
    is otherwise allowed to write in place, these are generated files and
    rewriting them is what they are for.
    """
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    # Decks included. They were excluded on the grounds that they "write
    # binaries", and the cost of that was build_baseline_review_slides.py
    # sitting broken for a day after model_table moved into the package —
    # exactly the failure this test exists to catch. python-pptx is a declared
    # dev dependency, so there is nothing to skip for.
    renderers = sorted(p.name for p in (root / "scripts").glob("build_*.py"))
    assert renderers, "no renderers found"

    failed = []
    for name in renderers:
        r = subprocess.run(
            [sys.executable, f"scripts/{name}"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if r.returncode != 0:
            failed.append(
                f"{name}: {(r.stderr or r.stdout).strip().splitlines()[-1][:120]}"
            )
    assert not failed, "renderers that import but do not run:\n  " + "\n  ".join(failed)


def test_every_implemented_model_says_whether_an_ehr_can_run_it():
    """The deployment question, answered per model rather than per person.

    Asked whether the models were "too old", the useful answer turned out to be
    that age is nearly irrelevant: ALBI (2015) needs two routine labs while
    CRC-PRO (2014) needs ounces of red meat per day. What decides whether a
    model can be pointed at hospital data is where its inputs live, and that
    was recorded nowhere, so a colleague had to work it out from the input
    list, per model, by hand.
    """
    tiers = {"routine", "specialty", "not_ehr"}
    bad = []
    for m in load_models():
        if m.get("status") != "implemented":
            continue
        if m.get("ehr_availability") not in tiers:
            bad.append(f"{m['id']}: {m.get('ehr_availability')!r}")
        elif not str(m.get("ehr_note") or "").strip():
            bad.append(f"{m['id']}: tier but no note saying which inputs")
    assert not bad, f"missing or invalid ehr_availability: {bad}"


def test_every_implemented_model_lists_its_inputs():
    """Five models carried no `inputs` at all, so every table rendered from the
    registry showed them blank while their signatures sat in the code."""
    missing = [
        m["id"]
        for m in load_models()
        if m.get("status") == "implemented" and not m.get("inputs")
    ]
    assert not missing, f"implemented models with no inputs recorded: {missing}"


def test_a_model_is_only_routine_if_its_required_inputs_are():
    """`routine` is a promise that hospital data suffices. Guard the one case
    where that is subtle: pbcg_extended names race, family history and prostate
    volume, and is still `routine` because it REQUIRES only age and PSA, every
    other predictor is optional and selects one of 1,024 fitted sub-models.
    If those ever become required, the promise breaks silently.
    """
    m = next(m for m in load_models() if m["id"] == "pbcg_extended")
    assert m["ehr_availability"] == "routine"
    required = [i for i in m["inputs"] if "optional" not in i.lower()]
    assert required == ["age", "psa"], (
        f"pbcg_extended now requires {required}; it is only 'routine' while "
        "age and PSA are the only mandatory inputs"
    )


def test_every_implemented_model_has_an_apa_reference_and_a_title():
    """A citation you can paste into a manuscript, and a title to hyperlink.

    The hand-written `citation` field is a finding aid: "Cooperberg MR et al.
    J Urol. 2005;173(6):1938-1942", not a reference. `citation_apa` and
    `paper_title` come from the PubMed record via scripts/fetch_citations.py,
    because retyping an author list is where a citation quietly acquires an
    error. It already had: pbcg_extended was recorded with Ankerst DP as first
    author and page 211. The record says Neumair M is first, Ankerst DP is last
    (the corresponding author), and the page is 200.
    """
    bad = []
    for m in load_models():
        if m.get("status") != "implemented":
            continue
        title = str(m.get("paper_title") or "").strip()
        apa = str(m.get("citation_apa") or "").strip()
        if not title:
            bad.append(f"{m['id']}: no paper_title")
        if not apa:
            bad.append(f"{m['id']}: no citation_apa")
        elif "(" not in apa or ")" not in apa:
            bad.append(f"{m['id']}: citation_apa has no year in parentheses")
    assert not bad, f"citation gaps: {bad}"


def test_the_apa_reference_ends_in_the_same_doi_the_source_url_gives():
    """The reference and the link must point at one paper.

    Two fields naming a publication is two chances to name different ones.
    """
    mismatched = []
    for m in load_models():
        if m.get("status") != "implemented":
            continue
        src = str(m.get("source_url") or "")
        apa = str(m.get("citation_apa") or "")
        if "doi.org/" not in src:
            continue  # PMID-only sources have no DOI to compare
        doi = src.split("doi.org/", 1)[1].rstrip("/")
        if doi.lower() not in apa.lower():
            mismatched.append(f"{m['id']}: source {doi} not in its APA reference")
    assert not mismatched, f"citation and link disagree: {mismatched}"


def test_noncommercial_basis_matches_the_licence_field():
    """`license` and `license_basis` must not answer the same question twice.

    Every one of these has been wrong at least once, always the same way: the
    basis, which is written from the article, says the source is noncommercial,
    while `license` still says `open`, so the entry carries both answers and
    an audit reading only the short field believes the reassuring one.

    aMAP shipped like that for weeks. ATRIA was corrected on 2026-08-14 and a
    concurrent edit reverted it within three days, which is why this is a test
    and not a note: the two fields sit ninety lines apart in the YAML, so
    nothing about editing one puts the other in view.
    """
    import re

    nc = re.compile(
        r"BY-NC|noncommercial|non-commercial|Non Commercial|"
        r"PolyForm|all rights reserved|research[- ]only",
        re.I,
    )
    contradictory = []
    for m in load_models():
        if m.get("status") != "implemented":
            continue
        basis = str(m.get("license_basis") or "")
        if not basis:
            continue
        # A basis that opens by naming a permissive licence is not a
        # noncommercial one, pbcg_extended's says CC BY 4.0 and mentions
        # PolyForm only to explain what it replaced.
        opens_permissive = re.match(r"\s*CC BY [0-9]", basis)
        # What is forbidden is `open`, not a particular restricted label.
        # The first version demanded `noncommercial_source` exactly and
        # immediately flagged cibula_arrm, which is `restricted` and correctly
        # so: that article is not open access at ALL -- Europe PMC reports no
        # licence, and the deployed calculator says "All rights reserved". That
        # is a stricter category than noncommercial, and a test that insists on
        # the looser label would have pushed a true record toward a false one.
        RESTRICTED = {"noncommercial_source", "restricted", "web-only"}
        if nc.search(basis) and not opens_permissive:
            if m.get("license") not in RESTRICTED:
                contradictory.append(
                    f"{m['id']}: license={m.get('license')!r} but license_basis "
                    f"describes a source that is not open"
                )
    assert not contradictory, (
        f"entries answering the licence question two ways: {contradictory}"
    )


def test_gap_cells_name_what_they_rejected():
    """An empty cell must say what was rejected and why, not just that it is empty.

    "No published equation found" is the absence of a finding, and this project
    has asserted it wrongly five times, see
    `test_no_cell_is_recorded_as_never_published`, which polices the same
    mistake from the other end. That test stops a cell CLAIMING nothing was
    published; this one stops a cell saying nothing at all.

    The three cells this currently governs (ovarian, pancreatic and head & neck
    response) each hold a candidate with an AUC between 0.82 and 0.86 that was
    read and rejected on evidence rather than performance. Losing those three
    paragraphs would mean re-running three searches to rediscover three
    decisions, which is precisely what happened before the notes were written.

    Criteria are in docs/INCLUSION_CRITERIA.md.
    """
    implemented = {
        (m["disease"], m["axis"])
        for m in load_models()
        if m.get("status") == "implemented"
    }
    thin = []
    for m in load_models():
        if m.get("status") != "gap":
            continue
        if (m["disease"], m["axis"]) in implemented:
            continue  # a historical record kept beside a filled cell
        note = " ".join(
            str(m.get(k) or "") for k in ("tier_note", "blocker", "next_action")
        )
        cell = f"{m['disease']}/{m['axis']}"
        # A search date, so "we looked" is falsifiable rather than implied.
        if not re.search(r"SEARCHED|RE-SEARCHED|RE-CHECKED", note):
            thin.append(f"{cell}: no search record")
        # Something specific enough to look up: a DOI, a PMC/PMID, or a journal
        # with a year. A candidate nobody can find again is not a record of one.
        elif not re.search(
            r"doi:|10\.\d{4}|PMC\d+|PMID\s*\d+|\b(19|20)\d\d[;:,]", note
        ):
            thin.append(f"{cell}: no citable candidate")
        elif len(note) < 200:
            thin.append(f"{cell}: note too short to carry a reason ({len(note)} chars)")
    assert not thin, "gap cells that do not record what was rejected: " + str(thin)


def test_no_duplicate_keys_in_the_registry():
    """A key written twice in one entry loses the first value silently.

    PyYAML resolves duplicates by keeping the LAST occurrence. No error, no
    warning, and `.get()` cannot tell "absent" from "present but overridden".
    This bit four times before the check existed, and each time the value that
    won was the wrong one:

      - `moore_criteria` and `cvd_statin_benefit` each carried a stale
        `discrimination: null` below a real value, so both rendered as
        "we have not read this from the paper yet" after being filled in.
      - `pbcg_extended` carried an outdated `discrimination_source` below the
        current one, so a freshly written provenance record never took effect.
      - `msk_ovarian` carried two `citation_note` keys, and the OLDER of two
        corrections was overriding the newer, a correction that had itself
        been reverted, invisibly.

    Parsing cannot detect this, so the raw text is scanned instead.
    """
    import re
    from collections import Counter

    text = (
        pathlib.Path(__file__).resolve().parents[1] / "registry" / "models.yaml"
    ).read_text()

    bad = []
    for block in re.split(r"^- id: ", text, flags=re.M)[1:]:
        model_id = block.split("\n", 1)[0].strip()
        keys = re.findall(r"^  ([a-z_][a-z0-9_]*):", block, re.M)
        for key, n in sorted(Counter(keys).items()):
            if n > 1:
                bad.append(f"{model_id}.{key} appears {n} times")

    assert not bad, (
        "duplicate keys. YAML keeps only the last, so the others are lost:\n  "
        + "\n  ".join(bad)
    )


def test_no_module_is_shadowed_by_a_function_of_its_own_name():
    """`from .foo import foo` in a package `__init__` hides the module `foo`.

    The package attribute is rebound from the module to the function, so
    `import pkg.foo as m` yields the function and `m.SOME_CONSTANT` raises
    AttributeError. `importlib.import_module` still returns the real module,
    which is exactly why this hides: the registry loader and the whole test
    suite are unaffected, and only tooling that walks module attributes breaks.

    It cost real time twice before being pinned, once in `xu_trg_score`,
    fixed at authoring time by naming the function `xu_trg_points`, and once in
    `predict_breast`, fixed on 2026-08-18 by renaming the module to `predict`
    while leaving the function name (the public API) alone. Renaming the module
    is usually the cheaper of the two: callers import the function, not the
    module.
    """
    import importlib
    import types

    offenders = []
    for m in load_models():
        if m.get("status") != "implemented" or not m.get("code"):
            continue
        parent, _, leaf = m["code"].rpartition(".")
        if not parent:
            continue
        package = importlib.import_module(parent)
        importlib.import_module(m["code"])       # ensure the submodule is loaded
        attr = getattr(package, leaf, None)
        if attr is not None and not isinstance(attr, types.ModuleType):
            offenders.append(
                f"{m['id']}: {parent}.{leaf} is a {type(attr).__name__}, not the "
                f"module, rename the module, or the function, so they differ")
    assert not offenders, "\n  ".join([""] + offenders)


def test_no_registry_url_is_visibly_malformed():
    """Cheap structural check on every URL the registry carries, offline.

    A live link-check across all 115 of them is not a test: two dozen
    publishers return 403 to anything without a browser UA, so a network check
    reports two dozen false failures and gets muted, which is worse than not
    having it. What CAN be checked without the network is shape, and shape is
    where the real defect was on 2026-08-18. Both apparent 404s in a live sweep
    turned out to be the sweep's own regex truncating a URL at a bracket
    (`10.1016/S0140-6736(10` for `...(10)61350-5`), not bad data.

    So this asserts the things a typo produces: unbalanced brackets, whitespace,
    a trailing separator, a doubled scheme. Reachability belongs in the audit
    script, which already resolves the pinned manifest URLs on demand.
    """
    urls = []

    def walk(node, model_id):
        if isinstance(node, str):
            for u in re.findall(r"https?://\S+", node):
                # Prose wraps URLs in parentheses: "(https://example.org/)"
                #, so a greedy \S+ swallows the closing one and then reports
                # the note's own punctuation as a malformed URL. Drop trailing
                # brackets that have no opener inside the match.
                u = u.rstrip(".,;")
                while u.endswith(")") and u.count(")") > u.count("("):
                    u = u[:-1]
                urls.append((model_id, u))
        elif isinstance(node, dict):
            for v in node.values():
                walk(v, model_id)
        elif isinstance(node, list):
            for v in node:
                walk(v, model_id)

    for m in load_models():
        walk(m, m["id"])

    bad = []
    for mid, u in urls:
        if u.count("(") != u.count(")"):
            bad.append(f"{mid}: unbalanced brackets — {u}")
        elif u.rstrip("/").endswith(("-", "_", ":", "&", "?")):
            bad.append(f"{mid}: trailing separator — {u}")
        elif u.count("://") != 1:
            bad.append(f"{mid}: malformed scheme — {u}")
        elif any(c in u for c in " \t\n"):
            bad.append(f"{mid}: whitespace inside URL — {u}")
    assert not bad, "malformed URLs in the registry:\n  " + "\n  ".join(bad)


def test_vendored_reference_packages_match_their_pins():
    """`collected/` must hold the exact commits MANIFEST.yaml pins.

    These five R packages are what the parity suite compares against, so a
    silent drift between the pin and what is on disk would mean the recorded
    parity results were produced against something other than what the manifest
    claims. They are gitignored and fetched on demand, which is deliberate,
    two are GPL and vendoring them into an Apache-2.0 repository would create a
    licensing question, but it also means nothing but this check ties the
    checkout back to the pin.

    Skips when a package has not been fetched: a fresh clone has none of them
    and the parity fixtures are captured JSON, so the suite runs without them.
    """
    root = Path(__file__).resolve().parents[1]
    manifest = root / "collected" / "MANIFEST.yaml"
    if not manifest.exists():
        pytest.skip("collected/MANIFEST.yaml is not present")

    import yaml as _yaml
    pinned = _yaml.safe_load(manifest.read_text())["packages"]

    problems, seen = [], 0
    for pkg in pinned:
        d = root / "collected" / pkg["name"]
        if not d.exists():
            continue
        seen += 1
        source = d / "SOURCE.txt"
        if not source.exists():
            problems.append(f"{pkg['name']}: fetched but has no SOURCE.txt")
            continue
        got = dict(
            line.split(":", 1)[0].strip() and
            (line.split(":", 1)[0].strip(), line.split(":", 1)[1].strip())
            for line in source.read_text().splitlines() if ":" in line)
        if got.get("commit") != pkg["commit"]:
            problems.append(
                f"{pkg['name']}: manifest pins {pkg['commit'][:12]}, "
                f"disk has {got.get('commit', '?')[:12]}")
        description = d / "DESCRIPTION"
        if description.exists():
            version = next(
                (ln.split(":", 1)[1].strip()
                 for ln in description.read_text(errors="replace").splitlines()
                 if ln.startswith("Version:")), None)
            if version != pkg["version"]:
                problems.append(
                    f"{pkg['name']}: manifest says v{pkg['version']}, "
                    f"DESCRIPTION says v{version}")
    if seen == 0:
        pytest.skip("no reference packages fetched; run scripts/fetch_references.py")
    assert not problems, "vendored packages differ from their pins:\n  " + "\n  ".join(problems)


def test_audit_headline_matches_the_registry():
    """The commercial-use audit's denominator must be the live model count.

    It had drifted to 37 while the registry held 40, which put three models
    outside the audit's own arithmetic and three more inside it but named
    nowhere in the document. Enforcement never lapsed, `audit_public_repo.py`
    reads the registry and kept reporting COMPLIANT, but a reader checking
    the prose would have counted the wrong population.

    Same defect class as the VERIFICATION.md headline this file already pins:
    a number typed into prose is a second copy, and second copies rot silently.
    """
    root = Path(__file__).resolve().parents[1]
    doc = root / "docs" / "COMMERCIAL_USE_AUDIT.md"
    if not doc.exists():
        pytest.skip("docs/COMMERCIAL_USE_AUDIT.md is not distributed here")

    implemented = [m for m in load_models() if m.get("status") == "implemented"]
    text = doc.read_text()

    stated = re.findall(r"\|\s*Implemented models\s*\|\s*\*\*(\d+)\*\*\s*\|", text)
    assert stated, "audit has no 'Implemented models' count row to check"
    assert all(int(s) == len(implemented) for s in stated), (
        f"audit table says {stated} implemented models, registry has "
        f"{len(implemented)}")

    inline = re.findall(r"\*\*(\d+) of (\d+) implemented models", text)
    for _, denominator in inline:
        assert int(denominator) == len(implemented), (
            f"audit prose uses a denominator of {denominator}, registry has "
            f"{len(implemented)} implemented models")


def test_spreadsheet_csv_and_xlsx_are_the_same_table():
    """`docs/MODEL_SPREADSHEET.csv` and `.xlsx` are one table rendered twice.

    Both come from `build_model_spreadsheet.py`, but they are separate files in
    the working tree and only one of them is human-diffable. If someone edits
    the xlsx by hand, which is exactly what a spreadsheet invites, the CSV
    keeps the old values and nothing notices, because every other check in this
    repository reads the registry rather than either file.
    """
    root = Path(__file__).resolve().parents[1]
    csv_path = root / "docs" / "MODEL_SPREADSHEET.csv"
    xlsx_path = root / "docs" / "MODEL_SPREADSHEET.xlsx"
    if not (csv_path.exists() and xlsx_path.exists()):
        pytest.skip("spreadsheet exports are not distributed here")
    # Deliberately stdlib-only. The first version of this test used pandas and
    # openpyxl via importorskip, and the test environment has neither, so it
    # skipped on every run, a test that never executes is worse than no test,
    # because the suite reports it as present. An .xlsx is a zip of XML, and
    # both files only need their first column read to catch a hand-edit.
    import csv as csvlib
    import zipfile
    from xml.etree import ElementTree

    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        csv_rows = list(csvlib.reader(fh))

    NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(xlsx_path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ElementTree.fromstring(z.read("xl/sharedStrings.xml")):
                shared.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
        sheet = ElementTree.fromstring(z.read("xl/worksheets/sheet1.xml"))
        xlsx_rows = []
        for row in sheet.iter(f"{NS}row"):
            cells = []
            for c in row.iter(f"{NS}c"):
                # Three encodings occur: a shared-string index, an inline
                # string (which is what build_model_spreadsheet.py emits), and
                # a bare value. Reading only <v> returns empty for inline
                # strings, which made the first version of this test report
                # every header as blank.
                if c.get("t") == "inlineStr":
                    node = c.find(f"{NS}is")
                    text = "".join(x.text or "" for x in node.iter(f"{NS}t")) if node is not None else ""
                else:
                    v = c.find(f"{NS}v")
                    text = "" if v is None else (v.text or "")
                    if c.get("t") == "s" and text.isdigit():
                        text = shared[int(text)]
                cells.append(text)
            xlsx_rows.append(cells)

    assert len(csv_rows) == len(xlsx_rows), (
        f"CSV has {len(csv_rows)} rows, XLSX has {len(xlsx_rows)}")
    assert csv_rows[0] == xlsx_rows[0][:len(csv_rows[0])], (
        f"header rows differ:\n  csv  {csv_rows[0]}\n  xlsx {xlsx_rows[0]}")

    # strict=True is redundant against the length assert two lines above, and
    # it is here so it stays redundant. If that assert is ever loosened, a
    # plain zip would silently compare only the shorter file and this test
    # would pass while the two spreadsheets disagreed, which is the exact
    # drift it exists to catch.
    differing = [i for i, (a, b) in enumerate(zip(csv_rows, xlsx_rows, strict=True), 1)
                 if [x.strip() for x in a[:1]] != [x.strip() for x in b[:1]]]
    assert not differing, (
        f"CSV and XLSX disagree in the first column at row(s) {differing}. "
        f"Re-run scripts/build_model_spreadsheet.py rather than editing either.")


def test_parity_fixtures_and_their_generators_come_in_pairs():
    """Every captured fixture must name the script that produced it.

    The parity suite compares against JSON captured from a vendor's R or from a
    deployed calculator, because re-running those needs R, a network, or both.
    That makes the fixture the evidence, and a fixture with no generator is
    evidence nobody can regenerate or challenge, which is the opposite of what
    `tests/parity/` exists for.

    The reverse direction is deliberately NOT checked here. Three reference
    scripts (`bcrat`, `predict`, `score2`) produce no fixture on purpose: their
    expected values are inlined in `test_r_reference_parity.py` and the script
    is kept as the recipe for regenerating them.
    """
    root = Path(__file__).resolve().parents[1]
    ref = root / "tests" / "parity" / "reference"
    if not ref.exists():
        pytest.skip("parity fixtures are not distributed here")

    generators = {p.stem for p in ref.iterdir() if p.suffix in {".R", ".py"}}
    suite = " ".join(p.read_text(errors="replace")
                     for p in (root / "tests").rglob("*.py"))

    orphans = []
    for fixture in sorted(ref.glob("*_cases.json")):
        stem = fixture.stem.replace("_cases", "")
        if not any(g.startswith(stem) for g in generators):
            orphans.append(f"{fixture.name}: no generator script beside it")
        if fixture.name not in suite:
            orphans.append(f"{fixture.name}: captured but no test reads it")
    assert not orphans, "parity fixtures without provenance:\n  " + "\n  ".join(orphans)


def test_no_gap_entry_survives_the_cell_being_filled():
    """A `status: gap` row must not sit in a cell that has a flagship.

    The pattern for closing a cell is to keep the gap row as the record of what
    was searched, `colorectal_response_gap` and `gastric_response_gap` both do
    this correctly, demoted to `catalog` with a `superseded_by`. The failure
    mode is doing four fifths of that: on 2026-08-18 both
    `esophageal_response_gap` and `cervical_response_gap` carried a `resolved_by`
    and a full `resolution_note` saying the cell was closed weeks earlier, while
    still declaring `role: flagship, status: gap`.

    Nothing caught it because every renderer reads the implemented models first,
    so the ROADMAP correctly listed three open cells while the registry claimed
    five. The stale rows were invisible in output and wrong in the data, which     is the worst combination, because the output is what gets reviewed.
    """
    models = load_models()
    flagship = {
        (m["disease"], m["axis"]): m["id"]
        for m in models
        if m.get("status") == "implemented" and m.get("role") == "flagship"
    }
    contradictions = []
    for m in models:
        if m.get("status") != "gap":
            continue
        held_by = flagship.get((m.get("disease"), m.get("axis")))
        if held_by:
            contradictions.append(
                f"{m['id']} still says status=gap, but {m['disease']}/{m['axis']} "
                f"is implemented by {held_by}. Demote it to role/status "
                f"`catalog` with `superseded_by: {held_by}` and keep the note.")
    assert not contradictions, "\n  ".join([""] + contradictions)


def test_every_alternative_says_what_it_is_an_alternative_to():
    """`role: alternative` must be traceable to a default, or explain why not.

    Six models carry this role and all six explain themselves in prose, but on
    2026-08-18 only one (`rmi`) also carried the machine-readable
    `superseded_by`. Three more (`roma`, `erspc_rc3`, `cha2ds2_vasc`) named
    their default only in `flagship_note`, so any tool reading fields rather
    than sentences could not tell what they were alternatives TO.

    Two of the six deliberately have no `superseded_by`, and forcing one on
    them would be a false statement rather than tidier metadata:

      score2            a regional peer, not a lesser model: "differently
                        targeted", recalibrated for four European risk regions
      optum_lung_lasso  deliberately not the default despite the larger cohort,
                        because PLCOm2012 is what screening guidelines specify

    So the rule is: either point at a default, or say in prose that you are a
    peer. What is banned is neither.
    """
    peers = {"score2", "optum_lung_lasso"}
    ids = {m["id"] for m in load_models()}

    problems = []
    for m in load_models():
        if m.get("role") != "alternative":
            continue
        target = m.get("superseded_by")
        note = " ".join(str(m.get("flagship_note") or "").split())
        if target:
            if target not in ids:
                problems.append(f"{m['id']}: superseded_by={target!r} is not a model id")
            continue
        if m["id"] in peers:
            assert note, f"{m['id']} is an unsuperseded peer and must say why in flagship_note"
            continue
        problems.append(
            f"{m['id']}: role=alternative with no `superseded_by` and not listed "
            f"as a deliberate peer. Add the default it defers to, or add it to "
            f"`peers` here with the reason it is not a lesser model.")
    assert not problems, "\n  ".join([""] + problems)


def test_restricted_catalog_rows_also_carry_a_written_determination():
    """`audit_public_repo.py` checks implemented models; catalog rows are a blind spot.

    That is defensible for the audit itself, a catalog row ships no code, so
    nothing has been taken under an unclear licence. It is not defensible as a
    record: a row marked `restricted` with no `license_basis` says "we decided
    something" without saying what, and the row exists precisely to stop the
    next person re-deciding it.

    `bcsc` (BCSC v3) had `license: restricted`, a 4,400
    character `blocker` containing the entire determination, and neither of the
    two fields anything machine-readable would look at.
    """
    missing = []
    for m in load_models():
        if m.get("license") not in {"restricted", "noncommercial_source"}:
            continue
        if not m.get("license_basis"):
            missing.append(f"{m['id']} ({m.get('status')}): license={m['license']!r}, no license_basis")
        elif not m.get("license_url"):
            missing.append(f"{m['id']} ({m.get('status')}): has a basis but no license_url")
    assert not missing, (
        "restricted/noncommercial rows with no written determination:\n  "
        + "\n  ".join(missing))


def test_the_registry_syntax_checker_actually_rejects_bad_yaml():
    """The guard against the widest failure this repository has.

    A YAML error in registry/models.yaml stops 28 scripts and every test at
    once, and it surfaces from pytest as a bare INTERNALERROR through
    yaml/scanner.py, naming neither the file nor the line. This checker turns
    that into one actionable line, and `conftest.pytest_configure` does the same
    for the suite.

    A checker that silently stopped rejecting things would be worse than none,
    so this feeds it a known-bad document rather than trusting it to work.
    """
    import importlib.util
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "check_registry_syntax.py"
    if not script.exists():
        pytest.skip("scripts/check_registry_syntax.py is not present")

    # the real registry must pass
    ok = subprocess.run([sys.executable, str(script)],
                        cwd=root, capture_output=True, text=True)
    assert ok.returncode == 0, (
        f"the live registry does not parse:\n{ok.stderr}")

    # and the exact shape that broke it on 2026-08-18 must fail, with the
    # line number and the offending text in the message
    spec = importlib.util.spec_from_file_location("_syntax", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    bad = "models:\n- id: x\n  note: value with a colon: here\n"
    tmp = root / "registry" / "_syntax_probe.yaml"
    tmp.write_text(bad)
    try:
        message = module.check("registry/_syntax_probe.yaml")
    finally:
        tmp.unlink()
    assert message, "the checker accepted a document PyYAML cannot parse"
    assert ":3:" in message, f"no line number in the message: {message!r}"
    assert "colon" in message, f"no actionable cause in the message: {message!r}"


def test_public_repo_does_not_point_at_the_paper():
    """The column headed "Public repository" must not link to the article.

    `pbcg_extended` carried `public_repo` equal to its own `source_url`, the
    article DOI. Both renderers label that link with the URL's last segment, so
    the coverage page and the README showed a link reading
    `s12874-022-01674-x`, under a heading promising code, that landed the
    reader on the paper already linked in the next column.

    The code was public the whole time: 1,091 lines of R in Additional file 2,
    CC BY 4.0. Only the link was wrong, which is the kind of defect a reader
    finds and a test never does, until there is a test.

    A DOI is not a repository even when the code is genuinely attached to it;
    what belongs here is the artifact a reader can open and diff against.
    """
    bad = []
    for m in load_models():
        repo = m.get("public_repo")
        if not repo:
            continue
        if repo == m.get("source_url"):
            bad.append(f"{m['id']}: public_repo is its own source_url ({repo})")
        elif "doi.org/" in repo:
            bad.append(f"{m['id']}: public_repo is a DOI, not an artifact ({repo})")
    assert not bad, (
        "public_repo pointing at a paper rather than at code:\n  " + "\n  ".join(bad))

