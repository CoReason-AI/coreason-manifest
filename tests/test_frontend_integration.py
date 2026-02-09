# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from pydantic import TypeAdapter

from coreason_manifest import (
    GraphEvent,
    GraphEventError,
    GraphEventNodeStart,
    GraphEventNodeStream,
)


def test_graph_event_polymorphism() -> None:
    data = [
        {
            "event_type": "NODE_START",
            "run_id": "r1",
            "trace_id": "t1",
            "node_id": "n1",
            "timestamp": 123.456,
            "payload": {"k": "v"},
        },
        {
            "event_type": "NODE_STREAM",
            "run_id": "r1",
            "trace_id": "t1",
            "node_id": "n1",
            "timestamp": 123.457,
            "chunk": "hello",
        },
        {
            "event_type": "ERROR",
            "run_id": "r1",
            "trace_id": "t1",
            "node_id": "n1",
            "timestamp": 123.458,
            "error_message": "oops",
        },
    ]

    adapter = TypeAdapter(list[GraphEvent])
    events = adapter.validate_python(data)

    assert len(events) == 3
    assert isinstance(events[0], GraphEventNodeStart)
    assert events[0].payload == {"k": "v"}
    assert isinstance(events[1], GraphEventNodeStream)
    assert events[1].chunk == "hello"
    assert isinstance(events[2], GraphEventError)
    assert events[2].error_message == "oops"


def test_graph_event_serialization() -> None:
    event = GraphEventNodeStream(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, chunk="hi")
    dumped = event.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dumped["event_type"] == "NODE_STREAM"
    assert dumped["chunk"] == "hi"
