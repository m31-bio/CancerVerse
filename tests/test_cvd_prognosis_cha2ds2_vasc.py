"""Tests for CHA2DS2-VASc (Lip et al., Chest 2010)."""


from mayo_baseline.cvd.prognosis import cha2ds2_vasc_predict, cha2ds2_vasc_score

NONE = dict(
    heart_failure=False,
    hypertension=False,
    age=50,
    diabetes=False,
    prior_stroke_tia_thromboembolism=False,
    vascular_disease=False,
    female=False,
)


def test_zero_score_for_no_risk_factors():
    assert cha2ds2_vasc_score(**NONE) == 0


def test_max_score_is_nine():
    out = cha2ds2_vasc_score(
        heart_failure=True,
        hypertension=True,
        age=80,
        diabetes=True,
        prior_stroke_tia_thromboembolism=True,
        vascular_disease=True,
        female=True,
    )
    assert out == 1 + 1 + 2 + 1 + 2 + 1 + 1 == 9


def test_age_points_are_mutually_exclusive_bands():
    assert cha2ds2_vasc_score(**{**NONE, "age": 64}) == 0
    assert cha2ds2_vasc_score(**{**NONE, "age": 65}) == 1
    assert cha2ds2_vasc_score(**{**NONE, "age": 74}) == 1
    assert cha2ds2_vasc_score(**{**NONE, "age": 75}) == 2
    # Never both bands at once — score should never exceed the higher band alone.
    assert cha2ds2_vasc_score(**{**NONE, "age": 90}) == 2


def test_stroke_history_worth_two_points_same_as_high_age():
    a = cha2ds2_vasc_score(**{**NONE, "prior_stroke_tia_thromboembolism": True})
    b = cha2ds2_vasc_score(**{**NONE, "age": 75})
    assert a == b == 2


def test_lone_female_point_is_low_risk():
    out = cha2ds2_vasc_predict(**{**NONE, "female": True})
    assert out["score"] == 1
    assert out["risk_category"] == "low"


def test_lone_non_sex_point_is_intermediate():
    out = cha2ds2_vasc_predict(**{**NONE, "hypertension": True})
    assert out["score"] == 1
    assert out["risk_category"] == "intermediate"


def test_two_or_more_points_is_high_regardless_of_sex():
    out = cha2ds2_vasc_predict(**{**NONE, "hypertension": True, "diabetes": True})
    assert out["score"] == 2
    assert out["risk_category"] == "high"


def test_metadata():
    out = cha2ds2_vasc_predict(**NONE)
    assert out["model_id"] == "cha2ds2_vasc"
    assert out["axis"] == "prognosis"
    assert out["disease"] == "cvd"
    assert out["risk"] is None
