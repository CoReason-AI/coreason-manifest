# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.reasoning import (
    AdversarialConfig,
    GapScanConfig,
    ReasoningConfig,
    ReviewStrategy,
)
from coreason_manifest.spec.v2.recipe import RecipeNode


def test_episteme_defaults() -> None:
    """Verify default meta-cognition settings."""
    config = ReasoningConfig()
    assert config.strategy == ReviewStrategy.NONE
    assert config.max_revisions == 1


def test_adversarial_configuration() -> None:
    """Verify detailed adversarial review configuration."""
    adv_config = AdversarialConfig(
        persona="security_auditor", attack_vectors=["prompt_injection", "pii_leak"], temperature=0.5
    )
    reasoning = ReasoningConfig(strategy=ReviewStrategy.ADVERSARIAL, adversarial=adv_config, max_revisions=3)

    assert reasoning.strategy == "adversarial"
    assert reasoning.adversarial is not None
    assert reasoning.adversarial.persona == "security_auditor"
    assert len(reasoning.adversarial.attack_vectors) == 2


def test_gap_scan_toggle() -> None:
    """Verify knowledge gap scanning toggle."""
    config = ReasoningConfig(gap_scan=GapScanConfig(enabled=True, confidence_threshold=0.9))
    assert config.gap_scan is not None
    assert config.gap_scan.enabled is True
    assert config.gap_scan.confidence_threshold == 0.9


def test_node_integration() -> None:
    """Ensure a RecipeNode can carry reasoning logic."""
    node = RecipeNode(id="step_1", reasoning=ReasoningConfig(strategy=ReviewStrategy.BASIC))
    assert node.reasoning is not None
    assert node.reasoning.strategy == ReviewStrategy.BASIC

    # Test JSON serialization
    data = node.model_dump(mode="json")
    assert data["reasoning"]["strategy"] == "basic"
