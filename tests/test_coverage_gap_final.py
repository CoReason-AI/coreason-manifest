from datetime import datetime

import pytest

from coreason_manifest.builder import NewGraphFlow
from coreason_manifest.spec.core.engines import ComputerUseReasoning
from coreason_manifest.spec.core.flow import AnyNode, FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, PlaceholderNode
from coreason_manifest.spec.interop.compliance import ErrorCatalog
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.gatekeeper import validate_policy


def test_builder_set_entry_point() -> None:
    """Cover builder.py set_entry_point method."""
    builder = NewGraphFlow("test", "1.0.0", "desc")
    builder.add_agent(AgentNode(id="node1", profile=CognitiveProfile(role="r", persona="p")))

    # Call the method to cover it
    builder.set_entry_point("node1")

    flow = builder.build()
    assert flow.graph.entry_point == "node1"


def test_gatekeeper_published_dangerous_unreachable() -> None:
    """Cover gatekeeper.py published mode with dangerous unreachable nodes."""
    # Create a flow manually to ensure status="published" and dangerous node
    nodes: dict[str, AnyNode] = {
        "node1": AgentNode(id="node1", profile=CognitiveProfile(role="assistant", persona="p")),
        "node2": AgentNode(
            id="node2",
            profile=CognitiveProfile(
                role="hacker",
                persona="p",
                reasoning=ComputerUseReasoning(
                    model="gpt-4", interaction_mode="native_os", coordinate_system="normalized_0_1"
                ),
            ),
        ),
    }

    flow = GraphFlow(
        status="published",
        metadata=FlowMetadata(name="Test Flow", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes=nodes, edges=[], entry_point="node1"),
    )

    reports = validate_policy(flow)

    # Verify we hit the published dangerous block
    risk_reports = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_UNREACHABLE_RISK_003]
    assert len(risk_reports) > 0
    assert risk_reports[0].severity == "violation"


def test_telemetry_parent_hash_sync() -> None:
    """
    Cover telemetry.py:92 logic: parent_hash present, parent_hashes list, mismatch.
    """
    # Create a NodeExecution with parent_hash="h1" and parent_hashes=["h2"]
    ne = NodeExecution(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=datetime.now(),
        duration_ms=10,
        request_id="req1",
        # Inputs to trigger the logic
        parent_hash="h1",
        parent_hashes=["h2"],
    )

    assert "h1" in ne.parent_hashes
    assert "h2" in ne.parent_hashes
    assert len(ne.parent_hashes) == 2


def test_telemetry_parent_hash_sync_none() -> None:
    """
    Cover telemetry.py:91 logic: parent_hash present, parent_hashes None.
    """
    # Create a NodeExecution with parent_hash="h1" and parent_hashes missing
    ne = NodeExecution(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={},
        outputs={},
        timestamp=datetime.now(),
        duration_ms=10,
        request_id="req1",
        # Inputs to trigger the logic
        parent_hash="h1",
        # parent_hashes defaults to list via default_factory, BUT model_validator mode="before" runs on raw dict.
        # If we omit it in dict, get() returns None?
        # Wait, if we use NodeExecution constructor, we pass arguments.
        # Pydantic validates BEFORE model creation if we pass dict?
        # model_validator(mode="before") intercepts the inputs.
        # If I don't pass parent_hashes, it's NOT in the dict passed to enforce_envelope_consistency?
        # Yes.
    )

    # In enforce_envelope_consistency:
    # prev_hashes = data.get("parent_hashes") -> None
    # if p_hash ("h1"):
    #   if prev_hashes is None: -> True
    #     data["parent_hashes"] = [p_hash]

    assert ne.parent_hashes == ["h1"]


def test_flow_published_placeholder_check() -> None:
    """
    Cover flow.py:411 logic: Published flow with PlaceholderNode raises ManifestError.
    """
    nodes: dict[str, AnyNode] = {
        "start": AgentNode(id="start", profile=CognitiveProfile(role="assistant", persona="p")),
        "tbd": PlaceholderNode(id="tbd", required_capabilities=[]),
    }

    # We must explicitly set status="published" to trigger the validator

    with pytest.raises(ManifestError) as excinfo:
        GraphFlow(
            status="published",
            metadata=FlowMetadata(name="Test Flow", version="1.0.0"),
            interface=FlowInterface(),
            graph=Graph(
                nodes=nodes,
                edges=[],
                entry_point="start",  # Valid entry point, so we pass check 1
            ),
        )

    assert "CRSN-VAL-ABSTRACT-NODE" in str(excinfo.value)
