from coreason_manifest.spec.v2.reasoning import (
    AdversarialConfig,
    GapScanConfig,
    ReasoningConfig,
    ReviewStrategy,
)
from coreason_manifest.spec.v2.recipe import AgentNode


def test_adversarial_config() -> None:
    """Test instantiating AdversarialConfig with valid values."""
    config = ReasoningConfig(
        strategy=ReviewStrategy.ADVERSARIAL,
        adversarial=AdversarialConfig(
            persona="devil's advocate",
            attack_vectors=["hallucination", "bias"],
            temperature=0.9,
        ),
    )

    assert config.strategy == ReviewStrategy.ADVERSARIAL
    assert config.adversarial is not None
    assert config.adversarial.persona == "devil's advocate"
    assert "hallucination" in config.adversarial.attack_vectors
    assert config.adversarial.temperature == 0.9


def test_gap_scan_defaults() -> None:
    """Test GapScanConfig defaults and overrides."""
    # Default
    config = GapScanConfig()
    assert config.enabled is False
    assert config.confidence_threshold == 0.8

    # Override
    config_enabled = GapScanConfig(enabled=True, confidence_threshold=0.95)
    assert config_enabled.enabled is True
    assert config_enabled.confidence_threshold == 0.95


def test_recipe_node_integration() -> None:
    """Test attaching ReasoningConfig to a RecipeNode (AgentNode)."""
    reasoning = ReasoningConfig(
        strategy=ReviewStrategy.BASIC,
        max_revisions=3,
        gap_scan=GapScanConfig(enabled=True),
    )

    node = AgentNode(
        id="agent_1",
        reasoning=reasoning,
        agent_ref="some_agent_id",
    )

    assert node.reasoning is not None
    assert node.reasoning.strategy == ReviewStrategy.BASIC
    assert node.reasoning.max_revisions == 3
    assert node.reasoning.gap_scan is not None
    assert node.reasoning.gap_scan.enabled is True


def test_serialization() -> None:
    """Verify JSON serialization of the reasoning block."""
    reasoning = ReasoningConfig(
        strategy=ReviewStrategy.CAUSAL,
        adversarial=AdversarialConfig(persona="logician"),
    )
    node = AgentNode(
        id="agent_2",
        reasoning=reasoning,
        agent_ref="logic_agent",
    )

    data = node.dump()
    assert "reasoning" in data
    assert data["reasoning"]["strategy"] == "causal"
    assert data["reasoning"]["adversarial"]["persona"] == "logician"


def test_defaults() -> None:
    """Verify defaults for ReasoningConfig."""
    config = ReasoningConfig()
    assert config.strategy == ReviewStrategy.NONE
    assert config.adversarial is None
    assert config.gap_scan is None
    assert config.max_revisions == 1
