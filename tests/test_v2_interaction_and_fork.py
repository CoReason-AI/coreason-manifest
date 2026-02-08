# Copyright (c) 2025 CoReason, Inc.

import pytest
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GenerativeNode,
    InteractionConfig,
    InterventionTrigger,
    TransparencyLevel,
)


def test_interaction_config_universal_inheritance():
    """Verify that both AgentNode and GenerativeNode accept interaction config."""

    # Define interaction config
    interaction = InteractionConfig(
        transparency=TransparencyLevel.INTERACTIVE,
        triggers=[InterventionTrigger.ON_START, InterventionTrigger.ON_FAILURE],
        editable_fields=["system_prompt_override", "inputs"],
        enforce_contract=True,
        guidance_hint="Review input arguments carefully."
    )

    # 1. AgentNode
    agent_node = AgentNode(
        id="agent-1",
        agent_ref="agent-v1",
        interaction=interaction
    )
    assert agent_node.interaction is not None
    assert agent_node.interaction.transparency == TransparencyLevel.INTERACTIVE
    assert InterventionTrigger.ON_START in agent_node.interaction.triggers

    # 2. GenerativeNode
    gen_node = GenerativeNode(
        id="gen-1",
        goal="Solve world peace",
        output_schema={"type": "object"},
        interaction=interaction
    )
    assert gen_node.interaction is not None
    assert gen_node.interaction.enforce_contract is True


def test_interaction_config_serialization():
    """Verify InteractionConfig serializes correctly, especially enforce_contract."""

    config = InteractionConfig(
        transparency=TransparencyLevel.OBSERVABLE,
        triggers=[InterventionTrigger.ON_COMPLETION],
        enforce_contract=True
    )

    dumped = config.dump()
    assert dumped["transparency"] == "observable"
    assert dumped["triggers"] == ["on_completion"]
    assert dumped["enforce_contract"] is True


def test_fork_provenance():
    """Verify ManifestMetadata supports 'Steered Fork' provenance structure."""

    # Create ProvenanceData mimicking a steered fork
    provenance = ProvenanceData(
        type="human",
        derived_from="recipe-v1-published",
        modifications=["Changed input on step-3", "Tweaked system prompt"],
        generated_by="user-123",
        rationale="Optimizing for better tone"
    )

    # Attach to ManifestMetadata
    metadata = ManifestMetadata(
        name="Steered Recipe",
        provenance=provenance
    )

    assert metadata.provenance is not None
    assert metadata.provenance.type == "human"
    assert metadata.provenance.derived_from == "recipe-v1-published"
    assert len(metadata.provenance.modifications) == 2
    assert "Changed input on step-3" in metadata.provenance.modifications

    # Verify dump structure
    dumped = metadata.dump()
    assert dumped["provenance"]["derived_from"] == "recipe-v1-published"
    assert dumped["provenance"]["modifications"] == ["Changed input on step-3", "Tweaked system prompt"]
