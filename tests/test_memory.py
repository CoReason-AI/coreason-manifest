from coreason_manifest.core.state.memory import ConsolidationStrategy, EpisodicMemoryConfig


def test_episodic_memory_config_default_strategy() -> None:
    """Test that EpisodicMemoryConfig defaults to SESSION_CLOSE strategy."""
    config = EpisodicMemoryConfig(
        salience_threshold=0.5,
    )
    assert config.consolidation_strategy == ConsolidationStrategy.SESSION_CLOSE
    assert config.salience_threshold == 0.5
    assert config.consolidation_interval_turns is None


def test_episodic_memory_config_custom_strategy() -> None:
    """Test that EpisodicMemoryConfig can be instantiated with a custom strategy."""
    config = EpisodicMemoryConfig(
        salience_threshold=0.5,
        consolidation_strategy=ConsolidationStrategy.SUMMARY_WINDOW,
        consolidation_interval_turns=10,
    )
    assert config.consolidation_strategy == ConsolidationStrategy.SUMMARY_WINDOW
    assert config.consolidation_interval_turns == 10
