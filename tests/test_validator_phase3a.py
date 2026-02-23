from typing import cast

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

    # Architectural Update: Referential integrity is strictly enforced during model validation.
    # Note: Model validation only enforces Placeholder check. Structural integrity is checked
    # by validate_flow for PUBLISHED flows.
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        status="published",  # Must be published to trigger strict checks
    )

    errors = validate_flow(flow)
    assert any(
        "target 'missing' not found" in e or "source 'missing' not found" in e or "Dangling Edge Error" in e
        for e in errors
    )


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
        status="published",  # Strict checks
    )
    errors = validate_flow(flow)
    assert len(errors) == 2
    assert "Broken Switch Error: Node 'switch1' case 'case1' points to missing ID 'missing1'." in errors
    assert "Broken Switch Error: Node 'switch1' default route points to missing ID 'missing2'." in errors


def test_validate_missing_tool() -> None:
    agent = create_agent_node("agent1", ["tool1"])
    # Tool pack has no tools
    tp = create_tool_pack("ns", [])
    graph = Graph(nodes={"agent1": agent}, edges=[], entry_point="agent1")

    # Expect errors from validate_flow, not ValidationError
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
    # _validate_tools runs for both draft and published? No, let's check validator.py.
    # _validate_tools is NOT wrapped in is_published. So it should run.
    assert any("requires tool 'tool1'" in e for e in errors)


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
    assert "Governance Error: rate_limit_rpm cannot be negative." in errors
    assert "Governance Error: cost_limit_usd cannot be negative." in errors


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
        status="published",  # Required for empty check
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
        steps=[switch],  # switch is the only node
        status="published",  # Required for switch logic check
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
        status = "draft"  # Add status

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
        steps=[agent1, agent2],
    )
    errors = validate_flow(flow)
    assert "ID Collision Error: Duplicate Node ID 'agent1' found." in errors


def test_validate_graph_flow_empty() -> None:
    """Test validation for empty graph."""
    # Graph allows empty nodes if structurally sound (no cycles possible)
    # Entry point missing is checked in verify_integrity (strict) or validate_flow
    graph = Graph(nodes={}, edges=[], entry_point="missing")

    # Architectural Update: Strict referential integrity enforcement causes validation error on instantiation.
    # Note: Now handled by validate_flow for published flows.
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        status="published",
    )

    errors = validate_flow(flow)
    assert any("must contain at least one node" in e for e in errors)


def test_validate_graph_flow_key_id_mismatch() -> None:
    """Test validation for mismatch between graph node key and node ID."""
    agent = create_agent_node("agent1", [])
    # Key is "wrong_key", ID is "agent1"

    # Graph integrity is checked in validate_flow, not Graph constructor
    graph = Graph(nodes={"wrong_key": agent}, edges=[], entry_point="wrong_key")

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        status="published",
    )

    errors = validate_flow(flow)
    assert any("Graph Integrity Error" in e for e in errors)


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
        status="published",  # Required for orphan check
    )
    errors = validate_flow(flow)

    # node1 has no incoming edges but should be exempt as entry point
    # node3 has no incoming edges and should be flagged
    assert not any("node1" in e for e in errors)
    assert any("Orphan Node Warning: Node 'node3' has no incoming edges." in e for e in errors)
