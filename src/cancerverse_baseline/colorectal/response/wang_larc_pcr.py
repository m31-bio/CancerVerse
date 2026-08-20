"""Wang 2024 dynamic nomogram, pathological complete response (pCR) after
neoadjuvant chemoradiotherapy in locally advanced rectal cancer.

Equation source
---------------
Wang G, Li J, Huang Y, Guo Y. "A dynamic nomogram for predicting pathologic
complete response to neoadjuvant chemotherapy in locally advanced rectal
cancer." Cancer Med. 2024;13(11):e7251. doi:10.1002/cam4.7251. PMID 38819440,
open access at PMC11141331.

**The paper alone is not sufficient to compute a probability, and that is the
single most important thing to know about this model.** What the article
publishes is:

  * Table 4, univariable and multivariable odds ratios (printed as "HR"),
    six multivariable terms, no intercept row and no constant anywhere.
  * A sentence in Results 3.3 giving the nomogram's *points* formula:
    "22.0 x Pre-CRT N stage + 15.0 x Pre-CRT T stage + 70.0 x Pre-CRT MRI_EMVI
    + 55.0 x Total neoadjuvant therapy + 100 x Histopathology + 3.85 x
    Pre-CRT CEA".
  * Figure 3A, the nomogram, in which the points-to-probability axis exists
    only as a drawn scale.

Points rank patients; they do not state a probability. The data-availability
statement is "All data obtained or analyzed during this work are included
within the article", and there is no supplementary file, no erratum, and no
GitHub/CRAN release of the app. So the intercept, the one constant that turns
the ranking into a probability, is published nowhere in the literature.

Where the numbers below actually came from
------------------------------------------
The authors deployed the model as an R/Shiny "dynamic nomogram" (built with
the `DynNom` package) at

    https://pcrpredict.shinyapps.io/LARC2/

`DynNom` ships a **"Model Summary" tab** that prints the fitted object with R's
own `print` method. For an `rms::lrm` fit that output is the complete
coefficient table, intercept included. The app was driven directly over its
SockJS/Shiny websocket on 2026-08-14 and returned:

    lrm(formula = pCR ~ Pre_CRT_N_stage + Pre_CRT_T_stage + Pre_CRT_MRI_EMVI +
        Total_neoadjuvant_therapy + Histopathology + Pre_CRT_CEA,
        data = data, x = T, y = T, maxit = 5000)

    Obs 1579   (0: 1229, 1: 350)   d.f. 9   C 0.737   Brier 0.151

with the ten coefficients transcribed verbatim into `COEF` below. This is
`EXTRACTION.md` Route A, not Route B, the deployed tool handed over the whole
model rather than one output per request, so the model is verified everywhere
and not just at the probed points. The captured text is committed at
tests/parity/reference/wang_larc_pcr_model_summary.txt.

Three independent checks that this is the paper's model
-------------------------------------------------------
  * `Obs 1579` is exactly the paper's training cohort, split 1229/350, the
    paper says 350 (22.2%) of 1579 achieved pCR.
  * `C 0.737` rounds to the published C-index of 0.73 (95% CI 0.70-0.75).
  * The six predictors and their level names match Table 4 term for term.

Form
----
    logit(P(pCR)) = -0.0131
                    + N-stage term          (reference cN0)
                    + T-stage term          (reference cT2)
                    - 1.1061 * [MRI EMVI positive]
                    + 0.7642 * [total neoadjuvant therapy given]
                    - 1.4323 * [signet-ring / mucinous histology]
                    - 0.0584 * CEA in ng/mL

    P(pCR) = 1 / (1 + exp(-logit))

WHERE THE DEPLOYED MODEL DIFFERS FROM TABLE 4. READ THIS BEFORE COMPARING
--------------------------------------------------------------------------
Table 4 reports T stage and N stage as a **single ordinal odds ratio each**
(0.793 and 0.727 "per level"). The deployed model fits them as **unordered
factors**, spending 3 degrees of freedom on T and 2 on N. That is why d.f. is
9 rather than 6. Both fits are of the same cohort and the deployed one is the
one the nomogram and the calculator use, so it is the one implemented here.

Consequently exp(beta) here will NOT reproduce Table 4 for T and N, and only
approximately reproduces it for the other four:

    CEA          exp(-0.0584) = 0.943   Table 4: 0.944   agrees
    histology    exp( 1.4323) = 4.19    Table 4: 4.608   close, not equal
    MRI EMVI     exp(-1.1061) = 0.331   Table 4: 0.352   close, not equal
    TNT          exp( 0.7642) = 2.15    Table 4: 2.264   close, not equal

The residual gap is the ordinal-versus-factor coding of T and N changing the
other four estimates. Do not "correct" the coefficients below toward Table 4;
Table 4 is a different fit of the same data and cannot produce a probability
at all, because it has no intercept.

Four things that look like bugs and are not
-------------------------------------------
1. **T stage is NOT monotone, and cT2 is the reference.** The fitted log-odds
   relative to cT2 are cT1 +1.3364, cT3 +0.5773, cT4 +0.0587. So the model
   says a cT3 tumour is *more* likely to achieve pCR than a cT2 one, and cT4
   is barely different from cT2. Clinically that ordering is backwards, and
   the paper papers over it by presenting T stage as a clean ordinal 15.0
   points per level. Only cT3 reaches significance (p 0.0266); cT4 is p 0.836
   on 137 patients' worth of standard error. This module reproduces the fit,
   not the tidy story about it.

2. **The cT1 level is literally named `cTcT1` in the source data**, a "cT"
   prefix applied twice when the dataset was built. It is the cT1 level; the
   app's own dropdown shows the mangled string. This module accepts `cT1` and
   normalises to it, and the parity fixture stores the raw app string.

3. **The CEA coefficient is negative while its points term is positive.** The
   paper's points sentence reads "+ 3.85 x Pre-CR CEA (>= 24 = 0)", i.e. the
   points axis is *reversed*, 24 ng/mL scores zero points and 0 ng/mL scores
   the most. The regression coefficient is -0.0584 per ng/mL. Both say the
   same thing: more CEA, less pCR. Feeding CEA into a "+3.85 per ng/mL" term
   without the reversal inverts the effect.

4. **The intercept is statistically indistinguishable from zero** (-0.0131,
   SE 0.2588, p 0.96). It is still required: it fixes the reference patient
   (cN0, cT2, EMVI-negative, no TNT, adenocarcinoma, CEA 0 ng/mL) at
   P(pCR) = 0.497, and every other prediction hangs off that. A model with no
   intercept is not the same model with a small one.

Scope and bounds
----------------
Locally advanced rectal cancer, staged before chemoradiotherapy, in patients
who go on to complete nCRT and surgery. Development was two Chinese centres
(Union Hospital n=1579 training; Zhangzhou Hospital n=246 external
validation); external C-index 0.78 (0.72-0.83).

CEA is bounded to 0-24 ng/mL because that is the range the authors' own
calculator accepts (`data-min="0" data-max="24"` on its slider) and because
the paper's points formula explicitly floors at ">= 24". A linear logit term
extrapolated past the fitted range is our invention, so values outside are
refused rather than guessed.

Licensing
---------
The article is open access (CC BY). The coefficients were read from the
authors' own freely-published calculator, which prints them itself; nothing
here is reverse-engineered from a proprietary artifact.
"""

from __future__ import annotations

import math
import re

AXIS = "response"
MODEL_ID = "wang_larc_pcr"

MODEL_CITATION = (
    "Wang G, Li J, Huang Y, Guo Y. Cancer Med. 2024;13(11):e7251. "
    "doi:10.1002/cam4.7251"
)

#: The deployed calculator, whose "Model Summary" tab is the equation source.
CALCULATOR_URL = "https://pcrpredict.shinyapps.io/LARC2/"

#: Date the coefficients were read out of that calculator. The app is a live
#: artifact; pin and date anything taken from one (docs/CONVENTIONS.md).
COEFFICIENTS_READ = "2026-08-14"

#: Verbatim from `rms::lrm` as printed by the app, to the 4 decimal places
#: that `print.lrm` shows. Keys mirror the R level names exactly.
COEF = {
    "Intercept": -0.0131,
    "Pre_CRT_N_stage=cN1": -0.4513,
    "Pre_CRT_N_stage=cN2": -0.6596,
    "Pre_CRT_T_stage=cT3": 0.5773,
    "Pre_CRT_T_stage=cT4": 0.0587,
    "Pre_CRT_T_stage=cTcT1": 1.3364,
    "Pre_CRT_MRI_EMVI=Positive": -1.1061,
    "Total_neoadjuvant_therapy=Yes": 0.7642,
    "Histopathology=Signet-ring cell carcinoma/Mucinous adenocarcinoma": -1.4323,
    "Pre_CRT_CEA": -0.0584,
}

#: Levels that carry no coefficient because they ARE the reference. Stating
#: them explicitly is the point: cT2 being the T reference is not guessable
#: from the paper, which presents T stage as an ordinal score.
REFERENCE_LEVELS = {
    "n_stage": "cN0",
    "t_stage": "cT2",
    "mri_emvi": "negative",
    "total_neoadjuvant_therapy": "no",
    "histopathology": "adenocarcinoma",
}

N_STAGES = ("cN0", "cN1", "cN2")
T_STAGES = ("cT1", "cT2", "cT3", "cT4")
HISTOLOGIES = ("adenocarcinoma", "signet_ring_mucinous")

#: The calculator's own slider bounds, and the paper's ">= 24" floor.
CEA_MIN_NG_ML = 0.0
CEA_MAX_NG_ML = 24.0

#: R's mangled name for the cT1 level (see docstring note 2).
_T_LEVEL_IN_R = {"cT1": "cTcT1", "cT2": "cT2", "cT3": "cT3", "cT4": "cT4"}


def _squash(value: str) -> str:
    return str(value).strip().lower().replace("-", "").replace(" ", "")


def _normalize_n_stage(value: str) -> str:
    m = re.fullmatch(r"c?n([0-2])", _squash(value))
    if not m:
        raise ValueError(f"n_stage must be one of {N_STAGES}, got {value!r}")
    return "cN" + m.group(1)


def _normalize_t_stage(value: str) -> str:
    # `(?:c?t)+` tolerates the source data's doubled prefix, e.g. "cTcT1",
    # alongside the ordinary "cT1" and bare "T1".
    m = re.fullmatch(r"(?:c?t)+([1-4])", _squash(value))
    if not m:
        raise ValueError(f"t_stage must be one of {T_STAGES}, got {value!r}")
    return "cT" + m.group(1)


def _normalize_histopathology(value: str) -> str:
    s = str(value).strip().lower()
    if s.startswith("adeno") and "mucin" not in s and "signet" not in s:
        return "adenocarcinoma"
    if "signet" in s or "mucin" in s:
        return "signet_ring_mucinous"
    raise ValueError(f"histopathology must be one of {HISTOLOGIES}, got {value!r}")


def linear_predictor(
    *,
    n_stage: str,
    t_stage: str,
    mri_emvi_positive: bool,
    total_neoadjuvant_therapy: bool,
    histopathology: str,
    cea_ng_ml: float,
) -> float:
    """logit(P(pCR)) for one patient, staged BEFORE chemoradiotherapy.

    Every argument is a pre-CRT value. Feeding post-treatment (yp) staging in
    here is a different model and a different question.
    """
    n = _normalize_n_stage(n_stage)
    t = _normalize_t_stage(t_stage)
    histology = _normalize_histopathology(histopathology)

    cea = float(cea_ng_ml)
    if not CEA_MIN_NG_ML <= cea <= CEA_MAX_NG_ML:
        raise ValueError(
            f"cea_ng_ml must be within the fitted/deployed range "
            f"[{CEA_MIN_NG_ML}, {CEA_MAX_NG_ML}] ng/mL, got {cea}. The linear "
            f"logit term is not extrapolated past it."
        )

    lp = COEF["Intercept"]

    # N stage, reference cN0 (carries no term).
    if n != REFERENCE_LEVELS["n_stage"]:
        lp += COEF[f"Pre_CRT_N_stage={n}"]

    # T stage, reference cT2. NOT cT1, and the effect is not monotone.
    if t != REFERENCE_LEVELS["t_stage"]:
        lp += COEF[f"Pre_CRT_T_stage={_T_LEVEL_IN_R[t]}"]

    if mri_emvi_positive:
        lp += COEF["Pre_CRT_MRI_EMVI=Positive"]
    if total_neoadjuvant_therapy:
        lp += COEF["Total_neoadjuvant_therapy=Yes"]
    if histology == "signet_ring_mucinous":
        lp += COEF[
            "Histopathology=Signet-ring cell carcinoma/Mucinous adenocarcinoma"
        ]

    # Continuous, per ng/mL, and NEGATIVE: more CEA means less pCR.
    lp += COEF["Pre_CRT_CEA"] * cea
    return lp


def wang_larc_pcr_predict(
    *,
    n_stage: str,
    t_stage: str,
    mri_emvi_positive: bool,
    total_neoadjuvant_therapy: bool,
    histopathology: str,
    cea_ng_ml: float,
) -> dict:
    """
    Probability of pathological complete response after neoadjuvant
    chemoradiotherapy for locally advanced rectal cancer.

    Note the direction: `risk` here is the probability of a GOOD outcome. The
    repository's model API names the primary scalar `risk` regardless, so a
    high number is a favourable prediction for this model and `p_pcr` is
    provided under its own name to make that unambiguous at the call site.
    """
    lp = linear_predictor(
        n_stage=n_stage,
        t_stage=t_stage,
        mri_emvi_positive=mri_emvi_positive,
        total_neoadjuvant_therapy=total_neoadjuvant_therapy,
        histopathology=histopathology,
        cea_ng_ml=cea_ng_ml,
    )
    p = 1.0 / (1.0 + math.exp(-lp))
    return {
        "risk": p,
        "p_pcr": p,
        "linear_predictor": lp,
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "colorectal",
        "citation": MODEL_CITATION,
        "notes": "probability of a GOOD outcome (pathological complete "
        "response), so higher is better. Pre-CRT staging only. Intercept and "
        "the categorical coding are not in the paper; they were read from the "
        f"authors' own calculator ({CALCULATOR_URL}) on {COEFFICIENTS_READ}.",
    }
