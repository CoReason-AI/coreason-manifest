# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

from coreason_manifest import (
    GraphEvent,
    GraphEventArtifactGenerated,
    GraphEventCouncilVote,
    GraphEventNodeDone,
    GraphEventNodeStart,
    GraphEventNodeStream,
)


def test_payload_recursion() -> None:
    """Edge Case: Deeply nested dictionary in payload."""
    recursive_data: dict[str, Any] = {"level": 0}
    current = recursive_data
    # Reducing recursion depth to 50 to avoid Pydantic/JSON serialization limits in CI environments
    for i in range(50):
        current["next"] = {"level": i + 1}
        current = current["next"]

    event = GraphEventNodeStart(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, payload=recursive_data)

    dumped = event.dump()
    assert dumped["payload"]["level"] == 0
    # verify deep access
    assert dumped["payload"]["next"]["next"]["level"] == 2


def test_special_characters() -> None:
    """Edge Case: Unicode/Emoji/Control chars."""
    special_str = "Hello \u0000 World 🌍 🚀 \n \t"
    event = GraphEventNodeStream(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, chunk=special_str)

    dumped = event.dump()
    assert dumped["chunk"] == special_str


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

    dumped = event.dump()

    assert dumped["output"] == {}
    assert "visual_cue" not in dumped  # Should be excluded if None
    assert dumped["event_type"] == "NODE_DONE"


def test_large_payload() -> None:
    """Edge Case: Large payload."""
    large_str = "a" * 100_000  # 100KB
    event = GraphEventNodeStream(run_id="r1", trace_id="t1", node_id="n1", timestamp=100.0, chunk=large_str)

    dumped = event.dump()
    assert len(dumped["chunk"]) == 100_000


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

    # Dump Check
    dumped_events = [e.dump() for e in events]

    assert len(dumped_events) == 6
    assert dumped_events[0]["event_type"] == "NODE_START"
    assert dumped_events[0]["payload"] == {"query": "Why?"}

    # Check streaming sequence
    assert dumped_events[1]["chunk"] == "Because"
    assert dumped_events[2]["chunk"] == " "
    assert dumped_events[3]["chunk"] == "Science"

    # Check artifact
    assert dumped_events[4]["event_type"] == "ARTIFACT_GENERATED"
    assert dumped_events[4]["artifact_type"] == "text/plain"

    # Check done
    assert dumped_events[5]["event_type"] == "NODE_DONE"
    assert dumped_events[5]["output"] == {"answer": "Because Science"}

    # Verify Extension consistency
    assert dumped_events[1]["visual_cue"] == "typing"


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

    dumped = event.dump()

    assert dumped["event_type"] == "COUNCIL_VOTE"
    assert dumped["votes"] == votes_data
    assert dumped["votes"]["results"]["legal_bot"]["vote"] == "REJECT"
