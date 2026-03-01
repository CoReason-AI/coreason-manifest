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
    VAL_SCHEMA_INVALID = "VAL-SCHEMA-INVALID"
    VAL_MIDDLEWARE_MISSING = "VAL-MIDDLEWARE-MISSING"
    VAL_RESILIENCE_MISSING = "VAL-RESILIENCE-MISSING"
    VAL_ENTRY_POINT_MISSING = "VAL-ENTRY-POINT-MISSING"
    VAL_FALLBACK_MISSING = "VAL-FALLBACK-MISSING"
    VAL_SWARM_VAR_MISSING = "VAL-SWARM-VAR-MISSING"
    VAL_INTEGRITY_PROFILE_MISSING = "VAL-INTEGRITY-PROFILE-MISSING"
    VAL_HUMAN_SHADOW = "VAL-HUMAN-SHADOW"
    VAL_HUMAN_TIMEOUT = "VAL-HUMAN-TIMEOUT"
    VAL_HUMAN_BLOCKING = "VAL-HUMAN-BLOCKING"
    VAL_HUMAN_STEERING = "VAL-HUMAN-STEERING"
    VAL_SWARM_REDUCER = "VAL-SWARM-REDUCER"
    VAL_TOPOLOGY_EMPTY = "VAL-TOPOLOGY-EMPTY"
    VAL_TOPOLOGY_ID_MISMATCH = "VAL-TOPOLOGY-ID-MISMATCH"
    VAL_TOPOLOGY_MISSING_ENTRY = "VAL-TOPOLOGY-MISSING-ENTRY"
    VAL_TOPOLOGY_DANGLING_EDGE = "VAL-TOPOLOGY-DANGLING-EDGE"
    VAL_TOPOLOGY_CYCLE = "VAL-TOPOLOGY-CYCLE"
    VAL_TOPOLOGY_LINEAR_EMPTY = "VAL-TOPOLOGY-LINEAR-EMPTY"
    VAL_TOPOLOGY_NODE_ID_COLLISION = "VAL-TOPOLOGY-NODE-ID-COLLISION"
    VAL_LIFECYCLE_UNRESOLVED = "VAL-LIFECYCLE-UNRESOLVED"

    # Security
    SEC_KILL_SWITCH_VIOLATION = "SEC-KILL-SWITCH-VIOLATION"
    SEC_JAIL_002 = "SEC-JAIL-002"
    SEC_LINEAGE_001 = "SEC-LINEAGE-001"

    # Standard Authentication Errors (OAuth2/OIDC)
    UNAUTHORIZED_MISSING_TOKEN = "UNAUTHORIZED_MISSING_TOKEN"  # noqa: S105
    UNAUTHORIZED_TOKEN_EXPIRED = "UNAUTHORIZED_TOKEN_EXPIRED"  # noqa: S105
    UNAUTHORIZED_INVALID_SIGNATURE = "UNAUTHORIZED_INVALID_SIGNATURE"
    UNAUTHORIZED_UNTRUSTED_ISSUER = "UNAUTHORIZED_UNTRUSTED_ISSUER"
    FORBIDDEN_INSUFFICIENT_SCOPE = "FORBIDDEN_INSUFFICIENT_SCOPE"
    FORBIDDEN_AUDIENCE_MISMATCH = "FORBIDDEN_AUDIENCE_MISMATCH"

    # Standard Zero-Trust Security Errors
    SECURITY_SSRF_ATTEMPT = "SECURITY_SSRF_ATTEMPT"
    SECURITY_JWKS_RATE_LIMIT = "SECURITY_JWKS_RATE_LIMIT"
    SECURITY_TOKEN_TAMPERING = "SECURITY_TOKEN_TAMPERING"  # noqa: S105
    SECURITY_PII_LEAK_PREVENTED = "SECURITY_PII_LEAK_PREVENTED"


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
                error_code=ManifestErrorCode.SEC_JAIL_002,
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
                error_code=ManifestErrorCode.SEC_LINEAGE_001,
                message=message,
                severity=FaultSeverity.CRITICAL,
                recovery_action=RecoveryAction.HALT,
            )
        )
