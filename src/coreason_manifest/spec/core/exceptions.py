import json
from typing import Any

from coreason_manifest.spec.interop.compliance import ComplianceReport, RemediationAction


class DomainValidationError(ValueError):
    """
    A domain-specific validation error that includes structured diagnostics.
    """

    def __init__(
        self,
        message: str,
        report: ComplianceReport | None = None,
        remediation: RemediationAction | None = None,
    ):
        super().__init__(message)
        self.report = report
        self.remediation = remediation

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.remediation:
            # Directive 5: Serialize remediation payload so it survives Pydantic exception masking
            payload = json.dumps(self.remediation.model_dump())
            return f"{base_msg} [Remediation: {self.remediation.description}] [Payload: {payload}]"
        return base_msg


class ManifestSyntaxError(ValueError):
    """
    Raised when the manifest structure is invalid (e.g., type mismatch, missing field).
    """

    def __init__(self, message: str, json_path: str = "$", context: dict[str, Any] | None = None):
        self.json_path = json_path
        self.context = context or {}
        super().__init__(f"{message} (at {json_path})")


class GovernanceViolation(ValueError):
    """
    Raised when a governance policy is violated.
    """

    def __init__(self, message: str, json_path: str = "$", context: dict[str, Any] | None = None):
        self.json_path = json_path
        self.context = context or {}
        super().__init__(f"Governance Policy Violation: {message} (at {json_path})")


class SecurityException(ValueError):
    """
    Raised when a security constraint is violated (e.g., cycle, bomb, illegal access).
    """

    def __init__(self, message: str, json_path: str = "$", context: dict[str, Any] | None = None):
        self.json_path = json_path
        self.context = context or {}
        super().__init__(f"Security Violation: {message} (at {json_path})")
