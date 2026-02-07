# Copyright (c) 2025 CoReason, Inc.

import pytest
from unittest.mock import patch, MagicMock
from coreason_manifest.runtime.executor import GraphExecutor
from coreason_manifest.spec.v2.recipe import (
    RecipeDefinition,
    RecipeInterface,
    GraphTopology,
    AgentNode,
    HumanNode,
    RouterNode,
    GraphEdge,
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.common.presentation import NodePresentation

# Helper
def create_recipe(nodes, edges, entry_point, name="CoverageTest"):
    # We use model_construct to bypass validation if needed for edge cases
    return RecipeDefinition.model_construct(
        apiVersion="coreason.ai/v2",
        kind="Recipe",
        metadata=ManifestMetadata(name=name),
        interface=RecipeInterface(),
        topology=GraphTopology.model_construct(
            nodes=nodes,
            edges=edges,
            entry_point=entry_point
        )
    )

@pytest.mark.asyncio
async def test_missing_node_runtime_error():
    # Test line 51: Node not found in topology
    # We construct a topology where entry_point points to a non-existent node
    recipe = create_recipe(
        nodes=[],
        edges=[],
        entry_point="phantom"
    )
    executor = GraphExecutor(recipe, {})

    with pytest.raises(ValueError, match="Node phantom not found in topology"):
        await executor.run()

@pytest.mark.asyncio
async def test_resolve_next_invalid_node():
    # Test line 137: _resolve_next with invalid node
    recipe = create_recipe(nodes=[], edges=[], entry_point="start")
    executor = GraphExecutor(recipe, {})

    # Directly call _resolve_next with invalid ID
    result = executor._resolve_next("phantom")
    assert result is None

@pytest.mark.asyncio
async def test_human_input_eof_error():
    # Test lines 102-105: input() raises EOFError
    node = HumanNode(id="H", prompt="Ask", presentation=NodePresentation(x=0, y=0))
    recipe = create_recipe(nodes=[node], edges=[], entry_point="H")

    executor = GraphExecutor(recipe, {})

    with patch("builtins.input", side_effect=EOFError):
        # We need to capture stdout to verify "Mocked Input" print if we want,
        # but mostly we want to ensure it doesn't crash and sets context
        await executor.run()

    assert executor.context.get("response") == "Mocked Input"

@pytest.mark.asyncio
async def test_resolve_next_router_fallback():
    # Test lines 146-149: _resolve_next fallback logic for Router
    # We call _resolve_next WITHOUT a last_step

    node = RouterNode(
        id="R",
        input_key="key",
        routes={"A": "NodeA"},
        default_route="NodeB",
        presentation=NodePresentation(x=0, y=0)
    )
    recipe = create_recipe(nodes=[node], edges=[], entry_point="R")
    executor = GraphExecutor(recipe, {"key": "A"})

    # Call directly
    next_node = executor._resolve_next("R", last_step=None)
    assert next_node == "NodeA"

    # Test default fallback
    executor.context["key"] = "Z"
    next_node = executor._resolve_next("R", last_step=None)
    assert next_node == "NodeB"
