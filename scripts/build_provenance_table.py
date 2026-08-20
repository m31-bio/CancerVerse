#!/usr/bin/env python3
"""Where did each flagship model's numbers actually come from?

    python scripts/build_provenance_table.py

Writes docs/PARAMETER_PROVENANCE.md from `equation_location` in the registry.

The question this answers is narrower than "what is the citation", and it is
the one that matters when somebody challenges a coefficient: *which artifact
was read, and can it be read again?* A DOI does not answer that. Half the
flagship models in this library take their numbers from something other than
the paper the citation names, a vendor's R source, a supplementary text file,
a deployed calculator's own printout, and in several cases the paper contains
no closed form at all.

Four provenance classes, ordered by how cheaply a challenge can be settled:

  file      a machine-readable artifact: R source, .json, .csv, .txt, .xlsx.
            Re-checkable by anyone, offline, forever. The strongest kind.
  printed   a numbered table or a sentence in the article text. Re-checkable
            by reading, needs no tooling.
  figure    the numbers exist only as pixels and were read off a rendered
            image. Re-checkable only by rendering it again and re-reading, so
            transcription is the weak step and a second independent read is
            mandatory.
  derived   this project composed the model; there is no upstream equation.

`confirmed` is a separate axis from all four. Some rows were located while the
model was being implemented and never re-read against the source afterwards.
Those say so, and they are the rows to hand to a human, because a provenance
note nobody has checked is a claim, not a record.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "src"))
from cancerverse_baseline.reporting.atomic import write_text_atomically  # noqa: E402

REGISTRY = ROOT / "registry" / "models.yaml"
BIBLIO = ROOT / "registry" / "bibliometrics.json"
OUT = ROOT / "docs" / "PARAMETER_PROVENANCE.md"

AXIS_ORDER = {"detection": 0, "response": 1, "prognosis": 2}
AXIS_LABEL = {"detection": "Prediction", "response": "Response",
              "prognosis": "Prognosis"}

#: A note that admits its own location was never re-read.
UNCONFIRMED = re.compile(
    r"not re-read|approximate|not captured|unverified|not confirmed", re.I)

#: The artifact actually read. Order matters: a row that names both a figure
#: and a vendor source took its numbers from the source, not the picture.
FILE_HINT = re.compile(
    r"\.(json|csv|txt|xlsx|rda)\b|server\.R|\bR/|riskcalc-website|github|"
    r"CRAN package|Additional file|MOESM|Model Summary|supplement", re.I)
FIGURE_HINT = re.compile(r"\beFigure\b|\bFigure \d|nomogram figure", re.I)
DERIVED_HINT = re.compile(r"no source paper|composition this project", re.I)


#: Keyword matching cannot decide these, and it got both of them backwards.
#: `equation_location.where` is prose written for a human, so a row can name a
#: figure it did NOT read from and a supplement it did. Checked against each
#: module's own docstring, which is where the reader is recorded.
#:
#:   msk_rectal   the where-note says "Supplement 1", so the file rule claimed
#:                it. But msk_rectal.py: "The eFigure is a rendered image, not
#:                text; the coefficients below were read from it and re-read
#:                from independent renders at 300 and 600 dpi." It is a figure
#:                read, and it is the one row where transcription risk is real.
#:   ang2010_rpa  the where-note names Figure 2, so the figure rule claimed it.
#:                But ang2010_rpa.py: "Exact quote from the Results section
#:                (the decision tree, verbatim)." The tree is drawn in Figure 2
#:                and also stated in prose; the prose is what was read.
#:   kunzmann     same shape, added 2026-08-14 when the location was re-read.
#:                The note now cites the published Figure 2 nomogram, so the
#:                figure rule claimed it. But kunzmann.py records the points as
#:                "transcribed from Table 2", and the 2026-08-14 pass used
#:                Figure 2 only to confirm them independently. Corroborating a
#:                printed table with a picture does not make it a figure read.
#:   bcsc_v2      added 2026-08-18, and this one the regex could never have got:
#:                its where-note says "Appendix Figure", which carries no number,
#:                so `\bFigure \d` does not match and the row classified as
#:                "printed", the reassuring answer. It is not printed. The
#:                whole algorithm is one image: searching the article's text
#:                layer for 0.520553050, 0.48107, 0.003695745, 0.7182, 1.495 and
#:                0.906 returns ZERO hits, on pages 9-10 and in the document as a
#:                whole. All 57 constants were read off a 300-dpi render. This is
#:                the second row where transcription risk is real, and the table
#:                was reporting it as the safe kind.
OVERRIDE = {
    "msk_rectal": "figure",
    "bcsc_v2": "figure",
    "ang2010_rpa": "printed",
    "kunzmann": "printed",
}


def classify(model_id: str, where: str) -> str:
    if model_id in OVERRIDE:
        return OVERRIDE[model_id]
    if DERIVED_HINT.search(where):
        return "derived"
    if FILE_HINT.search(where):
        return "file"
    if FIGURE_HINT.search(where):
        return "figure"
    return "printed"


def load_biblio() -> dict:
    """Citation counts, cached by scripts/fetch_impact.py.

    Citations rank papers here, and raw count is confounded with age: a 1989
    paper has had thirty-seven years to accumulate them and a 2024 paper two.
    So both are carried, the raw count, and the per-year rate that normalises
    for it. Compare within a vintage first; the rate is what makes papers of
    different vintages comparable at all.

    Impact factor is deliberately absent. Clarivate's JIF is proprietary and
    the open substitute is inconsistently wrong: journals that deposit
    conference abstracts have their means diluted to nonsense (Journal of
    Clinical Oncology reads 1.65 against a real JIF near 45, because 174,155
    indexed works include tens of thousands of ASCO abstracts) while journals
    that deposit few come out plausible. A metric wrong only sometimes is worse
    for ranking than no metric.
    """
    if not BIBLIO.exists():                                    # pragma: no cover
        print("  (registry/bibliometrics.json missing, run scripts/fetch_impact.py)")
        return {}
    import json
    return {r["id"]: r for r in json.loads(BIBLIO.read_text())}


def cite_cell(b: dict | None) -> tuple[str, str, int]:
    """(citations, per-year, sort key) for one model."""
    if not b or b.get("citations") is None:
        return "—", "—", -1
    return (f"{b['citations']:,}",
            str(b.get("citations_per_year") or "—"),
            b["citations"])


def main() -> int:
    models = yaml.safe_load(REGISTRY.read_text())["models"]
    biblio = load_biblio()
    flag = [m for m in models
            if m.get("status") == "implemented" and m.get("role") == "flagship"]
    flag.sort(key=lambda m: (m["disease"], AXIS_ORDER.get(m["axis"], 9)))

    rows, unconfirmed, figures = [], [], []
    for m in flag:
        loc = m.get("equation_location") or {}
        where = " ".join(str(loc.get("where", "")).split())
        verified = " ".join(str(loc.get("verified", "")).split())
        kind = classify(m["id"], where)
        is_unconfirmed = bool(UNCONFIRMED.search(f"{where} {verified}"))
        rows.append((m, where, verified, kind, is_unconfirmed))
        if is_unconfirmed:
            unconfirmed.append(m)
        if kind == "figure":
            figures.append(m)

    L = []
    L.append("# Where each flagship model's parameters came from\n")
    L.append("Generated by `scripts/build_provenance_table.py` from the "
             "`equation_location` field in `registry/models.yaml`. Edit the "
             "registry, not this file.\n")
    L.append(f"{len(flag)} flagship models. "
             f"{sum(1 for r in rows if r[3] == 'file')} take their numbers from a "
             f"machine-readable file, "
             f"{sum(1 for r in rows if r[3] == 'printed')} from a printed table or "
             f"sentence, {sum(1 for r in rows if r[3] == 'figure')} from a rendered "
             f"figure, {sum(1 for r in rows if r[3] == 'derived')} from a composition "
             f"this project defined.\n")

    L.append("\n## Read this first: the paper is often not the source\n")
    L.append("For eight of these models the cited article contains **no closed "
             "form at all**, it prints a nomogram picture and nothing else. The "
             "coefficients come from a vendor's deployed R source, a "
             "supplementary data file, or the calculator's own printout. The "
             "citation is the scientific record; it is not where the numbers "
             "were read. Any audit that checks the DOI and stops will not have "
             "checked anything.\n")

    if unconfirmed:
        L.append("\n## Needs a human read, location never confirmed\n")
        L.append("These rows were written while the model was being implemented "
                 "and **never re-read against the source afterwards**. The "
                 "coefficients themselves are parity-tested and are not in "
                 "doubt; what is unconfirmed is *which table or section they sit "
                 "in*. Anyone citing a location from this list should open the "
                 "paper first.\n")
        L.append("Ordered by citations, the most-read papers are the ones "
                 "whose provenance is most likely to be challenged.\n")
        L.append("| Cites | /yr | Year | Disease | Question | Model | What the note claims |")
        L.append("|---:|---:|---|---|---|---|---|")
        for m in sorted(unconfirmed, key=lambda x: -cite_cell(biblio.get(x["id"]))[2]):
            loc = m.get("equation_location") or {}
            w = " ".join(str(loc.get("where", "")).split())
            b = biblio.get(m["id"])
            c, pyr, _ = cite_cell(b)
            yr = (b or {}).get("year") or m.get("year") or "—"
            L.append(f"| {c} | {pyr} | {yr} | {m['disease']} "
                     f"| {AXIS_LABEL.get(m['axis'], m['axis'])} | `{m['id']}` | {w} |")

    if figures:
        L.append("\n## Read off a rendered image, transcription is the weak step\n")
        L.append("The numbers exist only as pixels. Re-checking means rendering "
                 "the page again and re-reading it, and a single read is not "
                 "enough: on the MSK rectal supplement a coefficient could have "
                 "been `0.470128` or `0.0470128`, and the dropped leading zero "
                 "would have moved a hazard ratio from 1.60 to 1.05.\n")
        for m in sorted(figures, key=lambda x: -cite_cell(biblio.get(x["id"]))[2]):
            loc = m.get("equation_location") or {}
            c, pyr, _ = cite_cell(biblio.get(m["id"]))
            L.append(f"- **`{m['id']}`** ({m['disease']} / "
                     f"{AXIS_LABEL.get(m['axis'], m['axis'])}): "
                     f"**{c} citations, {pyr}/yr**: "
                     f"{' '.join(str(loc.get('where','')).split())}")

    L.append("\n## Every flagship model\n")
    L.append("Sorted by citations. Raw count is confounded with age, so `/yr` "
             "sits beside it; compare within a vintage first.\n")
    L.append("| Cites | /yr | Year | Journal | Disease | Question | Model | Source | Where exactly | Confirmed |")
    L.append("|---:|---:|---|---|---|---|---|---|---|---|")
    for m, where, verified, kind, unconf in sorted(
            rows, key=lambda r: -cite_cell(biblio.get(r[0]["id"]))[2]):
        mark = {"file": "file", "printed": "printed", "figure": "**figure**",
                "derived": "derived"}[kind]
        ok = "no, see above" if unconf else (verified or "—")
        b = biblio.get(m["id"])
        c, pyr, _ = cite_cell(b)
        yr = (b or {}).get("year") or m.get("year") or "—"
        jr = (b or {}).get("journal") or "—"
        L.append(f"| {c} | {pyr} | {yr} | {jr} | {m['disease']} "
                 f"| {AXIS_LABEL.get(m['axis'], m['axis'])} "
                 f"| `{m['id']}` | {mark} | {where} | {ok} |")

    write_text_atomically(OUT, "\n".join(L) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {len(flag)} flagship models; {len(unconfirmed)} need a human read; "
          f"{len(figures)} read off a figure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
