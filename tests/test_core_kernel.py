from coreason_manifest.spec.core.engines import (
    FastPath,
    Optimizer,
    StandardReasoning,
    TreeSearchReasoning,
)
from coreason_manifest.spec.core.flow import (
    Blackboard,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
    VariableDef,
)
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    CognitiveProfile,
    HumanNode,
    PlaceholderNode,
    PlannerNode,
    SwitchNode,
)
from coreason_manifest.spec.core.resilience import (
    RetryStrategy,
    SupervisionPolicy,
)
from coreason_manifest.spec.core.tools import ToolPack


def test_core_kernel_instantiation() -> None:
    # Test Engines
    reasoning = StandardReasoning(model="gpt-4", thoughts_max=5, min_confidence=0.8)
    reflex = FastPath(model="gpt-3.5", timeout_ms=1000, caching=True)

    supervision = SupervisionPolicy(handlers=[], default_strategy=RetryStrategy(max_attempts=3))

    optimizer = Optimizer(teacher_model="gpt-4", metric="accuracy", max_demonstrations=3)

    # Test Nodes
    brain = CognitiveProfile(role="assistant", persona="helpful", reasoning=reasoning, fast_path=reflex)
    agent_node = AgentNode(
        id="agent-1",
        metadata={"foo": "bar", "priority": 1},
        supervision=supervision,
        profile=brain,
        tools=["search"],
        type="agent",
    )
    switch_node = SwitchNode(
        id="switch-1",
        metadata={},
        supervision=None,
        variable="user_choice",
        cases={"x > 1": "node-2"},
        default="node-3",
        type="switch",
    )
    planner_node = PlannerNode(
        id="planner-1",
        metadata={},
        supervision=None,
        goal="solve problem",
        optimizer=optimizer,
        type="planner",
        output_schema={"type": "object", "properties": {"plan": {"type": "string"}}},
    )
    human_node = HumanNode(
        id="human-1",
        metadata={},
        supervision=None,
        prompt="Please approve",
        timeout_seconds=60,
        type="human",
    )
    placeholder = PlaceholderNode(
        id="place-1",
        metadata={},
        supervision=None,
        required_capabilities=["email"],
        type="placeholder",
    )

    # Test Flow
    metadata = FlowMetadata(name="test-flow", version="1.0", description="test", tags=["test"])
    interface = FlowInterface(inputs={"q": {"type": "string"}}, outputs={"a": {"type": "string"}})
    variable_def = VariableDef(type="string", description="User context")
    blackboard = Blackboard(variables={"context": variable_def}, persistence=False)

    # Define ToolPack for integrity
    tool_pack = ToolPack(kind="ToolPack", namespace="core", tools=["search"], dependencies=[], env_vars=[])
    definitions = FlowDefinitions(tool_packs={"core": tool_pack})

    edge = Edge(source="agent-1", target="switch-1")
    graph = Graph(
        nodes={
            "agent-1": agent_node,
            "switch-1": switch_node,
            "planner-1": planner_node,
            "human-1": human_node,
            "place-1": placeholder,
        },
        edges=[edge],
    )

    linear_flow = LinearFlow(
        kind="LinearFlow",
        metadata=metadata,
        sequence=[agent_node, switch_node, planner_node, human_node, placeholder],
        definitions=definitions,
    )
    graph_flow = GraphFlow(
        kind="GraphFlow",
        metadata=metadata,
        interface=interface,
        blackboard=blackboard,
        graph=graph,
        definitions=definitions,
    )

    # Test Serialization / Deserialization Polymorphism
    graph_json = graph_flow.model_dump_json()
    graph_loaded = GraphFlow.model_validate_json(graph_json)
    assert isinstance(graph_loaded.graph.nodes["agent-1"], AgentNode)
    assert isinstance(graph_loaded.graph.nodes["switch-1"], SwitchNode)
    assert isinstance(graph_loaded.graph.nodes["planner-1"], PlannerNode)

    linear_json = linear_flow.model_dump_json()
    linear_loaded = LinearFlow.model_validate_json(linear_json)
    assert isinstance(linear_loaded.sequence[0], AgentNode)
    assert isinstance(linear_loaded.sequence[1], SwitchNode)
    assert isinstance(linear_loaded.sequence[2], PlannerNode)


def test_polymorphic_reasoning() -> None:
    # Test TreeSearchReasoning
    lats_reasoning = TreeSearchReasoning(
        model="gpt-4", depth=5, branching_factor=4, simulations=10, exploration_weight=1.5
    )
    brain = CognitiveProfile(role="solver", persona="math", reasoning=lats_reasoning, fast_path=None)
    agent = AgentNode(id="agent-lats", metadata={}, supervision=None, type="agent", profile=brain, tools=[])

    # Validate JSON serialization/deserialization for LATS
    agent_json = agent.model_dump_json()
    agent_loaded = AgentNode.model_validate_json(agent_json)

    assert isinstance(agent_loaded.profile, CognitiveProfile)
    assert isinstance(agent_loaded.profile.reasoning, TreeSearchReasoning)
    assert agent_loaded.profile.reasoning.type == "tree_search"
    assert agent_loaded.profile.reasoning.depth == 5
