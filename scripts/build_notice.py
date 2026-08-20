"""Generate NOTICE from collected/MANIFEST.yaml.

    python scripts/build_notice.py                      # write ./NOTICE
    python scripts/build_notice.py --name CancerVerse --out ../CancerVerse/NOTICE

Attribution is the one file that must not drift from the thing it describes,
and a hand-written NOTICE drifts the moment a dependency is added or a licence
changes. `audit_public_repo.py` requires every package in the manifest to be
named in NOTICE; this generates it from the same manifest, so the check cannot
be satisfied by editing prose.

It caught a live gap: CancerVerse, the repository actually meant for other
people, described the third-party packages as a group ("each retains its own
license") without naming any of them, so a reader could not tell which
dependency carried which licence, and two of the five are GPL.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "src"))
from cancerverse_baseline.reporting.atomic import write_text_atomically  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

TEMPLATE = """\
{name}
Copyright {year} {holder}

Licensed under the Apache License, Version 2.0. See LICENSE.


The models
----------
The clinical risk models implemented here are published equations belonging to
their respective authors. Each is cited in registry/models.yaml, in the module
that implements it, and in the coverage table in README.md, together with the
place in the source paper where the equation sits. This repository claims no
ownership of the underlying models, and the Apache licence above covers only
this reimplementation.


Model sources whose licence makes attribution a condition of use
-----------------------------------------------------------------
Every model here is cited. For the sources below, citing is not courtesy,
their licence terms require attribution, so using the model without naming the
source is a licence breach rather than a lapse of manners. Listed separately
for that reason, and generated from `license_basis` in registry/models.yaml so
the list cannot fall behind the registry.

{attribution_list}

Third-party reference implementations
-------------------------------------
Independent implementations of some of these models were used to verify ours.
They are NOT redistributed here. Each is pinned by version and commit in
collected/MANIFEST.yaml and fetched on demand by scripts/fetch_references.py;
the parity tests run against reference values captured under
tests/parity/reference/, so the test suite passes without them.

{table}

{gpl_note}Nothing in src/ imports, links against, or derives from any of them:
the implementations here are plain Python written from the published equations,
and these packages were used only to generate the reference values the parity
tests compare against.


Files NOT covered by this repository's Apache-2.0 licence
---------------------------------------------------------
THIS REPOSITORY IS MIXED-LICENCE. The files listed below copy arithmetic
verbatim from ClevelandClinicQHS/riskcalc-website, which is licensed PolyForm
Noncommercial 1.0.0. The LICENSE file in this repository does NOT apply to
them, and cannot: nobody may relicense someone else's work by placing it in
their tree.

{polyform_list}

Each carries the same notice at the top of the file. They may be used only for
a noncommercial purpose, which PolyForm defines as "any noncommercial purpose"
regardless of who is doing the using.

These were withheld from this repository until 2026-08-18, on the reasoning
that a company repository could not have a noncommercial purpose. That tested
the wrong thing. PolyForm gates on purpose, not on the identity of the user,
and this project's use is academic research only. If that ever stops being
true, these files must be removed again. scripts/sync_public_repo.py asserts
that every one of them carries its notice, and fails the sync if any does not.

Nothing under src/ derives from them. They are tools for regenerating test
fixtures, are never imported, and are never run by the test suite, which
compares against captured JSON instead.
"""

GPL_NOTE = """\
{gpl_list} {verb} released under the GPL, a copyleft licence, while this
repository is Apache-2.0. The GPL's obligations attach to distribution rather
than to use, so not redistributing them is what keeps the two compatible,
which costs nothing here, because they are a verification tool rather than a
dependency.

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="baseline")
    ap.add_argument("--holder", default="M31 Biomedical AI")
    ap.add_argument("--year", default="2026")
    ap.add_argument("--out", type=Path, default=ROOT / "NOTICE")
    ap.add_argument(
        "--manifest", type=Path, default=ROOT / "collected" / "MANIFEST.yaml"
    )
    args = ap.parse_args()

    packages = yaml.safe_load(args.manifest.read_text())["packages"]

    width = max(len(p["name"]) for p in packages)
    lic_width = max(len(str(p["license"])) for p in packages)
    rows = [
        f"    {p['name']:<{width}}  {str(p['license']):<{lic_width}}  {p['source']}"
        for p in packages
    ]

    gpl = [p["name"] for p in packages if "GPL" in str(p["license"]).upper()]
    gpl_note = ""
    if gpl:
        listed = (
            " and ".join([", ".join(gpl[:-1]), gpl[-1]]) if len(gpl) > 1 else gpl[0]
        )
        gpl_note = GPL_NOTE.format(
            gpl_list=listed, verb="are" if len(gpl) > 1 else "is"
        )

    # Read from registry/withheld_third_party_files.yaml, which both this
    # renderer and scripts/sync_public_repo.py load, so the list has one home
    # and cannot drift between the file that NAMES the withheld files and the
    # script that ENFORCES their exclusion.
    #
    # The list has one home so that the file NAMING these files and the tooling
    # ENFORCING their notices cannot disagree about which files they are.
    import yaml as _yaml

    withheld = _yaml.safe_load(
        (ROOT / "registry" / "polyform_noncommercial_files.yaml").read_text()
    )["polyform_noncommercial"]
    polyform = sorted(f"    {path}" for path in withheld)

    # Model sources whose own licence conditions use on attribution. Derived
    # from `license_basis`, which is where each determination was written, so
    # this cannot list a term the registry does not actually record.
    import re as _re

    from cancerverse_baseline.registry import load_models

    attribution = []
    for model in sorted(load_models(), key=lambda m: m["id"]):
        if model.get("status") != "implemented":
            continue
        basis = str(model.get("license_basis") or "")
        # Match the licence token only. The lazy form used first stopped at the
        # "." inside a version number and emitted "CC BY-NC-ND 4" for 4.0, so
        # the version is matched explicitly rather than left to a lookahead.
        term = _re.match(r"\s*(CC[ -]BY(?:-[A-Z]{2})*(?:\s+\d+\.\d+)?)", basis)
        if not term:
            continue
        citation = " ".join(str(model.get("citation_apa")
                                or model.get("citation") or "").split())
        attribution.append(
            f"    {model['id']}  —  {term.group(1).strip()}\n"
            f"        {citation}")
    attribution_list = "\n".join(attribution) or "    (none)"

    text = TEMPLATE.format(
        name=args.name,
        holder=args.holder,
        year=args.year,
        table="\n".join(rows),
        gpl_note=gpl_note,
        polyform_list="\n".join(polyform),
        attribution_list=attribution_list,
    )
    write_text_atomically(args.out, text)
    print(
        f"wrote {args.out} — {len(packages)} package(s) named, {len(gpl)} of them GPL"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
