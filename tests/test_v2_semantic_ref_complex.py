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


def test_mixed_references_in_draft() -> None:
    """Verify a DRAFT recipe can contain both concrete `str` IDs and `SemanticRef` objects."""
    concrete = AgentNode(id="concrete", agent_ref="agent-123")
    abstract = AgentNode(id="abstract", agent_ref=SemanticRef(intent="Do magic"))

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Mixed Draft"),
        interface=RecipeInterface(),
        status=RecipeStatus.DRAFT,
        topology=GraphTopology(
            nodes=[concrete, abstract], edges=[{"source": "concrete", "target": "abstract"}], entry_point="concrete"
        ),
    )

    assert recipe.status == RecipeStatus.DRAFT
    # Check nodes
    nodes = {n.id: n for n in recipe.topology.nodes}
    concrete_node = nodes["concrete"]
    abstract_node = nodes["abstract"]

    assert isinstance(concrete_node, AgentNode)
    assert isinstance(abstract_node, AgentNode)
    assert isinstance(concrete_node.agent_ref, str)
    assert isinstance(abstract_node.agent_ref, SemanticRef)


def test_complex_semantic_ref_serialization() -> None:
    """Verify full serialization/deserialization of a `SemanticRef` with rich metadata."""
    rec1 = RecipeRecommendation(ref="cand-1", score=0.9, rationale="Good", warnings=[])
    rec2 = RecipeRecommendation(ref="cand-2", score=0.8, rationale="Cheap", warnings=["Slow"])
    opt = OptimizationIntent(base_ref="base-v1", improvement_goal="Speed up", strategy="atomic")

    sem_ref = SemanticRef(
        intent="Optimize DB",
        constraints=["latency < 10ms"],
        candidates=[rec1, rec2],
        optimization=opt,
    )

    node = AgentNode(id="opt-task", agent_ref=sem_ref)

    # Round trip via model_dump_json/model_validate_json
    json_str = node.model_dump_json()
    loaded_node = AgentNode.model_validate_json(json_str)

    assert isinstance(loaded_node.agent_ref, SemanticRef)
    assert len(loaded_node.agent_ref.candidates) == 2
    assert loaded_node.agent_ref.candidates[1].warnings == ["Slow"]
    assert loaded_node.agent_ref.optimization is not None
    assert loaded_node.agent_ref.optimization.strategy == "atomic"


def test_edge_case_empty_lists_semantic_ref() -> None:
    """Verify `SemanticRef` works with empty `constraints` and `candidates` (default factories)."""
    sem_ref = SemanticRef(intent="Simple intent")
    assert sem_ref.constraints == []
    assert sem_ref.candidates == []
    assert sem_ref.optimization is None

    # Verify explicitly empty
    sem_ref_explicit = SemanticRef(intent="Explicit", constraints=[], candidates=[])
    assert sem_ref_explicit.constraints == []


def test_edge_case_optimization_strategy_enum() -> None:
    """Verify valid vs invalid `strategy` literals in `OptimizationIntent`."""
    # Valid
    _ = OptimizationIntent(base_ref="b", improvement_goal="g", strategy="atomic")
    _ = OptimizationIntent(base_ref="b", improvement_goal="g", strategy="parallel")

    # Invalid
    with pytest.raises(ValidationError) as excinfo:
        # We pass an invalid string to test validation, but cast it to Any to satisfy MyPy
        OptimizationIntent.model_validate(
            {
                "base_ref": "b",
                "improvement_goal": "g",
                "strategy": "invalid_strategy",
            }
        )

    assert "Input should be 'atomic' or 'parallel'" in str(excinfo.value)


def test_lifecycle_mixed_publish_failure() -> None:
    """Verify that if *any* node is SemanticRef (even if others are concrete), publishing fails."""
    concrete = AgentNode(id="concrete", agent_ref="agent-123")
    abstract = AgentNode(id="abstract", agent_ref=SemanticRef(intent="Do magic"))

    with pytest.raises(ValidationError) as excinfo:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Mixed Publish"),
            interface=RecipeInterface(),
            status=RecipeStatus.PUBLISHED,
            topology=GraphTopology(
                nodes=[concrete, abstract], edges=[{"source": "concrete", "target": "abstract"}], entry_point="concrete"
            ),
        )

    err_msg = str(excinfo.value)
    assert "Lifecycle Error" in err_msg
    assert "abstract" in err_msg
    # Ensure "concrete" is NOT listed as abstract
    # This assumes the error message lists abstract nodes.
    # Based on implementation: `f"Lifecycle Error: Nodes {abstract_nodes} are still abstract...`
    assert "'concrete'" not in err_msg


def test_lifecycle_multiple_abstract_nodes_failure() -> None:
    """Verify error message lists *all* abstract nodes when multiple are present."""
    n1 = AgentNode(id="n1", agent_ref=SemanticRef(intent="i1"))
    n2 = AgentNode(id="n2", agent_ref=SemanticRef(intent="i2"))
    n3 = AgentNode(id="n3", agent_ref="concrete-1")

    with pytest.raises(ValidationError) as excinfo:
        RecipeDefinition(
            metadata=ManifestMetadata(name="Multi Abstract"),
            interface=RecipeInterface(),
            status=RecipeStatus.PUBLISHED,
            topology=GraphTopology(
                nodes=[n1, n2, n3],
                edges=[{"source": "n1", "target": "n2"}, {"source": "n2", "target": "n3"}],
                entry_point="n1",
            ),
        )

    err_msg = str(excinfo.value)
    assert "n1" in err_msg
    assert "n2" in err_msg
    assert "n3" not in err_msg
