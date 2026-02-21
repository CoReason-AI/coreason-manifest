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


class DomainValidationError(ManifestError):
    """
    Validation error for domain constraints.
    Added to support existing code expecting this exception.
    """

    def __init__(
        self,
        message: str,
        report: Any | None = None,
        remediation: Any | None = None,
        error_code: str = "CRSN-VAL-GENERIC",
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        severity = FaultSeverity.CRITICAL

        if report:
            # Assuming report has model_dump or similar if it's a model
            ctx["report"] = report.model_dump() if hasattr(report, "model_dump") else report
            # Map severity if possible
            if hasattr(report, "severity"):
                sev_str = str(report.severity).upper()
                if sev_str in ("WARNING", "INFO"):
                    severity = FaultSeverity.WARNING

        if remediation:
            ctx["remediation"] = remediation.model_dump() if hasattr(remediation, "model_dump") else remediation

        fault = SemanticFault(
            error_code=error_code, message=message, severity=severity, recovery_action=RecoveryAction.HALT, context=ctx
        )
        super().__init__(fault)
