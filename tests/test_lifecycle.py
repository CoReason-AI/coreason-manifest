# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphEdge,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
    RecipeStatus,
    SemanticRef,
)


def test_draft_recipe_with_semantic_ref() -> None:
    """Test that a DRAFT recipe allows SemanticRef."""
    semantic_node = AgentNode(
        id="planner",
        agent_ref=SemanticRef(intent="Plan the trip"),
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Draft Recipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(nodes=[semantic_node], edges=[], entry_point="planner", status="draft"),
        status=RecipeStatus.DRAFT,
    )

    assert recipe.status == RecipeStatus.DRAFT
    assert isinstance(recipe.topology.nodes[0], AgentNode)
    assert isinstance(recipe.topology.nodes[0].agent_ref, SemanticRef)


def test_published_recipe_with_semantic_ref_fails() -> None:
    """Test that a PUBLISHED recipe raises ValidationError if SemanticRef is present."""
    semantic_node = AgentNode(
        id="planner",
        agent_ref=SemanticRef(intent="Plan the trip"),
    )

    with pytest.raises(ValidationError) as exc:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Published Recipe"),
            interface=RecipeInterface(),
            topology=GraphTopology(nodes=[semantic_node], edges=[], entry_point="planner", status="valid"),
            status=RecipeStatus.PUBLISHED,
        )

    assert "Resolve all SemanticRefs to concrete IDs" in str(exc.value)


def test_published_recipe_with_broken_topology_fails() -> None:
    """Test that a PUBLISHED recipe raises ValidationError if topology is incomplete."""
    # Dangling edge scenario
    node1 = AgentNode(id="start", agent_ref="agent-1")

    # We pass status="draft" to GraphTopology so it skips its own validation,
    # allowing us to test that RecipeDefinition catches it when status=PUBLISHED.

    with pytest.raises(ValidationError) as exc:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Broken Recipe"),
            interface=RecipeInterface(),
            topology=GraphTopology(
                nodes=[node1], edges=[GraphEdge(source="start", target="missing")], entry_point="start", status="draft"
            ),
            status=RecipeStatus.PUBLISHED,
        )

    assert "Topology is structurally invalid" in str(exc.value)


def test_published_recipe_valid() -> None:
    """Test that a valid PUBLISHED recipe passes validation."""
    node1 = AgentNode(id="start", agent_ref="agent-1")
    node2 = AgentNode(id="end", agent_ref="agent-2")

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Valid Recipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=[node1, node2], edges=[GraphEdge(source="start", target="end")], entry_point="start", status="valid"
        ),
        status=RecipeStatus.PUBLISHED,
    )

    assert recipe.status == RecipeStatus.PUBLISHED


def test_draft_recipe_with_broken_topology_passes() -> None:
    """Test that a DRAFT recipe allows broken topology."""
    node1 = AgentNode(id="start", agent_ref="agent-1")

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Broken Draft"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=[node1], edges=[GraphEdge(source="start", target="missing")], entry_point="start", status="draft"
        ),
        status=RecipeStatus.DRAFT,
    )

    assert recipe.status == RecipeStatus.DRAFT
