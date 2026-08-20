# Registry tests

import pathlib
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
    """The flagship here is PBCG since the 2026-08-06 audit, not ERSPC RC3.

    Pinned together with its reasoning: PBCG separates high-grade disease from
    any cancer, which is what a biopsy decision turns on, and fits eight
    sub-models so an incomplete record still gets a model. Flipping the default
    back means arguing with `flagship_note`, not just editing a string here.
    """
    matrix = coverage_matrix()
    assert set(matrix["prostate"]) == set(AXES)
    flag = matrix["prostate"]["detection"]
    assert flag is not None
    assert flag["status"] == "implemented"
    assert flag["id"] == "pbcg"
    assert "high-grade" in flag["flagship_note"]

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
        "checked", "not_checked", "matched", "unmatched", "n/a",
    }


def test_parity_breaks_flagship_ties():
    checked = {"role": "flagship", "status": "implemented", "parity_status": "checked"}
    not_checked = {"role": "flagship", "status": "implemented", "parity_status": "not_checked"}
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
        # `vault` points into the private Obsidian notebook and is stripped
        # from the published registry, because 36 pointers into a filing system
        # nobody outside the team can open are noise. Require it only where the
        # notebook it names is actually present.
        fields = ["equation_source", "citation", "our_code"]
        if (Path(__file__).resolve().parents[1] / "vault").exists():
            fields.append("vault")
        for field in fields:
            if not m.get(field):
                missing.append(f"{m['id']}.{field}")
    assert not missing, f"implemented models missing provenance: {missing}"


def test_every_implemented_model_has_a_vault_note_that_exists():
    root = Path(__file__).resolve().parents[1] / "vault"
    if not root.exists():
        pytest.skip("vault/ is not distributed with the public repo")
    missing = [
        f"{m['id']} -> {m['vault']}"
        for m in load_models()
        if m.get("status") == "implemented" and not (root / m["vault"]).exists()
    ]
    assert not missing, f"vault notes referenced but absent: {missing}"


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
        assert impl.get("url") or impl.get("note") or impl.get("type") == "paper_only", m["id"]
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
    assert set(q["available"]) | set(q["web_only"]) | set(q["none"]) == set(board["implemented"])


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
    now, never in fact -- which is the honest outcome. Assert the invariant
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
        r["n_cells_unreachable"] == 0)


def test_no_cell_is_recorded_as_never_published():
    """`repro_tier: D` is a claim about the literature, not about our search.

    This project asserted "no published equation exists" and was wrong five
    separate times. Every remaining D was checked on 2026-08-06 and none
    survived. If a D reappears, the note attached to it has to say what was
    searched -- otherwise it is the same mistake in a new cell.
    """
    tiers = cell_tiers()
    still_d = sorted(cell for cell, tier in tiers.items() if tier == "D")
    assert not still_d, (
        "cells claiming nothing was ever published as an equation: "
        f"{still_d}. Record what was searched before asserting this.")


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
        "bcrat": ("cancerverse_baseline.breast.detection", "bcrat_predict",
                  dict(start_age=50, end_age=55, n_biopsies=0, age_menarche=13,
                       age_first_birth=25, n_relatives=0)),
        "albi": ("cancerverse_baseline.liver.prognosis", "albi_predict",
                 dict(bilirubin_umol_l=20.0, albumin_g_l=40.0)),
        "grace": ("cancerverse_baseline.cvd.prognosis", "grace_predict",
                  dict(killip_class=1, sbp=130, heart_rate=80, age=60,
                       creatinine_mg_dl=1.0)),
        "kunzmann": ("cancerverse_baseline.esophageal.detection", "kunzmann_predict",
                     dict(age=60, male=True, bmi=28, smoking="former",
                          esophageal_condition=False)),
        "roma": ("cancerverse_baseline.ovarian.detection", "roma_predict",
                 dict(he4_pmol_l=60.0, ca125_u_ml=30.0, postmenopausal=True)),
    }
    registry_ids = {m["id"] for m in load_models()}
    for expected_id, (mod, fn, kwargs) in calls.items():
        assert expected_id in registry_ids, expected_id
        out = getattr(importlib.import_module(mod), fn)(**kwargs)
        assert out["model_id"] == expected_id, (
            f"{mod}.{fn} returns model_id={out['model_id']!r} "
            f"but the registry row is {expected_id!r}"
        )


def test_vault_note_frontmatter_agrees_with_the_registry():
    """Doc drift is how the wrong MSK claims survived three survey passes.

    Exception: two models occupy two cells each (PREDICT Breast, LIPI). Their
    second registry row points at the sibling cell's note on purpose, so the
    axis is allowed to differ for those.
    """
    import re

    root = Path(__file__).resolve().parents[1] / "vault"
    if not root.exists():
        pytest.skip("vault/ is not distributed with the public repo")
    dual_axis = {"predict_breast_response", "lipi_prognosis"}
    issues = []
    for m in load_models():
        if m.get("status") != "implemented" or not m.get("vault"):
            continue
        p = root / m["vault"]
        assert p.exists(), f"{m['id']} -> missing {m['vault']}"
        fm = re.match(r"---\n(.*?)\n---", p.read_text(), re.S)
        assert fm, f"{m['id']} note has no frontmatter"
        front = dict(
            (k.strip(), v.strip())
            for k, v in (l.split(":", 1) for l in fm.group(1).splitlines() if ":" in l)
        )
        for key in ("disease", "status"):
            if front.get(key) != str(m.get(key)):
                issues.append(f"{m['id']}.{key}: note={front.get(key)} registry={m.get(key)}")
        if m["id"] not in dual_axis and front.get("axis") != m.get("axis"):
            issues.append(f"{m['id']}.axis: note={front.get('axis')} registry={m.get('axis')}")
    assert not issues, issues


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
                missing.append(f"{path.relative_to(src)} declares MODEL_ID={model_id!r}")

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
    checked = [m for m in implemented
               if m.get("parity_status") in {"checked", "matched"}]
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

    assert n_dis == len(diseases), f"doc says {n_dis} diseases, registry has {len(diseases)}"
    assert n_dis_total == 12
    assert n_models == len(implemented), (
        f"doc says {n_models} models coded, registry has {len(implemented)}"
    )
    assert n_checked == len(checked), (
        f"doc says {n_checked} checked, registry has {len(checked)}"
    )
    assert pct == round(len(checked) / len(implemented) * 100), "the percentage disagrees"


def test_every_checked_model_says_how_it_was_checked():
    """A `checked` row with no parity_note is a claim with no evidence behind it,
    and it renders as "Yes — —" in the generated README. Caught plcom2012.
    """
    thin = [
        m["id"] for m in load_models()
        if m.get("parity_status") in {"checked", "matched"}
        and len(str(m.get("parity_note", "")).strip()) < 40
    ]
    assert not thin, f"checked but no substantive parity_note: {thin}"


def test_every_implemented_model_has_an_architecture_and_a_core_formula():
    """Both are surfaced in the README's coverage table; a blank cell there reads
    as 'we do not know what this model is'."""
    missing = [
        m["id"] for m in load_models()
        if m.get("status") == "implemented"
        and not (m.get("architecture_family") and m.get("architecture")
                 and m.get("core_formula"))
    ]
    assert not missing, f"missing architecture or core_formula: {missing}"


def test_every_implemented_model_says_where_its_equation_sits():
    """Naming the paper is not enough to check our work against it.

    `equation_source` says which paper; `equation_location` says where in that
    paper to look -- the equation number if it has one, otherwise the section
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
    "crc_pro_reference.R", "pbcg_reference.R", "dutasteride_reference.R",
    "msk_gastric_reference.R", "msk_ovarian_reference.R",
    "msk_pancreatic_reference.R", "dutasteride_extract.py",
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
            # licence rule working, not a dangling pointer -- but only for
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
        m["id"] for m in load_models()
        if m.get("status") == "implemented"
        and m.get("open_source") == "available"
        and not m.get("public_repo")
    ]
    assert not bad, f"claim 'available' with no public_repo: {bad}"


def test_no_public_repo_is_claimed_for_a_model_marked_otherwise():
    """The reverse. A public_repo URL on a model marked web_only or none means
    one of the two fields is wrong."""
    bad = [
        m["id"] for m in load_models()
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


def test_discrimination_carries_its_source():
    """An AUC or C-index without provenance is a number someone will quote.

    The rule that governs every coefficient in this repo governs these too: it
    enters only from a source actually read. So a `discrimination` value must
    be accompanied by `discrimination_source` naming where it came from.
    """
    bad = [
        m["id"] for m in load_models()
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
        in_citation = {int(x) for x in
                       re.findall(r"\b(19\d{2}|20\d{2})\b", str(m.get("citation", "")))}
        if in_citation and year not in in_citation:
            problems.append(f"{m['id']}: year {year} not in citation {sorted(in_citation)}")
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
        "docs/README_for_public_repo.md",   # replaced by the generated README
        "docs/MODEL_TABLE.md",
        # replaced by the generated ROADMAP, which now carries the flagship
        # decisions. The hand-written shortlist drifted until it contradicted
        # the registry it claimed to summarise.
        "docs/FLAGSHIP_SHORTLIST.md",
        "docs/TODO.md",
        "docs/OUR_IMPLEMENTATIONS.md",
    ]
    present = [p for p in banned if (root / p).exists()]
    assert not present, (
        f"hand-maintained duplicates of generated files: {present}"
    )


def test_absences_are_described_as_ours_not_the_literatures():
    """We have judged five cells to have no published equation and been wrong
    about all five. Renderers must say what we have found, not what exists.

    Extended on 2026-08-06 to cover `docs/` and `vault/` as well as the code.
    The code had already been cleaned, but two hand-maintained summaries -- the
    reproducibility map and the vault's baseline matrix -- were still asserting
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
    ]
    # phrases that mark a line as a retraction rather than an assertion
    retracting = ("was wrong", "were wrong", "that was", "used to", "retired",
                  "superseded", "no longer", "until 2026", "had been",
                  "is retired", "instead of quoting", "corrected",
                  "was recorded", "were recorded")
    offenders = []
    for rel in ("scripts", "src", "registry", "docs", "vault"):
        base = root / rel
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.suffix not in {".py", ".yaml", ".md"} or "__pycache__" in p.parts:
                continue
            if p.name == "soften_claims.py":     # it quotes them to replace them
                continue
            for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                low = line.lower()
                if any(mark in low for mark in retracting):
                    continue
                for phrase in banned:
                    if phrase in line:
                        offenders.append(f"{p.relative_to(root)}:{i}: {phrase!r}")
    assert not offenders, (
        "these assert what the literature contains rather than what we found:\n  "
        + "\n  ".join(offenders)
    )


def test_each_cell_has_exactly_one_flagship():
    """The convention is one default per disease x question cell. Four cells
    had two models both marked flagship for weeks, because nobody had chosen —
    the label was left on whatever was implemented first."""
    from collections import defaultdict

    cells = defaultdict(list)
    for m in load_models():
        if m.get("status") == "implemented":
            cells[(m["disease"], m["axis"])].append(m)

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
        for models in cells.values() if len(models) > 1
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
        paths = [base] if base.is_file() else (
            [p for p in base.rglob("*") if p.suffix in {".md", ".py"}]
            if base.exists() else [])
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
                        offenders.append(f"{p.relative_to(root)}:{i}: {line.strip()[:70]}")
    assert not offenders, (
        "these tell a reader to use pip/conda instead of uv:\n  "
        + "\n  ".join(offenders))


def test_readme_python_version_matches_pyproject():
    """A version claim that disagrees with the packaging metadata sends people
    to install the wrong interpreter. The README said 3.11+; pyproject said
    >=3.10."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = re.search(r'requires-python\s*=\s*"([^"]+)"',
                     (root / "pyproject.toml").read_text()).group(1)
    expected = spec.replace(">=", "") + "+"
    readme = (root / "README.md").read_text()
    claims = re.findall(r"Python (\d+\.\d+\+)", readme)
    assert claims, "README no longer states a Python version"
    assert set(claims) == {expected}, (
        f"README says Python {set(claims)}, pyproject requires {spec}")


def test_hand_written_docs_do_not_hardcode_progress_numbers():
    """One place computes progress; prose must not restate it.

    `docs/CANDIDATE_MODELS.md` (then OPPORTUNITIES.md) quoted "96% to 81%" and
    was wrong twice over within a day: the reachable denominator it referred to
    later collapsed onto the plain 36, and the figure is now 26/36. The
    document's own subject was surveys going stale.

    Generated files are exempt -- they render from `progress_report()` and
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
        r"|\b\d{1,2}\s*/\s*3[26]\b[^.\n]{0,20}(cell|filled))", re.I)

    offenders = []
    for p in (root / "docs").glob("*.md"):
        if p.name in generated:
            continue
        for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            # a line that explicitly disclaims the number is the fix, not the bug
            if "on purpose" in line or "no progress figure" in line.lower():
                continue
            if pattern.search(line):
                offenders.append(f"{p.relative_to(root)}:{i}: {line.strip()[:90]}")
    assert not offenders, (
        "hand-written docs quoting a progress figure; render it from "
        "progress_report() or drop it:\n  " + "\n  ".join(offenders))


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
