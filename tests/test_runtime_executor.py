# Copyright (c) 2025 CoReason, Inc.

from unittest.mock import patch

import pytest

from coreason_manifest.runtime.executor import GraphExecutor
from coreason_manifest.spec.common.presentation import NodePresentation
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphEdge,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RecipeInterface,
    RecipeNode,
    RouterNode,
)


# Helper to create recipe
def create_recipe(
    nodes: list[RecipeNode], edges: list[GraphEdge], entry_point: str, name: str = "TestRecipe"
) -> RecipeDefinition:
    return RecipeDefinition(
        metadata=ManifestMetadata(name=name),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=nodes, edges=edges, entry_point=entry_point),
    )


@pytest.mark.asyncio
async def test_branching_workflow() -> None:
    # Define Nodes
    node_a = HumanNode(id="A", prompt="Go Left or Right?", presentation=NodePresentation(x=0, y=0))
    node_b = RouterNode(
        id="B",
        input_key="response",
        routes={"Left": "C", "Right": "D"},
        default_route="D",
        presentation=NodePresentation(x=0, y=0),
    )
    node_c = AgentNode(
        id="C", agent_ref="agent_left", inputs_map={"input": "response"}, presentation=NodePresentation(x=0, y=0)
    )
    node_d = AgentNode(
        id="D", agent_ref="agent_right", inputs_map={"input": "response"}, presentation=NodePresentation(x=0, y=0)
    )

    # Define Edges
    # Edge A -> B
    edges = [
        GraphEdge(source="A", target="B"),
    ]

    recipe = create_recipe(nodes=[node_a, node_b, node_c, node_d], edges=edges, entry_point="A")

    # Mock input for HumanNode
    with patch("builtins.input", return_value="Left"):
        executor = GraphExecutor(recipe, {})
        trace = await executor.run()

    # Verify Trace
    node_ids = [step.node_id for step in trace.steps]
    assert node_ids == ["A", "B", "C"]
    assert "D" not in node_ids

    # Verify State
    # Node C output: {"output": "Mocked output from agent_left"}
    assert executor.context.get("output") == "Mocked output from agent_left"
    assert executor.context.get("response") == "Left"


@pytest.mark.asyncio
async def test_infinite_loop_protection() -> None:
    # Node A -> Node B -> Node A
    node_a = AgentNode(id="A", agent_ref="agent_a", presentation=NodePresentation(x=0, y=0))
    node_b = AgentNode(id="B", agent_ref="agent_b", presentation=NodePresentation(x=0, y=0))

    edges = [GraphEdge(source="A", target="B"), GraphEdge(source="B", target="A")]

    recipe = create_recipe(nodes=[node_a, node_b], edges=edges, entry_point="A")

    executor = GraphExecutor(recipe, {})
    executor.max_steps = 5  # Set low limit

    trace = await executor.run()

    assert len(trace.steps) == 5
    # Should be A, B, A, B, A
    expected_ids = ["A", "B", "A", "B", "A"]
    assert [step.node_id for step in trace.steps] == expected_ids


@pytest.mark.asyncio
async def test_router_missing_key_fallback() -> None:
    # Router needs key "choice", but it's not in context. Should go to default.
    node_a = RouterNode(
        id="A", input_key="choice", routes={"yes": "B"}, default_route="C", presentation=NodePresentation(x=0, y=0)
    )
    node_b = AgentNode(id="B", agent_ref="agent_yes", presentation=NodePresentation(x=0, y=0))
    node_c = AgentNode(id="C", agent_ref="agent_default", presentation=NodePresentation(x=0, y=0))

    recipe = create_recipe(nodes=[node_a, node_b, node_c], edges=[], entry_point="A")

    executor = GraphExecutor(recipe, initial_state={})  # Empty state
    trace = await executor.run()

    node_ids = [step.node_id for step in trace.steps]
    assert node_ids == ["A", "C"]
    assert "B" not in node_ids


@pytest.mark.asyncio
async def test_router_no_match_fallback() -> None:
    # Router has key, but value doesn't match routes.
    node_a = RouterNode(
        id="A", input_key="choice", routes={"yes": "B"}, default_route="C", presentation=NodePresentation(x=0, y=0)
    )
    node_b = AgentNode(id="B", agent_ref="agent_yes", presentation=NodePresentation(x=0, y=0))
    node_c = AgentNode(id="C", agent_ref="agent_default", presentation=NodePresentation(x=0, y=0))

    recipe = create_recipe(nodes=[node_a, node_b, node_c], edges=[], entry_point="A")

    executor = GraphExecutor(recipe, initial_state={"choice": "maybe"})
    trace = await executor.run()

    node_ids = [step.node_id for step in trace.steps]
    assert node_ids == ["A", "C"]


@pytest.mark.asyncio
async def test_diamond_workflow() -> None:
    # A (Router) -> B or C -> D
    # "Split and Merge"
    # We will test path A -> B -> D

    node_a = RouterNode(
        id="A",
        input_key="path",
        routes={"upper": "B", "lower": "C"},
        default_route="C",
        presentation=NodePresentation(x=0, y=0),
    )
    node_b = AgentNode(id="B", agent_ref="agent_b", presentation=NodePresentation(x=0, y=0))
    node_c = AgentNode(id="C", agent_ref="agent_c", presentation=NodePresentation(x=0, y=0))
    node_d = AgentNode(id="D", agent_ref="agent_d", presentation=NodePresentation(x=0, y=0))

    edges = [GraphEdge(source="B", target="D"), GraphEdge(source="C", target="D")]

    recipe = create_recipe(nodes=[node_a, node_b, node_c, node_d], edges=edges, entry_point="A")

    executor = GraphExecutor(recipe, initial_state={"path": "upper"})
    trace = await executor.run()

    node_ids = [step.node_id for step in trace.steps]
    assert node_ids == ["A", "B", "D"]


@pytest.mark.asyncio
async def test_ping_pong_loop() -> None:
    # Complex Case: Interaction Loop
    # A (Agent) -> B (Agent) -> C (Router: continue?) -> A or End

    # We need to simulate changing state to break the loop.
    # Since we use a simple loop, we can't easily change the mock output dynamically
    # unless we subclass or mock side effects.
    # For now, we will let it hit max_steps or use a slightly smarter mock.

    # Let's use max_steps to break it, but ensure sequence is A-B-C-A-B-C...

    node_a = AgentNode(id="A", agent_ref="ping", presentation=NodePresentation(x=0, y=0))
    node_b = AgentNode(id="B", agent_ref="pong", presentation=NodePresentation(x=0, y=0))
    node_c = RouterNode(
        id="C",
        input_key="counter",
        routes={"stop": "D"},
        default_route="A",  # Loop back to A
        presentation=NodePresentation(x=0, y=0),
    )
    node_d = AgentNode(id="D", agent_ref="end", presentation=NodePresentation(x=0, y=0))

    edges = [
        GraphEdge(source="A", target="B"),
        GraphEdge(source="B", target="C"),
    ]

    recipe = create_recipe(nodes=[node_a, node_b, node_c, node_d], edges=edges, entry_point="A")

    executor = GraphExecutor(recipe, initial_state={"counter": "go"})
    executor.max_steps = 7  # A, B, C, A, B, C, A

    trace = await executor.run()

    ids = [step.node_id for step in trace.steps]
    assert ids == ["A", "B", "C", "A", "B", "C", "A"]
