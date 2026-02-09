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
    GraphTopology,
    OptimizationIntent,
    RecipeDefinition,
    RecipeInterface,
    RecipeRecommendation,
    RecipeStatus,
    SemanticRef,
)


def test_legacy_compatibility_string_ref() -> None:
    """Test that an AgentNode initialized with a string ID is valid."""
    node = AgentNode(id="agent-1", agent_ref="legacy-agent-id")
    assert node.agent_ref == "legacy-agent-id"
    assert isinstance(node.agent_ref, str)


def test_rich_structure_semantic_ref() -> None:
    """Test that a SemanticRef persists candidates and optimization data correctly."""
    recommendation = RecipeRecommendation(ref="rec-1", score=0.95, rationale="Best match", warnings=[])
    optimization = OptimizationIntent(base_ref="base-agent", improvement_goal="Make it faster", strategy="parallel")
    semantic_ref = SemanticRef(
        intent="Analyze data", constraints=["accuracy > 0.9"], candidates=[recommendation], optimization=optimization
    )

    assert semantic_ref.intent == "Analyze data"
    assert semantic_ref.constraints == ["accuracy > 0.9"]
    assert len(semantic_ref.candidates) == 1
    assert semantic_ref.candidates[0].ref == "rec-1"
    assert semantic_ref.optimization is not None
    assert semantic_ref.optimization.base_ref == "base-agent"


def test_draft_mode_allows_semantic_ref() -> None:
    """Test that a Recipe with status='draft' allows SemanticRefs."""
    semantic_ref = SemanticRef(intent="Placeholder")

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Draft Recipe"),
        interface=RecipeInterface(),
        status=RecipeStatus.DRAFT,
        topology=GraphTopology(
            nodes=[
                AgentNode(id="start", agent_ref=semantic_ref),
            ],
            edges=[],
            entry_point="start",
            status="draft",  # Allow disconnected graph
        ),
    )

    assert recipe.status == RecipeStatus.DRAFT
    assert isinstance(recipe.topology.nodes[0], AgentNode)
    assert isinstance(recipe.topology.nodes[0].agent_ref, SemanticRef)


def test_publishing_block_semantic_ref() -> None:
    """Test that a Recipe with status='published' RAISES ValidationError if it contains a SemanticRef."""
    semantic_ref = SemanticRef(intent="Placeholder")

    with pytest.raises(ValidationError) as excinfo:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Published Recipe"),
            interface=RecipeInterface(),
            status=RecipeStatus.PUBLISHED,
            topology=GraphTopology(
                nodes=[
                    AgentNode(id="start", agent_ref=semantic_ref),
                ],
                edges=[],
                entry_point="start",
                status="draft",  # Even if topology is valid (or draft), SemanticRef should block
            ),
        )

    # Check for specific error message about abstract nodes
    assert "Lifecycle Error" in str(excinfo.value)
    assert "start" in str(excinfo.value)
    assert "still abstract" in str(excinfo.value)


def test_publishing_success() -> None:
    """Test that a Recipe with status='published' passes if all nodes use concrete string IDs and graph is connected."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Published Recipe"),
        interface=RecipeInterface(),
        status=RecipeStatus.PUBLISHED,
        topology=GraphTopology(
            nodes=[
                AgentNode(id="start", agent_ref="concrete-agent-id"),
                AgentNode(id="end", agent_ref="concrete-agent-id-2"),
            ],
            edges=[{"source": "start", "target": "end"}],
            entry_point="start",
            status="valid",
        ),
    )

    assert recipe.status == RecipeStatus.PUBLISHED
    assert isinstance(recipe.topology.nodes[0], AgentNode)
    assert isinstance(recipe.topology.nodes[0].agent_ref, str)


def test_publishing_block_invalid_topology() -> None:
    """Test that a Recipe with status='published' RAISES ValidationError if graph has dangling edges."""
    with pytest.raises(ValidationError) as excinfo:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Published Recipe"),
            interface=RecipeInterface(),
            status=RecipeStatus.PUBLISHED,
            topology=GraphTopology(
                nodes=[
                    AgentNode(id="start", agent_ref="concrete-agent-id"),
                ],
                edges=[{"source": "start", "target": "missing-node"}],
                entry_point="start",
                # Use draft for topology to bypass immediate topology check, catch it in lifecycle check
                status="draft",
            ),
        )

    assert "Lifecycle Error" in str(excinfo.value)
    assert "structurally invalid" in str(excinfo.value)
