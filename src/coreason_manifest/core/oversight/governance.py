import time
from enum import IntEnum
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from coreason_manifest.core.common.base import CoreasonModel
from coreason_manifest.core.common.exceptions import FaultSeverity, ManifestError, RecoveryAction, SemanticFault
from coreason_manifest.core.oversight.intervention import CoIntelligencePolicy
from coreason_manifest.core.oversight.mixed_initiative import MixedInitiativePolicy
from coreason_manifest.core.primitives.types import MiddlewareID, NodeID, RiskLevel, ToolID


class RequestCriticality(IntEnum):
    CRITICAL = 10
    STANDARD = 5
    SHEDDABLE = 1


class SemanticCacheConfig(CoreasonModel):
    enabled: bool = Field(True, description="Enable semantic caching.", examples=[True])
    similarity_threshold: float = Field(
        0.85, ge=0.0, le=1.0, description="Similarity threshold for cache hits.", examples=[0.85]
    )
    ttl_seconds: int | None = Field(3600, description="Time to live for cache entries in seconds.", examples=[3600])


class TrafficPolicy(CoreasonModel):
    criticality: RequestCriticality = Field(
        RequestCriticality.STANDARD, description="Request criticality level.", examples=[RequestCriticality.STANDARD]
    )
    rate_limit_rpm: int | None = Field(None, gt=0, description="Rate limit in requests per minute.", examples=[60])
    rate_limit_tpm: int | None = Field(None, gt=0, description="Rate limit in tokens per minute.", examples=[10000])
    semantic_cache: SemanticCacheConfig | None = Field(
        default_factory=SemanticCacheConfig,
        description="Semantic cache configuration.",
        examples=[{"enabled": True, "similarity_threshold": 0.85, "ttl_seconds": 3600}],
    )


class UnicodeSanitization(CoreasonModel):
    """Declarative instructions for the runtime middleware to neutralize invisible payload attacks."""

    strip_invisible_tags: bool = Field(
        True, description="Strips Unicode Tag Plane characters (U+E0000-U+E007F) used for ASCII Smuggling."
    )
    strip_bidi_overrides: bool = Field(
        True, description="Strips Bidirectional formatting characters used to mask malicious payloads."
    )
    normalization_form: Literal["NFC", "NFKC", "none"] = Field("NFC", description="Required canonical normalization.")


class Safety(CoreasonModel):
    """Safety and filtering configuration."""

    input_filtering: bool = Field(..., description="Enable input filtering.", examples=[True])
    pii_redaction: bool = Field(..., description="Enable PII redaction.", examples=[True])
    content_safety: Literal["high", "medium", "low"] = Field(
        ..., description="Content safety level.", examples=["high"]
    )
    safety_preamble: str | None = Field(
        None,
        description="Mandatory safety instruction injected into the system prompt deterministically by the runtime.",
    )
    legal_disclaimer: str | None = Field(
        None, description="Text that must be appended to the final output deterministically by the runtime."
    )
    unicode_sanitization: UnicodeSanitization = Field(
        default_factory=UnicodeSanitization, description="Hardened protections against invisible character injection."
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
        """Enforce baseline operational requirements on incoming component payload.

        Raises:
            ValueError: Yields a validation error if input logic fails syntactic or topological constraints.
        """
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


class FinancialLimits(CoreasonModel):
    max_cost_usd: float | None = Field(None, ge=0.0, description="Maximum cost in USD.", examples=[100.0])
    max_tokens_total: int | None = Field(None, gt=0, description="Maximum total tokens allowed.", examples=[50000])
    budget_depletion_routing: str | None = Field(
        None,
        description="Model ID to fallback to when budget hits 90% depletion (e.g., swap o1-pro to gpt-4o-mini).",
        examples=["gpt-4o-mini"],
    )
    max_transaction_cost_usd: float | None = Field(
        None, ge=0.0, description="Maximum allowed cost for a single transaction or branch.", examples=[5.0]
    )


class DataLimits(CoreasonModel):
    max_rows_per_query: int | None = Field(None, gt=0, description="Maximum rows returned per query.", examples=[100])
    max_payload_bytes: int | None = Field(
        None, gt=0, description="Max bytes for active memory insertion/API responses.", examples=[1048576]
    )
    max_search_results: int | None = Field(None, gt=0, description="Maximum search results to return.", examples=[10])


class ComputeLimits(CoreasonModel):
    max_execution_time_seconds: int | None = Field(
        None, gt=0, description="Maximum execution time in seconds.", examples=[300]
    )
    max_cognitive_steps: int | None = Field(None, gt=0, description="Max turn/DAG transitions.", examples=[50])
    max_concurrent_agents: int | None = Field(
        None, gt=0, description="Maximum number of concurrent agents.", examples=[10]
    )
    max_tokens_per_turn: int | None = Field(
        None, gt=0, description="Maximum allowed tokens per execution turn.", examples=[4000]
    )
    context_compression_strategy: Literal["none", "summarize", "truncate_oldest"] = Field(
        "none", description="Strategy to compress context when it exceeds bounds.", examples=["summarize"]
    )


class OperationalPolicy(CoreasonModel):
    financial: FinancialLimits | None = Field(None, description="Financial limits configuration.")
    data: DataLimits | None = Field(None, description="Data usage limits configuration.")
    compute: ComputeLimits | None = Field(None, description="Compute resources limits configuration.")
    traffic: TrafficPolicy | None = Field(None, description="Traffic and rate limit configuration.")


class Governance(CoreasonModel):
    """Governance constraints and policies."""

    active_middlewares: list[MiddlewareID] = Field(
        default_factory=list,
        description=(
            "Ordered list of middleware references (from definitions.middlewares) to apply sequentially "
            "to execution requests and streams."
        ),
        examples=[["pii_redactor", "toxicity_filter"]],
    )
    max_risk_level: RiskLevel | None = Field(
        None,
        description=(
            "Global kill switch. No tool exceeding this risk level can be executed across the "
            "entire manifest, regardless of individual tool policies."
        ),
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
    opa_policies: list[str] = Field(
        default_factory=list,
        description="References to .rego files or inline Open Policy Agent definitions for custom enterprise rules.",
    )
    mixed_initiative: MixedInitiativePolicy | None = Field(None)

    @field_validator("active_middlewares")
    @classmethod
    def deduplicate_middlewares(cls, v: list[MiddlewareID]) -> list[MiddlewareID]:
        """Deduplicate middleware identifiers while preserving topological execution order."""
        return list(dict.fromkeys(v))

    @field_validator("allowed_domains")
    @classmethod
    def validate_allowed_domains(cls, v: list[str]) -> list[str]:
        """Enforce explicit canonicalization across all allowed operational domains."""
        return [d.strip().lower() for d in v]


class CircuitState(CoreasonModel):
    """Runtime state of a circuit breaker for a specific node."""

    state: Literal["open", "closed", "half-open"] = Field("closed", description="Current state.", examples=["closed"])
    failure_count: int = Field(0, description="Consecutive failure count.", examples=[0])
    last_failure_time: float | None = Field(None, description="Timestamp of last failure.", examples=[1633024800.0])


class CircuitOpenError(Exception):
    """Raised when an operation is attempted on an open circuit."""


def check_circuit(node_id: str, policy: CircuitBreaker, state_store: dict[str, CircuitState]) -> None:
    """Enforce circuit breaker policy prior to execution.

    Mutates state_store to reflect state changes.

    Raises:
        ManifestError: Yields a CRITICAL execution fault on validation or security policy failure.
    """
    # Get or create state
    state = state_store.get(node_id)
    if not state:
        state = CircuitState()
        state_store[node_id] = state

    if state.state == "open":
        if state.last_failure_time and (time.monotonic() - state.last_failure_time > policy.reset_timeout_seconds):
            # Timeout expired, try half-open
            # Immutability: Create new state and update store
            new_state = state.model_copy(update={"state": "half-open"})
            state_store[node_id] = new_state
            # We don't reset failure_count here; usually we wait for a success to close and reset.
        else:
            # Raise strict structured error instead of raw exception
            raise ManifestError(
                fault=SemanticFault(
                    error_code="EXEC-CIRCUIT-OPEN",
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
    """Record a failed execution, transitioning circuit to open if threshold exceeded.

    Mutates state_store to reflect state changes.
    """
    state = state_store.get(node_id)
    if not state:
        state = CircuitState()
        # Just continue to calculate new state

    if state.state == "open":
        return

    new_failure_count = state.failure_count + 1
    new_last_failure_time = time.monotonic()
    new_status: Literal["open", "closed", "half-open"] = state.state

    if new_failure_count >= policy.error_threshold_count:
        new_status = "open"

    new_state = state.model_copy(
        update={"failure_count": new_failure_count, "last_failure_time": new_last_failure_time, "state": new_status}
    )
    state_store[node_id] = new_state


def record_success(node_id: str, state_store: dict[str, CircuitState]) -> None:
    """Record successful execution, resetting failure metrics and closing circuit.

    Mutates state_store to reflect state changes.
    """
    state = state_store.get(node_id)
    if state:
        new_state = state.model_copy(update={"state": "closed", "failure_count": 0, "last_failure_time": None})
        state_store[node_id] = new_state
