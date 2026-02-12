from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ConstitutionalScope(BaseModel):
    """
    Defines the ethical and safety boundaries for the cognitive process.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    principles: list[str] = Field(..., description="List of safety principles.")
    enforcement: Literal["warning", "block", "correction"] = Field(..., description="Action on violation.")
    inject_into_system_prompt: bool = Field(True, description="Whether to prepend principles to the prompt.")


class PolicyConfig(BaseModel):
    """Configuration for policy enforcement and risk management."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    allowed_capabilities: list[str] = Field(..., description="List of allowed capabilities (e.g. computer_use).")
    require_human_in_loop_for: list[str] = Field(..., description="Risk triggers that require human oversight.")
    max_risk_score: float = Field(..., ge=0.0, le=1.0, description="Maximum allowed risk score (0.0 - 1.0).")


class IntegrityConfig(BaseModel):
    """Configuration for cryptographic integrity and verification."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    hashing_algorithm: Literal["sha256", "sha512"] = Field(..., description="Hashing algorithm for state verification.")
    sign_states: bool = Field(..., description="Whether to digitally sign every blackboard state change.")


class Safety(BaseModel):
    """Safety and filtering configuration."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    input_filtering: bool
    pii_redaction: bool
    content_safety: Literal["high", "medium", "low"]


class Audit(BaseModel):
    """Audit and logging configuration."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    trace_retention_days: int
    log_payloads: bool


class CircuitBreaker(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    error_threshold_count: int = Field(..., description="Number of errors before opening the circuit.")
    reset_timeout_seconds: int = Field(..., description="Seconds to wait before attempting half-open state.")
    fallback_node_id: str | None = Field(None, description="Optional node to jump to when circuit opens.")


class Governance(BaseModel):
    """Governance constraints and policies."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    rate_limit_rpm: int | None = None
    timeout_seconds: int | None = None
    cost_limit_usd: float | None = None

    # Existing Governance
    safety: Safety | None = None
    audit: Audit | None = None
    circuit_breaker: CircuitBreaker | None = None

    # New SOTA Governance
    constitution: ConstitutionalScope | None = None
    policy: PolicyConfig | None = None
    integrity: IntegrityConfig | None = None
