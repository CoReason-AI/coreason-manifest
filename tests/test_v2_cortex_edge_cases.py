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

from coreason_manifest.spec.v2.knowledge import ConsolidationStrategy, MemoryWriteConfig
from coreason_manifest.spec.v2.reasoning import ReflexConfig


def test_memory_write_config_defaults() -> None:
    """Test default values for MemoryWriteConfig."""
    config = MemoryWriteConfig()
    assert config.strategy == ConsolidationStrategy.SESSION_CLOSE
    assert config.frequency_turns == 10
    assert config.destination_collection is None


def test_memory_write_config_custom() -> None:
    """Test custom values for MemoryWriteConfig."""
    config = MemoryWriteConfig(
        strategy=ConsolidationStrategy.SUMMARY_WINDOW,
        frequency_turns=20,
        destination_collection="long_term_store",
    )
    assert config.strategy == ConsolidationStrategy.SUMMARY_WINDOW
    assert config.frequency_turns == 20
    assert config.destination_collection == "long_term_store"


def test_memory_write_config_extra_forbid() -> None:
    """Test that extra fields are forbidden in MemoryWriteConfig."""
    with pytest.raises(ValidationError) as exc:
        MemoryWriteConfig.model_validate({"strategy": "none", "extra_field": "not_allowed"})
    assert "Extra inputs are not permitted" in str(exc.value)


def test_reflex_config_defaults() -> None:
    """Test default values for ReflexConfig."""
    config = ReflexConfig()
    assert config.enabled is True
    assert config.confidence_threshold == 0.9
    assert config.allowed_tools == []


def test_reflex_config_custom() -> None:
    """Test custom values for ReflexConfig."""
    config = ReflexConfig(
        enabled=False,
        confidence_threshold=0.5,
        allowed_tools=["search"],
    )
    assert config.enabled is False
    assert config.confidence_threshold == 0.5
    assert config.allowed_tools == ["search"]


def test_reflex_config_extra_forbid() -> None:
    """Test that extra fields are forbidden in ReflexConfig."""
    with pytest.raises(ValidationError) as exc:
        ReflexConfig.model_validate({"enabled": True, "extra": "field"})
    assert "Extra inputs are not permitted" in str(exc.value)


def test_reflex_config_frozen() -> None:
    """Test that ReflexConfig is frozen."""
    config = ReflexConfig()
    with pytest.raises(ValidationError):
        config.enabled = False  # type: ignore


def test_memory_write_config_frozen() -> None:
    """Test that MemoryWriteConfig is frozen."""
    config = MemoryWriteConfig()
    with pytest.raises(ValidationError):
        config.frequency_turns = 100  # type: ignore
