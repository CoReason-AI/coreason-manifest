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

from ..common_base import ManifestBaseModel


class CapabilityType(StrEnum):
    """Architectural complexity of the agent."""

    ATOMIC = "atomic"
    GRAPH = "graph"


class DeliveryMode(StrEnum):
    """Supported transport mechanisms."""

    REQUEST_RESPONSE = "request_response"
    SERVER_SENT_EVENTS = "server_sent_events"


class AgentCapabilities(ManifestBaseModel):
    """Feature flags and capabilities for the agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: CapabilityType = Field(
        default=CapabilityType.GRAPH,
        description="The architectural complexity of the agent.",
    )
    delivery_mode: DeliveryMode = Field(
        default=DeliveryMode.REQUEST_RESPONSE,
        description="The primary transport mechanism.",
    )
    history_support: bool = Field(
        default=True,
        description="Whether the agent manages conversation history.",
    )
