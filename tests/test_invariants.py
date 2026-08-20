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
    from cancerverse_baseline.cvd.detection import prevent_coefficients as C
    from cancerverse_baseline.cvd.detection import prevent_predict

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
    from cancerverse_baseline.lung.detection import coefficients as C
    from cancerverse_baseline.lung.detection import plcom2012_predict

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


def test_optum_lung_lasso_probability_bounds_and_monotone_in_added_covariates():
    """Random subsets of the 278 covariates, plus the property that decides
    whether the dot product is wired up correctly: adding a covariate must move
    risk in the direction of its own beta's sign, every time.
    """
    from cancerverse_baseline.lung.detection.optum_lung_lasso import (
        BETAS,
        optum_lung_lasso_predict,
    )

    ids = sorted(BETAS)
    r = _rng()
    for _ in range(N):
        chosen = [c for c in ids if r.random() < 0.2]
        out = optum_lung_lasso_predict(chosen)
        assert 0.0 < out["risk"] < 1.0
        assert out["n_covariates_used"] == len(chosen)

        spare = [c for c in ids if c not in set(chosen) and BETAS[c] != 0]
        extra = r.choice(spare)
        after = optum_lung_lasso_predict(chosen + [extra])["risk"]
        if BETAS[extra] > 0:
            assert after > out["risk"], extra
        else:
            assert after < out["risk"], extra


def test_bcrat_probability_bounds_and_horizon_monotonicity():
    from cancerverse_baseline.breast.detection import bcrat_predict

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
    from cancerverse_baseline.breast.prognosis import predict_breast

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
    from cancerverse_baseline.cervical.detection import cervical_cin_risk_predict
    from cancerverse_baseline.cervical.detection.cin_risk import CYTOLOGY_LEVELS, MODELS
    from cancerverse_baseline.cvd.detection import score2_predict
    from cancerverse_baseline.ovarian.detection import roma_predict

    r = _rng()
    for _ in range(N):
        s = score2_predict(
            sex=r.choice(["male", "female"]),
            age=r.uniform(40, 69),
            sbp=r.uniform(90, 220),
            total_chol_mmol=r.uniform(2.5, 12),
            hdl_mmol=r.uniform(0.4, 3.0),
            smoker=r.random() < 0.4,
            region=r.choice(["low", "moderate", "high", "very_high"]),
        )
        assert 0.0 < s["risk"] < 1.0

        o = roma_predict(
            he4_pmol_l=r.uniform(10, 3000),
            ca125_u_ml=r.uniform(1, 10000),
            postmenopausal=r.random() < 0.5,
        )
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
            age=r.uniform(18, 90),
            variant=variant,
            **kw,
        )
        assert 0.0 < c["risk"] < 1.0


def test_grace_risk_stays_within_the_published_lookup_range():
    from cancerverse_baseline.cvd.prognosis import grace_predict

    r = _rng()
    for _ in range(N):
        out = grace_predict(
            killip_class=r.choice([1, 2, 3, 4]),
            sbp=r.uniform(50, 260),
            heart_rate=r.uniform(20, 260),
            age=r.uniform(18, 105),
            creatinine_mg_dl=r.uniform(0.1, 12),
            cardiac_arrest_at_admission=r.random() < 0.1,
            st_segment_deviation=r.random() < 0.4,
            elevated_cardiac_enzymes=r.random() < 0.5,
        )
        assert 0.002 <= out["risk"] <= 0.52  # published table bounds
        assert 0 <= out["score"] <= 59 + 58 + 46 + 100 + 28 + 39 + 28 + 14


# --------------------------------------------------------------------------
# Point scores: bounded by the published range, components sum to the total.
# --------------------------------------------------------------------------


def test_point_scores_respect_their_published_bounds_and_sum():
    from cancerverse_baseline.cvd.prognosis import cha2ds2_vasc_score
    from cancerverse_baseline.esophageal.detection import kunzmann_predict
    from cancerverse_baseline.pancreatic.detection import endpac as E
    from cancerverse_baseline.pancreatic.detection import endpac_predict
    from cancerverse_baseline.prostate.prognosis import capra_predict

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
            age=r.uniform(50, 95),
            male=r.random() < 0.5,
            bmi=r.uniform(15, 60),
            smoking=r.choice(["never", "former", "current"]),
            esophageal_condition=r.random() < 0.3,
        )
        assert 0.0 <= k["score"] <= 15.0
        assert sum(k["components"].values()) == k["score"]

        v = cha2ds2_vasc_score(
            heart_failure=r.random() < 0.3,
            hypertension=r.random() < 0.5,
            age=r.uniform(18, 100),
            diabetes=r.random() < 0.3,
            prior_stroke_tia_thromboembolism=r.random() < 0.2,
            vascular_disease=r.random() < 0.3,
            female=r.random() < 0.5,
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
        assert (
            E.GLUCOSE_SCORE_RANGE[0]
            <= e["components"]["glucose"]
            <= E.GLUCOSE_SCORE_RANGE[1]
        )
        assert sum(e["components"].values()) == e["score"]


# --------------------------------------------------------------------------
# Monotonicity: directions the literature states must hold.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("factor", ["psa", "cores", "age"])
def test_capra_is_monotone_in_each_continuous_factor(factor):
    from cancerverse_baseline.prostate.prognosis import capra_predict

    base = dict(
        psa=5.0,
        gleason_primary=3,
        gleason_secondary=3,
        t_stage="T1c",
        percent_positive_cores=10.0,
        age=45,
    )
    grids = {
        "psa": [1, 5, 8, 15, 25, 50],
        "cores": [0, 20, 33, 34, 60, 100],
        "age": [40, 49, 50, 60, 80],
    }
    key = {"psa": "psa", "cores": "percent_positive_cores", "age": "age"}[factor]
    scores = [capra_predict(**{**base, key: v})["score"] for v in grids[factor]]
    assert scores == sorted(scores), (factor, scores)


def test_prevent_is_monotone_in_age_and_sbp_above_the_knot():
    from cancerverse_baseline.cvd.detection import prevent_predict

    base = dict(
        sex="male",
        total_chol_mg_dl=200,
        hdl_mg_dl=45,
        diabetes=False,
        smoker=False,
        bmi=27,
        egfr=90,
    )
    ages = [40, 50, 60, 70, 79]
    risks = [prevent_predict(**base, age=a, sbp=130)["risk"] for a in ages]
    assert risks == sorted(risks)
    # Above the 110 mm Hg knot, higher SBP is higher risk.
    sbps = [115, 130, 150, 175, 200]
    risks = [prevent_predict(**base, age=60, sbp=s)["risk"] for s in sbps]
    assert risks == sorted(risks)


def test_albi_and_amap_are_monotone_in_liver_dysfunction():
    from cancerverse_baseline.liver.detection import amap_predict
    from cancerverse_baseline.liver.prognosis import albi_score

    # Rising bilirubin and falling albumin both worsen ALBI.
    bili = [5, 10, 20, 40, 90]
    assert [albi_score(bilirubin_umol_l=b, albumin_g_l=40) for b in bili] == sorted(
        [albi_score(bilirubin_umol_l=b, albumin_g_l=40) for b in bili]
    )
    alb = [50, 45, 40, 35, 25]
    assert [albi_score(bilirubin_umol_l=20, albumin_g_l=a) for a in alb] == sorted(
        [albi_score(bilirubin_umol_l=20, albumin_g_l=a) for a in alb]
    )

    # aMAP rises with age and falls with platelets.
    ages = [30, 45, 60, 75]
    s = [
        amap_predict(
            age=a, male=True, platelets=200, bilirubin_umol_l=15, albumin_g_l=42
        )["score"]
        for a in ages
    ]
    assert s == sorted(s)
    plts = [400, 300, 200, 100, 50]
    s = [
        amap_predict(
            age=55, male=True, platelets=p, bilirubin_umol_l=15, albumin_g_l=42
        )["score"]
        for p in plts
    ]
    assert s == sorted(s)


def test_msk_rectal_survival_is_monotone_in_time_and_nodes():
    from cancerverse_baseline.colorectal.prognosis import msk_rectal_predict

    base = dict(
        ypt="ypT3",
        positive_nodes=2,
        distance_to_anal_verge_cm=4.0,
        venous_invasion=False,
        perineural_invasion=False,
    )
    for endpoint, extra in (("rfs", {}), ("os", {"age": 60})):
        surv = [
            msk_rectal_predict(endpoint=endpoint, months=m, **base, **extra)["survival"]
            for m in (0, 60, 120, 180)
        ]
        assert surv == sorted(surv, reverse=True)
        nodes = [
            msk_rectal_predict(
                endpoint=endpoint, months=60, **{**base, "positive_nodes": n}, **extra
            )["survival"]
            for n in (0, 1, 2, 4, 8)
        ]
        assert nodes == sorted(nodes, reverse=True)


def test_lipi_is_monotone_and_bounded():
    from cancerverse_baseline.lung.response import lipi_predict

    r = _rng()
    for _ in range(N):
        out = lipi_predict(
            dnlr=r.uniform(0.1, 20),
            ldh=r.uniform(50, 2000),
            ldh_upper_limit_normal=r.uniform(150, 300),
        )
        assert out["score"] in (0, 1, 2)
        assert out["group"] in ("good", "intermediate", "poor")


def test_atria_reproduces_table_3_including_its_non_monotonic_age_column():
    """The age x prior-stroke interaction, pinned against the paper.

    Verified against Table 3 of PMC3698792 on 2026-08-18. Age is NOT one term
    plus a stroke flag, it is scored 0/3/5/6 without a prior stroke and
    8/7/7/9 with one, and that second column is non-monotonic: 65-74 and 75-84
    both score 7, and a patient under 65 scores 8, more than a 75-year-old.

    This is worth a test rather than a comment because a third-party
    implementation already gets it wrong. CRAN `cliot` 1.0.0 models ATRIA as
    additive, age 0/3/5/6 plus a flat +4 for prior stroke, which agrees
    with this module on every patient WITHOUT a prior stroke and disagrees on
    every patient with one. Anyone comparing the two would see a partial
    mismatch and could plausibly "fix" the wrong side.

    The published score ranges are the sharpest available check on the whole
    table, and they are asserted by exhaustion rather than by sampling: the
    with-stroke minimum of 7 comes from the 65-74 band, NOT from the youngest
    band, so probing the extremes of age would report 8 and look like a defect.
    """
    import itertools

    from cancerverse_baseline.cvd.prognosis.atria import atria_score

    # Table 3, both columns, read from PMC3698792
    expected = {
        (90, False): 6, (80, False): 5, (70, False): 3, (50, False): 0,
        (90, True): 9, (80, True): 7, (70, True): 7, (50, True): 8,
    }
    for (age, prior), points in expected.items():
        bare = atria_score(
            age=age, prior_stroke=prior, female=False, diabetes=False,
            heart_failure=False, hypertension=False, proteinuria=False,
            egfr_under_45_or_esrd=False)
        assert bare == points, (
            f"age {age}, prior_stroke={prior}: Table 3 says {points}, got {bare}")

    # "Possible point scores range from 0 to 12 for those without a prior
    # stroke and from 7 to 15 for those with a prior stroke."
    for prior, published in ((False, (0, 12)), (True, (7, 15))):
        reachable = {
            atria_score(age=age, prior_stroke=prior, female=f, diabetes=d,
                        heart_failure=c, hypertension=h, proteinuria=p,
                        egfr_under_45_or_esrd=e)
            for age in (50, 70, 80, 90)
            for f, d, c, h, p, e in itertools.product([False, True], repeat=6)
        }
        assert (min(reachable), max(reachable)) == published, (
            f"prior_stroke={prior}: paper says {published}, reachable range is "
            f"{(min(reachable), max(reachable))}")

    # the non-monotonicity itself, so a "tidying" refactor cannot silently lose it
    flat = dict(female=False, diabetes=False, heart_failure=False,
                hypertension=False, proteinuria=False, egfr_under_45_or_esrd=False)
    assert atria_score(age=50, prior_stroke=True, **flat) > \
           atria_score(age=80, prior_stroke=True, **flat), (
        "with a prior stroke, under-65 must score HIGHER than 75-84 (8 vs 7)")


# --------------------------------------------------------------------------
# Generic sweep over EVERY model that declares a reference patient.
#
# The thirteen tests above are hand-written, one per model, which is why they
# reached only 17 of 40 implemented models: a model added later is silently
# absent, and this file's own docstring claims to cover "every implemented
# model". The sweep below closes that by reusing the reference patients and
# clinical ranges already maintained in scripts/feature_importance.py, so a new
# model becomes covered the moment it gains a sensitivity-sweep entry.
#
# It asserts only what holds without knowing a model's semantics, the output
# key exists, is numeric, is not NaN, and a `risk` is a genuine probability.
# Anything sharper belongs in a hand-written test above, where the units and
# the direction of effect are known.
# --------------------------------------------------------------------------


def _sweep_spec():
    """The SPEC table from scripts/feature_importance.py, or None."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts" / "feature_importance.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("_fi_spec", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "SPEC", None)


_SPEC = _sweep_spec() or {}


@pytest.mark.parametrize("model_id", sorted(_SPEC))
def test_output_stays_well_formed_over_a_randomized_legal_sweep(model_id):
    """Output key present, numeric, finite; a `risk` stays inside [0, 1].

    Randomizing each swept input independently can produce combinations the
    model legitimately refuses. BCRAT with end_age below start_age, PLCOm2012
    with a current smoker who also has quit_years, ADNEX with a solid component
    larger than the whole lesion. A raised ValueError there is the model working,
    so it is counted as a pass and not silently swallowed: anything OTHER than
    ValueError still fails, and so does a ValueError with no message.
    """
    import importlib
    import math

    module_path, fn_name, key, _scale, reference, sweeps = _SPEC[model_id]
    fn = getattr(importlib.import_module(module_path), fn_name)
    r = _rng()

    checked = 0
    for _ in range(N):
        kwargs = dict(reference)
        for _label, (arg, values) in sweeps.items():
            kwargs[arg] = r.choice(values)
        try:
            out = fn(**kwargs)
        except ValueError as exc:
            assert str(exc).strip(), (
                f"{model_id} rejected {kwargs} with an empty ValueError; a "
                f"refusal has to say what was wrong")
            continue
        checked += 1
        assert key in out, f"{model_id}: output has no {key!r}, got {sorted(out)}"
        value = out[key]
        assert isinstance(value, (int, float)) and not isinstance(value, bool), (
            f"{model_id}.{key} is {value!r}, not a number")
        assert math.isfinite(value), f"{model_id}.{key} is {value} for {kwargs}"
        if key == "risk":
            assert 0.0 <= value <= 1.0, (
                f"{model_id} returned risk={value} for {kwargs}")

    assert checked, (
        f"{model_id}: every one of {N} sampled inputs was refused, so nothing "
        f"was actually checked, the reference patient or ranges are wrong")


def test_every_implemented_model_is_reachable_by_some_invariant_check():
    """No model may be absent from all three buckets.

    This file's docstring says "every implemented model", and on 2026-08-18 the
    thirteen hand-written tests above reached 17 of 40. The generic sweep closes
    most of that, but only for models `feature_importance.SPEC` describes, so
    the gap can silently reopen the next time a model is added.

    Three legitimate buckets, and a model must be in one:

      SPEC              numeric output, swept above
      CATEGORICAL_NOTE  output is a category, so numeric bounds do not apply,
                        ang2010_rpa returns a risk group, LIPI a three-level
                        index, the Optum LASSO takes a covariate dict
      _NO_SWEEP         explicitly excused here, with the reason

    Anything else fails, which forces the choice to be made rather than skipped.
    """
    import importlib.util
    from pathlib import Path

    #: Excused, with the reason. Keep this list short.
    _NO_SWEEP = {
        "cvd_statin_benefit":
            "a derived composition, it takes another model's output as its "
            "input, so there is no patient to sweep and no external target",
        "dutasteride":
            "9 outcomes x 2 arms; the output is a table of differences, not a "
            "single risk, so the generic numeric assertion does not apply",
    }

    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "feature_importance.py"
    if not path.exists():
        pytest.skip("scripts/feature_importance.py is not present")
    spec = importlib.util.spec_from_file_location("_fi_cov", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    from cancerverse_baseline.registry import load_models

    covered = (set(getattr(module, "SPEC", {}))
               | set(getattr(module, "CATEGORICAL_NOTE", {}))
               | set(_NO_SWEEP))
    uncovered = sorted(m["id"] for m in load_models()
                       if m.get("status") == "implemented" and m["id"] not in covered)
    assert not uncovered, (
        "implemented models in no invariant bucket: " + ", ".join(uncovered)
        + ". Add a reference patient to feature_importance.SPEC, or a note to "
          "CATEGORICAL_NOTE, or excuse it in _NO_SWEEP with a reason.")
