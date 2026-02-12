from coreason_manifest.spec.core.engines import ComputerUseReasoning, StandardReasoning
from coreason_manifest.spec.core.flow import Edge, FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.spec.core.governance import Governance, PolicyConfig
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, HumanNode
from coreason_manifest.utils.gatekeeper import validate_policy


def test_gatekeeper_capability_check() -> None:
    # Setup
    policy = PolicyConfig(
        allowed_capabilities=[],  # No computer_use
        require_human_in_loop_for=[],
        max_risk_score=0.5,
    )
    gov = Governance(policy=policy)

    profile = CognitiveProfile(
        role="worker", persona="you are a worker", reasoning=ComputerUseReasoning(model="gpt-4"), fast_path=None
    )

    node = AgentNode(id="agent1", type="agent", metadata={}, supervision=None, profile=profile, tools=[])

    graph = Graph(nodes={"agent1": node}, edges=[])

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph,
        governance=gov,
    )

    violations = validate_policy(flow)
    assert len(violations) == 1
    assert violations[0].rule == "Capability Check"


def test_gatekeeper_topology_check_unguarded_path() -> None:
    # Setup: Policy requires critical nodes to be guarded
    policy = PolicyConfig(allowed_capabilities=["computer_use"], require_human_in_loop_for=[], max_risk_score=0.5)
    gov = Governance(policy=policy)

    # Critical Node
    critical = AgentNode(
        id="critical",
        type="agent",
        metadata={"risk_level": "critical"},
        supervision=None,
        profile=CognitiveProfile(role="foo", persona="bar", reasoning=StandardReasoning(model="gpt-4"), fast_path=None),
        tools=[],
    )

    human = HumanNode(
        id="human",
        type="human",
        metadata={},
        supervision=None,
        prompt="Confirm?",
        timeout_seconds=60,
        interaction_mode="blocking",
    )

    start = AgentNode(
        id="start",
        type="agent",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="start", persona="s", reasoning=StandardReasoning(model="gpt-4"), fast_path=None),
        tools=[],
    )

    # Graph with TWO paths:
    # 1. start -> human -> critical (SAFE)
    # 2. start -> critical (UNSAFE - The Exploit!)

    graph_exploit = Graph(
        nodes={"critical": critical, "human": human, "start": start},
        edges=[
            Edge(source="start", target="human"),
            Edge(source="human", target="critical"),
            Edge(source="start", target="critical"),  # Bypass!
        ],
    )

    flow_exploit = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph_exploit,
        governance=gov,
    )

    violations = validate_policy(flow_exploit)
    assert len(violations) == 1
    assert violations[0].rule == "Topology Check"
    assert "accessible via unguarded path" in violations[0].message


def test_gatekeeper_topology_check_fully_guarded() -> None:
    # Setup
    policy = PolicyConfig(allowed_capabilities=["computer_use"], require_human_in_loop_for=[], max_risk_score=0.5)
    gov = Governance(policy=policy)

    critical = AgentNode(
        id="critical",
        type="agent",
        metadata={"risk_level": "critical"},
        supervision=None,
        profile=CognitiveProfile(role="foo", persona="bar", reasoning=StandardReasoning(model="gpt-4"), fast_path=None),
        tools=[],
    )

    human = HumanNode(
        id="human",
        type="human",
        metadata={},
        supervision=None,
        prompt="Confirm?",
        timeout_seconds=60,
        interaction_mode="blocking",
    )

    start = AgentNode(
        id="start",
        type="agent",
        metadata={},
        supervision=None,
        profile=CognitiveProfile(role="start", persona="s", reasoning=StandardReasoning(model="gpt-4"), fast_path=None),
        tools=[],
    )

    # Graph with ONE path, fully guarded
    # start -> human -> critical

    graph_safe = Graph(
        nodes={"critical": critical, "human": human, "start": start},
        edges=[
            Edge(source="start", target="human"),
            Edge(source="human", target="critical"),
        ],
    )

    flow_safe = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph_safe,
        governance=gov,
    )

    assert len(validate_policy(flow_safe)) == 0
