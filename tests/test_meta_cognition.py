import pytest
from pydantic import ValidationError

from coreason_manifest.core.compute.reasoning import (
    AdversarialConfig,
    GapScanConfig,
    ReviewStrategy,
)


def test_review_strategy_enum():
    assert ReviewStrategy.NONE == "none"
    assert ReviewStrategy.BASIC == "basic"
    assert ReviewStrategy.ADVERSARIAL == "adversarial"
    assert ReviewStrategy.CAUSAL == "causal"
    assert ReviewStrategy.CONSENSUS == "consensus"


def test_adversarial_config():
    # Test valid
    config = AdversarialConfig(persona="hacker", attack_vectors=["payload_splitting"])
    assert config.persona == "hacker"
    assert config.attack_vectors == ["payload_splitting"]

    # Test frozen
    with pytest.raises(ValidationError):
        config.persona = "new"

    # Test extra forbid
    with pytest.raises(ValidationError):
        AdversarialConfig(extra_field="invalid")


def test_gap_scan_config():
    # Test valid
    config = GapScanConfig(enabled=True, confidence_threshold=0.9)
    assert config.enabled is True
    assert config.confidence_threshold == 0.9

    # Test frozen
    with pytest.raises(ValidationError):
        config.enabled = False


def test_base_reasoning_validation():
    # Test valid base case
    from coreason_manifest.core.compute.reasoning import StandardReasoning

    reasoning = StandardReasoning(model="gpt-4", review_strategy=ReviewStrategy.BASIC)
    assert reasoning.review_strategy == ReviewStrategy.BASIC

    # Test invalid adversarial without config
    with pytest.raises(ValueError, match="adversarial_config is required"):
        StandardReasoning(model="gpt-4", review_strategy=ReviewStrategy.ADVERSARIAL)

    # Test valid adversarial
    reasoning = StandardReasoning(
        model="gpt-4", review_strategy=ReviewStrategy.ADVERSARIAL, adversarial_config=AdversarialConfig()
    )
    assert reasoning.review_strategy == ReviewStrategy.ADVERSARIAL
    assert reasoning.adversarial_config is not None
