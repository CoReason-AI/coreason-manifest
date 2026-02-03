# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Defines the data structures for the Coreason Agent Protocol (CAP)."""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from coreason_manifest.common import CoReasonBaseModel
from coreason_manifest.definitions.events import CloudEvent
from coreason_manifest.definitions.presentation import StreamPacket
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.session import SessionContext

DEFAULT_ENDPOINT_PATH = "/v1/assist"
CONTENT_TYPE_SSE = "text/event-stream"
STREAM_PACKET_EVENT_TYPE = "stream.packet"


class ServerSentEvent(CoReasonBaseModel):
    """The strict wire format for a single chunk in the response stream."""

    event: str = Field(..., description="The event type (e.g., 'ai.coreason.node.started'). Maps to CloudEvent 'type'.")
    data: str = Field(..., description="The payload. MUST be a JSON string of the CloudEvent.")
    id: Optional[str] = Field(None, description="The unique ID of the event for stream resumption.")

    @classmethod
    def from_cloud_event(cls, event: CloudEvent[Any]) -> "ServerSentEvent":
        """Factory method to create a ServerSentEvent from a CloudEvent.

        Args:
            event: The CloudEvent to wrap.

        Returns:
            A strictly formatted SSE object ready for the wire.
        """
        return cls(
            event=event.type,
            data=event.to_json(),
            id=event.id,
        )

    @classmethod
    def from_stream_packet(cls, packet: StreamPacket) -> "ServerSentEvent":
        """Factory method to create a ServerSentEvent from a StreamPacket.

        Args:
            packet: The StreamPacket to wrap.

        Returns:
            A strictly formatted SSE object ready for the wire.
        """
        return cls(
            event=STREAM_PACKET_EVENT_TYPE,
            data=packet.to_json(),
            id=str(packet.stream_id),
        )


class ServiceRequest(CoReasonBaseModel):
    """The envelope for agent invocations, strictly separating context from payload.

    Allows the engine to strip off authentication/tracing (SessionContext)
    before passing the raw payload (AgentRequest) to the agent logic.
    """

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(..., description="Unique ID for this HTTP transaction.")
    context: SessionContext = Field(..., description="Immutable session context (Who is asking).")
    payload: AgentRequest = Field(..., description="The actual query payload (What they are asking).")


class ServiceResponse(CoReasonBaseModel):
    """Standard synchronous response for non-streaming agent invocations."""

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(..., description="Echoes the request ID.")
    created_at: datetime = Field(..., description="Timestamp of response creation.")
    output: Dict[str, Any] = Field(..., description="The final result.")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Execution stats like token count, latency.")


class HealthCheckResponse(CoReasonBaseModel):
    """Response model for service health checks."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok", "degraded", "maintenance"] = Field(..., description="Current service status.")
    agent_id: UUID = Field(..., description="Unique ID of the agent instance.")
    version: str = Field(..., description="Semantic version string.")
    uptime_seconds: float = Field(..., description="Service uptime in seconds.")


class ServiceContract(CoReasonBaseModel):
    """Defines the Coreason Agent Protocol (CAP) interface and generates its OpenAPI specification."""

    def generate_openapi_path(self) -> Dict[str, Any]:
        """Generates the OpenAPI Path Object for POST /v1/assist.

        Returns:
            A Dictionary representing the OpenAPI Path Object.
        """
        return {
            "post": {
                "summary": "Invoke Agent",
                "requestBody": {"content": {"application/json": {"schema": ServiceRequest.model_json_schema()}}},
                "responses": {
                    "200": {
                        "description": "Event Stream",
                        "content": {CONTENT_TYPE_SSE: {"schema": {"type": "string"}}},
                    },
                    "400": {"description": "Client Error"},
                    "500": {"description": "Server Error"},
                },
            }
        }
