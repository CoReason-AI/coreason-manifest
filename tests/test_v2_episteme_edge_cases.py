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

from coreason_manifest.spec.v2.reasoning import (
    AdversarialConfig,
    GapScanConfig,
    ReasoningConfig,
    ReviewStrategy,
)
from coreason_manifest.spec.v2.recipe import AgentNode


def test_episteme_explicit_none() -> None:
    """Verify handling of explicit None values."""
    config = ReasoningConfig(strategy=ReviewStrategy.NONE, adversarial=None, gap_scan=None, max_revisions=1)
    assert config.strategy == ReviewStrategy.NONE
    assert config.adversarial is None
    assert config.gap_scan is None


def test_adversarial_empty_vectors() -> None:
    """Verify adversarial config with empty attack vectors."""
    adv_config = AdversarialConfig(persona="critic", attack_vectors=[], temperature=0.7)
    assert adv_config.attack_vectors == []


def test_gap_scan_defaults() -> None:
    """Verify gap scan defaults when instantiated partially."""
    gap_config = GapScanConfig()
    assert gap_config.enabled is False
    assert gap_config.confidence_threshold == 0.8  # Default


def test_max_revisions_zero() -> None:
    """Verify max_revisions can be 0 (no loops)."""
    config = ReasoningConfig(max_revisions=0)
    assert config.max_revisions == 0


def test_complex_nesting_serialization() -> None:
    """Verify serialization of a fully populated node."""
    node = AgentNode(
        id="complex_node",
        agent_ref="agent-x",
        reasoning=ReasoningConfig(
            strategy=ReviewStrategy.ADVERSARIAL,
            adversarial=AdversarialConfig(persona="devil", attack_vectors=["bias", "logic"], temperature=0.9),
            gap_scan=GapScanConfig(enabled=True, confidence_threshold=0.95),
            max_revisions=5,
        ),
    )

    data = node.model_dump(mode="json")
    assert data["reasoning"]["strategy"] == "adversarial"
    assert data["reasoning"]["adversarial"]["persona"] == "devil"
    assert data["reasoning"]["gap_scan"]["enabled"] is True
    assert data["reasoning"]["max_revisions"] == 5


def test_strategy_string_coercion() -> None:
    """Verify string input for strategy enum."""
    config = ReasoningConfig(strategy="adversarial")
    assert config.strategy == ReviewStrategy.ADVERSARIAL


def test_extra_fields_forbidden() -> None:
    """Verify that extra fields raise ValidationError."""
    with pytest.raises(ValidationError):
        # Use model_validate to simulate runtime payload validation
        ReasoningConfig.model_validate({"extra_field": "invalid"})

    with pytest.raises(ValidationError):
        AdversarialConfig.model_validate({"persona": "skeptic", "extra_field": "invalid"})

    with pytest.raises(ValidationError):
        GapScanConfig.model_validate({"extra_field": "invalid"})
