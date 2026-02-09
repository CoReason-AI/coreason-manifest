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
from coreason_manifest.spec.v2.recipe import AgentNode, RecipeNode


def test_episteme_defaults() -> None:
    """Verify default meta-cognition settings."""
    config = ReasoningConfig()
    assert config.strategy == ReviewStrategy.NONE
    assert config.max_revisions == 1
    assert config.adversarial is None
    assert config.gap_scan is None


def test_adversarial_configuration() -> None:
    """Verify detailed adversarial review configuration."""
    adv_config = AdversarialConfig(
        persona="security_auditor",
        attack_vectors=["prompt_injection", "pii_leak"],
        temperature=0.5,
    )
    reasoning = ReasoningConfig(
        strategy=ReviewStrategy.ADVERSARIAL,
        adversarial=adv_config,
        max_revisions=3,
    )

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
    node = RecipeNode(
        id="step_1",
        reasoning=ReasoningConfig(strategy=ReviewStrategy.BASIC),
    )
    assert node.reasoning is not None
    assert node.reasoning.strategy == ReviewStrategy.BASIC

    # Test JSON serialization
    data = node.model_dump(mode="json")
    assert data["reasoning"]["strategy"] == "basic"


def test_agent_node_integration() -> None:
    """
    Ensure an AgentNode (as shown in docs) can carry reasoning logic.
    This validates the documentation example.
    """
    reasoning = ReasoningConfig(
        strategy=ReviewStrategy.ADVERSARIAL, max_revisions=3, adversarial=AdversarialConfig(persona="critic")
    )

    node = AgentNode(id="writer", agent_ref="copywriter-v1", reasoning=reasoning)

    assert node.id == "writer"
    assert node.agent_ref == "copywriter-v1"
    assert node.reasoning is not None
    assert node.reasoning.strategy == ReviewStrategy.ADVERSARIAL
    assert node.reasoning.adversarial is not None
    assert node.reasoning.adversarial.persona == "critic"


def test_edge_cases_empty_collections() -> None:
    """Verify handling of empty lists in AdversarialConfig."""
    adv_config = AdversarialConfig(
        persona="empty_critic",
        attack_vectors=[],  # Empty list
    )
    assert adv_config.attack_vectors == []

    # Ensure empty list serializes correctly
    data = adv_config.model_dump(mode="json")
    assert data["attack_vectors"] == []


def test_complex_case_mixed_strategies() -> None:
    """
    Test a complex scenario where both gap scanning (pre-check)
    and adversarial review (post-check) are enabled.
    """
    reasoning = ReasoningConfig(
        strategy=ReviewStrategy.ADVERSARIAL,
        max_revisions=5,
        gap_scan=GapScanConfig(enabled=True, confidence_threshold=0.75),
        adversarial=AdversarialConfig(
            persona="harshest_critic", attack_vectors=["logic", "style", "completeness"], temperature=1.0
        ),
    )

    assert reasoning.strategy == ReviewStrategy.ADVERSARIAL
    assert reasoning.gap_scan is not None
    assert reasoning.gap_scan.enabled is True
    assert reasoning.adversarial is not None
    assert reasoning.adversarial.temperature == 1.0
    assert len(reasoning.adversarial.attack_vectors) == 3


def test_forbidden_extra_fields() -> None:
    """
    Verify that providing extra fields raises a ValidationError
    because extra='forbid' is set in ConfigDict.
    """
    with pytest.raises(ValidationError) as excinfo:
        AdversarialConfig.model_validate({"persona": "tester", "temperature": 0.5, "extra_field": "should_fail"})
    assert "extra_field" in str(excinfo.value)


def test_explicit_none_assignment() -> None:
    """Verify that optional fields can be explicitly set to None."""
    config = ReasoningConfig(strategy=ReviewStrategy.NONE, adversarial=None, gap_scan=None)
    assert config.adversarial is None
    assert config.gap_scan is None
