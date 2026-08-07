"""Risk of Malignancy Index (RMI 1-4) — adnexal mass triage.

Not a regression: a hand-computable multiplicative index.

    RMI = U * M * CA-125          (RMI 4: * S)

U = ultrasound score (count of 5 features: multilocular cyst, solid areas,
bilateral lesions, ascites, intra-abdominal metastases), M = menopausal
score, S = tumour-size score (RMI 4 only). The four published variants
disagree on the U/M/S mappings and the cut-off:

    variant   U mapping              M (pre/post)   S           cutoff
    RMI 1     0->0, 1->1, 2-5->3     1 / 3           n/a         200
    RMI 2     0-1->1, 2-5->4         1 / 4           n/a         200
    RMI 3     0-1->1, 2-5->3         1 / 3           n/a         200
    RMI 4     0-1->1, 2-5->4         1 / 4           <7cm 1,     450
                                                       >=7cm 2

Output is an INDEX, not a probability — there is no link function. The only
published interpretation is "above cut-off, refer to gynae-oncology".

Equation source
----------------
Jacobs I, Oram D, Fairbanks J, Turner J, Frost C, Grudzinskas JG. A risk of
malignancy index incorporating CA 125, ultrasound and menopausal status for
the accurate preoperative diagnosis of ovarian cancer. Br J Obstet Gynaecol.
1990;97:922-929. doi:10.1111/j.1471-0528.1990.tb02448.x — RMI 1 U/M scores
reproduced verbatim in Moore RG et al., Gynecol Oncol 2012 (PMC3351260).
RMI 2: Tingulstad S et al. Br J Obstet Gynaecol. 1996;103:826-31. RMI 3:
Tingulstad S et al. Obstet Gynecol. 1999;93:448-52. RMI 4: Yamamoto Y et al.
Eur J Obstet Gynecol Reprod Biol. 2009;144:163-7. All retrieved 2026-08-05.
No coefficient is estimated — every number is a published integer score or
cut-off.

Caveats
-------
RMI 1 sets U=0 when the ultrasound score is 0, forcing the whole index to 0
regardless of CA-125 — the published definition, reproduced faithfully, and
the reason RMI 2/3 exist. CA-125 enters linearly and untransformed, so false
positives cluster wherever CA-125 is raised for reasons unrelated to
malignancy (endometriosis, PID, menstruation, ascites of any cause). RMI is
a diagnostic triage tool for a known mass, not a screening test for
asymptomatic women.
"""

from __future__ import annotations

AXIS = "detection"
MODEL_ID = "rmi"

SIZE_THRESHOLD_CM = 7.0
M_PREMENOPAUSAL = 1


def _u_rmi1(score: int) -> int:
    if score == 0:
        return 0
    if score == 1:
        return 1
    return 3


def _u_two_level(score: int, high: int) -> int:
    return 1 if score <= 1 else high


VARIANTS = {
    "rmi1": {"u": _u_rmi1, "m_post": 3, "size_score": False, "cutoff": 200.0,
             "source": "Jacobs 1990 (U: 0/1/3; M: 1/3; cutoff 200)"},
    "rmi2": {"u": lambda s: _u_two_level(s, 4), "m_post": 4, "size_score": False,
             "cutoff": 200.0, "source": "Tingulstad 1996 (U: 1/4; M: 1/4; cutoff 200)"},
    "rmi3": {"u": lambda s: _u_two_level(s, 3), "m_post": 3, "size_score": False,
             "cutoff": 200.0, "source": "Tingulstad 1999 (U: 1/3; M: 1/3; cutoff 200)"},
    "rmi4": {"u": lambda s: _u_two_level(s, 4), "m_post": 4, "size_score": True,
             "cutoff": 450.0,
             "source": "Yamamoto 2009 (U: 1/4; M: 1/4; S: 1 if <7cm else 2; cutoff 450)"},
}

MODEL_CITATION = (
    "Jacobs I et al. Br J Obstet Gynaecol. 1990;97:922-929. "
    "doi:10.1111/j.1471-0528.1990.tb02448.x (RMI 1); RMI 2 Tingulstad 1996, "
    "RMI 3 Tingulstad 1999, RMI 4 Yamamoto 2009 — see module docstring."
)


def rmi_predict(
    *,
    ultrasound_score: float,
    postmenopausal: bool,
    ca125: float,
    variant: str = "rmi1",
    max_diameter_cm: float | None = None,
) -> dict:
    """
    RMI index and above/below-cutoff call for the given variant.

    Notes
    -----
    ``ultrasound_score`` is the count (0-5) of Jacobs' five morphological
    features. ``max_diameter_cm`` is required for ``variant="rmi4"`` and
    ignored (with a warning) for every other variant.
    """
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {tuple(VARIANTS)}, got {variant!r}")
    if not 0 <= ultrasound_score <= 5:
        raise ValueError(f"ultrasound_score must be 0-5, got {ultrasound_score}")
    if ca125 <= 0:
        raise ValueError(f"ca125 must be > 0, got {ca125}")

    rules = VARIANTS[variant]
    score = int(round(ultrasound_score))
    notes = []
    if score != ultrasound_score:
        notes.append(f"ultrasound_score {ultrasound_score} rounded to {score}")

    u = rules["u"](score)
    m = rules["m_post"] if postmenopausal else M_PREMENOPAUSAL

    s = 1
    if rules["size_score"]:
        if max_diameter_cm is None:
            raise ValueError("variant 'rmi4' requires max_diameter_cm")
        s = 2 if max_diameter_cm >= SIZE_THRESHOLD_CM else 1
    elif max_diameter_cm is not None:
        notes.append(f"max_diameter_cm supplied but {variant} has no size term; ignored")

    index = float(u) * float(m) * float(s) * float(ca125)
    cutoff = float(rules["cutoff"])
    above = index >= cutoff

    return {
        "risk": None,  # index, not a probability
        "index": index,
        "above_cutoff": above,
        "cutoff": cutoff,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "ovarian",
        "variant": variant,
        "components": {"U": u, "M": m, "S": s, "ca125": ca125},
        "interpretation": "likely malignant, refer to gynae-oncology" if above else "likely benign",
        "citation": MODEL_CITATION,
        "notes": "; ".join(notes) if notes else rules["source"],
    }
