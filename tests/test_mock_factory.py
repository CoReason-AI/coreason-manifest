# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

from coreason_manifest.spec.v2.contracts import InterfaceDefinition
from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.utils.mock import generate_mock_output


def create_agent(outputs_schema: dict[str, Any]) -> AgentDefinition:
    return AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Test",
        interface=InterfaceDefinition(outputs=outputs_schema),
    )


def test_scalar_generation() -> None:
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "active": {"type": "boolean"},
            "score": {"type": "number"},
        },
        "required": ["name", "age", "active", "score"],
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)

    assert isinstance(output, dict)
    assert isinstance(output["name"], str)
    assert isinstance(output["age"], int)
    assert isinstance(output["active"], bool)
    assert isinstance(output["score"], float)


def test_determinism() -> None:
    schema = {
        "type": "object",
        "properties": {"val": {"type": "string"}},
    }
    agent = create_agent(schema)

    out1 = generate_mock_output(agent, seed=42)
    out2 = generate_mock_output(agent, seed=42)
    out3 = generate_mock_output(agent, seed=43)

    assert out1 == out2
    assert out1 != out3


def test_nested_refs() -> None:
    schema = {
        "$defs": {
            "Address": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "zip": {"type": "integer"},
                },
            }
        },
        "type": "object",
        "properties": {
            "employee": {"type": "string"},
            "address": {"$ref": "#/$defs/Address"},
        },
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)

    assert isinstance(output["address"], dict)
    assert isinstance(output["address"]["city"], str)
    assert isinstance(output["address"]["zip"], int)


def test_enum_constraints() -> None:
    schema = {
        "type": "object",
        "properties": {"status": {"type": "string", "enum": ["OPEN", "CLOSED"]}},
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert output["status"] in ["OPEN", "CLOSED"]


def test_formats() -> None:
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "created_at": {"type": "string", "format": "date-time"},
        },
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    # Basic check if it looks right
    assert isinstance(output["id"], str)
    assert len(output["id"]) > 30  # UUID length
    assert "T" in output["created_at"]
    assert "Z" in output["created_at"]


def test_arrays() -> None:
    schema = {
        "type": "object",
        "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output["tags"], list)
    if output["tags"]:
        assert isinstance(output["tags"][0], str)


def test_nullable_union() -> None:
    schema = {
        "type": "object",
        "properties": {"opt": {"type": ["string", "null"]}},
    }
    agent = create_agent(schema)
    # It prefers non-null in my implementation
    output = generate_mock_output(agent)
    # Could be string or None, but likely string due to impl
    assert output["opt"] is None or isinstance(output["opt"], str)


def test_const() -> None:
    schema = {
        "type": "object",
        "properties": {"c": {"const": "fixed"}},
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert output["c"] == "fixed"


def test_any_of() -> None:
    schema = {
        "type": "object",
        "properties": {"choice": {"anyOf": [{"type": "string"}, {"type": "integer"}]}},
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output["choice"], (str, int))


def test_all_of() -> None:
    schema = {
        "type": "object",
        "allOf": [
            {"properties": {"a": {"type": "integer"}}},
            {"properties": {"b": {"type": "string"}}},
        ],
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output.get("a"), int)
    assert isinstance(output.get("b"), str)


def test_recursion_limit() -> None:
    schema = {
        "$defs": {
            "Node": {
                "type": "object",
                "properties": {"child": {"$ref": "#/$defs/Node"}},
            }
        },
        "$ref": "#/$defs/Node",
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    # Should stop eventually and return None or something manageable
    # We just want to ensure it doesn't crash with RecursionError
    assert isinstance(output, dict)


def test_missing_ref() -> None:
    schema = {"$ref": "#/missing"}
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert output == {}


def test_definitions_fallback() -> None:
    # Test definitions key instead of $defs
    schema = {
        "definitions": {"MyType": {"type": "string"}},
        "$ref": "#/definitions/MyType",
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output, str)


def test_unknown_type_and_fallback() -> None:
    schema = {"type": "unknown"}
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert output == {}

    schema2 = {"type": "null"}
    agent2 = create_agent(schema2)
    output2 = generate_mock_output(agent2)
    assert output2 is None

    schema3 = {"type": ["null"]}
    agent3 = create_agent(schema3)
    output3 = generate_mock_output(agent3)
    assert output3 is None


def test_all_of_with_ref_and_top_properties() -> None:
    schema = {
        "$defs": {"Base": {"properties": {"base_prop": {"type": "string"}}}},
        "type": "object",
        "properties": {"top_prop": {"type": "integer"}},
        "allOf": [{"$ref": "#/$defs/Base"}, {"properties": {"other_prop": {"type": "boolean"}}}],
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output["base_prop"], str)
    assert isinstance(output["top_prop"], int)
    assert isinstance(output["other_prop"], bool)


def test_all_of_no_props_in_allof() -> None:
    schema = {"type": "object", "allOf": [{"required": ["a"]}], "properties": {"a": {"type": "string"}}}
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output["a"], str)


def test_all_of_mixed_props() -> None:
    schema = {"type": "object", "allOf": [{"required": ["a"]}, {"properties": {"a": {"type": "integer"}}}]}
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output["a"], int)
