# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.spec.common.graph_events import (
    GraphEvent,
    GraphEventNodeDone,
    GraphEventNodeStart,
    GraphEventNodeStream,
)
from coreason_manifest.spec.common.observability import EventContentType
from coreason_manifest.utils.migration import migrate_graph_event_to_cloud_event


def test_polymorphic_serialization() -> None:
    """
    1. Polymorphic Serialization:
    * Create a list of mixed events (Start, Stream, Done).
    * Serialize to a list of dicts.
    * Use TypeAdapter(list[GraphEvent]).validate_python(data) to parse them back.
    * Assert: The types are correctly restored.
    """
    now = datetime.now().timestamp()

    events: list[GraphEvent] = [
        GraphEventNodeStart(
            run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=now, payload={"input": "test"}
        ),
        GraphEventNodeStream(
            run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=now + 1, chunk="Hello", stream_id="default"
        ),
        GraphEventNodeDone(
            run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=now + 2, output={"result": "Hello World"}
        ),
    ]

    # Serialize
    adapter = TypeAdapter(list[GraphEvent])
    serialized_data = adapter.dump_python(events)

    # Validate/Deserialize
    restored_events = adapter.validate_python(serialized_data)

    assert len(restored_events) == 3
    assert isinstance(restored_events[0], GraphEventNodeStart)
    assert restored_events[0].payload == {"input": "test"}

    assert isinstance(restored_events[1], GraphEventNodeStream)
    assert restored_events[1].chunk == "Hello"

    assert isinstance(restored_events[2], GraphEventNodeDone)
    assert restored_events[2].output == {"result": "Hello World"}


def test_migration_logic() -> None:
    """
    2. Migration Logic:
    * Create a GraphEventNodeStream.
    * Call migrate_graph_event_to_cloud_event.
    * Assert: cloudevent.type == "ai.coreason.node.stream".
    * Assert: cloudevent.datacontenttype == "application/vnd.coreason.stream+json".
    """
    now = datetime.now().timestamp()
    event = GraphEventNodeStream(
        run_id="run-1", trace_id="trace-1", node_id="step-x", timestamp=now, chunk=" partial", visual_cue="typing"
    )

    cloud_event = migrate_graph_event_to_cloud_event(event)

    # Check CloudEvent fields
    assert cloud_event.type == "ai.coreason.node.stream"
    assert cloud_event.source == "urn:node:step-x"
    assert cloud_event.datacontenttype == EventContentType.STREAM

    # Check data content
    assert cloud_event.data == {"chunk": " partial"}

    # Check Extensions
    # Note: CloudEvent model puts extensions as fields if defined in model, or extra fields?
    # ExtendedCloudEvent defines com_coreason_ui_cue explicitly.
    # We access it via getattr or direct attribute if typed.
    # Since migrate returns CloudEvent (base) but it's actually ExtendedCloudEvent.
    assert getattr(cloud_event, "com_coreason_ui_cue", None) == "typing"
    assert cloud_event.traceparent == "trace-1"


def test_immutability() -> None:
    """
    3. Immutability:
    * Attempt to modify event.chunk after instantiation.
    * Assert: ValidationError.
    """
    now = datetime.now().timestamp()
    event = GraphEventNodeStream(run_id="run-1", trace_id="trace-1", node_id="node-1", timestamp=now, chunk="Hello")

    with pytest.raises(ValidationError):
        event.chunk = "Modified"  # type: ignore
