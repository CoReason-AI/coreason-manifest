# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from pydantic import AwareDatetime, ConfigDict, Field, SecretStr, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.primitives.types import DataClassification


class AgentIdentity(CoreasonModel):
    model_config = ConfigDict(frozen=True)
    """
    Cryptographic identity of the agent operating within the Zero-Trust Prompt paradigm.
    Proves the acting software entity.
    """

    agent_id: str = Field(..., description="Unique, verifiable ID for the agent instance.")
    version: str = Field(..., description="Version of the agent.")
    software_hash: str | None = Field(None, description="Cryptographic hash of the agent's manifest definition.")


class UserIdentity(CoreasonModel):
    model_config = ConfigDict(frozen=True)
    """
    The principal human or service account initiating the trace in the On-Behalf-Of (OBO) flow.
    Includes Persona-Based Access Control (PBAC) roles.
    """

    user_id: str = Field(..., description="The principal human or service account initiating the trace.")
    roles: list[str] = Field(
        default_factory=list, description="Persona-Based Access Control (PBAC) roles assigned to the user."
    )


class DelegationScope(CoreasonModel):
    model_config = ConfigDict(frozen=True)
    """
    The strict boundaries of authority granted to the agent for this specific trace.
    Part of the Zero-Trust Identity Context Envelope.
    """

    allowed_tools: list[str] = Field(
        default_factory=list, description="Strictly scoped tool whitelist for this specific request."
    )
    max_budget_usd: float | None = Field(None, description="Financial cap for this trace.")
    session_expiry: AwareDatetime | None = Field(
        None, description="When this context envelope expires. Must be TZ-aware."
    )


class SessionContext(CoreasonModel):
    model_config = ConfigDict(frozen=True)
    """
    The Zero-Trust Identity Context Envelope for this request.
    Proves cryptographically who is making the request, who the agent is, and what its delegated authority is.
    """

    session_id: str = Field(..., description="ID of the interaction session.")
    user: UserIdentity = Field(..., description="The delegating principal.")
    agent: AgentIdentity = Field(..., description="The acting agent.")
    delegation: DelegationScope = Field(..., description="The authority granted.")
    trace_id: str | None = Field(
        None,
        pattern=r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
        description="W3C Trace Context ID for distributed secure tracking.",
    )


class ResourceCaveat(CoreasonModel):
    """
    SOTA UCAN/Macaroon-style capability attenuation.
    Defines strict boundaries on a delegated resource.
    """

    model_config = ConfigDict(frozen=True)

    target_resource: str = Field(..., description="The tool or capability being restricted (e.g., 'db_query', '*').")
    constraint: str = Field(
        ..., description="AST-safe Python expression representing the boundary (e.g., 'cost < 5.00')."
    )


class DelegationContract(CoreasonModel):
    """
    The strictly bounded and time-limited authority granted for a specific execution trace.
    """

    model_config = ConfigDict(frozen=True)

    allowed_tools: list[str] = Field(default=["*"], description="Whitelist of permitted tools.")
    caveats: list[ResourceCaveat] = Field(default_factory=list, description="Cryptographic attenuations on authority.")
    max_budget_usd: float | None = Field(None, description="Financial circuit breaker for this specific trace.")

    max_tokens: int | None = Field(
        None,
        description=(
            "Physical circuit breaker: Maximum LLM tokens (in+out) authorized to prevent local compute exhaustion."
        ),
    )
    max_compute_time_ms: int | None = Field(
        None,
        description="Temporal circuit breaker: Maximum asynchronous wall-time before forced execution termination.",
    )
    caep_stream_uri: str | None = Field(
        None,
        description=(
            "Shared Signals Framework (SSF) URI. The orchestrator subscribes "
            "to this for real-time instantaneous passport revocation."
        ),
    )

    # SOTA Temporal Bounding
    issued_at: float = Field(..., description="Unix epoch timestamp of delegation issuance.")
    expires_at: float = Field(..., description="Unix epoch timestamp of delegation expiry.")

    max_data_classification: DataClassification = Field(
        default=DataClassification.INTERNAL,
        description=(
            "Information Flow Control bound (e.g., 'public', 'internal', 'confidential', 'restricted'). "
            "Dictates the highest sensitivity of data this trace can ingest."
        ),
    )

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> "DelegationContract":
        """Verify that cryptographic tokens or identities fall strictly within their allowed temporal validity window.

        Raises:
            ValueError: If the current time is outside the valid 'not_before' to 'expires_at' window.
        """
        if self.expires_at <= self.issued_at:
            raise ValueError("Delegation expires_at must be strictly greater than issued_at.")
        return self


class UserContext(CoreasonModel):
    """
    Privacy-first representation of the human principal.
    """

    model_config = ConfigDict(frozen=True)

    raw_user_id: SecretStr | None = Field(
        None, description="The actual IdP subject. SecretStr prevents accidental logging leakage."
    )
    anonymized_user_id: str = Field(
        ..., description="Deterministic HMAC-SHA256 ID used for cache keys and telemetry routing without exposing PII."
    )
    tenant_id: str | None = Field(None, description="Cryptographic boundary for data segregation.")
    roles: list[str] = Field(default_factory=list, description="Standardized PBAC roles mapped from the IdP.")


class SystemContext(CoreasonModel):
    """
    Cryptographic identity of the acting software entity (Agent/Worker).
    """

    model_config = ConfigDict(frozen=True)

    agent_id: str = Field(..., description="The ID of the autonomous agent.")
    version: str = Field(..., description="SemVer of the agent manifest.")
    software_hash: str | None = Field(
        None, description="SHA-256 hash of the agent's definition, proving execution integrity."
    )


class IdentityPassport(CoreasonModel):
    """
    The Supreme Zero-Trust Context Envelope.
    Replaces legacy SessionContext. Travels alongside the W3C Trace Context.
    """

    model_config = ConfigDict(frozen=True)

    passport_id: str = Field(..., description="Unique JTI for this exact passport instance to prevent replay attacks.")
    user: UserContext
    system: SystemContext
    delegation: DelegationContract

    # Cryptographic Lineage
    issuer_uri: str = Field(..., description="The verified IdP that established the root of trust.")
    signature_hash: str = Field(
        ..., description="Hash of the originating JWT/Token signature. Anchors the passport to reality."
    )
    parent_passport_id: str | None = Field(
        None,
        description=(
            "ID of the parent's passport if this agent was spawned by a "
            "Swarm delegation. Enables recursive lineage tracking."
        ),
    )
    signature_algorithm: str = Field(
        default="ES256",
        description=(
            "Algorithm used for the root signature (e.g., 'ES256', 'EdDSA', "
            "or NIST FIPS 204 PQC 'ML-DSA-65'). Protects against downgrade attacks."
        ),
    )
