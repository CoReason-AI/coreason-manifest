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
    SCHEMA_INVALID = "CRSN-VAL-SCHEMA-INVALID"
    MIDDLEWARE_MISSING = "CRSN-VAL-MIDDLEWARE-MISSING"
    RESILIENCE_MISSING = "CRSN-VAL-RESILIENCE-MISSING"
    ENTRY_POINT_MISSING = "CRSN-VAL-ENTRY-POINT-MISSING"
    FALLBACK_MISSING = "CRSN-VAL-FALLBACK-MISSING"
    SWARM_VAR_MISSING = "CRSN-VAL-SWARM-VAR-MISSING"
    INTEGRITY_PROFILE_MISSING = "CRSN-VAL-INTEGRITY-PROFILE-MISSING"
    HUMAN_SHADOW = "CRSN-VAL-HUMAN-SHADOW"
    HUMAN_TIMEOUT = "CRSN-VAL-HUMAN-TIMEOUT"
    HUMAN_BLOCKING = "CRSN-VAL-HUMAN-BLOCKING"
    HUMAN_STEERING = "CRSN-VAL-HUMAN-STEERING"
    SWARM_REDUCER = "CRSN-VAL-SWARM-REDUCER"
    TOPOLOGY_EMPTY = "CRSN-VAL-TOPOLOGY-EMPTY"
    TOPOLOGY_ID_MISMATCH = "CRSN-VAL-TOPOLOGY-ID-MISMATCH"
    TOPOLOGY_MISSING_ENTRY = "CRSN-VAL-TOPOLOGY-MISSING-ENTRY"
    TOPOLOGY_DANGLING_EDGE = "CRSN-VAL-TOPOLOGY-DANGLING-EDGE"
    TOPOLOGY_CYCLE = "CRSN-VAL-TOPOLOGY-CYCLE"
    TOPOLOGY_LINEAR_EMPTY = "CRSN-VAL-TOPOLOGY-LINEAR-EMPTY"
    TOPOLOGY_NODE_ID_COLLISION = "CRSN-VAL-TOPOLOGY-NODE-ID-COLLISION"
    LIFECYCLE_UNRESOLVED = "CRSN-VAL-LIFECYCLE-UNRESOLVED"

    # Security
    KILL_SWITCH_VIOLATION = "CRSN-SEC-KILL-SWITCH-VIOLATION"
    JAIL_002 = "CRSN-SEC-JAIL-002"
    LINEAGE_001 = "CRSN-SEC-LINEAGE-001"

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
                error_code=ManifestErrorCode.JAIL_002,
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
                error_code=ManifestErrorCode.LINEAGE_001,
                message=message,
                severity=FaultSeverity.CRITICAL,
                recovery_action=RecoveryAction.HALT,
            )
        )
