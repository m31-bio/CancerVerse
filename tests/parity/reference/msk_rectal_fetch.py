"""Capture reference outputs from MSK's own hosted rectal calculator.

Verification route 6 (POST to the server endpoint), used here because the model
is published only as an image in a supplement and has no worked example.

MSK hosts the deployed model at

    https://www.mskcc.org/nomograms/rectal/post-treatment

whose "Supporting Publication" block cites exactly our equation source (Weiser
MR et al. JAMA Netw Open. 2021;4(11):e2133457, PMCID PMC8576585), so the tool
and the paper are the same model. The page is a Drupal form that POSTs to
/nomograms/rectal/post_treatment and renders the two probabilities server-side;
there are no client-side coefficients to read.

This script is NOT run by the test suite. It writes msk_rectal_cases.json, and
tests/parity/test_msk_rectal_parity.py asserts against that captured file so CI
stays offline. Re-run it only to refresh the fixture:

    python tests/parity/reference/msk_rectal_fetch.py

The tool reports whole percentages, so the fixture resolution is 1 point.

Caveat recorded deliberately: MSK's form field is named
`distance_from_the_anal_verge_gt_5cm` (greater than 5), while both the eFigure
equation and the eTable print `DTAV >= 5`. The form makes the *user* apply the
threshold, so a POST cannot distinguish > from >=. We follow the paper (>=5).
Cases below avoid distance exactly 5 cm so the ambiguity never bites.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

PAGE = "https://www.mskcc.org/nomograms/rectal/post-treatment"
ENDPOINT = "https://www.mskcc.org/nomograms/rectal/post_treatment"
OUT = Path(__file__).with_name("msk_rectal_cases.json")

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Incomplete responders only, the equation's scope. Spans both ypT reference
# groups (T0/T1/T2 collapse differently for RFS and OS), the posLN spline knots
# at 0/1/3, and both binary covariates.
CASES = [
    dict(age=60, t_stage="T3", nodes=2, dtav_gt5=True, vi=False, pni=False),
    dict(age=40, t_stage="T1", nodes=0, dtav_gt5=True, vi=False, pni=False),
    dict(age=75, t_stage="T4", nodes=7, dtav_gt5=False, vi=True, pni=True),
    dict(age=55, t_stage="T2", nodes=1, dtav_gt5=False, vi=True, pni=False),
    dict(age=68, t_stage="T3", nodes=3, dtav_gt5=True, vi=False, pni=True),
    dict(age=45, t_stage="T1", nodes=0, dtav_gt5=False, vi=False, pni=False),
    dict(age=80, t_stage="T2", nodes=5, dtav_gt5=True, vi=True, pni=True),
    dict(age=36, t_stage="T4", nodes=1, dtav_gt5=True, vi=False, pni=False),
    dict(age=52, t_stage="T3", nodes=0, dtav_gt5=False, vi=True, pni=True),
    dict(age=64, t_stage="T1", nodes=4, dtav_gt5=True, vi=True, pni=False),
    dict(age=71, t_stage="T2", nodes=2, dtav_gt5=False, vi=False, pni=True),
    dict(age=58, t_stage="T4", nodes=9, dtav_gt5=True, vi=True, pni=True),
]

# The hosted tool REJECTS ypT0 for an incomplete responder ("T0 is an invalid
# value for T-stage"), even though the RFS equation's reference group is
# labelled ypT0/T1, in the UI, ypT0 means the primary responded completely and
# the patient belongs on the complete-responder branch. Our module accepts ypT0
# because the equation does; the two are not in conflict, but no ypT0 case can
# be captured here, so that corner is covered by the equation only.


def _opener() -> urllib.request.OpenerDirector:
    import http.cookiejar

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent", UA)]
    return op


def _form_build_id(op, html_holder: list) -> str:
    html = _get(op, PAGE)
    html_holder.append(html)
    m = re.search(r'name="form_build_id"\s+value="([^"]+)"', html)
    if not m:
        raise RuntimeError("form_build_id not found, the page layout changed")
    return m.group(1)


def _percentages(html: str) -> dict:
    """Pull the two labelled probabilities out of the rendered result page."""
    i = html.find("nomograms-results-header")
    if i < 0:
        raise RuntimeError("no result block returned (validation error?)")
    seg = html[i : i + 60000]
    out = {}
    for key, label in (
        ("rfs", "Recurrence-Free Probability"),
        ("os", "Overall Survival Probability"),
    ):
        j = seg.find(label)
        if j < 0:
            raise RuntimeError(f"{label!r} missing from result page")
        m = re.search(r'data-value="([\d.]+)"', seg[j : j + 4000])
        if not m:
            raise RuntimeError(f"no percentage after {label!r}")
        out[key] = float(m.group(1))
    return out


def _key(c: dict) -> tuple:
    return (c["age"], c["t_stage"], c["nodes"], c["dtav_gt5"], c["vi"], c["pni"])


def _get(op, req_or_url, tries: int = 5):
    """Open with exponential backoff, the host rate-limits at 429."""
    import urllib.error

    for attempt in range(tries):
        try:
            return op.open(req_or_url, timeout=60).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == tries - 1:
                raise
            wait = 15 * (attempt + 1)
            print(f"    429, backing off {wait}s")
            time.sleep(wait)
    raise AssertionError("unreachable")


def main() -> None:
    op = _opener()
    holder: list = []

    # Resume: keep whatever a previous run already captured.
    rows = []
    if OUT.exists():
        rows = json.loads(OUT.read_text()).get("cases", [])
        print(f"resuming with {len(rows)} case(s) already captured")
    have = {_key(r) for r in rows}

    for k, c in enumerate(CASES):
        if _key(c) in have:
            print(f"[{k + 1:2d}/{len(CASES)}] cached")
            continue
        # Drupal rotates form_build_id on every submission, so re-fetch it.
        build_id = _form_build_id(op, holder)
        fields = {
            "complete_path_response": "False",  # incomplete responders only
            "age": str(c["age"]),
            "t_stage": c["t_stage"],
            "number_of_positive_nodes": str(c["nodes"]),
            "distance_from_the_anal_verge_gt_5cm": str(c["dtav_gt5"]),
            "venous_invasion": str(c["vi"]),
            "perineural_invasion": str(c["pni"]),
            "op": "Calculate",
            "form_build_id": build_id,
            "form_id": "nomograms_calculator_form",
        }
        req = urllib.request.Request(
            ENDPOINT,
            data=urllib.parse.urlencode(fields).encode(),
            headers={
                "Referer": PAGE,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        html = _get(op, req)
        pct = _percentages(html)
        rows.append({**c, "months": 60, **pct})
        print(f"[{k + 1:2d}/{len(CASES)}] {c} -> RFS {pct['rfs']}%  OS {pct['os']}%")
        _save(rows)  # incremental, so a 429 never loses captured work
        time.sleep(3.0)  # be a polite client

    _save(rows)
    print(f"\nwrote {OUT} ({len(rows)} cases)")


def _save(rows: list) -> None:
    OUT.write_text(
        json.dumps(
            {
                "source": ENDPOINT,
                "tool": "MSK rectal post-treatment calculator",
                "supporting_publication": (
                    "Weiser MR et al. JAMA Netw Open. 2021;4(11):e2133457, "
                    "PMCID PMC8576585, cited by the tool itself"
                ),
                "resolution": "whole percent, as displayed by the tool",
                "cases": rows,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
