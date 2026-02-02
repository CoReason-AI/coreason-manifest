# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict, Optional

from pydantic import Field

from coreason_manifest.definitions.base import CoReasonBaseModel
from coreason_manifest.definitions.events import CloudEvent
from coreason_manifest.definitions.request import AgentRequest

DEFAULT_ENDPOINT_PATH = "/v1/assist"
CONTENT_TYPE_SSE = "text/event-stream"


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


class ServiceContract(CoReasonBaseModel):
    """Generates the OpenAPI specification for the Agent Service."""

    def generate_openapi_path(self) -> Dict[str, Any]:
        """Generates the OpenAPI Path Object for POST /v1/assist.

        Returns:
            A Dictionary representing the OpenAPI Path Object.
        """
        return {
            "post": {
                "summary": "Invoke Agent",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": AgentRequest.model_json_schema()
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Event Stream",
                        "content": {
                            CONTENT_TYPE_SSE: {
                                "schema": {
                                    "type": "string"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Client Error"
                    },
                    "500": {
                        "description": "Server Error"
                    }
                }
            }
        }
