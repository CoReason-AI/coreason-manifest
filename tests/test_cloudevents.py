
import json
from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.events import (
    CloudEvent,
    GenAICompletion,
    GenAIRequest,
    GenAISemantics,
    GenAIUsage,
    GraphEvent,
    StandardizedNodeCompleted,
    StandardizedNodeStarted,
    StandardizedNodeStream,
    migrate_graph_event_to_cloud_event,
)


def test_cloudevent_minimal() -> None:
    """Test minimal CloudEvent creation."""
    event: CloudEvent[Dict[str, str]] = CloudEvent(type="ai.coreason.test", source="urn:test", data={"foo": "bar"})
    assert event.specversion == "1.0"
    assert event.type == "ai.coreason.test"
    assert event.source == "urn:test"
    assert event.id is not None
    assert isinstance(event.time, datetime)
    assert event.datacontenttype == "application/json"
    assert event.data == {"foo": "bar"}


def test_cloudevent_extensions() -> None:
    """Test CloudEvent with trace extensions."""
    event: CloudEvent[None] = CloudEvent(
        type="ai.coreason.test",
        source="urn:test",
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        tracestate="rojo=00f067aa0ba902b7",
    )
    assert event.traceparent == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    assert event.tracestate == "rojo=00f067aa0ba902b7"


def test_cloudevent_validation_error() -> None:
    """Test missing required fields."""
    with pytest.raises(ValidationError):
        CloudEvent(source="urn:test")  # type: ignore[call-arg]


def test_otel_semantics() -> None:
    """Test OTel semantic models."""
    semantics = GenAISemantics(
        system="Standard System Prompt",
        usage=GenAIUsage(input_tokens=100, output_tokens=50),
        request=GenAIRequest(model="gpt-4", temperature=0.7),
        completion=GenAICompletion(chunk="Hello", finish_reason="stop"),
    )

    assert semantics.system == "Standard System Prompt"
    assert semantics.usage is not None
    assert semantics.usage.input_tokens == 100
    assert semantics.request is not None
    assert semantics.request.model == "gpt-4"
    assert semantics.completion is not None
    assert semantics.completion.chunk == "Hello"

    # Verify embedding in CloudEvent
    event: CloudEvent[GenAISemantics] = CloudEvent(
        type="ai.coreason.genai.completion", source="urn:agent:123", data=semantics
    )

    assert event.data is not None
    assert event.data.usage is not None
    assert event.data.usage.input_tokens == 100


def test_standardized_payloads() -> None:
    """Test standardized node payloads."""
    # Test StandardizedNodeStarted
    started = StandardizedNodeStarted(
        node_id="node-123",
        gen_ai=GenAISemantics(usage=GenAIUsage(input_tokens=50), request=GenAIRequest(model="gpt-3.5-turbo")),
    )
    event_start: CloudEvent[StandardizedNodeStarted] = CloudEvent(
        type="ai.coreason.node.started", source="urn:node:node-123", data=started
    )
    assert event_start.data is not None
    assert event_start.data.node_id == "node-123"
    assert event_start.data.gen_ai is not None
    assert event_start.data.gen_ai.usage is not None
    assert event_start.data.gen_ai.usage.input_tokens == 50
    assert event_start.data.gen_ai.request is not None
    assert event_start.data.gen_ai.request.model == "gpt-3.5-turbo"

    # Test StandardizedNodeStream
    stream = StandardizedNodeStream(
        node_id="node-123", gen_ai=GenAISemantics(completion=GenAICompletion(chunk="world"))
    )
    event_stream: CloudEvent[StandardizedNodeStream] = CloudEvent(
        type="ai.coreason.node.stream", source="urn:node:node-123", data=stream
    )
    assert event_stream.data is not None
    assert event_stream.data.gen_ai is not None
    assert event_stream.data.gen_ai.completion is not None
    assert event_stream.data.gen_ai.completion.chunk == "world"

    # Test StandardizedNodeCompleted
    completed = StandardizedNodeCompleted(
        node_id="node-123",
        output_summary="Hello world",
        gen_ai=GenAISemantics(usage=GenAIUsage(input_tokens=50, output_tokens=10)),
    )
    event_complete: CloudEvent[StandardizedNodeCompleted] = CloudEvent(
        type="ai.coreason.node.completed", source="urn:node:node-123", data=completed
    )
    assert event_complete.data is not None
    assert event_complete.data.output_summary == "Hello world"
    assert event_complete.data.gen_ai is not None
    assert event_complete.data.gen_ai.usage is not None
    assert event_complete.data.gen_ai.usage.output_tokens == 10


def test_migration_node_start() -> None:
    """Test migration of NODE_START event."""
    legacy_event = GraphEvent(
        event_type="NODE_START",
        run_id="run-1",
        node_id="node-1",
        timestamp=1700000000.0,
        payload={"status": "RUNNING", "input_tokens": 42, "model": "gpt-4", "system": "You are a helpful assistant"},
        visual_metadata={"animation": "pulse", "color": "blue"},
    )

    cloud_event = migrate_graph_event_to_cloud_event(legacy_event)

    assert cloud_event.specversion == "1.0"
    assert cloud_event.type == "ai.coreason.node.started"
    assert cloud_event.source == "urn:node:node-1"
    # assert cloud_event.time.timestamp() == 1700000000.0
    assert cloud_event.time == datetime.fromtimestamp(1700000000.0, timezone.utc)

    # Check Standardized Payload
    assert isinstance(cloud_event.data, StandardizedNodeStarted)
    assert cloud_event.data.node_id == "node-1"
    assert cloud_event.data.status == "RUNNING"
    assert cloud_event.data.gen_ai is not None
    assert cloud_event.data.gen_ai.usage is not None
    assert cloud_event.data.gen_ai.usage.input_tokens == 42
    assert cloud_event.data.gen_ai.request is not None
    assert cloud_event.data.gen_ai.request.model == "gpt-4"
    assert cloud_event.data.gen_ai.system == "You are a helpful assistant"

    # Check Extensions
    dump = cloud_event.model_dump(by_alias=True)
    assert dump["com_coreason_ui_cue"] == "pulse"
    assert dump["com_coreason_ui_metadata"] == {"animation": "pulse", "color": "blue"}


def test_migration_node_stream() -> None:
    """Test migration of NODE_STREAM event."""
    legacy_event = GraphEvent(
        event_type="NODE_STREAM",
        run_id="run-1",
        node_id="node-1",
        timestamp=1700000000.0,
        payload={"chunk": "hello ", "visual_cue": "typing"},
        visual_metadata={"animation": "typing"},
    )

    cloud_event = migrate_graph_event_to_cloud_event(legacy_event)

    assert cloud_event.type == "ai.coreason.node.stream"
    assert isinstance(cloud_event.data, StandardizedNodeStream)
    assert cloud_event.data.gen_ai is not None
    assert cloud_event.data.gen_ai.completion is not None
    assert cloud_event.data.gen_ai.completion.chunk == "hello "

    dump = cloud_event.model_dump(by_alias=True)
    assert dump["com_coreason_ui_cue"] == "typing"


def test_migration_node_completed() -> None:
    """Test migration of NODE_DONE event."""
    legacy_event = GraphEvent(
        event_type="NODE_DONE",
        run_id="run-1",
        node_id="node-1",
        timestamp=1700000000.0,
        payload={"output_summary": "Done.", "status": "SUCCESS"},
        visual_metadata={"animation": "glow"},
    )

    cloud_event = migrate_graph_event_to_cloud_event(legacy_event)

    assert cloud_event.type == "ai.coreason.node.completed"
    assert isinstance(cloud_event.data, StandardizedNodeCompleted)
    assert cloud_event.data.output_summary == "Done."

    dump = cloud_event.model_dump(by_alias=True)
    assert dump["com_coreason_ui_cue"] == "glow"


def test_migration_generic_fallback() -> None:
    """Test migration of generic events like NODE_INIT."""
    legacy_event = GraphEvent(
        event_type="NODE_INIT",
        run_id="run-1",
        node_id="node-1",
        timestamp=1700000000.0,
        payload={"type": "DEFAULT", "visual_cue": "IDLE"},
        visual_metadata={"animation": "idle"},
    )

    cloud_event = migrate_graph_event_to_cloud_event(legacy_event)

    assert cloud_event.type == "ai.coreason.legacy.node_init"
    assert cloud_event.data == {"type": "DEFAULT", "visual_cue": "IDLE"}

    dump = cloud_event.model_dump(by_alias=True)
    assert dump["com_coreason_ui_cue"] == "idle"


def test_migration_partial_data() -> None:
    """Test migration with missing optional fields."""
    # Missing input_tokens in NODE_START
    legacy_event = GraphEvent(
        event_type="NODE_START",
        run_id="run-1",
        node_id="node-1",
        timestamp=1700000000.0,
        payload={
            "status": "RUNNING"
            # input_tokens missing
        },
        visual_metadata={},  # Empty visual metadata
    )

    cloud_event = migrate_graph_event_to_cloud_event(legacy_event)
    # Check that data is StandardizedNodeStarted
    assert isinstance(cloud_event.data, StandardizedNodeStarted)
    assert cloud_event.data.gen_ai is None

    dump = cloud_event.model_dump(by_alias=True)
    assert "com_coreason_ui_cue" not in dump
    assert "com_coreason_ui_metadata" not in dump


def test_migration_empty_string_extension() -> None:
    """Test that empty string extensions are filtered out."""
    legacy_event = GraphEvent(
        event_type="NODE_INIT",
        run_id="run-1",
        node_id="node-1",
        timestamp=1700000000.0,
        payload={"visual_cue": ""},
        visual_metadata={"animation": ""},
    )
    cloud_event = migrate_graph_event_to_cloud_event(legacy_event)
    dump = cloud_event.model_dump(by_alias=True)
    assert "com_coreason_ui_cue" not in dump
    assert "com_coreason_ui_metadata" not in dump


def test_cloudevent_serialization() -> None:
    """Test JSON serialization and deserialization."""
    event: CloudEvent[Dict[str, str]] = CloudEvent(
        type="ai.coreason.test", source="urn:test", data={"foo": "bar"}, my_custom_extension="value"
    )

    # Serialize
    json_str = event.model_dump_json(by_alias=True)
    data = json.loads(json_str)

    assert data["type"] == "ai.coreason.test"
    assert data["data"] == {"foo": "bar"}
    assert data["my_custom_extension"] == "value"

    # Deserialize
    event_back: CloudEvent[Any] = CloudEvent(**data)
    assert event_back.type == "ai.coreason.test"
    # Extensions are in model_extra if allowed
    dump_back = event_back.model_dump(by_alias=True)
    assert dump_back["my_custom_extension"] == "value"


def test_timestamp_handling() -> None:
    """Test that timestamps are correctly handled as UTC."""
    ts = 1700000000.0
    dt_utc = datetime.fromtimestamp(ts, timezone.utc)

    legacy_event = GraphEvent(
        event_type="NODE_INIT", run_id="run-1", node_id="node-1", timestamp=ts, payload={}, visual_metadata={}
    )

    cloud_event = migrate_graph_event_to_cloud_event(legacy_event)
    assert cloud_event.time == dt_utc
    assert cloud_event.time.tzinfo == timezone.utc


def test_custom_extensions_in_constructor() -> None:
    """Test passing custom extensions to CloudEvent constructor."""
    event: CloudEvent[None] = CloudEvent(type="test", source="test", com_coreason_custom="custom_value")
    dump = event.model_dump(by_alias=True)
    assert dump["com_coreason_custom"] == "custom_value"

def test_migration_node_skipped() -> None:
    """Test migration of NODE_SKIPPED event."""
    legacy_event = GraphEvent(
        event_type="NODE_SKIPPED",
        run_id="run-1",
        node_id="node-1",
        timestamp=1700000000.0,
        payload={"status": "SKIPPED", "visual_cue": "GREY_OUT"},
        visual_metadata={"animation": "skipped"},
    )
    cloud_event = migrate_graph_event_to_cloud_event(legacy_event)

    assert cloud_event.type == "ai.coreason.legacy.node_skipped"
    assert isinstance(cloud_event.data, dict)
    assert cloud_event.data["status"] == "SKIPPED"

    dump = cloud_event.model_dump(by_alias=True)
    assert dump["com_coreason_ui_cue"] == "skipped"

def test_migration_error_event() -> None:
    """Test migration of ERROR event."""
    legacy_event = GraphEvent(
        event_type="ERROR",
        run_id="run-1",
        node_id="node-1",
        timestamp=1700000000.0,
        payload={
            "error_message": "Oops",
            "stack_trace": "...",
            "visual_cue": "RED_FLASH"
        },
        visual_metadata={"animation": "error"},
    )
    cloud_event = migrate_graph_event_to_cloud_event(legacy_event)

    assert cloud_event.type == "ai.coreason.legacy.error"
    assert isinstance(cloud_event.data, dict)
    assert cloud_event.data["error_message"] == "Oops"

    dump = cloud_event.model_dump(by_alias=True)
    assert dump["com_coreason_ui_cue"] == "error"

def test_migration_invalid_types_handled() -> None:
    """Test that invalid types in payload (e.g. input_tokens as string) cause validation error."""
    # Since we want to know if it fails or works.
    legacy_event = GraphEvent(
        event_type="NODE_START",
        run_id="run-1",
        node_id="node-1",
        timestamp=1700000000.0,
        payload={
            "status": "RUNNING",
            "input_tokens": "not_an_int" # This is the edge case
        },
        visual_metadata={},
    )

    # It should raise a validation error because we try to coerce into GenAIUsage
    with pytest.raises(ValidationError):
        migrate_graph_event_to_cloud_event(legacy_event)
