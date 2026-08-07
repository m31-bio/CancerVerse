"""MSK rectal cancer calculator — RFS and OS after chemoradiotherapy + surgery.

Equation source
---------------
Weiser MR, Chou JF, Keshinro A, et al; Colorectal Cancer Disease Management
Team of Memorial Sloan Kettering Cancer Center. "Development and Assessment of
a Clinical Calculator for Estimating the Likelihood of Recurrence and Survival
Among Patients With Locally Advanced Rectal Cancer Treated With Chemotherapy,
Radiotherapy, and Surgery." JAMA Netw Open. 2021;4(11):e2133457.
doi:10.1001/jamanetworkopen.2021.33457 — Supplement 1, eFigure ("Predictive
Equations for Incomplete Responders for RFS (top) and OS (bottom)").

The eFigure is a rendered image, not text; the coefficients below were read
from it and re-read from independent renders at 300 and 600 dpi.

Verified against MSK's own hosted deployment of this model
(mskcc.org/nomograms/rectal/post-treatment, whose "Supporting Publication"
block cites this exact paper): 12 patients, both endpoints, all 24
probabilities match to the tool's 1-point display resolution. See
tests/parity/test_msk_rectal_parity.py.

A published inconsistency you will trip over if you check our work
------------------------------------------------------------------
exp(beta) from the eFigure does NOT reproduce the hazard ratios printed in the
eTable of the same supplement — but only for OS:

    RFS   6/6 terms agree to 3 significant figures
    OS    0/5 agree (T3 1.31 vs 1.48, T4 4.00 vs 3.80, DTAV 0.64 vs 0.69,
                     VI 1.60 vs 1.09, PNI 1.97 vs 2.02)

Both artifacts were re-read at high resolution; both readings are exact, so
this is not a transcription error. The RFS model has no age term and its eTable
has no Age row; the OS model has an age spline and its eTable does. The
article's correction notice (PMC8759003) amends only three collaborator names
and leaves the equations untouched. The parity run above settles which artifact
is the model: the eFigure. Do not "fix" the OS coefficients toward the eTable.

Cox form, with time in MONTHS:

    Prob{T >= t} = S0(t) ** exp(X*beta)

    [c]    = 1 if the subject is in group c, else 0
    (x)_+  = x if x > 0, else 0

Population
----------
**Incomplete pathological responders** only — patients with locally advanced
rectal cancer (stage II/III) who underwent neoadjuvant chemoradiotherapy and
surgery and did NOT achieve a complete pathological response. Complete
responders are handled by a Kaplan-Meier estimate in the source tool, not by
this equation, and this module does not cover them.

A trap worth stating plainly: the two endpoints use DIFFERENT ypT reference
groups. RFS is coded against ypT0/T1 (so T2, T3, T4 each get an indicator);
OS is coded against ypT0/T1/T2 (so only T3 and T4 do). Applying the RFS
coding to the OS model silently misprices every ypT2 patient.

Two more things that look like bugs and are not
-----------------------------------------------
1. **OS can come out BELOW RFS.** Logically RFS <= OS, since every death is
   also an RFS event. But the two endpoints are separate marginal Cox fits and
   only the OS model carries age, so for an older patient the OS model predicts
   heavy mortality while the age-blind RFS model does not follow, and the
   ordering inverts. MSK's own deployed tool does this too — an 80-year-old
   ypT2 with 5 positive nodes, venous and perineural invasion returns RFS 42%
   with OS 15% there and here. Reproduced, not corrected.
2. **ypT0.** MSK's web form rejects ypT0 for an incomplete responder ("T0 is an
   invalid value"), because in its UI ypT0 means the primary responded
   completely and the patient belongs on the complete-responder branch. The
   equation's RFS reference group is nonetheless labelled ypT0/T1, so this
   module accepts ypT0. That corner is covered by the equation alone; no live
   reference value can be captured for it.

Licensing
---------
The equations are published in an open-access JAMA Network Open supplement and
are used here on that basis. MSK's own hosted calculator carries a separate
research-and-education-only, non-commercial disclaimer; this reimplementation
follows the paper, not the hosted tool.
"""

from __future__ import annotations

AXIS = "prognosis"
MODEL_ID = "msk_rectal"

# Baseline survival is published only at these follow-up times, in months.
BASELINE_SURVIVAL = {
    "rfs": {0: 1.000, 60: 0.719, 120: 0.560, 180: 0.320},
    "os": {0: 1.000, 60: 0.854, 120: 0.654, 180: 0.420},
}
SUPPORTED_MONTHS = (0, 60, 120, 180)
ENDPOINTS = ("rfs", "os")

# Restricted-cubic-spline knots, transcribed from the eFigure.
POSLN_KNOTS = (0.0, 1.0, 3.0)
AGE_KNOTS = (36.0, 52.0, 64.0, 78.7)

MODEL_CITATION = (
    "Weiser MR et al. JAMA Netw Open. 2021;4(11):e2133457. "
    "doi:10.1001/jamanetworkopen.2021.33457, Supplement 1 eFigure."
)


def _plus(x: float) -> float:
    """(x)_+ = x if x > 0, else 0."""
    return x if x > 0 else 0.0


def _normalize_ypt(ypt: str) -> str:
    s = ypt.strip().lower().replace("yp", "").replace("p", "", 1) if ypt else ""
    s = s.strip()
    if not s.startswith("t") or s[1:] not in {"0", "1", "2", "3", "4"}:
        raise ValueError(f"ypt must be one of ypT0..ypT4, got {ypt!r}")
    return s


def linear_predictor(
    *,
    endpoint: str,
    ypt: str,
    positive_nodes: int,
    distance_to_anal_verge_cm: float,
    venous_invasion: bool,
    perineural_invasion: bool,
    age: float | None = None,
) -> float:
    """X*beta for one endpoint. `age` is required for OS and unused for RFS."""
    if endpoint not in ENDPOINTS:
        raise ValueError(f"endpoint must be one of {ENDPOINTS}, got {endpoint!r}")
    if positive_nodes < 0:
        raise ValueError(f"positive_nodes must be >= 0, got {positive_nodes}")
    if distance_to_anal_verge_cm < 0:
        raise ValueError(
            f"distance_to_anal_verge_cm must be >= 0, got {distance_to_anal_verge_cm}"
        )

    t = _normalize_ypt(ypt)
    n = float(positive_nodes)
    dtav_ge5 = 1.0 if distance_to_anal_verge_cm >= 5.0 else 0.0
    vi = 1.0 if venous_invasion else 0.0
    pni = 1.0 if perineural_invasion else 0.0

    if endpoint == "rfs":
        # Reference group: ypT0/T1.
        lp = -0.5425329
        lp += 0.3143759 * (t == "t2")
        lp += 0.6630723 * (t == "t3")
        lp += 1.521675 * (t == "t4")
        lp += (
            0.522283 * n
            - 0.05440106 * _plus(n) ** 3
            + 0.08160159 * _plus(n - 1.0) ** 3
            - 0.02720053 * _plus(n - 3.0) ** 3
        )
        lp += -0.3811237 * dtav_ge5 + 0.136099 * vi + 0.6336823 * pni
        return lp

    # OS. Reference group: ypT0/T1/T2 — deliberately different from RFS.
    if age is None:
        raise ValueError("age is required for the OS endpoint")
    if age <= 0:
        raise ValueError(f"age must be > 0, got {age}")
    a = float(age)
    lp = -0.9603734
    lp += (
        0.00535203 * a
        + 2.213425e-5 * _plus(a - 36.0) ** 3
        - 1.059292e-5 * _plus(a - 52.0) ** 3
        - 4.505452e-5 * _plus(a - 64.0) ** 3
        + 3.351319e-5 * _plus(a - 78.7) ** 3
    )
    lp += 0.2726462 * (t == "t3")
    lp += 1.386825 * (t == "t4")
    lp += (
        0.5150229 * n
        - 0.05251174 * _plus(n) ** 3
        + 0.07876761 * _plus(n - 1.0) ** 3
        - 0.02625587 * _plus(n - 3.0) ** 3
    )
    lp += -0.4471371 * dtav_ge5 + 0.470128 * vi + 0.6762158 * pni
    return lp


def msk_rectal_predict(
    *,
    endpoint: str = "rfs",
    months: int = 60,
    ypt: str,
    positive_nodes: int,
    distance_to_anal_verge_cm: float,
    venous_invasion: bool,
    perineural_invasion: bool,
    age: float | None = None,
) -> dict:
    """
    Probability of remaining recurrence-free (`rfs`) or alive (`os`) at
    `months` after surgery, for an incomplete pathological responder.

    `months` must be one of 0 / 60 / 120 / 180 — the only follow-up times for
    which the paper publishes a baseline survival value. Interpolating between
    them would be our invention, so it is refused rather than guessed.
    """
    if months not in SUPPORTED_MONTHS:
        raise ValueError(
            f"months must be one of {SUPPORTED_MONTHS} (the published S0 grid), "
            f"got {months}"
        )
    lp = linear_predictor(
        endpoint=endpoint,
        ypt=ypt,
        positive_nodes=positive_nodes,
        distance_to_anal_verge_cm=distance_to_anal_verge_cm,
        venous_invasion=venous_invasion,
        perineural_invasion=perineural_invasion,
        age=age,
    )
    s0 = BASELINE_SURVIVAL[endpoint][months]
    import math

    survival = s0 ** math.exp(lp)
    return {
        "survival": survival,
        "risk": 1.0 - survival,
        "linear_predictor": lp,
        "baseline_survival": s0,
        "endpoint": endpoint,
        "months": months,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "colorectal",
        "citation": MODEL_CITATION,
        "notes": "incomplete pathological responders only; complete responders "
        "are estimated by Kaplan-Meier in the source tool, not this equation",
    }
