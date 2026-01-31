# Copyright (c) 2025 CoReason, Inc.

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_manifest.recipes import RecipeInterface, StateDefinition


def test_recipe_interface_valid() -> None:
    """Test creating a valid RecipeInterface."""
    interface = RecipeInterface(
        inputs={"type": "object", "properties": {"query": {"type": "string"}}},
        outputs={"type": "object", "properties": {"answer": {"type": "string"}}},
    )
    assert interface.inputs["type"] == "object"
    assert interface.outputs["type"] == "object"


def test_recipe_interface_invalid_missing_fields() -> None:
    """Test validation failure for missing fields in RecipeInterface."""
    with pytest.raises(ValidationError):
        # type: ignore[call-arg]
        RecipeInterface(inputs={})


def test_state_definition_valid_defaults() -> None:
    """Test creating a valid StateDefinition with defaults."""
    state = StateDefinition(schema={"type": "object", "properties": {"messages": {"type": "array"}}})
    assert state.schema_["type"] == "object"
    assert state.persistence == "ephemeral"


def test_state_definition_valid_persistent() -> None:
    """Test creating a valid StateDefinition with persistence."""
    state = StateDefinition(
        schema={"type": "object", "properties": {"messages": {"type": "array"}}},
        persistence="persistent",
    )
    assert state.persistence == "persistent"


def test_state_definition_invalid_persistence() -> None:
    """Test validation failure for invalid persistence value."""
    with pytest.raises(ValidationError):
        StateDefinition(
            schema={"type": "object"},
            persistence="invalid_value",  # type: ignore[arg-type]
        )
