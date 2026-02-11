from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    safety: Safety | None = None
    audit: Audit | None = None
    circuit_breaker: CircuitBreaker | None = None
