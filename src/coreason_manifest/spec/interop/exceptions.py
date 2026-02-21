from coreason_manifest.spec.core.exceptions import DomainValidationError


class LineageIntegrityError(DomainValidationError):
    """
    Raised when trace lineage integrity is compromised (e.g. orphaned requests).
    """


class SecurityJailViolationError(DomainValidationError):
    """
    Raised when a security jail boundary is violated (e.g. path traversal, permission error).
    """
