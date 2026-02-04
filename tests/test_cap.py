# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.identity import Identity
from coreason_manifest.spec.cap import (
    AgentRequest,
    HealthCheckResponse,
    HealthCheckStatus,
    ServiceRequest,
    ServiceResponse,
    SessionContext,
    StreamPacket,
)

# --- Unit Tests ---


def test_health_check_response_serialization() -> None:
    agent_id = uuid4()
    response = HealthCheckResponse(
        status=HealthCheckStatus.OK, agent_id=agent_id, version="1.0.0", uptime_seconds=123.45
    )
    dumped = response.dump()
    assert dumped["status"] == "ok"
    assert dumped["agent_id"] == str(agent_id)
    assert dumped["version"] == "1.0.0"
    assert dumped["uptime_seconds"] == 123.45


def test_stream_packet_creation() -> None:
    # Test with string data
    packet1 = StreamPacket(op="delta", p="hello")
    assert packet1.op == "delta"
    assert packet1.p == "hello"

    # Test with dict data
    packet2 = StreamPacket(op="event", p={"tokens": 5, "model": "gpt-4"})
    assert isinstance(packet2.p, dict)
    assert packet2.p["tokens"] == 5


def test_service_response_serialization() -> None:
    req_id = uuid4()
    now = datetime.now(timezone.utc)
    response = ServiceResponse(
        request_id=req_id, created_at=now, output={"result": "success"}, metrics={"latency": 100}
    )
    dumped = response.dump()
    assert dumped["request_id"] == str(req_id)
    # Pydantic v2 JSON serialization uses 'Z' for UTC, while python uses +00:00
    assert dumped["created_at"] == now.isoformat().replace("+00:00", "Z")
    assert dumped["output"] == {"result": "success"}


def test_service_request_instantiation() -> None:
    req_id = uuid4()
    user = Identity.anonymous()
    context = SessionContext(session_id="s123", user=user)
    payload = AgentRequest(query="test")
    req = ServiceRequest(request_id=req_id, context=context, payload=payload)
    assert req.request_id == req_id
    assert req.context.session_id == "s123"
    assert req.payload.query == "test"


# --- Edge Case Tests ---


def test_invalid_uuid_validation() -> None:
    with pytest.raises(ValidationError) as excinfo:
        ServiceRequest.model_validate(
            {
                "request_id": "not-a-uuid",
                "context": {"session_id": "s1", "user": {"id": "u1", "name": "User"}},
                "payload": {"query": "q"},
            }
        )
    assert "Input should be a valid UUID" in str(excinfo.value)


def test_invalid_enum_status() -> None:
    with pytest.raises(ValidationError) as excinfo:
        HealthCheckResponse.model_validate(
            {
                "status": "invalid_status",
                "agent_id": str(uuid4()),
                "version": "1.0.0",
                "uptime_seconds": 10.0,
            }
        )
    # Pydantic v2 error message for enum
    assert "Input should be 'ok', 'degraded' or 'maintenance'" in str(excinfo.value)


def test_missing_required_fields() -> None:
    with pytest.raises(ValidationError) as excinfo:
        ServiceRequest(
            request_id=uuid4(),
            # Missing context and payload
        )  # type: ignore[call-arg]
    assert "Field required" in str(excinfo.value)
    assert "context" in str(excinfo.value)
    assert "payload" in str(excinfo.value)


def test_stream_packet_invalid_data_type() -> None:
    with pytest.raises(ValidationError):
        StreamPacket.model_validate(
            {
                "op": "error",
                "p": [1, 2, 3],
            }
        )


# --- Complex Case Tests ---


def test_service_request_deep_nesting() -> None:
    # Use meta for nested data
    meta = {"level1": {"level2": {"level3": {"data": "deep", "list": [1, 2, {"nested": "item"}]}}}}
    payload = AgentRequest(query="test", meta=meta)
    context = SessionContext(session_id="s1", user=Identity.anonymous())
    req = ServiceRequest(request_id=uuid4(), context=context, payload=payload)

    dumped = req.dump()
    assert dumped["payload"]["meta"]["level1"]["level2"]["level3"]["data"] == "deep"
    assert dumped["payload"]["meta"]["level1"]["level2"]["level3"]["list"][2]["nested"] == "item"


def test_round_trip_json_serialization() -> None:
    context = SessionContext(session_id="s1", user=Identity.anonymous())
    payload = AgentRequest(query="run", meta={"params": {"x": 10}})
    original_req = ServiceRequest(
        request_id=uuid4(), context=context, payload=payload
    )

    # Dump to JSON string
    json_str = original_req.to_json()

    # Load back from JSON string
    loaded_req = ServiceRequest.model_validate_json(json_str)

    assert loaded_req.request_id == original_req.request_id
    assert loaded_req.context == original_req.context
    assert loaded_req.payload == original_req.payload

    # Ensure deep equality
    assert loaded_req == original_req


def test_immutability_frozen() -> None:
    context = SessionContext(session_id="s1", user=Identity.anonymous())
    payload = AgentRequest(query="test")
    req = ServiceRequest(request_id=uuid4(), context=context, payload=payload)

    with pytest.raises(ValidationError) as excinfo:
        req.context = context  # type: ignore[misc]

    # Error message for frozen instance assignment
    assert "Instance is frozen" in str(excinfo.value)


def test_type_preservation_in_dict() -> None:
    """Ensure that native types in Dict[str, Any] are preserved."""
    # Ensure they are not aggressively coerced to strings if not needed.
    meta = {"int_val": 123, "float_val": 45.67, "bool_val": True, "none_val": None, "list_val": [1, "two"]}
    context = SessionContext(session_id="s1", user=Identity.anonymous())
    payload = AgentRequest(query="test", meta=meta)
    req = ServiceRequest(request_id=uuid4(), context=context, payload=payload)

    # Dump using the CoReasonBaseModel.dump() which sets mode='json'
    dumped = req.dump()

    # In mode='json', Pydantic might serialize types to their JSON equivalents.
    # int -> int, float -> float, bool -> bool, None -> null
    assert dumped["payload"]["meta"]["int_val"] == 123
    assert dumped["payload"]["meta"]["float_val"] == 45.67
    assert dumped["payload"]["meta"]["bool_val"] is True
    assert dumped["payload"]["meta"]["none_val"] is None
    assert dumped["payload"]["meta"]["list_val"] == [1, "two"]


def test_extra_fields_behavior() -> None:
    """Verify behavior when extra fields are passed (should be ignored or allowed, but not crash)."""
    # By default, Pydantic ignores extra fields unless configured otherwise.
    # We want to confirm it doesn't raise ValidationError.

    data = {
        "request_id": str(uuid4()),
        "context": {"session_id": "s1", "user": {"id": "u1", "name": "User"}},
        "payload": {"query": "q"},
        "extra_field": "should_be_ignored"
    }

    # Should not raise
    req = ServiceRequest.model_validate(data)

    # Check if extra field is present or not.
    # Since config is not explicit about extra, default is usually 'ignore'.
    # If it's 'ignore', hasattr is False.
    assert not hasattr(req, "extra_field")
