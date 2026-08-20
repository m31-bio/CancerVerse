#!/usr/bin/env python3
"""Generate docs/ROADMAP.md from the registry.

Hand-maintained roadmaps go stale — docs/TODO.md was still asking for work on
ERSPC RC3 and SCORE2 long after both were verified. This reads the registry so
it cannot.

    python scripts/build_roadmap.py [output_path]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cancerverse_baseline.registry.load import load_models, progress_report  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from model_table import DISEASE_LABEL  # noqa: E402


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "ROADMAP.md"
    models = load_models()
    report = progress_report()
    impl = [m for m in models if m.get("status") == "implemented"]
    unchecked = [m for m in impl
                 if m.get("parity_status") not in {"checked", "matched"}]

    notes = {}
    for m in models:
        if m.get("status") in {"gap", "catalog"}:
            notes.setdefault((m.get("disease"), m.get("axis")), m.get("tier_note")
                             or m.get("title", ""))

    lines = [
        "# Roadmap",
        "",
        "**Generated from `registry/models.yaml` — do not edit by hand.**",
        "Regenerate with `python scripts/build_roadmap.py`.",
        "",
        f"{len(impl)} models implemented; "
        f"{len(impl) - len(unchecked)} verified against an independent source.",
        "",
        "## Open cells",
        "",
        "Disease × question pairs where a published equation exists and we have not",
        "implemented one yet. Nothing is excluded: the exclusion this line used",
        "to describe -- cells with no published equation at all -- no longer has",
        "any members, so every one of the 36 counts.",
        "",
        "| Disease | Question | What is known |",
        "|---|---|---|",
    ]
    for disease, axis in report["remaining_cells"]:
        note = " ".join(str(notes.get((disease, axis), "")).split()) or "—"
        lines.append(f"| {DISEASE_LABEL.get(disease, disease)} | {axis} | {note} |")

    lines += ["", "## Unverified models", ""]
    if unchecked:
        lines += ["| Model | Blocked by |", "|---|---|"]
        for m in unchecked:
            lines.append(f"| `{m['id']}` | {m.get('parity_blocker', '—')} |")
    else:
        lines.append(
            "None. Every implemented model has been compared against a source we "
            "did not write; the evidence is in `docs/VERIFICATION.md`."
        )

    lines += [
        "",
        "## Standing work",
        "",
        "- **Re-check flagship designations** where a cell now holds more than one",
        "  model (cardiovascular detection has PREVENT and SCORE2; ovarian detection",
        "  has RMI and ROMA). Which is the default deserves a fresh look.",
        "- **Decide how to report the cells with no published equation** rather than",
        "  carrying them as permanent to-dos. There are",
        f"  {report['n_cells_unreachable']} of them.",
        "",
    ]

    # Which model is the default where a cell holds more than one, and why.
    # This used to live in a hand-written FLAGSHIP_SHORTLIST.md that drifted
    # until it contradicted the registry, so it is generated now.
    from collections import defaultdict

    cells = defaultdict(list)
    for m in impl:
        cells[(m["disease"], m["axis"])].append(m)
    contested = {c: v for c, v in cells.items() if len(v) > 1}

    if contested:
        lines += [
            "## Cells with more than one model",
            "",
            f"{len(contested)} of {len(cells)}. Each has one default; the others are",
            "peers with a recorded reason to prefer them in some situations. Two of",
            "these are not really contests at all — see the notes.",
            "",
        ]
        for (dis, axis), models in sorted(contested.items()):
            lines.append(f"### {DISEASE_LABEL.get(dis, dis)} · {axis}")
            lines.append("")
            for m in sorted(models, key=lambda x: x.get("role") != "flagship"):
                tag = "**default**" if m.get("role") == "flagship" else "alternative"
                lines.append(f"- `{m['id']}` — {tag}. "
                             f"{' '.join(str(m.get('flagship_note', '')).split())}")
            lines.append("")

    # The discrimination gap, named model by model so it is actionable rather
    # than a lament. These are blank because the paper could not be opened, not
    # because we have not read it, not because it does not exist.
    no_disc = [m for m in impl if not m.get("discrimination")]
    lines += [
        "## Models with no recorded discrimination",
        "",
        f"{len(no_disc)} of {len(impl)}. An AUC or C-index enters this registry only",
        "from a paper actually read — the same rule as every coefficient — so these",
        "are blank rather than filled from a search summary.",
        "",
        "| Model | Year | Paper to read |",
        "|---|---|---|",
    ]
    for m in sorted(no_disc, key=lambda x: x.get("year", 0)):
        lines.append(f"| `{m['id']}` | {m.get('year', '')} "
                     f"| {m.get('source_url', '—')} |")

    lines += [
        "",
        "## How to help",
        "",
        "See the Contributing section of the README. The single most valuable thing",
        "you can send is a correction: if a coefficient here disagrees with its",
        "source, open an issue with the citation and the exact table.",
    ]
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
