# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

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
