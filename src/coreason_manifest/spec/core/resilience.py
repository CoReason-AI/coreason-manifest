import re
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from coreason_manifest.spec.core.engines import ModelRef


class ErrorDomain(StrEnum):
    CLIENT = "client"
    SYSTEM = "system"
    LLM = "llm"
    TOOL = "tool"
    SECURITY = "security"
    CONTEXT = "context"
    DATA = "data"
    RESOURCE = "resource"


class ResilienceStrategy(BaseModel):
    """Base configuration for resilience strategies."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    trace_activation: bool = Field(True, description="Emit telemetry event when this strategy triggers.")


class RetryStrategy(ResilienceStrategy):
    """Network/System focus: Retry with backoff."""

    type: Literal["retry"] = "retry"

    max_attempts: int = Field(..., gt=0, description="Hard limit on recovery loops.")
    backoff_factor: float = Field(2.0, description="Exponential backoff multiplier.")
    initial_delay_seconds: float = Field(1.0, description="Initial wait time.")
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


class EscalationStrategy(ResilienceStrategy):
    """Human-in-the-Loop focus: Pause and wait for intervention."""

    type: Literal["escalate"] = "escalate"

    queue_name: str = Field(..., description="The task queue for suspended sessions.")
    notification_level: Literal["info", "warning", "critical"] = Field(..., description="Severity level.")
    timeout_seconds: int = Field(..., description="Max wait for human intervention.")


# Polymorphic Union
ResilienceConfig = Annotated[
    RetryStrategy | FallbackStrategy | ReflexionStrategy | EscalationStrategy,
    Field(discriminator="type"),
]


class ErrorHandler(BaseModel):
    """
    Maps specific failure types to a specific strategy.

    Matching logic is strict intersection (AND). If multiple criteria are provided
    (e.g., domain AND pattern), the error must match ALL of them to trigger the strategy.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    match_domain: list[ErrorDomain] | None = Field(None, description="List of error domains to handle.")
    match_pattern: str | None = Field(None, description="Regex for fine-grained error message matching.")
    match_error_code: list[str] | None = Field(None, description="List of specific error codes to match.")
    strategy: ResilienceConfig = Field(..., description="The polymorphic strategy to execute.")

    @model_validator(mode="after")
    def validate_criteria_existence(self) -> "ErrorHandler":
        if not any([self.match_domain, self.match_pattern, self.match_error_code]):
            raise ValueError("ErrorHandler must specify at least one matching criterion (domain, pattern, or code).")
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
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    handlers: list[ErrorHandler] = Field(..., description="An ordered list of specific rules.")
    default_strategy: ResilienceConfig = Field(..., description="Catch-all strategy (usually Escalation or Retry).")
