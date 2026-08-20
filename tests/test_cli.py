"""The CLI is the surface a colleague meets first, so it gets tested like one.

The value it adds over the Python API is that it refuses to let a number
escape without its scope, and that it fails helpfully when the caller does not
know a model's inputs. Both are asserted here.
"""

from __future__ import annotations

import json

import pytest

from cancerverse_baseline.cli import _coerce, _parse_predictors, main


# ---------------------------------------------------------------- parsing
def test_coerce_reads_numbers_bools_and_strings():
    assert _coerce("20") == 20
    assert _coerce("20.5") == 20.5
    assert _coerce("1e-3") == pytest.approx(0.001)
    assert _coerce("yes") is True
    assert _coerce("false") is False
    assert _coerce("Japanese") == "Japanese"


def test_parse_predictors_accepts_both_flag_forms():
    assert _parse_predictors(["--age", "50", "--male=yes"]) == {
        "age": 50, "male": True}


def test_parse_predictors_maps_dashes_to_underscores():
    """`--bilirubin-umol-l` is what a shell user types; the model takes
    `bilirubin_umol_l`."""
    assert _parse_predictors(["--bilirubin-umol-l", "20"]) == {
        "bilirubin_umol_l": 20}


def test_parse_predictors_rejects_a_value_with_no_flag():
    with pytest.raises(SystemExit):
        _parse_predictors(["20"])


def test_parse_predictors_rejects_a_flag_with_no_value():
    with pytest.raises(SystemExit):
        _parse_predictors(["--age"])


# ------------------------------------------------------------------ list
def test_list_filters_by_disease(capsys):
    assert main(["list", "--disease", "liver"]) == 0
    out = capsys.readouterr().out
    assert "albi" in out and "amap" in out
    assert "score2" not in out


def test_list_json_is_parseable(capsys):
    assert main(["list", "--json"]) == 0
    ids = json.loads(capsys.readouterr().out)
    assert "albi" in ids and len(ids) >= 30


# ------------------------------------------------------------------ info
def test_info_shows_inputs_and_how_it_was_verified(capsys):
    assert main(["info", "crc_pro"]) == 0
    out = capsys.readouterr().out
    assert "required" in out and "male" in out
    assert "verified" in out
    assert "scope" in out


def test_info_on_an_unknown_model_fails_cleanly(capsys):
    assert main(["info", "no_such_model"]) == 1
    assert "no such model" in capsys.readouterr().err


# --------------------------------------------------------------- predict
def test_predict_returns_the_same_number_as_the_api(capsys):
    from cancerverse_baseline import predict

    assert main(["predict", "albi", "--bilirubin_umol_l", "20",
                 "--albumin_g_l", "40", "--json"]) == 0
    from_cli = json.loads(capsys.readouterr().out)
    from_api = predict("albi", bilirubin_umol_l=20.0, albumin_g_l=40.0)
    assert from_cli["score"] == pytest.approx(from_api["score"])
    assert from_cli["grade"] == from_api["grade"]


def test_predict_prints_scope_before_the_number(capsys):
    """Running a model is not the same as being entitled to believe it. Where a
    scope is recorded, it must appear before the result, not after."""
    assert main(["predict", "crc_pro",
                 "--male", "yes", "--age", "60", "--ethnicity", "Japanese",
                 "--weight_lb", "170", "--height_in", "68",
                 "--years_education", "12", "--pack_years", "0",
                 "--alcohol_drinks_per_day", "0", "--family_history", "no",
                 "--multivitamin", "no", "--diabetes", "no"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("scope:")
    assert out.index("scope:") < out.index("risk")


def test_predict_with_no_predictors_points_at_info(capsys):
    assert main(["predict", "albi"]) == 1
    assert "info albi" in capsys.readouterr().err


def test_predict_with_a_missing_predictor_says_so_and_points_at_info(capsys):
    assert main(["predict", "albi", "--bilirubin_umol_l", "20"]) == 1
    err = capsys.readouterr().err
    assert "info albi" in err


# ---------------------------------------------------------------- verify
def test_verify_names_a_runnable_check(capsys):
    assert main(["verify", "--model", "albi"]) == 0
    assert "pytest" in capsys.readouterr().out


def test_there_is_still_no_predict_all_subcommand():
    """The deliberate refusal, pinned. Running every model against one record
    produces a column of equally authoritative-looking numbers, most of them
    outside their model's scope."""
    with pytest.raises(SystemExit):
        main(["predict-all", "--age", "50"])
