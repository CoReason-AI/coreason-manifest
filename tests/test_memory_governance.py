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

from coreason_manifest import AgentDefinition, AgentRuntimeConfig
from coreason_manifest.spec.common.memory import MemoryConfig, MemoryStrategy


def test_memory_config_serialization() -> None:
    """Test that MemoryConfig serializes correctly within AgentRuntimeConfig."""
    mem = MemoryConfig(strategy=MemoryStrategy.SUMMARY, limit=10, summary_prompt="Compress this.")
    config = AgentRuntimeConfig(memory=mem)

    dumped = config.model_dump(mode="json")

    assert dumped["memory"]["strategy"] == "summary"
    assert dumped["memory"]["limit"] == 10
    assert dumped["memory"]["summary_prompt"] == "Compress this."


def test_memory_config_defaults() -> None:
    """Test that MemoryConfig applies correct defaults."""
    mem = MemoryConfig(limit=20)

    assert mem.strategy == MemoryStrategy.SLIDING_WINDOW
    assert mem.summary_prompt is None
    assert mem.limit == 20


def test_memory_config_immutability() -> None:
    """Test that MemoryConfig is immutable."""
    mem = MemoryConfig(limit=20)
    config = AgentRuntimeConfig(memory=mem)

    # Test mutating MemoryConfig directly
    with pytest.raises(ValidationError):
        mem.limit = 30  # type: ignore

    # Test mutating via AgentRuntimeConfig
    with pytest.raises(ValidationError):
        config.memory = MemoryConfig(limit=50)  # type: ignore


def test_edge_case_limit_validation() -> None:
    """Test validation for limit field."""
    # Test limit 0
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        MemoryConfig(limit=0)

    # Test negative limit
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        MemoryConfig(limit=-1)


def test_edge_case_summary_validation() -> None:
    """Test validation for summary strategy requirements."""
    # Fail if SUMMARY strategy is used without summary_prompt
    with pytest.raises(ValidationError, match="summary_prompt is required when strategy is SUMMARY"):
        MemoryConfig(strategy=MemoryStrategy.SUMMARY, limit=10)

    # Pass if SUMMARY strategy has prompt
    mem = MemoryConfig(strategy=MemoryStrategy.SUMMARY, limit=10, summary_prompt="Test")
    assert mem.strategy == MemoryStrategy.SUMMARY
    assert mem.summary_prompt == "Test"

    # Pass if other strategy has no prompt
    mem = MemoryConfig(strategy=MemoryStrategy.TOKEN_BUFFER, limit=100)
    assert mem.summary_prompt is None


def test_complex_integration_agent_definition() -> None:
    """Test MemoryConfig integrated into a full AgentDefinition."""
    agent = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Test things",
        runtime=AgentRuntimeConfig(memory=MemoryConfig(strategy=MemoryStrategy.SLIDING_WINDOW, limit=5)),
    )

    dumped = agent.model_dump(mode="json")
    assert dumped["runtime"]["memory"]["strategy"] == "sliding_window"
    assert dumped["runtime"]["memory"]["limit"] == 5

    # Test round trip
    restored = AgentDefinition.model_validate(dumped)
    assert restored.runtime is not None
    assert restored.runtime.memory is not None
    assert restored.runtime.memory.limit == 5


def test_json_round_trip() -> None:
    """Test JSON serialization and deserialization."""
    mem = MemoryConfig(limit=42)
    json_str = mem.model_dump_json()

    # Check compact JSON format
    assert '"limit":42' in json_str or '"limit": 42' in json_str

    restored = MemoryConfig.model_validate_json(json_str)
    assert restored == mem
