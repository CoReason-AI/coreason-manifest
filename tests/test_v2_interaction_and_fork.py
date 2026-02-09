# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData, ProvenanceType
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GenerativeNode,
    InteractionConfig,
    InterventionTrigger,
    TransparencyLevel,
)


def test_interaction_config_serialization() -> None:
    """Verify InteractionConfig serializes correctly with defaults and custom values."""
    # Default
    config = InteractionConfig()
    assert config.transparency == TransparencyLevel.OPAQUE
    assert config.triggers == []
    assert config.editable_fields == []
    assert config.enforce_contract is True
    assert config.guidance_hint is None

    # Custom
    config = InteractionConfig(
        transparency=TransparencyLevel.INTERACTIVE,
        triggers=[InterventionTrigger.ON_FAILURE, InterventionTrigger.ON_COMPLETION],
        editable_fields=["inputs", "system_prompt_override"],
        enforce_contract=False,
        guidance_hint="Please review carefully.",
    )
    assert config.transparency == "interactive"
    assert InterventionTrigger.ON_FAILURE in config.triggers
    assert config.enforce_contract is False
    assert config.guidance_hint == "Please review carefully."


def test_universal_inheritance() -> None:
    """Verify AgentNode and GenerativeNode accept interaction config."""
    interaction = InteractionConfig(transparency=TransparencyLevel.OBSERVABLE)

    # AgentNode
    agent_node = AgentNode(id="agent-1", agent_ref="agent-v1", interaction=interaction)
    assert agent_node.interaction is not None
    assert agent_node.interaction.transparency == TransparencyLevel.OBSERVABLE

    # GenerativeNode
    gen_node = GenerativeNode(
        id="gen-1", goal="Solve world hunger", output_schema={"type": "string"}, interaction=interaction
    )
    assert gen_node.interaction is not None
    assert gen_node.interaction.transparency == TransparencyLevel.OBSERVABLE


def test_provenance_fork_lineage() -> None:
    """Verify ManifestMetadata with ProvenanceData for a steered fork."""
    provenance = ProvenanceData(
        type=ProvenanceType.HUMAN,
        derived_from="recipe-v1-published",
        modifications=["Changed input on step-3"],
        original_intent="Optimize for speed",
    )

    metadata = ManifestMetadata(name="Forked Recipe", provenance=provenance)

    assert metadata.provenance is not None
    assert metadata.provenance.type == "human"
    assert metadata.provenance.derived_from == "recipe-v1-published"
    assert metadata.provenance.modifications == ["Changed input on step-3"]
    assert metadata.provenance.original_intent == "Optimize for speed"


def test_provenance_serialization() -> None:
    """Verify ProvenanceData dumps correctly."""
    provenance = ProvenanceData(type=ProvenanceType.AI, generated_by="coreason-strategist-v1", confidence_score=0.95)
    data = provenance.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert data["type"] == "ai"
    assert data["generated_by"] == "coreason-strategist-v1"
    assert data["confidence_score"] == 0.95
    assert "derived_from" not in data  # Should be excluded if None by default
