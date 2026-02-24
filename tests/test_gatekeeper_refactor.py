from typing import Any, cast

from coreason_manifest.spec.core.engines import StandardReasoning
from coreason_manifest.spec.core.flow import Edge, FlowInterface, FlowMetadata, Graph, GraphFlow, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, AuthorizationScope, CognitiveProfile, HumanNode
from coreason_manifest.utils.gatekeeper import _is_guarded, validate_policy


def create_agent(node_id: str, tools: list[str] | None = None) -> AgentNode:
    if tools is None:
        tools = []

    # Correctly construct reasoning using the Pydantic model
    reasoning = StandardReasoning(type="standard", model="gpt-4")

    return AgentNode(
        id=node_id,
        type="agent",
        profile=CognitiveProfile(role="Worker", persona="Worker", reasoning=reasoning),
        tools=tools,
    )


def create_human(node_id: str, authorizes: str | None = None) -> HumanNode:
    auth_list = None
    if authorizes:
        auth_list = [AuthorizationScope(target_node_id=authorizes, granted_capabilities="*")]
    return HumanNode(
        id=node_id,
        type="human",
        prompt="Approve?",
        timeout_seconds=300,
        interaction_mode="blocking",
        authorizations=auth_list,
    )


def test_linear_flow_explicit_guarding() -> None:
    agent = create_agent("agent_1")
    human_unguarded = create_human("human_1", authorizes=None)
    human_guarded = create_human("human_2", authorizes="agent_1")
    human_wrong = create_human("human_3", authorizes="agent_2")

    # Case 1: Unguarded
    flow1 = LinearFlow(metadata=FlowMetadata(name="test", version="1"), steps=[human_unguarded, agent])
    assert not _is_guarded(agent, flow1)

    # Case 2: Guarded
    flow2 = LinearFlow(metadata=FlowMetadata(name="test", version="1"), steps=[human_guarded, agent])
    assert _is_guarded(agent, flow2)

    # Case 3: Wrong Guard
    flow3 = LinearFlow(metadata=FlowMetadata(name="test", version="1"), steps=[human_wrong, agent])
    assert not _is_guarded(agent, flow3)


def test_graph_flow_explicit_guarding() -> None:
    agent = create_agent("agent_1")
    start = create_agent("start")

    # Case 1: Simple Path, Unguarded Human
    human_unguarded = create_human("human_1", authorizes=None)
    graph1 = Graph(
        nodes={"start": start, "human_1": human_unguarded, "agent_1": agent},
        edges=[Edge(from_node="start", to_node="human_1"), Edge(from_node="human_1", to_node="agent_1")],
        entry_point="start",
    )
    flow1 = GraphFlow(metadata=FlowMetadata(name="test", version="1"), graph=graph1, interface=FlowInterface())
    assert not _is_guarded(agent, flow1)

    # Case 2: Simple Path, Guarded Human
    human_guarded = create_human("human_2", authorizes="agent_1")
    graph2 = Graph(
        nodes={"start": start, "human_2": human_guarded, "agent_1": agent},
        edges=[Edge(from_node="start", to_node="human_2"), Edge(from_node="human_2", to_node="agent_1")],
        entry_point="start",
    )
    flow2 = GraphFlow(metadata=FlowMetadata(name="test", version="1"), graph=graph2, interface=FlowInterface())
    assert _is_guarded(agent, flow2)

    # Case 3: Multipath, One path unguarded
    # start -> human_guarded -> agent_1 (Guarded path)
    # start -> direct -> agent_1 (Unguarded path)
    direct = create_agent("direct")
    graph3 = Graph(
        nodes={"start": start, "human_2": human_guarded, "agent_1": agent, "direct": direct},
        edges=[
            Edge(from_node="start", to_node="human_2"),
            Edge(from_node="human_2", to_node="agent_1"),
            Edge(from_node="start", to_node="direct"),
            Edge(from_node="direct", to_node="agent_1"),
        ],
        entry_point="start",
    )
    flow3 = GraphFlow(metadata=FlowMetadata(name="test", version="1"), graph=graph3, interface=FlowInterface())
    assert not _is_guarded(agent, flow3)  # Should be FALSE because one path is unguarded


def test_validate_policy_auto_remediation() -> None:
    # Test that auto-remediation inserts a HumanNode with correct authorization
    agent = create_agent("agent_crit", tools=["code_execution"])

    flow = LinearFlow(metadata=FlowMetadata(name="test", version="1"), steps=[agent])

    reports = validate_policy(flow)
    assert len(reports) == 1
    report = reports[0]
    assert report.code == "ERR_SEC_UNGUARDED_CRITICAL_003"

    # Check remediation patch
    remediation = report.remediation
    assert remediation is not None
    assert remediation.type == "add_guard_node"

    patch_data = remediation.patch_data
    assert patch_data is not None
    assert isinstance(patch_data, list)

    # Verify the inserted node has authorizations
    # patch_data is a list of ops. For LinearFlow, it's an 'add' op.
    add_op = patch_data[0]
    # Use cast to help mypy know this dict has string keys
    inserted_node = cast("dict[str, Any]", add_op["value"])

    assert inserted_node["type"] == "human"
    auths = inserted_node["authorizations"]
    assert len(auths) == 1
    assert auths[0]["target_node_id"] == "agent_crit"


def test_validate_policy_auto_remediation_graph() -> None:
    # Test that auto-remediation inserts a HumanNode with correct authorization in GraphFlow
    agent = create_agent("agent_crit", tools=["code_execution"])
    start = create_agent("start")

    graph = Graph(
        nodes={"start": start, "agent_crit": agent},
        edges=[Edge(from_node="start", to_node="agent_crit")],
        entry_point="start",
    )

    flow = GraphFlow(metadata=FlowMetadata(name="test", version="1"), graph=graph, interface=FlowInterface())

    reports = validate_policy(flow)
    assert len(reports) == 1
    report = reports[0]

    remediation = report.remediation
    assert remediation is not None

    patch_data = remediation.patch_data
    assert patch_data is not None
    assert isinstance(patch_data, list)

    # Find the 'add' op for the node
    add_node_op = next(op for op in patch_data if op["op"] == "add" and "nodes" in str(op["path"]))
    inserted_node = cast("dict[str, Any]", add_node_op["value"])

    assert inserted_node["type"] == "human"
    auths = inserted_node["authorizations"]
    assert len(auths) == 1
    assert auths[0]["target_node_id"] == "agent_crit"
