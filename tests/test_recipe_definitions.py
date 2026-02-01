# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

# Copyright (c) 2025 CoReason, Inc.

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.topology import StateDefinition
from coreason_manifest.recipes import RecipeInterface


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
        RecipeInterface(inputs={})  # type: ignore[call-arg]


def test_state_definition_valid_defaults() -> None:
    """Test creating a valid StateDefinition with defaults."""
    state = StateDefinition(schema_={"type": "object", "properties": {"messages": {"type": "array"}}})
    assert state.schema_["type"] == "object"
    assert state.persistence == "ephemeral"


def test_state_definition_valid_persistent() -> None:
    """Test creating a valid StateDefinition with persistence."""
    state = StateDefinition(
        schema_={"type": "object", "properties": {"messages": {"type": "array"}}},
        persistence="persistent",
    )
    assert state.persistence == "persistent"


def test_state_definition_invalid_persistence() -> None:
    """Test validation failure for invalid persistence value."""
    with pytest.raises(ValidationError):
        StateDefinition(
            schema_={"type": "object"},
            persistence="invalid_value",
        )
