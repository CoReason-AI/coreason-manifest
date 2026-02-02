# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import json
from datetime import datetime, timezone

from coreason_manifest.definitions.events import CloudEvent, NodeStarted
from coreason_manifest.definitions.service import (
    CONTENT_TYPE_SSE,
    ServerSentEvent,
    ServiceContract,
)


def test_wire_format_serialization() -> None:
    """Test that ServerSentEvent correctly serializes a CloudEvent."""
    # Create payload
    payload = NodeStarted(
        node_id="node-1",
        timestamp=1234567890.0,
        status="RUNNING"
    )

    # Create CloudEvent
    event = CloudEvent[NodeStarted](
        type="ai.coreason.node.started",
        source="urn:node:node-1",
        data=payload,
        time=datetime.now(timezone.utc)
    )

    # Convert to SSE
    sse = ServerSentEvent.from_cloud_event(event)

    # Assertions
    assert sse.event == "ai.coreason.node.started"
    assert sse.id == event.id
    assert isinstance(sse.data, str)

    # Decode data - it should be the full CloudEvent JSON
    cloud_event_dict = json.loads(sse.data)
    assert cloud_event_dict["specversion"] == "1.0"
    assert cloud_event_dict["type"] == "ai.coreason.node.started"
    assert cloud_event_dict["source"] == "urn:node:node-1"
    # Check payload inside data
    assert cloud_event_dict["data"]["node_id"] == "node-1"
    assert cloud_event_dict["data"]["status"] == "RUNNING"


def test_openapi_generation() -> None:
    """Test that ServiceContract generates the correct OpenAPI path object."""
    contract = ServiceContract()
    openapi = contract.generate_openapi_path()

    assert "post" in openapi
    post_op = openapi["post"]

    assert "summary" in post_op
    assert post_op["summary"] == "Invoke Agent"

    assert "requestBody" in post_op
    req_body = post_op["requestBody"]

    # Verify content type
    assert "content" in req_body
    assert "application/json" in req_body["content"]
    assert "schema" in req_body["content"]["application/json"]

    # Verify Responses
    assert "responses" in post_op
    responses = post_op["responses"]

    # 200 OK
    assert "200" in responses
    success_resp = responses["200"]
    assert success_resp["description"] == "Event Stream"
    assert "content" in success_resp
    assert CONTENT_TYPE_SSE in success_resp["content"]
    assert success_resp["content"][CONTENT_TYPE_SSE]["schema"]["type"] == "string"

    # Errors
    assert "400" in responses
    assert "500" in responses
