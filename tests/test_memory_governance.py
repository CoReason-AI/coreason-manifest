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

from coreason_manifest.spec.common.interoperability import AgentRuntimeConfig
from coreason_manifest.spec.common.memory import MemoryConfig, MemoryStrategy


def test_memory_config_serialization():
    """Test that MemoryConfig serializes correctly within AgentRuntimeConfig."""
    mem = MemoryConfig(
        strategy=MemoryStrategy.SUMMARY, limit=10, summary_prompt="Compress this."
    )
    config = AgentRuntimeConfig(memory=mem)

    dumped = config.model_dump(mode="json")

    assert dumped["memory"]["strategy"] == "summary"
    assert dumped["memory"]["limit"] == 10
    assert dumped["memory"]["summary_prompt"] == "Compress this."


def test_memory_config_defaults():
    """Test that MemoryConfig applies correct defaults."""
    mem = MemoryConfig(limit=20)

    assert mem.strategy == MemoryStrategy.SLIDING_WINDOW
    assert mem.summary_prompt is None
    assert mem.limit == 20


def test_memory_config_immutability():
    """Test that MemoryConfig is immutable."""
    mem = MemoryConfig(limit=20)
    config = AgentRuntimeConfig(memory=mem)

    # Test mutating MemoryConfig directly
    with pytest.raises(ValidationError):
        mem.limit = 30  # type: ignore

    # Test mutating via AgentRuntimeConfig
    # Note: Pydantic models are not recursive immutable by default unless they are frozen too.
    # AgentRuntimeConfig is frozen, MemoryConfig is frozen.

    # However, attempting to set an attribute on a frozen model raises ValidationError.
    with pytest.raises(ValidationError):
        config.memory = MemoryConfig(limit=50) # type: ignore

    # We should also check if we can mutate the nested object (we can't because we can't assign to it,
    # but we also can't modify the nested object itself as verified above).
