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

from coreason_manifest.definitions.observability import CloudEvent, ReasoningTrace


def test_cloud_event_serialization() -> None:
    now = datetime.now(timezone.utc)
    event = CloudEvent(
        id="evt-1",
        source="urn:node:step-1",
        type="ai.coreason.node.started",
        time=now,
        data={"message": "hello"},
    )

    dumped = event.dump()
    assert dumped["specversion"] == "1.0"
    assert dumped["id"] == "evt-1"
    assert dumped["source"] == "urn:node:step-1"
    assert dumped["type"] == "ai.coreason.node.started"
    # CoReasonBaseModel serializes datetime with Z suffix
    assert dumped["time"] == now.isoformat().replace("+00:00", "Z")
    assert dumped["datacontenttype"] == "application/json"
    assert dumped["data"] == {"message": "hello"}


def test_cloud_event_tracing_extensions() -> None:
    now = datetime.now(timezone.utc)
    event = CloudEvent(
        id="evt-2",
        source="urn:node:step-2",
        type="ai.coreason.node.completed",
        time=now,
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="rojo=00f067aa0ba902b7-01",
    )
    dumped = event.dump()
    assert dumped["traceparent"] == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    assert dumped["tracestate"] == "rojo=00f067aa0ba902b7-01"


def test_reasoning_trace_serialization() -> None:
    req_id = uuid4()
    root_id = uuid4()
    now = datetime.now(timezone.utc)

    trace = ReasoningTrace(
        request_id=req_id,
        root_request_id=root_id,
        node_id="step-analysis",
        status="success",
        inputs={"query": "why?"},
        outputs={"answer": "because"},
        latency_ms=123.4,
        timestamp=now,
    )

    dumped = trace.dump()
    assert dumped["request_id"] == str(req_id)
    assert dumped["root_request_id"] == str(root_id)
    assert dumped["node_id"] == "step-analysis"
    assert dumped["status"] == "success"
    assert dumped["inputs"] == {"query": "why?"}
    assert dumped["outputs"] == {"answer": "because"}
    assert dumped["latency_ms"] == 123.4
    assert dumped["timestamp"] == now.isoformat().replace("+00:00", "Z")


def test_immutability() -> None:
    now = datetime.now(timezone.utc)
    event = CloudEvent(
        id="evt-3",
        source="urn:node:step-3",
        type="test",
        time=now,
    )

    with pytest.raises(ValidationError) as excinfo:
        setattr(event, "id", "new-id")  # noqa: B010

    assert "Instance is frozen" in str(excinfo.value)

    trace = ReasoningTrace(
        request_id=uuid4(),
        root_request_id=uuid4(),
        node_id="test",
        status="success",
        latency_ms=1.0,
        timestamp=now,
    )

    with pytest.raises(ValidationError) as excinfo:
        setattr(trace, "status", "failed")  # noqa: B010

    assert "Instance is frozen" in str(excinfo.value)
