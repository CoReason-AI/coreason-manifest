import pytest
from pydantic import ValidationError

from coreason_manifest.core.state.tools import LoadStrategy, ToolCapability


def test_tool_capability_lazy_loading_without_intent() -> None:
    """Test that a lazy tool without a trigger_intent raises a ValueError."""
    with pytest.raises(ValidationError) as exc_info:
        ToolCapability(
            name="lazy_tool",
            description="A lazy tool",
            load_strategy=LoadStrategy.LAZY,
        )
    assert "Lazy loading requires a trigger_intent" in str(exc_info.value)


def test_tool_capability_lazy_loading_with_intent() -> None:
    """Test that a lazy tool with a trigger_intent is valid."""
    tool = ToolCapability(
        name="lazy_tool",
        description="A lazy tool",
        load_strategy=LoadStrategy.LAZY,
        trigger_intent="A semantic description of what this tool does",
    )
    assert tool.name == "lazy_tool"
    assert tool.load_strategy == LoadStrategy.LAZY
    assert tool.trigger_intent == "A semantic description of what this tool does"


def test_tool_capability_eager_loading_without_intent() -> None:
    """Test that an eager tool without a trigger_intent is valid."""
    tool = ToolCapability(
        name="eager_tool",
        description="An eager tool",
        load_strategy=LoadStrategy.EAGER,
    )
    assert tool.name == "eager_tool"
    assert tool.load_strategy == LoadStrategy.EAGER
    assert tool.trigger_intent is None
