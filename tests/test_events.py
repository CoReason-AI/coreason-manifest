import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.events import (
    ArtifactGenerated,
    ArtifactGeneratedPayload,
    CouncilVote,
    CouncilVotePayload,
    EdgeTraversed,
    EdgeTraversedPayload,
    GraphEvent,
    NodeCompleted,
    NodeCompletedPayload,
    NodeInit,
    NodeInitPayload,
    NodeRestored,
    NodeSkipped,
    NodeSkippedPayload,
    NodeStarted,
    NodeStartedPayload,
    NodeStream,
    NodeStreamPayload,
    WorkflowError,
    WorkflowErrorPayload,
)


def test_graph_event_creation() -> None:
    """Test successful creation of a GraphEvent with NodeInit payload."""
    payload = NodeInit(node_id="node-1", type="AGENT", visual_cue="THINKING")
    event = GraphEvent(
        event_type="NODE_INIT",
        run_id="run-1",
        trace_id="trace-1",
        node_id="node-1",
        timestamp=1234567890.0,
        payload=payload.model_dump(),
        visual_metadata={"color": "#FFFFFF"},
    )
    assert event.event_type == "NODE_INIT"
    assert event.payload["type"] == "AGENT"
    assert event.visual_metadata["color"] == "#FFFFFF"


def test_graph_event_default_trace_id() -> None:
    """Test default trace_id assignment."""
    payload = NodeInit(node_id="node-1")
    event = GraphEvent(
        event_type="NODE_INIT",
        run_id="run-1",
        node_id="node-1",
        timestamp=1234567890.0,
        payload=payload.model_dump(),
        visual_metadata={"color": "#FFFFFF"},
    )
    assert event.trace_id == "unknown"


def test_graph_event_validation_error_missing_fields() -> None:
    """Test validation error for missing required fields."""
    with pytest.raises(ValidationError):
        GraphEvent(
            event_type="NODE_INIT",
            # run_id is missing
            node_id="node-1",
            timestamp=1234567890.0,
            payload={},
            visual_metadata={},
        )  # type: ignore[call-arg]


def test_graph_event_extra_forbid() -> None:
    """Test that extra fields are forbidden."""
    payload = NodeInit(node_id="node-1")
    with pytest.raises(ValidationError):
        GraphEvent(
            event_type="NODE_INIT",
            run_id="run-1",
            node_id="node-1",
            timestamp=1234567890.0,
            payload=payload.model_dump(),
            visual_metadata={"color": "#FFFFFF"},
            extra_field="this should fail",
        )  # type: ignore[call-arg]


def test_node_started_payload() -> None:
    """Test NodeStarted payload structure."""
    payload = NodeStarted(node_id="node-1", timestamp=123.0, status="RUNNING")
    assert payload.node_id == "node-1"
    assert payload.status == "RUNNING"
    assert payload.visual_cue == "PULSE"


def test_node_completed_payload() -> None:
    """Test NodeCompleted payload structure."""
    payload = NodeCompleted(node_id="node-1", output_summary="Done", status="SUCCESS")
    assert payload.status == "SUCCESS"
    assert payload.visual_cue == "GREEN_GLOW"


def test_node_restored_payload() -> None:
    """Test NodeRestored payload structure."""
    payload = NodeRestored(node_id="node-1", output_summary="Restored", status="RESTORED")
    assert payload.status == "RESTORED"
    assert payload.visual_cue == "INSTANT_GREEN"


def test_node_skipped_payload() -> None:
    """Test NodeSkipped payload structure."""
    payload = NodeSkipped(node_id="node-1", status="SKIPPED")
    assert payload.status == "SKIPPED"
    assert payload.visual_cue == "GREY_OUT"


def test_node_stream_payload() -> None:
    """Test NodeStream payload structure."""
    payload = NodeStream(node_id="node-1", chunk="Hello")
    assert payload.chunk == "Hello"
    assert payload.visual_cue == "TEXT_BUBBLE"


def test_artifact_generated_payload() -> None:
    """Test ArtifactGenerated payload structure."""
    payload = ArtifactGenerated(node_id="node-1", url="http://example.com/doc.pdf")
    assert payload.artifact_type == "PDF"
    assert payload.url == "http://example.com/doc.pdf"


def test_edge_traversed_payload() -> None:
    """Test EdgeTraversed payload structure."""
    payload = EdgeTraversed(source="node-1", target="node-2")
    assert payload.source == "node-1"
    assert payload.target == "node-2"
    assert payload.animation_speed == "FAST"


def test_council_vote_payload() -> None:
    """Test CouncilVote payload structure."""
    payload = CouncilVote(node_id="node-1", votes={"agent-1": "approve"})
    assert payload.votes["agent-1"] == "approve"


def test_workflow_error_payload() -> None:
    """Test WorkflowError payload structure."""
    payload = WorkflowError(
        node_id="node-1",
        error_message="Oops",
        stack_trace="Traceback...",
        input_snapshot={"key": "value"},
    )
    assert payload.status == "ERROR"
    assert payload.visual_cue == "RED_FLASH"


def test_aliases() -> None:
    """Test that aliases work correctly."""
    assert NodeInitPayload is NodeInit
    assert NodeStartedPayload is NodeStarted
    assert NodeCompletedPayload is NodeCompleted
    assert NodeSkippedPayload is NodeSkipped
    assert NodeStreamPayload is NodeStream
    assert EdgeTraversedPayload is EdgeTraversed
    assert ArtifactGeneratedPayload is ArtifactGenerated
    assert CouncilVotePayload is CouncilVote
    assert WorkflowErrorPayload is WorkflowError


# def test_node_end_compatibility() -> None:
#     """Test NODE_END event type compatibility."""
#     # NODE_END was removed from GraphEvent literal
#     pass
