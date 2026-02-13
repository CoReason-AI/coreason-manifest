from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from coreason_manifest.spec.core.engines import ModelRef


class ErrorDomain(str, Enum):
    CLIENT = "client"
    SYSTEM = "system"
    LLM = "llm"
    TOOL = "tool"
    SECURITY = "security"


class ResilienceStrategy(BaseModel):
    """Base configuration for resilience strategies."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    max_attempts: int = Field(..., description="Hard limit on recovery loops.")


class RetryStrategy(ResilienceStrategy):
    """Network/System focus: Retry with backoff."""
    type: Literal["retry"] = "retry"

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
    Union[RetryStrategy, FallbackStrategy, ReflexionStrategy, EscalationStrategy],
    Field(discriminator="type"),
]


class ErrorHandler(BaseModel):
    """Maps specific failure types to a specific strategy."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    match_domain: list[ErrorDomain] = Field(..., description="List of error domains to handle.")
    match_pattern: str | None = Field(None, description="Regex for fine-grained error message matching.")
    strategy: ResilienceConfig = Field(..., description="The polymorphic strategy to execute.")


class SupervisionPolicy(BaseModel):
    """The container attached to every Node."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    handlers: list[ErrorHandler] = Field(..., description="An ordered list of specific rules.")
    default_strategy: ResilienceConfig = Field(..., description="Catch-all strategy (usually Escalation or Retry).")
