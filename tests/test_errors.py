from coreason_manifest.spec.interop.exceptions import (
    LineageIntegrityError,
    ManifestError,
    SecurityJailViolationError,
    SemanticFault,
)


def test_semantic_fault_structure() -> None:
    err = LineageIntegrityError("Test error")
    assert isinstance(err, ManifestError)
    assert isinstance(err.fault, SemanticFault)
    assert err.fault.error_code == "CRSN-SEC-LINEAGE-001"
    assert err.fault.severity == "CRITICAL"


def test_manifest_error_serialization() -> None:
    err = LineageIntegrityError("Orphaned trace")
    payload = err.fault.model_dump()
    assert payload["message"] == "Orphaned trace"
    assert payload["error_code"] == "CRSN-SEC-LINEAGE-001"


def test_security_jail_error() -> None:
    err = SecurityJailViolationError("Jailbreak!")
    assert err.fault.error_code == "CRSN-SEC-JAIL-002"
    assert "Jailbreak" in err.fault.message
