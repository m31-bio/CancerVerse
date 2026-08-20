#!/usr/bin/env python3
"""Which predictor actually drives each model?

    python scripts/feature_importance.py [--json out.json]

Method: hold every input at a clinically ordinary reference patient, sweep one
input across its plausible clinical range, and record how far the output moves.
The swing is the feature's influence *in the range a real patient occupies*,
which is the question a clinician asks, and is not the same as the size of the
coefficient. Age in a Cox model can carry a small beta and still dominate,
because it ranges over fifty years.

Reported on each model's own output scale:
  * probability models  -> percentage points of absolute risk
  * point scores        -> points
  * index / linear      -> index units

Comparisons are therefore valid WITHIN a model, not across models. Each swing
is also given as a share of that model's total swing, which is comparable.

Ranges are deliberately clinical, not mathematical: PSA 1-30 not 0-1000. A
sweep over impossible inputs would name whichever feature has the widest
arithmetic domain, which tells you nothing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# spec: model_id -> (module, function, output_key, reference kwargs, sweeps)
# `sweeps` maps a human label to (kwarg, [values across the clinical range]).
# ---------------------------------------------------------------------------
SPEC = {
    "bcrat": (
        "cancerverse_baseline.breast.detection",
        "bcrat_predict",
        "risk",
        100,
        dict(
            start_age=50,
            end_age=55,
            race="white",
            n_biopsies=0,
            atypical_hyperplasia="unknown",
            age_menarche=13,
            age_first_birth=25,
            n_relatives=0,
        ),
        {
            "age at menarche": ("age_menarche", [15, 13, 11]),
            "age at first birth": ("age_first_birth", [19, 25, 32]),
            "prior biopsies": ("n_biopsies", [0, 1, 2]),
            "first-degree relatives": ("n_relatives", [0, 1, 2]),
            "current age": ("start_age", [40, 50, 65]),
        },
    ),
    "bcsc_v2": (
        "cancerverse_baseline.breast.detection",
        "bcsc_v2_predict",
        "risk",
        100,
        dict(
            start_age=55,
            race="white",
            density=2,
            family_history=False,
            biopsy_history=False,
        ),
        {
            "density": ("density", [1, 2, 3, 4]),
            "biopsy history": ("biopsy_history", [False, True]),
            "family history": ("family_history", [False, True]),
            "current age": ("start_age", [40, 55, 70]),
            "race": ("race", ["white", "black", "asian", "hispanic"]),
        },
    ),
    "prevent": (
        "cancerverse_baseline.cvd.detection",
        "prevent_predict",
        "risk",
        100,
        dict(
            sex="female",
            age=55,
            total_chol_mg_dl=200,
            hdl_mg_dl=50,
            sbp=130,
            diabetes=False,
            smoker=False,
            bmi=27,
            egfr=90,
            htn_meds=False,
            statin=False,
        ),
        {
            "age": ("age", [40, 55, 75]),
            "systolic BP": ("sbp", [110, 130, 180]),
            "total cholesterol": ("total_chol_mg_dl", [150, 200, 280]),
            "HDL": ("hdl_mg_dl", [30, 50, 80]),
            "eGFR": ("egfr", [30, 90, 120]),
            "diabetes": ("diabetes", [False, True]),
            "smoking": ("smoker", [False, True]),
            "BMI (total CVD, no effect, see note)": ("bmi", [20, 27, 40]),
        },
    ),
    "score2": (
        "cancerverse_baseline.cvd.detection",
        "score2_predict",
        "risk",
        100,
        dict(
            sex="male",
            age=55,
            sbp=130,
            total_chol_mmol=5.5,
            hdl_mmol=1.3,
            smoker=False,
            region="moderate",
        ),
        {
            "age": ("age", [40, 55, 69]),
            "systolic BP": ("sbp", [110, 130, 180]),
            "total cholesterol": ("total_chol_mmol", [4.0, 5.5, 8.0]),
            "HDL": ("hdl_mmol", [0.8, 1.3, 2.2]),
            "smoking": ("smoker", [False, True]),
        },
    ),
    "grace": (
        "cancerverse_baseline.cvd.prognosis",
        "grace_predict",
        "score",
        1,
        dict(killip_class=1, sbp=130, heart_rate=80, age=65, creatinine_mg_dl=1.0),
        {
            "age": ("age", [35, 65, 85]),
            "Killip class": ("killip_class", [1, 2, 3, 4]),
            "systolic BP": ("sbp", [80, 130, 200]),
            "heart rate": ("heart_rate", [55, 80, 200]),
            "creatinine": ("creatinine_mg_dl", [0.5, 1.0, 4.5]),
            "cardiac arrest": ("cardiac_arrest_at_admission", [False, True]),
        },
    ),
    "cha2ds2_vasc": (
        "cancerverse_baseline.cvd.prognosis",
        "cha2ds2_vasc_predict",
        "score",
        1,
        dict(
            heart_failure=False,
            hypertension=False,
            age=60,
            diabetes=False,
            prior_stroke_tia_thromboembolism=False,
            vascular_disease=False,
            female=False,
        ),
        {
            "age": ("age", [60, 70, 80]),
            "prior stroke / TIA": ("prior_stroke_tia_thromboembolism", [False, True]),
            "heart failure": ("heart_failure", [False, True]),
            "hypertension": ("hypertension", [False, True]),
            "diabetes": ("diabetes", [False, True]),
            "vascular disease": ("vascular_disease", [False, True]),
            "female sex": ("female", [False, True]),
        },
    ),
    "atria_stroke_2013": (
        "cancerverse_baseline.cvd.prognosis",
        "atria_predict",
        "score",
        1,
        dict(
            age=60,
            prior_stroke=False,
            female=False,
            diabetes=False,
            heart_failure=False,
            hypertension=False,
            proteinuria=False,
            egfr_under_45_or_esrd=False,
        ),
        # Age is swept WITHOUT a prior stroke and the stroke flag separately,
        # because the two interact: the sweep would understate age's effect if
        # it moved age while prior_stroke was fixed at True (where the bands
        # run 8, 7, 7, 9 rather than 0, 3, 5, 6).
        {
            "age": ("age", [60, 70, 80, 90]),
            "prior stroke": ("prior_stroke", [False, True]),
            "eGFR<45 or ESRD": ("egfr_under_45_or_esrd", [False, True]),
            "proteinuria": ("proteinuria", [False, True]),
            "heart failure": ("heart_failure", [False, True]),
            "hypertension": ("hypertension", [False, True]),
            "diabetes": ("diabetes", [False, True]),
            "female sex": ("female", [False, True]),
        },
    ),
    "ukb_hnc": (
        "cancerverse_baseline.head_neck.detection",
        "ukb_hnc_predict",
        "risk",
        100,
        dict(
            age=60,
            male=True,
            smoking_status="never",
            townsend_quintile=3,
            bmi=27,
            alcohol_status="current",
            exercise_days="1-4_days",
            fruit_veg="5_or_more",
        ),
        # Alcohol is swept never -> previous -> current rather than in the
        # obvious order, because the fitted effect is non-monotonic: previous
        # drinkers carry OR 3.26 and current drinkers 1.42. A sweep that
        # stopped at "current" would report the alcohol term as small.
        {
            "age": ("age", [50, 60, 69]),
            "smoking": ("smoking_status", ["never", "previous", "current"]),
            "alcohol": ("alcohol_status", ["never", "current", "previous"]),
            "deprivation": ("townsend_quintile", [1, 3, 4]),
            "BMI": ("bmi", [20, 27, 35]),
            "male sex": ("male", [False, True]),
            "exercise": ("exercise_days", ["5_or_more_days", "1-4_days", "none"]),
            "five-a-day": ("fruit_veg", ["5_or_more", "under_5"]),
        },
    ),
    "plcom2012": (
        "cancerverse_baseline.lung.detection",
        "plcom2012_predict",
        "risk",
        100,
        dict(
            age=62,
            race="white",
            education_level=4,
            bmi=27,
            copd=False,
            personal_cancer_history=False,
            family_history_lung_cancer=False,
            current_smoker=False,
            cigarettes_per_day=20,
            smoking_duration_years=30,
            quit_years=10,
        ),
        {
            "age": ("age", [55, 62, 74]),
            "smoking duration": ("smoking_duration_years", [10, 30, 50]),
            "cigarettes per day": ("cigarettes_per_day", [5, 20, 60]),
            "years since quitting": ("quit_years", [0, 10, 30]),
            "current smoker": ("current_smoker", [False, True]),
            "COPD": ("copd", [False, True]),
            "BMI": ("bmi", [18, 27, 40]),
            "family history": ("family_history_lung_cancer", [False, True]),
        },
    ),
    "erspc_rc3": (
        "cancerverse_baseline.prostate.detection",
        "erspc_rc3_predict",
        "risk",
        100,
        dict(psa=4.0, volume_ml=40, dre_positive=False),
        {
            "PSA": ("psa", [1.0, 4.0, 30.0]),
            "prostate volume": ("volume_ml", [20, 40, 80]),
            "abnormal DRE": ("dre_positive", [False, True]),
        },
    ),
    "pbcg": (
        "cancerverse_baseline.prostate.detection",
        "pbcg_predict",
        "risk",
        100,
        dict(
            psa=6.0,
            age=65,
            african_ancestry=False,
            prior_biopsy=False,
            dre_abnormal=False,
            family_history=False,
        ),
        {
            "PSA": ("psa", [1.0, 6.0, 30.0]),
            "abnormal DRE": ("dre_abnormal", [False, True]),
            "age": ("age", [45, 65, 85]),
            "African ancestry": ("african_ancestry", [False, True]),
            "prior negative biopsy": ("prior_biopsy", [False, True]),
            "family history": ("family_history", [False, True]),
        },
    ),
    "pbcg_extended": (
        "cancerverse_baseline.prostate.detection",
        "pbcg_extended_predict",
        "risk",
        100,
        dict(
            age=65,
            psa=6.0,
            race=0,
            prior_biopsy=0,
            dre_abnormal=0,
            famhist_1=0,
            famhist_2=0,
            famhist_bca=0,
            prostate_volume=40.0,
            ari_use=0,
            hispanic=0,
            prior_psa=0,
        ),
        # Sweeping a value here does NOT hold the model fixed the way it does
        # elsewhere: every predictor is optional, so removing one selects a
        # different fitted sub-model. The sweep varies values, never presence.
        {
            "PSA": ("psa", [1.0, 6.0, 30.0]),
            "abnormal DRE": ("dre_abnormal", [0, 1]),
            "age": ("age", [45, 65, 85]),
            "African ancestry": ("race", [0, 1]),
            "prostate volume": ("prostate_volume", [20.0, 40.0, 100.0]),
            "prior negative biopsy": ("prior_biopsy", [0, 1]),
            "first-degree family history": ("famhist_1", [0, 1]),
        },
    ),
    "capra": (
        "cancerverse_baseline.prostate.prognosis",
        "capra_predict",
        "score",
        1,
        dict(
            psa=6.0,
            gleason_primary=3,
            gleason_secondary=3,
            t_stage="T1c",
            percent_positive_cores=20,
            age=60,
        ),
        {
            "PSA": ("psa", [3.0, 6.0, 35.0]),
            "Gleason primary": ("gleason_primary", [3, 4, 5]),
            "T stage": ("t_stage", ["T1c", "T3a"]),
            "% positive cores": ("percent_positive_cores", [10, 20, 60]),
            "age": ("age", [45, 60]),
        },
    ),
    "amap": (
        "cancerverse_baseline.liver.detection",
        "amap_predict",
        "score",
        1,
        dict(age=55, male=True, platelets=200, bilirubin_umol_l=15, albumin_g_l=42),
        {
            "age": ("age", [30, 55, 80]),
            "platelets": ("platelets", [60, 200, 350]),
            "albumin": ("albumin_g_l", [28, 42, 50]),
            "bilirubin": ("bilirubin_umol_l", [5, 15, 60]),
            "male sex": ("male", [False, True]),
        },
    ),
    "albi": (
        "cancerverse_baseline.liver.prognosis",
        "albi_predict",
        "score",
        1,
        dict(bilirubin_umol_l=20, albumin_g_l=40),
        {
            "albumin": ("albumin_g_l", [25, 40, 50]),
            "bilirubin": ("bilirubin_umol_l", [5, 20, 100]),
        },
    ),
    "hap": (
        "cancerverse_baseline.liver.response",
        "hap_predict",
        "score",
        1,
        dict(
            albumin_g_l=40,
            bilirubin_umol_l=15,
            afp_ng_ml=100,
            dominant_tumour_size_cm=5,
        ),
        {
            "albumin < 36 g/L": ("albumin_g_l", [40, 30]),
            "bilirubin > 17 µmol/L": ("bilirubin_umol_l", [15, 25]),
            "AFP > 400 ng/mL": ("afp_ng_ml", [100, 800]),
            "tumour > 7 cm": ("dominant_tumour_size_cm", [5, 9]),
        },
    ),
    "kunzmann": (
        "cancerverse_baseline.esophageal.detection",
        "kunzmann_predict",
        "score",
        1,
        dict(age=60, male=False, bmi=24, smoking="never", esophageal_condition=False),
        {
            "male sex": ("male", [False, True]),
            "age": ("age", [52, 60, 70]),
            "smoking": ("smoking", ["never", "former", "current"]),
            "BMI": ("bmi", [24, 27, 40]),
            "oesophageal condition": ("esophageal_condition", [False, True]),
        },
    ),
    "iota_adnex": (
        "cancerverse_baseline.ovarian.detection",
        "adnex_predict",
        "risk",
        100,
        dict(
            age=55,
            ca125=64.0,
            lesion_diameter_mm=64.0,
            solid_diameter_mm=20.0,
            more_than_10_locules=False,
            papillary_structures=0,
            acoustic_shadows=False,
            ascites=False,
            oncology_centre=False,
        ),
        {
            "CA-125": ("ca125", [10.0, 64.0, 500.0]),
            "solid component": ("solid_diameter_mm", [0.0, 20.0, 60.0]),
            "ascites": ("ascites", [False, True]),
            "age": ("age", [30, 55, 80]),
            "papillary structures": ("papillary_structures", [0, 2, 4]),
            "lesion diameter": ("lesion_diameter_mm", [30.0, 64.0, 150.0]),
            # a site constant rather than a patient variable, swept because it
            # moves the answer and a reader should see by how much
            "oncology centre": ("oncology_centre", [False, True]),
        },
    ),
    "roma": (
        "cancerverse_baseline.ovarian.detection",
        "roma_predict",
        "risk",
        100,
        dict(he4_pmol_l=60, ca125_u_ml=30, postmenopausal=True),
        {
            "HE4": ("he4_pmol_l", [25, 60, 400]),
            "CA-125": ("ca125_u_ml", [10, 30, 500]),
            "postmenopausal": ("postmenopausal", [False, True]),
        },
    ),
    "rmi": (
        "cancerverse_baseline.ovarian.detection",
        "rmi_predict",
        "index",
        1,
        dict(ultrasound_score=1, postmenopausal=False, ca125=30, variant="rmi1"),
        {
            "CA-125": ("ca125", [10, 30, 500]),
            "ultrasound features": ("ultrasound_score", [0, 1, 4]),
            "postmenopausal": ("postmenopausal", [False, True]),
        },
    ),
    "cervical_cin_risk": (
        "cancerverse_baseline.cervical.detection",
        "cervical_cin_risk_predict",
        "risk",
        100,
        dict(hrhpv_positive=False, cytology="NILM", age=40, variant="base"),
        {
            "cytology grade": (
                "cytology",
                ["NILM", "ASC-US", "LSIL", "ASC-H", "HSIL/AIS", "SCC/ADC"],
            ),
            "hrHPV positive": ("hrhpv_positive", [False, True]),
            "age": ("age", [25, 40, 65]),
        },
    ),
    # Reference patient is the modal one in the paper's own Table 1: squamous
    # (68.4%), 0.5-1.99 cm (39.7%), grade 2 (51.8%), node-negative, LVSI-
    # negative (55.6%), 15 points, band 1-25.
    #
    # The sweep and the audit are expected to DISAGREE about histotype here,
    # and that is the finding rather than a defect. The sweep runs each input
    # to the end of its clinical range, so histotype swings 0 -> 33 points and
    # comes out on top. Weighting by how often each level actually occurs
    # (Table 1) puts tumour diameter first at 14.4 average points against 2.9,
    # because neuroendocrine is 1.0% of patients. Diameter moves the average
    # patient; histotype moves the extreme one. See registry/parameters.yaml.
    "cibula_arrm": (
        "cancerverse_baseline.cervical.prognosis",
        "cibula_arrm_predict",
        "score",
        1,
        dict(
            histotype="squamous",
            tumour_diameter_cm=1.5,
            grade=2,
            positive_pelvic_nodes=0,
            lvsi=False,
        ),
        {
            "histotype": (
                "histotype",
                [
                    "squamous",
                    "adenocarcinoma",
                    "adenosquamous",
                    "other",
                    "neuroendocrine",
                ],
            ),
            "tumour diameter": ("tumour_diameter_cm", [0.3, 1.5, 3.0, 5.0]),
            "grade": ("grade", [1, 2, 3]),
            "positive pelvic nodes": ("positive_pelvic_nodes", [0, 1, 2, 4]),
            "LVSI": ("lvsi", [False, True]),
        },
    ),
    # No output_key of "risk" or "score": moore_criteria returns a count
    # (risk_factor_count), and every factor moves it by exactly 1, the
    # paper's own point, since it explicitly declined to weight them
    # differently. The sweep is included anyway to confirm that in code: all
    # five swings should come out equal, which no other model in this file
    # is expected to show.
    # Reference patient carries no risk factors: PS 1, no metastases, ALP 80.
    # Like moore_criteria, every factor should swing the count by exactly 1 --
    # the paper declined to weight them ("similar order of magnitude"). The two
    # models are the only ones in this file where equal swings are the CORRECT
    # result rather than a coincidence.
    # Output is 1-year survival, so a HIGHER swing means a worse patient.
    # ypN is swept over all four categories deliberately: ypN2 returns None
    # (no published survival at odd totals) and the sweep has to cope with
    # that rather than crash, which is itself worth exercising.
    "shapiro_ncrt": (
        "cancerverse_baseline.esophageal.prognosis",
        "shapiro_ncrt_predict",
        "total_points",
        1,
        dict(cn_category="cN0", ypt_category="ypT0", ypn_category="ypN0"),
        {
            "clinical N": ("cn_category", ["cN0", "cN1"]),
            "ypT": ("ypt_category", ["ypT0", "ypT1", "ypT3"]),
            "ypN": ("ypn_category", ["ypN0", "ypN1", "ypN2", "ypN3"]),
        },
    ),
    "chau_eg": (
        "cancerverse_baseline.esophageal.response",
        "chau_eg_predict",
        "risk_factor_count",
        1,
        dict(
            performance_status=1,
            liver_metastases=False,
            peritoneal_metastases=False,
            alkaline_phosphatase_u_l=80.0,
        ),
        {
            "performance status": ("performance_status", [1, 2]),
            "liver metastases": ("liver_metastases", [False, True]),
            "peritoneal metastases": ("peritoneal_metastases", [False, True]),
            "alkaline phosphatase": ("alkaline_phosphatase_u_l", [80.0, 150.0]),
        },
    ),
    "moore_criteria": (
        "cancerverse_baseline.cervical.response",
        "moore_criteria_predict",
        "risk_factor_count",
        1,
        dict(
            black_race=False,
            performance_status=0,
            disease_site="distant",
            prior_radiosensitizer=False,
            months_diagnosis_to_first_recurrence=24,
        ),
        {
            "race": ("black_race", [False, True]),
            "performance status": ("performance_status", [0, 2]),
            "disease site": ("disease_site", ["distant", "pelvic"]),
            "prior radiosensitizer": ("prior_radiosensitizer", [False, True]),
            "recurrence interval": ("months_diagnosis_to_first_recurrence", [24, 6]),
        },
    ),
    "endpac": (
        "cancerverse_baseline.pancreatic.detection",
        "endpac_predict",
        "score",
        1,
        dict(
            glucose_at_diabetes_mg_dl=130,
            glucose_one_year_before_mg_dl=105,
            weight_change_kg=0.0,
            age_at_diabetes_onset=65,
        ),
        {
            "weight change": ("weight_change_kg", [6.0, 0.0, -7.0]),
            "glucose rise": ("glucose_one_year_before_mg_dl", [120, 105, 95]),
            "age at onset": ("age_at_diabetes_onset", [55, 65, 75]),
        },
    ),
    "abc_method": (
        "cancerverse_baseline.gastric.detection",
        "abc_method_predict",
        "risk",
        100,
        dict(
            h_pylori_antibody_positive=False, pepsinogen_i=60, pepsinogen_i_ii_ratio=4.0
        ),
        # Atrophy requires PG I <= 70 AND PG I/II <= 3.0, so sweeping PG I
        # alone can never flip it, the ratio has to move with it.
        {
            "pepsinogen atrophy": ("pepsinogen_i_ii_ratio", [4.0, 2.5]),
            "H. pylori antibody": ("h_pylori_antibody_positive", [False, True]),
        },
    ),
    "xu_gastric_trg_score": (
        # Swept on "score", not "risk": this model publishes no
        # points-to-probability mapping, so it has no risk to sweep. The
        # scale is 1 because the score is already in points.
        "cancerverse_baseline.gastric.response",
        "xu_gastric_trg_score_predict",
        "score",
        1,
        dict(ca19_9_u_ml=50.0, ca72_4_u_ml=9.0, differentiation="poor", lnmax_cm=1.0),
        # Each predictor is dichotomous, so two levels per sweep is the whole
        # range, there is nothing between "scores" and "does not score".
        # LNmax is swept LOW to HIGH deliberately: the large node is the level
        # that scores, which is the paper's direction and the counterintuitive
        # one. See the module docstring.
        {
            "differentiation": ("differentiation", ["poor", "well"]),
            "largest node short axis": ("lnmax_cm", [1.0, 2.0]),
            "CA19-9": ("ca19_9_u_ml", [50.0, 5.0]),
            "CA72-4": ("ca72_4_u_ml", [9.0, 2.0]),
        },
    ),
    "msk_gastric": (
        "cancerverse_baseline.gastric.prognosis",
        "msk_gastric_predict",
        "risk",
        100,
        dict(
            age=60,
            male=True,
            primary_site="antrum_or_pyloric",
            lauren="intestinal",
            size_cm=4.0,
            positive_nodes=3,
            negative_nodes=15,
            depth="subserosa",
            years=5,
        ),
        {
            "depth of invasion": (
                "depth",
                ["mucosa", "subserosa", "adjacent_organ_involvement"],
            ),
            "positive nodes": ("positive_nodes", [0, 3, 23]),
            "negative nodes": ("negative_nodes", [0, 15, 146]),
            "age": ("age", [30, 60, 90]),
            "primary site": (
                "primary_site",
                ["antrum_or_pyloric", "gastroesophageal_junction"],
            ),
            "tumour size": ("size_cm", [1.0, 4.0, 21.0]),
            "Lauren type": ("lauren", ["intestinal", "mixed", "diffuse"]),
            "male sex": ("male", [False, True]),
        },
    ),
    "crc_pro": (
        "cancerverse_baseline.colorectal.detection",
        "crc_pro_predict",
        "risk",
        100,
        dict(
            male=True,
            age=62,
            ethnicity="white",
            weight_lb=180,
            height_in=69,
            years_education=14,
            pack_years=10,
            alcohol_drinks_per_day=1.0,
            family_history=False,
            multivitamin=False,
            diabetes=False,
            aspirin="no",
            red_meat_oz_per_day=1.5,
            activity_hours_per_day=1.0,
        ),
        {
            "age": ("age", [45, 62, 85]),
            "ethnicity": ("ethnicity", ["black", "japanese", "white", "latino"]),
            "alcohol": ("alcohol_drinks_per_day", [0.0, 1.0, 12.0]),
            "red meat": ("red_meat_oz_per_day", [0.0, 1.5, 5.0]),
            "physical activity": ("activity_hours_per_day", [0.0, 1.0, 4.0]),
            "aspirin": ("aspirin", ["no", "previously", "currently"]),
            "family history": ("family_history", [False, True]),
            "weight": ("weight_lb", [130, 180, 300]),
            "education": ("years_education", [6, 14, 20]),
            "pack-years": ("pack_years", [0, 10, 50]),
            "diabetes": ("diabetes", [False, True]),
            "multivitamin": ("multivitamin", [False, True]),
        },
    ),
    "msk_ovarian": (
        "cancerverse_baseline.ovarian.prognosis",
        "msk_ovarian_predict",
        "risk",
        100,
        dict(
            age=60,
            grade="3",
            histology_yes=False,
            platelets=400,
            ascites=False,
            residual_disease="0.5_1_cm",
        ),
        {
            "residual disease": (
                "residual_disease",
                ["no_gross_residual", "0.5_1_cm", "gt_2_cm"],
            ),
            "ascites": ("ascites", [False, True]),
            "age": ("age", [22, 60, 87]),
            "platelets": ("platelets", [113, 400, 1078]),
            "histology": ("histology_yes", [False, True]),
            "grade 3": ("grade", ["1-2", "3"]),
        },
    ),
    "msk_pancreatic": (
        "cancerverse_baseline.pancreatic.prognosis",
        "msk_pancreatic_predict",
        "risk",
        100,
        dict(
            age=62,
            male=True,
            location="head",
            differentiation="moderate",
            positive_nodes=2,
            negative_nodes=12,
            t_stage="2",
            size_cm=3.0,
            months=12,
        ),
        {
            "tumour size": ("size_cm", [0.5, 3.0, 12.0]),
            "positive nodes": ("positive_nodes", [0, 2, 39]),
            "splenectomy": ("splenectomy", [False, True]),
            "resection location": ("location", ["head", "other"]),
            "T stage": ("t_stage", ["1", "2", "3", "4"]),
            "differentiation": ("differentiation", ["well", "moderate", "poor"]),
            "posterior margin": ("posterior_margin_positive", [False, True]),
            "back pain": ("back_pain", [False, True]),
            "portal vein resected": ("portal_vein_resected", [False, True]),
            "negative nodes": ("negative_nodes", [0, 12, 83]),
            "age": ("age", [33, 62, 89]),
        },
    ),
    "msk_rectal": (
        "cancerverse_baseline.colorectal.prognosis",
        "msk_rectal_predict",
        "risk",
        100,
        dict(
            endpoint="os",
            months=60,
            ypt="ypT3",
            positive_nodes=2,
            distance_to_anal_verge_cm=6.0,
            venous_invasion=False,
            perineural_invasion=False,
            age=60,
        ),
        {
            "ypT stage": ("ypt", ["ypT0", "ypT3", "ypT4"]),
            "positive nodes": ("positive_nodes", [0, 2, 9]),
            "age": ("age", [40, 60, 80]),
            "perineural invasion": ("perineural_invasion", [False, True]),
            "venous invasion": ("venous_invasion", [False, True]),
            "distance to anal verge": ("distance_to_anal_verge_cm", [2.0, 8.0]),
        },
    ),
    # Reference patient = the model's own reference level on every covariate
    # (cN0, cT2, EMVI-negative, no TNT, adenocarcinoma) with CEA 0, so the
    # baseline is the intercept alone: 49.67 pp. CEA sweeps the full 0-24
    # ng/mL slider the authors' calculator allows, and nothing wider, the
    # term is linear in the logit and is not extrapolated.
    "wang_larc_pcr": (
        "cancerverse_baseline.colorectal.response",
        "wang_larc_pcr_predict",
        "risk",
        100,
        dict(
            n_stage="cN0",
            t_stage="cT2",
            mri_emvi_positive=False,
            total_neoadjuvant_therapy=False,
            histopathology="adenocarcinoma",
            cea_ng_ml=0.0,
        ),
        {
            "histopathology": (
                "histopathology",
                ["adenocarcinoma", "signet_ring_mucinous"],
            ),
            "pre-CRT CEA": ("cea_ng_ml", [0.0, 5.0, 24.0]),
            # cT2 is the reference and the effect is NOT monotone: cT3 sits above
            # cT2 and cT4 barely differs from it.
            "pre-CRT T stage": ("t_stage", ["cT1", "cT2", "cT3", "cT4"]),
            "MRI EMVI": ("mri_emvi_positive", [False, True]),
            "total neoadjuvant therapy": ("total_neoadjuvant_therapy", [False, True]),
            "pre-CRT N stage": ("n_stage", ["cN0", "cN1", "cN2"]),
        },
    ),
    "lipi": (
        "cancerverse_baseline.lung.response",
        "lipi_predict",
        "score",
        1,
        dict(dnlr=2.0, ldh=200, ldh_upper_limit_normal=250),
        {"dNLR > 3": ("dnlr", [2.0, 5.0]), "LDH > ULN": ("ldh", [200, 400])},
    ),
}

# Models whose output is a category, not a number, importance is structural.
CATEGORICAL_NOTE = {
    "ang2010_rpa": (
        "HPV status",
        "The first split of the tree. HPV-positive "
        "disease is low risk unless the patient is both a heavy "
        "smoker and node-positive; HPV-negative is high risk "
        "unless a light smoker with T2/T3.",
    ),
    "predict_breast": (
        "tumour size, nodes and grade, then treatment",
        "A survival model, so influence depends on the horizon; "
        "the prognostic index is dominated by nodal status and "
        "size, and the treatment arms shift survival by "
        "10-30 percentage points at 10 years.",
    ),
    "predict_breast_response": (
        "chemotherapy generation and ER status",
        "Benefit is the difference between two survival "
        "curves, so the treatment arms ARE the model.",
    ),
    "lipi_prognosis": (
        "dNLR and LDH equally",
        "Two binary items, one point each; neither is weighted above the other.",
    ),
    "optum_lung_lasso": (
        "coded smoking status, then age band",
        "No clinical-range sweep is possible or meaningful: all 278 predictors "
        "are 0/1 indicators for an OMOP concept observed in the year before "
        "index, so there is no range to vary and 'one standard patient' does "
        "not exist. Importance is read off the fitted coefficients instead: "
        "current smoker (+1.5915) is the largest, then the 65-69 and 60-64 age "
        "bands. Worth flagging rather than smoothing over: the fourth and "
        "fifth largest coefficients are a body-temperature measurement "
        "(-0.8444) and a temperature observation (+0.8025), the same fact "
        "filed in two OMOP domains with opposite signs. That is documentation "
        "and utilisation showing through, not lung biology.",
    ),
}


def sweep(model_id: str) -> dict | None:
    import importlib

    if model_id not in SPEC:
        return None
    modname, fnname, key, scale, ref, sweeps = SPEC[model_id]
    fn = getattr(importlib.import_module(modname), fnname)

    base = fn(**ref)[key]
    rows = []
    for label, (kwarg, values) in sweeps.items():
        outs = []
        for v in values:
            kw = dict(ref)
            kw[kwarg] = v
            try:
                outs.append(fn(**kw)[key])
            except Exception:
                continue
        if len(outs) < 2:
            continue
        rows.append(
            {
                "feature": label,
                "low": min(outs) * scale,
                "high": max(outs) * scale,
                "swing": (max(outs) - min(outs)) * scale,
            }
        )
    total = sum(r["swing"] for r in rows) or 1.0
    for r in rows:
        r["share"] = r["swing"] / total
    rows.sort(key=lambda r: -r["swing"])
    return {"model": model_id, "baseline": base * scale, "features": rows}


def main() -> int:
    import sys

    import yaml

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    reg = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "registry" / "models.yaml").read_text()
    )["models"]
    impl = [m for m in reg if m.get("status") == "implemented"]
    by_disease: dict[str, list] = {}
    for m in impl:
        by_disease.setdefault(m["disease"], []).append(m)

    out = {}
    for disease in sorted(by_disease):
        print(f"\n{'=' * 74}\n{disease.upper()}")
        for m in by_disease[disease]:
            res = sweep(m["id"])
            if res is None:
                feat, why = CATEGORICAL_NOTE.get(m["id"], ("—", ""))
                print(f"\n  {m['id']}  ({m['axis']})")
                print(f"     dominant: {feat}")
                if why:
                    print(f"     {why}")
                out[m["id"]] = {"model": m["id"], "dominant": feat, "note": why}
                continue
            unit = "pp risk" if SPEC[m["id"]][3] == 100 else "points"
            print(
                f"\n  {m['id']}  ({m['axis']})   reference patient: "
                f"{res['baseline']:.2f} {unit}"
            )
            for r in res["features"]:
                bar = "#" * max(1, round(r["share"] * 34))
                print(
                    f"     {r['feature']:26} {r['swing']:8.2f}  "
                    f"{r['share']:5.0%}  {bar}"
                )
            out[m["id"]] = res

    if args.json:
        args.json.write_text(json.dumps(out, indent=2))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
