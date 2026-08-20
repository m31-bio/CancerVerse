"""Generated files must never be readable in a half-written state.

Why this file exists
--------------------
`Path.write_text` truncates and then writes. Between those two steps the file
on disk is a fragment. That is fine in a repo one person builds serially, and
this is not one: `registry/models.yaml` is ~420 KB and every renderer, test and
audit reads it, the working tree gets edited by more than one process at a
time, and the registry has been corrupted mid-write twice.

The window is small enough to be easy to dismiss, so the first test below
measures it rather than arguing about it.
"""

from __future__ import annotations

import re
import tempfile
import threading
from pathlib import Path

import pytest

from cancerverse_baseline.reporting.atomic import (
    write_bytes_atomically,
    write_text_atomically,
)

ROOT = Path(__file__).resolve().parents[1]


def _read_states(target: Path, old: str, new: str, writer, iterations: int, readers: int):
    """Hammer `target` with `writer` while reading it, and report what was seen."""
    write_text_atomically(target, old)
    stop, seen, lock = threading.Event(), set(), threading.Lock()

    def read_loop():
        while not stop.is_set():
            try:
                text = target.read_text()
            except FileNotFoundError:
                with lock:
                    seen.add("MISSING")
                continue
            state = "old" if text == old else ("new" if text == new else "TORN")
            with lock:
                seen.add(state)

    threads = [threading.Thread(target=read_loop) for _ in range(readers)]
    for t in threads:
        t.start()
    try:
        for _ in range(iterations):
            write_text_atomically(target, old)  # reset atomically, so only
            writer()                            # the call under test can tear
    finally:
        stop.set()
        for t in threads:
            t.join()
    return seen


def test_a_concurrent_reader_never_sees_a_partial_document():
    """The guarantee, stated as an experiment rather than as a claim.

    Only the atomic writer is asserted on. The naive writer's tearing is
    *observed* in the same harness (see the docstring of this module and the
    2026-08-18 run, which saw TORN on the plain path and never on this one),
    but asserting that a race reliably loses would make this test flaky in the
    one direction that teaches nothing.
    """
    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / "doc.txt"
        old, new = "old\n", "x" * 4_000_000 + "\nEND\n"
        seen = _read_states(target, old, new,
                            lambda: write_text_atomically(target, new),
                            iterations=25, readers=4)
    assert not ({"TORN", "MISSING"} & seen), (
        f"a reader saw {sorted(seen)}, write_text_atomically left a window in "
        f"which the file was neither the old document nor the new one"
    )


def test_the_temp_file_is_cleaned_up_when_the_write_fails():
    """A failed write must not leave a `.name.xxxx.tmp` beside the real file."""
    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / "doc.txt"
        write_text_atomically(target, "original\n")

        class Exploding:
            """Fails at the moment the bytes are handed to the file object.

            Subclassing `bytes` and raising from `__len__` does not work,
            `BufferedWriter.write` never calls it, and a test that cannot
            fail proves nothing, so the failure is injected where the write
            actually touches the object.
            """

            def __buffer__(self, flags):
                raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            write_bytes_atomically(target, Exploding())

        assert target.read_text() == "original\n", "the old document was damaged"
        leftovers = [p.name for p in Path(d).iterdir() if p.name != "doc.txt"]
        assert not leftovers, f"temp files left behind: {leftovers}"


def test_no_renderer_writes_text_the_unsafe_way():
    """The guard that keeps this from regressing one new script at a time.

    Every `scripts/build_*.py` that emits text goes through the atomic writer.
    A renderer added later will fail here rather than quietly reintroducing the
    window, which is how it got in: nobody chose `write_text`, it was simply
    the obvious call.
    """
    offenders = []
    for script in sorted((ROOT / "scripts").glob("build_*.py")):
        for i, line in enumerate(script.read_text().splitlines(), 1):
            if re.search(r"\.write_text\(", line) and not line.lstrip().startswith("#"):
                offenders.append(f"{script.name}:{i}: {line.strip()[:90]}")
    assert not offenders, (
        "these renderers write text non-atomically; use "
        "cancerverse_baseline.reporting.atomic.write_text_atomically instead:\n  "
        + "\n  ".join(offenders)
    )
