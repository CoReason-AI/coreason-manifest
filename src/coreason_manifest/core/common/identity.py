# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from pydantic import Field, SecretStr, model_validator

from coreason_manifest.core.common.base import CoreasonModel


class ResourceCaveat(CoreasonModel):
    """
    SOTA UCAN/Macaroon-style capability attenuation.
    Defines strict boundaries on a delegated resource.
    """

    target_resource: str = Field(..., description="The tool or capability being restricted (e.g., 'db_query', '*').")
    constraint: str = Field(
        ..., description="AST-safe Python expression representing the boundary (e.g., 'cost < 5.00')."
    )


class DelegationContract(CoreasonModel):
    """
    The strictly bounded and time-limited authority granted for a specific execution trace.
    """

    allowed_tools: list[str] = Field(default=["*"], description="Whitelist of permitted tools.")
    caveats: list[ResourceCaveat] = Field(default_factory=list, description="Cryptographic attenuations on authority.")
    max_budget_usd: float | None = Field(None, description="Financial circuit breaker for this specific trace.")

    # SOTA Temporal Bounding
    issued_at: float = Field(..., description="Unix epoch timestamp of delegation issuance.")
    expires_at: float = Field(..., description="Unix epoch timestamp of delegation expiry.")

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> "DelegationContract":
        if self.expires_at <= self.issued_at:
            raise ValueError("Delegation expires_at must be strictly greater than issued_at.")
        return self


class UserContext(CoreasonModel):
    """
    Privacy-first representation of the human principal.
    """

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

    passport_id: str = Field(..., description="Unique JTI for this exact passport instance to prevent replay attacks.")
    user: UserContext
    system: SystemContext
    delegation: DelegationContract

    # Cryptographic Lineage
    issuer_uri: str = Field(..., description="The verified IdP that established the root of trust.")
    signature_hash: str = Field(
        ..., description="Hash of the originating JWT/Token signature. Anchors the passport to reality."
    )
