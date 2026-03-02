from coreason_manifest.core.common.exceptions import (
    FaultSeverity,
    ManifestError,
    ManifestErrorCode,
    RecoveryAction,
    SemanticFault,
)


class LineageIntegrityError(ManifestError):
    """
    Raised when a trace lineage violation is detected.
    """

    def __init__(self, message: str) -> None:
        """Initialize the core exception envelope backed by a semantic fault."""
        super().__init__(
            SemanticFault(
                error_code=ManifestErrorCode.SEC_LINEAGE_001,
                message=message,
                severity=FaultSeverity.CRITICAL,
                recovery_action=RecoveryAction.HALT,
            )
        )
