from coreason_manifest.utils.diff import _generate_diff


def test_diff_identity_by_name() -> None:
    # Use raw _generate_diff to avoid constructing complex Flows
    l1 = [{"name": "n1", "val": 1}, {"name": "n2", "val": 2}]
    l2 = [{"name": "n1", "val": 1}, {"name": "n2", "val": 3}]

    changes = _generate_diff("/list", l1, l2)
    # Identity diffing should trigger.
    # n2 changed val.
    assert len(changes) == 1
    assert changes[0].op == "replace"
    assert changes[0].path == "/list/1/val"


def test_diff_identity_by_key() -> None:
    l1 = [{"key": "k1", "val": 1}]
    l2 = [{"key": "k1", "val": 2}]

    changes = _generate_diff("/list", l1, l2)
    assert len(changes) == 1
    assert changes[0].op == "replace"
    assert changes[0].path == "/list/0/val"


def test_diff_identity_mixed_missing() -> None:
    # List of dicts, some have ID, some don't.
    # Should fall back to index diffing.
    l1 = [{"id": "i1"}, {"val": 2}]  # 2nd item has no ID
    l2 = [{"id": "i1"}, {"val": 3}]

    # get_identity({"val": 2}) returns None.
    # dict1 will have size 1. len(l1) is 2.
    # len(dict1) != len(l1) -> Fallback to index.

    changes = _generate_diff("/list", l1, l2)
    # index 0: equal
    # index 1: replace val
    assert len(changes) == 1
    assert changes[0].op == "replace"
    assert changes[0].path == "/list/1/val"


def test_diff_identity_all_missing() -> None:
    # List of dicts, none have ID
    l1 = [{"val": 1}]
    l2 = [{"val": 2}]

    changes = _generate_diff("/list", l1, l2)
    assert len(changes) == 1
    assert changes[0].op == "replace"
