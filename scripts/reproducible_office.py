"""Make a generated Office file a function of its inputs, not of the clock.

    from reproducible_office import make_reproducible
    wb.save(path); make_reproducible(path)

Why this exists
---------------
`.xlsx`, `.pptx` and `.docx` are all zip archives, and a zip records the time
each entry was written. Two builds from an unchanged registry therefore differ
in almost every byte, which has one concrete consequence in this repository:
the `generated-files-are-current` pre-commit hook could never pass on them. A
check that cannot pass is one people learn to skip, so the artefacts it was
meant to guard were effectively unguarded.

There is a second clock inside the first. `docProps/core.xml` carries
`dcterms:created` and `dcterms:modified`, and the libraries fill them with the
wall clock at save time. openpyxl lets `created` be pinned before `save()` and
then **overwrites `modified` on the way out**, so that one can only be fixed
after the library has finished, which is what this module does, by patching
the XML during the rewrite rather than trying to persuade the writer.

How the non-reproducibility was nearly missed
---------------------------------------------
The first measurement said four of five decks were fine. They were not: both
builds in each pair had landed inside the same one-second tick, so their entry
timestamps matched by luck. Re-running with a delay across the second boundary
showed four artefacts failing, not one. A reproducibility test that does not
force a clock tick between builds mostly measures how fast the machine is.
`tests/test_reproducible_builds.py` sleeps for that reason.

The fixed instant is deliberately not "now": 1980-01-01 is the zero of the DOS
timestamp format zip uses, so it is the one value that cannot be misread as
information about when the file was built.
"""

from __future__ import annotations

import datetime
import re
import zipfile
from pathlib import Path

#: Zip entry timestamps. DOS format cannot represent anything earlier.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

#: The same instant for `docProps/core.xml`, and for any writer that will
#: accept it before saving.
BUILD_EPOCH = datetime.datetime(1980, 1, 1)

_CORE_DATES = re.compile(
    rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)"
)


def make_reproducible(path: Path | str) -> None:
    """Rewrite an OOXML file so identical inputs give identical bytes.

    Safe to call on `.xlsx`, `.pptx` and `.docx` alike: it only touches entry
    timestamps and the two date fields in `docProps/core.xml`, and leaves every
    other part byte-for-byte as the writing library produced it.
    """
    path = Path(path)
    stamp = BUILD_EPOCH.strftime("%Y-%m-%dT%H:%M:%SZ").encode()

    with zipfile.ZipFile(path) as zin:
        items = [(i, zin.read(i.filename)) for i in zin.infolist()]

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in items:
            if info.filename == "docProps/core.xml":
                data = _CORE_DATES.sub(lambda m: m.group(1) + stamp + m.group(2), data)
            fixed = zipfile.ZipInfo(info.filename, date_time=ZIP_EPOCH)
            fixed.compress_type = info.compress_type
            fixed.external_attr = info.external_attr
            zout.writestr(fixed, data)
