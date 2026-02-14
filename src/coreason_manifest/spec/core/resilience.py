import re
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from coreason_manifest.spec.core.engines import ModelCriteria, ModelRef


class ErrorDomain(StrEnum):
    CLIENT = "client"
    SYSTEM = "system"
    LLM = "llm"
    TOOL = "tool"
    SECURITY = "security"
    CONTEXT = "context"
    DATA = "data"
    RESOURCE = "resource"
    TIMEOUT = "timeout"


class ResilienceStrategy(BaseModel):
    """Base configuration for resilience strategies."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str | None = Field(None, description="Human-readable ID for this strategy (e.g. 'gpt4-rate-limit-handler').")
    trace_activation: bool = Field(True, description="Emit telemetry event when this strategy triggers.")

    @field_validator("name")
    @classmethod
    def validate_name_slug(cls, v: str | None) -> str | None:
        if v is not None:
            if not re.match(r"^[a-z0-9_\-]+$", v):
                raise ValueError(
                    "Strategy name must be lowercase, alphanumeric, with underscores or dashes only (metric-safe)."
                )
        return v


class RetryStrategy(ResilienceStrategy):
    """Network/System focus: Retry with backoff."""

    type: Literal["retry"] = "retry"

    max_attempts: int = Field(..., gt=0, description="Hard limit on recovery loops.")
    backoff_factor: float = Field(2.0, ge=1.0, description="Exponential backoff multiplier.")
    initial_delay_seconds: float = Field(1.0, description="Initial wait time.")
    max_delay_seconds: float = Field(
        60.0, description="Ceiling for the backoff calculation (e.g., never sleep more than 60s)."
    )
    jitter: bool = Field(True, description="Add random jitter to delay.")


class FallbackStrategy(ResilienceStrategy):
    """Redundancy focus: Switch to a backup node."""

    type: Literal["fallback"] = "fallback"

    fallback_node_id: str = Field(..., description="The ID of the backup node/agent.")
    fallback_payload: dict[str, Any] | None = Field(None, description="Static data to inject if the node is skipped.")


class ReflexionStrategy(ResilienceStrategy):
    """Cognitive Correction focus: Use a critic to analyze and fix."""

    type: Literal["reflexion"] = "reflexion"

    max_attempts: int = Field(..., gt=0, description="Hard limit on recovery loops.")
    critic_model: ModelRef = Field(..., description="The model used to analyze the error.")
    critic_prompt: str = Field(..., description="Instructions for the critic (e.g., 'Identify logic errors').")
    include_trace: bool = Field(True, description="Whether to feed the execution trace to the critic.")
    max_trace_turns: int | None = Field(
        3, description="Limit the history feed to the Critic to the last N turns. Prevents context overflow."
    )
    critic_schema: dict[str, Any] | None = Field(
        None,
        description=(
            "JSON Schema to enforce structured output from the critic "
            "(e.g. {'properties': {'fix': {'type': 'string'}}})."
        ),
    )

    @field_validator("critic_schema")
    @classmethod
    def validate_json_schema(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
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
        # If include_trace is explicitly False, force max_trace_turns to None
        if isinstance(data, dict) and data.get("include_trace") is False:
            data["max_trace_turns"] = None
        return data

    @model_validator(mode="after")
    def validate_capabilities(self) -> "ReflexionStrategy":
        if self.critic_schema is not None and isinstance(self.critic_model, ModelCriteria):
            caps = self.critic_model.capabilities or []
            if "json_mode" not in caps:
                raise ValueError(
                    "ReflexionStrategy defines a 'critic_schema' but the 'critic_model' criteria "
                    "does not explicitly require 'json_mode'. Please add 'json_mode' to the model capabilities."
                )
        return self


class EscalationStrategy(ResilienceStrategy):
    """Human-in-the-Loop focus: Pause and wait for intervention."""

    type: Literal["escalate"] = "escalate"

    queue_name: str = Field(..., description="The task queue for suspended sessions.")
    notification_level: Literal["info", "warning", "critical"] = Field(..., description="Severity level.")
    timeout_seconds: int = Field(..., description="Max wait for human intervention.")
    template: str | None = Field(
        None,
        description=(
            "Jinja2 template for the human notification. "
            "Available context: {{ node_id }}, {{ error_type }}, {{ error_message }}, {{ inputs }}, {{ history }}."
        ),
    )

    @field_validator("template")
    @classmethod
    def validate_template_syntax(cls, v: str | None) -> str | None:
        if v and "{{" not in v:
            # Warning or Note: This looks like a static string, not a Jinja2 template.
            # We won't block it (valid use case), but it's good to note mentally.
            pass
        return v


# Polymorphic Union
ResilienceConfig = Annotated[
    RetryStrategy | FallbackStrategy | ReflexionStrategy | EscalationStrategy,
    Field(discriminator="type"),
]


class ErrorHandler(BaseModel):
    """
    Maps specific failure types to a specific strategy.

    Matching Logic:
    1. Inter-field: AND. If 'match_domain' AND 'match_error_code' are set, BOTH must match.
    2. Intra-field: OR. If 'match_domain' is ['LLM', 'SYSTEM'], the error can be EITHER.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    match_domain: list[ErrorDomain] | None = Field(None, description="List of error domains to handle.")
    match_pattern: str | None = Field(None, description="Regex for fine-grained error message matching.")
    match_error_code: list[str] | None = Field(None, description="List of specific error codes to match.")
    strategy: ResilienceConfig = Field(..., description="The polymorphic strategy to execute.")

    @field_validator("match_error_code", mode="before")
    @classmethod
    def normalize_error_codes(cls, v: Any) -> list[str] | None:
        if v is None:
            return None
        if isinstance(v, (int, str)):
            return [str(v)]
        if isinstance(v, list):
            return [str(item) for item in v]
        return v  # type: ignore # Let Pydantic raise validation error for other types

    @model_validator(mode="after")
    def validate_criteria_existence(self) -> "ErrorHandler":
        if not any([self.match_domain, self.match_pattern, self.match_error_code]):
            raise ValueError("ErrorHandler must specify at least one matching criterion (domain, pattern, or code).")
        return self

    @model_validator(mode="after")
    def validate_security_policy(self) -> "ErrorHandler":
        # Security Policy: Never blindly retry security violations.
        # Allow Reflexion (Correction) or Escalate (Human Review), but forbid Retry.
        if (
            self.match_domain
            and ErrorDomain.SECURITY in self.match_domain
            and self.strategy.type == "retry"
        ):
            raise ValueError(
                "Security Policy Violation: 'RetryStrategy' cannot be used with 'SECURITY' domain. "
                "Use 'ReflexionStrategy' (to fix the violation) or 'EscalationStrategy' instead."
            )
        return self

    @field_validator("match_pattern")
    @classmethod
    def validate_regex(cls, v: str | None) -> str | None:
        if v:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}") from e
        return v


class SupervisionPolicy(BaseModel):
    """
    The container attached to every Node.

    Note: Local supervision executes *before* global governance circuit breakers trip,
    unless the error is a GovernanceViolation.

    Evaluation Logic:
    1. Iterate through 'handlers' list in order (Index 0 -> N).
    2. First handler to match the error triggers its strategy.
    3. If no handlers match:
       - If 'default_strategy' is set, execute it.
       - If 'default_strategy' is None, raise the original exception.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    handlers: list[ErrorHandler] = Field(..., description="An ordered list of specific rules.")
    default_strategy: ResilienceConfig | None = Field(
        None, description="Catch-all strategy. If None, unhandled errors bubble up."
    )
    max_cumulative_actions: int = Field(
        10,
        description=(
            "Total number of recovery actions (retries + reflexions + fallbacks) "
            "allowed for this node before hard failure."
        ),
    )

    @model_validator(mode="after")
    def validate_limits(self) -> "SupervisionPolicy":
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
