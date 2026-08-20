"""One-step file replacement, for files something else is reading.

Why this exists
---------------
`Path.write_text(...)` opens the file with `O_TRUNC` and then writes it. Between
those two steps the file on disk is empty or half-written, and anything that
reads it in that window gets a truncated document rather than an error.

That window is small and it is not theoretical here:

* `registry/models.yaml` is the single source of truth, ~420 KB, and *every*
  renderer, test and audit reads it. It has been corrupted mid-write twice in
  this project's history and both times had to be restored from a backup.
* This working tree is edited by more than one process at a time. On
  2026-08-18 a full test run failed once in `test_every_renderer_actually_runs`,
  which shells out to all ten renderers, and passed on every rerun, while the registry was being written seconds earlier. That specific cause
  was never proven, and this module is not offered as proof of it. It removes
  the possibility either way, which is worth more than the diagnosis.

Writing a sibling temp file and `os.replace`-ing it is atomic on POSIX and on
Windows: a reader sees either the whole old file or the whole new one, never a
join between them. The temp file is a sibling rather than in `/tmp` because
`os.replace` is only atomic within one filesystem.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

__all__ = ["write_text_atomically", "write_bytes_atomically"]


def write_bytes_atomically(path: str | Path, data: bytes) -> Path:
    """Replace `path` with `data` in one step. Returns the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # delete=False because the file is renamed rather than closed-and-removed;
    # the finally-block covers the case where the rename never happens.
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            # Without this the rename can land before the contents do, which
            # turns a crash into a zero-length file that looks like a valid one.
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path


def write_text_atomically(
    path: str | Path, text: str, *, encoding: str = "utf-8", newline: str = "\n"
) -> Path:
    """`Path.write_text` with no window in which the file is half-written."""
    return write_bytes_atomically(path, text.replace("\n", newline).encode(encoding))
