import pytest
from coreason_manifest.spec.core.engines import ReasoningEngine, Reflex, Supervision, Optimizer
from coreason_manifest.spec.core.nodes import AgentBrain, AgentNode, SwitchNode, PlannerNode, HumanNode, Placeholder, Node
from coreason_manifest.spec.core.flow import LinearFlow, GraphFlow, Step, Graph, FlowMetadata, FlowInterface, Blackboard

def test_engines_instantiation():
    r = ReasoningEngine()
    assert r.model_dump() == {}

    s = Supervision()
    assert s.model_dump() == {}

def test_nodes_instantiation():
    brain = AgentBrain(role="test_role")
    assert brain.role == "test_role"

    agent_node = AgentNode(id="node1", brain=brain)
    assert agent_node.id == "node1"
    assert agent_node.brain.role == "test_role"

    switch_node = SwitchNode(id="node2", variable="var", cases={"a": "node3"}, default="node4")
    assert switch_node.cases["a"] == "node3"
    assert switch_node.variable == "var"

def test_planner_node_instantiation():
    optimizer = Optimizer()
    planner = PlannerNode(id="plan1", goal="solve world hunger", optimizer=optimizer)
    assert planner.goal == "solve world hunger"

def test_human_node_instantiation():
    human = HumanNode(id="human1", prompt="Confirm?")
    assert human.prompt == "Confirm?"

def test_placeholder_instantiation():
    # Placeholder is ManifestBaseModel, not Node (doesn't have id/metadata/supervision)
    ph = Placeholder(ref="some_agent_ref")
    assert ph.ref == "some_agent_ref"

def test_flow_instantiation():
    meta = FlowMetadata(name="test", version="1.0")
    interface = FlowInterface(inputs={}, outputs={})

    step = Step(node=AgentNode(id="n1", brain=AgentBrain(role="r1")))

    flow = LinearFlow(kind="LinearFlow", metadata=meta, interface=interface, sequence=[step])
    assert flow.kind == "LinearFlow"
    assert len(flow.sequence) == 1
    assert flow.sequence[0].node.id == "n1"

def test_graph_flow_instantiation():
    meta = FlowMetadata(name="test_graph", version="1.0")
    interface = FlowInterface(inputs={}, outputs={})

    nodes = [AgentNode(id="n1", brain=AgentBrain(role="r1"))]
    edges = [{"from": "n1", "to": "n2"}]
    graph = Graph(nodes=nodes, edges=edges)

    flow = GraphFlow(kind="GraphFlow", metadata=meta, interface=interface, graph=graph)
    assert flow.kind == "GraphFlow"
    assert len(flow.graph.nodes) == 1
    assert flow.graph.edges[0]["from"] == "n1"
