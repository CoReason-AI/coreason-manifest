from typing import TYPE_CHECKING, cast

import pytest

from coreason_manifest.builder import AgentBuilder, NewGraphFlow

if TYPE_CHECKING:
    from collections.abc import Sequence
from coreason_manifest.spec.core.contracts import AtomicSkill
from coreason_manifest.spec.core.engines import DecompositionReasoning
from coreason_manifest.spec.core.flow import Graph
from coreason_manifest.spec.core.nodes import AgentNode, PlannerNode
from coreason_manifest.spec.interop.exceptions import ManifestError


def test_decomposition_reasoning_creates_immutable_nodes() -> None:
    engine = DecompositionReasoning(model="gpt-4")

    constraints: Sequence[str | AtomicSkill] = [AtomicSkill(id="step_a", description="Step A", immutable=True)]

    plan = engine.decompose("Step A", _context={}, constraints=constraints)

    assert isinstance(plan, AtomicSkill)
    assert plan.id == "step_a"
    assert plan.immutable is True


def test_decomposition_reasoning_linear_strategy() -> None:
    engine = DecompositionReasoning(model="gpt-4")
    goal = "Test Goal"
    plan = engine.decompose(goal, _context={}, strategy="linear")

    assert isinstance(plan, list)
    assert len(plan) == 3
    # Mypy cannot infer list content type easily here due to union return type
    step1 = plan[0]
    assert isinstance(step1, dict)
    assert step1["id"] == "step_1"
    assert "Analyze: Test Goal" in cast("str", step1["description"])


def test_decomposition_recursion_depth_limit() -> None:
    engine = DecompositionReasoning(model="gpt-4")
    goal = "Complex Goal"

    plan = engine.decompose(goal, _context={})

    # Verify structure: list of lists ... until AtomicSkill
    assert isinstance(plan, list)
    # Check one branch
    level1 = plan[0]
    assert isinstance(level1, list)
    level2 = level1[0]
    assert isinstance(level2, list)
    level3 = level2[0]
    assert isinstance(level3, AtomicSkill)
    assert "atomic" in level3.id


def test_planner_process_respects_constraints() -> None:
    planner = PlannerNode(
        id="planner_1",
        goal="Execute Task",
        output_schema={"type": "object", "properties": {"steps": {"type": "array"}}},
    )

    constraints: Sequence[str | AtomicSkill] = [
        AtomicSkill(
            id="fixed_task",
            description="Execute Task",
            immutable=True,
        )
    ]

    result = planner.process(input_payload={}, context={}, constraints=constraints)

    nodes = result["nodes"]
    edges = result["edges"]
    assert len(nodes) == 1
    assert nodes[0]["id"] == "fixed_task"
    assert nodes[0]["locked"] is True
    # One node means zero edges in a linear sequence
    assert len(edges) == 0


def test_planner_process_generates_edges() -> None:
    planner = PlannerNode(id="planner_edges", goal="Two Step Task", output_schema={})

    # Force a mock plan with 2 steps for testing edges
    # We can't easily force the engine to return exactly 2 steps without complex mocking,
    # so we'll test _compile_to_graph directly.
    plan = [
        AtomicSkill(id="step_1", description="1"),
        AtomicSkill(id="step_2", description="2"),
        AtomicSkill(id="step_3", description="3"),
    ]

    result = planner._compile_to_graph(plan)
    nodes = result["nodes"]
    edges = result["edges"]

    assert len(nodes) == 3
    assert len(edges) == 2
    assert edges[0]["from"] == "step_1"
    assert edges[0]["to"] == "step_2"
    assert edges[1]["from"] == "step_2"
    assert edges[1]["to"] == "step_3"


def test_planner_process_extracts_constraints_from_input() -> None:
    planner = PlannerNode(
        id="planner_2",
        goal="Execute Task",
        output_schema={"type": "object", "properties": {"steps": {"type": "array"}}},
    )

    constraints = [AtomicSkill(id="dynamic_fixed", description="Execute Task", immutable=True)]
    input_payload = {"constraints": constraints}

    result = planner.process(input_payload=input_payload, context={})

    nodes = result["nodes"]
    assert len(nodes) == 1
    assert nodes[0]["id"] == "dynamic_fixed"
    assert nodes[0]["locked"] is True


def test_graph_flow_governance_prevents_mutation() -> None:
    graph = Graph(nodes={}, edges=[])

    # Manually lock a node via private API for testing
    graph._locked_nodes.add("critical_step")

    with pytest.raises(ManifestError) as exc:
        graph.inject_subgraph("critical_step", {"nodes": []})

    assert "Cannot mutate immutable step: critical_step" in str(exc.value)


def test_graph_isolation() -> None:
    graph1 = Graph(nodes={}, edges=[])
    graph2 = Graph(nodes={}, edges=[])

    graph1._locked_nodes.add("node_1")

    assert "node_1" in graph1._locked_nodes
    assert "node_1" not in graph2._locked_nodes


def test_builder_locks_static_nodes() -> None:
    flow_builder = NewGraphFlow("static_flow", "1.0.0", "A flow with fixed recipes")

    agent = AgentBuilder("fixed_agent").with_identity("worker", "You work hard").build()

    flow_builder.add_agent(agent)

    built_flow = flow_builder.build()

    assert "fixed_agent" in built_flow.graph._locked_nodes


def test_agent_node_has_immutable_flag() -> None:
    agent = AgentBuilder("test_agent").with_identity("bot", "helper").build()
    assert hasattr(agent, "immutable")
    assert agent.immutable is False

    agent_imm = AgentNode(id="imm", type="agent", profile="prof", immutable=True)
    assert agent_imm.immutable is True
