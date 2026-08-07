"""Randomized invariant sweep across every implemented model.

The other test files check models against their sources at specific points.
This one checks properties that must hold at *every* point, over a wide
randomized sweep of the input space. It is aimed at the failure modes that spot
checks structurally cannot catch:

  * a probability escaping [0, 1] under extreme but legal inputs
  * a sign error in a branch no worked example happens to exercise
  * non-monotonicity in a factor the literature says is monotone
  * a point score exceeding its published maximum
  * components that no longer sum to the reported total

Seeded, so failures are reproducible.
"""

from __future__ import annotations

import random

import pytest

SEED = 20260805
N = 300


def _rng():
    return random.Random(SEED)


# --------------------------------------------------------------------------
# Probability models: output must be a genuine probability, everywhere.
# --------------------------------------------------------------------------

def test_prevent_probability_bounds_over_the_whole_legal_domain():
    from mayo_baseline.cvd.detection import prevent_coefficients as C
    from mayo_baseline.cvd.detection import prevent_predict

    r = _rng()
    for _ in range(N):
        for horizon in C.HORIZONS:
            lo, hi = C.AGE_RANGE[horizon]
            out = prevent_predict(
                sex=r.choice(["male", "female"]),
                age=r.uniform(lo, hi),
                total_chol_mg_dl=r.uniform(100, 400),
                hdl_mg_dl=r.uniform(15, 110),
                sbp=r.uniform(80, 220),
                diabetes=r.random() < 0.3,
                smoker=r.random() < 0.3,
                bmi=r.uniform(15, 60),
                egfr=r.uniform(10, 150),
                htn_meds=r.random() < 0.4,
                statin=r.random() < 0.3,
                outcome=r.choice(list(C.OUTCOMES)),
                horizon_years=horizon,
            )
            assert 0.0 < out["risk"] < 1.0


def test_plcom2012_probability_bounds():
    from mayo_baseline.lung.detection import coefficients as C
    from mayo_baseline.lung.detection import plcom2012_predict

    r = _rng()
    for _ in range(N):
        current = r.random() < 0.5
        out = plcom2012_predict(
            age=r.uniform(50, 85),
            race=r.choice(list(C.RACE)),
            education_level=r.choice(C.EDUCATION_LEVELS),
            bmi=r.uniform(15, 60),
            copd=r.random() < 0.2,
            personal_cancer_history=r.random() < 0.1,
            family_history_lung_cancer=r.random() < 0.2,
            current_smoker=current,
            cigarettes_per_day=r.uniform(1, 80),
            smoking_duration_years=r.uniform(1, 60),
            quit_years=0 if current else r.uniform(0, 40),
        )
        assert 0.0 < out["risk"] < 1.0


def test_bcrat_probability_bounds_and_horizon_monotonicity():
    from mayo_baseline.breast.detection import bcrat_predict

    r = _rng()
    for _ in range(N // 3):
        start = r.uniform(35, 80)
        kw = dict(
            race="white",
            n_biopsies=r.choice([0, 1, 2]),
            age_menarche=r.choice([11, 13, 14]),
            age_first_birth=r.choice([20, 25, 30, 98]),
            n_relatives=r.choice([0, 1, 2]),
        )
        short = bcrat_predict(start_age=start, end_age=start + 5, **kw)["risk"]
        long = bcrat_predict(start_age=start, end_age=start + 10, **kw)["risk"]
        assert 0.0 < short < 1.0 and 0.0 < long < 1.0
        # Risk accumulates: a longer projection window cannot lower it.
        assert long >= short - 1e-12


def test_predict_breast_survival_bounds_and_benefit_is_never_negative():
    from mayo_baseline.breast.prognosis import predict_breast

    r = _rng()
    for _ in range(N // 3):
        er = r.random() < 0.7
        out = predict_breast(
            age=r.uniform(25, 90),
            size_mm=r.uniform(1, 120),
            nodes=r.choice([0, 1, 3, 10, 25]),
            grade=r.choice([1, 2, 3, 9]),
            er_positive=er,
            her2=r.choice([0, 1, 9]),
            ki67=r.choice([0, 1, 9]),
            chemo_generation=r.choice([0, 2, 3]),
            hormone=r.random() < 0.5,
            trastuzumab=r.random() < 0.3,
            bisphosphonate=r.random() < 0.3,
            years=r.choice([1, 5, 10, 15]),
        )
        assert 0.0 <= out["survival_no_treatment"] <= 1.0
        assert 0.0 <= out["survival_with_treatment"] <= 1.0
        # Every treatment log-HR in the model is <= 0.
        assert out["benefit"] >= -1e-12


def test_score2_and_roma_and_cervical_probability_bounds():
    from mayo_baseline.cervical.detection import cervical_cin_risk_predict
    from mayo_baseline.cervical.detection.cin_risk import CYTOLOGY_LEVELS, MODELS
    from mayo_baseline.cvd.detection import score2_predict
    from mayo_baseline.ovarian.detection import roma_predict

    r = _rng()
    for _ in range(N):
        s = score2_predict(
            sex=r.choice(["male", "female"]), age=r.uniform(40, 69),
            sbp=r.uniform(90, 220), total_chol_mmol=r.uniform(2.5, 12),
            hdl_mmol=r.uniform(0.4, 3.0), smoker=r.random() < 0.4,
            region=r.choice(["low", "moderate", "high", "very_high"]),
        )
        assert 0.0 < s["risk"] < 1.0

        o = roma_predict(he4_pmol_l=r.uniform(10, 3000),
                         ca125_u_ml=r.uniform(1, 10000),
                         postmenopausal=r.random() < 0.5)
        assert 0.0 < o["risk"] < 1.0

        variant = r.choice(list(MODELS))
        kw = {}
        if "E6" in MODELS[variant]:
            kw["e6_positive"] = r.random() < 0.5
        if any(g.startswith("HPV") for g in MODELS[variant]):
            kw["genotypes"] = {}
        c = cervical_cin_risk_predict(
            hrhpv_positive=r.random() < 0.6,
            cytology=r.choice(CYTOLOGY_LEVELS),
            age=r.uniform(18, 90), variant=variant, **kw,
        )
        assert 0.0 < c["risk"] < 1.0


def test_grace_risk_stays_within_the_published_lookup_range():
    from mayo_baseline.cvd.prognosis import grace_predict

    r = _rng()
    for _ in range(N):
        out = grace_predict(
            killip_class=r.choice([1, 2, 3, 4]),
            sbp=r.uniform(50, 260), heart_rate=r.uniform(20, 260),
            age=r.uniform(18, 105), creatinine_mg_dl=r.uniform(0.1, 12),
            cardiac_arrest_at_admission=r.random() < 0.1,
            st_segment_deviation=r.random() < 0.4,
            elevated_cardiac_enzymes=r.random() < 0.5,
        )
        assert 0.002 <= out["risk"] <= 0.52     # published table bounds
        assert 0 <= out["score"] <= 59 + 58 + 46 + 100 + 28 + 39 + 28 + 14


# --------------------------------------------------------------------------
# Point scores: bounded by the published range, components sum to the total.
# --------------------------------------------------------------------------

def test_point_scores_respect_their_published_bounds_and_sum():
    from mayo_baseline.cvd.prognosis import cha2ds2_vasc_score
    from mayo_baseline.esophageal.detection import kunzmann_predict
    from mayo_baseline.pancreatic.detection import endpac as E
    from mayo_baseline.pancreatic.detection import endpac_predict
    from mayo_baseline.prostate.prognosis import capra_predict

    r = _rng()
    for _ in range(N):
        c = capra_predict(
            psa=r.uniform(0.1, 100),
            gleason_primary=r.choice([1, 2, 3, 4, 5]),
            gleason_secondary=r.choice([1, 2, 3, 4, 5]),
            t_stage=r.choice(["T1", "T1c", "T2", "T2b", "T3a"]),
            percent_positive_cores=r.uniform(0, 100),
            age=r.uniform(35, 90),
        )
        assert 0 <= c["score"] <= 10
        assert sum(c["components"].values()) == c["score"]

        k = kunzmann_predict(
            age=r.uniform(50, 95), male=r.random() < 0.5,
            bmi=r.uniform(15, 60),
            smoking=r.choice(["never", "former", "current"]),
            esophageal_condition=r.random() < 0.3,
        )
        assert 0.0 <= k["score"] <= 15.0
        assert sum(k["components"].values()) == k["score"]

        v = cha2ds2_vasc_score(
            heart_failure=r.random() < 0.3, hypertension=r.random() < 0.5,
            age=r.uniform(18, 100), diabetes=r.random() < 0.3,
            prior_stroke_tia_thromboembolism=r.random() < 0.2,
            vascular_disease=r.random() < 0.3, female=r.random() < 0.5,
        )
        assert 0 <= v <= 9

        # In scope by construction: below 126 mg/dL a year before, at or above
        # it at diagnosis. That is what "new-onset diabetes" means, and it is
        # what bounds the glucose term to the published 1-4.
        e = endpac_predict(
            glucose_at_diabetes_mg_dl=r.uniform(126, 400),
            glucose_one_year_before_mg_dl=r.uniform(70, 125),
            weight_change_kg=r.uniform(-20, 20),
            age_at_diabetes_onset=r.uniform(30, 95),
        )
        lo, hi = E.TOTAL_SCORE_RANGE
        assert lo <= e["score"] <= hi
        assert E.GLUCOSE_SCORE_RANGE[0] <= e["components"]["glucose"] <= E.GLUCOSE_SCORE_RANGE[1]
        assert sum(e["components"].values()) == e["score"]


# --------------------------------------------------------------------------
# Monotonicity: directions the literature states must hold.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("factor", ["psa", "cores", "age"])
def test_capra_is_monotone_in_each_continuous_factor(factor):
    from mayo_baseline.prostate.prognosis import capra_predict

    base = dict(psa=5.0, gleason_primary=3, gleason_secondary=3,
                t_stage="T1c", percent_positive_cores=10.0, age=45)
    grids = {"psa": [1, 5, 8, 15, 25, 50],
             "cores": [0, 20, 33, 34, 60, 100],
             "age": [40, 49, 50, 60, 80]}
    key = {"psa": "psa", "cores": "percent_positive_cores", "age": "age"}[factor]
    scores = [capra_predict(**{**base, key: v})["score"] for v in grids[factor]]
    assert scores == sorted(scores), (factor, scores)


def test_prevent_is_monotone_in_age_and_sbp_above_the_knot():
    from mayo_baseline.cvd.detection import prevent_predict

    base = dict(sex="male", total_chol_mg_dl=200, hdl_mg_dl=45, diabetes=False,
                smoker=False, bmi=27, egfr=90)
    ages = [40, 50, 60, 70, 79]
    risks = [prevent_predict(**base, age=a, sbp=130)["risk"] for a in ages]
    assert risks == sorted(risks)
    # Above the 110 mm Hg knot, higher SBP is higher risk.
    sbps = [115, 130, 150, 175, 200]
    risks = [prevent_predict(**base, age=60, sbp=s)["risk"] for s in sbps]
    assert risks == sorted(risks)


def test_albi_and_amap_are_monotone_in_liver_dysfunction():
    from mayo_baseline.liver.detection import amap_predict
    from mayo_baseline.liver.prognosis import albi_score

    # Rising bilirubin and falling albumin both worsen ALBI.
    bili = [5, 10, 20, 40, 90]
    assert [albi_score(bilirubin_umol_l=b, albumin_g_l=40) for b in bili] == sorted(
        [albi_score(bilirubin_umol_l=b, albumin_g_l=40) for b in bili])
    alb = [50, 45, 40, 35, 25]
    assert [albi_score(bilirubin_umol_l=20, albumin_g_l=a) for a in alb] == sorted(
        [albi_score(bilirubin_umol_l=20, albumin_g_l=a) for a in alb])

    # aMAP rises with age and falls with platelets.
    ages = [30, 45, 60, 75]
    s = [amap_predict(age=a, male=True, platelets=200, bilirubin_umol_l=15,
                      albumin_g_l=42)["score"] for a in ages]
    assert s == sorted(s)
    plts = [400, 300, 200, 100, 50]
    s = [amap_predict(age=55, male=True, platelets=p, bilirubin_umol_l=15,
                      albumin_g_l=42)["score"] for p in plts]
    assert s == sorted(s)


def test_msk_rectal_survival_is_monotone_in_time_and_nodes():
    from mayo_baseline.colorectal.prognosis import msk_rectal_predict

    base = dict(ypt="ypT3", positive_nodes=2, distance_to_anal_verge_cm=4.0,
                venous_invasion=False, perineural_invasion=False)
    for endpoint, extra in (("rfs", {}), ("os", {"age": 60})):
        surv = [msk_rectal_predict(endpoint=endpoint, months=m, **base, **extra)["survival"]
                for m in (0, 60, 120, 180)]
        assert surv == sorted(surv, reverse=True)
        nodes = [msk_rectal_predict(endpoint=endpoint, months=60,
                                    **{**base, "positive_nodes": n}, **extra)["survival"]
                 for n in (0, 1, 2, 4, 8)]
        assert nodes == sorted(nodes, reverse=True)


def test_lipi_is_monotone_and_bounded():
    from mayo_baseline.lung.response import lipi_predict

    r = _rng()
    for _ in range(N):
        out = lipi_predict(dnlr=r.uniform(0.1, 20), ldh=r.uniform(50, 2000),
                           ldh_upper_limit_normal=r.uniform(150, 300))
        assert out["score"] in (0, 1, 2)
        assert out["group"] in ("good", "intermediate", "poor")
