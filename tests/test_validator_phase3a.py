import pytest
from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow, Graph, FlowMetadata, FlowInterface, Blackboard, Edge
from coreason_manifest.spec.core.nodes import AgentNode, SwitchNode, Brain
from coreason_manifest.spec.core.tools import ToolPack, Dependency
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.utils.validator import validate_flow

# Helpers to create dummy objects
def create_metadata():
    return FlowMetadata(name="test", version="1.0", description="test", tags=[])

def create_interface():
    return FlowInterface(inputs={}, outputs={})

def create_agent_node(id: str, tools: list[str]):
    return AgentNode(
        id=id,
        metadata={},
        supervision=None,
        brain=Brain(role="assistant", persona="helpful", reasoning=None, reflex=None),
        tools=tools
    )

def create_switch_node(id: str, variable: str, cases: dict[str, str], default: str):
    return SwitchNode(
        id=id,
        metadata={},
        supervision=None,
        variable=variable,
        cases=cases,
        default=default
    )

def create_tool_pack(namespace: str, tools: list[str]):
    return ToolPack(
        kind="ToolPack",
        namespace=namespace,
        tools=tools,
        dependencies=[],
        env_vars=[]
    )

def test_validate_graph_flow_valid():
    agent = create_agent_node("agent1", ["tool1"])
    tp = create_tool_pack("ns", ["tool1"])
    graph = Graph(nodes={"agent1": agent}, edges=[])
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        tool_packs=[tp]
    )
    errors = validate_flow(flow)
    assert errors == []

def test_validate_graph_flow_invalid_edges():
    agent = create_agent_node("agent1", [])
    # Edge points to non-existent nodes
    graph = Graph(
        nodes={"agent1": agent},
        edges=[Edge(source="agent1", target="missing"), Edge(source="missing", target="agent1")]
    )
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph
    )
    errors = validate_flow(flow)
    assert len(errors) == 2
    assert "Edge target 'missing' not found in graph nodes." in errors
    assert "Edge source 'missing' not found in graph nodes." in errors

def test_validate_switch_node_invalid_targets():
    switch = create_switch_node("switch1", "var", {"case1": "missing1"}, "missing2")
    graph = Graph(nodes={"switch1": switch}, edges=[])
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph
    )
    errors = validate_flow(flow)
    assert len(errors) == 2
    assert "SwitchNode 'switch1' case 'case1' target 'missing1' not found." in errors
    assert "SwitchNode 'switch1' default target 'missing2' not found." in errors

def test_validate_missing_tool():
    agent = create_agent_node("agent1", ["tool1"])
    # Tool pack has no tools
    tp = create_tool_pack("ns", [])
    graph = Graph(nodes={"agent1": agent}, edges=[])
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        tool_packs=[tp]
    )
    errors = validate_flow(flow)
    assert len(errors) == 1
    assert "Agent 'agent1' requires tool 'tool1' but it is not provided by any ToolPack." in errors

def test_validate_governance_sanity():
    agent = create_agent_node("agent1", [])
    graph = Graph(nodes={"agent1": agent}, edges=[])
    gov = Governance(rate_limit_rpm=-1, cost_limit_usd=-5.0)
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=create_metadata(),
        interface=create_interface(),
        blackboard=None,
        graph=graph,
        governance=gov
    )
    errors = validate_flow(flow)
    assert len(errors) == 2
    assert "Governance rate_limit_rpm must be non-negative." in errors
    assert "Governance cost_limit_usd must be non-negative." in errors

def test_validate_linear_flow_valid():
    agent = create_agent_node("agent1", ["tool1"])
    tp = create_tool_pack("ns", ["tool1"])
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        sequence=[agent],
        tool_packs=[tp]
    )
    errors = validate_flow(flow)
    assert errors == []

def test_validate_linear_flow_empty():
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        sequence=[],
    )
    errors = validate_flow(flow)
    assert len(errors) == 1
    assert "LinearFlow sequence must not be empty." in errors

def test_validate_linear_flow_switch_missing_targets():
    # Switch node in linear flow referring to missing nodes (since they are not in sequence)
    switch = create_switch_node("switch1", "var", {"case1": "missing1"}, "missing2")
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=create_metadata(),
        sequence=[switch], # switch is the only node
    )
    errors = validate_flow(flow)
    # Target IDs must be present in the sequence
    assert len(errors) == 2
    assert "SwitchNode 'switch1' case 'case1' target 'missing1' not found." in errors
    assert "SwitchNode 'switch1' default target 'missing2' not found." in errors
