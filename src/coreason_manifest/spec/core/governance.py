import time
from typing import Annotated, Any, Literal, Mapping

from pydantic import Field, field_validator, model_validator

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.co_intelligence import CoIntelligencePolicy
from coreason_manifest.spec.core.types import NodeID, RiskLevel, ToolID
from coreason_manifest.spec.interop.exceptions import FaultSeverity, ManifestError, RecoveryAction, SemanticFault


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
    risk_level: RiskLevel = Field(..., description="Risk level.", examples=["standard"])
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

            raw_risk = data.get("risk_level")
            is_critical = False
            if (isinstance(raw_risk, RiskLevel) and raw_risk == RiskLevel.CRITICAL) or (
                isinstance(raw_risk, str) and raw_risk.lower() == "critical"
            ):
                is_critical = True

            if is_critical:
                if data.get("require_auth") is False:
                    raise ValueError("Critical tools must require authentication.")
                if data.get("require_auth") is None:
                    data["require_auth"] = True
            elif data.get("require_auth") is None:
                data["require_auth"] = False
        return data


class OperationalPolicy(CoreasonModel):
    """
    Dynamic configuration for operational limits, routing, and economic model-switching.
    Replaces static nested models with flat dictionaries for zero-downtime extensibility.
    """

    retry_counts: Mapping[str, Annotated[int, Field(ge=0)]] = Field(
        default_factory=dict, description="Granular control over retries per operation/node (NodeID keys)."
    )
    row_limits: Mapping[str, Annotated[int, Field(gt=0)]] = Field(
        default_factory=dict, description="Granular data retrieval limits (e.g., 'default', 'query_users')."
    )
    search_limits: Mapping[str, Annotated[int, Field(gt=0)]] = Field(
        default_factory=dict, description="Dynamic search result limits (e.g., 'web', 'vector')."
    )
    timeout_durations: Mapping[str, Annotated[int, Field(gt=0)]] = Field(
        default_factory=dict, description="Operation-specific timeouts in seconds (NodeID keys)."
    )
    cost_multipliers: Mapping[str, Annotated[float, Field(gt=0.0)]] = Field(
        default_factory=dict, description="Dynamic adjustment of cost thresholds (NodeID/ToolID keys)."
    )
    model_switching: Mapping[str, Annotated[float, Field(ge=0.0, le=1.0)]] = Field(
        default_factory=dict, description="Thresholds for tiered model degradation/swapping."
    )
    custom_thresholds: Mapping[str, float] = Field(
        default_factory=dict, description="Generic extension dictionary for float limits."
    )
    custom_limits: Mapping[str, int] = Field(
        default_factory=dict, description="Generic extension dictionary for integer limits."
    )


class Governance(CoreasonModel):
    """Governance constraints and SOTA Edge-First API routing policies."""

    max_risk_level: RiskLevel | None = Field(
        None,
        description=(
            "Global kill switch. No tool exceeding this risk level can be executed across the "
            "entire manifest, regardless of individual tool policies."
        ),
    )

    # New Global Guardrails (Hoisted from deleted nested models)
    rate_limit_rpm: int | None = Field(
        None,
        ge=0,
        description="Global requests per minute limit across the entire flow. PRECEDENCE: Acts as an absolute global ceiling, overriding any local node policies."
    )
    timeout_seconds: int | None = Field(
        None,
        gt=0,
        description="Global execution timeout in seconds. PRECEDENCE: Acts as an absolute hard ceiling, overriding any local timeout_durations."
    )
    cost_limit_usd: float | None = Field(
        None,
        ge=0.0,
        description="Global financial blast-radius limit (USD). PRECEDENCE: Triggers absolute halting, overriding any dynamic cost multipliers."
    )

    operational_policy: OperationalPolicy | None = Field(
        None, description="Global operational, financial, and compute constraints."
    )
    safety: Safety | None = Field(
        None,
        description="Safety configuration.",
        examples=[{"input_filtering": True, "pii_redaction": True, "content_safety": "high"}],
    )
    audit: Audit | None = Field(
        None, description="Audit configuration.", examples=[{"trace_retention_days": 7, "log_payloads": True}]
    )
    co_intelligence: CoIntelligencePolicy | None = Field(
        None, description="Human-AI Co-Intelligence policy.", examples=[{"global_intervention_mode": "blocking"}]
    )
    circuit_breaker: CircuitBreaker | None = Field(
        None,
        description="Circuit breaker policy.",
        examples=[{"error_threshold_count": 3, "reset_timeout_seconds": 30}],
    )
    tool_policy: Mapping[ToolID, ToolAccessPolicy] | None = Field(
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

    @model_validator(mode="after")
    def validate_global_precedence(self) -> "Governance":
        """SOTA defensive validation: ensure local dynamic policies do not exceed global hard ceilings."""
        if self.timeout_seconds is not None and self.operational_policy is not None:
            for node, local_timeout in self.operational_policy.timeout_durations.items():
                if local_timeout > self.timeout_seconds:
                    raise ValueError(
                        f"Contradiction: Local timeout for '{node}' ({local_timeout}s) "
                        f"cannot exceed the global hard ceiling timeout ({self.timeout_seconds}s)."
                    )
        return self


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
        ManifestError: If the circuit is open and timeout has not expired (ExecutionFault).
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
            # Raise strict structured error instead of raw exception
            raise ManifestError(
                fault=SemanticFault(
                    error_code="CRSN-EXEC-CIRCUIT-OPEN",
                    message=f"Circuit is OPEN for node {node_id}. Execution halted.",
                    severity=FaultSeverity.CRITICAL,
                    recovery_action=RecoveryAction.RETRY,
                    context={
                        "node_id": node_id,
                        "failure_count": state.failure_count,
                        "reset_timeout": policy.reset_timeout_seconds,
                    },
                )
            )


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
