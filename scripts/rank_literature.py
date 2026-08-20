#!/usr/bin/env python3
"""Rank a hand-curated candidate list by how much the papers have been read.

    python scripts/rank_literature.py docs/literature/gastric-response/candidates.yaml
    python scripts/rank_literature.py <dir-or-file> --write   # rewrite RANKING.md beside it

This is the counterpart to `fetch_impact.py`. That script ranks papers we have
already committed to, reading them out of `registry/models.yaml`. This one ranks
papers we have not committed to yet: the shortlist that comes out of a
literature search for one empty cell, before any of them is implemented.

The input is a `candidates.yaml` written by hand during the search. Everything
in it that a human had to read the paper to know, what the model takes as
input, whether the coefficients are printed, how the validation was done,
stays hand-written and is never inferred here. What this script adds is the
part that is a lookup: OpenAlex's citation count, the publication year, the
journal, and the journal's citedness.

**On "impact factor".** Clarivate's JIF is proprietary and is not fetched here,
for the reason spelled out at the top of `fetch_impact.py`: OpenAlex's
`2yr_mean_citedness` is diluted to uselessness for journals that deposit
conference abstracts, so it is inconsistently wrong and cannot be used to rank.
It is reported beside `works_count` so the dilution is visible, and it is NOT an
input to the ordering. If a real JIF is needed it has to come from Journal
Citation Reports, by hand, into the `jif` field of `candidates.yaml`.

**What the ordering actually is.** Papers are sorted by citations per year,
which is the fairer of the two citation measures when a shortlist mixes a 2019
paper with a 2025 one. That ordering answers "which of these has been read",
and that is the only question it answers. It is deliberately not a quality
score: a highly-cited radiomics model this library cannot take as input is
still unusable, and the `usable` column is what says so. Read both columns.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

OPENALEX = "https://api.openalex.org"
MAILTO = "research@example.org"
UA = "cancerverse-literature/1.0 (research)"
THIS_YEAR = 2026


def _get(url: str, tries: int = 4) -> dict | None:
    import time

    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as fh:
                return json.load(fh)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)
        except urllib.error.URLError:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)
    return None


def resolve(paper: dict) -> dict:
    """Look one candidate up in OpenAlex, by DOI first and PMID as a fallback."""
    out = dict(paper)
    out.update(citations=None, cites_per_year=None, journal=None, title=None,
               first_author=None, journal_2yr_mean=None, journal_works=None,
               openalex=None)

    rec = None
    doi = paper.get("doi")
    if doi:
        doi = doi.replace("https://doi.org/", "").strip()
        rec = _get(f"{OPENALEX}/works/doi:{urllib.parse.quote(doi)}?mailto={MAILTO}")
    if rec is None and paper.get("pmid"):
        rec = _get(f"{OPENALEX}/works/pmid:{paper['pmid']}?mailto={MAILTO}")
    if rec is None:
        return out

    out["citations"] = rec.get("cited_by_count")
    out["openalex"] = rec.get("id")
    out["title"] = rec.get("title")
    auth = rec.get("authorships") or []
    if auth:
        out["first_author"] = (auth[0].get("author") or {}).get("display_name")
    year = rec.get("publication_year") or paper.get("year")
    out["year"] = year
    if year and out["citations"] is not None:
        out["cites_per_year"] = round(out["citations"] / max(1, THIS_YEAR - year + 1), 1)

    src = ((rec.get("primary_location") or {}).get("source")) or {}
    out["journal"] = src.get("display_name") or paper.get("journal")
    if src.get("id"):
        s = _get(f"{OPENALEX}/sources/{src['id'].rsplit('/', 1)[-1]}?mailto={MAILTO}")
        if s:
            out["journal_2yr_mean"] = (s.get("summary_stats") or {}).get("2yr_mean_citedness")
            out["journal_works"] = s.get("works_count")
    return out


COLUMNS = ["key", "first_author", "year", "citations", "cites_per_year",
           "journal", "jif", "journal_2yr_mean", "journal_works", "endpoint",
           "inputs", "usable", "n_train", "n_val", "val_kind", "auc", "code",
           "pmid", "doi", "title", "openalex"]


def render(rows: list[dict]) -> str:
    head = ("| # | Paper | Year | Cites | /yr | Journal | JIF | Inputs | "
            "Equation published? |\n|---|---|---|---|---|---|---|---|---|\n")
    body = ""
    for i, r in enumerate(rows, 1):
        cite = "—" if r.get("citations") is None else r["citations"]
        per = "—" if r.get("cites_per_year") is None else r["cites_per_year"]
        body += (f"| {i} | {r.get('key', '')} | {r.get('year', '—')} | {cite} | {per} "
                 f"| {r.get('journal') or '—'} | {r.get('jif') or '—'} "
                 f"| {r.get('inputs') or '—'} | {r.get('usable') or '—'} |\n")
    return head + body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="candidates.yaml, or the directory holding it")
    ap.add_argument("--write", action="store_true",
                    help="write ranked.csv and RANKING.md beside the input")
    args = ap.parse_args()

    path = Path(args.target)
    if path.is_dir():
        path = path / "candidates.yaml"
    papers = yaml.safe_load(path.read_text())["candidates"]

    rows = [resolve(p) for p in papers]
    unresolved = [r["key"] for r in rows if r["citations"] is None]
    rows.sort(key=lambda r: (r.get("cites_per_year") or -1), reverse=True)

    print(render(rows))
    if unresolved:
        print(f"\nnot found in OpenAlex ({len(unresolved)}): {', '.join(unresolved)}")

    if args.write:
        csv_path = path.with_name("ranked.csv")
        with csv_path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
