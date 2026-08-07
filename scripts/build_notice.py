"""Generate NOTICE from collected/MANIFEST.yaml.

    python scripts/build_notice.py                      # write ./NOTICE
    python scripts/build_notice.py --name CancerVerse --out ../CancerVerse/NOTICE

Attribution is the one file that must not drift from the thing it describes,
and a hand-written NOTICE drifts the moment a dependency is added or a licence
changes. `audit_public_repo.py` requires every package in the manifest to be
named in NOTICE; this generates it from the same manifest, so the check cannot
be satisfied by editing prose.

It caught a live gap: CancerVerse -- the repository actually meant for other
people -- described the third-party packages as a group ("each retains its own
license") without naming any of them, so a reader could not tell which
dependency carried which licence, and two of the five are GPL.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

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
"""

GPL_NOTE = """\
{gpl_list} {verb} released under the GPL, a copyleft licence, while this
repository is Apache-2.0. The GPL's obligations attach to distribution rather
than to use, so not redistributing them is what keeps the two compatible --
which costs nothing here, because they are a verification tool rather than a
dependency.

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="baseline")
    ap.add_argument("--holder", default="M31 Biomedical AI")
    ap.add_argument("--year", default="2026")
    ap.add_argument("--out", type=Path, default=ROOT / "NOTICE")
    ap.add_argument("--manifest", type=Path,
                    default=ROOT / "collected" / "MANIFEST.yaml")
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
        listed = " and ".join([", ".join(gpl[:-1]), gpl[-1]]) if len(gpl) > 1 \
            else gpl[0]
        gpl_note = GPL_NOTE.format(
            gpl_list=listed, verb="are" if len(gpl) > 1 else "is")

    text = TEMPLATE.format(name=args.name, holder=args.holder, year=args.year,
                           table="\n".join(rows), gpl_note=gpl_note)
    args.out.write_text(text)
    print(f"wrote {args.out} — {len(packages)} package(s) named, "
          f"{len(gpl)} of them GPL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
