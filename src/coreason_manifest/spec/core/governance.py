import time
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import NodeID, RiskLevel, ToolID


class Safety(CoreasonModel):
    """Safety and filtering configuration."""

    input_filtering: bool = Field(..., description="Enable input filtering.", examples=[True])
    pii_redaction: bool = Field(..., description="Enable PII redaction.", examples=[True])
    content_safety: Literal["high", "medium", "low"] = Field(
        ..., description="Content safety level.", examples=["high"]
    )


class Audit(CoreasonModel):
    """Audit and logging configuration."""

    trace_retention_days: int = Field(..., description="Days to retain traces.", examples=[30])
    log_payloads: bool = Field(..., description="Log full payloads.", examples=[False])


class CircuitBreaker(CoreasonModel):
    error_threshold_count: int = Field(..., description="Number of errors before opening the circuit.", examples=[5])
    reset_timeout_seconds: int = Field(
        ..., description="Seconds to wait before attempting half-open state.", examples=[60]
    )
    fallback_node_id: NodeID | None = Field(
        None, description="Optional node to jump to when circuit opens.", examples=["fallback_agent"]
    )


class ToolAccessPolicy(CoreasonModel):
    risk_level: RiskLevel = Field(
        ..., description="Risk level.", examples=["standard"]
    )
    require_auth: bool | None = Field(None, description="Require authentication.", examples=[True])
    allowed_roles: list[str] | None = Field(
        None,
        description="If None, allow all. If list, allow only these. Empty list implies deny-all.",
        examples=[["admin"]],
    )

    @model_validator(mode="before")
    @classmethod
    def set_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Functional purity: copy data
            data = data.copy()
            if data.get("risk_level") == "critical":
                if data.get("require_auth") is False:
                    raise ValueError("Critical tools must require authentication.")
                if data.get("require_auth") is None:
                    data["require_auth"] = True
            elif data.get("require_auth") is None:
                data["require_auth"] = False
        return data


class Governance(CoreasonModel):
    """Governance constraints and policies."""

    max_risk_level: RiskLevel | None = Field(
        None,
        description="Global kill switch. No tool exceeding this risk level can be executed across the entire manifest, regardless of individual tool policies.",
    )
    rate_limit_rpm: int | None = Field(None, description="Rate limit in requests per minute.", examples=[60])
    timeout_seconds: int | None = Field(None, description="Global execution timeout.", examples=[300])
    cost_limit_usd: float | None = Field(None, description="Cost limit in USD.", examples=[10.0])
    safety: Safety | None = Field(
        None,
        description="Safety configuration.",
        examples=[{"input_filtering": True, "pii_redaction": True, "content_safety": "high"}],
    )
    audit: Audit | None = Field(
        None, description="Audit configuration.", examples=[{"trace_retention_days": 7, "log_payloads": True}]
    )
    circuit_breaker: CircuitBreaker | None = Field(
        None,
        description="Circuit breaker policy.",
        examples=[{"error_threshold_count": 3, "reset_timeout_seconds": 30}],
    )
    tool_policy: dict[ToolID, ToolAccessPolicy] | None = Field(
        None,
        description="Per-tool access policies.",
        examples=[{"web_search": {"risk_level": "standard", "require_auth": False}}],
    )
    default_tool_policy: ToolAccessPolicy | None = Field(
        None, description="Default tool policy.", examples=[{"risk_level": "safe", "require_auth": False}]
    )
    allowed_domains: list[str] = Field(
        default_factory=list, description="Allowed external domains.", examples=[["example.com"]]
    )

    @field_validator("allowed_domains")
    @classmethod
    def validate_allowed_domains(cls, v: list[str]) -> list[str]:
        # Architectural Note: Enforce strict canonicalization (RFC 8785 / IDNA 2008)
        from urllib.parse import urlparse

        from coreason_manifest.utils.net_utils import canonicalize_domain

        cleaned = []
        for d in v:
            # Architectural Note: Extract host from URL-like strings to prevent policy bypass via paths/schemes.
            # Handle "https://example.com/api" -> "example.com"
            # Handle "example.com/api" -> "example.com"
            candidate = d
            if "://" in candidate:
                parsed = urlparse(candidate)
                candidate = parsed.hostname or candidate
            elif "/" in candidate:
                # Schemeless path heuristic
                parsed = urlparse(f"http://{candidate}")
                candidate = parsed.hostname or candidate

            cleaned.append(canonicalize_domain(candidate))

        return cleaned


class CircuitState(CoreasonModel):
    """Runtime state of a circuit breaker for a specific node."""

    state: Literal["open", "closed", "half-open"] = Field("closed", description="Current state.")
    failure_count: int = Field(0, description="Consecutive failure count.")
    last_failure_time: float | None = Field(None, description="Timestamp of last failure.")


class CircuitOpenError(Exception):
    """Raised when an operation is attempted on an open circuit."""


def check_circuit(node_id: str, policy: CircuitBreaker, state_store: dict[str, CircuitState]) -> None:
    """
    Middleware hook to enforce circuit breaker policy.

    Args:
        node_id: The ID of the node being executed.
        policy: The circuit breaker policy configuration.
        state_store: A mutable dictionary mapping node IDs to CircuitState objects.

    Raises:
        CircuitOpenError: If the circuit is open and timeout has not expired.
    """
    # Get or create state
    state = state_store.get(node_id)
    if not state:
        state = CircuitState()
        state_store[node_id] = state

    if state.state == "open":
        if state.last_failure_time and (time.time() - state.last_failure_time > policy.reset_timeout_seconds):
            # Timeout expired, try half-open
            # Immutability: Create new state and update store
            new_state = state.model_copy(update={"state": "half-open"})
            state_store[node_id] = new_state
            # We don't reset failure_count here; usually we wait for a success to close and reset.
        else:
            raise CircuitOpenError(f"Circuit is OPEN for node {node_id}")


def record_failure(node_id: str, policy: CircuitBreaker, state_store: dict[str, CircuitState]) -> None:
    """
    Record a failure for the given node and open the circuit if threshold is reached.
    """
    state = state_store.get(node_id)
    if not state:
        state = CircuitState()
        # Just continue to calculate new state

    if state.state == "open":
        return

    new_failure_count = state.failure_count + 1
    new_last_failure_time = time.time()
    new_status: Literal["open", "closed", "half-open"] = state.state

    if new_failure_count >= policy.error_threshold_count:
        new_status = "open"

    new_state = state.model_copy(
        update={"failure_count": new_failure_count, "last_failure_time": new_last_failure_time, "state": new_status}
    )
    state_store[node_id] = new_state


def record_success(node_id: str, state_store: dict[str, CircuitState]) -> None:
    """
    Record a success, resetting the circuit state to closed.
    """
    state = state_store.get(node_id)
    if state:
        new_state = state.model_copy(update={"state": "closed", "failure_count": 0, "last_failure_time": None})
        state_store[node_id] = new_state
