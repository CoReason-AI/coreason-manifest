from pydantic import TypeAdapter

from coreason_manifest.spec.core.engines import (
    ComputerUseReasoning,
    ReasoningConfig,
)


def test_computer_use_instantiation() -> None:
    # Test defaults
    cu = ComputerUseReasoning(model="gpt-4-vision")
    assert cu.type == "computer_use"
    assert cu.screen_resolution is None
    assert cu.interaction_mode == "native_os"
    assert cu.allowed_actions == ["click", "type", "scroll", "screenshot"]
    assert cu.screenshot_frequency_ms == 1000

    # Test custom configuration
    cu_custom = ComputerUseReasoning(
        model="claude-3.5-sonnet",
        screen_resolution=(1920, 1080),
        interaction_mode="browser_dom",
        allowed_actions=["click", "type"],
        screenshot_frequency_ms=500,
    )
    assert cu_custom.screen_resolution == (1920, 1080)
    assert cu_custom.interaction_mode == "browser_dom"
    assert cu_custom.allowed_actions == ["click", "type"]
    assert cu_custom.screenshot_frequency_ms == 500


def test_reasoning_config_union_computer_use() -> None:
    # Use TypeAdapter to test parsing into the Union
    adapter: TypeAdapter[ReasoningConfig] = TypeAdapter(ReasoningConfig)

    data = {
        "type": "computer_use",
        "model": "gpt-4-turbo",
        "interaction_mode": "hybrid",
        "allowed_actions": ["click", "drag", "hotkey"],
    }
    parsed = adapter.validate_python(data)
    assert isinstance(parsed, ComputerUseReasoning)
    assert parsed.type == "computer_use"
    assert parsed.interaction_mode == "hybrid"
    assert "hotkey" in parsed.allowed_actions
