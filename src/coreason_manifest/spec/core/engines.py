from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ReasoningEngine(BaseModel):
    """Configuration for deep thought."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: str
    thoughts_max: int
    min_confidence: float


class Reflex(BaseModel):
    """Configuration for fast action."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    model: str
    timeout_ms: int
    caching: bool


class Supervision(BaseModel):
    """The fault-tolerance config."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    strategy: Literal["resume", "restart", "escalate", "degrade"]
    max_retries: int
    fallback: str | None
    retry_delay_seconds: float = 1.0
    backoff_factor: float = 2.0
    default_payload: dict[str, Any] | None = None


class Optimizer(BaseModel):
    """Self-improvement config."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    teacher_model: str
    metric: str
    max_demonstrations: int
