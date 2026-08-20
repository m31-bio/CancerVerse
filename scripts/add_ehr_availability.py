"""Record, per model, whether an EHR can actually supply its inputs.

The question "are these models too old?" turned out to be the wrong one. Age
and EHR-computability are close to uncorrelated here: ALBI (2015) needs two
routine labs and nothing else, GRACE (2003) needs only what an acute coronary
admission already documents, while CRC-PRO (2014) needs years of education and
ounces of red meat per day. What matters is whether a model asks for things a
health record holds, and that was recorded nowhere.

Three tiers, defined by where the value lives rather than by how hard it feels:

  routine    demographics, standard labs (CBC, CMP, lipids, HbA1c, creatinine),
             vitals, BMI, coded diagnoses and medications, coded smoking
             status. Present in essentially any EHR.

  specialty  a pathology or staging field, an imaging measurement, or a
             send-out assay. Real data, routinely captured at a cancer centre
             and often absent elsewhere, and frequently living in a report
             rather than a structured column.

  not_ehr    questionnaire and patient-reported items: years of education,
             pack-years as a number, drinks per day, ounces of red meat,
             symptom scores, sexual function. A health record does not hold
             these because nobody is asked them at registration.

`ehr_note` names the specific obstacles rather than leaving the tier to be
guessed at, and only ever lists REQUIRED inputs, an optional input that an
EHR lacks costs nothing.

That distinction is the whole reason pbcg_extended is `routine` despite naming
race, family history and prostate volume: it requires only age and PSA, and
fits a separate sub-model for every pattern of the other ten. Missing data
selects a model rather than triggering an imputation. That behaviour, not
recency, is what makes a model usable on real records.

This pass also fills `inputs` for five models that had none recorded. Their
signatures were in the code all along; the registry simply never carried them,
so any table built from the registry showed a blank.
"""

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from cancerverse_baseline.registry.save import save_models  # noqa: E402

# id -> (tier, note). Classified by reading each model's required inputs, not
# by pattern-matching their names.
EHR = {
    # ---- routine: an EHR has all of this ------------------------------
    "albi": ("routine", "Two standard chemistry values: bilirubin and albumin."),
    "amap": ("routine", "Age, sex, platelets, bilirubin, albumin, a CBC and a "
                        "liver panel."),
    "lipi": ("routine", "LDH and a differential white count, with the local "
                        "upper limit of normal."),
    "lipi_prognosis": ("routine", "Same two values as the response model."),
    "cha2ds2_vasc": ("routine", "Age, sex and five coded diagnoses."),
    "score2": ("routine", "Age, sex, blood pressure, cholesterol, smoking "
                          "status, plus the ESC risk region, which is a "
                          "property of the site rather than the patient."),
    "prevent": ("routine", "Age, sex, lipids, blood pressure, eGFR, BMI and "
                           "coded diabetes, smoking and medication. The three "
                           "extended predictors (UACR, HbA1c, deprivation "
                           "index) are optional and select a variant."),
    "cvd_statin_benefit": ("routine", "Takes another model's output plus an "
                                      "intended LDL reduction; no patient "
                                      "fields of its own."),
    "grace": ("routine", "Everything an acute coronary syndrome admission "
                         "already documents: vitals, creatinine, troponin, and "
                         "the ECG and Killip assessment from the admission "
                         "note."),
    "endpac": ("routine", "Two glucose values a year apart, weight change and "
                          "age, all of it longitudinal EHR data, which is "
                          "unusual among these models and a good fit."),
    "kunzmann": ("routine", "Age, sex, BMI, coded smoking status and a coded "
                            "oesophageal diagnosis."),
    "erspc_rc3": ("routine", "PSA, prostate volume and the DRE finding."),
    "pbcg_extended": ("routine",
                      "Requires only age and PSA. The other ten predictors are "
                      "optional, and each pattern of them has its own fitted "
                      "sub-model, 1,024 in all, so a record missing family "
                      "history is scored by the model fitted without it rather "
                      "than by imputing one. This is the design an EHR "
                      "deployment wants."),

    # ---- specialty: a cancer centre has it, a clinic may not ----------
    "hap": ("specialty", "Albumin, bilirubin and AFP are routine; the dominant "
                         "tumour diameter comes from an imaging report."),
    "capra": ("specialty", "PSA and age are routine; Gleason grades, T stage "
                           "and percent positive cores come from the pathology "
                           "report."),
    "msk_gastric": ("specialty", "Staging and pathology detail: Lauren type, "
                                 "depth of invasion, and counts of positive AND "
                                 "negative nodes, the negative count is often "
                                 "missing even where the positive one is "
                                 "recorded."),
    "msk_pancreatic": ("specialty", "Fourteen operative and pathology fields, "
                                    "including margin status, splenectomy and "
                                    "portal vein resection. All in an operative "
                                    "note; few are structured."),
    "msk_rectal": ("specialty", "Post-treatment pathology: ypT stage, node "
                                "count, venous and perineural invasion."),
    "msk_ovarian": ("specialty", "Grade, histology, platelets and residual "
                                 "disease diameter, plus ascites, the last two "
                                 "from the operative note."),
    "predict_breast": ("specialty", "Tumour size, node count, grade, ER, HER2 "
                                    "and Ki-67 from pathology, plus which "
                                    "adjuvant treatments were given."),
    "predict_breast_response": ("specialty", "Same fields as the prognosis "
                                             "model, which it runs twice."),
    "roma": ("specialty", "CA-125 is routine; HE4 is a send-out assay and is "
                          "platform-specific, and the ultrasound score comes "
                          "from a radiology report."),
    "rmi": ("specialty", "Same ultrasound score and CA-125, plus menopausal "
                         "status."),
    "abc_method": ("specialty", "Pepsinogen I and the I/II ratio with H. pylori "
                                "serology. Routine screening in Japan, rarely "
                                "ordered elsewhere."),
    "cervical_cin_risk": ("specialty", "hrHPV result and cytology grade, "
                                       "optionally HPV genotyping and E6. "
                                       "Available where the screening programme "
                                       "runs, absent otherwise."),

    # ---- not_ehr: questionnaire and patient-reported -------------------
    "crc_pro": ("not_ehr",
                "Years of education, pack-years, drinks per day, and for men "
                "ounces of red meat and hours of activity per day. These are "
                "cohort-study questionnaire items; no health record holds "
                "them."),
    "dutasteride": ("not_ehr",
                    "Sexual activity, history of impotence and of libido "
                    "problems, IPSS symptom score, maximum urinary flow and "
                    "post-void residual volume. Urology questionnaires and "
                    "urodynamics, not routine records."),
    "plcom2012": ("not_ehr",
                  "Education level, and pack-years split into cigarettes per "
                  "day, duration and years since quitting. Most EHRs code "
                  "smoking as a status, not as those three numbers."),
    "bcrat": ("not_ehr",
              "Age at menarche, age at first live birth, number of "
              "first-degree relatives with breast cancer and number of prior "
              "biopsies, a reproductive and family history interview."),
    "ang2010_rpa": ("not_ehr",
                    "HPV status and stage are specialty data, but the rule "
                    "turns on a pack-years threshold, and pack-years as a "
                    "number is rarely recorded."),
}

#: Signatures that were in the code but never in the registry, so every table
#: built from the registry showed these models with no inputs at all.
MISSING_INPUTS = {
    "bcrat": ["start_age", "end_age", "n_biopsies", "age_menarche",
              "age_first_birth", "n_relatives", "race (optional)",
              "atypical_hyperplasia (optional)"],
    "predict_breast_response": [
        "age", "size_mm", "nodes", "grade", "er_positive", "her2 (optional)",
        "ki67 (optional)", "screen_detected (optional)",
        "chemo_generation (optional)", "hormone (optional)",
        "extended_hormone (optional)", "trastuzumab (optional)",
        "bisphosphonate (optional)", "years (optional)"],
    "ang2010_rpa": ["hpv_positive", "pack_years", "n_stage", "t_stage",
                    "definition (optional)"],
    "lipi_prognosis": ["ldh", "ldh_upper_limit_normal", "dnlr (optional)",
                       "neutrophils (optional)", "leukocytes (optional)"],
    "rmi": ["ultrasound_score", "postmenopausal", "ca125", "variant (optional)",
            "max_diameter_cm (optional)"],
}

TIERS = ("routine", "specialty", "not_ehr")


def main() -> None:
    p = pathlib.Path("registry/models.yaml")
    d = yaml.safe_load(p.read_text())
    by_id = {m["id"]: m for m in d["models"]}

    impl = [m for m in d["models"] if m.get("status") == "implemented"]
    missing = {m["id"] for m in impl} - set(EHR)
    assert not missing, f"implemented models with no EHR classification: {sorted(missing)}"

    for mid, values in MISSING_INPUTS.items():
        assert not by_id[mid].get("inputs"), f"{mid} already has inputs"
        by_id[mid]["inputs"] = values

    for mid, (tier, note) in EHR.items():
        assert tier in TIERS, tier
        by_id[mid]["ehr_availability"] = tier
        by_id[mid]["ehr_note"] = note

    save_models(d["models"], p)

    from collections import Counter
    c = Counter(EHR[m["id"]][0] for m in impl)
    print(f"classified {len(impl)} models, filled inputs for {len(MISSING_INPUTS)}")
    for tier in TIERS:
        ids = sorted(m["id"] for m in impl if EHR[m["id"]][0] == tier)
        print(f"  {tier:<10} {c[tier]:>2}  {', '.join(ids)}")


if __name__ == "__main__":
    main()
