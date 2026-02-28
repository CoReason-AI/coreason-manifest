import pytest
from pydantic import ValidationError

from coreason_manifest.core.compute.reasoning import (
    AdversarialConfig,
    GapScanConfig,
    ReviewStrategy,
)


def test_review_strategy_enum() -> None:
    assert ReviewStrategy.NONE.value == "none"
    assert ReviewStrategy.BASIC.value == "basic"
    assert ReviewStrategy.ADVERSARIAL.value == "adversarial"
    assert ReviewStrategy.CAUSAL.value == "causal"
    assert ReviewStrategy.CONSENSUS.value == "consensus"


def test_adversarial_config() -> None:
    # Test valid
    config = AdversarialConfig(persona="hacker", attack_vectors=["payload_splitting"])
    assert config.persona == "hacker"
    assert config.attack_vectors == ["payload_splitting"]

    # Test frozen
    with pytest.raises(ValidationError):
        config.persona = "new"  # type: ignore[misc]

    # Test extra forbid
    with pytest.raises(ValidationError):
        AdversarialConfig(extra_field="invalid")  # type: ignore[call-arg]


def test_gap_scan_config() -> None:
    # Test valid
    config = GapScanConfig(enabled=True, confidence_threshold=0.9)
    assert config.enabled is True
    assert config.confidence_threshold == 0.9

    # Test frozen
    with pytest.raises(ValidationError):
        config.enabled = False  # type: ignore


def test_base_reasoning_validation() -> None:
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
