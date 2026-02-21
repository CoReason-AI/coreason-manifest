import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.spec.interop.compliance import ComplianceReport, RemediationAction


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    RECOVERABLE = "RECOVERABLE"
    WARNING = "WARNING"


class RecoveryAction(StrEnum):
    PROMPT_RETRY = "PROMPT_RETRY"
    HALT_GRAPH = "HALT_GRAPH"
    SKIP_NODE = "SKIP_NODE"
    RETRY_NODE = "RETRY_NODE"
    NONE = "NONE"


class SemanticFault(BaseModel):
    """
    Structured error envelope for all Manifest exceptions.
    """
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    error_code: str
    severity: Severity
    recovery_action: RecoveryAction | str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class ManifestError(Exception):
    """
    Base class for all library exceptions, carrying a SemanticFault payload.
    """
    def __init__(self, fault: SemanticFault):
        self.fault = fault
        super().__init__(f"[{fault.error_code}] {fault.message}")


class DomainValidationError(ManifestError):
    """
    A domain-specific validation error that includes structured diagnostics.
    Refactored to inherit from ManifestError.
    """

    def __init__(
        self,
        message: str,
        report: ComplianceReport | None = None,
        remediation: RemediationAction | None = None,
        error_code: str = "CRSN-VAL-GENERIC",
    ):
        # Map legacy inputs to SemanticFault
        severity = Severity.CRITICAL
        recovery = RecoveryAction.HALT_GRAPH

        context = {}
        if report:
            context["report"] = report.model_dump()
            # Map severity
            if report.severity == "warning":
                severity = Severity.WARNING
            elif report.severity == "info":
                severity = Severity.WARNING

            error_code = report.code

        if remediation:
            context["remediation"] = remediation.model_dump()

        fault = SemanticFault(
            error_code=error_code,
            severity=severity,
            recovery_action=recovery,
            message=message,
            context=context
        )
        super().__init__(fault)
        self.report = report
        self.remediation = remediation

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.remediation:
            # Directive 5: Serialize remediation payload so it survives Pydantic exception masking
            payload = json.dumps(self.remediation.model_dump())
            return f"{base_msg} [Remediation: {self.remediation.description}] [Payload: {payload}]"
        return base_msg
