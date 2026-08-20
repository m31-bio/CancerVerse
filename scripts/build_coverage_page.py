#!/usr/bin/env python3
"""Render the coverage table as a standalone reviewable page.

    python scripts/build_coverage_page.py [output.html]

Same data as the README table, laid out so a 7-column x 36-row grid is actually
readable. Generated from registry/models.yaml.

WHERE IT IS WRITTEN. Into the shared repository beside this one
(../CancerVerse/coverage.html), not into this tree. The page is a public-facing
artifact: it is what someone outside the team opens to see what the library
covers, and it has no reader here. Keeping a second copy in this repository
only created a file that had to be regenerated and re-committed in lockstep
with the real one, which is how a generated file goes stale while looking
current.

Consequences:
  - `coverage.html` is NOT tracked in this repository and is in .gitignore.
  - sync_public_repo.py lists it in DEST_ONLY, not PUBLIC_FILES: it is
    maintained at the destination rather than copied there.
  - the pre-commit "generated files are current" hook does not run this
    script, because a commit here must not write into a sibling repository.
    Rerun it by hand after changing the registry.

One row per disease and question: the flagship. See build().
"""

from __future__ import annotations

import html
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "models.yaml"
CONSTRAINTS = ROOT / "registry" / "constraints.yaml"

# Importable from a plain checkout as well as an installed package: the
# renderers are run with `python scripts/...` during development, when
# `src/` is not yet on the path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cancerverse_baseline.reporting import (  # noqa: E402
    AXES,
    AXIS_LABEL,
    GAP_CAPTION,
    GAP_CELL_LABEL,
    clinical_question,
    equation_location,
    linked_reference,
)
from cancerverse_baseline.reporting import (
    DISEASE_LABEL as _DISEASE_LABEL,
)
from cancerverse_baseline.reporting import (
    OPEN_SOURCE_LABEL as SOURCE_LABEL,
)
from cancerverse_baseline.reporting.atomic import write_text_atomically  # noqa: E402

# the page is HTML, so the ampersand needs escaping
DISEASE_LABEL = {k: v.replace("&", "&amp;") for k, v in _DISEASE_LABEL.items()}
SOURCE_CLASS = {"available": "src-code", "web_only": "src-web", "none": "src-paper"}


def e(x) -> str:
    return html.escape(" ".join(str(x or "").split()))


CSS = """
.apa { font-size: 11px; color: #5b6b7a; line-height: 1.4; }
:root{
  --ink:#16211f; --ink-2:#33413e; --muted:#5f6d6a;
  --paper:#f6f8f7; --card:#ffffff; --rule:#dde4e1; --rule-2:#eef2f0;
  --accent:#0f6e5c; --accent-soft:#e4f0ec;
  --warn:#8a5410; --warn-soft:#f7ecdd;
  --band:#f0f4f2;
}
@media (prefers-color-scheme: dark){
  :root{
    --ink:#e6ece9; --ink-2:#c2ccc8; --muted:#8b9995;
    --paper:#0e1413; --card:#151d1b; --rule:#26302d; --rule-2:#1c2523;
    --accent:#4fbfa4; --accent-soft:#12302a;
    --warn:#d9a05b; --warn-soft:#2e2418;
    --band:#121a18;
  }
}
:root[data-theme="dark"]{
  --ink:#e6ece9; --ink-2:#c2ccc8; --muted:#8b9995;
  --paper:#0e1413; --card:#151d1b; --rule:#26302d; --rule-2:#1c2523;
  --accent:#4fbfa4; --accent-soft:#12302a;
  --warn:#d9a05b; --warn-soft:#2e2418;
  --band:#121a18;
}
:root[data-theme="light"]{
  --ink:#16211f; --ink-2:#33413e; --muted:#5f6d6a;
  --paper:#f6f8f7; --card:#ffffff; --rule:#dde4e1; --rule-2:#eef2f0;
  --accent:#0f6e5c; --accent-soft:#e4f0ec;
  --warn:#8a5410; --warn-soft:#f7ecdd;
  --band:#f0f4f2;
}


*{box-sizing:border-box;}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  font-size:15px; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1500px;margin:0 auto;padding:40px 28px 80px;}

header{border-bottom:2px solid var(--ink);padding-bottom:22px;margin-bottom:28px;}
.eyebrow{
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);font-weight:650;margin-bottom:10px;
}
h1{
  font-family:"Iowan Old Style","Charter","Palatino Linotype",Palatino,Georgia,serif;
  font-size:clamp(30px,4vw,44px); line-height:1.08; margin:0 0 10px;
  font-weight:600; letter-spacing:-.01em; text-wrap:balance;
}
.sub{color:var(--muted);max-width:64ch;margin:0;font-size:15.5px;}

.stats{display:flex;flex-wrap:wrap;gap:0;margin:26px 0 0;
  border:1px solid var(--rule);border-radius:3px;overflow:hidden;background:var(--card);}
.stat{flex:1 1 170px;padding:16px 18px;border-right:1px solid var(--rule);}
.stat:last-child{border-right:0;}
.stat b{
  display:block;font-size:27px;font-weight:600;letter-spacing:-.02em;
  font-variant-numeric:tabular-nums;color:var(--accent);line-height:1.1;
}
.stat span{display:block;font-size:12.5px;color:var(--muted);margin-top:3px;}

.note{
  margin:26px 0 0;padding:13px 16px;border-left:3px solid var(--warn);
  background:var(--warn-soft);border-radius:0 3px 3px 0;font-size:13.5px;color:var(--ink-2);
}

.scroller{
  margin-top:30px;overflow-x:auto;border:1px solid var(--rule);
  border-radius:3px;background:var(--card);
}
table{border-collapse:collapse;width:100%;min-width:2320px;font-size:13.5px;}
thead th{
  position:sticky;top:0;z-index:2;background:var(--card);
  border-bottom:2px solid var(--ink);
  text-align:left;padding:11px 13px;font-size:11px;letter-spacing:.09em;
  text-transform:uppercase;color:var(--ink);font-weight:650;white-space:nowrap;
}
td{padding:12px 13px;border-bottom:1px solid var(--rule-2);vertical-align:top;}
tr.group-start td{border-top:1px solid var(--ink);}
tr.banded td{background:var(--band);}
/* Merged cells. The disease cell spans all three questions and the question
   cell spans its models, so neither carries an internal horizontal rule. A
   vertical rule marks the boundary instead. */
td.disease,td.axis{border-right:1px solid var(--rule);border-bottom:0;}
td.disease{
  font-family:"Iowan Old Style","Charter",Palatino,Georgia,serif;
  font-size:17px;font-weight:600;white-space:nowrap;width:1%;
  padding-top:14px;letter-spacing:-.005em;
}
td.axis{
  color:var(--ink-2);white-space:nowrap;width:1%;font-size:13px;
  padding-top:13px;
}
td.model{font-weight:600;min-width:150px;}
.question{display:block;margin-top:4px;font-size:11px;font-weight:500;
  color:var(--muted);font-style:italic;line-height:1.35;}
td.cite{color:var(--muted);font-size:11.5px;min-width:180px;max-width:230px;line-height:1.4;}
td.repo{font-size:12px;min-width:145px;max-width:185px;}
td.repo a,td.cite a{color:var(--accent);text-decoration:none;
  border-bottom:1px solid var(--rule);overflow-wrap:anywhere;font-weight:600;}
td.repo a:hover,td.cite a:hover{border-bottom-color:var(--accent);}
td.arch{min-width:230px;max-width:300px;}
.fam{
  display:inline-block;font-size:11px;letter-spacing:.05em;text-transform:uppercase;
  font-weight:650;color:var(--accent);
}
.archline{margin-top:5px;font-size:12px;color:var(--ink-2);line-height:1.45;}
td.formula{min-width:340px;max-width:480px;}
td.formula pre{
  margin:0;
  font-family:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
  font-size:11.5px;line-height:1.62;color:var(--ink);
  white-space:pre;overflow-x:auto;
  padding:9px 11px;background:var(--band);border-radius:3px;
  border-left:2px solid var(--accent);
}
tr.banded td.formula pre{background:var(--card);}
td.year{
  font-size:18px;font-weight:600;color:var(--ink);width:1%;
  font-variant-numeric:tabular-nums;white-space:nowrap;padding-top:13px;
}
td.perf{min-width:195px;max-width:255px;}
.disc{font-size:12px;color:var(--accent);font-weight:600;line-height:1.4;}
.unrec{font-size:11.5px;color:var(--muted);font-style:italic;line-height:1.4;}
.coh{margin-top:5px;font-size:11.5px;color:var(--muted);line-height:1.4;}
td.verified{min-width:230px;max-width:330px;}
/* Where it applies. The widest thing on the page after the formula, because a
   scope statement that has to be truncated is a scope statement that will be
   read as permission. */
td.scope{min-width:330px;max-width:420px;}
.applies{font-size:12.5px;color:var(--ink);line-height:1.5;font-weight:500;}
.scope{font-size:12.5px;line-height:1.5;}
.sc{margin:0 0 6px;color:var(--ink);}
.sc:last-child{margin-bottom:0;}
.sc span{
  display:block;font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;
  font-weight:700;color:var(--muted);margin-bottom:1px;
}
.sc.trap{color:#7c2d12;}
.sc.trap span{color:#9a3412;}
.srccount{
  display:block;margin-top:7px;font-size:11px;color:var(--muted);
  letter-spacing:.03em;
}
.qlist{margin:0;padding:0;list-style:none;}
.qlist li{
  margin:11px 0 0;padding:9px 11px;background:var(--band);
  border-left:2px solid var(--accent);border-radius:0 3px 3px 0;
}
tr.banded .qlist li{background:var(--card);}
.qclaim{font-size:11.5px;font-weight:650;color:var(--ink);line-height:1.4;}
.qwhere{
  display:block;margin:4px 0 5px;font-size:10.5px;color:var(--accent);
  letter-spacing:.03em;font-weight:600;
}
.qquote{
  font-size:11.5px;color:var(--ink-2);line-height:1.5;font-style:italic;
  border-left:0;margin:0;
}
.qlink{
  display:block;margin-top:10px;font-size:11px;
}
.qlink a{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--rule);
  overflow-wrap:anywhere;font-weight:600;}
.qlink a:hover{border-bottom-color:var(--accent);}
.closed{
  display:inline-block;margin-top:6px;font-size:10.5px;font-weight:650;
  letter-spacing:.04em;text-transform:uppercase;color:var(--warn);
}
code{
  font-family:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
  font-size:11.8px;line-height:1.55;color:var(--ink);
  overflow-wrap:anywhere;display:block;
}
.empty td{color:var(--muted);}
.dash{color:var(--rule);font-size:17px;}
.gapnote{font-size:11.5px;color:var(--muted);font-style:italic;}
.gapfull{font-size:11.5px;color:var(--ink-2);line-height:1.5;
  white-space:pre-wrap;}
/* An empty cell whose blocker is a published negative result, not an
   unfinished search. It is the only red on this page apart from a
   failed figure check, and it is spent here because 'gap' otherwise
   reads as 'look again', which for this cell is the wrong action. */
.needsimg{font-size:12px;font-weight:650;color:#b32d2d;margin-top:5px;
  line-height:1.45;}
.needsimg a{color:#b32d2d;}
.imgsrc{margin-top:3px;font-size:10.5px;font-weight:400;color:var(--muted);
  line-height:1.4;}

.chip{
  display:inline-block;padding:2px 8px;border-radius:2px;
  font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;font-weight:650;
  white-space:nowrap;
}
.ok{background:var(--accent-soft);color:var(--accent);}
/* The nomogram-check chips. `bad` is the only loud colour on the page, and it
   is spent on the one cell where our implementation disagrees with the figure
   its authors published; see nomogram_chip(). A coverage page that renders
   its own failure quietly is worth less than no page. */
.bad{background:#fdecec;color:#b32d2d;}
.part{background:var(--warn-soft);color:var(--warn);}
.chip + .chip{margin-left:5px;}
.src-code{background:var(--accent-soft);color:var(--accent);}
.src-web{background:var(--warn-soft);color:var(--warn);}
.src-paper{background:transparent;color:var(--muted);border:1px solid var(--rule);}
.how{margin-top:6px;font-size:12px;color:var(--ink-2);line-height:1.45;}
.repro{margin-top:9px;padding-top:8px;border-top:1px dashed var(--rule);}
.repro>span{
  font-size:10px;letter-spacing:.09em;text-transform:uppercase;
  font-weight:650;color:var(--accent);
}
.repro ul{margin:5px 0 0;padding-left:15px;}
.repro li{font-size:11.5px;color:var(--muted);margin-bottom:3px;line-height:1.45;}
.repro code{display:inline;font-size:11px;color:var(--ink-2);}
details{margin-top:5px;}
summary{
  cursor:pointer;font-size:11.5px;color:var(--accent);
  list-style:none;font-weight:600;
}
summary::-webkit-details-marker{display:none;}
summary::before{content:"+ ";font-weight:700;}
details[open] summary::before{content:"\\2212 ";}
details p{margin:6px 0 0;font-size:12px;color:var(--muted);line-height:1.5;}
summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:2px;}

footer{margin-top:34px;padding-top:20px;border-top:1px solid var(--rule);
  font-size:12.5px;color:var(--muted);}
footer b{color:var(--ink-2);}
@media (max-width:760px){.wrap{padding:26px 14px 60px;} h1{font-size:27px;}}
"""


def nomogram_chip(m: dict) -> str:
    """The second verification, where one was done, beside the first.

    Six of these models take their coefficients from a vendor's deployed code
    rather than from their paper, because the paper printed a nomogram figure
    and no equation. Parity against that deployment is one question: do we
    compute what they compute, and it is the one the `verified` chip answers.
    Whether the deployment matches the FIGURE THE AUTHORS PUBLISHED is a second
    question, it had never been asked, and for one cell the answer is no.

    It belongs in this column rather than a new one: both chips answer "checked
    against what", and a page that shows only the passing check is the kind of
    page this project exists not to produce. The failing cell is deliberately
    the loudest thing in its row.
    """
    text = str(m.get("nomogram_check") or "")
    if not text:
        return ""

    # The verdict is a registry field, not something inferred from the prose.
    # The first version guessed by looking for "does not" in the first 400
    # characters, and rendered the one FAILING cell as passing, because the
    # sentence that says so happens to fall later in the paragraph. A page that
    # reports its own failure as a success is worse than no page, so the state
    # is declared once, in the registry, and an unknown value raises instead of
    # defaulting to the reassuring answer.
    CHIPS = {
        "agrees": ("ok", "figure: agrees"),
        "disagrees": ("bad", "figure: DISAGREES"),
        "shape_only": ("part", "figure: shape only"),
    }
    result = m.get("nomogram_check_result")
    if result not in CHIPS:
        raise ValueError(
            f"{m['id']}: nomogram_check is present but "
            f"nomogram_check_result is {result!r}; expected one of "
            f"{sorted(CHIPS)}"
        )
    cls, label = CHIPS[result]
    head = text.split(".")[0].strip()
    return (
        f'<span class="chip {cls}" title="{e(head)}">{label}</span>'
        f"<details><summary>checked against the published figure</summary>"
        f"<p>{e(text)}</p></details>"
    )


def verified_chip(m: dict) -> str:
    """The verification chip, derived from parity_status rather than assumed.

    This was a hardcoded `<span class="chip ok">verified</span>` on EVERY row.
    On a page whose subject is verification that is the worst possible default:
    the header stat counted 30 of 40 independently verified while all 34 model
    rows displayed "verified", so the ten exceptions were invisible at exactly
    the place a reader looks for them. Three states, matching the registry:
      checked / matched  an independent implementation or reference was run
      not_checked with   the constants were transcribed from the paper and
        no_independent_   checked against it, and no third party exists to run
        reference_impl    them against, a weaker claim, shown as weaker
      anything else      not checked
    """
    status = m.get("parity_status")
    if status in {"checked", "matched"}:
        return '<span class="chip ok">verified</span>'
    if m.get("parity_blocker") == "no_independent_reference_implementation":
        return (
            '<span class="chip part" title="Constants transcribed from the '
            "paper and checked against it; no third-party implementation "
            'exists to run them against">transcription only</span>'
        )
    return '<span class="chip warn">not checked</span>'


#: The seven kinds of limit a reader can act on, in the order a clinician meets
#: them: who the patient is, where they are in their care, what disease, which
#: population, what has already been done, and last, the ways the number
#: itself is misread. That last group is the largest (28 of 34 models) and the
#: one a prose paragraph hid worst: units, direction, and which edition of a
#: staging system a field expects.
SCOPE_ORDER = ["age", "sex", "point_in_care", "disease",
               "population", "prior_treatment", "misuse"]
SCOPE_LABEL = {
    "age": "Age",
    "sex": "Sex",
    "point_in_care": "Point in care",
    "disease": "Disease &amp; histology",
    "population": "Population",
    "prior_treatment": "Prior treatment",
    "misuse": "Misuse traps",
}


def scope_cell(m: dict, constraints: dict) -> str:
    """The 'Where it applies' cell: the scope statement, then the paper text
    that establishes it.

    Every model in this library carries a population it was built for, and the
    page's own disclaimer says that applying one outside its scope produces a
    number that looks valid and is not. That warning was previously the only
    thing on the page about scope: a general caution with no per-model
    content behind it, which a reader cannot act on. This cell is the content:
    what the model is for, and the sentence in the source paper that says so,
    with its section and page so the claim can be checked rather than trusted.

    Quotes are capped at five per model. The full record, 465 sourced quotes
    across 34 models, each independently re-fetched and adversarially verified
    across 34 models, is docs/MODEL_CONSTRAINTS_SOURCES.md, and the audit that produced them
    is docs/MODEL_CONSTRAINTS.md.
    """
    c = constraints.get(m["id"])
    if not c:
        return '<span class="dash">&mdash;</span>'

    parts = []
    scope = c.get("scope") or {}
    if scope:
        rows = "".join(
            f'<p class="sc{" trap" if k == "misuse" else ""}">'
            f'<span>{SCOPE_LABEL[k]}</span>{e(scope[k])}</p>'
            for k in SCOPE_ORDER
            if scope.get(k)
        )
        parts.append(f'<div class="scope">{rows}</div>')
    else:
        parts.append(f'<div class="applies">{e(c["applies_to"])}</div>')

    if c.get("access") == "closed":
        parts.append(
            '<span class="closed">closed access &mdash; abstract only</span>'
        )

    srcs = c.get("sources") or []
    if srcs:
        total = c.get("n_sourced_total", len(srcs))
        shown = len(srcs)
        # A count alone leaves the reader nowhere to go. Where some are
        # withheld for space, name the file and the section that holds them.
        where = f"docs/MODEL_CONSTRAINTS_SOURCES.md &sect; <code>{e(m['id'])}</code>"
        label = (
            f"{total} constraint{'s' if total != 1 else ''} sourced to the paper"
            if total == shown
            else f"{shown} of {total} shown &mdash; the rest in {where}"
        )
        parts.append(f'<span class="srccount">{label}</span>')

        items = []
        for sdef in srcs:
            # `page` is absent for most entries and that is the normal case:
            # the paper was retrieved in a format with section headings and no
            # printed pagination, so there is no page to give. Only the two
            # models read from genuinely paginated sources carry the key, and
            # only those render a page number. Nothing is printed to mark its
            # absence. An earlier version said "no pagination in retrieved
            # format" on 24 of 34 models, which repeated a non-answer 160 times
            # while the section heading was already doing the work.
            where = e(sdef.get("section"))
            page = str(sdef.get("page") or "")
            if page:
                where += f" &middot; p. {e(page)}"
            items.append(
                f'<li><span class="qclaim">{e(sdef.get("claim"))}</span>'
                f'<span class="qwhere">{where}</span>'
                f'<p class="qquote">&ldquo;{e(sdef.get("quote"))}&rdquo;</p></li>'
            )

        link = c.get("full_text") or c.get("doi")
        tail = (
            f'<div class="qlink"><a href="{e(link)}">read the paper</a></div>'
            if link
            else ""
        )
        parts.append(
            f"<details><summary>where each limit is stated</summary>"
            f'<ul class="qlist">{"".join(items)}</ul>{tail}</details>'
        )

    return "".join(parts)


def build(models: list[dict], constraints: dict | None = None) -> str:
    constraints = constraints or {}
    impl = [m for m in models if m.get("status") == "implemented"]

    # ONE ROW PER CELL: the flagship, and nothing else.
    #
    # This page answers "what does this library run for each disease and
    # question", and that has exactly one answer per cell. It previously
    # rendered every implemented model, so cvd/prognosis came out three rows
    # deep and the reader had to work out which one was the default. Worse,
    # models sharing a cell answer DIFFERENT clinical questions. GRACE is
    # ACS mortality while CHA2DS2-VASc and ATRIA are atrial fibrillation --
    # so stacking them read as three competing options for one decision,
    # which is not what they are.
    #
    # A cell is (disease, axis, CLINICAL QUESTION), not (disease, axis). Almost
    # always the question is just the axis and nothing changes. cvd/prognosis
    # is the exception and the reason the third component exists: GRACE answers
    # ACS mortality, ATRIA and CHA2DS2-VASc answer AF stroke, and one row for
    # the three of them would have to drop two real answers to keep the rule.
    # It renders as two rows instead, each with its own flagship. See
    # reporting.clinical_question.
    #
    # Safe to filter on: test_each_cell_has_exactly_one_flagship uses the same
    # key, so every populated question holds exactly one flagship and this can
    # never silently empty one. The assert restates that here rather than
    # trusting it from a distance.
    #
    # Alternatives are not lost. They stay in the registry, in the spreadsheet,
    # and in the per-disease dossiers under docs/diseases/, which is where a
    # reader choosing between two models should be looking anyway.
    by = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for m in impl:
        if m.get("role") == "flagship":
            by[m["disease"]][m["axis"]][clinical_question(m)].append(m)
    multi = {
        f"{d}/{a}/{q}": [x["id"] for x in v]
        for d, axes in by.items()
        for a, qs in axes.items()
        for q, v in qs.items()
        if len(v) != 1
    }
    assert not multi, f"cells without exactly one flagship: {multi}"
    flagships = [m for m in impl if m.get("role") == "flagship"]

    gap_note = {}
    #: Cells where the blocker is not "nothing found yet" but a published
    #: finding that the inputs this library takes cannot answer the question.
    #: Rendered loudly, because a reader scanning empty cells will otherwise
    #: read "gap" as "someone should look again", and for these, looking
    #: again is not the plan.
    needs_imaging = {}
    for m in models:
        if m.get("status") in {"gap", "catalog"}:
            gap_note.setdefault((m.get("disease"), m.get("axis")), m)
        if m.get("requires_imaging"):
            needs_imaging[(m.get("disease"), m.get("axis"))] = m

    rows: list[str] = []
    for i, did in enumerate(sorted(DISEASE_LABEL, key=lambda k: DISEASE_LABEL[k])):
        band = " banded" if i % 2 else ""
        # One merged cell per disease spanning all of its rows, and one per
        # question spanning its models. Without this the eye reads three
        # unrelated rows instead of one disease asked three questions.
        # Rows per axis is now the number of QUESTIONS in it, not the number
        # of models: one flagship each, so the two counts coincide except
        # where an axis carries more than one question.
        disease_span = sum(max(1, len(by.get(did, {}).get(a, {}))) for a in AXES)
        first = True
        for axis in AXES:
            questions = by.get(did, {}).get(axis, {})
            entries = [ms[0] for ms in questions.values()]
            gs = " group-start" if first else ""
            dcell = (
                f'<td class="disease" rowspan="{disease_span}">'
                f"{DISEASE_LABEL[did]}</td>"
                if first
                else ""
            )
            acell = (
                f'<td class="axis" rowspan="{max(1, len(entries))}">'
                f"{AXIS_LABEL[axis]}</td>"
            )
            if not entries:
                # A gap cell used to print the first 120 characters of
                # `tier_note` and stop, mid-word, and never showing the
                # fields written since. Two of the three open cells were
                # therefore displaying a stale 2026-08-06 sentence while the
                # registry held a named rejected candidate, the criterion it
                # failed, and in one case a clinical decision rule with its
                # own survival table. A page that says "gap" and truncates the
                # reason is worse than one that says nothing, because it looks
                # like the whole answer.
                gm = gap_note.get((did, axis)) or {}
                lead = e(gm.get("tier_note"))
                detail = " ".join(
                    e(gm.get(k)) for k in
                    # Whitelisting field names is how the previous version
                    # lost every note written after it was authored. Take
                    # everything narrative on the entry instead, minus the
                    # keys that are structured data or rendered elsewhere, so
                    # a field added tomorrow appears without a code change.
                    [k for k in gm
                     if k not in {"id", "disease", "axis", "status", "role",
                                  "year", "title", "license", "repro_tier",
                                  "tier_note", "parity_status", "inputs",
                                  "requires_imaging", "requires_imaging_note",
                                  "requires_imaging_auc_routine",
                                  "requires_imaging_auc_imaging",
                                  "requires_imaging_cohort",
                                  "requires_imaging_citation",
                                  "requires_imaging_url"}
                     and isinstance(gm.get(k), str) and len(str(gm[k])) > 60]
                    if gm.get(k))
                extra = ""
                if lead:
                    head = lead if len(lead) <= 240 else lead[:239].rsplit(" ", 1)[0] + "\u2026"
                    extra = f'<div class="gapnote">{head}</div>'
                    body = (lead if len(lead) > 240 else "") + " " + detail
                    if body.strip():
                        extra += (f"<details><summary>why this cell is open"
                                  f'</summary><p class="gapfull">{body.strip()}'
                                  f"</p></details>")
                img = needs_imaging.get((did, axis))
                if img is not None:
                    # Numbers and citation read from their own fields and
                    # printed in the loud line itself. An earlier version put
                    # only a verdict here and hid the evidence behind a
                    # <details>, which asks the reader to take "does not
                    # predict" on trust, the opposite of this page's job.
                    # It also derived that verdict by slicing the first
                    # sentence of a prose note, the same technique that once
                    # made the nomogram chip render this library's only
                    # failing cell as passing.
                    extra = (
                        f'<div class="needsimg">Routine clinical variables do'
                        f' not predict this: <b>AUC '
                        f'{img["requires_imaging_auc_routine"]}</b>, below'
                        f' chance. With imaging, <b>AUC '
                        f'{img["requires_imaging_auc_imaging"]}</b>.'
                        f'<div class="imgsrc">'
                        f'{e(img["requires_imaging_cohort"])} &middot; '
                        f'<a href="{e(img["requires_imaging_url"])}">'
                        f'{e(img["requires_imaging_citation"])}</a>'
                        f"</div></div>"
                        f"<details><summary>why this changes what the gap is"
                        f'</summary><p>{e(img.get("requires_imaging_note"))}'
                        f"</p></details>"
                    ) + extra
                rows.append(
                    f'<tr class="empty{band}{gs}">{dcell}{acell}'
                    f'<td colspan="9"><span class="dash">&mdash;</span> '
                    f'<span class="gapnote">{GAP_CELL_LABEL}</span>'
                    f"{extra}</td></tr>"
                )
                first = False
                continue
            for k, m in enumerate(entries):
                # The model's own name, and only that.
                #
                # This cell used to be headed by a PLANNED replacement,
                # a model not yet implemented, with the one actually running
                # demoted to a grey "Interim:" line and the full next_action
                # printed underneath in red. Three things were wrong with it:
                # the headline named a model this library cannot run, the red
                # paragraphs were the loudest thing on a page whose subject is
                # what IS verified, and a cell showing two names contradicts
                # the one-flagship-per-cell rule the rest of the page follows.
                #
                # Planned replacements are still tracked: registry
                # `candidate_for` / `next_action`, docs/ROADMAP.md, and the
                # per-disease dossiers. They are roadmap, not coverage, and
                # this page is coverage.
                name = e(m["title"].split("(")[0].split("—")[0].strip())
                # Where an axis carries more than one clinical question, say
                # which one this row answers. Without it cvd/prognosis shows
                # GRACE above ATRIA with nothing explaining why one disease and
                # one question produced two rows, and a reader would reasonably
                # read the second as a competitor to the first.
                if len(entries) > 1:
                    name += f'<span class="question">{e(clinical_question(m))}</span>'
                osrc = m.get("open_source")
                note = e(m.get("parity_note"))
                short = note.split(". ")[0]
                if len(short) < 45 and ". " in note:
                    short = ". ".join(note.split(". ")[:2])
                if len(short) > 190:
                    short = short[:189].rsplit(" ", 1)[0] + "…"
                ev = m.get("evidence") or {}
                fn = ev.get("test_function")
                repro = ['<div class="repro"><span>reproduce it</span><ul>']
                if ev.get("test"):
                    repro.append(
                        f"<li><code>pytest {e(ev['test'])}"
                        + (f"::{e(fn)}" if fn else "")
                        + "</code></li>"
                    )
                if ev.get("script"):
                    repro.append(f"<li>captured by <code>{e(ev['script'])}</code></li>")
                if ev.get("fixture"):
                    repro.append(f"<li>fixture <code>{e(ev['fixture'])}</code></li>")
                repro.append("</ul></div>")
                more = (
                    "<details><summary>full evidence</summary>"
                    f"<p>{note}</p>{''.join(repro)}</details>"
                )
                repo = m.get("public_repo")
                source_url = m.get("source_url") or ""
                repo_cell = (
                    f'<a href="{e(repo)}">{e(repo.rstrip("/").split("/")[-1])}</a>'
                    if repo
                    else '<span class="dash">&mdash;</span>'
                )
                rows.append(
                    f'<tr class="{band.strip()}{gs if k == 0 else ""}">'
                    f"{dcell if k == 0 else ''}"
                    f"{acell if k == 0 else ''}"
                    f'<td class="model">{name}</td>'
                    f'<td class="scope">{scope_cell(m, constraints)}</td>'
                    f'<td class="repo">{repo_cell}<br>'
                    f'<span class="chip {SOURCE_CLASS.get(osrc, "")}">'
                    f"{SOURCE_LABEL.get(osrc, '')}</span></td>"
                    # One APA reference, with the title inside it linked —
                    # the way a reference list does it. Printing the title
                    # separately above the reference said it twice.
                    f'<td class="cite"><span class="apa">'
                    f"{linked_reference({'Reference': m.get('citation_apa') or m.get('citation'), '_paper_title': m.get('paper_title'), '_source_url': source_url})}"
                    f"</span></td>"
                    # Where in the paper the equation sits. Naming the paper
                    # is not enough to check the work against it.
                    f'<td class="where">{e(equation_location(m))}</td>'
                    f'<td class="arch"><span class="fam">'
                    f"{e(m.get('architecture_family'))}</span>"
                    f'<div class="archline">{e(m.get("architecture"))}</div></td>'
                    f'<td class="formula"><pre>'
                    f"{html.escape(str(m.get('core_formula') or ''))}</pre></td>"
                    f'<td class="year">{m.get("year", "")}</td>'
                    + '<td class="perf">'
                    # Three states, not two. A blank used to mean one thing
                    # ("nobody has read the paper"), and that was wrong for the
                    # derived models: cvd_statin_benefit has no AUC to read
                    # because it does not rank patients, so calling it unread
                    # implied homework that does not exist. A discrimination
                    # string beginning "n/a" is the third state and renders
                    # muted, because it is an explanation rather than a result
                    # and must not sit in the same style as a measured figure.
                    + (
                        f'<div class="unrec">{e(m.get("discrimination"))}</div>'
                        if str(m.get("discrimination") or "").lower().startswith("n/a")
                        else f'<div class="disc">{e(m.get("discrimination"))}</div>'
                        if m.get("discrimination")
                        else '<div class="unrec">we have not read this from the '
                        "paper yet</div>"
                    )
                    + (
                        f'<div class="coh">Built on {e(m.get("development_cohort"))}</div>'
                        if m.get("development_cohort")
                        else ""
                    )
                    + "</td>"
                    f'<td class="verified">{verified_chip(m)}'
                    f"{nomogram_chip(m)}"
                    f'<div class="how">{short}</div>{more}</td></tr>'
                )
                first = False

    return f"""<title>CancerVerse &mdash; coverage</title>
<style>{CSS}</style>
<div class="wrap">
<header>
  <div class="eyebrow">M31 Biomedical AI &middot; classical baselines</div>
  <h1>Every disease, every question, one model</h1>
  <p class="sub">Published clinical risk equations reimplemented in Python. One
  row per disease and question &mdash; the flagship, the model this library runs
  by default for that cell. Each row records where the equation came from, what
  kind of model it is, its core formula, and how the implementation was checked
  against a source we did not write. {len(impl) - len(flagships)} further models
  are implemented as alternatives on cells that already have a flagship; they are
  in the spreadsheet and the per-disease dossiers, not here.</p>
  <div class="stats">
    <div class="stat"><b>{len(by)} / 12</b><span>diseases covered</span></div>
    <div class="stat"><b>{len(flagships)}</b><span>flagships shown below</span></div>
    <div class="stat"><b>{len(impl)}</b><span>models implemented in total</span></div>
  </div>
  <p class="note"><b>Not for clinical use.</b> A research artifact, not a medical
  device. Every model carries its own population and scope; applied outside it,
  the number looks valid and is not.</p>
</header>

<div class="scroller">
<table>
  <thead><tr>
    <th>Disease</th><th>Question</th><th>Model</th>
    <th>Where it applies</th>
    <th>Public repository</th><th>Reference</th><th>Where the equation sits</th>
    <th>Architecture</th>
    <th>Core formula</th><th>Year</th><th>How well it discriminates</th>
    <th>Verified &mdash; how</th>
  </tr></thead>
  <tbody>
{chr(10).join(rows)}
  </tbody>
</table>
</div>

<footer>
  <b>Public repository</b> links the code we diffed against, where one exists.
  <b>Reference</b> is the APA entry, with the title linked. Every model has one, and it is the
  thing to check us against.
  <br><br>
  <b>How hard it was to get.</b> <span class="chip src-code">public code</span>
  a runnable implementation we could diff against &nbsp;
  <span class="chip src-web">web calculator only</span> the maths lived on
  someone else's server &nbsp;
  <span class="chip src-paper">paper only</span> printed coefficients, sometimes
  as an image.
  <br><br>
  {GAP_CAPTION}
  Generated from <code style="display:inline">registry/models.yaml</code>.
</footer>
</div>
"""


#: Where the page belongs. It is a public-facing artifact for the shared
#: repository, so it is written STRAIGHT THERE and no copy is kept in this
#: tree; see the module docstring. Matches DEFAULT_DEST in
#: scripts/sync_public_repo.py; the two must agree.
DEFAULT_OUT = ROOT.parent / "CancerVerse" / "coverage.html"


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    if not out.parent.exists():
        # Refuse rather than create. A missing parent means the sibling
        # checkout is not where this expects it, and silently making the
        # directory would produce a second, stale copy of the page that
        # nothing syncs and nobody looks at, exactly the state this
        # arrangement exists to prevent.
        print(
            f"destination directory does not exist: {out.parent}\n"
            f"clone the shared repo beside this one, or pass an explicit "
            f"output path.",
            file=sys.stderr,
        )
        return 1
    models = yaml.safe_load(REGISTRY.read_text())["models"]
    constraints = {}
    if CONSTRAINTS.exists():
        constraints = yaml.safe_load(CONSTRAINTS.read_text())["constraints"]
    write_text_atomically(out, build(models, constraints))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
