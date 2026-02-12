from coreason_manifest.spec.core.engines import (
    Optimizer,
    Reflex,
    StandardReasoning,
    Supervision,
    TreeSearchReasoning,
)
from coreason_manifest.spec.core.flow import (
    Blackboard,
    Edge,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
    VariableDef,
)
from coreason_manifest.spec.core.nodes import (
    AgentNode,
    Brain,
    HumanNode,
    Placeholder,
    PlannerNode,
    SwitchNode,
)


def test_core_kernel_instantiation() -> None:
    # Test Engines
    reasoning = StandardReasoning(model="gpt-4", thoughts_max=5, min_confidence=0.8)
    reflex = Reflex(model="gpt-3.5", timeout_ms=1000, caching=True)
    supervision = Supervision(strategy="restart", max_retries=3, fallback=None)
    optimizer = Optimizer(teacher_model="gpt-4", metric="accuracy", max_demonstrations=3)

    # Test Nodes
    brain = Brain(role="assistant", persona="helpful", reasoning=reasoning, reflex=reflex)
    agent_node = AgentNode(
        id="agent-1",
        metadata={"foo": "bar", "priority": 1},
        supervision=supervision,
        brain=brain,
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
    placeholder = Placeholder(
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
    )
    graph_flow = GraphFlow(
        kind="GraphFlow",
        metadata=metadata,
        interface=interface,
        blackboard=blackboard,
        graph=graph,
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
    brain = Brain(role="solver", persona="math", reasoning=lats_reasoning, reflex=None)
    agent = AgentNode(id="agent-lats", metadata={}, supervision=None, type="agent", brain=brain, tools=[])

    # Validate JSON serialization/deserialization for LATS
    agent_json = agent.model_dump_json()
    agent_loaded = AgentNode.model_validate_json(agent_json)

    assert isinstance(agent_loaded.brain, Brain)
    assert isinstance(agent_loaded.brain.reasoning, TreeSearchReasoning)
    assert agent_loaded.brain.reasoning.type == "tree_search"
    assert agent_loaded.brain.reasoning.depth == 5
