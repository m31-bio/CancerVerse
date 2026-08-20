"""Xu 2021 risk score, complete pathological regression after preoperative
chemotherapy in advanced gastric cancer.

Not a regression at prediction time: four pretreatment values are each
dichotomised and given an integer weight, and the sum is the model. The paper
fits a logistic regression to derive the weights and then never uses it again
— "Based on the risk score, we established a prediction model for TRG = 0",
so the score IS the model, not a lossy rendering of one.

    CA19-9  <= 10.90 U/mL   5 points
    CA72-4  <=  3.19 U/mL   4 points
    well differentiated     7 points
    LNmax   >=  1.535 cm    7 points

    total 0-23; > 13 is the high-score group

**Higher score means MORE likely to achieve complete regression.** The paper
states it outright: "The higher the score is, the more likely it indicates
TRG = 0."

The cut-off has no boundary ambiguity, and that is worth knowing
-----------------------------------------------------------------
Four weights of 5, 4, 7 and 7 make only twelve of the twenty-four totals
reachable: 0, 4, 5, 7, 9, 11, 12, 14, 16, 18, 19, 23. **A score of exactly 13
cannot occur.** The published cut-off sits in the gap between 12 and 14, so
the paper's "low-risk (<=13 points) and high-risk (>13 points)" split is
identical to <=12 against >=14, and the usual question of whether a threshold
is inclusive cannot change a single patient's group. ``test_the_cutoff_falls
_in_an_unreachable_gap`` pins this.

Two things about this model will be read backwards if they are not flagged,
and both are flagged in the output rather than left in a docstring.

The lymph-node direction is the surprising one
-----------------------------------------------
A LARGER node scores toward complete response, which inverts the usual reading
of nodal burden. This is deliberate, not a transcription error: Table 3 indexes
the ">=" level, Table 4 assigns it the 7 points, and the Discussion singles it
out: "To our knowledge, this is the first report showing the value of LNmax
for predicting TRG = 0 after PCT in gastric cancer. We speculate that patients
with large regional lymph nodes have strong immunity against infection and
tumor cell invasion ... However, further investigations are needed to identify
the underlying physiological mechanism."

So the authors noticed it, said it was novel, and offered a speculative
mechanism. That is the honest version of a surprising coefficient. It is also
a single-cohort finding resting on 20 events, and it is the first thing that
should be checked if this model ever fails to transport.

"High risk" in the paper means a GOOD outcome
----------------------------------------------
The paper calls scores > 13 the "high-risk TRG group", and that group is the
one likely to achieve complete regression and to survive longer, its 3-year
survival is 76.75% against 53.45%. The label is inverted relative to every
normal use of "high risk". This module therefore does not use it: the groups
are named for what they predict, ``high_likelihood`` and ``low_likelihood``.

Equation source
----------------
Xu W, Ma Q, Wang L, et al. "Prediction Model of Tumor Regression Grade for
Advanced Gastric Cancer After Preoperative Chemotherapy." Front Oncol.
2021;11:607640. doi:10.3389/fonc.2021.607640. PMC8082104, read in full
2026-08-14.

Points from Table 4, "Risk Score of Prediction Model for TRG". The underlying
coefficients are Table 3, "Multivariate analysis: variables correlated with
TRG in the training set" (CA19-9 B=1.725, CA72-4 B=1.511, differentiation
B=2.005, LNmax B=2.073). Cut-offs, the 0-23 range and the 13-point threshold
are all in the Results text. Both tables are machine-readable in PMC; nothing
here was read off a figure, and the paper contains no nomogram figure at all.

The paper does not state the rule that maps the four odds ratios (5.615,
4.531, 7.426, 7.945) onto the four point values (5, 4, 7, 7). It says only
that "a risk score was assigned to each predictor on the basis of the OR
resulting from the logistic regression analysis".

The rule is nevertheless recoverable, by the same trick that settled the
Kunzmann divisor: each published point p constrains a divisor d by
p - 0.5 <= or/d < p + 0.5, and intersecting the four constraints leaves

    d in (1.0593, 1.1425]

which is narrow and non-empty. The natural anchor sits inside it, the
smallest odds ratio over its own points, 4.531 / 4 = 1.13275, and dividing
every odds ratio by that value and rounding to the nearest integer reproduces
all four published points (4.957, 4.000, 6.556, 7.014). So this is very likely
the authors' construction, on the odds-ratio scale where Kunzmann used the
coefficient scale.

This is a reconstruction, not a published rule, and nothing here depends on
it: the points are transcribed from Table 4. It is recorded because an earlier
version of this docstring asserted the opposite, that no consistent divisor
existed, and ``test_the_points_are_re_derivable_from_the_odds_ratios`` is
what disproved it.

What this model does not give you
----------------------------------
A probability. The paper reports the observed rate of complete regression in
each group, 0% below the cut-off and 22.35% above it, and nothing else. The
0% is 0 events in a group, not a probability of zero, and this module refuses
to return it as one. There is no points-to-probability axis to recover: the
paper has no nomogram figure, so the quantity was never estimated.

Caveats
-------
Single centre (Shanghai Ruijin), and the paper's own limitations say so. Its
"external validation group" is 124 patients enrolled prospectively at the SAME
hospital in a later window, prospective temporal validation, not geographic.
That validation is still worth more than its size suggests, because the
regimens changed between the eras (EOX and taxane-containing retrospectively,
SOX and FLOT prospectively), making it a genuine out-of-era test.

The evidence is thin. 30 TRG=0 events retrospectively, 20 of them in training
against four retained predictors, so events per variable is about 5 and the
0.84 training AUC is optimistic on its face. The internal validation AUC of
0.73 rests on 10 events and its CI runs down to 0.55. The prospective AUC of
0.82 rests on 9. No calibration was ever assessed. Univariate screening was
done on all 304 retrospective patients before the split, so the internal
validation set was in view when the predictors were chosen; the prospective
cohort is unaffected.

Scope is narrow and specific: every patient was staged **cT4N+Mx**, serosal
invasion WITH regional nodal metastasis, and received an average of three
cycles of preoperative chemotherapy. The score has never been tested outside
that stage.

Finally, the endpoint is not ypT0N0. TRG = 0 in the Ryan system is complete
regression of the PRIMARY tumour; of the 30 patients with TRG = 0 in the
retrospective cohort, 6 still had positive lymph nodes. Do not read this as
predicting pathological complete response in the ypT0N0 sense.
"""

from __future__ import annotations

AXIS = "response"
MODEL_ID = "xu_gastric_trg_score"

CA19_9_CUTOFF = 10.90     # U/mL, <= scores
CA72_4_CUTOFF = 3.19      # U/mL, <= scores
LNMAX_CUTOFF = 1.535      # cm, short axis on MDCT, >= scores
HIGH_SCORE_THRESHOLD = 13  # strictly greater than

MAX_SCORE = 23

POINTS = {
    "ca19_9": 5,
    "ca72_4": 4,
    "differentiation": 7,
    "lnmax": 7,
}

#: Table 3 multivariate coefficients, kept for provenance. They are NOT used
#: to compute anything, the points are the model, but a reader checking our
#: transcription against the paper needs them beside the points.
TABLE3_COEFFICIENTS = {
    "ca19_9": {"beta": 1.725, "odds_ratio": 5.615, "ci": (1.272, 24.782), "p": 0.023},
    "ca72_4": {"beta": 1.511, "odds_ratio": 4.531, "ci": (1.167, 17.589), "p": 0.029},
    "differentiation": {"beta": 2.005, "odds_ratio": 7.426, "ci": (2.143, 25.725), "p": 0.002},
    "lnmax": {"beta": 2.073, "odds_ratio": 7.945, "ci": (2.085, 30.279), "p": 0.002},
}

#: Observed rates of TRG = 0 in the derivation cohort, per group. These are
#: counts, not calibrated probabilities, and the 0.0 is 0 events rather than
#: an estimate of zero. Reported as `observed_trg0_rate_in_derivation` and
#: never as `risk`.
OBSERVED_TRG0_RATE = {"low_likelihood": 0.0, "high_likelihood": 0.2235}

DISCRIMINATION = {
    "training": {"auc": 0.84, "ci": (0.77, 0.91), "n": 202},
    "internal_validation": {"auc": 0.73, "ci": (0.55, 0.91), "n": 102},
    "prospective_validation": {"auc": 0.82, "ci": (0.71, 0.92), "n": 124},
}

MODEL_CITATION = (
    "Xu W, Ma Q, Wang L, et al. Front Oncol. 2021;11:607640. "
    "doi:10.3389/fonc.2021.607640, points from Table 4, coefficients from "
    "Table 3."
)

_DIFFERENTIATION = {"well", "poor"}


def _differentiation_scores(differentiation: str) -> bool:
    """True when the grade scores its 7 points.

    The paper dichotomises well against poor and states no middle category,
    so "moderate" is rejected rather than silently folded into one side. That
    is a real limitation of the source, and the caller has to own the choice.
    """
    key = str(differentiation).strip().lower()
    if key not in _DIFFERENTIATION:
        raise ValueError(
            f"differentiation must be one of {sorted(_DIFFERENTIATION)}, got "
            f"{differentiation!r}. Xu 2021 Table 3 dichotomises well against "
            f"poor and states no intermediate level, so a moderately "
            f"differentiated tumour cannot be scored without deciding, "
            f"outside this model, which side it falls on."
        )
    return key == "well"


def xu_trg_points(
    *,
    ca19_9_u_ml: float,
    ca72_4_u_ml: float,
    differentiation: str,
    lnmax_cm: float,
) -> dict:
    """The four point assignments and their sum (0-23)."""
    earned = {
        "ca19_9": POINTS["ca19_9"] if ca19_9_u_ml <= CA19_9_CUTOFF else 0,
        "ca72_4": POINTS["ca72_4"] if ca72_4_u_ml <= CA72_4_CUTOFF else 0,
        "differentiation": (
            POINTS["differentiation"] if _differentiation_scores(differentiation) else 0
        ),
        "lnmax": POINTS["lnmax"] if lnmax_cm >= LNMAX_CUTOFF else 0,
    }
    return {"points": earned, "score": sum(earned.values())}


def xu_gastric_trg_score_predict(
    *,
    ca19_9_u_ml: float,
    ca72_4_u_ml: float,
    differentiation: str,
    lnmax_cm: float,
) -> dict:
    """
    Likelihood of complete pathological regression (Ryan TRG = 0) of the
    primary tumour after preoperative chemotherapy in advanced gastric cancer.

    Parameters
    ----------
    ca19_9_u_ml, ca72_4_u_ml
        Pretreatment serum tumour markers, U/mL. LOW values score.
    differentiation
        ``"well"`` or ``"poor"``. The paper states no intermediate level;
        ``"moderate"`` raises rather than being assigned a side.
    lnmax_cm
        Short-axis diameter of the largest regional lymph node on MDCT, cm.
        LARGE nodes score, see the module docstring; this is the paper's
        direction and it is deliberate.

    Notes
    -----
    Returns a score and a group, not a probability. The paper published only
    the observed rate of TRG = 0 in each group (0% and 22.35%) and no
    points-to-probability mapping, so none is available to return.

    Scope: derived entirely in cT4N+Mx patients, serosal invasion with nodal
    metastasis, given an average of three cycles of preoperative chemotherapy,
    at a single centre.
    """
    scored = xu_trg_points(
        ca19_9_u_ml=ca19_9_u_ml,
        ca72_4_u_ml=ca72_4_u_ml,
        differentiation=differentiation,
        lnmax_cm=lnmax_cm,
    )
    score = scored["score"]
    group = "high_likelihood" if score > HIGH_SCORE_THRESHOLD else "low_likelihood"

    notes = [
        "score, not a probability: the paper publishes no points-to-probability "
        "mapping and has no nomogram figure",
        "endpoint is Ryan TRG = 0 of the PRIMARY tumour, not ypT0N0, 6 of the "
        "30 patients with TRG = 0 still had positive nodes",
        "derived only in cT4N+Mx disease at a single centre; validation is "
        "prospective and temporal, not geographic",
    ]
    if scored["points"]["lnmax"]:
        notes.append(
            "the 7 points for a LARGE lymph node are the paper's direction, not "
            "an error, it is a novel single-cohort finding the authors flag as "
            "needing mechanistic confirmation"
        )
    if group == "low_likelihood":
        notes.append(
            "the derivation cohort's 0% for this group is 0 events, not a "
            "probability of zero"
        )

    return {
        "score": score,
        "max_score": MAX_SCORE,
        "points": scored["points"],
        "group": group,
        "threshold": HIGH_SCORE_THRESHOLD,
        "observed_trg0_rate_in_derivation": OBSERVED_TRG0_RATE[group],
        "model_id": MODEL_ID,
        "axis": AXIS,
        "disease": "gastric",
        "interpretation": (
            "higher score means more likely complete regression; "
            f"{'above' if group == 'high_likelihood' else 'at or below'} the "
            f"{HIGH_SCORE_THRESHOLD}-point cut-off"
        ),
        "citation": MODEL_CITATION,
        "notes": "; ".join(notes),
    }
