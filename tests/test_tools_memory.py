import pytest

from coreason_manifest.core.state.memory import ConsolidationStrategy, EpisodicMemoryConfig
from coreason_manifest.core.state.tools import LoadStrategy, ToolCapability


def test_load_strategy_enum() -> None:
    assert LoadStrategy.EAGER.value == "eager"
    assert LoadStrategy.LAZY.value == "lazy"


def test_tool_capability_validation() -> None:
    # Test valid eager
    tool = ToolCapability(name="test_tool", load_strategy=LoadStrategy.EAGER)
    assert tool.load_strategy == LoadStrategy.EAGER

    # Test invalid lazy without intent
    with pytest.raises(ValueError, match="trigger_intent is required"):
        ToolCapability(name="test_tool", load_strategy=LoadStrategy.LAZY)

    # Test valid lazy
    tool = ToolCapability(name="test_tool", load_strategy=LoadStrategy.LAZY, trigger_intent="do something")
    assert tool.load_strategy == LoadStrategy.LAZY
    assert tool.trigger_intent == "do something"


def test_consolidation_strategy_enum() -> None:
    assert ConsolidationStrategy.NONE.value == "none"
    assert ConsolidationStrategy.SUMMARY_WINDOW.value == "summary_window"
    assert ConsolidationStrategy.SEMANTIC_CLUSTER.value == "semantic_cluster"
    assert ConsolidationStrategy.SESSION_CLOSE.value == "session_close"


def test_episodic_memory_config() -> None:
    config = EpisodicMemoryConfig(salience_threshold=0.5, consolidation_strategy=ConsolidationStrategy.SUMMARY_WINDOW)
    assert config.consolidation_strategy == ConsolidationStrategy.SUMMARY_WINDOW
