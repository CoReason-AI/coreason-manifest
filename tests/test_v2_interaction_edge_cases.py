# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData, ProvenanceType
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    EvaluatorNode,
    GenerativeNode,
    GraphTopology,
    HumanNode,
    InteractionConfig,
    InterventionTrigger,
    RecipeDefinition,
    RecipeInterface,
    RouterNode,
    TransparencyLevel,
)

# ==========================================
# 1. Edge Cases: InteractionConfig
# ==========================================


def test_interaction_config_empty_triggers() -> None:
    """Verify empty list for triggers is valid and distinct from None (if None was allowed, but default is list)."""
    config = InteractionConfig(triggers=[])
    assert config.triggers == []
    assert len(config.triggers) == 0


def test_interaction_config_invalid_transparency() -> None:
    """Verify invalid enum value raises ValidationError."""
    with pytest.raises(ValidationError) as exc:
        InteractionConfig(transparency="crystal_clear")
    assert "Input should be 'opaque', 'observable' or 'interactive'" in str(exc.value)


def test_interaction_config_invalid_trigger() -> None:
    """Verify invalid trigger enum value."""
    with pytest.raises(ValidationError) as exc:
        InteractionConfig(triggers=["on_whim"])
    assert "Input should be 'on_start', 'on_plan_generation', 'on_failure' or 'on_completion'" in str(exc.value)


def test_interaction_config_editable_fields_non_existent() -> None:
    """
    Verify editable_fields accepts arbitrary strings (runtime validation responsibility).
    The schema just validates it's a list of strings.
    """
    config = InteractionConfig(editable_fields=["non_existent_field", "inputs.nested"])
    assert "non_existent_field" in config.editable_fields


# ==========================================
# 2. Edge Cases: Universal Inheritance
# ==========================================


def test_inheritance_human_node() -> None:
    """Verify HumanNode accepts interaction config (even if redundant)."""
    node = HumanNode(
        id="human-1", prompt="Review", interaction=InteractionConfig(transparency=TransparencyLevel.OBSERVABLE)
    )
    assert node.interaction is not None
    assert node.interaction.transparency == TransparencyLevel.OBSERVABLE


def test_inheritance_router_node() -> None:
    """Verify RouterNode accepts interaction config."""
    node = RouterNode(
        id="router-1",
        input_key="classification",
        routes={"A": "node-A"},
        default_route="node-B",
        interaction=InteractionConfig(triggers=[InterventionTrigger.ON_START]),
    )
    assert node.interaction is not None
    assert InterventionTrigger.ON_START in node.interaction.triggers


def test_inheritance_evaluator_node() -> None:
    """Verify EvaluatorNode accepts interaction config."""
    node = EvaluatorNode(
        id="eval-1",
        target_variable="output",
        evaluator_agent_ref="judge-v1",
        evaluation_profile="strict",
        pass_threshold=0.8,
        max_refinements=2,
        pass_route="success",
        fail_route="retry",
        feedback_variable="critique",
        interaction=InteractionConfig(enforce_contract=False),
    )
    assert node.interaction is not None
    assert node.interaction.enforce_contract is False


# ==========================================
# 3. Complex Cases: Provenance & Full Recipe
# ==========================================


def test_full_provenance_structure() -> None:
    """Verify a maximally populated ProvenanceData object."""
    now = datetime.now(UTC)
    provenance = ProvenanceData(
        type=ProvenanceType.HYBRID,
        generated_by="coreason-strategist-v2",
        generated_date=now,
        rationale="User requested lower latency.",
        original_intent="Build a fast scraper.",
        confidence_score=0.88,
        methodology="Prompt Chaining",
        derived_from="recipe-v1-slow",
        modifications=["Removed retry loop", "Added caching"],
    )

    dump = provenance.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert dump["type"] == "hybrid"
    assert dump["generated_by"] == "coreason-strategist-v2"
    assert dump["confidence_score"] == 0.88
    # Date serialization check
    assert isinstance(dump["generated_date"], str)


def test_complex_recipe_mixed_interactions() -> None:
    """
    Verify a RecipeDefinition containing nodes with mixed interaction configurations.
    - Node 1: Interactive (Start Trigger)
    - Node 2: Opaque (Default)
    - Node 3: Observable
    """

    # Node 1: Interactive
    node1 = AgentNode(
        id="step-1",
        agent_ref="agent-interactive",
        interaction=InteractionConfig(
            transparency=TransparencyLevel.INTERACTIVE,
            triggers=[InterventionTrigger.ON_START],
            guidance_hint="Check inputs",
        ),
    )

    # Node 2: Opaque (No interaction config)
    node2 = AgentNode(id="step-2", agent_ref="agent-opaque")

    # Node 3: Observable
    node3 = GenerativeNode(
        id="step-3",
        goal="Generate report",
        output_schema={"type": "string"},
        interaction=InteractionConfig(transparency=TransparencyLevel.OBSERVABLE),
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(
            name="Mixed Interaction Recipe",
            provenance=ProvenanceData(type=ProvenanceType.HUMAN, derived_from="template-v1"),
        ),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=[node1, node2, node3],
            edges=[{"source": "step-1", "target": "step-2"}, {"source": "step-2", "target": "step-3"}],
            entry_point="step-1",
        ),
    )

    # Serialize & Deserialize
    json_str = recipe.model_dump_json()
    loaded = RecipeDefinition.model_validate_json(json_str)

    nodes = {n.id: n for n in loaded.topology.nodes}

    # Check Node 1
    assert nodes["step-1"].interaction is not None
    assert nodes["step-1"].interaction.transparency == TransparencyLevel.INTERACTIVE
    assert nodes["step-1"].interaction.triggers == [InterventionTrigger.ON_START]

    # Check Node 2 (Should be None or implied Opaque if we enforced defaults, but field is optional)
    assert nodes["step-2"].interaction is None

    # Check Node 3
    assert nodes["step-3"].interaction is not None
    assert nodes["step-3"].interaction.transparency == TransparencyLevel.OBSERVABLE
    assert nodes["step-3"].interaction.triggers == []  # Default empty list

    # Check Provenance
    assert loaded.metadata.provenance is not None
    assert loaded.metadata.provenance.type == "human"
    assert loaded.metadata.provenance.derived_from == "template-v1"
