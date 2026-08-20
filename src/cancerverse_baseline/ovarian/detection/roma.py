"""ROMA — Risk of Ovarian Malignancy Algorithm (HE4 + CA125).

Equation source
---------------
Moore RG, McMeekin DS, Brown AK, et al. "A novel multiple marker bioassay
utilizing HE4 and CA125 for the prediction of ovarian cancer in patients with a
pelvic mass." Gynecol Oncol. 2009;112(1):40-46.

Separate logistic algorithms by menopausal status, quoted verbatim from the
paper's Statistical analysis section:

    Premenopausal:   PI = -12.0 + 2.38*LN(HE4) + 0.0626*LN(CA125)
    Postmenopausal:  PI =  -8.09 + 1.04*LN(HE4) + 0.732*LN(CA125)

    Predicted Probability (PP) = exp(PI) / [1 + exp(PI)]

High risk of malignancy, at 75% specificity in the validation cohort:

    Premenopausal:   PP > 13.1%
    Postmenopausal:  PP > 27.7%

TWO SETS OF CUTOFFS EXIST AND THEY DISAGREE
-------------------------------------------
The coefficients above are not in doubt, the paper, the Abbott/Fujirebio assay
insert and ARUP's test directory all print the same six numbers. The
*thresholds* do not agree:

    source                          premenopausal   postmenopausal
    Moore 2009 (this default)          > 13.1%          > 27.7%
    assay package insert / ARUP        >= 11.4%         >= 29.9%

They cross over: the commercial cutoff is MORE sensitive premenopausally and
LESS sensitive postmenopausally. A premenopausal woman at PP = 12% is low risk
by the paper and high risk by the assay insert.

`cutoff_source` selects between them. The default is `"paper"`, per this
project's rule of reproducing what was published; `"assay_insert"` is what a
clinical laboratory reporting a ROMA result will actually have used.

Two things worth noticing in the coefficients themselves. The premenopausal
model is driven almost entirely by HE4, its CA125 coefficient (0.0626) is
nearly negligible, while postmenopausally CA125 carries real weight (0.732).
That is the model encoding a clinical fact: CA125 is elevated by benign
gynaecological disease common in premenopausal women, so it discriminates
poorly there. Correspondingly the paper reports much weaker premenopausal
sensitivity (67-76%) than postmenopausal (92.3-92.5%).

Assay dependence
----------------
Developed with the Architect CA125II assay (Abbott) and the HE4 EIA assay
(Fujirebio). Units are U/mL for CA125 and pmol/L for HE4. The cut-offs are
assay-specific and do not transfer to other platforms without a bridging study.

Relation to RMI
---------------
[[RMI]] (also implemented here) uses ultrasound morphology x menopausal status x
CA125 and needs no HE4. Meta-analyses generally find ROMA and RMI comparable,
with ROMA marginally ahead on AUC. They are alternatives for the same cell, not
a sequence.
"""

from __future__ import annotations

import math

AXIS = "detection"
MODEL_ID = "roma"

PREMENOPAUSAL = {
    "intercept": -12.0,
    "ln_he4": 2.38,
    "ln_ca125": 0.0626,
    "cutoff": 0.131,
}
POSTMENOPAUSAL = {
    "intercept": -8.09,
    "ln_he4": 1.04,
    "ln_ca125": 0.732,
    "cutoff": 0.277,
}

# Thresholds by source. Coefficients are identical either way; only the
# high-risk cut differs. See the module docstring.
CUTOFFS = {
    "paper": {"premenopausal": 0.131, "postmenopausal": 0.277},
    "assay_insert": {"premenopausal": 0.114, "postmenopausal": 0.299},
}

MODEL_CITATION = (
    "Moore RG, McMeekin DS, Brown AK, et al. Gynecol Oncol. 2009;112(1):40-46 "
    "(ROMA). Architect CA125II + HE4 EIA assays."
)


def predictive_index(
    *, he4_pmol_l: float, ca125_u_ml: float, postmenopausal: bool
) -> float:
    """ROMA predictive index (the logit)."""
    if he4_pmol_l <= 0:
        raise ValueError(f"he4_pmol_l must be > 0, got {he4_pmol_l}")
    if ca125_u_ml <= 0:
        raise ValueError(f"ca125_u_ml must be > 0, got {ca125_u_ml}")
    c = POSTMENOPAUSAL if postmenopausal else PREMENOPAUSAL
    return (
        c["intercept"]
        + c["ln_he4"] * math.log(he4_pmol_l)
        + c["ln_ca125"] * math.log(ca125_u_ml)
    )


def roma_predict(
    *,
    he4_pmol_l: float,
    ca125_u_ml: float,
    postmenopausal: bool,
    cutoff_source: str = "paper",
) -> dict:
    """
    ROMA predicted probability of epithelial ovarian cancer, and risk group.

    HE4 in pmol/L, CA125 in U/mL. Menopausal status selects the algorithm, the
    two are different models, not one model with an indicator.

    `cutoff_source` is "paper" (Moore 2009, the default) or "assay_insert"
    (the commercial package insert / ARUP). The coefficients are the same
    either way; only the high-risk threshold differs, and they disagree in
    opposite directions by menopausal status. See the module docstring.
    """
    if cutoff_source not in CUTOFFS:
        raise ValueError(
            f"cutoff_source must be one of {sorted(CUTOFFS)}, got {cutoff_source!r}"
        )
    pi = predictive_index(
        he4_pmol_l=he4_pmol_l, ca125_u_ml=ca125_u_ml, postmenopausal=postmenopausal
    )
    pp = math.exp(pi) / (1.0 + math.exp(pi))
    stratum = "postmenopausal" if postmenopausal else "premenopausal"
    cutoff = CUTOFFS[cutoff_source][stratum]
    high_risk = pp > cutoff
    return {
        "risk": pp,
        "predictive_index": pi,
        "risk_group": "high" if high_risk else "low",
        "cutoff": cutoff,
        "cutoff_source": cutoff_source,
        "menopausal_status": "postmenopausal" if postmenopausal else "premenopausal",
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "ovarian",
        "citation": MODEL_CITATION,
        "notes": "assay-specific (Architect CA125II, HE4 EIA); cut-offs set at 75% specificity",
    }
