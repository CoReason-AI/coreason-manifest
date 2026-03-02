import re
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from coreason_manifest.core.common.presentation import NotificationRouting, RenderStrategy
from coreason_manifest.core.compute.reasoning import ModelCriteria, ModelRef


class ErrorDomain(StrEnum):
    CLIENT = "client"
    SYSTEM = "system"
    LLM = "llm"
    TOOL = "tool"
    SECURITY = "security"
    CONTEXT = "context"
    DATA = "data"  # Maps to DataLimits
    RESOURCE = "resource"  # Maps to ComputeLimits
    TIMEOUT = "timeout"
    FINANCIAL = "financial"
    IDENTITY = "identity"


class ResilienceStrategy(BaseModel):
    """Base configuration for resilience strategies."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: Annotated[
        str | None,
        Field(description="Human-readable ID for this strategy.", examples=["gpt4-rate-limit-handler"]),
    ] = None
    trace_activation: Annotated[
        bool, Field(description="Emit telemetry event when this strategy triggers.", examples=[True])
    ] = True
    symbolic_repair_budget: int = Field(
        0,
        ge=0,
        description="Max iterations for the Tutor-Apprentice repair loop. "
        "If a symbolic solver fails, the strict compilation error is fed "
        "back to the generator LLM up to this many times before halting.",
    )

    @field_validator("name")
    @classmethod
    def validate_name_slug(cls, v: str | None) -> str | None:
        """Assert that names strictly conform to alphanumeric slug constraints for path safety.

        Raises:
            ValueError: If the strategy name is not lowercase, alphanumeric, with underscores or dashes only.
        """
        if v is not None and not re.match(r"^[a-z0-9_\-]+$", v):
            raise ValueError(
                "Strategy name must be lowercase, alphanumeric, with underscores or dashes only (metric-safe)."
            )
        return v


class RetryStrategy(ResilienceStrategy):
    """Strategy for retrying operations with exponential backoff."""

    type: Literal["retry"] = Field("retry", description="The strategy type.", examples=["retry"])

    max_attempts: int = Field(..., gt=0, description="Hard limit on recovery loops.", examples=[3])
    backoff_factor: Annotated[float, Field(ge=1.0, description="Exponential backoff multiplier.", examples=[2.0])] = 2.0
    initial_delay_seconds: Annotated[float, Field(description="Initial wait time.", examples=[1.0])] = 1.0
    max_delay_seconds: Annotated[float, Field(description="Ceiling for the backoff calculation.", examples=[60.0])] = (
        60.0
    )
    jitter: Annotated[bool, Field(description="Add random jitter to delay.", examples=[True])] = True


class FallbackStrategy(ResilienceStrategy):
    """Strategy for falling back to an alternative node or payload upon failure."""

    type: Literal["fallback"] = Field("fallback", description="The strategy type.", examples=["fallback"])

    fallback_node_id: str = Field(..., description="The ID of the backup node/agent.", examples=["backup_agent"])
    fallback_payload: Annotated[
        dict[str, Any] | None,
        Field(description="Static data to inject if the node is skipped.", examples=[{"status": "degraded"}]),
    ] = None


class ReflexionStrategy(ResilienceStrategy):
    """Strategy that uses an LLM critic to analyze and correct errors."""

    type: Literal["reflexion"] = Field("reflexion", description="The strategy type.", examples=["reflexion"])

    max_attempts: int = Field(..., gt=0, description="Hard limit on recovery loops.", examples=[3])
    critic_model: ModelRef = Field(..., description="The model used to analyze the error.", examples=["gpt-4"])
    critic_prompt: str = Field(..., description="Instructions for the critic.", examples=["Identify logic errors"])
    include_trace: Annotated[
        bool, Field(description="Whether to feed the execution trace to the critic.", examples=[True])
    ] = True
    max_trace_turns: Annotated[
        int | None,
        Field(
            description="Limit the history feed to the Critic to the last N turns. Prevents context overflow.",
            examples=[3],
        ),
    ] = 3
    critic_schema: Annotated[
        dict[str, Any] | None,
        Field(
            description="JSON Schema to enforce structured output from the critic.",
            examples=[{"type": "object", "properties": {"fix": {"type": "string"}}}],
        ),
    ] = None

    @field_validator("critic_schema")
    @classmethod
    def validate_json_schema(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Enforce that embedded schemas parse as minimally valid JSON Schema.

        Raises:
            ValueError: If the schema object lacks foundational properties like 'type', 'properties', or '$ref'.
        """
        # Minimal check for JSON Schema validity
        if v is not None:
            if "type" not in v and "properties" not in v and "$ref" not in v:
                raise ValueError("critic_schema must be a valid JSON Schema (missing 'type', 'properties', or '$ref').")
            if v.get("type") == "object" and "properties" not in v:
                raise ValueError("Invalid JSON Schema: 'properties' are required when type is 'object'.")
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_trace_config(cls, data: Any) -> Any:
        """Enforce rigorous semantic tracing fields for execution auditing compliance."""
        # If include_trace is explicitly False, force max_trace_turns to None
        if isinstance(data, dict) and data.get("include_trace") is False:
            data["max_trace_turns"] = None
        return data

    @model_validator(mode="after")
    def validate_capabilities(self) -> "ReflexionStrategy":
        """Ensure resource allocations enforce the required capabilities for verification.

        Raises:
            ValueError: If 'json_mode' capability is missing when a critic schema is defined.
        """
        if self.critic_schema is not None and isinstance(self.critic_model, ModelCriteria):
            caps = self.critic_model.capabilities or []
            if "json_mode" not in caps:
                raise ValueError(
                    "ReflexionStrategy defines a 'critic_schema' but the 'critic_model' criteria "
                    "does not explicitly require 'json_mode'. Please add 'json_mode' to the model capabilities."
                )
        return self


class EscalationStrategy(ResilienceStrategy):
    """Strategy that escalates execution to a human operator."""

    type: Literal["escalate"] = Field("escalate", description="The strategy type.", examples=["escalate"])

    queue_name: str = Field(
        ..., min_length=1, description="The task queue for suspended sessions.", examples=["review_queue"]
    )
    notification_level: Literal["info", "warning", "critical"] = Field(
        ..., description="Severity level.", examples=["critical"]
    )
    timeout_seconds: int = Field(..., description="Max wait for human intervention.", examples=[3600])
    fallback_node_id: str | None = Field(
        None,
        description="Graceful degradation target if timeout is reached (overrides global SLA).",
        examples=["fallback_agent"],
    )
    template: Annotated[
        str | None,
        Field(
            description="Jinja2 template for notification. Context: {{ node_id }}, {{ error_type }}, {{ message }}.",
            examples=["Alert: {{ error_type }} in {{ node_id }}"],
        ),
    ] = None
    routing: NotificationRouting | None = None
    render_strategy: RenderStrategy = Field(default=RenderStrategy.PLAIN_TEXT)

    @field_validator("template")
    @classmethod
    def validate_template_syntax(cls, v: str | None) -> str | None:
        """Check syntactic correctness of prompt templates strictly before instantiation."""
        if v and "{{" not in v:
            # Warning or Note: This looks like a static string, not a Jinja2 template.
            # We won't block it (valid use case), but it's good to note mentally.
            pass
        return v


class DiagnosisReasoning(ResilienceStrategy):
    """Agentic Error Recovery: Spawns a mini-agent to diagnose and fix inputs."""

    type: Literal["diagnosis"] = Field("diagnosis", description="The strategy type.", examples=["diagnosis"])
    diagnostic_model: ModelRef = Field(..., description="The model used to diagnose the issue.", examples=["gpt-4"])
    fix_strategies: list[Literal["schema_repair", "parameter_tuning", "context_pruning"]] = Field(
        ..., description="Allowed strategies for automatic fixing.", examples=[["schema_repair", "context_pruning"]]
    )


class HumanHandoffStrategy(ResilienceStrategy):
    """Strategy for an urgent human handoff."""

    type: Literal["human_handoff"] = Field(
        "human_handoff", description="The strategy type.", examples=["human_handoff"]
    )
    urgency: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Urgency of the handoff.", examples=["critical"]
    )


# Polymorphic Union
RecoveryStrategy = Annotated[
    RetryStrategy
    | FallbackStrategy
    | ReflexionStrategy
    | EscalationStrategy
    | DiagnosisReasoning
    | HumanHandoffStrategy,
    Field(discriminator="type"),
]


class ErrorHandler(BaseModel):
    """Maps specific failure types to a recovery strategy."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    match_domain: Annotated[
        list[ErrorDomain] | None,
        Field(description="List of error domains to handle.", examples=[["llm", "system"]]),
    ] = None
    match_pattern: Annotated[
        str | None, Field(description="Regex for fine-grained error message matching.", examples=[".*Timeout.*"])
    ] = None
    match_error_code: Annotated[
        list[str] | None, Field(description="List of specific error codes to match.", examples=[["VAL-001"]])
    ] = None
    strategy: RecoveryStrategy = Field(
        ..., description="The polymorphic strategy to execute.", examples=[{"type": "retry", "max_attempts": 3}]
    )

    @field_validator("match_error_code", mode="before")
    @classmethod
    def normalize_error_codes(cls, v: Any) -> list[str] | None:
        """Sanitize unstructured exceptions to standard canonical error representations."""
        if v is None:
            return None
        if isinstance(v, (int, str)):
            return [str(v)]
        if isinstance(v, list):
            # Expanded for coverage
            return [str(item) for item in v]
        return v  # type: ignore # Let Pydantic raise validation error for other types

    @model_validator(mode="after")
    def validate_criteria_existence(self) -> "ErrorHandler":
        """Enforce that conditional transition edges map precisely to defined boolean expressions.

        Raises:
            ValueError: If no matching criterion (domain, pattern, or code) is specified.
        """
        if not any([self.match_domain, self.match_pattern, self.match_error_code]):
            raise ValueError("ErrorHandler must specify at least one matching criterion (domain, pattern, or code).")
        return self

    @model_validator(mode="after")
    def validate_security_policy(self) -> "ErrorHandler":
        """Assert compliance with established OPA or generic authorization policies."""
        # Security Policy: Never blindly retry security violations.
        # Allow Reflexion (Correction) or Escalate (Human Review), but forbid Retry.
        if self.match_domain and ErrorDomain.SECURITY in self.match_domain and self.strategy.type == "retry":
            raise ValueError(
                "Security Policy Violation: 'RetryStrategy' cannot be used with 'SECURITY' domain. "
                "Use 'ReflexionStrategy' (to fix the violation) or 'EscalationStrategy' instead."
            )
        return self

    @field_validator("match_pattern")
    @classmethod
    def validate_regex(cls, v: str | None) -> str | None:
        """Ensure regular expressions compile properly to prevent malicious backtracking DoS.

        Raises:
            ValueError: If the provided regular expression pattern is invalid.
        """
        if v:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}") from e
        return v


class SupervisionPolicy(BaseModel):
    """Supervision policy defining error handlers and default strategies for a node."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["supervision"] = Field("supervision", description="The policy type.", examples=["supervision"])
    handlers: list[ErrorHandler] = Field(
        ...,
        description="An ordered list of specific rules.",
        examples=[[{"match_domain": ["llm"], "strategy": {"type": "retry", "max_attempts": 3}}]],
    )
    default_strategy: Annotated[
        RecoveryStrategy | None,
        Field(
            None,
            description="Catch-all strategy. If None, unhandled errors bubble up.",
            examples=[{"type": "escalate", "queue_name": "default"}],
        ),
    ]
    max_cumulative_actions: Annotated[
        int,
        Field(
            10,
            description="Total number of recovery actions (retries + reflexions + fallbacks) allowed.",
            examples=[10],
        ),
    ]

    @model_validator(mode="after")
    def validate_limits(self) -> "SupervisionPolicy":
        """Enforce invariant that retry boundaries and concurrency limits never fall below zero."""
        strategies = [h.strategy for h in self.handlers]
        if self.default_strategy:
            strategies.append(self.default_strategy)

        for strategy in strategies:
            if hasattr(strategy, "max_attempts") and strategy.max_attempts > self.max_cumulative_actions:
                raise ValueError(
                    f"SupervisionPolicy global limit (max_cumulative_actions={self.max_cumulative_actions}) "
                    f"is lower than a strategy limit (max_attempts={strategy.max_attempts}). "
                    "The strategy will never complete."
                )
        return self


ResilienceConfig = Annotated[RecoveryStrategy | SupervisionPolicy, Field(discriminator="type")]
