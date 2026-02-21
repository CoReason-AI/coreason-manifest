from typing import Any

from coreason_manifest.utils.diff import _generate_diff


def test_diff_dict_add_remove_keys() -> None:
    # Test adding and removing keys in a dict to trigger lines 154/156
    d1: dict[str, Any] = {"a": 1}
    d2: dict[str, Any] = {"b": 2}

    # "a" in d1, not in d2 -> remove
    # "b" in d2, not in d1 -> add

    changes = _generate_diff("/dict", d1, d2)

    # We expect 2 changes
    ops = {c.op for c in changes}
    assert "add" in ops
    assert "remove" in ops

    add_op = next(c for c in changes if c.op == "add")
    assert add_op.path == "/dict/b"
    assert add_op.value == 2

    rem_op = next(c for c in changes if c.op == "remove")
    assert rem_op.path == "/dict/a"


def test_diff_dict_domain_switching() -> None:
    # Test domain switching logic
    d1: dict[str, Any] = {}
    d2: dict[str, Any] = {"governance": {}}

    changes = _generate_diff("", d1, d2)
    assert len(changes) == 1
    assert changes[0].op == "add"
    assert changes[0].mutation_type == "governance"
