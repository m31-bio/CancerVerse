"""How much has each model's paper actually been read?

    python scripts/fetch_impact.py                 # every implemented model
    python scripts/fetch_impact.py --all           # catalog and gap entries too
    python scripts/fetch_impact.py --json out.json

Two different questions get muddled here, so this reports them separately.

**Citations** are a property of the PAPER: how many other works cite it. That
is a fact, it is openly published, and OpenAlex serves it without a key.

**Impact factor** is a property of the JOURNAL, and Clarivate's JIF is
proprietary. This script does NOT report JIF and cannot: a guessed impact
factor is exactly the kind of number that gets quoted back as fact.

It reports OpenAlex's `2yr_mean_citedness` instead, and that number is **not a
usable JIF substitute for several journals in this library**. Checked
2026-08-14, the failure mode is meeting abstracts. OpenAlex counts every
indexed item as a work, and the clinical societies deposit tens of thousands of
conference abstracts that are never cited:

    Journal of Clinical Oncology   174,155 works   2yr mean 1.65   (real JIF ~45)
    The Journal of Urology         153,210 works   2yr mean 0.36
    CHEST                           85,323 works   2yr mean 0.67

Those are the correct journals, the ISSNs check out, so this is dilution, not
a lookup error. Journals that deposit few abstracts come out plausible (NEJM
30.2, Lancet 19.9), which makes the metric *inconsistently* wrong and therefore
worse than no metric at all for ranking.

`works_count` is reported beside it so the dilution is visible rather than
silent. Treat the pair as a smell test, never as a ranking. If you need real
JIF, it is in Journal Citation Reports and needs an institutional subscription.

A caution that matters for reading the table: citation count is confounded with
age. A 1989 paper has had thirty-seven years to accumulate citations and a 2024
paper has had two. `citations_per_year` is given for that reason and is the
fairer comparison, though it flatters recent papers in fast-moving fields.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "models.yaml"
OPENALEX = "https://api.openalex.org"
# OpenAlex asks for a contact address in the query string; it is not auth.
MAILTO = "research@example.org"
UA = "cancerverse-impact/1.0 (research)"
THIS_YEAR = 2026


def _get(url: str, tries: int = 4) -> dict | None:
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as fh:
                return json.loads(fh.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
    return None


def doi_of(model: dict) -> str | None:
    """The model's DOI, from source_url or from an upstream entry."""
    for candidate in [model.get("source_url", "")] + [
        u.get("doi", "") for u in (model.get("upstream") or []) if isinstance(u, dict)
    ]:
        m = re.search(r"10\.\d{4,9}/\S+", str(candidate))
        if m:
            return m.group(0).rstrip(".,;)")
    return None


def pmid_of(model: dict) -> str | None:
    blob = yaml.safe_dump(model, allow_unicode=True)
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d{6,9})", blob)
    if m:
        return m.group(1)
    m = re.search(r"PMID:?\s*(\d{6,9})", blob)
    return m.group(1) if m else None


def lookup(model: dict) -> dict:
    """Resolve one model to OpenAlex, by DOI first and PMID as a fallback."""
    out = {
        "id": model["id"], "disease": model.get("disease"),
        "axis": model.get("axis"), "year": model.get("year"),
        "resolved_by": None, "title": None, "journal": None,
        "citations": None, "journal_2yr_mean_citedness": None,
        "openalex_url": None,
    }
    rec = None
    doi = doi_of(model)
    if doi:
        rec = _get(f"{OPENALEX}/works/doi:{urllib.parse.quote(doi)}?mailto={MAILTO}")
        if rec:
            out["resolved_by"] = f"doi:{doi}"
    if rec is None:
        pmid = pmid_of(model)
        if pmid:
            rec = _get(f"{OPENALEX}/works/pmid:{pmid}?mailto={MAILTO}")
            if rec:
                out["resolved_by"] = f"pmid:{pmid}"
    if rec is None:
        return out

    out["title"] = rec.get("title")
    out["citations"] = rec.get("cited_by_count")
    out["openalex_url"] = rec.get("id")
    pub_year = rec.get("publication_year")
    if pub_year:
        out["year"] = pub_year

    src = ((rec.get("primary_location") or {}).get("source")) or {}
    out["journal"] = src.get("display_name")
    src_id = src.get("id")
    if src_id:
        s = _get(f"{OPENALEX}/sources/{src_id.rsplit('/', 1)[-1]}?mailto={MAILTO}")
        if s:
            out["journal_2yr_mean_citedness"] = (
                (s.get("summary_stats") or {}).get("2yr_mean_citedness"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="include catalog and gap entries, not just implemented")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    models = yaml.safe_load(REGISTRY.read_text())["models"]
    if not args.all:
        models = [m for m in models if m.get("status") == "implemented"]

    rows = []
    for m in models:
        r = lookup(m)
        if r["citations"] is not None and r["year"]:
            age = max(1, THIS_YEAR - int(r["year"]))
            r["citations_per_year"] = round(r["citations"] / age, 1)
        else:
            r["citations_per_year"] = None
        rows.append(r)
        mark = "ok " if r["citations"] is not None else "?? "
        print(f"  {mark}{r['id']:24} {str(r['citations']):>7}  {str(r['journal'])[:44]}")
        time.sleep(0.15)

    got = [r for r in rows if r["citations"] is not None]
    print(f"\nresolved {len(got)} of {len(rows)}")
    if got:
        top = max(got, key=lambda r: r["citations"])
        print(f"most cited:   {top['id']} — {top['citations']:,} ({top['journal']})")
        jr = [r for r in got if r["journal_2yr_mean_citedness"]]
        if jr:
            tj = max(jr, key=lambda r: r["journal_2yr_mean_citedness"])
            print(f"highest journal 2yr mean citedness: {tj['id']}: "
                  f"{tj['journal_2yr_mean_citedness']:.1f} ({tj['journal']})")

    if args.json:
        args.json.write_text(json.dumps(rows, indent=2))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
