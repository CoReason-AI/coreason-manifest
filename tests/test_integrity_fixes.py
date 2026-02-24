from coreason_manifest.utils.integrity import CanonicalHashingStrategy


def test_canonical_hashing_float_mutation() -> None:
    """
    Test that CanonicalHashingStrategy does NOT mutate floats to integers.
    Directive: 'avoid mutating floats to integers natively'.
    """
    strategy = CanonicalHashingStrategy()

    # Current implementation converts 1.0 -> 1 (int)
    # We want to verify if it does or doesn't, and fix it to NOT do it.

    val_float = 1.0
    sanitized = strategy._recursive_sort_and_sanitize(val_float)

    # If the directive means "preserve float type", then sanitized should be float.
    assert isinstance(sanitized, float), f"Expected float, got {type(sanitized)}"
    assert sanitized == 1.0


def test_canonical_hashing_float_vs_int_hash() -> None:
    """
    Verify that 1.0 and 1 result in different hashes if we stop mutating.
    """
    strategy = CanonicalHashingStrategy()
    h1 = strategy.compute_hash({"val": 1.0})
    h2 = strategy.compute_hash({"val": 1})

    # If 1.0 stays 1.0, and 1 stays 1, json.dumps produces "1.0" and "1", so hashes differ.
    assert h1 != h2
