"""Build APA citations for every model, from authoritative metadata.

    python scripts/fetch_citations.py            # report what resolves
    python scripts/fetch_citations.py --write    # write into the registry

The registry's `citation` field was written by hand in a compressed house
style: "Cooperberg MR et al. J Urol. 2005;173(6):1938-1942". That is enough
to find a paper and not enough to cite one: APA needs every author, the article
title, and the DOI as a URL.

So this does not reformat the existing strings. It resolves each model's
`source_url` to a PMID and pulls the record from NCBI, which is the same route
the discrimination harvester uses and which has no reCAPTCHA. Author lists,
titles, volume, issue and pages all come from the record rather than from our
retyping, because retyping an author list is exactly where a citation acquires
a silent error.

Two fields are written:

    paper_title      the article title on its own, so a table can hyperlink it
    citation_apa     the full APA 7th reference

`citation` is left alone. It is short enough to sit in a narrow column and is
referenced in prose in several places; APA belongs beside it, not instead of
it.

Where a DOI resolves to nothing in PubMed the model is reported and skipped
rather than guessed at.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cancerverse_baseline.registry.save import save_models  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = "cancerverse-citations/1.0 (research)"


def _get(url: str, tries: int = 4) -> str:
    import urllib.error

    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            return urllib.request.urlopen(req, timeout=60).read().decode(
                "utf-8", "replace")
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def pmid_for(source_url: str) -> str | None:
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", source_url or "")
    if m:
        return m.group(1)
    m = re.search(r"doi\.org/(.+)$", source_url or "")
    if not m:
        return None
    doi = m.group(1).rstrip("/")
    try:
        j = json.loads(_get(
            "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
            f"?ids={urllib.parse.quote(doi)}&format=json"))
        pmid = (j.get("records") or [{}])[0].get("pmid")
        if pmid:
            return pmid
    except Exception:
        pass
    for term in (f'"{doi}"[DOI]', f'"{doi}"[AID]'):
        try:
            xml = _get(f"{EUTILS}/esearch.fcgi?db=pubmed"
                       f"&term={urllib.parse.quote(term)}&retmode=xml")
            ids = ET.fromstring(xml).findall(".//Id")
            if ids:
                return ids[0].text
        except Exception:
            continue
        time.sleep(0.4)
    return None


#: Small words APA leaves lower-case inside a title.
_MINOR = {"a", "an", "and", "the", "of", "for", "in", "on", "to", "with", "at",
          "by", "from", "as", "or", "nor", "but"}


def _journal_name(raw: str) -> str:
    """PubMed's journal title, in the form APA wants.

    NLM stores these lower-cased and with the society subtitle attached --
    "Journal of clinical oncology : official journal of the American Society of
    Clinical Oncology". APA cites the journal by the name it is known by, in
    title case, so the subtitle is dropped and the words are capitalised.
    """
    name = raw.split(" : ")[0].strip()
    words = name.split()
    out = []
    for i, w in enumerate(words):
        if w.isupper() or any(c.isdigit() for c in w):
            out.append(w)                       # BMC, JAMA, acronyms
        elif i and w.lower() in _MINOR:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def _initials(fore: str | None) -> str:
    """APA gives initials with periods and spaces: 'Mark W.' -> 'M. W.'"""
    if not fore:
        return ""
    return " ".join(f"{part[0]}." for part in re.split(r"[\s\-]+", fore) if part)


def apa(record: ET.Element, doi: str | None) -> tuple[str, str] | None:
    title = (record.findtext(".//ArticleTitle") or "").strip().rstrip(".")
    if not title:
        return None
    journal = _journal_name(record.findtext(".//Journal/Title") or "")
    year = (record.findtext(".//JournalIssue/PubDate/Year")
            or record.findtext(".//PubDate/Year") or "n.d.")
    volume = record.findtext(".//JournalIssue/Volume") or ""
    issue = record.findtext(".//JournalIssue/Issue") or ""
    pages = record.findtext(".//Pagination/MedlinePgn") or ""

    names = []
    for a in record.findall(".//AuthorList/Author"):
        last = a.findtext("LastName")
        if last:
            names.append(f"{last}, {_initials(a.findtext('ForeName'))}".strip())
        elif a.findtext("CollectiveName"):
            names.append(a.findtext("CollectiveName").strip())

    # APA 7th: up to 20 authors listed; beyond that, first 19 … last.
    if len(names) > 20:
        authors = ", ".join(names[:19]) + ", . . . " + names[-1]
    elif len(names) > 1:
        authors = ", ".join(names[:-1]) + ", & " + names[-1]
    else:
        authors = names[0] if names else ""

    ref = f"{authors} ({year}). {title}."
    if journal:
        ref += f" {journal}"
        if volume:
            ref += f", {volume}"
            if issue:
                ref += f"({issue})"
        if pages:
            ref += f", {pages}"
        ref += "."
    if doi:
        ref += f" https://doi.org/{doi}"
    return title, re.sub(r"\s+", " ", ref).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    p = ROOT / "registry" / "models.yaml"
    d = yaml.safe_load(p.read_text())
    # Catalog entries too: a model lined up as a replacement is named in the
    # submission documents, so it needs the same citation the implemented ones
    # get. BCSC appeared there with an empty reference until this changed.
    impl = [m for m in d["models"]
            if m.get("status") in {"implemented", "catalog"}
            and m.get("source_url")]

    done, failed = 0, []
    for m in impl:
        src = m.get("source_url") or ""
        doi_m = re.search(r"doi\.org/(.+)$", src)
        doi = doi_m.group(1).rstrip("/") if doi_m else None
        pmid = pmid_for(src)
        if not pmid:
            failed.append(f"{m['id']}: no PMID from {src or '(no source_url)'}")
            continue
        try:
            rec = ET.fromstring(_get(
                f"{EUTILS}/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"))
            if not doi:
                doi = next((a.text for a in rec.findall(".//ArticleId")
                            if a.get("IdType") == "doi"), None)
            built = apa(rec, doi)
        except Exception as exc:
            failed.append(f"{m['id']}: {exc}")
            continue
        if not built:
            failed.append(f"{m['id']}: PMID {pmid} has no title")
            continue
        title, ref = built
        m["paper_title"] = title
        m["citation_apa"] = ref
        done += 1
        print(f"  {m['id']:<24} {title[:70]}")
        time.sleep(0.4)

    print(f"\n{done}/{len(impl)} resolved")
    for f in failed:
        print(f"  UNRESOLVED  {f}")
    if args.write:
        save_models(d["models"], p)
        print(f"\nwrote {p.relative_to(ROOT)}")
    else:
        print("\n(dry run, pass --write to save)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
