# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, cast

import pytest

from coreason_manifest.spec.v2.contracts import InterfaceDefinition
from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.utils.mock import MockGenerator, generate_mock_output


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

    assert isinstance(output, dict)
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
    assert isinstance(output, dict)
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
    assert isinstance(output, dict)
    # Basic check if it looks right
    assert isinstance(output["id"], str)
    assert len(output["id"]) > 30  # UUID length
    assert "T" in cast("str", output["created_at"])
    assert "Z" in cast("str", output["created_at"])


def test_arrays() -> None:
    schema = {
        "type": "object",
        "properties": {"tags": {"type": "array", "items": {"type": "string"}}},
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output, dict)
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
    assert isinstance(output, dict)
    # Could be string or None, but likely string due to impl
    assert output["opt"] is None or isinstance(output["opt"], str)


def test_const() -> None:
    schema = {
        "type": "object",
        "properties": {"c": {"const": "fixed"}},
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output, dict)
    assert output["c"] == "fixed"


def test_any_of() -> None:
    schema = {
        "type": "object",
        "properties": {"choice": {"anyOf": [{"type": "string"}, {"type": "integer"}]}},
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output, dict)
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
    assert isinstance(output, dict)
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
    assert isinstance(output, dict)
    assert isinstance(output["base_prop"], str)
    assert isinstance(output["top_prop"], int)
    assert isinstance(output["other_prop"], bool)


def test_all_of_no_props_in_allof() -> None:
    schema = {"type": "object", "allOf": [{"required": ["a"]}], "properties": {"a": {"type": "string"}}}
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output, dict)
    assert isinstance(output["a"], str)


def test_all_of_mixed_props() -> None:
    schema = {"type": "object", "allOf": [{"required": ["a"]}, {"properties": {"a": {"type": "integer"}}}]}
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output, dict)
    assert isinstance(output["a"], int)


def test_strict_mode_unknown_type() -> None:
    schema = {"type": "unknown"}
    agent = create_agent(schema)
    with pytest.raises(ValueError, match="Unknown type"):
        generate_mock_output(agent, strict=True)


def test_strict_mode_missing_ref() -> None:
    schema = {"$ref": "#/missing"}
    agent = create_agent(schema)
    with pytest.raises(ValueError, match="Missing definition"):
        generate_mock_output(agent, strict=True)


def test_strict_mode_valid() -> None:
    schema = {"type": "string"}
    agent = create_agent(schema)
    output = generate_mock_output(agent, strict=True)
    assert isinstance(output, str)


def test_deep_merge_direct() -> None:
    gen = MockGenerator()
    base = {"required": ["a"], "properties": {"x": {"type": "integer"}}, "other": {"foo": 1}}
    update = {"required": ["b"], "properties": {"y": {"type": "string"}}, "other": {"bar": 2}}
    merged = gen._deep_merge(base, update)

    assert isinstance(merged.get("required"), list)
    assert set(merged["required"]) == {"a", "b"}

    assert isinstance(merged.get("properties"), dict)
    assert "x" in merged["properties"]
    assert "y" in merged["properties"]

    assert isinstance(merged.get("other"), dict)
    assert merged["other"]["foo"] == 1
    assert merged["other"]["bar"] == 2


def test_recursion_limit_array() -> None:
    schema = {
        "$defs": {
            "List": {
                "type": "array",
                "items": {"$ref": "#/$defs/List"},
            }
        },
        "$ref": "#/$defs/List",
    }
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output, list)
    # The list may contain other lists, but eventually it should bottom out to []
    # due to recursion limit in _generate_value calls.


def test_recursion_limit_scalar_with_ref() -> None:
    # Test reaching recursion limit for scalar types via cyclic refs to hit _get_safe_default branches
    types = [
        ("string", str, ""),
        ("integer", int, 0),
        ("number", float, 0.0),
        ("boolean", bool, False),
    ]

    for type_name, py_type, expected_default in types:
        schema = {
            "$defs": {"Rec": {"type": type_name, "$ref": "#/$defs/Rec"}},
            "$ref": "#/$defs/Rec",
        }

        agent = create_agent(schema)
        output = generate_mock_output(agent)
        assert isinstance(output, py_type)
        assert output == expected_default


def test_strict_recursion_fallback() -> None:
    schema = {"$defs": {"Rec": {"type": "unknown", "$ref": "#/$defs/Rec"}}, "$ref": "#/$defs/Rec"}

    agent = create_agent(schema)
    with pytest.raises(ValueError, match="Cannot determine safe default"):
        generate_mock_output(agent, strict=True)


def test_recursion_limit_union() -> None:
    # Recursion with union types to hit _get_safe_default union branch
    schema = {
        "$defs": {"RecUnion": {"type": ["string", "null"], "$ref": "#/$defs/RecUnion"}},
        "$ref": "#/$defs/RecUnion",
    }
    agent = create_agent(schema)
    # Should resolve to string or None, but safe default prefers string ("")
    # or if it picks null (unlikely due to prioritize non-null), None.
    # _get_safe_default(union) -> picks non-null -> "string" -> ""
    output = generate_mock_output(agent)
    assert output == "" or output is None


def test_deep_merge_nested_properties() -> None:
    gen = MockGenerator()
    base = {"properties": {"nest": {"properties": {"a": {"type": "int"}}}}}
    update = {"properties": {"nest": {"properties": {"b": {"type": "str"}}}}}
    merged = gen._deep_merge(base, update)

    assert isinstance(merged.get("properties"), dict)
    assert isinstance(merged["properties"].get("nest"), dict)
    assert isinstance(merged["properties"]["nest"].get("properties"), dict)
    assert "a" in merged["properties"]["nest"]["properties"]
    assert "b" in merged["properties"]["nest"]["properties"]


def test_invalid_constraints_correction() -> None:
    # Test string: maxLength < minLength
    schema_str = {"type": "string", "minLength": 25}  # Default maxLength is 20
    agent = create_agent(schema_str)
    out_str = generate_mock_output(agent)
    assert isinstance(out_str, str)
    assert len(out_str) >= 25

    # Test int: maximum < minimum
    schema_int = {"type": "integer", "minimum": 150}  # Default maximum is 100
    agent = create_agent(schema_int)
    out_int = generate_mock_output(agent)
    assert isinstance(out_int, int)
    assert out_int >= 150

    # Test float: maximum < minimum
    schema_float = {"type": "number", "minimum": 150.0}  # Default maximum is 100.0
    agent = create_agent(schema_float)
    out_float = generate_mock_output(agent)
    assert isinstance(out_float, float)
    assert out_float >= 150.0


def test_fallback_safe_default_unknown_type() -> None:
    # Coverage for _get_safe_default with unknown type (strict=False)
    gen = MockGenerator(strict=False)
    default = gen._get_safe_default({"type": "unknown-type"})
    assert default == {}


def test_strict_fallback_safe_default_unknown_type() -> None:
    # Coverage for _get_safe_default with unknown type (strict=True)
    # This might be redundant with test_strict_recursion_fallback but let's be explicit
    # to target the specific line in _get_safe_default
    gen = MockGenerator(strict=True)
    with pytest.raises(ValueError, match="Cannot determine safe default"):
        gen._get_safe_default({"type": "unknown-type"})


def test_heuristic_object_type() -> None:
    # Coverage for heuristic: properties -> object
    schema = {"properties": {"a": {"type": "string"}}}
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output, dict)
    assert "a" in output
    assert isinstance(output["a"], str)


def test_heuristic_array_type() -> None:
    # Coverage for heuristic: items -> array
    schema = {"items": {"type": "string"}}
    agent = create_agent(schema)
    output = generate_mock_output(agent)
    assert isinstance(output, list)
    if output:
        assert isinstance(output[0], str)


def test_safe_default_null_type() -> None:
    # Coverage for _get_safe_default with type="null"
    gen = MockGenerator(strict=False)
    default = gen._get_safe_default({"type": "null"})
    assert default is None
