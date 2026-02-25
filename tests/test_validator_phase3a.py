from typing import cast

import pytest

from coreason_manifest.spec.core.flow import (
    Blackboard,
    DataSchema,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
    VariableDef,
)
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, SwitchNode
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.utils.validator import validate_flow


# Helpers to create dummy objects
def create_metadata() -> FlowMetadata:
    return FlowMetadata(name="test", version="1.0.0", description="test", tags=[])


def create_interface() -> FlowInterface:
    return FlowInterface(
        inputs=DataSchema(json_schema={}),
        outputs=DataSchema(json_schema={}),
    )


def create_agent_node(node_id: str, tools: list[str]) -> AgentNode:
    return AgentNode(
        id=node_id,
        metadata={},
        resilience=None,
        profile=CognitiveProfile(role="assistant", persona="helpful", reasoning=None, fast_path=None),
        tools=tools,
    )


def create_switch_node(node_id: str, variable: str, cases: dict[str, str], default: str) -> SwitchNode:
    return SwitchNode(
        id=node_id,
        metadata={},
        # # Removed from Node
        variable=variable,
        cases=cases,
        default=default,
    )


def create_tool_pack(namespace: str, tools: list[str]) -> ToolPack:
    return ToolPack(
        kind="ToolPack",
        namespace=namespace,
        tools=[ToolCapability(name=t) for t in tools],
        dependencies=[],
        env_vars=[],
    )


def test_validate_graph_flow_valid() -> None:
    agent = create_agent_node("agent1", ["tool1"])
    tp = create_tool_pack("ns", ["tool1"])
    graph = Graph(nodes={"agent1": agent}, edges=[], entry_point="agent1")
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
            Edge(from_node="agent1", to_node="missing"),
            Edge(from_node="missing", to_node="agent1"),
        ],
        entry_point="agent1",
    )

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        status="draft",
    )
    errors = validate_flow(flow)
    assert any(e.code == "ERR_TOPOLOGY_DANGLING_EDGE" and e.details["target"] == "missing" for e in errors if e.code == "ERR_TOPOLOGY_DANGLING_EDGE" and "target" in e.details)
    assert any(e.code == "ERR_TOPOLOGY_DANGLING_EDGE" and e.details["source"] == "missing" for e in errors if e.code == "ERR_TOPOLOGY_DANGLING_EDGE" and "source" in e.details)


def test_validate_switch_node_invalid_targets() -> None:
    switch = create_switch_node("switch1", "var", {"case1": "missing1"}, "missing2")
    graph = Graph(nodes={"switch1": switch}, edges=[], entry_point="switch1")
    blackboard = Blackboard(
        variables={"var": VariableDef(type="string")},
        persistence=False,
    )
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=blackboard,
        graph=graph,
    )
    errors = validate_flow(flow)
    assert len(errors) == 2
    assert any(e.code == "ERR_TOPOLOGY_BROKEN_SWITCH" and e.details.get("target_id") == "missing1" for e in errors)
    assert any(e.code == "ERR_TOPOLOGY_BROKEN_SWITCH" and e.details.get("target_id") == "missing2" for e in errors)


def test_validate_missing_tool() -> None:
    agent = create_agent_node("agent1", ["tool1"])
    # Tool pack has no tools
    tp = create_tool_pack("ns", [])
    graph = Graph(nodes={"agent1": agent}, edges=[], entry_point="agent1")

    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        definitions=FlowDefinitions(tool_packs={"tp": tp}),
    )
    errors = validate_flow(flow)
    assert any(e.code == "ERR_CAP_MISSING_TOOL_001" and e.details.get("tool") == "tool1" for e in errors)


def test_validate_governance_sanity() -> None:
    agent = create_agent_node("agent1", [])
    graph = Graph(nodes={"agent1": agent}, edges=[], entry_point="agent1")
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
    assert all(e.code == "ERR_GOV_INVALID_CONFIG" for e in errors)


def test_validate_linear_flow_valid() -> None:
    agent = create_agent_node("agent1", ["tool1"])
    tp = create_tool_pack("ns", ["tool1"])
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        steps=[agent],
        definitions=FlowDefinitions(tool_packs={"tp": tp}),
    )
    errors = validate_flow(flow)
    assert errors == []


def test_validate_linear_flow_empty() -> None:
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        steps=[],
    )
    errors = validate_flow(flow)
    assert len(errors) == 1
    assert errors[0].code == "ERR_TOPOLOGY_LINEAR_EMPTY"


def test_validate_linear_flow_switch_missing_targets() -> None:
    # Switch node in linear flow referring to missing nodes (since they are not in sequence)
    switch = create_switch_node("switch1", "var", {"case1": "missing1"}, "missing2")
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        steps=[switch],  # switch is the only node
    )
    errors = validate_flow(flow)
    # Target IDs must be present in the sequence
    assert len(errors) == 2
    assert any(e.code == "ERR_TOPOLOGY_BROKEN_SWITCH" and e.details.get("target_id") == "missing1" for e in errors)
    assert any(e.code == "ERR_TOPOLOGY_BROKEN_SWITCH" and e.details.get("target_id") == "missing2" for e in errors)


def test_validate_flow_invalid_type() -> None:
    """Test that validate_flow handles unknown flow types gracefully."""

    class DummyFlow:
        governance = None
        definitions = None

    with pytest.raises(ValueError):
        validate_flow(cast("LinearFlow", DummyFlow()))


def test_validate_duplicate_node_ids() -> None:
    """Test validation for duplicate node IDs."""
    agent1 = create_agent_node("agent1", [])
    agent2 = create_agent_node("agent1", [])  # Duplicate ID
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        steps=[agent1, agent2],
    )
    errors = validate_flow(flow)
    assert any(e.code == "ERR_TOPOLOGY_NODE_ID_COLLISION" for e in errors)


def test_validate_graph_flow_empty() -> None:
    """Test validation for empty graph."""
    import pytest

    # Entry point missing is checked in verify_integrity (strict) or validate_flow
    graph = Graph(nodes={}, edges=[], entry_point="missing")

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
    )
    errors = validate_flow(flow)

    # We expect graph empty error
    assert any(e.code == "ERR_TOPOLOGY_EMPTY_GRAPH" for e in errors)
    # And potentially missing entry point
    assert any(e.code == "ERR_TOPOLOGY_MISSING_ENTRY" for e in errors)


def test_validate_graph_flow_key_id_mismatch() -> None:
    """Test validation for mismatch between graph node key and node ID."""
    agent = create_agent_node("agent1", [])
    # Key is "wrong_key", ID is "agent1"

    graph = Graph(nodes={"wrong_key": agent}, edges=[], entry_point="wrong_key")
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
    )
    errors = validate_flow(flow)
    assert any(e.code == "ERR_TOPOLOGY_ID_MISMATCH" for e in errors)


def test_validate_orphan_nodes() -> None:
    """Test orphan node detection with entry point exemption."""
    # node1 is entry point (first in dict)
    # node2 is connected
    # node3 is orphan
    node1 = create_agent_node("node1", [])
    node2 = create_agent_node("node2", [])
    node3 = create_agent_node("node3", [])

    graph = Graph(
        nodes={"node1": node1, "node2": node2, "node3": node3},
        edges=[Edge(from_node="node1", to_node="node2")],
        entry_point="node1",
    )
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
    assert not any(e.node_id == "node1" for e in errors if e.code == "ERR_TOPOLOGY_ORPHAN_001")
    assert any(e.node_id == "node3" for e in errors if e.code == "ERR_TOPOLOGY_ORPHAN_001")
