from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FaultSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    RECOVERABLE = "RECOVERABLE"
    WARNING = "WARNING"


class RecoveryAction(StrEnum):
    HALT = "HALT"
    RETRY = "RETRY"
    FALLBACK = "FALLBACK"
    QUARANTINE = "QUARANTINE"


class SemanticFault(BaseModel):
    """Machine-readable error envelope."""

    model_config = ConfigDict(frozen=True, strict=True)

    error_code: str
    message: str
    severity: FaultSeverity
    recovery_action: RecoveryAction
    context: dict[str, Any] = Field(default_factory=dict)


class ManifestError(Exception):
    """Base exception for all Manifest protocol errors."""

    def __init__(self, fault: SemanticFault) -> None:
        super().__init__(fault.message)
        self.fault = fault


class LineageIntegrityError(ManifestError):
    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        fault = SemanticFault(
            error_code="CRSN-SEC-LINEAGE-001",
            message=message,
            severity=FaultSeverity.CRITICAL,
            recovery_action=RecoveryAction.HALT,
            context=context or {},
        )
        super().__init__(fault)


class SecurityJailViolationError(ManifestError):
    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        fault = SemanticFault(
            error_code="CRSN-SEC-JAIL-002",
            message=message,
            severity=FaultSeverity.CRITICAL,
            recovery_action=RecoveryAction.HALT,
            context=context or {},
        )
        super().__init__(fault)
