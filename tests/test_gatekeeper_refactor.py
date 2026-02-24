
import pytest
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode, CognitiveProfile
from coreason_manifest.spec.core.flow import LinearFlow, GraphFlow, Graph, Edge, FlowMetadata, FlowInterface
from coreason_manifest.utils.gatekeeper import _is_guarded, validate_policy
from coreason_manifest.spec.core.flow import FlowDefinitions as Definitions

def create_agent(id: str, tools: list[str] = []) -> AgentNode:
    return AgentNode(
        id=id,
        type="agent",
        profile=CognitiveProfile(
            role="Worker",
            persona="Worker",
            reasoning={"type": "standard", "model": "gpt-4"}
        ),
        tools=tools
    )

def create_human(id: str, authorizes: str | None = None) -> HumanNode:
    return HumanNode(
        id=id,
        type="human",
        prompt="Approve?",
        timeout_seconds=300,
        interaction_mode="blocking",
        authorizes_node_id=authorizes
    )

def test_linear_flow_explicit_guarding():
    agent = create_agent("agent_1")
    human_unguarded = create_human("human_1", authorizes=None)
    human_guarded = create_human("human_2", authorizes="agent_1")
    human_wrong = create_human("human_3", authorizes="agent_2")

    # Case 1: Unguarded
    flow1 = LinearFlow(
        metadata=FlowMetadata(name="test", version="1"),
        steps=[human_unguarded, agent]
    )
    assert not _is_guarded(agent, flow1)

    # Case 2: Guarded
    flow2 = LinearFlow(
        metadata=FlowMetadata(name="test", version="1"),
        steps=[human_guarded, agent]
    )
    assert _is_guarded(agent, flow2)

    # Case 3: Wrong Guard
    flow3 = LinearFlow(
        metadata=FlowMetadata(name="test", version="1"),
        steps=[human_wrong, agent]
    )
    assert not _is_guarded(agent, flow3)

def test_graph_flow_explicit_guarding():
    agent = create_agent("agent_1")
    start = create_agent("start")

    # Case 1: Simple Path, Unguarded Human
    human_unguarded = create_human("human_1", authorizes=None)
    graph1 = Graph(
        nodes={"start": start, "human_1": human_unguarded, "agent_1": agent},
        edges=[
            Edge(from_node="start", to_node="human_1"),
            Edge(from_node="human_1", to_node="agent_1")
        ],
        entry_point="start"
    )
    flow1 = GraphFlow(
        metadata=FlowMetadata(name="test", version="1"),
        graph=graph1,
        interface=FlowInterface()
    )
    assert not _is_guarded(agent, flow1)

    # Case 2: Simple Path, Guarded Human
    human_guarded = create_human("human_2", authorizes="agent_1")
    graph2 = Graph(
        nodes={"start": start, "human_2": human_guarded, "agent_1": agent},
        edges=[
            Edge(from_node="start", to_node="human_2"),
            Edge(from_node="human_2", to_node="agent_1")
        ],
        entry_point="start"
    )
    flow2 = GraphFlow(
        metadata=FlowMetadata(name="test", version="1"),
        graph=graph2,
        interface=FlowInterface()
    )
    assert _is_guarded(agent, flow2)

    # Case 3: Multipath, One path unguarded
    # start -> human_guarded -> agent_1 (Guarded path)
    # start -> direct -> agent_1 (Unguarded path)
    direct = create_agent("direct")
    graph3 = Graph(
        nodes={
            "start": start,
            "human_2": human_guarded,
            "agent_1": agent,
            "direct": direct
        },
        edges=[
            Edge(from_node="start", to_node="human_2"),
            Edge(from_node="human_2", to_node="agent_1"),
            Edge(from_node="start", to_node="direct"),
            Edge(from_node="direct", to_node="agent_1")
        ],
        entry_point="start"
    )
    flow3 = GraphFlow(
        metadata=FlowMetadata(name="test", version="1"),
        graph=graph3,
        interface=FlowInterface()
    )
    assert not _is_guarded(agent, flow3) # Should be FALSE because one path is unguarded

def test_validate_policy_auto_remediation():
    # Test that auto-remediation inserts a HumanNode with correct authorization
    agent = create_agent("agent_crit", tools=["code_execution"])

    flow = LinearFlow(
        metadata=FlowMetadata(name="test", version="1"),
        steps=[agent]
    )

    reports = validate_policy(flow)
    assert len(reports) == 1
    report = reports[0]
    assert report.code == "ERR_SEC_UNGUARDED_CRITICAL_003"

    # Check remediation patch
    remediation = report.remediation
    assert remediation.type == "add_guard_node"
    patch_data = remediation.patch_data

    # Verify the inserted node has authorizes_node_id
    # patch_data is a list of ops. For LinearFlow, it's an 'add' op.
    add_op = patch_data[0]
    inserted_node = add_op["value"]

    assert inserted_node["type"] == "human"
    assert inserted_node["authorizes_node_id"] == "agent_crit"

def test_validate_policy_auto_remediation_graph():
    # Test that auto-remediation inserts a HumanNode with correct authorization in GraphFlow
    agent = create_agent("agent_crit", tools=["code_execution"])
    start = create_agent("start")

    graph = Graph(
        nodes={"start": start, "agent_crit": agent},
        edges=[Edge(from_node="start", to_node="agent_crit")],
        entry_point="start"
    )

    flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1"),
        graph=graph,
        interface=FlowInterface()
    )

    reports = validate_policy(flow)
    assert len(reports) == 1
    report = reports[0]

    remediation = report.remediation
    patch_data = remediation.patch_data

    # Find the 'add' op for the node
    add_node_op = next(op for op in patch_data if op["op"] == "add" and "nodes" in op["path"])
    inserted_node = add_node_op["value"]

    assert inserted_node["type"] == "human"
    assert inserted_node["authorizes_node_id"] == "agent_crit"
