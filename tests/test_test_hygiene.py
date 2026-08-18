"""Tests about the tests themselves."""

from __future__ import annotations

import ast
from pathlib import Path


def test_no_test_can_never_pass():
    """A test whose body cannot pass is a TODO wearing a test costume.

    Two of these lived in tests/parity/test_canonical_parity.py until
    2026-08-18: `xfail(strict=False)` around

        expected_risk = None
        assert expected_risk is not None

    They could not pass however the library behaved, so they reported nothing,
    and `strict=False` meant that even filling one in correctly would raise no
    signal. They also carried prose that drifted -- one gave its reason as
    `parity_status=not_checked` thirteen days after the registry said
    `checked`. Both were removed; this stops the shape coming back.

    A wanted-but-unwritten parity route belongs in the model's registry entry,
    where the other provenance lives and where the audit can see it.
    """
    root = Path(__file__).resolve().parents[1] / "tests"
    dead = []
    for path in sorted(root.rglob("test_*.py")):
        tree = ast.parse(path.read_text())
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef) or not fn.name.startswith("test_"):
                continue
            # names bound to a literal None anywhere in the function
            none_names = {
                t.id
                for node in ast.walk(fn)
                if isinstance(node, ast.Assign)
                for t in node.targets
                if isinstance(t, ast.Name)
                and isinstance(node.value, ast.Constant)
                and node.value.value is None
            }
            for node in ast.walk(fn):
                if not isinstance(node, ast.Assert):
                    continue
                cmp = node.test
                if (
                    isinstance(cmp, ast.Compare)
                    and isinstance(cmp.left, ast.Name)
                    and cmp.left.id in none_names
                    and len(cmp.ops) == 1
                    and isinstance(cmp.ops[0], ast.IsNot)
                    and isinstance(cmp.comparators[0], ast.Constant)
                    and cmp.comparators[0].value is None
                ):
                    dead.append(
                        f"{path.relative_to(root.parent)}::{fn.name} asserts "
                        f"`{cmp.left.id} is not None` on a name this function "
                        f"only ever binds to None"
                    )

    assert not dead, (
        "test(s) that cannot pass no matter how the library behaves:\n  "
        + "\n  ".join(dead)
    )
