# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict

from coreason_manifest import (
    EventContentType,
    GraphEvent,
    GraphEventArtifactGenerated,
    GraphEventCouncilVote,
    GraphEventNodeDone,
    GraphEventNodeStart,
    GraphEventNodeStream,
    migrate_graph_event_to_cloud_event,
)


def test_payload_recursion() -> None:
    """Edge Case: Deeply nested dictionary in payload."""
    recursive_data: Dict[str, Any] = {"level": 0}
    current = recursive_data
    for i in range(100):
        current["next"] = {"level": i + 1}
        current = current["next"]

    event = GraphEventNodeStart(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, payload=recursive_data)

    # Should serialize fine (Python default depth is usually 1000)
    # CloudEvent dump checks JSON serialization
    ce = migrate_graph_event_to_cloud_event(event)
    dumped = ce.dump()
    assert dumped["data"]["level"] == 0
    # verify deep access
    assert dumped["data"]["next"]["next"]["level"] == 2


def test_special_characters() -> None:
    """Edge Case: Unicode/Emoji/Control chars."""
    special_str = "Hello \u0000 World 🌍 🚀 \n \t"
    event = GraphEventNodeStream(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, chunk=special_str)

    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.data is not None
    assert ce.data["chunk"] == special_str

    dumped = ce.dump()
    assert dumped["data"]["chunk"] == special_str


def test_empty_fields() -> None:
    """Edge Case: Optional fields missing or None."""
    event = GraphEventNodeDone(
        run_id="r1",
        trace_id="t1",
        node_id="n1",
        timestamp=100.0,
        output={},  # Empty output
        sequence_id=None,
        visual_cue=None,
    )

    ce = migrate_graph_event_to_cloud_event(event)
    dumped = ce.dump()

    assert ce.data == {}
    assert "com_coreason_ui_cue" not in dumped  # Should be excluded if None
    assert ce.type == "ai.coreason.node.done"


def test_large_payload() -> None:
    """Edge Case: Large payload."""
    large_str = "a" * 100_000  # 100KB
    event = GraphEventNodeStream(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, chunk=large_str)

    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.data is not None
    assert len(ce.data["chunk"]) == 100_000


def test_full_node_lifecycle() -> None:
    """Complex Case: Simulate a full node lifecycle."""
    events: list[GraphEvent] = []

    # Start
    events.append(
        GraphEventNodeStart(
            run_id="run-1",
            trace_id="trace-1",
            node_id="step-A",
            timestamp=100.0,
            payload={"query": "Why?"},
            sequence_id=0,
            visual_cue="start",
        )
    )

    # Stream x3
    for i, char in enumerate(["Because", " ", "Science"]):
        events.append(
            GraphEventNodeStream(
                run_id="run-1",
                trace_id="trace-1",
                node_id="step-A",
                timestamp=100.1 + i,
                chunk=char,
                sequence_id=1 + i,
                visual_cue="typing",
            )
        )

    # Artifact
    events.append(
        GraphEventArtifactGenerated(
            run_id="run-1",
            trace_id="trace-1",
            node_id="step-A",
            timestamp=105.0,
            artifact_type="text/plain",
            url="s3://bucket/log.txt",
            sequence_id=4,
        )
    )

    # Done
    events.append(
        GraphEventNodeDone(
            run_id="run-1",
            trace_id="trace-1",
            node_id="step-A",
            timestamp=106.0,
            output={"answer": "Because Science"},
            sequence_id=5,
            visual_cue="done",
        )
    )

    # Migration Check
    cloud_events = [migrate_graph_event_to_cloud_event(e) for e in events]

    assert len(cloud_events) == 6
    assert cloud_events[0].type == "ai.coreason.node.start"
    assert cloud_events[0].data == {"query": "Why?"}

    # Check streaming sequence
    assert cloud_events[1].data == {"chunk": "Because"}
    assert cloud_events[2].data == {"chunk": " "}
    assert cloud_events[3].data == {"chunk": "Science"}
    assert cloud_events[3].datacontenttype == EventContentType.STREAM

    # Check artifact
    assert cloud_events[4].type == "ai.coreason.artifact.generated"
    assert cloud_events[4].datacontenttype == EventContentType.ARTIFACT

    # Check done
    assert cloud_events[5].type == "ai.coreason.node.done"
    assert cloud_events[5].data == {"answer": "Because Science"}

    # Verify Extension consistency
    assert cloud_events[1].dump()["com_coreason_ui_cue"] == "typing"


def test_complex_council_vote() -> None:
    """Complex Case: Council Vote with nested structure."""
    votes_data = {
        "motion_id": "m-123",
        "quorum_reached": True,
        "results": {
            "security_bot": {"vote": "APPROVE", "reason": "Safe"},
            "legal_bot": {"vote": "REJECT", "reason": "Too risky", "citations": ["Policy 7"]},
            "ethics_bot": {"vote": "ABSTAIN", "reason": "Insufficient data"},
        },
        "final_decision": "REJECT",
    }

    event = GraphEventCouncilVote(run_id="r1", trace_id="t1", node_id="council-1", timestamp=100.0, votes=votes_data)

    ce = migrate_graph_event_to_cloud_event(event)

    assert ce.type == "ai.coreason.council.vote"
    assert ce.data is not None
    assert ce.data["votes"] == votes_data
    assert ce.data["votes"]["results"]["legal_bot"]["vote"] == "REJECT"
