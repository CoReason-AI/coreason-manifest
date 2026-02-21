from coreason_manifest.spec.core.exceptions import DomainValidationError, ManifestError, SemanticFault
from coreason_manifest.spec.interop.exceptions import LineageIntegrityError


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


def test_legacy_validation_adapter() -> None:
    # Test DomainValidationError maps legacy args
    from coreason_manifest.spec.interop.compliance import ComplianceReport, ErrorCatalog

    report = ComplianceReport(
        code=ErrorCatalog.ERR_SEC_PATH_ESCAPE_001, severity="violation", message="Path escape detected"
    )

    err = DomainValidationError("Validation failed", report=report)
    assert err.fault.error_code == str(ErrorCatalog.ERR_SEC_PATH_ESCAPE_001)
    # Check context contains the full report
    assert err.fault.context["report"]["code"] == str(ErrorCatalog.ERR_SEC_PATH_ESCAPE_001)
