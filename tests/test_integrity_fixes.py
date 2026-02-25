from coreason_manifest.utils.integrity import CanonicalHashingStrategy


def test_canonical_hashing_float_mutation() -> None:
    """
    Test that CanonicalHashingStrategy DOES mutate floats to integers if they are whole numbers,
    complying with RFC 8785.
    """
    strategy = CanonicalHashingStrategy()

    val_float = 1.0
    sanitized = strategy._recursive_sort_and_sanitize(val_float)

    # RFC 8785: 1.0 must be 1
    assert isinstance(sanitized, int), f"Expected int, got {type(sanitized)}"
    assert sanitized == 1

    # Non-whole float should remain float
    val_float_2 = 1.5
    sanitized_2 = strategy._recursive_sort_and_sanitize(val_float_2)
    assert isinstance(sanitized_2, float)
    assert sanitized_2 == 1.5


def test_canonical_hashing_float_vs_int_hash() -> None:
    """
    Verify that 1.0 and 1 result in SAME hashes due to integer truncation (RFC 8785).
    """
    strategy = CanonicalHashingStrategy()
    h1 = strategy.compute_hash({"val": 1.0})
    h2 = strategy.compute_hash({"val": 1})

    # 1.0 -> 1, so hashes match
    assert h1 == h2
