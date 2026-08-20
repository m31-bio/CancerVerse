"""Extract the 18 dutasteride sub-models from riskcalc.org's R source.

    python tests/parity/reference/dutasteride_extract.py

Writes dutasteride_coefficients.json, which
src/cancerverse_baseline/prostate/response/dutasteride.py loads.

Why extract rather than transcribe
----------------------------------
347 coefficients across 18 functions, each a Cox form
``1 - S0 ** exp(score)`` with its own predictor subset, spline knots and
applicability bounds. Hand-copying that many numbers has a defect rate; this
project has already shipped one wrong coefficient (ALBI's -0.0852) from a much
smaller transcription. Machine extraction removes that failure mode, and the
parity test against the same R proves the extraction is faithful.

Source:
  https://github.com/ClevelandClinicQHS/riskcalc-website/blob/main/
      ProstateCancerConsideringDutasteride/server.R
"""

# ---------------------------------------------------------------------------
# LICENCE NOTICE -- THIS FILE IS NOT COVERED BY THIS REPOSITORY'S LICENCE.
#
# The arithmetic below is copied verbatim from
#   https://github.com/ClevelandClinicQHS/riskcalc-website
# which is licensed **PolyForm Noncommercial 1.0.0**, NOT Apache-2.0.
#
# The repository's own LICENSE (Apache-2.0) does not, and cannot, apply to it:
# nobody may relicense someone else's work by putting it in their tree. This
# file may be used only for a noncommercial purpose, which PolyForm defines as
# "any noncommercial purpose" regardless of who is using it.
#
# It is present because this project's use is academic research only. If that
# ever stops being true, this file must come out again, and so must the five
# others listed in NOTICE beside it.
#
# Withheld from the public mirror until 2026-08-18 on the reasoning that a
# company repository could not have a noncommercial purpose. That reasoning
# tested the wrong thing: PolyForm gates on PURPOSE, not on who is using it.
# See docs/THIRD_PARTY_CODE.md and docs/ACADEMIC_USE_LICENSE_REVIEW.md.
# ---------------------------------------------------------------------------


from __future__ import annotations

import base64
import json
import re
import subprocess
from pathlib import Path

REPO = "ClevelandClinicQHS/riskcalc-website"
SRC = "ProstateCancerConsideringDutasteride/server.R"
OUT = Path(__file__).with_name("dutasteride_coefficients.json")

NUM = r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?"


def fetch() -> str:
    got = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{SRC}", "--jq", ".content"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return base64.b64decode(got).decode("utf-8", "replace")


def _bounds_of(body: str) -> tuple[dict, list[str]]:
    cond = body[body.index("if (") : body.index(") {", body.index("if ("))]
    numeric = {
        m.group(2): (float(m.group(1)), float(m.group(3)))
        for m in re.finditer(
            rf"({NUM})\s*<=\s*([A-Z_]+)\s*&&\s*\2\s*<=\s*({NUM})", cond
        )
    }
    return numeric, sorted(set(re.findall(r'([A-Z_]+)\s*!=\s*"Unknown"', cond)))


def parse_function(body: str) -> dict:
    """Pull one `score = ...` expression and its S0 / bounds into data.

    One sub-model has no score at all: `predict.hgpin.dutasteride` returns a
    FIXED 3.838831% to everyone in scope, with no predictors. That is what the
    source says, so it is recorded as a constant rather than forced into the
    Cox shape.
    """
    if "score" not in body:
        m = re.search(rf"round\(\s*({NUM})\s*\*\s*100", body)
        if not m:
            raise ValueError("no score and no constant found")
        numeric, known = _bounds_of(body)
        return {
            "constant_risk": float(m.group(1)),
            "intercept": None,
            "linear": {},
            "splines": [],
            "indicators": [],
            "baseline_survival": None,
            "bounds": numeric,
            "requires_known": known,
        }

    score = body[body.index("score") :]
    score = score[: score.index("\n    if")]
    score = score.split("=", 1)[1]
    score = " ".join(score.split())

    # Split on +/- at parenthesis depth 0 only. A naive split breaks every
    # spline, because `max(AGE - 55, 0)` contains a minus of its own.
    terms, buf, depth, sign = [], "", 0, 1
    for ch in score.strip():
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        # a +/- straight after an exponent marker belongs to the number, not
        # to the expression: 2.0545925e-05 is one coefficient, not two terms
        if ch in "+-" and buf[-1:].lower() == "e" and buf[-2:-1].isdigit():
            buf += ch
            continue
        if depth == 0 and ch in "+-" and buf.strip():
            terms.append((sign, buf.strip()))
            buf, sign = "", 1 if ch == "+" else -1
            continue
        if depth == 0 and ch in "+-" and not buf.strip():
            sign = sign * (1 if ch == "+" else -1)
            continue
        buf += ch
    if buf.strip():
        terms.append((sign, buf.strip()))

    intercept = 0.0
    linear: dict[str, float] = {}
    splines: list[dict] = []
    indicators: list[dict] = []

    for sign, term in terms:
        # spline: c * max(VAR - knot, 0)**3, and the knot-at-zero form the
        # source also uses, c * max(VAR, 0)**3
        m = re.fullmatch(
            rf"({NUM})\s*\*\s*max\(\s*([A-Z_]+)\s*(?:-\s*({NUM})\s*)?,\s*0\s*\)\s*\*\*\s*3",
            term,
        )
        if m:
            splines.append(
                {
                    "var": m.group(2),
                    "knot": float(m.group(3)) if m.group(3) else 0.0,
                    "coef": sign * float(m.group(1)),
                }
            )
            continue
        # indicator: c * (VAR == "level")
        m = re.fullmatch(rf'({NUM})\s*\*\s*\(\s*([A-Z_]+)\s*==\s*"([^"]+)"\s*\)', term)
        if m:
            indicators.append(
                {
                    "var": m.group(2),
                    "level": m.group(3),
                    "coef": sign * float(m.group(1)),
                }
            )
            continue
        # linear: c * VAR
        m = re.fullmatch(rf"({NUM})\s*\*\s*([A-Z_]+)", term)
        if m:
            linear[m.group(2)] = linear.get(m.group(2), 0.0) + sign * float(m.group(1))
            continue
        # bare intercept
        m = re.fullmatch(NUM, term)
        if m:
            intercept += sign * float(term)
            continue
        raise ValueError(f"unparsed term: {term!r}")

    s0 = re.search(rf"1\s*-\s*({NUM})\s*\*\*\s*exp\(score\)", body)
    if not s0:
        raise ValueError("no baseline survival found")

    numeric_bounds, required_known = _bounds_of(body)

    return {
        "constant_risk": None,
        "intercept": intercept,
        "linear": linear,
        "splines": splines,
        "indicators": indicators,
        "baseline_survival": float(s0.group(1)),
        "bounds": numeric_bounds,
        "requires_known": required_known,
    }


def main() -> None:
    src = fetch()
    pattern = re.compile(
        r"predict\.([a-z]+)\.(dutasteride|nodutasteride)\s*<-\s*function\([^)]*\)\s*\{",
        re.M,
    )

    models: dict[str, dict[str, dict]] = {}
    starts = [(m.group(1), m.group(2), m.end()) for m in pattern.finditer(src)]
    for i, (outcome, arm, start) in enumerate(starts):
        end = starts[i + 1][2] if i + 1 < len(starts) else len(src)
        body = src[start:end]
        body = body[: body.rindex("}")]
        models.setdefault(outcome, {})[arm] = parse_function(body)

    n = sum(len(v) for v in models.values())
    coefs = sum(
        1 + len(f["linear"]) + len(f["splines"]) + len(f["indicators"])
        for v in models.values()
        for f in v.values()
    )
    OUT.write_text(
        json.dumps(
            {
                "source": f"https://github.com/{REPO}/blob/main/{SRC}",
                "note": "machine-extracted; faithfulness proven by "
                "tests/parity/test_dutasteride_parity.py against the same R",
                "models": models,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"{len(models)} outcomes x 2 arms = {n} sub-models, {coefs} coefficients")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
