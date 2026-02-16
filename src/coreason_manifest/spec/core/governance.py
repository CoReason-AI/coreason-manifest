from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class ToolAccessPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    risk_level: Literal["critical", "standard", "minimal"]
    require_auth: bool | None = None
    allowed_roles: list[str] | None = Field(
        None, description="If None, allow all. If list, allow only these. Empty list implies deny-all."
    )

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("risk_level") == "critical":
                if data.get("require_auth") is False:
                    raise ValueError("Critical tools must require authentication.")
                if data.get("require_auth") is None:
                    data["require_auth"] = True
            elif data.get("require_auth") is None:
                data["require_auth"] = False
        return data


class Governance(BaseModel):
    """Governance constraints and policies."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    rate_limit_rpm: int | None = None
    timeout_seconds: int | None = None
    cost_limit_usd: float | None = None
    safety: Safety | None = None
    audit: Audit | None = None
    circuit_breaker: CircuitBreaker | None = None
    tool_policy: dict[str, ToolAccessPolicy] | None = None
    default_tool_policy: ToolAccessPolicy | None = None
