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

from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    CollaborationConfig,
    CollaborationMode,
    PresentationHints,
    VisualizationStyle,
)


def test_presentation_hints_defaults() -> None:
    """Test defaults for PresentationHints."""
    hints = PresentationHints()
    assert hints.style == VisualizationStyle.CHAT
    assert hints.display_title is None
    assert hints.icon is None
    assert hints.hidden_fields == []
    assert hints.progress_indicator is None


def test_presentation_hints_invalid_style() -> None:
    """Test invalid style enum value."""
    with pytest.raises(ValidationError) as excinfo:
        PresentationHints(style="INVALID_STYLE")  # type: ignore[arg-type]
    assert "Input should be 'CHAT', 'TREE', 'KANBAN' or 'DOCUMENT'" in str(excinfo.value)


def test_presentation_hints_empty_hidden_fields() -> None:
    """Test explicit empty list for hidden_fields."""
    hints = PresentationHints(hidden_fields=[])
    assert hints.hidden_fields == []


def test_presentation_hints_special_chars_title() -> None:
    """Test display_title with special characters."""
    title = "My Node: 🚀 & (Special)"
    hints = PresentationHints(display_title=title)
    assert hints.display_title == title


def test_collaboration_config_defaults() -> None:
    """Test defaults for CollaborationConfig."""
    config = CollaborationConfig()
    assert config.mode == CollaborationMode.COMPLETION
    assert config.feedback_schema is None
    assert config.supported_commands == []


def test_collaboration_config_invalid_mode() -> None:
    """Test invalid mode enum value."""
    with pytest.raises(ValidationError) as excinfo:
        CollaborationConfig(mode="INVALID_MODE")  # type: ignore[arg-type]
    assert "Input should be 'COMPLETION', 'INTERACTIVE' or 'CO_EDIT'" in str(excinfo.value)


def test_collaboration_config_complex_feedback_schema() -> None:
    """Test feedback_schema with nested structure."""
    schema = {
        "type": "object",
        "properties": {
            "rating": {"type": "integer", "minimum": 1, "maximum": 5},
            "comments": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
    config = CollaborationConfig(feedback_schema=schema)
    assert config.feedback_schema == schema


def test_collaboration_config_empty_commands() -> None:
    """Test explicit empty list for supported_commands."""
    config = CollaborationConfig(supported_commands=[])
    assert config.supported_commands == []


def test_node_integration_missing_optional_fields() -> None:
    """Test AgentNode with minimal PresentationHints and CollaborationConfig."""
    node = AgentNode(
        id="test-node",
        agent_ref="ref",
        presentation=PresentationHints(),
        collaboration=CollaborationConfig()
    )
    assert node.presentation is not None
    assert node.presentation.style == VisualizationStyle.CHAT
    assert node.collaboration is not None
    assert node.collaboration.mode == CollaborationMode.COMPLETION
