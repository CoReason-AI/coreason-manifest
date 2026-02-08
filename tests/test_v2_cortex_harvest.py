# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.agent import CognitiveProfile
from coreason_manifest.spec.v2.knowledge import ConsolidationStrategy, MemoryWriteConfig, RetrievalConfig
from coreason_manifest.spec.v2.reasoning import ReflexConfig, ReasoningConfig

def test_memory_consolidation() -> None:
    """Test 1: Memory Consolidation configuration."""
    config = MemoryWriteConfig(
        strategy=ConsolidationStrategy.SUMMARY_WINDOW,
        frequency_turns=5
    )
    assert config.strategy == ConsolidationStrategy.SUMMARY_WINDOW
    assert config.frequency_turns == 5
    assert config.destination_collection is None

def test_reflex_configuration() -> None:
    """Test 2: Reflex Configuration."""
    config = ReflexConfig(
        enabled=True,
        allowed_tools=["weather_api"]
    )
    assert config.enabled is True
    assert config.allowed_tools == ["weather_api"]
    # Verify default confidence threshold
    assert config.confidence_threshold == 0.9

def test_cognitive_profile_integration() -> None:
    """Test 3: Full Cognitive Profile Integration."""
    # Create configuration objects
    reflex_config = ReflexConfig(enabled=True)
    reasoning_config = ReasoningConfig(max_revisions=2)
    write_config = MemoryWriteConfig(strategy=ConsolidationStrategy.SESSION_CLOSE)
    read_config = RetrievalConfig(collection_name="test_collection")

    # Create CognitiveProfile with all new fields
    # Note: memory_read is aliased as "memory" in the model, but we use the field name here
    # Pydantic V2 model_validate or init allows using field names.

    profile = CognitiveProfile(
        role="tester",
        reflex=reflex_config,
        reasoning=reasoning_config,
        memory_write=write_config,
        memory_read=[read_config]
    )

    # Verify fields
    assert profile.reflex == reflex_config
    assert profile.reasoning == reasoning_config
    assert profile.memory_write == write_config
    assert profile.memory_read == [read_config]

    # Verify serialization
    dumped = profile.model_dump(by_alias=True)
    assert dumped["reflex"]["enabled"] is True
    assert dumped["reasoning"]["max_revisions"] == 2
    assert dumped["memory_write"]["strategy"] == "session_close"
    # Verify alias works in serialization (field 'memory_read' should be 'memory')
    assert "memory" in dumped
    assert dumped["memory"][0]["collection_name"] == "test_collection"

    # Verify alias works in input
    profile_from_alias = CognitiveProfile(
        role="tester",
        memory=[read_config] # using the alias 'memory'
    )
    assert profile_from_alias.memory_read == [read_config]
