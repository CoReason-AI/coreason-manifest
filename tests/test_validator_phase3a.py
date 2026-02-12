from typing import cast

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import (
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import AgentNode, Brain, SwitchNode
from coreason_manifest.spec.core.tools import ToolPack
from coreason_manifest.utils.validator import validate_flow


# Helpers to create dummy objects
def create_metadata() -> FlowMetadata:
    return FlowMetadata(name="test", version="1.0", description="test", tags=[])


def create_interface() -> FlowInterface:
    return FlowInterface(inputs={}, outputs={})


def create_agent_node(node_id: str, tools: list[str]) -> AgentNode:
    return AgentNode(
        id=node_id,
        metadata={},
        supervision=None,
        brain=Brain(role="assistant", persona="helpful", reasoning=None, reflex=None),
        tools=tools,
    )


def create_switch_node(node_id: str, variable: str, cases: dict[str, str], default: str) -> SwitchNode:
    return SwitchNode(
        id=node_id,
        metadata={},
        supervision=None,
        variable=variable,
        cases=cases,
        default=default,
    )


def create_tool_pack(namespace: str, tools: list[str]) -> ToolPack:
    return ToolPack(
        kind="ToolPack",
        namespace=namespace,
        tools=tools,
        dependencies=[],
        env_vars=[],
    )


def test_validate_graph_flow_valid() -> None:
    agent = create_agent_node("agent1", ["tool1"])
    tp = create_tool_pack("ns", ["tool1"])
    graph = Graph(nodes={"agent1": agent}, edges=[])
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        definitions=FlowDefinitions(tool_packs={"tp": tp}),
    )
    errors = validate_flow(flow)
    assert errors == []


def test_validate_graph_flow_invalid_edges() -> None:
    agent = create_agent_node("agent1", [])
    # Edge points to non-existent nodes
    graph = Graph(
        nodes={"agent1": agent},
        edges=[
            Edge(source="agent1", target="missing"),
            Edge(source="missing", target="agent1"),
        ],
    )
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
    )
    errors = validate_flow(flow)
    assert len(errors) == 2
    assert "Dangling Edge Error: Target 'missing' not found in graph nodes." in errors
    assert "Dangling Edge Error: Source 'missing' not found in graph nodes." in errors


def test_validate_switch_node_invalid_targets() -> None:
    switch = create_switch_node("switch1", "var", {"case1": "missing1"}, "missing2")
    graph = Graph(nodes={"switch1": switch}, edges=[])
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
    )
    errors = validate_flow(flow)
    assert len(errors) == 2
    assert "Broken Switch Error: Node 'switch1' case 'case1' points to missing ID 'missing1'." in errors
    assert "Broken Switch Error: Node 'switch1' default route points to missing ID 'missing2'." in errors


def test_validate_missing_tool() -> None:
    agent = create_agent_node("agent1", ["tool1"])
    # Tool pack has no tools
    tp = create_tool_pack("ns", [])
    graph = Graph(nodes={"agent1": agent}, edges=[])

    # Expect ValidationError during instantiation due to Runtime Integrity
    with pytest.raises(ValidationError, match="requires missing tool 'tool1'"):
        GraphFlow(
            kind="GraphFlow",
            metadata=create_metadata(),
            interface=create_interface(),
            blackboard=None,
            graph=graph,
            definitions=FlowDefinitions(tool_packs={"tp": tp}),
        )


def test_validate_governance_sanity() -> None:
    agent = create_agent_node("agent1", [])
    graph = Graph(nodes={"agent1": agent}, edges=[])
    gov = Governance(rate_limit_rpm=-1, cost_limit_usd=-5.0)
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        governance=gov,
    )
    errors = validate_flow(flow)
    assert len(errors) == 2
    assert "Governance Error: rate_limit_rpm cannot be negative." in errors
    assert "Governance Error: cost_limit_usd cannot be negative." in errors


def test_validate_linear_flow_valid() -> None:
    agent = create_agent_node("agent1", ["tool1"])
    tp = create_tool_pack("ns", ["tool1"])
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        sequence=[agent],
        definitions=FlowDefinitions(tool_packs={"tp": tp}),
    )
    errors = validate_flow(flow)
    assert errors == []


def test_validate_linear_flow_empty() -> None:
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        sequence=[],
    )
    errors = validate_flow(flow)
    assert len(errors) == 1
    assert "LinearFlow Error: Sequence cannot be empty." in errors


def test_validate_linear_flow_switch_missing_targets() -> None:
    # Switch node in linear flow referring to missing nodes (since they are not in sequence)
    switch = create_switch_node("switch1", "var", {"case1": "missing1"}, "missing2")
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        sequence=[switch],  # switch is the only node
    )
    errors = validate_flow(flow)
    # Target IDs must be present in the sequence
    assert len(errors) == 2
    assert "Broken Switch Error: Node 'switch1' case 'case1' points to missing ID 'missing1'." in errors
    assert "Broken Switch Error: Node 'switch1' default route points to missing ID 'missing2'." in errors


def test_validate_flow_invalid_type() -> None:
    """Test that validate_flow handles unknown flow types gracefully."""

    class DummyFlow:
        governance = None
        definitions = None

    # Should not raise error and return empty list (checks skipped)
    errors = validate_flow(cast("LinearFlow", DummyFlow()))
    assert errors == []


def test_validate_duplicate_node_ids() -> None:
    """Test validation for duplicate node IDs."""
    agent1 = create_agent_node("agent1", [])
    agent2 = create_agent_node("agent1", [])  # Duplicate ID
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        sequence=[agent1, agent2],
    )
    errors = validate_flow(flow)
    assert "ID Collision Error: Duplicate Node ID 'agent1' found." in errors


def test_validate_graph_flow_empty() -> None:
    """Test validation for empty graph."""
    graph = Graph(nodes={}, edges=[])
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
    )
    errors = validate_flow(flow)
    assert "GraphFlow Error: Graph must contain at least one node." in errors


def test_validate_graph_flow_key_id_mismatch() -> None:
    """Test validation for mismatch between graph node key and node ID."""
    agent = create_agent_node("agent1", [])
    # Key is "wrong_key", ID is "agent1"
    graph = Graph(nodes={"wrong_key": agent}, edges=[])
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
    )
    errors = validate_flow(flow)
    assert "Graph Integrity Error: Node key 'wrong_key' does not match Node ID 'agent1'." in errors


def test_validate_orphan_nodes() -> None:
    """Test orphan node detection with entry point exemption."""
    # node1 is entry point (first in dict)
    # node2 is connected
    # node3 is orphan
    node1 = create_agent_node("node1", [])
    node2 = create_agent_node("node2", [])
    node3 = create_agent_node("node3", [])

    graph = Graph(nodes={"node1": node1, "node2": node2, "node3": node3}, edges=[Edge(source="node1", target="node2")])
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
    )
    errors = validate_flow(flow)

    # node1 has no incoming edges but should be exempt as entry point
    # node3 has no incoming edges and should be flagged
    assert not any("node1" in e for e in errors)
    assert any("Orphan Node Warning: Node 'node3' has no incoming edges." in e for e in errors)
