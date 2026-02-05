# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum

from pydantic import ConfigDict, Field

from ..common_base import CoReasonBaseModel


class DeliveryMode(StrEnum):
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
