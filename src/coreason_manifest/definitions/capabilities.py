from enum import Enum
from typing import List

from pydantic import ConfigDict, Field

from ..common import CoReasonBaseModel


class DeliveryMode(str, Enum):
    """Supported transport mechanisms."""

    REQUEST_RESPONSE = "request_response"
    SSE = "sse"


class AgentCapabilities(CoReasonBaseModel):
    """Feature flags and capabilities for the agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    delivery_mode: List[DeliveryMode] = Field(
        default_factory=lambda: [DeliveryMode.SSE],
        description="Supported transport mechanisms.",
    )
    history_support: bool = Field(
        default=True,
        description="Whether the agent supports conversation history/context.",
    )
