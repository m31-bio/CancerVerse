# CancerVerse

**Published clinical risk equations, reimplemented in Python — and independently verified.**

`30 models` · `12 diseases` · `26/36 cells` · `29/30 verified` · `Apache-2.0`

Clinical risk models are scattered across paywalled PDFs, supplement images, dead
Flash calculators and hosted web forms. This repository collects them as running,
tested Python — with the provenance of every coefficient recorded, and with evidence
that each implementation reproduces an independent source.

```python
import mayo_baseline as mb

mb.predict("albi", bilirubin_umol_l=20.0, albumin_g_l=40.0)
# {'score': -2.54, 'grade': 2, 'registry_id': 'albi',
#  'citation': 'Johnson PJ et al. J Clin Oncol. 2015;33(6):550-558', ...}

[m.id for m in mb.list_models(disease="liver")]
# ['amap', 'hap', 'albi']

mb.model_info("crc_pro").required_inputs
# ('male', 'age', 'ethnicity', 'weight_lb', 'height_in', ...)

# one patient record, several models, each given only what it accepts
mb.predict_many(["albi", "amap"], age=55, male=True, platelets=200,
                bilirubin_umol_l=15.0, albumin_g_l=42.0)
```

Every result carries the model's `scope` — running a model is not the same as
being entitled to believe it. There is deliberately no "run everything"
convenience; see `mayo_baseline/api.py` for why.

---

> ### ⚠️ Not for clinical use
>
> This is a research artifact. It is **not a medical device**, has not been cleared or
> approved by any regulator, and must not be used to make decisions about a patient's
> care. Each model carries its own population and scope; applying one outside that
> scope produces a number that looks valid and is not.

---

## Coverage

Every disease is asked the same three questions. A dash means we have not implemented that cell. It does not mean the literature is empty: every one of the 36 cells has a published candidate, and each unfilled cell records the specific thing that blocks it -- a missing intercept, an unreachable supplement, inputs we do not take, or a model that is not a closed-form equation at all.

<table>
<thead><tr><th>Disease</th><th>Question</th><th>Model</th><th>Architecture</th><th>Architecture detail</th><th>Core formula</th><th>Year</th><th>Discrimination (AUC / C-index)</th><th>Developed on</th><th>Public repository</th><th>Source</th><th>Where the equation sits</th><th>Verified?</th><th>How it was verified</th><th>Re-run the check</th><th>Top predictor</th></tr></thead>
<tbody>
<tr><td rowspan="3" valign="top"><b>Breast cancer</b></td><td rowspan="1" valign="top">Prediction</td><td valign="top"><b>BCRAT / Gail model (absolute invasive breast cancer risk)</b></td><td valign="top"><b>Logistic regression</b></td><td valign="top">Relative risks fitted by conditional logistic regression, applied to race-specific baseline hazards and integrated year by year over the age interval against competing all-cause mortality, which is what converts them into an absolute risk.</td><td valign="top"><pre>A(t₁,t₂) = Σₐ [h₁(a) / (h₁(a)+h₂(a))] · e^(−Λ(a)) · [1 − e^(−(h₁(a)+h₂(a)))]

  h₁(a)  breast-cancer hazard  = RR(a) × race-specific baseline
  h₂(a)  competing all-cause mortality hazard
  Λ(a)   cumulative hazard up to age a
  a      runs year by year from t₁ to t₂</pre></td><td valign="top"><b>1989</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top"><a href="https://cran.r-project.org/package=BCRA">package=BCRA</a></td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/2593165/">PMID 2593165</a></td><td valign="top">Not a single printed equation. The relative-risk and baseline-hazard tables (SEER incidence, NCHS mortality) and the year-by-year competing-risk integration are as shipped in the CRAN package BCRA; the integration follows its absolute.risk.R.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 against CRAN BCRA 4 cases via absolute.risk(); worst absolute difference 3.7e-07 percentage points</td><td valign="top"><code>pytest tests/parity/test_r_reference_parity.py::test_bcrat_matches_cran_bcra</code></td><td valign="top">first-degree relatives</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td valign="top"><b>PREDICT Breast v2.2 — adjuvant treatment benefit</b></td><td valign="top"><b>Survival (parametric)</b></td><td valign="top">The same parametric survival model evaluated twice, treated and untreated; the difference in survival IS the predicted absolute treatment benefit.</td><td valign="top"><pre>benefit(t) = S_treated(t) − S_untreated(t)

  the same survival model evaluated twice; the difference IS the
  predicted absolute treatment benefit</pre></td><td valign="top"><b>2017</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top"><a href="https://github.com/WintonCentre/predictv30r">predictv30r</a></td><td valign="top"><a href="https://doi.org/10.1186/s13058-017-0852-3">doi:10.1186/s13058-017-0852-3</a></td><td valign="top">Same source as predict_breast (WintonCentre/predictv30r, R/benefits22.R). Absolute benefit is that model evaluated twice, so there is no separate published equation for the response cell.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 — same model and same R comparison as predict_breast.</td><td valign="top"><code>pytest tests/parity/test_r_reference_parity.py::test_predict_treatment_benefit_er_positive_10y</code></td><td valign="top">chemotherapy generation and ER status</td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td valign="top"><b>PREDICT Breast v2.2 (prognosis + adjuvant treatment benefit)</b></td><td valign="top"><b>Survival (parametric)</b></td><td valign="top">Parametric survival model with a closed-form log-cumulative-hazard in time, plus additive treatment log-hazard-ratios, one per therapy arm.</td><td valign="top"><pre>S(t) = exp( −H₀(t) · e^PI )

  PI    = Σ βᵢxᵢ  +  Σ log(HR) over the treatments given
  H₀(t) closed form in t, separately for ER+ and ER−</pre></td><td valign="top"><b>2017</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top"><a href="https://github.com/WintonCentre/predictv30r">predictv30r</a></td><td valign="top"><a href="https://doi.org/10.1186/s13058-017-0852-3">doi:10.1186/s13058-017-0852-3</a></td><td valign="top">NOT IN THE PAPER as a closed form. Taken from the MIT-licensed reference implementation WintonCentre/predictv30r, R/benefits22.R -- note this is the UNEXPORTED overall-survival function; the exported benefits222 computes disease-free survival and is a different model.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 against predictv30r:::benefits22 (the UNEXPORTED overall-survival function; the exported benefits222 computes disease-free survival and must not be used)</td><td valign="top"><code>pytest tests/parity/test_r_reference_parity.py::test_predict_untreated_survival_er_positive</code></td><td valign="top">tumour size, nodes and grade, then treatment</td></tr>
<tr><td rowspan="5" valign="top"><b>Cardiovascular disease</b></td><td rowspan="2" valign="top">Prediction</td><td valign="top"><b>AHA PREVENT — all 5 variants (base/uacr/hba1c/sdi/full) x 10y/30y x 5 outcomes</b></td><td valign="top"><b>Logistic regression</b></td><td valign="top">Sex-specific logistic regressions with age-centred predictors and interaction terms; 100 fixed coefficient sets (5 variants x 2 horizons x 5 outcomes x 2 sexes).</td><td valign="top"><pre>logit(p) = Σ βᵢxᵢ

  one of 100 coefficient sets:
    5 variants × 2 horizons × 5 outcomes × 2 sexes
  continuous predictors are age-centred; several enter as interactions</pre></td><td valign="top"><b>2024</b></td><td valign="top">C-statistic 0.794 (women) and 0.757 (men) for CVD, external validation</td><td valign="top">46 datasets, 3,281,919 individuals (AHA PREVENT development)</td><td valign="top"><a href="https://github.com/martingmayer/preventr">preventr</a></td><td valign="top"><a href="https://doi.org/10.1161/CIRCULATIONAHA.123.067626">doi:10.1161/CIRCULATIONAHA.123.067626</a></td><td valign="top">Supplemental appendix, all 100 coefficient sets; the base 10-year worked example is Table S25. Circulation 2024.</td><td valign="top"><b>Yes</b></td><td valign="top">matched applies to the base 10-year model only (Table S25)</td><td valign="top"><code>pytest tests/parity/test_canonical_parity.py::test_prevent_supplemental_table_s25_vignette</code></td><td valign="top">age</td></tr>
<tr><td valign="top"><b>ESC SCORE2</b></td><td valign="top"><b>Survival (Cox)</b></td><td valign="top">Cox proportional hazards: 1 - S0^exp(sum of beta*x), followed by a region-specific recalibration on the complementary log-log scale.</td><td valign="top"><pre>risk_uncal = 1 − S₀^exp(Σβx)

  risk       = 1 − exp( −exp( a + b · ln(−ln(1 − risk_uncal)) ) )
  a, b       region-specific recalibration constants (4 ESC risk regions)</pre></td><td valign="top"><b>2021</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top"><a href="https://cran.r-project.org/package=RiskScorescvd">package=RiskScorescvd</a></td><td valign="top"><a href="https://doi.org/10.1093/eurheartj/ehab309">doi:10.1093/eurheartj/ehab309</a></td><td valign="top">Not in the main text: the article says 'Details of statistical analysis are provided in Supplementary material online, Methods', and the coefficients, baseline survival and the four risk-region recalibration constants live there rather than in a numbered main table.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 against CRAN RiskScorescvd::SCORE2 (MIT) across all four ESC risk regions; agreement within that package's own 1-decimal rounding (it ends in round(x,1))</td><td valign="top"><code>pytest tests/parity/test_r_reference_parity.py::test_score2_matches_riskscorescvd</code></td><td valign="top">age</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td valign="top"><b>LDL-lowering absolute benefit (DERIVED: CTT trial effect x a baseline risk)</b></td><td valign="top"><b>Derived composition</b></td><td valign="top">Not a fitted model. A published trial rate ratio raised to the LDL reduction and applied multiplicatively to a baseline absolute risk from another model, yielding absolute risk reduction and number needed to treat.</td><td valign="top"><pre>ARR = baseline_risk × ( 1 − RR^ΔLDL )

  NNT = 1 / ARR
  RR  = 0.78 per 1.0 mmol/L LDL-C reduction   (CTT 2010)
        0.90 for all-cause mortality
  baseline_risk comes from a separate, verified model</pre></td><td valign="top"><b>2010</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top">CTT 2010: 26 randomised trials, 169,138 participants, median follow-up 4.8-5.1 years</td><td valign="top">&mdash;</td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/21067804/">PMID 21067804</a></td><td valign="top">There is no source paper for this model because it is not a published prediction model -- it is a composition this project defined from two published quantities (a CTT 2010 rate ratio and a separately verified baseline risk). The rate ratio's location in CTT 2010 is the only paper citation that applies.</td><td valign="top">No</td><td valign="top">NOT VERIFIABLE BY COMPARISON, and deliberately not claimed to be</td><td valign="top"><code>pytest tests/test_cvd_response_statin_benefit.py::test_rate_ratios_are_the_published_ctt_values</code></td><td valign="top">&mdash;</td></tr>
<tr><td rowspan="2" valign="top">Prognosis</td><td valign="top"><b>GRACE 2003 in-hospital mortality score (acute coronary syndromes)</b></td><td valign="top"><b>Points table</b></td><td valign="top">Points nomogram: each of 8 predictors is banded and mapped to integer points; the total indexes a published mortality table.</td><td valign="top"><pre>total = Σ points( Killip, SBP, heart rate, age, creatinine,
                  cardiac arrest, ST deviation, cardiac enzymes )

  total → published in-hospital mortality, by lookup</pre></td><td valign="top"><b>2003</b></td><td valign="top">C-statistic 0.83 derivation, 0.84 confirmation GRACE, 0.79 GUSTO-IIb</td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/14581255/">PMID 14581255</a></td><td valign="top">Figure 4, the nomogram, plus the points-to-mortality lookup. Arch Intern Med 2003;163(19):2345-2353. Section not captured.</td><td valign="top"><b>Yes</b></td><td valign="top">both published worked examples reproduce component-by-component</td><td valign="top"><code>pytest tests/parity/test_canonical_parity.py::test_grace_published_worked_examples</code></td><td valign="top">age</td></tr>
<tr><td valign="top"><b>CHA2DS2-VASc (stroke risk in atrial fibrillation)</b></td><td valign="top"><b>Points table</b></td><td valign="top">Additive integer point score (0-9): one or two points per clinical feature, summed.</td><td valign="top"><pre>score = C + H + 2·A₂ + D + 2·S₂ + V + A + Sc      (0–9)

  C  congestive heart failure      S₂ prior stroke / TIA        (2 points)
  H  hypertension                  V  vascular disease
  A₂ age ≥ 75                      A  age 65–74
  D  diabetes                      Sc female sex</pre></td><td valign="top"><b>2010</b></td><td valign="top">C-statistic 0.606 — modest, and lower than several alternatives</td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/19762550/">PMID 19762550</a></td><td valign="top">Chest 2010;137(2):263-272, the point list. Cross-checked against MDCalc's published schema. Table number not captured.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 against MDCalc's published point schema: age <65/65-74/>=75 = 0/1/2, female 1, CHF 1, hypertension 1, stroke 2, vascular 1, diabetes 1</td><td valign="top"><code>pytest tests/parity/test_r_reference_parity.py::test_cha2ds2_vasc_point_table_matches_mdcalc</code></td><td valign="top">age</td></tr>
<tr><td rowspan="3" valign="top"><b>Cervical cancer</b></td><td rowspan="1" valign="top">Prediction</td><td valign="top"><b>Cervical CIN2+/CIN3+ logistic models (hrHPV + cytology + age)</b></td><td valign="top"><b>Logistic regression</b></td><td valign="top">Multivariable logistic regression on hrHPV status, cytology grade and age (optionally E6 oncoprotein) to CIN2+/CIN3+ probability.</td><td valign="top"><pre>logit(p) = β₀ + β_hrHPV·hrHPV + β_cytology + β_age·age
             [ + β_E6·E6 + Σ β_genotype ]

  cytology  7 levels, NILM is the reference and carries no term
  variants  base / +E6 / +genotyping / +both</pre></td><td valign="top"><b>2021</b></td><td valign="top">AUC 0.91 (95% CI 0.88-0.93) for CIN2+, base model, cross-sectional validation set</td><td valign="top">Chinese screening population: cross-sectional N=1,915, plus two screening cohorts of 3,179 and 3,082</td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1186/s12916-021-02078-2">doi:10.1186/s12916-021-02078-2</a></td><td valign="top">Additional file 1, 'Table S1. - Logistic Regression Parameters'. Main text describes the model under Methods, 'Model development'.</td><td valign="top"><b>Yes</b></td><td valign="top">The paper publishes no worked example, no calibration table and no predicted-vs-observed cross-tabulation (checked)</td><td valign="top"><code>pytest tests/parity/test_cervical_cin_parity.py::test_every_coefficient_matches_table_s1_exactly</code></td><td valign="top">cytology grade</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="3" valign="top"><b>Colorectal cancer</b></td><td rowspan="1" valign="top">Prediction</td><td valign="top"><b>CRC-PRO (10-year colorectal cancer risk, Multi-Ethnic Cohort)</b></td><td valign="top"><b>Survival (Cox)</b></td><td valign="top">Two sex-specific Cox models with different predictor sets, each with restricted cubic splines on five or seven continuous predictors; risk is 1 - S0^exp(Xb) at a fixed 10-year horizon.</td><td valign="top"><pre>risk(10y) = 1 − S₀^exp(Xβ)

  S₀   = 0.9901043  (women)
         0.9846654  (men)
  Xβ   separate models per sex with DIFFERENT predictor sets
  splines on age, education, pack-years, BMI, alcohol
         (+ red meat and activity in men)</pre></td><td valign="top"><b>2014</b></td><td valign="top">Cross-validated C-statistic 0.681 (men), 0.679 (women)</td><td valign="top">Multi-Ethnic Cohort Study</td><td valign="top"><a href="https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/ColorectalCancer">ColorectalCancer</a></td><td valign="top"><a href="https://doi.org/10.3122/jabfm.2014.01.130040">doi:10.3122/jabfm.2014.01.130040</a></td><td valign="top">Table 5A 'Coefficients for the Model Predicting Colorectal Cancer in Men' and Table 5B, the same for women. NOTE: the baseline survival values this library uses (0.9901043 women, 0.9846654 men) are NOT in the paper -- they come from the vendor's R source at ClevelandClinicQHS/riskcalc-website/ColorectalCancer. The paper never states the risk equation 1 - S0^exp(Xb) either; it shows nomograms.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-06 against the vendor's own deployed R, route 1</td><td valign="top"><code>pytest tests/parity/test_crc_pro_parity.py::test_matches_the_vendor_r_when_emulating_its_defect</code></td><td valign="top">age</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td valign="top"><b>MSK rectal calculator (RFS + OS after CRT and surgery)</b></td><td valign="top"><b>Survival (Cox)</b></td><td valign="top">Cox proportional hazards with restricted cubic splines on age and positive-node count; survival is S0(t)^exp(X*beta) at four published follow-up times.</td><td valign="top"><pre>P(T ≥ t) = S₀(t)^exp(Xβ)

  S₀(t) published only at t = 0, 60, 120, 180 months
  Xβ    restricted cubic splines on age and positive-node count
  RFS and OS use DIFFERENT ypT reference groups</pre></td><td valign="top"><b>2021</b></td><td valign="top">C-index 0.70 (95% CI 0.65-0.76) RFS and 0.73 (0.65-0.80) OS, internal validation; 0.71 and 0.72 external</td><td valign="top">710 patients, Memorial Sloan Kettering, 1998-2014; externally validated at Siteman Cancer Center</td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1001/jamanetworkopen.2021.33457">doi:10.1001/jamanetworkopen.2021.33457</a></td><td valign="top">Supplement 1: the eTable 'Parameter Estimates for Cox Regression Models Predicting RFS and OS' holds the coefficients, and the eFigure 'Predictive Equations for Incomplete Responders for RFS and OS' holds the assembled linear predictors. Main text describes it under 'Development of Clinical Calculators'. Which of the two governs was itself a defect in this project -- settled against MSK's live calculator in favour of the eFigure.</td><td valign="top"><b>Yes</b></td><td valign="top">No worked example is published, so parity was established against MSK's own hosted deployment of this model (mskcc.org/nomograms/rectal/post-treatment, whose Supporting Publication block cites this exact paper)</td><td valign="top"><code>pytest tests/parity/test_msk_rectal_parity.py::test_matches_the_hosted_msk_calculator</code></td><td valign="top">age</td></tr>
<tr><td rowspan="3" valign="top"><b>Esophageal cancer</b></td><td rowspan="1" valign="top">Prediction</td><td valign="top"><b>Kunzmann points model (esophageal adenocarcinoma)</b></td><td valign="top"><b>Points table</b></td><td valign="top">Points model derived from a stepwise logistic regression, with each coefficient divided by the smallest one, so the integer points ARE the model rather than a lossy summary.</td><td valign="top"><pre>points = Σ round_to_half( βᵢ / 0.40 )      (0–15)

  over age, sex, BMI, smoking, oesophageal condition
  refer for screening if points ≥ 8</pre></td><td valign="top"><b>2018</b></td><td valign="top">AUROC 0.80 (95% CI 0.77-0.82); 0.79 internally validated</td><td valign="top">UK Biobank; 355,034 participants aged 50+, 220 oesophageal adenocarcinomas within 5 years</td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1016/j.cgh.2018.03.014">doi:10.1016/j.cgh.2018.03.014</a></td><td valign="top">Table 2, the points-based model. The points are the fitted coefficients divided by the smallest and rounded to the nearest 0.5 -- the divisor is stated as 0.41 but is provably 0.40 (see the parity test). Section heading not captured.</td><td valign="top"><b>Yes</b></td><td valign="top">No worked patient is published and the full text is paywalled, so this was the last model blocked on paper access; the PDF was supplied 2026-08-06</td><td valign="top"><code>pytest tests/parity/test_kunzmann_parity.py::test_every_published_point_is_re_derivable_from_its_odds_ratio</code></td><td valign="top">male sex</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="3" valign="top"><b>Gastric cancer</b></td><td rowspan="1" valign="top">Prediction</td><td valign="top"><b>ABC method (H. pylori antibody x pepsinogen serological groups A-D)</b></td><td valign="top"><b>Categorical rule</b></td><td valign="top">A 2x2 cross-tabulation, not a regression: H. pylori serology (+/-) crossed with pepsinogen-defined atrophy (+/-) gives 4 ordered groups A-D.</td><td valign="top"><pre>group = H. pylori antibody (±)  ×  pepsinogen atrophy (±)

  atrophy = PG I ≤ 70 ng/mL  AND  PG I / PG II ≤ 3.0
  → groups A, B, C, D, each with a published annual incidence</pre></td><td valign="top"><b>2005</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1136/gut.2004.055400">doi:10.1136/gut.2004.055400</a></td><td valign="top">Methods, subsection 'Serum pepsinogen level' defines atrophy (PG I <=70 ng/mL AND PG I/II <=3.0); Methods, subsection 'Classification by anti-H pylori antibody and serum pepsinogen status' defines groups A-D; the per-group annual incidence rates are in Table 2.</td><td valign="top"><b>Yes</b></td><td valign="top">incidence rates re-derived independently from the paper's own cases and person-years (Tables 1-2): 7/(3324*4.8y)=0.044%/y, 6/(2134*4.7y)=0.060%/y, 18/(1082*4.7y)=0.354%/y, 12/(443*4.5y)=0.602%/y — each reproduces the published rate</td><td valign="top"><code>pytest tests/test_gastric_detection_abc_method.py::test_group_and_rate_match_watabe_table_2</code></td><td valign="top">pepsinogen atrophy</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td valign="top"><b>MSK gastric nomogram (disease-specific survival after R0 resection)</b></td><td valign="top"><b>Survival (Cox)</b></td><td valign="top">Cox proportional hazards with restricted cubic splines on age, positive nodes, negative nodes and depth of invasion; depth is an ordinal 1-7 entered as a continuous splined term, not as indicators.</td><td valign="top"><pre>DSS(t) = S₀(t)^exp(Xβ)

  S₀ = 0.579053   at 5 years
       0.5089101  at 9 years
  Xβ   splines on age, positive nodes, negative nodes, depth
  references: female, Lauren diffuse, antrum/pyloric</pre></td><td valign="top"><b>2003</b></td><td valign="top">Concordance index 0.80, bootstrap-corrected</td><td valign="top">Memorial Sloan Kettering gastric resection series</td><td valign="top"><a href="https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/GastricCancer">GastricCancer</a></td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/14512396/">PMID 14512396</a></td><td valign="top">NOT IN THE PAPER as a closed form: J Clin Oncol 2003;21(19) prints a nomogram figure only. Coefficients from ClevelandClinicQHS/riskcalc-website/tree/main/GastricCancer (server.R), with S0 at 5 years (0.579053) and 9 years (0.5089101).</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-06 against the vendor's own deployed R, route 1</td><td valign="top"><code>pytest tests/parity/test_msk_gastric_parity.py::test_matches_the_vendor_r</code></td><td valign="top">positive nodes</td></tr>
<tr><td rowspan="3" valign="top"><b>Head & neck cancer</b></td><td rowspan="1" valign="top">Prediction</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="1" valign="top">Response</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td valign="top"><b>Ang 2010 RPA risk groups (HPV / smoking / stage, oropharynx)</b></td><td valign="top"><b>Decision tree</b></td><td valign="top">Recursive-partitioning (CART) decision tree: three binary splits on HPV status, pack-years and nodal/tumour stage produce 3 risk groups.</td><td valign="top"><pre>HPV+ ─┬─ ≤10 pack-years ─────────────→ low
      └─ &gt;10 ─┬─ N0–N2a ────────────→ low
              └─ N2b–N3 ───────────→ intermediate

HPV− ─┬─ ≤10 pack-years, T2–T3 ────→ intermediate
      └─ otherwise ────────────────→ high</pre></td><td valign="top"><b>2010</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1056/NEJMoa0912217">doi:10.1056/NEJMoa0912217</a></td><td valign="top">Results, subsection 'HPV status and survival', stated as prose and drawn as the recursive-partitioning tree in Figure 2. No table.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 against Fakhry et al. external validation (Cancer 2019;125:2027-2038, PMC6594017), which operationalizes the same risk groups</td><td valign="top"><code>pytest tests/test_head_neck_prognosis_ang2010.py::test_the_two_operationalizations_differ_only_for_hpv_negative_t1</code></td><td valign="top">HPV status</td></tr>
<tr><td rowspan="3" valign="top"><b>Liver cancer</b></td><td rowspan="1" valign="top">Prediction</td><td valign="top"><b>aMAP score (5-year HCC risk in chronic hepatitis)</b></td><td valign="top"><b>Linear score + cut-offs</b></td><td valign="top">Linear score on age, sex, ALBI and platelets, rescaled onto 0-100 and banded at 50 and 60; it embeds the whole ALBI score as one term.</td><td valign="top"><pre>aMAP = ( 0.06·age + 0.89·male + 0.48·ALBI − 0.01·platelets + 7.4 )
       ─────────────────────────────────────────────────────────── × 100
                                14.77

  ALBI = 0.66·log₁₀(bilirubin) − 0.085·albumin
  bands: &lt;50 low, 50–60 medium, ≥60 high</pre></td><td valign="top"><b>2020</b></td><td valign="top">C-index 0.82–0.87 across aetiologies and ethnicities</td><td valign="top">11 global prospective cohorts, 17,374 patients with chronic hepatitis</td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1016/j.jhep.2020.07.025">doi:10.1016/j.jhep.2020.07.025</a></td><td valign="top">The aMAP formula and the 50/60 cut-offs, J Hepatol 2020;73(6):1368-1378 (open access). Exact section heading not captured.</td><td valign="top"><b>Yes</b></td><td valign="top">No numeric worked example is published, so parity was established against the custodial calculator hosted by CUHK's Medical Data Analytics Centre, an aMAP collaborating site (mdac.cuhk.edu.hk/calculators/amap/)</td><td valign="top"><code>pytest tests/parity/test_amap_parity.py::test_score_matches_the_custodial_calculator</code></td><td valign="top">age</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td valign="top"><b>HAP score (pre-TACE prognosis / candidacy)</b></td><td valign="top"><b>Points table</b></td><td valign="top">Additive integer point score (0-4) from 4 dichotomised variables, mapped to 4 prognostic grades.</td><td valign="top"><pre>points = [albumin &lt; 36 g/L] + [bilirubin &gt; 17 µmol/L]
       + [AFP &gt; 400 ng/mL] + [dominant tumour &gt; 7 cm]

  0 → grade A,  1 → B,  2 → C,  &gt;2 → D</pre></td><td valign="top"><b>2013</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/23857958/">PMID 23857958</a></td><td valign="top">Point rule (albumin <36 g/L, bilirubin >17 umol/L, AFP >400 ng/mL, dominant tumour >7 cm; grades A-D), Ann Oncol 2013;24(10):2565-2570. Exact table/section not captured.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 against an independent statement of the score (interventionalradio.org/hap-score): same four criteria and thresholds, same A/B/C/D mapping with D as >2, same median survivals 27.6/18.5/9.0/3.6 months</td><td valign="top"><code>pytest tests/test_liver_response_hap.py::test_each_criterion_contributes_exactly_one_point</code></td><td valign="top">albumin < 36 g/L</td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td valign="top"><b>ALBI grade (albumin-bilirubin liver function)</b></td><td valign="top"><b>Linear score + cut-offs</b></td><td valign="top">Two-term linear score, log10(bilirubin) and albumin, cut at two fixed thresholds into 3 liver-function grades.</td><td valign="top"><pre>ALBI = 0.66 · log₁₀(bilirubin µmol/L)  −  0.085 · albumin g/L

  grade 1  ALBI ≤ −2.60
  grade 2  −2.60 &lt; ALBI ≤ −1.39
  grade 3  ALBI &gt; −1.39</pre></td><td valign="top"><b>2015</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1200/JCO.2014.57.9151">doi:10.1200/JCO.2014.57.9151</a></td><td valign="top">Results, in the multivariable Cox paragraph, printed inline as 'linear predictor = (log10 bilirubin x 0.66) + (albumin x -0.085)'. The grade cut-offs follow immediately in the same paragraph: 'xb <= -2.60 (ALBI grade 1), more than -2.60 to <= -1.39 (ALBI grade 2), and xb more than -1.39 (ALBI grade 3)'. Table 2 carries the underlying Cox parameters.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 against the primary text (PMC4322258), which prints verbatim: linear predictor = (log10 bilirubin x 0.66) + (albumin x -0.085), grades at -2.60 / -1.39</td><td valign="top"><code>pytest tests/parity/test_r_reference_parity.py::test_albi_formula_matches_mdcalc_statement</code></td><td valign="top">albumin</td></tr>
<tr><td rowspan="3" valign="top"><b>Lung cancer</b></td><td rowspan="1" valign="top">Prediction</td><td valign="top"><b>PLCOm2012 (6-year lung-cancer risk, ever-smokers)</b></td><td valign="top"><b>Logistic regression</b></td><td valign="top">Multivariable logistic regression on 11 predictors (smoking history, COPD, family history, education, BMI, race) to 6-year lung-cancer probability.</td><td valign="top"><pre>logit(p) = β₀ + Σ βᵢ (xᵢ − centreᵢ)

  11 predictors: age, race, education, BMI, COPD, personal and
  family cancer history, smoking status, intensity, duration,
  years since quitting</pre></td><td valign="top"><b>2013</b></td><td valign="top">AUC 0.803 development, 0.797 validation</td><td valign="top"><em>not recorded yet</em></td><td valign="top"><a href="https://github.com/resplab/PLCOm2012">PLCOm2012</a></td><td valign="top"><a href="https://doi.org/10.1056/NEJMoa1211776">doi:10.1056/NEJMoa1211776</a></td><td valign="top">Table 2, 'Modified Logistic-Regression Prediction Model (PLCOm2012) of Cancer Risk for 36,286 Control Participants Who Had Ever Smoked' -- coefficients and the model constant (-4.532506) in its last row. The logit-to-probability step is in Table 2's footnote. Described in the main text under 'Modified PLCO lung-cancer risk-prediction model (PLCOm2012)'.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED against the canonical R package resplab/PLCOm2012, using its README worked example (62 y, White, education 4, BMI 27, former smoker, 80 cigarettes/day for 27 years, quit 10 years ago): ours 0.017509223 vs 0.01750922 — agreement to 8 decimal places.</td><td valign="top"><code>pytest tests/parity/test_canonical_parity.py::test_plcom2012_resplab_worked_example</code></td><td valign="top">age</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td valign="top"><b>LIPI (Lung Immune Prognostic Index, ICI outcomes)</b></td><td valign="top"><b>Points table</b></td><td valign="top">Two-item binary index: derived neutrophil-lymphocyte ratio >3 and LDH above the upper limit of normal each score 1, giving 3 risk groups.</td><td valign="top"><pre>score = [dNLR &gt; 3] + [LDH &gt; ULN]      (0–2)

  dNLR = neutrophils / (leukocytes − neutrophils)
  0 good · 1 intermediate · 2 poor</pre></td><td valign="top"><b>2018</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/29327044/">PMID 29327044</a></td><td valign="top">A two-item definition rather than a fitted equation; no coefficient table to locate.</td><td valign="top"><b>Yes</b></td><td valign="top">No worked example exists — LIPI is a two-item binary index, so there is no arithmetic to reproduce beyond the rule itself</td><td valign="top"><code>pytest tests/parity/test_lipi_parity.py::test_every_cell_of_the_published_truth_table</code></td><td valign="top">dNLR > 3</td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td valign="top"><b>LIPI (prognostic use in advanced NSCLC)</b></td><td valign="top"><b>Points table</b></td><td valign="top">The same two-item binary index, applied prognostically in advanced NSCLC rather than to immunotherapy response.</td><td valign="top"><pre>score = [dNLR &gt; 3] + [LDH &gt; ULN]      (0–2)

  the same index, used prognostically rather than to predict
  immunotherapy benefit</pre></td><td valign="top"><b>2018</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/29327044/">PMID 29327044</a></td><td valign="top">Same two-item definition as the response cell.</td><td valign="top"><b>Yes</b></td><td valign="top">No worked example exists — LIPI is a two-item binary index, so there is no arithmetic to reproduce beyond the rule itself</td><td valign="top"><code>pytest tests/parity/test_lipi_parity.py::test_the_prognosis_axis_registration_shares_this_model</code></td><td valign="top">dNLR and LDH equally</td></tr>
<tr><td rowspan="4" valign="top"><b>Ovarian cancer</b></td><td rowspan="2" valign="top">Prediction</td><td valign="top"><b>RMI 1-4 (Risk of Malignancy Index, adnexal triage)</b></td><td valign="top"><b>Multiplicative index</b></td><td valign="top">A product, not a sum: ultrasound feature score x menopausal-status score x serum CA125, compared against a single threshold.</td><td valign="top"><pre>RMI = U × M × CA-125           (RMI 4 adds × S)

  U  ultrasound feature score
  M  menopausal status score
  S  tumour-size score, RMI 4 only
  refer above 200 (RMI 1–3) or 450 (RMI 4)</pre></td><td valign="top"><b>1990</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1111/j.1471-0528.1990.tb02448.x">doi:10.1111/j.1471-0528.1990.tb02448.x</a></td><td valign="top">Four separate papers, one per RMI version (Jacobs 1990, Tingulstad 1996 and 1999, Yamamoto 2009). Per-paper locations not captured.</td><td valign="top"><b>Yes</b></td><td valign="top">exact integer arithmetic (U x M x CA125) with no fitted coefficients; all four variants' scoring rules verified against their respective derivation papers</td><td valign="top"><code>pytest tests/test_ovarian_detection_rmi.py::test_rmi1_worked_example</code></td><td valign="top">CA-125</td></tr>
<tr><td valign="top"><b>ROMA (Risk of Ovarian Malignancy Algorithm, HE4 + CA125)</b></td><td valign="top"><b>Logistic regression</b></td><td valign="top">Two menopause-stratified logistic regressions on ln(HE4) and ln(CA125); the stratum picks which of the two 3-coefficient models applies.</td><td valign="top"><pre>PI = a + b · ln(HE4) + c · ln(CA-125)

  p  = e^PI / (1 + e^PI)
  separate (a, b, c) and cut-off per menopausal status</pre></td><td valign="top"><b>2009</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1016/j.ygyno.2008.08.031">doi:10.1016/j.ygyno.2008.08.031</a></td><td valign="top">'Statistical Analysis' section, both indices printed inline: premenopausal PI = -12.0 + 2.38*LN(HE4) + 0.0626*LN(CA125); postmenopausal PI = -8.09 + 1.04*LN(HE4) + 0.732*LN(CA125). The PP thresholds (13.1% premenopausal, 27.7% postmenopausal) are in the same section.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 at the equation level</td><td valign="top"><code>pytest tests/test_ovarian_detection_roma.py::test_coefficients_corroborated_by_the_assay_insert</code></td><td valign="top">CA-125</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td valign="top"><b>MSK ovarian nomogram (5-year survival after primary surgery, bulky stage IIIC)</b></td><td valign="top"><b>Survival (Cox)</b></td><td valign="top">Cox proportional hazards with a restricted cubic spline on age; five-level residual-disease term whose reference is the MIDDLE category (0.5-1 cm).</td><td valign="top"><pre>S(5y) = 0.4284861^exp(Xβ)

  Xβ   spline on age, plus grade, histology, platelets, ascites
       and residual-disease diameter
  residual disease reference is 0.5–1 cm, the MIDDLE category</pre></td><td valign="top"><b>2008</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top">Memorial Sloan Kettering bulky stage IIIC series</td><td valign="top"><a href="https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/OvarianCancerPredictSurvivalAfterSurgforBulkyStageIIICCarc">OvarianCancerPredictSurvivalAfterSurgforBulkyStageIIICCarc</a></td><td valign="top"><a href="https://doi.org/10.1016/j.ygyno.2007.09.019">doi:10.1016/j.ygyno.2007.09.019</a></td><td valign="top">NOT IN THE PAPER as a closed form. Coefficients from ClevelandClinicQHS/riskcalc-website/tree/main/OvarianCancerPredictSurvivalAfterSurgforBulkyStageIIICCarc, which riskcalc.org's own page attributes to the cited publication.</td><td valign="top"><b>Yes</b></td><td valign="top">Route 1, CHECKED 2026-08-06 against the vendor's own deployed R: the reference script copies the model expression VERBATIM from riskcalc.org's server.R and runs it under R 4.6.1, so the comparison is against their arithmetic rather than our reading of it</td><td valign="top"><code>pytest tests/parity/test_msk_ovarian_parity.py::test_matches_the_vendor_r</code></td><td valign="top">age</td></tr>
<tr><td rowspan="3" valign="top"><b>Pancreatic cancer</b></td><td rowspan="1" valign="top">Prediction</td><td valign="top"><b>END-PAC (pancreatic cancer risk in new-onset diabetes)</b></td><td valign="top"><b>Points table</b></td><td valign="top">Additive integer point score from 3 terms: blood-glucose CATEGORY change, weight change over the year, and age at diabetes onset.</td><td valign="top"><pre>total = ΔBG_category + weight_score + age_score      (−6 … 11)

  ΔBG    category difference, NOT mg/dL   (1–4)
  weight LOSS scores positive             (−6 … +6)
  age    ≤59 → −1,  60–69 → 0,  ≥70 → +1
  ≥3 high risk · 1–2 intermediate · ≤0 extremely low</pre></td><td valign="top"><b>2018</b></td><td valign="top">AUROC 0.87 (discovery)</td><td valign="top">Rochester Epidemiology Project; discovery 64 pancreatic cancers vs 192 type 2 diabetes, validation 1,096 with 9 cancers (0.82%)</td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1053/j.gastro.2018.05.023">doi:10.1053/j.gastro.2018.05.023</a></td><td valign="top">Table 1, titled 'Enriching New-onset Diabetes for Pancreatic Cancer (END-PDAC) score parameters' -- note the table says END-PDAC, not END-PAC. Described under 'Patients and Methods'. The three risk-group cut-offs are never listed together in one sentence, which is the direct cause of this project's <0 versus <=0 ambiguity.</td><td valign="top"><b>Yes</b></td><td valign="top">No worked example exists and the only public calculator (endpacscore.com) no longer resolves, so parity was established on the primary source itself</td><td valign="top"><code>pytest tests/parity/test_endpac_parity.py::test_the_published_group_proportions_sum_to_one_hundred</code></td><td valign="top">weight change</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td colspan="14"><em>&mdash; not implemented</em></td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td valign="top"><b>MSK pancreatic nomogram (disease-specific survival after resection)</b></td><td valign="top"><b>Survival (Cox)</b></td><td valign="top">Cox proportional hazards with restricted cubic splines on positive-node count and tumour size, plus ten categorical and binary terms; three published horizons.</td><td valign="top"><pre>S(t) = S₀(t)^exp(Xβ)

  S₀ = 0.6775     at 12 months
       0.3457804  at 24 months
       0.1976732  at 36 months
  Xβ   splines on positive-node count and tumour size, plus ten
       categorical and binary terms; T stage is non-monotone</pre></td><td valign="top"><b>2004</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top">Memorial Sloan Kettering pancreatic resection series</td><td valign="top"><a href="https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/PancreaticCancer1YrSurvivalAfterResectionforAdenocarcinoma">PancreaticCancer1YrSurvivalAfterResectionforAdenocarcinoma</a></td><td valign="top"><a href="https://doi.org/10.1097/01.sla.0000133125.85489.07">doi:10.1097/01.sla.0000133125.85489.07</a></td><td valign="top">NOT IN THE PAPER as a closed form. Coefficients from ClevelandClinicQHS/riskcalc-website/tree/main/PancreaticCancer1YrSurvivalAfterResectionforAdenocarcinoma.</td><td valign="top"><b>Yes</b></td><td valign="top">Route 1, CHECKED 2026-08-06 against the vendor's own deployed R: the reference script copies the model expression VERBATIM from riskcalc.org's server.R and runs it under R 4.6.1, so the comparison is against their arithmetic rather than our reading of it</td><td valign="top"><code>pytest tests/parity/test_msk_pancreatic_parity.py::test_matches_the_vendor_r</code></td><td valign="top">T stage</td></tr>
<tr><td rowspan="4" valign="top"><b>Prostate cancer</b></td><td rowspan="2" valign="top">Prediction</td><td valign="top"><b>ERSPC RC3 (DRE-volume, biopsy-naïve)</b></td><td valign="top"><b>Logistic regression</b></td><td valign="top">Multivariable logistic regression: weighted sum of 3 predictors (log2 PSA, log2 prostate volume, DRE) pushed through a logistic link to a probability.</td><td valign="top"><pre>logit(p) = −1.826
           + 1.024 · (log₂ PSA − 2.0)
           − 1.500 · (log₂ volume_class − 5.4)
           + 0.992 · DRE</pre></td><td valign="top"><b>2012</b></td><td valign="top">AUC 0.61–0.77 across validation cohorts</td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://doi.org/10.1007/s00345-011-0804-y">doi:10.1007/s00345-011-0804-y</a></td><td valign="top">Appendix, under the heading 'Formulas used to calculate volume classes and the DRE ERSPC RC risks'. Printed there as lpDRE_ERSPC_riskcalc = -1.826 + 1.024 x (log2(PSA) - 2.0) - 1.50 x (log2(volumeclasses) - 5.4) + 0.992 x DRE, which matches this library's coefficients term for term.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 by extracting the coefficients from SWOP's own Flash calculator (/2011/swf/c03dre.swf)</td><td valign="top"><code>pytest tests/parity/test_r_reference_parity.py::test_erspc_rc3_coefficients_match_swop_flash_calculator</code></td><td valign="top">PSA</td></tr>
<tr><td valign="top"><b>PBCG (Prostate Biopsy Collaborative Group; no cancer / low grade / high grade)</b></td><td valign="top"><b>Logistic regression</b></td><td valign="top">Multinomial logistic regression over three outcomes (no cancer, Gleason 6, Gleason 7+), with eight fitted coefficient sets so a record missing prior biopsy, DRE or family history uses the model fitted without it rather than an imputed value.</td><td valign="top"><pre>S₁ = β_low · x        S₂ = β_high · x

  P(no cancer)  = 1 / (1 + e^S₁ + e^S₂)
  P(low grade)  = e^S₁ / (1 + e^S₁ + e^S₂)
  P(high grade) = e^S₂ / (1 + e^S₁ + e^S₂)

  x = [1, log₂PSA, age, African ancestry, + known optionals]
  one of 8 coefficient sets, by which optionals are known</pre></td><td valign="top"><b>2018</b></td><td valign="top">AUC 75.5% internal validation, 72.3% external (vs 72.3%/69.7% for PCPTRC 2.0)</td><td valign="top">15,611 men undergoing 16,369 biopsies at eight North American institutions 2006-2017; validated at three European institutions</td><td valign="top"><a href="https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/PBCG">PBCG</a></td><td valign="top"><a href="https://doi.org/10.1016/j.eururo.2018.05.003">doi:10.1016/j.eururo.2018.05.003</a></td><td valign="top">NOT IN THE PAPER as a closed form. The coefficients are in the deployed calculator's R source, ClevelandClinicQHS/riskcalc-website/tree/main/PBCG, as eight coefficient sets (one per missing-data pattern). Establishing this by parity against that source is what verified the model.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-06 against the vendor's own deployed R, route 1</td><td valign="top"><code>pytest tests/parity/test_pbcg_parity.py::test_matches_the_vendor_r</code></td><td valign="top">PSA</td></tr>
<tr><td rowspan="1" valign="top">Response</td><td valign="top"><b>Dutasteride chemoprevention (9 outcomes x 2 arms, benefit and harm)</b></td><td valign="top"><b>Survival (Cox)</b></td><td valign="top">Seventeen Cox sub-models: nine outcomes each predicted on and off dutasteride, with restricted cubic splines and per-outcome applicability bounds, so the reported quantity is the treated-minus-untreated difference rather than either risk.</td><td valign="top"><pre>risk = 1 − S₀^exp(score)        per outcome, per arm

  difference = on-drug − off-drug
               negative is benefit, positive is harm
  9 outcomes × 2 arms (ASAP has only the on-drug arm)</pre></td><td valign="top"><b>2013</b></td><td valign="top"><em>we have not read this from the paper yet</em></td><td valign="top">REDUCE trial: men with a prior negative 6- to 12-core prostate biopsy</td><td valign="top"><a href="https://github.com/ClevelandClinicQHS/riskcalc-website/tree/main/ProstateCancerConsideringDutasteride">ProstateCancerConsideringDutasteride</a></td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/23768723/">PMID 23768723</a></td><td valign="top">NOT IN THE PAPER as a closed form. 315 coefficients across 17 Cox sub-models, machine-extracted from ClevelandClinicQHS/riskcalc-website/tree/main/ProstateCancerConsideringDutasteride by tests/parity/reference/dutasteride_extract.py.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-06 against the vendor's own deployed R, route 1</td><td valign="top"><code>pytest tests/parity/test_dutasteride_parity.py::test_matches_the_vendor_r</code></td><td valign="top">&mdash;</td></tr>
<tr><td rowspan="1" valign="top">Prognosis</td><td valign="top"><b>UCSF-CAPRA (preoperative recurrence risk)</b></td><td valign="top"><b>Points table</b></td><td valign="top">Additive integer point score (0-10) distilled from a Cox model; at prediction time it is table lookup and addition, with no regression evaluated.</td><td valign="top"><pre>total = PSA + Gleason + T-stage + %positive-cores + age   (0–10)

  PSA      2.1–6 → 0, 6.1–10 → 1, 10.1–20 → 2, 20.1–30 → 3, &gt;30 → 4
  Gleason  0, 1 or 3 — there is no 2-point level
  0–2 low · 3–5 intermediate · 6–10 high</pre></td><td valign="top"><b>2005</b></td><td valign="top">Concordance index 0.66</td><td valign="top"><em>not recorded yet</em></td><td valign="top">&mdash;</td><td valign="top"><a href="https://pubmed.ncbi.nlm.nih.gov/15879786/">PMID 15879786</a></td><td valign="top">Table 1, 'The UCSF-CAPRA scoring system'. Described in Methods under 'Development of the UCSF Cancer of the Prostate Risk Assessment (UCSF-CAPRA)'. The printed points match this library: PSA 0-4, Gleason 0/1/3 (no 2-point level), T stage 0-1, percent positive biopsies 0-1 at the 34% threshold, age 0-1 at 50.</td><td valign="top"><b>Yes</b></td><td valign="top">CHECKED 2026-08-05 against MDCalc's published point schema, entry by entry across all five fields (PSA 5 bands, Gleason 0/1/3 with no 2-point level, T-stage, percent cores, age)</td><td valign="top"><code>pytest tests/parity/test_r_reference_parity.py::test_capra_point_table_matches_mdcalc</code></td><td valign="top">PSA</td></tr>
</tbody>
</table>

**30 models across 12 diseases. 29 of 30 verified against a source we did not write.**

"Verified" means the output was compared against a source we did not write — a
published reference implementation, a second independent statement of the rule, the
paper's own worked example, or the vendor's live calculator.

The evidence is per model, in the table above: **How it was verified** names the
route and the source, and **Re-run the check** gives the exact pytest command that
reproduces it. [`docs/MODEL_SPREADSHEET.xlsx`](docs/MODEL_SPREADSHEET.xlsx) carries
the same columns plus each model's scope and caveats.

## Install

```bash
uv sync --group dev      # creates .venv and installs everything
uv run pytest -q         # no network required
```

`uv` handles the Python version, the virtualenv and the lockfile in one
tool, and `uv.lock` pins every version.
This project uses pip, conda and requirements.txt nowhere at all.

Python 3.10+. The equations themselves are plain arithmetic
with no dependencies; the library needs **PyYAML** to read the registry,
which is where every model's provenance lives.

Models live under `src/mayo_baseline/<disease>/<question>/`, mirroring the table.

## What kind of models these are

30 models, 9 architecture families — every one a
**fixed-coefficient statistical model**, carrying a handful of numbers estimated once
and printed in a paper. No learned representations, no training at prediction time.

| Architecture | Models |
|---|---|
| Points table | 8 |
| Logistic regression | 7 |
| Survival (Cox) | 7 |
| Survival (parametric) | 2 |
| Linear score + cut-offs | 2 |
| Derived composition | 1 |
| Categorical rule | 1 |
| Multiplicative index | 1 |
| Decision tree | 1 |

## Licensing and provenance

The Python in `src/` is ours, under **Apache-2.0**.

The *models* are not. Each is a published equation belonging to its authors, cited in
the code, in `registry/models.yaml`, and in the table above. Where a hosted calculator
carries its own terms — MSK's nomograms are research-and-education, non-commercial —
**we implement from the open-access publication, not from the hosted tool**.

Third-party reference implementations used for verification are **not vendored here**
(two are GPL). `collected/MANIFEST.yaml` pins each by version, source and license;
`scripts/fetch_references.py` retrieves them on demand. Nothing in `src/` imports them.

`registry/models.yaml` is the single source of truth. This README, the spreadsheet and
the roadmap are all generated from it, and CI checks that the numbers agree — a figure
here cannot drift from the repo.

## Contributing

Most valuable first:

1. **A correction.** If a coefficient here disagrees with its source, open an issue with
   the citation and the exact table. Nothing helps more.
2. **A model for an open cell** — see [`docs/ROADMAP.md`](docs/ROADMAP.md).
3. **A verification route** for anything we reached by a weaker one.

New models need: the equation source (specific table or figure), a registry row, an
implementation, unit tests, and a verification route. A model without one can still be
merged — but it is marked `not_checked` and the reason is recorded.
