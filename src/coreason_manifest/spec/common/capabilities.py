from enum import Enum

from pydantic import ConfigDict, Field

from ..common_base import CoReasonBaseModel


class DeliveryMode(str, Enum):
    """Supported transport mechanisms."""

    REQUEST_RESPONSE = "request_response"
    SSE = "sse"


class AgentCapabilities(CoReasonBaseModel):
    """Feature flags and capabilities for the agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    delivery_mode: list[DeliveryMode] = Field(
        default_factory=lambda: [DeliveryMode.SSE],
        description="Supported transport mechanisms.",
    )
    history_support: bool = Field(
        default=True,
        description="Whether the agent supports conversation history/context.",
    )
