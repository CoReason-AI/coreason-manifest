from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, ClassVar, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.exceptions import ManifestError, ManifestErrorCode
from coreason_manifest.core.workflow import LineageIntegrityError


class CryptographicSignature(CoreasonModel):
    """
    Standard definition for a cryptographic signature proving origin and integrity.
    """

    signature_scheme: Literal["ed25519", "rsa", "ecdsa"] = Field(
        ..., description="The algorithm used for the signature."
    )
    public_key: str = Field(..., description="The public key in base64 encoding.")
    signature_value: str = Field(..., description="The computed signature in base64 encoding.")
    signed_at: datetime = Field(..., description="Timestamp of the signature creation.")


class NodeState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


class NodeExecution(CoreasonModel):
    """
    Telemetry record for a single node execution attempt.
    Includes Veritas integrity fields for cryptographic chaining.
    Inherits CoreasonModel.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node_id: str
    state: NodeState
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    error: str | None = None
    timestamp: datetime
    duration_ms: float
    attributes: dict[str, str | int | float | bool] = Field(default_factory=dict)

    # --- TRACE CONTEXT (Standard Telemetry) ---
    request_id: str | None = Field(default=None, description="Current execution ID (Span ID).")
    parent_request_id: str | None = Field(default=None, description="Parent execution ID.")
    root_request_id: str | None = Field(default=None, description="Trace ID (Root).")

    traceparent: str | None = Field(
        default=None,
        pattern=r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
        description="W3C Trace Context: traceparent header",
    )
    tracestate: str | None = Field(default=None, description="W3C Trace Context: tracestate header")

    # --- VERITAS INTEGRITY RESTORATION ---
    hash_version: Literal["v2"] = Field(default="v2", description="Cryptographic hashing protocol version.")
    execution_hash: Annotated[str | None, Field(description="SHA-256 hash of inputs+outputs+config.")] = None

    # Topology: Support both Linear (parent_hash) and DAG (parent_hashes)
    parent_hash: str | None = Field(default=None, description="Hash of the single parent execution (Linear).")
    parent_hashes: list[str] = Field(default_factory=list, description="Hashes of preceding executions (DAG parents).")

    signature: CryptographicSignature | None = Field(
        default=None, description="Optional cryptographic signature of the event."
    )

    _hash_exclude_: ClassVar[set[str]] = {"execution_hash", "signature"}

    @model_validator(mode="before")
    @classmethod
    def enforce_envelope_consistency(cls, data: Any) -> Any:
        """Verify cryptographic and structural integrity for suspense envelopes."""
        if isinstance(data, dict):
            # One copy for all mutations
            data = data.copy()

            # 1. Lineage Auto-Rooting
            req_id = data.get("request_id")
            parent = data.get("parent_request_id")
            root = data.get("root_request_id")

            if not req_id:
                req_id = str(uuid4())
                data["request_id"] = req_id

            if not parent and not root:
                data["root_request_id"] = req_id

            # 2. Topology Consistency
            p_hash = data.get("parent_hash")
            prev_hashes = data.get("parent_hashes")

            if p_hash:
                if prev_hashes is None:
                    data["parent_hashes"] = [p_hash]
                elif isinstance(prev_hashes, list) and p_hash not in prev_hashes:
                    new_prev = prev_hashes.copy()
                    new_prev.append(p_hash)
                    data["parent_hashes"] = new_prev

        return data

    @model_validator(mode="after")
    def validate_trace_integrity(self) -> "NodeExecution":
        """Validate referential bounds between internal spans and lineage attributes.

        Raises:
            ManifestError: Yields a CRITICAL execution fault on validation or security policy failure.
        """
        errors = []
        if self.parent_request_id and not self.root_request_id:
            errors.append(LineageIntegrityError("Broken Lineage: Orphaned request (parent set, root missing)."))
        if self.root_request_id == self.request_id and self.parent_request_id is not None:
            errors.append(LineageIntegrityError("Broken Lineage: Root request cannot imply a parent."))
        if self.parent_request_id and self.parent_request_id == self.request_id:
            errors.append(LineageIntegrityError("Broken Lineage: Self-referential parent_request_id detected."))

        if errors:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.SEC_LINEAGE_001,
                message="Multiple Trace Integrity Violations detected.",
                context={"violations": [str(e) for e in errors]},
            )
        return self


class HumanSteeringEvent(CoreasonModel):
    """
    Records a state mutation injected by a human (Time Travel/Steering).
    Used to preserve the Merkle execution trace when state is altered mid-flight.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    checkpoint_id: str = Field(..., description="Unique ID for this checkpoint.")
    timestamp: datetime = Field(..., description="When the mutation occurred.")
    mutated_variables: dict[str, Any] = Field(..., description="The variables that were changed.")
    human_identity: str = Field(..., description="ID/Email of the human operator.")


class MemoryMutationEvent(CoreasonModel):
    """
    Telemetry record for memory mutations (ADD, UPDATE, DELETE, EVICT, CONSOLIDATE)
    within the 4-tier memory subsystem. Ensures the Merkle DAG lineage isn't broken
    by implicit state changes.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    request_id: str | None = Field(
        default_factory=lambda: str(uuid4()), description="Unique ID for this mutation event."
    )
    parent_request_id: str | None = Field(default=None, description="The execution ID that triggered this mutation.")
    root_request_id: str | None = Field(default=None, description="The trace ID.")
    tier: Literal["working", "episodic", "semantic", "procedural"] = Field(
        ...,
        description="The memory tier affected.",
    )
    operation: Literal[
        "ADD",
        "UPDATE",
        "DELETE",
        "EVICT",
        "CONSOLIDATE",
    ] = Field(
        ...,
        description="The type of mutation.",
    )
    mutation_payload: dict[str, Any] = Field(..., description="The state diff or payload of the mutation.")
    timestamp: datetime = Field(..., description="When the mutation occurred.")

    # --- VERITAS INTEGRITY RESTORATION ---
    hash_version: Literal["v2"] = Field(default="v2", description="Cryptographic hashing protocol version.")
    mutation_hash: Annotated[str | None, Field(description="SHA-256 hash of the mutation payload.")] = None
    parent_hash: str | None = Field(default=None, description="Hash of the preceding execution state.")

    _hash_exclude_: ClassVar[set[str]] = {"mutation_hash"}

    @model_validator(mode="after")
    def validate_trace_integrity(self) -> "MemoryMutationEvent":
        """Validate referential bounds between internal spans and lineage attributes.

        Raises:
            ManifestError: Yields a CRITICAL execution fault on validation or security policy failure.
        """
        errors = []
        if self.parent_request_id and not self.root_request_id:
            errors.append(LineageIntegrityError("Broken Lineage: Orphaned request (parent set, root missing)."))
        if self.root_request_id == self.request_id and self.parent_request_id is not None:
            errors.append(LineageIntegrityError("Broken Lineage: Root request cannot imply a parent."))
        if self.parent_request_id and self.parent_request_id == self.request_id:
            errors.append(LineageIntegrityError("Broken Lineage: Self-referential parent_request_id detected."))

        if errors:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.SEC_LINEAGE_001,
                message="Multiple Trace Integrity Violations detected.",
                context={"violations": [str(e) for e in errors]},
            )
        return self


class ExecutionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    node_states: dict[str, NodeState]
    active_path: list[str]


from datetime import UTC  # noqa: E402


class SecurityViolationEvent(CoreasonModel):
    """
    SIEM-Native Security Alerting Contract.
    Emitted when the identity middleware detects malicious activity or strict policy breaches.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    # Event Classification
    event_type: Literal[
        "invalid_signature",
        "expired_token",
        "ssrf_attempt",  # Blocked attempt to query internal/malicious IdP URIs
        "jwks_rate_limit_exceeded",  # Potential DoS attack via forced key refreshes
        "issuer_mismatch",  # Token issuer does not match trusted authorities
        "insufficient_scope",  # Token lacks the required capability bounds
    ] = Field(..., description="Machine-readable taxonomy of the security violation.")

    severity: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Used by SOAR to determine automated response (e.g., page SOC vs. passive log)."
    )
    message: str = Field(..., description="Human-readable context.")

    # Attacker Profiling
    ip_address: str | None = Field(None, description="IP address initiating the request.")
    attempted_uri: str | None = Field(None, description="The URL the attacker attempted to force the system to reach.")
    raw_headers: dict[str, str] = Field(default_factory=dict, description="Sanitized HTTP headers for SIEM profiling.")

    # W3C Lineage
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace_id: str | None = Field(
        None, description="W3C traceparent ID linking this attack to a broader execution trace."
    )


class AuthLifecycleEvent(CoreasonModel):
    """
    Zero-Knowledge Identity Telemetry.
    Tracks authentication state changes strictly without leaking PII.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    request_id: str | None = Field(default_factory=lambda: str(uuid4()))
    parent_request_id: str | None = None
    root_request_id: str | None = None

    event_type: Literal[
        "login_success", "token_refresh", "logout", "device_flow_initiated", "device_flow_completed"
    ] = Field(..., description="The lifecycle state transition.")

    # Privacy-First Identifiers
    anonymized_user_id: str = Field(..., description="The HMAC-SHA256 hashed identity. NEVER log the raw subject ID.")
    tenant_id: str | None = Field(None, description="The organizational boundary.")

    # Ephemeral Context
    session_id: str | None = Field(None, description="The JTI or session identifier.")
    granted_scopes: list[str] = Field(default_factory=list, description="The bounded capabilities granted.")

    # W3C Lineage
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace_id: str | None = Field(None, description="W3C traceparent ID linking to the agent execution.")

    @model_validator(mode="after")
    def validate_trace_integrity(self) -> "AuthLifecycleEvent":
        """Validate referential bounds between internal spans and lineage attributes.

        Raises:
            ManifestError: Yields a CRITICAL execution fault on validation or security policy failure.
        """
        errors = []
        if self.parent_request_id and not self.root_request_id:
            errors.append(LineageIntegrityError("Broken Lineage: Orphaned request (parent set, root missing)."))
        if self.root_request_id == self.request_id and self.parent_request_id is not None:
            errors.append(LineageIntegrityError("Broken Lineage: Root request cannot imply a parent."))
        if self.parent_request_id and self.parent_request_id == self.request_id:
            errors.append(LineageIntegrityError("Broken Lineage: Self-referential parent_request_id detected."))

        if errors:
            raise ManifestError.critical_halt(
                code=ManifestErrorCode.SEC_LINEAGE_001,
                message="Multiple Trace Integrity Violations detected.",
                context={"violations": [str(e) for e in errors]},
            )
        return self
