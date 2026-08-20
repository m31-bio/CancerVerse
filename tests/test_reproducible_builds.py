"""Every generated Office file must be a function of the registry, not the clock.

`.xlsx`, `.pptx` and `.docx` are zip archives, and a zip stores the time each
entry was written. Left alone, two builds from an unchanged registry differ in
almost every byte, which had one concrete cost here: the
`generated-files-are-current` pre-commit hook could never pass on them, so it
failed on every run, and a check that cannot pass is one people learn to skip.

`scripts/reproducible_office.py` pins the three clocks involved (entry times,
and `created`/`modified` in `docProps/core.xml`). This test is what stops that
silently regressing the next time a builder is added or rewritten.

**The sleep is the point of the test, not an accident.** The first attempt to
measure this reported four of five artefacts as reproducible. They were not:
each pair of builds had landed inside the same one-second tick, so their entry
timestamps matched by luck. Forcing a tick between builds turned four passes
into four failures. A version of this test without the delay would mostly
measure how fast the machine is, and would go green on a broken build.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: (builder script, artefact it writes). Every generated binary in the repo.
ARTEFACTS = [
    ("build_model_spreadsheet.py", "docs/MODEL_SPREADSHEET.xlsx"),
    ("build_phase2_tables.py", "docs/Phase2_a_Evaluation_Metrics.docx"),
    ("build_phase2_tables.py", "docs/Phase2_b_Baseline_Models.docx"),
    ("build_baseline_review_slides.py", "slides/baseline-models-review.pptx"),
    ("build_license_audit_slide.py", "slides/license-academic-use-2026-08-17.pptx"),
    ("build_licensing_slide.py", "slides/licensing-review-2026-08-07.pptx"),
    ("build_standup_slides.py", "slides/ziqi-2026-08-05.pptx"),
]

#: Long enough to cross a one-second boundary with margin. Without it this
#: whole file is theatre, see the module docstring.
TICK = 1.2


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _build(script: str) -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )
    assert r.returncode == 0, f"{script} failed:\n{(r.stderr or r.stdout)[-600:]}"


@pytest.mark.slow
@pytest.mark.parametrize(
    "script,artefact", ARTEFACTS, ids=[a.split("/")[-1] for _, a in ARTEFACTS]
)
def test_generated_office_files_are_byte_reproducible(script, artefact):
    out = ROOT / artefact
    if not out.exists():
        pytest.skip(f"{artefact} not present")

    _build(script)
    first = _sha(out)
    time.sleep(TICK)
    _build(script)
    second = _sha(out)

    assert first == second, (
        f"{artefact} differs between two builds of the same registry.\n"
        f"  {first[:16]} then {second[:16]}\n"
        "An OOXML file carries three clocks: the zip entry times, and "
        "created/modified in docProps/core.xml. Route the save through "
        "scripts/reproducible_office.make_reproducible(), which pins all three."
    )


def test_every_office_builder_routes_through_the_helper():
    """The reproducibility fix is one call, which makes it easy to forget in a
    new builder. This fails when a script writes an OOXML file without pinning
    its clocks, rather than waiting for the hash test to catch it later.
    """
    missing = []
    for script, artefact in ARTEFACTS:
        path = ROOT / "scripts" / script
        # Some builders are private and absent from the published repository --
        # build_phase2_tables.py answers a partner's questionnaire and is in
        # PRIVATE_SCRIPTS. Reading it unconditionally raised FileNotFoundError
        # in a clone of the public repo rather than checking what is there.
        if not path.exists():
            continue
        src = path.read_text()
        if "make_reproducible" not in src:
            missing.append(f"{script} (writes {artefact})")
    assert not missing, (
        "these builders write an Office file without pinning its clocks:\n  "
        + "\n  ".join(sorted(set(missing)))
    )
