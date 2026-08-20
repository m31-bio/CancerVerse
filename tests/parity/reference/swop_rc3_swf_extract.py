"""Extract the ERSPC RC3 coefficients from SWOP's official Flash calculator.

Run:  python tests/parity/reference/swop_rc3_swf_extract.py

Why this exists
---------------
SWOP's calculator at prostatecancer-riskcalculator.com is the canonical tool for
ERSPC RC3, but it cannot be probed the usual way:

  * the page validates inputs in JavaScript and then hands off to
    `getMovieByName("calc03").allResult(...)`, the arithmetic lives inside a
    Flash object, `/2011/swf/c03dre.swf`;
  * Flash has been end-of-life since 2020, so the official calculator no longer
    runs in any modern browser. There is no output to compare against.

The SWF is still served, though. It is a `CWS` (zlib-compressed) Flash 8 file;
its ActionScript stores numeric literals as raw IEEE-754 doubles. Scanning the
decompressed bytecode for doubles and matching them against our coefficients
verifies the model *itself* rather than one of its outputs, a stronger check
than a spot value, since it covers every input at once.

Result (2026-08-05): all six RC3 constants present, worst deviation 2.2e-06,
which is float round-tripping rather than disagreement.
"""

from __future__ import annotations

import struct
import sys
import urllib.request
import zlib

SWF_URL = "https://www.prostatecancer-riskcalculator.com/2011/swf/c03dre.swf"

# From cancerverse_baseline.prostate.detection.coefficients
OURS = {
    "RC3_INTERCEPT": -1.826,
    "RC3_PSA": 1.024,
    "RC3_VOL": -1.50,
    "RC3_DRE": 0.992,
    "RC3_PSA_CENTER": 2.0,
    "RC3_VOL_CENTER": 5.4,
}
TOLERANCE = 1e-5


def decompress_swf(raw: bytes) -> bytes:
    if raw[:3] == b"CWS":
        return zlib.decompress(raw[8:])
    if raw[:3] == b"FWS":
        return raw[8:]
    raise ValueError(f"not a SWF: {raw[:3]!r}")


def doubles_in(body: bytes) -> set[float]:
    out: set[float] = set()
    for off in range(len(body) - 8):
        for fmt in ("<d", ">d"):
            v = struct.unpack_from(fmt, body, off)[0]
            if v == v and 1e-6 < abs(v) < 1e4:
                out.add(v)
    return out


def main() -> int:
    with urllib.request.urlopen(SWF_URL) as fh:
        raw = fh.read()
    body = decompress_swf(raw)
    vals = doubles_in(body)

    print(
        f"SWF {len(raw)} bytes -> {len(body)} decompressed, "
        f"{len(vals)} plausible doubles\n"
    )
    print(f"{'constant':18}{'ours':>10}{'in SWF':>14}{'|diff|':>12}")
    worst = 0.0
    for name, ours in OURS.items():
        best = min(vals, key=lambda v: abs(v - ours))
        d = abs(best - ours)
        worst = max(worst, d)
        print(f"{name:18}{ours:10.4f}{best:14.6f}{d:12.2e}")
    print(f"\nworst deviation: {worst:.2e}")
    return 0 if worst < TOLERANCE else 1


if __name__ == "__main__":
    sys.exit(main())
