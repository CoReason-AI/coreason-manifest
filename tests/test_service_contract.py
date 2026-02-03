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
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.events import CloudEvent, NodeStarted
from coreason_manifest.definitions.presentation import StreamOpCode, StreamPacket
from coreason_manifest.definitions.request import AgentRequest
from coreason_manifest.definitions.service import (
    CONTENT_TYPE_SSE,
    STREAM_PACKET_EVENT_TYPE,
    HealthCheckResponse,
    ServerSentEvent,
    ServiceContract,
    ServiceRequest,
)
from coreason_manifest.definitions.session import SessionContext, TraceContext, UserContext


def test_wire_format_serialization() -> None:
    """Test that ServerSentEvent correctly serializes a CloudEvent."""
    # Create payload
    payload = NodeStarted(node_id="node-1", timestamp=1234567890.0, status="RUNNING")

    # Create CloudEvent
    event = CloudEvent[NodeStarted](
        type="ai.coreason.node.started", source="urn:node:node-1", data=payload, time=datetime.now(timezone.utc)
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


def test_sse_from_stream_packet() -> None:
    """Test converting a StreamPacket directly to ServerSentEvent."""
    stream_id = uuid4()
    packet = StreamPacket(
        stream_id=stream_id,
        seq=1,
        op=StreamOpCode.DELTA,
        t=datetime.now(timezone.utc),
        p="Hello",
    )

    sse = ServerSentEvent.from_stream_packet(packet)

    assert sse.event == STREAM_PACKET_EVENT_TYPE
    assert sse.id == str(stream_id)
    assert isinstance(sse.data, str)

    # Decode data
    data_dict = json.loads(sse.data)
    assert data_dict["p"] == "Hello"
    assert data_dict["op"] == "DELTA"
    assert data_dict["stream_id"] == str(stream_id)


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


def test_service_request_serialization() -> None:
    """Test ServiceRequest serialization and strict type checking."""
    session_id = uuid4()
    agent_id = uuid4()
    trace_id = uuid4()

    user_context = UserContext(user_id="user-123", email="test@example.com", tier="pro", locale="en-US")

    trace_context = TraceContext(trace_id=trace_id, span_id=uuid4())

    session_context = SessionContext(
        session_id=session_id,
        agent_id=agent_id,
        user=user_context,
        trace=trace_context,
        permissions=["read", "write"],
        created_at=datetime.now(timezone.utc),
    )

    agent_request = AgentRequest(session_id=session_id, payload={"query": "Hello world"})

    service_request = ServiceRequest(request_id=uuid4(), context=session_context, payload=agent_request)

    # Verify dumping
    data = service_request.dump()
    assert data["context"]["user"]["user_id"] == "user-123"
    assert data["payload"]["payload"]["query"] == "Hello world"

    # Test strict type checking (validation error)
    # Pydantic v2 might coerce dict to model if strict is not set, but UserContext/SessionContext
    # are regular models. If we pass a dict that matches schema, it *might* convert it depending on config.
    # However, passing a completely invalid dict should fail.
    # The prompt asked: "Verify strict type checking (e.g., passing a dict instead of SessionContext should
    # fail validation *before* serialization if possible, or ensure the structure is validated)"
    # If Pydantic coerces dict to SessionContext, that is technically valid validation.
    # To test failure, let's pass an invalid object.

    with pytest.raises(ValidationError):
        ServiceRequest(
            request_id=uuid4(),
            context="invalid_context_string",
            payload=agent_request,
        )


def test_health_check_response() -> None:
    """Verify HealthCheckResponse status enums."""
    agent_id = uuid4()

    # Valid
    resp = HealthCheckResponse(status="ok", agent_id=agent_id, version="1.0.0", uptime_seconds=100.5)
    assert resp.status == "ok"

    # Invalid status
    with pytest.raises(ValidationError):
        HealthCheckResponse(
            status="invalid_status",
            agent_id=agent_id,
            version="1.0.0",
            uptime_seconds=100.5,
        )
