#!/usr/bin/env python3
"""Fetch the third-party reference implementations used for verification.

These are NOT vendored into this repository. BCRA is GPL (>= 2) and PLCOm2012 is
GPL-3; vendoring them alongside Apache-2.0 code creates an avoidable licensing
question, and they add several megabytes for something only needed when
re-running a parity check. Nothing in src/ imports them at runtime.

    python scripts/fetch_references.py            # list what is pinned
    python scripts/fetch_references.py --fetch    # download into collected/

CRAN packages are fetched as source tarballs from the CRAN archive; GitHub-only
packages are cloned. Versions are pinned in collected/MANIFEST.yaml.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "collected" / "MANIFEST.yaml"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="actually download")
    args = ap.parse_args()

    data = yaml.safe_load(MANIFEST.read_text())
    print(data["note"], "\n")

    for pkg in data["packages"]:
        present = (ROOT / "collected" / pkg["name"]).exists()
        mark = "present" if present else "absent "
        print(
            f"[{mark}] {pkg['name']:16} {str(pkg['version']):11} "
            f"{pkg['license']:20} {pkg['source']}"
        )
        print(f"           verifies: {pkg['used_for']}")

    if not args.fetch:
        print("\nRe-run with --fetch to download the absent ones.")
        return 0

    dest = ROOT / "collected"
    dest.mkdir(exist_ok=True)
    for pkg in data["packages"]:
        if (dest / pkg["name"]).exists():
            print(f"skip {pkg['name']} (already present)")
            continue
        src = pkg["source"] or ""
        if "github.com" in src:
            cmd = ["git", "clone", "--depth", "1", src, str(dest / pkg["name"])]
        elif "cran.r-project.org" in src:
            url = (
                f"https://cran.r-project.org/src/contrib/"
                f"{pkg['name']}_{pkg['version']}.tar.gz"
            )
            cmd = ["sh", "-c", f"curl -fsSL {url} | tar xz -C {dest}"]
        else:
            print(f"!! {pkg['name']}: no known fetch method for {src!r}")
            continue
        print("+", " ".join(cmd))
        subprocess.run(cmd, check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
