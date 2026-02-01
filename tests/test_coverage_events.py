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

from coreason_manifest.definitions.events import (
    ArtifactGenerated,
    CouncilVote,
    EdgeTraversed,
    GraphEventArtifactGenerated,
    GraphEventCouncilVote,
    GraphEventEdgeActive,
    GraphEventNodeRestored,
    NodeRestored,
    migrate_graph_event_to_cloud_event,
)


def test_coverage_node_restored() -> None:
    event = GraphEventNodeRestored(
        event_type="NODE_RESTORED",
        run_id="run-1",
        node_id="node-1",
        timestamp=100.0,
        payload=NodeRestored(node_id="node-1", output_summary="restored", status="RESTORED"),
        visual_metadata={"animation": "green"},
    )
    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.type == "ai.coreason.legacy.node_restored"
    assert isinstance(ce.data, NodeRestored)


def test_coverage_artifact_generated() -> None:
    event = GraphEventArtifactGenerated(
        event_type="ARTIFACT_GENERATED",
        run_id="run-1",
        node_id="node-1",
        timestamp=100.0,
        payload=ArtifactGenerated(node_id="node-1", url="http://test.com"),
        visual_metadata={},
    )
    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.type == "ai.coreason.legacy.artifact_generated"
    assert isinstance(ce.data, ArtifactGenerated)


def test_coverage_edge_active() -> None:
    event = GraphEventEdgeActive(
        event_type="EDGE_ACTIVE",
        run_id="run-1",
        node_id="node-1",
        timestamp=100.0,
        payload=EdgeTraversed(source="n1", target="n2"),
        visual_metadata={},
    )
    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.type == "ai.coreason.legacy.edge_active"
    # EdgeTraversed.as_cloud_event_payload returns self
    assert isinstance(ce.data, EdgeTraversed)


def test_coverage_council_vote() -> None:
    event = GraphEventCouncilVote(
        event_type="COUNCIL_VOTE",
        run_id="run-1",
        node_id="node-1",
        timestamp=100.0,
        payload=CouncilVote(node_id="node-1", votes={"voter": "yes"}),
        visual_metadata={},
    )
    ce = migrate_graph_event_to_cloud_event(event)
    assert ce.type == "ai.coreason.legacy.council_vote"
    assert isinstance(ce.data, CouncilVote)


def test_coverage_fallback_payload() -> None:
    """Test fallback when payload does not implement CloudEventSource."""
    event = GraphEventArtifactGenerated(
        event_type="ARTIFACT_GENERATED",
        run_id="run-1",
        node_id="node-1",
        timestamp=100.0,
        payload=ArtifactGenerated(node_id="node-1", url="http://test.com"),
        visual_metadata={},
    )

    # We want isinstance(event.payload, CloudEventSource) to return False
    # Since we can't easily patch isinstance built-in for a specific call,
    # we can patch the protocol check mechanism or wrap the function.
    # A cleaner way given Python's dynamic nature is to temporarily wrap the payload
    # in a way that hides the method, or mock the payload object on the event.

    # Create a mock that looks like the payload but fails the protocol check?
    # CloudEventSource checks for `as_cloud_event_payload` method.

    # Let's use `patch` on `coreason_manifest.definitions.events.isinstance`.
    # But `isinstance` is a builtin.

    # Alternative: Modify the payload instance to NOT have the method?
    # Pydantic models might be tricky.

    # Let's try mocking the object inside the function call by passing a mock event?
    # But migrate... expects strictly typed GraphEvent.

    # Let's try to 'hide' the method from the instance.
    # Since `as_cloud_event_payload` is defined on the class, we can try to mask it on the instance?
    # But Python looks up class for methods usually.

    # Better: Patch `CloudEventSource` in the events module to exclude the payload type?
    # No, it's a Protocol.

    # BEST:  Just patch the line: `if isinstance(event.payload, CloudEventSource):`
    # We can't patch logic.

    # Let's create a Mock object that mimics the payload but DOES NOT have `as_cloud_event_payload`.
    # And force it into the event. Strict validation might complain if we construct it,
    # but we can modify the attribute after construction (if mutable) or use `model_copy(update=...)`.
    # Pydantic models are usually mutable unless frozen.

    class DummyPayload:
        visual_cue = "dummy"

        def model_dump(self) -> Dict[str, Any]:
            return {}

        # No as_cloud_event_payload method

    # Force inject the dummy payload.
    # This violates type hints but works at runtime.
    event.payload = DummyPayload()  # type: ignore[assignment]

    ce = migrate_graph_event_to_cloud_event(event)

    # Verify fallback path was taken
    assert isinstance(ce.data, DummyPayload)
    # Extra fields are in model_extra or accessed via getattr dynamically if strictly typed
    assert getattr(ce, "com_coreason_ui_cue", None) == "dummy"
