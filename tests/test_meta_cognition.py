import pytest

from coreason_manifest.core.compute.reasoning import (
    AdversarialConfig,
    GapScanConfig,
    ReviewStrategy,
    StandardReasoning,
)
from coreason_manifest.toolkit.builder import AgentBuilder


def test_gapscan_adversarial_instantiation() -> None:
    """Test successful instantiation of GapScanConfig and AdversarialConfig."""
    gap_scan = GapScanConfig(enabled=True, confidence_threshold=0.9)
    assert gap_scan.enabled is True
    assert gap_scan.confidence_threshold == 0.9

    adversarial = AdversarialConfig(persona="auditor", attack_vectors=["injection"])
    assert adversarial.persona == "auditor"
    assert adversarial.attack_vectors == ["injection"]

    # Test default values
    gap_scan_default = GapScanConfig()
    assert gap_scan_default.enabled is False
    assert gap_scan_default.confidence_threshold == 0.8

    adversarial_default = AdversarialConfig()
    assert adversarial_default.persona == "skeptic"
    assert adversarial_default.attack_vectors == []


def test_base_reasoning_adversarial_validation() -> None:
    """Test that BaseReasoning model validator raises ValueError appropriately."""
    # Should work fine without adversarial config if strategy is not adversarial
    reasoning_basic = StandardReasoning(model="gpt-4o", review_strategy=ReviewStrategy.BASIC)
    assert reasoning_basic.review_strategy == ReviewStrategy.BASIC

    # Should raise ValueError when review_strategy is adversarial but config is None
    with pytest.raises(ValueError, match="adversarial_config must be provided when review_strategy is 'adversarial'"):
        StandardReasoning(
            model="gpt-4o",
            review_strategy=ReviewStrategy.ADVERSARIAL,
        )

    # Should work fine when review_strategy is adversarial and config is provided
    adv_config = AdversarialConfig(persona="devil_advocate")
    reasoning_adv = StandardReasoning(
        model="gpt-4o",
        review_strategy=ReviewStrategy.ADVERSARIAL,
        adversarial_config=adv_config,
    )
    assert reasoning_adv.review_strategy == ReviewStrategy.ADVERSARIAL
    assert reasoning_adv.adversarial_config is not None
    assert reasoning_adv.adversarial_config.persona == "devil_advocate"


def test_agent_builder_with_meta_cognition() -> None:
    """Test that AgentBuilder.with_meta_cognition() constructs AgentNode with correct params."""
    builder = (
        AgentBuilder("test_agent")
        .with_identity(role="reviewer", persona="You review stuff")
        .with_reasoning(model="gpt-4o")
        .with_meta_cognition(
            review_strategy="adversarial",
            adversarial_persona="security_auditor",
            gap_scan_enabled=True,
            gap_scan_threshold=0.85,
            max_revisions=3,
        )
    )

    agent_node = builder.build()

    assert agent_node.profile is not None
    assert not isinstance(agent_node.profile, str)
    assert agent_node.profile.reasoning is not None

    reasoning = agent_node.profile.reasoning

    assert reasoning.review_strategy == ReviewStrategy.ADVERSARIAL
    assert reasoning.max_revisions == 3

    assert reasoning.gap_scan is not None
    assert reasoning.gap_scan.enabled is True
    assert reasoning.gap_scan.confidence_threshold == 0.85

    assert reasoning.adversarial_config is not None
    assert reasoning.adversarial_config.persona == "security_auditor"
    assert reasoning.adversarial_config.attack_vectors == []

    # Test with standard meta cognition
    builder_basic = (
        AgentBuilder("test_agent_basic")
        .with_identity(role="assistant", persona="You help")
        .with_reasoning(model="gpt-4o")
        .with_meta_cognition(
            review_strategy="basic",
            gap_scan_enabled=False,
        )
    )

    agent_node_basic = builder_basic.build()
    assert agent_node_basic.profile is not None
    assert not isinstance(agent_node_basic.profile, str)
    assert agent_node_basic.profile.reasoning is not None
    reasoning_basic = agent_node_basic.profile.reasoning

    assert reasoning_basic.review_strategy == ReviewStrategy.BASIC
    assert reasoning_basic.adversarial_config is None
    assert reasoning_basic.gap_scan is None
