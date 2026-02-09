# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.common.observability import CloudEvent, EventContentType, ReasoningTrace

# --- Unit Tests ---


def test_cloud_event_serialization() -> None:
    now = datetime.now(UTC)
    event = CloudEvent(
        id="evt-1",
        source="urn:node:step-1",
        type="ai.coreason.node.started",
        time=now,
        data={"message": "hello"},
    )

    dumped = event.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["specversion"] == "1.0"
    assert dumped["id"] == "evt-1"
    assert dumped["source"] == "urn:node:step-1"
    assert dumped["type"] == "ai.coreason.node.started"
    # ManifestBaseModel serializes datetime with Z suffix
    assert dumped["time"] == now.isoformat().replace("+00:00", "Z")
    assert dumped["datacontenttype"] == "application/json"
    assert dumped["data"] == {"message": "hello"}


def test_cloud_event_tracing_extensions() -> None:
    now = datetime.now(UTC)
    event = CloudEvent(
        id="evt-2",
        source="urn:node:step-2",
        type="ai.coreason.node.completed",
        time=now,
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="rojo=00f067aa0ba902b7-01",
    )
    dumped = event.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["traceparent"] == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    assert dumped["tracestate"] == "rojo=00f067aa0ba902b7-01"


def test_reasoning_trace_serialization() -> None:
    req_id = uuid4()
    root_id = uuid4()
    now = datetime.now(UTC)

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

    dumped = trace.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["request_id"] == str(req_id)
    assert dumped["root_request_id"] == str(root_id)
    assert dumped["node_id"] == "step-analysis"
    assert dumped["status"] == "success"
    assert dumped["inputs"] == {"query": "why?"}
    assert dumped["outputs"] == {"answer": "because"}
    assert dumped["latency_ms"] == 123.4
    assert dumped["timestamp"] == now.isoformat().replace("+00:00", "Z")


def test_immutability() -> None:
    now = datetime.now(UTC)
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


def test_event_content_type_enum() -> None:
    now = datetime.now(UTC)
    # 1. Instantiation with Enum
    event = CloudEvent(
        id="evt-enum", source="urn:enum", type="test.enum", time=now, datacontenttype=EventContentType.ERROR
    )

    # 2. Serialization Check
    dumped = event.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["datacontenttype"] == "application/vnd.coreason.error+json"

    # 3. String Compatibility
    event_str = CloudEvent(id="evt-str", source="urn:str", type="test.str", time=now, datacontenttype="text/plain")
    dumped_str = event_str.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped_str["datacontenttype"] == "text/plain"


# --- Edge Case Tests ---


def test_cloud_event_minimal() -> None:
    """Test CloudEvent with only required fields."""
    now = datetime.now(UTC)
    event = CloudEvent(id="evt-min", source="urn:min", type="test.min", time=now)
    dumped = event.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["id"] == "evt-min"
    # data is optional and None by default, so exclude_none=True removes it
    assert "data" not in dumped
    # datacontenttype has a default
    assert dumped["datacontenttype"] == "application/json"


def test_cloud_event_data_variations() -> None:
    """Test CloudEvent with different data shapes (None, Empty Dict)."""
    base_args = {"id": "evt-data", "source": "urn:data", "type": "test.data", "time": datetime.now(UTC)}

    # None
    evt_none = CloudEvent(**base_args, data=None)
    assert evt_none.data is None

    # Empty Dict
    evt_empty = CloudEvent(**base_args, data={})
    assert evt_empty.data == {}


def test_reasoning_trace_missing_optional() -> None:
    """Test ReasoningTrace serialization when optional fields are missing (None)."""
    req_id = uuid4()
    root_id = uuid4()
    now = datetime.now(UTC)

    trace = ReasoningTrace(
        request_id=req_id,
        root_request_id=root_id,
        # parent_request_id omitted (None)
        node_id="step-1",
        status="success",
        # inputs/outputs omitted (None)
        latency_ms=10.0,
        timestamp=now,
    )

    dumped = trace.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["request_id"] == str(req_id)
    assert "parent_request_id" not in dumped  # exclude_none=True
    assert "inputs" not in dumped
    assert "outputs" not in dumped


def test_validation_failure_missing_fields() -> None:
    """Test that missing required fields raises ValidationError."""
    with pytest.raises(ValidationError):
        # Missing 'id'
        CloudEvent(source="urn:test", type="test", time=datetime.now(UTC))  # type: ignore

    with pytest.raises(ValidationError):
        # Missing 'latency_ms'
        ReasoningTrace(
            request_id=uuid4(),
            root_request_id=uuid4(),
            node_id="test",
            status="ok",
            timestamp=datetime.now(UTC),
        )  # type: ignore


# --- Complex Case Tests ---


def test_complex_nested_payloads() -> None:
    """Test serialization of deeply nested complex data structures."""
    complex_data = {
        "user": {
            "profile": {
                "name": "Test User",
                "roles": ["admin", "editor"],
                "settings": {"theme": "dark", "notifications": True},
            },
            "history": [{"event": "login", "ts": 123456}, {"event": "click", "coords": {"x": 10, "y": 20}}],
        },
        "meta": "top-level",
    }

    event = CloudEvent(
        id="evt-complex", source="urn:complex", type="test.complex", time=datetime.now(UTC), data=complex_data
    )

    dumped = event.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["data"]["user"]["profile"]["roles"][1] == "editor"
    assert dumped["data"]["user"]["history"][1]["coords"]["y"] == 20


def test_trace_chain_simulation() -> None:
    """
    Simulate a chain of traces (Root -> Child A -> Child B) and verify
    lineage via request_ids.
    """
    root_id = uuid4()
    start_time = datetime.now(UTC)

    # 1. Root Trace
    trace_root = ReasoningTrace(
        request_id=root_id,
        root_request_id=root_id,
        parent_request_id=None,
        node_id="orchestrator",
        status="running",
        latency_ms=5.0,
        timestamp=start_time,
    )

    # 2. Child Trace (Analysis)
    child_a_id = uuid4()
    trace_child_a = ReasoningTrace(
        request_id=child_a_id,
        root_request_id=root_id,
        parent_request_id=root_id,
        node_id="analyzer",
        status="success",
        inputs={"doc": "text"},
        latency_ms=50.0,
        timestamp=datetime.now(UTC),
    )

    # 3. Child Trace (Generation) - child of Analysis (hypothetically, or usually child of root)
    # Let's say it's sequential: Root -> Analyzer; Root -> Generator.
    # Or deeper: Root -> Analyzer -> SubTask.
    # Let's do deeper: Analyzer calls SubTask.

    subtask_id = uuid4()
    trace_subtask = ReasoningTrace(
        request_id=subtask_id,
        root_request_id=root_id,
        parent_request_id=child_a_id,
        node_id="analyzer-sub",
        status="success",
        outputs={"score": 0.9},
        latency_ms=10.0,
        timestamp=datetime.now(UTC),
    )

    # Verification

    # Check Root Lineage
    assert trace_root.root_request_id == root_id
    assert trace_root.parent_request_id is None

    # Check Child A Lineage
    assert trace_child_a.root_request_id == root_id
    assert trace_child_a.parent_request_id == trace_root.request_id

    # Check Subtask Lineage
    assert trace_subtask.root_request_id == root_id
    assert trace_subtask.parent_request_id == trace_child_a.request_id

    # Check Dump Consistency
    dump_sub = trace_subtask.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dump_sub["root_request_id"] == str(root_id)
    assert dump_sub["parent_request_id"] == str(child_a_id)


# --- Extended Edge & Complex Cases for EventContentType ---


def test_enum_as_string_input() -> None:
    """
    Test passing a raw string that exactly matches an Enum value.
    Ideally, Pydantic should handle this gracefully, or at least serialize correctly.
    """
    now = datetime.now(UTC)
    # "application/vnd.coreason.error+json" matches EventContentType.ERROR
    event = CloudEvent(
        id="evt-str-match",
        source="urn:test",
        type="test.match",
        time=now,
        datacontenttype="application/vnd.coreason.error+json",
    )
    dumped = event.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["datacontenttype"] == "application/vnd.coreason.error+json"

    # Since we are using Union[EventContentType, str], the value might be stored as string or coerced.
    # Because 'EventContentType' is first in the Union, Pydantic might try to coerce if configured,
    # but strictly speaking, if a string is passed, it matches 'str' too.
    # However, 'EventContentType' inherits from 'str', so it is comparable.
    assert event.datacontenttype == EventContentType.ERROR


def test_empty_string_content_type() -> None:
    """Test empty string as content type."""
    now = datetime.now(UTC)
    event = CloudEvent(id="evt-empty", source="urn:test", type="test.empty", time=now, datacontenttype="")
    dumped = event.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["datacontenttype"] == ""


def test_mixed_list_of_events() -> None:
    """Test a list of events with mixed content types (Enum and Str)."""
    now = datetime.now(UTC)
    events = [
        CloudEvent(id="1", source="u", type="t", time=now, datacontenttype=EventContentType.JSON),
        CloudEvent(id="2", source="u", type="t", time=now, datacontenttype="text/plain"),
        CloudEvent(id="3", source="u", type="t", time=now, datacontenttype=EventContentType.STREAM),
    ]

    dumped = [e.model_dump(mode="json", by_alias=True, exclude_none=True) for e in events]
    assert dumped[0]["datacontenttype"] == "application/json"
    assert dumped[1]["datacontenttype"] == "text/plain"
    assert dumped[2]["datacontenttype"] == "application/vnd.coreason.stream+json"


def test_nested_cloud_event_in_data() -> None:
    """
    Test embedding a dumped CloudEvent inside the 'data' of another CloudEvent.
    This simulates an event carrying another event as payload.
    """
    now = datetime.now(UTC)
    inner_event = CloudEvent(
        id="inner-1",
        source="urn:inner",
        type="inner.type",
        time=now,
        datacontenttype=EventContentType.ARTIFACT,
        data={"file": "report.pdf"},
    )

    outer_event = CloudEvent(
        id="outer-1",
        source="urn:outer",
        type="outer.wrapper",
        time=now,
        datacontenttype=EventContentType.JSON,
        data={"wrapped_event": inner_event.model_dump(mode="json", by_alias=True, exclude_none=True)},
    )

    dumped = outer_event.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["datacontenttype"] == "application/json"
    assert dumped["data"]["wrapped_event"]["datacontenttype"] == "application/vnd.coreason.artifact+json"
