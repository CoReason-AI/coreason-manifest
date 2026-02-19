import time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    allowed_domains: list[str] = Field(default_factory=list)

    @field_validator("allowed_domains")
    @classmethod
    def validate_allowed_domains(cls, v: list[str]) -> list[str]:
        # SOTA Fix: Enforce strict canonicalization (RFC 8785 / IDNA 2008)
        # We import here to avoid circular dependency with gatekeeper.py
        # which imports Flow -> Governance.
        try:
            from coreason_manifest.utils.gatekeeper import canonicalize_domain
        except ImportError:
            # Fallback if gatekeeper is not yet available (e.g. during partial init)
            # Duplicate minimal logic or raise?
            # Ideally we rely on idna directly if needed, but DRY is better.
            # But gatekeeper depends on Flow which depends on Governance.
            # This is a hard cycle.
            # We should probably duplicate the logic or move canonicalize_domain to a common util.
            # Since I cannot create new files easily, I will duplicate logic using idna directly.
            import idna

            def canonicalize_domain(d: str) -> str:
                if not d: return ""
                d = d.rstrip(".").lower()
                try:
                    return idna.encode(d).decode("ascii")
                except idna.IDNAError:
                    return d

        return [canonicalize_domain(d) for d in v]


class CircuitState(BaseModel):
    """Runtime state of a circuit breaker for a specific node."""

    state: Literal["open", "closed", "half-open"] = "closed"
    failure_count: int = 0
    last_failure_time: float | None = None


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
            state.state = "half-open"
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
        state_store[node_id] = state

    if state.state == "open":
        return

    state.failure_count += 1
    state.last_failure_time = time.time()

    if state.failure_count >= policy.error_threshold_count:
        state.state = "open"


def record_success(node_id: str, state_store: dict[str, CircuitState]) -> None:
    """
    Record a success, resetting the circuit state to closed.
    """
    state = state_store.get(node_id)
    if state:
        state.state = "closed"
        state.failure_count = 0
        state.last_failure_time = None
