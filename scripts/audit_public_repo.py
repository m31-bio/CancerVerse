"""Check what the public repository actually publishes, against what it should.

    python scripts/audit_public_repo.py                 # audit the live remote
    python scripts/audit_public_repo.py --local PATH    # audit a directory

"Is it compliant?" is not a question anyone should answer from memory. This
reads the published tree and checks it, so the answer is a exit code rather
than an assurance.

It audits the REMOTE by default, not the local working copy. The two drift, and
the local copy is not what other people can see; auditing the tree in front of
you is how a difference between them goes unnoticed.

Checks, in the order that matters:

  1. no private paths            vault/ and slides/ are internal
  2. no vendored third-party     two of the five packages are GPL
  3. no copyrighted PDFs         redistributing paywalled papers is a real
                                 copyright problem, and a worse one than the
                                 licence mixing that prompted this script
  4. a licence exists            no LICENSE means all rights reserved, which
                                 stops colleagues using it at all
  5. NOTICE names every          a dependency that is used but not declared is
     third-party dependency      the failure mode attribution rules exist for
  6. manifest URLs resolve       a pinned source that 404s cannot be fetched,
                                 so the "fetch on demand" story silently breaks
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
#: Default remote to audit. Overridable with --repo: there is more than one
#: repository in this project's orbit, and hardcoding a single name is how the
#: wrong one gets checked.
DEFAULT_REPO = "Ziqi-Hao/CancerVerse"

PRIVATE = re.compile(r"^(vault|slides)/")
VENDORED = re.compile(
    r"^collected/(BCRA|PLCOm2012|RiskScorescvd|predictv30r|preventr)/")
#: Article PDFs. `docs/` may legitimately hold our own generated PDFs, so this
#: flags every PDF for a human rather than trying to tell them apart.
PDFS = re.compile(r"\.pdf$", re.I)

#: Internal working notes. This check exists because the first version of this
#: script did not have it and therefore passed a repository that was publishing
#: docs/SESSION_SALVAGE_2026-08-05.md -- a note about a failed session which
#: states, among other things, that the organisation had hit its monthly spend
#: limit. Directory-level rules (vault/, slides/) missed it because it sat in
#: docs/ alongside legitimate documentation.
INTERNAL_NOTES = re.compile(
    r"(SESSION_SALVAGE|SALVAGE|_INTERNAL|SCRATCH|TODO_PRIVATE|MEETING)", re.I)

#: Phrases that mark a file as internal regardless of where it lives. Operational
#: and billing detail about the organisation is the category that matters: it is
#: nobody's business outside it, and it is easy to leave in a working note.
#: Names of components in the wider system this repository is one layer of.
#: docs/CONVENTIONS.md listed four of them as "out of scope", which told a
#: reader outside the team nothing while sketching the architecture of the
#: parent project to anyone who opened the file. A scope boundary stated as a
#: property needs no product names, so any that reappear are a leak, not a
#: definition.
INTERNAL_COMPONENTS = [
    "medsam",
    "scgpt",
    "temporal transformer",
    "unified embedding",
]
#: NOT in that list, deliberately: the parent project's own name. Naming the
#: project this repository belongs to is ordinary attribution -- it is already
#: the repository description -- while naming the components inside it sketches
#: an architecture. The first version of this check conflated the two and
#: flagged a legitimate sentence in docs/REPRODUCIBILITY_MAP.md explaining why
#: the response axis matters.

INTERNAL_PHRASES = [
    "spend limit",
    "monthly spend",
    "org monthly",
    "billing",
    "seat limit",
    "internal only",
    "do not share",
    "confidential",
]


def remote_tree(repo: str) -> list[str]:
    out = subprocess.run(
        ["gh", "api", f"repos/{repo}/git/trees/main?recursive=1",
         "--jq", ".tree[].path"],
        capture_output=True, text=True, check=True)
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def local_tree(path: Path) -> list[str]:
    """Every file the directory would publish.

    Falls back to a filesystem walk when the directory is not a git repository.
    That case is not an edge case -- it is the important one: a candidate
    publish directory should be audited BEFORE `git init`, while removing a
    file still costs nothing. Requiring git here meant the one tree actually
    destined for other people could not be checked at all.
    """
    out = subprocess.run(["git", "ls-files"], cwd=path,
                         capture_output=True, text=True)
    if out.returncode == 0 and out.stdout.strip():
        return [ln for ln in out.stdout.splitlines() if ln.strip()]

    skip = {".git", "__pycache__", ".pytest_cache", ".venv", ".ruff_cache",
            "node_modules"}
    files = []
    for p in path.rglob("*"):
        if p.is_dir() or skip & set(p.relative_to(path).parts):
            continue
        if p.suffix in {".pyc", ".pyo"}:
            continue
        files.append(str(p.relative_to(path)))
    return sorted(files)


def remote_file(repo: str, path: str) -> str | None:
    r = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}", "--jq", ".content"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import base64
    return base64.b64decode(r.stdout.strip()).decode("utf-8", "replace")


def url_ok(url: str) -> bool:
    try:
        req = urllib.request.Request(
            url, method="HEAD",
            headers={"User-Agent": "cancerverse-compliance-audit/1.0"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status < 400
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", type=Path,
                    help="audit this directory instead of the live remote")
    ap.add_argument("--repo", default=DEFAULT_REPO,
                    help="owner/name of the remote to audit")
    ap.add_argument("--skip-network", action="store_true",
                    help="skip the manifest URL resolution check")
    args = ap.parse_args()

    if args.local:
        tree = local_tree(args.local)
        read = lambda p: (args.local / p).read_text(errors="replace") \
            if (args.local / p).exists() else None
        where = str(args.local)
    else:
        tree = remote_tree(args.repo)
        read = lambda p: remote_file(args.repo, p)
        where = f"github.com/{args.repo} (live)"

    print(f"auditing {where}\n  {len(tree)} published files\n")
    failures: list[str] = []
    warnings: list[str] = []

    # 1 ------------------------------------------------------------- private
    private = [p for p in tree if PRIVATE.match(p)]
    if private:
        failures.append(
            f"{len(private)} private file(s) published, e.g. {private[:3]}")
    print(f"  [{'FAIL' if private else ' ok '}] no private paths "
          f"(vault/, slides/): {len(private)} found")

    # 2 ----------------------------------------------------------- vendored
    vend = [p for p in tree if VENDORED.match(p)]
    if vend:
        failures.append(
            f"{len(vend)} vendored third-party file(s) published (two of the "
            f"five packages are GPL), e.g. {vend[:3]}")
    print(f"  [{'FAIL' if vend else ' ok '}] no vendored third-party source: "
          f"{len(vend)} found")

    # 3 --------------------------------------------------------------- PDFs
    pdfs = [p for p in tree if PDFS.search(p)]
    if pdfs:
        warnings.append(
            f"{len(pdfs)} PDF(s) published -- confirm none is a copyrighted "
            f"article: {pdfs[:5]}")
    print(f"  [{'warn' if pdfs else ' ok '}] no article PDFs: {len(pdfs)} found")

    # 3b -------------------------------------------------- internal notes
    notes = [p for p in tree if INTERNAL_NOTES.search(Path(p).name)]
    if notes:
        failures.append(f"internal working note(s) published: {notes}")
    print(f"  [{'FAIL' if notes else ' ok '}] no internal working notes by "
          f"name: {len(notes)} found")

    # 3c ------------------------------------- internal detail by content
    # Only the text files, and only the ones cheap to read: this is a
    # backstop for notes that do not announce themselves in the filename.
    leaky: list[str] = []
    for p in tree:
        if not p.endswith((".md", ".txt", ".yaml", ".yml")):
            continue
        body = read(p)
        if not body:
            continue
        low = body.lower()
        hits = [ph for ph in INTERNAL_PHRASES if ph in low]
        hits += [c for c in INTERNAL_COMPONENTS if c in low]
        if hits:
            leaky.append(f"{p} ({', '.join(hits)})")
    if leaky:
        failures.append(f"internal/operational detail in published text: {leaky}")
    print(f"  [{'FAIL' if leaky else ' ok '}] no internal detail in published "
          f"text: {len(leaky)} file(s)")

    # 3d ------------------------------------- claims about named vendors
    # Not a compliance failure, and deliberately not treated as one: the
    # defect log is true, evidenced by reproducible tests, and is this
    # project's most original output. But several entries assert that a named
    # organisation's DEPLOYED CLINICAL TOOL computes the wrong number -- one
    # says a calculator over-scores a group of women by about 4.2%. Published
    # under an individual's account that is research; published under a
    # company's, it carries different weight and deserves the same courtesy a
    # security finding gets, which is to tell the vendor first.
    #
    # So this warns, every time, and names the files. Someone should be
    # deciding this at each publish rather than inheriting it.
    vendors = re.compile(r"riskcalc\.org|Cleveland Clinic|MSKCC|MDCalc|SWOP")
    defect = re.compile(
        r"\b(defect|dead code|cannot (apply|fire)|over-?(score|estimate)|"
        r"mislabel|contradicts|does not do what)\b", re.I)
    claiming = []
    for p in tree:
        if not p.endswith(".md"):
            continue
        body = read(p) or ""
        lines = [ln for ln in body.splitlines()
                 if vendors.search(ln) and defect.search(ln)]
        if lines:
            claiming.append(f"{p} ({len(lines)} claim(s))")
    if claiming:
        warnings.append(
            "publishes defect claims about named third-party clinical tools: "
            f"{claiming}. True and evidenced, but confirm the vendors have "
            "been told before publishing this under an organisation's name.")
    print(f"  [{'warn' if claiming else ' ok '}] third-party defect claims: "
          f"{len(claiming)} file(s)")

    # 4 ------------------------------------------------------------ licence
    has_licence = "LICENSE" in tree or "LICENSE.md" in tree
    if not has_licence:
        failures.append("no LICENSE file -- the repo is all-rights-reserved "
                        "and colleagues cannot legally use it")
    print(f"  [{' ok ' if has_licence else 'FAIL'}] LICENSE present")

    # 5 ------------------------------------------------------------- NOTICE
    notice = read("NOTICE") or ""
    manifest_raw = read("collected/MANIFEST.yaml")
    if manifest_raw is None:
        manifest_raw = (ROOT / "collected" / "MANIFEST.yaml").read_text()
        warnings.append("collected/MANIFEST.yaml is not published; read the "
                        "local copy to check NOTICE against it")
    packages = yaml.safe_load(manifest_raw)["packages"]
    undeclared = [p["name"] for p in packages if p["name"] not in notice]
    if undeclared:
        failures.append(f"used but not declared in NOTICE: {undeclared}")
    print(f"  [{'FAIL' if undeclared else ' ok '}] NOTICE declares all "
          f"{len(packages)} third-party dependencies")

    # 6 --------------------------------------------------------- pinned URLs
    if args.skip_network:
        print("  [skip] manifest source URLs (--skip-network)")
    else:
        dead = [f"{p['name']} -> {p['source']}"
                for p in packages if not url_ok(p["source"])]
        if dead:
            failures.append(f"pinned source URL does not resolve: {dead}")
        print(f"  [{'FAIL' if dead else ' ok '}] all {len(packages)} pinned "
              f"source URLs resolve")

    # ------------------------------------------------------------- verdict
    print()
    for w in warnings:
        print(f"  warning: {w}")
    if failures:
        print(f"\nNOT COMPLIANT -- {len(failures)} problem(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("COMPLIANT: nothing published that should not be, licence and "
          "attribution in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
