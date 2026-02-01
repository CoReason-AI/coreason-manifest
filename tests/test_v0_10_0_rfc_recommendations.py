# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Dict, Any
import pytest
from pydantic import ValidationError, TypeAdapter

from coreason_manifest.definitions.topology import AgentNode, LogicNode, GraphTopology, Edge, ConditionalEdge, RouterDefinition, RouterRef
from coreason_manifest.definitions.events import GraphEvent, NodeInit, GraphEventNodeInit, NodeStarted

def test_agent_node_overrides() -> None:
    """Test that AgentNode accepts runtime overrides."""
    node = AgentNode(
        id="a1",
        agent_name="test_agent",
        overrides={"temperature": 0.9, "model": "gpt-4"}
    )
    assert node.overrides == {"temperature": 0.9, "model": "gpt-4"}

def test_node_metadata() -> None:
    """Test that nodes accept metadata."""
    node = LogicNode(
        id="l1",
        code="pass",
        metadata={"cost_center": "dev", "timeout_ms": 100}
    )
    assert node.metadata["cost_center"] == "dev"
    assert node.metadata["timeout_ms"] == 100

def test_graph_topology_validation_success() -> None:
    """Test successful graph validation."""
    n1 = LogicNode(id="n1", code="pass")
    n2 = LogicNode(id="n2", code="pass")
    edge = Edge(source_node_id="n1", target_node_id="n2")

    topo = GraphTopology(nodes=[n1, n2], edges=[edge])
    assert len(topo.nodes) == 2
    assert len(topo.edges) == 1

def test_graph_topology_validation_failure_missing_source() -> None:
    """Test graph validation fails when edge source is missing."""
    n1 = LogicNode(id="n1", code="pass")
    edge = Edge(source_node_id="missing", target_node_id="n1")

    with pytest.raises(ValidationError) as exc:
        GraphTopology(nodes=[n1], edges=[edge])
    assert "Edge source node 'missing' not found in nodes" in str(exc.value)

def test_graph_topology_validation_failure_missing_target() -> None:
    """Test graph validation fails when edge target is missing."""
    n1 = LogicNode(id="n1", code="pass")
    edge = Edge(source_node_id="n1", target_node_id="missing")

    with pytest.raises(ValidationError) as exc:
        GraphTopology(nodes=[n1], edges=[edge])
    assert "Edge target node 'missing' not found in nodes" in str(exc.value)

def test_graph_topology_validation_conditional_edge() -> None:
    """Test graph validation for conditional edges."""
    n1 = LogicNode(id="n1", code="pass")
    n2 = LogicNode(id="n2", code="pass")
    # Missing n3

    edge = ConditionalEdge(
        source_node_id="n1",
        router_logic="my_router",
        mapping={"yes": "n2", "no": "n3"}
    )

    with pytest.raises(ValidationError) as exc:
        GraphTopology(nodes=[n1, n2], edges=[edge])
    assert "ConditionalEdge target node 'n3' not found in nodes" in str(exc.value)

def test_graph_event_discriminated_union() -> None:
    """Test GraphEvent discriminated union behavior."""
    payload = NodeInit(node_id="n1", type="AGENT")
    event_data = {
        "event_type": "NODE_INIT",
        "run_id": "r1",
        "node_id": "n1",
        "timestamp": 123.456,
        "payload": payload.model_dump(),
        "visual_metadata": {"color": "red"}
    }

    # Use TypeAdapter to validate the Union
    event: GraphEvent = TypeAdapter(GraphEvent).validate_python(event_data)

    # Check it is instance of GraphEventNodeInit
    assert isinstance(event, GraphEventNodeInit)
    assert event.event_type == "NODE_INIT"
    assert isinstance(event.payload, NodeInit)
    assert event.payload.type == "AGENT"

    # Check direct instantiation from dict works due to coercion
    event_data2 = {
        "event_type": "NODE_INIT",
        "run_id": "r1",
        "node_id": "n1",
        "timestamp": 123.456,
        "payload": {"node_id": "n1", "type": "AGENT"},
        "visual_metadata": {"color": "red"}
    }
    event2: GraphEvent = TypeAdapter(GraphEvent).validate_python(event_data2)
    assert isinstance(event2.payload, NodeInit)

def test_graph_event_payload_validation() -> None:
    """Test that GraphEvent strictly validates payload structure."""

    # Let's try NODE_START which requires NodeStarted.
    # NodeStarted requires 'status' and 'timestamp'.

    bad_data = {
        "event_type": "NODE_START",
        "run_id": "r1",
        "node_id": "n1",
        "timestamp": 123.456,
        "payload": {"node_id": "n1"}, # Missing status, timestamp
        "visual_metadata": {"color": "red"}
    }

    with pytest.raises(ValidationError):
        TypeAdapter(GraphEvent).validate_python(bad_data)
