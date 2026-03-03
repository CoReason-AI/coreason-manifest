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
        """Initialize LineageIntegrityError with a critical security fault."""
        super().__init__(
            SemanticFault(
                error_code=ManifestErrorCode.SEC_LINEAGE_001,
                message=message,
                severity=FaultSeverity.CRITICAL,
                recovery_action=RecoveryAction.HALT,
            )
        )


class LatencySLAExceededError(ManifestError):
    """
    Raised when a Real-Time task exceeds its SLA.
    This signals the swarm to trigger Graceful Epistemic Degradation.
    """

    def __init__(self, message: str) -> None:
        """Initialize LatencySLAExceededError."""
        super().__init__(
            SemanticFault(
                error_code="SLA-LATENCY-001",
                message=message,
                severity=FaultSeverity.RECOVERABLE,
                recovery_action=RecoveryAction.RETRY,
            )
        )


class HardwarePreemptionInterrupt(ManifestError):  # noqa: N818
    """
    Raised when a cloud provider sends a preemption warning.
    This signals the pipeline to flush telemetry and checkpoint the Ledger.
    """

    def __init__(self, message: str) -> None:
        """Initialize HardwarePreemptionInterrupt."""
        super().__init__(
            SemanticFault(
                error_code="HW-PREEMPTION-001",
                message=message,
                severity=FaultSeverity.CRITICAL,
                recovery_action=RecoveryAction.HALT,
            )
        )
