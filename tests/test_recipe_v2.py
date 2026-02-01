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

import json

import pytest
from pydantic import ValidationError

from coreason_manifest import RecipeManifest, Topology
from coreason_manifest.recipes import RecipeInterface, StateDefinition


def test_full_recipe_v2_creation() -> None:
    """Test creating a fully populated V2 RecipeManifest."""
    interface = RecipeInterface(
        inputs={
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": ["topic"],
        },
        outputs={
            "type": "object",
            "properties": {"summary": {"type": "string"}},
        },
    )

    state = StateDefinition(
        schema_={
            "type": "object",
            "properties": {
                "messages": {"type": "array"},
                "artifacts": {"type": "array"},
            },
        },
        persistence="persistent",
    )

    parameters = {"model": "gpt-4", "max_tokens": 1000}

    manifest = RecipeManifest(
        id="recipe-v2",
        version="2.0.0",
        name="Research Agent",
        description="An autonomous research agent.",
        interface=interface,
        state=state,
        parameters=parameters,
        topology=Topology(nodes=[], edges=[]),
    )

    assert manifest.interface.inputs["properties"]["topic"]["type"] == "string"
    assert manifest.state.schema_["properties"]["messages"]["type"] == "array"
    assert manifest.state.persistence == "persistent"
    assert manifest.parameters["model"] == "gpt-4"


def test_recipe_v2_serialization() -> None:
    """Test that V2 RecipeManifest serializes correctly (with aliases)."""
    manifest = RecipeManifest(
        id="recipe-v2",
        version="2.0.0",
        name="Research Agent",
        interface=RecipeInterface(inputs={}, outputs={}),
        state=StateDefinition(schema_={"foo": "bar"}, persistence="ephemeral"),
        parameters={},
        topology=Topology(nodes=[], edges=[]),
    )

    # Must use by_alias=True to get "schema" instead of "schema_"
    json_output = manifest.model_dump_json(by_alias=True)
    data = json.loads(json_output)

    assert "interface" in data
    assert "state" in data
    assert "parameters" in data

    # Check state schema alias
    assert "schema" in data["state"]
    assert "schema_" not in data["state"]
    assert data["state"]["schema"] == {"foo": "bar"}


def test_recipe_v2_validation_error() -> None:
    """Test validation errors for missing new fields."""
    # Missing interface
    with pytest.raises(ValidationError) as excinfo:
        RecipeManifest(
            id="r1",
            version="1.0.0",
            name="n",
            # interface missing
            state=StateDefinition(schema_={}, persistence="ephemeral"),
            parameters={},
            topology=Topology(nodes=[], edges=[]),
        )  # type: ignore[call-arg]
    assert "interface" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)

    # Missing state
    with pytest.raises(ValidationError) as excinfo:
        RecipeManifest(
            id="r1",
            version="1.0.0",
            name="n",
            interface=RecipeInterface(inputs={}, outputs={}),
            # state missing
            parameters={},
            topology=Topology(nodes=[], edges=[]),
        )  # type: ignore[call-arg]
    assert "state" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)


def test_recipe_v2_extra_fields() -> None:
    """Test that extra fields are forbidden in V2 manifest."""
    with pytest.raises(ValidationError) as excinfo:
        RecipeManifest(
            id="r1",
            version="1.0.0",
            name="n",
            interface=RecipeInterface(inputs={}, outputs={}),
            state=StateDefinition(schema_={}, persistence="ephemeral"),
            parameters={},
            topology=Topology(nodes=[], edges=[]),
            extra_field="fail",  # type: ignore[call-arg]
        )
    assert "Extra inputs are not permitted" in str(excinfo.value)
