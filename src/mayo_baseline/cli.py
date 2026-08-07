"""Command-line entry point: list, describe, predict, verify.

    mayo-baseline list [--disease liver] [--axis prognosis]
    mayo-baseline info albi
    mayo-baseline predict albi --bilirubin_umol_l 20 --albumin_g_l 40
    mayo-baseline verify [--model albi]

The CLI exists mainly for the colleague who has a patient's numbers and one
question, and should not have to learn the Python API to get an answer.

It mirrors the library's one deliberate refusal: there is no `predict-all`.
Running every model against one record produces a column of numbers that look
equally authoritative and are not, because most of them will be outside their
model's scope. `info` prints that scope, and `predict` prints it alongside the
result rather than after it.

Types come from the registry rather than from guessing: a flag is parsed as a
float if the model declares it numeric, as a bool for yes/no predictors, and
left as a string otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import api

_TRUE = {"1", "true", "yes", "y", "t"}
_FALSE = {"0", "false", "no", "n", "f"}


def _coerce(value: str) -> Any:
    """Turn one command-line string into the value a model expects."""
    low = value.lower()
    if low in _TRUE:
        return True
    if low in _FALSE:
        return False
    try:
        return float(value) if ("." in value or "e" in low) else int(value)
    except ValueError:
        return value


def _parse_predictors(rest: list[str]) -> dict[str, Any]:
    """Parse trailing `--name value` pairs into a kwargs dict.

    argparse cannot do this: the accepted flags differ per model, and the set
    is defined by the registry rather than by this file.
    """
    out: dict[str, Any] = {}
    i = 0
    while i < len(rest):
        token = rest[i]
        if not token.startswith("--"):
            raise SystemExit(f"expected --name before {token!r}")
        name = token[2:].replace("-", "_")
        if "=" in name:
            name, _, value = name.partition("=")
            out[name] = _coerce(value)
            i += 1
            continue
        if i + 1 >= len(rest):
            raise SystemExit(f"--{name} has no value")
        out[name] = _coerce(rest[i + 1])
        i += 2
    return out


def _cmd_list(args: argparse.Namespace) -> int:
    models = api.list_models(disease=args.disease, axis=args.axis)
    if args.json:
        print(json.dumps([m.id for m in models], indent=2))
        return 0
    if not models:
        print("no models match that filter")
        return 1
    width = max(len(m.id) for m in models)
    for m in models:
        print(f"  {m.id:<{width}}  {m.disease}/{m.axis}  {m.title}")
    print(f"\n{len(models)} model(s)")
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    try:
        info = api.model_info(args.model)
    except KeyError:
        print(f"no such model: {args.model}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(info.__dict__, indent=2, default=str))
        return 0
    print(f"{info.id} — {info.title}  ({info.year})")
    print(f"  cell          {info.disease} / {info.axis}")
    for label, value in (
        ("architecture", info.architecture),
        ("discrimination", info.discrimination),
        ("developed on", info.developed_on),
        ("scope", info.scope),
        ("citation", info.citation),
        ("source", info.source_url),
        ("code", info.code),
    ):
        if value:
            print(f"  {label:<13} {value}")
    print(f"  verified      {'yes' if info.verified else 'NO'}")
    if info.verification:
        print(f"  how           {info.verification}")
    if info.required_inputs:
        print(f"  required      {', '.join(info.required_inputs)}")
    if info.optional_inputs:
        print(f"  optional      {', '.join(info.optional_inputs)}")
    if info.core_formula:
        print("\n" + "\n".join("  " + ln
                               for ln in info.core_formula.splitlines()))
    return 0


def _cmd_predict(args: argparse.Namespace, rest: list[str]) -> int:
    kwargs = _parse_predictors(rest)
    if not kwargs:
        print("no predictors given; try `mayo-baseline info "
              f"{args.model}` to see what it takes", file=sys.stderr)
        return 1
    try:
        result = api.predict(args.model, **kwargs)
    except KeyError:
        print(f"no such model: {args.model}", file=sys.stderr)
        return 1
    except (TypeError, ValueError) as exc:
        # TypeError is an unexpected keyword; ValueError is a model refusing
        # its own inputs -- a missing predictor, a bad unit, a value outside
        # the validated range. Both mean "you asked wrongly", and both should
        # end in a pointer rather than a traceback.
        print(f"{args.model}: {exc}", file=sys.stderr)
        print(f"try `mayo-baseline info {args.model}`", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0

    # Scope first, and it comes from the registry rather than the result dict:
    # the model functions return their computed fields, not their population.
    # A number printed without its scope invites use outside the cohort the
    # model was fitted on, which is how a plausible-looking result becomes a
    # wrong one.
    try:
        scope = api.model_info(args.model).scope
    except KeyError:
        scope = None
    if scope:
        print(f"scope: {scope}\n")
    for key, value in result.items():
        if value is None:
            continue
        print(f"  {key:<22} {value}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    """Point at the evidence rather than re-running it here.

    The parity checks are pytest tests, and they should stay that way -- a
    second runner would be a second thing to keep in step with the registry.
    """
    # The re-run command lives in the registry's `evidence` block rather than
    # on ModelInfo: it is provenance, not something a prediction needs.
    from .registry import load_models

    entries = [m for m in load_models() if m.get("status") == "implemented"]
    if args.model:
        entries = [m for m in entries if m["id"] == args.model]
        if not entries:
            print(f"no such model: {args.model}", file=sys.stderr)
            return 1
    shown = 0
    for m in entries:
        ev = m.get("evidence") or {}
        test = ev.get("test")
        if not test:
            continue
        fn = ev.get("test_function")
        cmd = f"pytest {test}" + (f"::{fn}" if fn else "")
        print(f"  {m['id']}\n      {cmd}")
        if ev.get("script"):
            print(f"      reference data captured by {ev['script']}")
        shown += 1
    if not shown:
        print("no re-run commands recorded")
        return 1
    print(f"\n{shown} check(s). Run them with pytest from the repository root.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mayo-baseline",
        description="Published clinical risk equations, independently verified.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list available models")
    p_list.add_argument("--disease")
    p_list.add_argument("--axis", choices=["detection", "response", "prognosis"])
    p_list.add_argument("--json", action="store_true")

    p_info = sub.add_parser("info", help="describe one model and its inputs")
    p_info.add_argument("model")
    p_info.add_argument("--json", action="store_true")

    p_pred = sub.add_parser(
        "predict", help="run one model: predict ID --predictor value ...")
    p_pred.add_argument("model")
    p_pred.add_argument("--json", action="store_true")

    p_ver = sub.add_parser("verify", help="show how each model was verified")
    p_ver.add_argument("--model")

    args, rest = parser.parse_known_args(argv)
    if args.command == "list":
        return _cmd_list(args)
    if args.command == "info":
        return _cmd_info(args)
    if args.command == "predict":
        return _cmd_predict(args, rest)
    if args.command == "verify":
        return _cmd_verify(args)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
