from coreason_manifest.spec.core.types import RiskLevel


def test_risk_level_comparisons() -> None:
    # Test weight comparisons instead of direct operator comparisons
    assert RiskLevel.SAFE.weight < RiskLevel.STANDARD.weight
    assert RiskLevel.STANDARD.weight < RiskLevel.CRITICAL.weight
    assert RiskLevel.SAFE.weight < RiskLevel.CRITICAL.weight

    assert RiskLevel.SAFE.weight <= RiskLevel.SAFE.weight
    assert RiskLevel.SAFE.weight <= RiskLevel.STANDARD.weight

    assert RiskLevel.CRITICAL.weight > RiskLevel.STANDARD.weight
    assert RiskLevel.STANDARD.weight > RiskLevel.SAFE.weight
    assert RiskLevel.CRITICAL.weight > RiskLevel.SAFE.weight

    assert RiskLevel.CRITICAL.weight >= RiskLevel.CRITICAL.weight
    assert RiskLevel.CRITICAL.weight >= RiskLevel.STANDARD.weight

    # Test equality (StrEnum default behavior)
    assert RiskLevel.SAFE.value == "safe"
    assert RiskLevel.STANDARD.value == "standard"
    assert RiskLevel.CRITICAL.value == "critical"

    # Test weight property directly
    assert RiskLevel.SAFE.weight == 0
    assert RiskLevel.STANDARD.weight == 1
    assert RiskLevel.CRITICAL.weight == 2

    # Verify that direct comparison (using default string comparison)
    # does NOT follow risk semantics (demonstrating why we removed the operators and use weights)
    # "safe" < "standard" is True (correct order but by coincidence of alphabet)
    # "standard" < "critical" is False ('s' > 'c'), but semantically standard(1) < critical(2).

    # This assertion proves that relying on default __lt__ is dangerous/wrong
    assert (RiskLevel.STANDARD < RiskLevel.CRITICAL) is False

    # But weight comparison is correct
    assert (RiskLevel.STANDARD.weight < RiskLevel.CRITICAL.weight) is True
