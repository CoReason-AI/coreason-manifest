from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FaultSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    RECOVERABLE = "RECOVERABLE"
    WARNING = "WARNING"
    INFO = "INFO"


class RecoveryAction(StrEnum):
    HALT = "HALT_GRAPH"
    RETRY = "PROMPT_RETRY"
    SKIP = "SKIP_NODE"
    IGNORE = "IGNORE"


class ManifestErrorCode(StrEnum):
    """
    Centralized catalog of all Coreason Manifest error codes.
    """

    # Validation
    CRSN_VAL_SCHEMA_INVALID = "CRSN-VAL-SCHEMA-INVALID"
    CRSN_VAL_MIDDLEWARE_MISSING = "CRSN-VAL-MIDDLEWARE-MISSING"
    CRSN_VAL_RESILIENCE_MISSING = "CRSN-VAL-RESILIENCE-MISSING"
    CRSN_VAL_ENTRY_POINT_MISSING = "CRSN-VAL-ENTRY-POINT-MISSING"
    CRSN_VAL_FALLBACK_MISSING = "CRSN-VAL-FALLBACK-MISSING"
    CRSN_VAL_SWARM_VAR_MISSING = "CRSN-VAL-SWARM-VAR-MISSING"
    CRSN_VAL_INTEGRITY_PROFILE_MISSING = "CRSN-VAL-INTEGRITY-PROFILE-MISSING"
    CRSN_VAL_HUMAN_SHADOW = "CRSN-VAL-HUMAN-SHADOW"
    CRSN_VAL_HUMAN_TIMEOUT = "CRSN-VAL-HUMAN-TIMEOUT"
    CRSN_VAL_HUMAN_BLOCKING = "CRSN-VAL-HUMAN-BLOCKING"
    CRSN_VAL_HUMAN_STEERING = "CRSN-VAL-HUMAN-STEERING"
    CRSN_VAL_SWARM_REDUCER = "CRSN-VAL-SWARM-REDUCER"

    # Security
    CRSN_SEC_KILL_SWITCH_VIOLATION = "CRSN-SEC-KILL-SWITCH-VIOLATION"
    CRSN_SEC_JAIL_002 = "CRSN-SEC-JAIL-002"
    CRSN_SEC_LINEAGE_001 = "CRSN-SEC-LINEAGE-001"


class SemanticFault(BaseModel):
    """
    Immutable error state envelope.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    error_code: str
    message: str
    severity: FaultSeverity
    recovery_action: RecoveryAction
    context: dict[str, Any] = Field(default_factory=dict)


class ManifestError(Exception):
    """
    Base exception for Coreason Manifest.
    Backed by a SemanticFault model.
    """

    def __init__(self, fault: SemanticFault) -> None:
        self.fault = fault
        super().__init__(fault.message)

    def __str__(self) -> str:
        return f"[{self.fault.error_code}] {self.fault.message} (Severity: {self.fault.severity})"

    @classmethod
    def critical_halt(
        cls, code: ManifestErrorCode | str, message: str, context: dict[str, Any] | None = None
    ) -> "ManifestError":
        """Factory for critical errors that halt execution."""
        return cls(
            SemanticFault(
                error_code=code,
                message=message,
                severity=FaultSeverity.CRITICAL,
                recovery_action=RecoveryAction.HALT,
                context=context or {},
            )
        )


class SecurityJailViolationError(ManifestError):
    """
    Raised when a file operation attempts to escape the sandbox jail.
    Legacy exception retained for compatibility with loader.py but upgraded to SOTA.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            SemanticFault(
                error_code=ManifestErrorCode.CRSN_SEC_JAIL_002,
                message=message,
                severity=FaultSeverity.CRITICAL,
                recovery_action=RecoveryAction.HALT,
            )
        )


class LineageIntegrityError(ManifestError):
    """
    Raised when a trace lineage violation is detected.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            SemanticFault(
                error_code=ManifestErrorCode.CRSN_SEC_LINEAGE_001,
                message=message,
                severity=FaultSeverity.CRITICAL,
                recovery_action=RecoveryAction.HALT,
            )
        )
