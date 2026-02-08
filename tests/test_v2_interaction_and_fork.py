# Copyright (c) 2025 CoReason, Inc.

from datetime import UTC

import pytest

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GenerativeNode,
    GraphTopology,
    InteractionConfig,
    InterventionTrigger,
    TransparencyLevel,
)


def test_interaction_config_universal_inheritance() -> None:
    """Verify that both AgentNode and GenerativeNode accept interaction config."""

    # Define interaction config
    interaction = InteractionConfig(
        transparency=TransparencyLevel.INTERACTIVE,
        triggers=[InterventionTrigger.ON_START, InterventionTrigger.ON_FAILURE],
        editable_fields=["system_prompt_override", "inputs"],
        enforce_contract=True,
        guidance_hint="Review input arguments carefully.",
    )

    # 1. AgentNode
    agent_node = AgentNode(id="agent-1", agent_ref="agent-v1", interaction=interaction)
    assert agent_node.interaction is not None
    assert agent_node.interaction.transparency == TransparencyLevel.INTERACTIVE
    assert InterventionTrigger.ON_START in agent_node.interaction.triggers

    # 2. GenerativeNode
    gen_node = GenerativeNode(
        id="gen-1", goal="Solve world peace", output_schema={"type": "object"}, interaction=interaction
    )
    assert gen_node.interaction is not None
    assert gen_node.interaction.enforce_contract is True


def test_interaction_config_serialization() -> None:
    """Verify InteractionConfig serializes correctly, especially enforce_contract."""

    config = InteractionConfig(
        transparency=TransparencyLevel.OBSERVABLE, triggers=[InterventionTrigger.ON_COMPLETION], enforce_contract=True
    )

    dumped = config.dump()
    assert dumped["transparency"] == "observable"
    assert dumped["triggers"] == ["on_completion"]
    assert dumped["enforce_contract"] is True


def test_fork_provenance() -> None:
    """Verify ManifestMetadata supports 'Steered Fork' provenance structure."""

    # Create ProvenanceData mimicking a steered fork
    provenance = ProvenanceData(
        type="human",
        derived_from="recipe-v1-published",
        modifications=["Changed input on step-3", "Tweaked system prompt"],
        generated_by="user-123",
        rationale="Optimizing for better tone",
    )

    # Attach to ManifestMetadata
    metadata = ManifestMetadata(name="Steered Recipe", provenance=provenance)

    assert metadata.provenance is not None
    assert metadata.provenance.type == "human"
    assert metadata.provenance.derived_from == "recipe-v1-published"
    assert len(metadata.provenance.modifications) == 2
    assert "Changed input on step-3" in metadata.provenance.modifications

    # Verify dump structure
    dumped = metadata.dump()
    assert dumped["provenance"]["derived_from"] == "recipe-v1-published"
    assert dumped["provenance"]["modifications"] == ["Changed input on step-3", "Tweaked system prompt"]


def test_empty_interaction_config() -> None:
    """Verify that an empty InteractionConfig is valid and has correct defaults."""
    config = InteractionConfig()
    assert config.transparency == TransparencyLevel.OPAQUE
    assert config.triggers == []
    assert config.editable_fields == []
    assert config.enforce_contract is True
    assert config.guidance_hint is None


def test_interaction_config_invalid_field() -> None:
    """Verify that extra fields are forbidden in InteractionConfig."""
    with pytest.raises(Exception):  # Pydantic validation error
        InteractionConfig(extra_field="invalid")  # type: ignore[call-arg]


def test_mixed_transparency_topology() -> None:
    """Verify a topology with mixed transparency levels across nodes."""

    node1 = AgentNode(
        id="step-1", agent_ref="agent-opaque", interaction=InteractionConfig(transparency=TransparencyLevel.OPAQUE)
    )

    node2 = AgentNode(
        id="step-2",
        agent_ref="agent-interactive",
        interaction=InteractionConfig(
            transparency=TransparencyLevel.INTERACTIVE, triggers=[InterventionTrigger.ON_FAILURE]
        ),
    )

    # Create a minimal valid topology
    topology = GraphTopology(
        nodes=[node1, node2], edges=[{"source": "step-1", "target": "step-2"}], entry_point="step-1"
    )

    assert topology.nodes[0].interaction.transparency == TransparencyLevel.OPAQUE
    assert topology.nodes[1].interaction.transparency == TransparencyLevel.INTERACTIVE


def test_provenance_minimal() -> None:
    """Verify ProvenanceData with only required fields."""
    provenance = ProvenanceData(type="ai")
    assert provenance.type == "ai"
    assert provenance.derived_from is None
    assert provenance.modifications == []


def test_provenance_full_serialization() -> None:
    """Verify full serialization of ProvenanceData."""
    from datetime import datetime

    now = datetime.now(UTC)
    provenance = ProvenanceData(
        type="hybrid",
        generated_by="system-x",
        generated_date=now,
        rationale="Testing",
        original_intent="Intent",
        confidence_score=0.9,
        methodology="Method",
        derived_from="parent-id",
        modifications=["mod1"],
    )

    dumped = provenance.dump()
    assert dumped["type"] == "hybrid"
    assert dumped["generated_by"] == "system-x"
    assert dumped["confidence_score"] == 0.9
    assert dumped["derived_from"] == "parent-id"
