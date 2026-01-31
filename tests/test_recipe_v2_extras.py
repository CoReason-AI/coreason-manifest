# Copyright (c) 2025 CoReason, Inc.

import json
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_manifest import RecipeManifest, Topology
from coreason_manifest.recipes import RecipeInterface, StateDefinition


def test_state_schema_aliasing_roundtrip() -> None:
    """Test that 'schema' input maps to 'schema_' and serializes back to 'schema'."""
    state_input = {
        "schema": {"foo": "bar"},
        "persistence": "ephemeral"
    }

    # 1. Input Mapping
    state = StateDefinition(**state_input)
    assert state.schema_ == {"foo": "bar"}
    # Note: Pydantic v2 might expose the alias as an attribute depending on configuration
    # or if it shadows a method. We primarily care that schema_ is populated correctly.

    # 2. Serialization Mapping
    dump = state.model_dump(by_alias=True)
    assert "schema" in dump
    assert dump["schema"] == {"foo": "bar"}

    # 3. Roundtrip via Manifest
    manifest = RecipeManifest(
        id="r1", version="1.0.0", name="n",
        interface=RecipeInterface(inputs={}, outputs={}),
        state=state,
        parameters={},
        graph=Topology(nodes=[], edges=[])
    )
    json_str = manifest.model_dump_json(by_alias=True)
    reloaded = RecipeManifest.model_validate_json(json_str)
    assert reloaded.state.schema_ == {"foo": "bar"}


def test_empty_interface_and_state() -> None:
    """Test that empty but valid objects are accepted."""
    manifest = RecipeManifest(
        id="empty-v2",
        version="1.0.0",
        name="Empty",
        interface=RecipeInterface(inputs={}, outputs={}),
        state=StateDefinition(schema={}, persistence="ephemeral"),
        parameters={},
        graph=Topology(nodes=[], edges=[])
    )
    assert manifest.interface.inputs == {}
    assert manifest.state.schema_ == {}


def test_complex_parameters() -> None:
    """Test parameters with nested complex types."""
    params = {
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.7,
            "stops": ["\n", "User:"]
        },
        "retries": 3,
        "features": ["logging", "monitoring"]
    }

    manifest = RecipeManifest(
        id="complex-params",
        version="1.0.0",
        name="Complex",
        interface=RecipeInterface(inputs={}, outputs={}),
        state=StateDefinition(schema={}, persistence="ephemeral"),
        parameters=params,
        graph=Topology(nodes=[], edges=[])
    )

    assert manifest.parameters["llm_config"]["model"] == "gpt-4"
    assert manifest.parameters["features"][0] == "logging"


def test_persistence_literal_strictness() -> None:
    """Test that persistence validation is case-sensitive and strict."""
    # Valid
    StateDefinition(schema={}, persistence="ephemeral")
    StateDefinition(schema={}, persistence="persistent")

    # Invalid Case
    with pytest.raises(ValidationError) as excinfo:
        StateDefinition(schema={}, persistence="Ephemeral") # type: ignore[arg-type]
    assert "Input should be 'ephemeral' or 'persistent'" in str(excinfo.value)

    # Invalid Value
    with pytest.raises(ValidationError) as excinfo:
        StateDefinition(schema={}, persistence="in-memory") # type: ignore[arg-type]
    assert "Input should be 'ephemeral' or 'persistent'" in str(excinfo.value)


def test_interface_schema_structure_preservation() -> None:
    """Test that nested JSON Schema structures in interface are preserved exactly."""
    complex_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "billing_address": {"$ref": "#/definitions/address"},
            "shipping_address": {"$ref": "#/definitions/address"}
        },
        "definitions": {
            "address": {
                "type": "object",
                "properties": {
                    "street_address": { "type": "string" },
                    "city":           { "type": "string" },
                    "state":          { "type": "string" }
                },
                "required": ["street_address", "city", "state"]
            }
        }
    }

    interface = RecipeInterface(inputs=complex_schema, outputs={})

    # Verify deep nesting
    assert interface.inputs["definitions"]["address"]["required"] == ["street_address", "city", "state"]
    assert interface.inputs["properties"]["billing_address"]["$ref"] == "#/definitions/address"
