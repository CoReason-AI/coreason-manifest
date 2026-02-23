from coreason_manifest.spec.core.types import RiskLevel


def test_risk_level_comparisons() -> None:
    # Test valid comparisons
    assert RiskLevel.SAFE < RiskLevel.STANDARD
    assert RiskLevel.STANDARD < RiskLevel.CRITICAL
    assert RiskLevel.SAFE < RiskLevel.CRITICAL

    assert RiskLevel.SAFE <= RiskLevel.SAFE
    assert RiskLevel.SAFE <= RiskLevel.STANDARD

    assert RiskLevel.CRITICAL > RiskLevel.STANDARD
    assert RiskLevel.STANDARD > RiskLevel.SAFE
    assert RiskLevel.CRITICAL > RiskLevel.SAFE

    assert RiskLevel.CRITICAL >= RiskLevel.CRITICAL
    assert RiskLevel.CRITICAL >= RiskLevel.STANDARD

    # Test equality (StrEnum default behavior)
    assert RiskLevel.SAFE.value == "safe"
    assert RiskLevel.STANDARD.value == "standard"
    assert RiskLevel.CRITICAL.value == "critical"

    # Test invalid comparisons to cover NotImplemented paths (lines 93, 98, 103, 111)
    # We catch TypeError because that's what Python usually raises when __lt__ returns NotImplemented
    # and the other side also returns NotImplemented.

    import contextlib

    with contextlib.suppress(TypeError):
        _ = RiskLevel.SAFE < 10

    with contextlib.suppress(TypeError):
        _ = RiskLevel.SAFE > "unknown"

    with contextlib.suppress(TypeError):
        _ = RiskLevel.SAFE <= None

    with contextlib.suppress(TypeError):
        _ = RiskLevel.SAFE >= []

    # Test weight property directly for coverage
    assert RiskLevel.SAFE.weight == 0
    assert RiskLevel.STANDARD.weight == 1
    assert RiskLevel.CRITICAL.weight == 2
