from coreason_manifest.spec.core.exceptions import DomainValidationError
from coreason_manifest.spec.interop.compliance import ComplianceReport, RemediationAction


class LineageIntegrityError(DomainValidationError):
    """
    Raised when trace lineage integrity is compromised (e.g. orphaned requests).
    """
    def __init__(self, message: str, report: ComplianceReport | None = None, remediation: RemediationAction | None = None) -> None:
        super().__init__(
            message=message,
            report=report,
            remediation=remediation,
            error_code="CRSN-SEC-LINEAGE-001"
        )


class SecurityJailViolationError(DomainValidationError):
    """
    Raised when a security jail boundary is violated (e.g. path traversal, permission error).
    """
    def __init__(self, message: str, report: ComplianceReport | None = None, remediation: RemediationAction | None = None) -> None:
        super().__init__(
            message=message,
            report=report,
            remediation=remediation,
            error_code="CRSN-SEC-JAIL-002"
        )
