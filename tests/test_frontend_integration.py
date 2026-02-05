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
    EventContentType,
    GraphEvent,
    GraphEventError,
    GraphEventNodeStart,
    GraphEventNodeStream,
    migrate_graph_event_to_cloud_event,
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
    dumped = event.dump()
    assert dumped["event_type"] == "NODE_STREAM"
    assert dumped["chunk"] == "hi"


def test_migration_logic() -> None:
    event = GraphEventNodeStream(
        run_id="run-1",
        trace_id="trace-1",
        node_id="step-1",
        timestamp=1700000000.0,
        chunk="Hello World",
        visual_cue="typing",
    )

    cloud_event = migrate_graph_event_to_cloud_event(event)

    assert cloud_event.type == "ai.coreason.node.stream"
    assert cloud_event.source == "urn:node:step-1"
    assert cloud_event.datacontenttype == EventContentType.STREAM
    assert cloud_event.data == {"chunk": "Hello World"}
    assert cloud_event.traceparent == "trace-1"

    # Check extension
    # We used ExtendedCloudEvent internally but it's returned as CloudEvent type hint.
    # We check if dump() contains the extension
    dumped_ce = cloud_event.dump()
    assert dumped_ce["com_coreason_ui_cue"] == "typing"

    # Also verify time conversion
    # 1700000000.0 is roughly 2023-11-14
    assert "2023" in str(cloud_event.time) or "2023" in cloud_event.time.isoformat()


def test_migration_error_event() -> None:
    event = GraphEventError(
        run_id="r2",
        trace_id="t2",
        node_id="step-2",
        timestamp=1700000000.0,
        error_message="Something bad",
        stack_trace="Traceback...",
    )

    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.type == "ai.coreason.error"
    assert ce.datacontenttype == EventContentType.ERROR
    assert ce.data is not None
    assert ce.data["error_message"] == "Something bad"


def test_migration_all_types() -> None:
    from coreason_manifest import (
        EventContentType,
        GraphEventArtifactGenerated,
        GraphEventCouncilVote,
        GraphEventNodeDone,
        GraphEventNodeRestored,
        GraphEventNodeStart,
    )

    # NODE_START
    e1 = GraphEventNodeStart(run_id="r", trace_id="t", node_id="n", timestamp=1.0, payload={"p": 1})
    c1 = migrate_graph_event_to_cloud_event(e1)
    assert c1.type == "ai.coreason.node.start"
    assert c1.data == {"p": 1}

    # NODE_DONE
    e2 = GraphEventNodeDone(run_id="r", trace_id="t", node_id="n", timestamp=1.0, output={"o": 2})
    c2 = migrate_graph_event_to_cloud_event(e2)
    assert c2.type == "ai.coreason.node.done"
    assert c2.data == {"o": 2}

    # ARTIFACT_GENERATED
    e3 = GraphEventArtifactGenerated(
        run_id="r", trace_id="t", node_id="n", timestamp=1.0, artifact_type="image/png", url="http://x"
    )
    c3 = migrate_graph_event_to_cloud_event(e3)
    assert c3.type == "ai.coreason.artifact.generated"
    assert c3.datacontenttype == EventContentType.ARTIFACT
    assert c3.data == {"artifact_type": "image/png", "url": "http://x"}

    # COUNCIL_VOTE
    e4 = GraphEventCouncilVote(run_id="r", trace_id="t", node_id="n", timestamp=1.0, votes={"alice": True})
    c4 = migrate_graph_event_to_cloud_event(e4)
    assert c4.type == "ai.coreason.council.vote"
    assert c4.data == {"votes": {"alice": True}}

    # NODE_RESTORED
    e5 = GraphEventNodeRestored(run_id="r", trace_id="t", node_id="n", timestamp=1.0, status="active")
    c5 = migrate_graph_event_to_cloud_event(e5)
    assert c5.type == "ai.coreason.node.restored"
    assert c5.data == {"status": "active"}
