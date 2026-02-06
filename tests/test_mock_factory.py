# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.contracts import InterfaceDefinition
from coreason_manifest.spec.v2.definitions import AgentDefinition
from coreason_manifest.utils.mock import generate_mock_output


def test_scalar_generation() -> None:
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "active": {"type": "boolean"},
            "score": {"type": "number"},
        },
    }

    agent = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Test things",
        interface=InterfaceDefinition(outputs=schema),
    )

    output = generate_mock_output(agent)

    assert isinstance(output["name"], str)
    assert isinstance(output["age"], int)
    assert isinstance(output["active"], bool)
    assert isinstance(output["score"], float)


def test_determinism() -> None:
    schema = {"type": "object", "properties": {"random_val": {"type": "integer"}}}

    agent = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Test things",
        interface=InterfaceDefinition(outputs=schema),
    )

    out1 = generate_mock_output(agent, seed=42)
    out2 = generate_mock_output(agent, seed=42)
    out3 = generate_mock_output(agent, seed=99)

    assert out1 == out2
    assert out1 != out3


def test_complex_nesting_and_refs() -> None:
    schema = {
        "$defs": {
            "Address": {"type": "object", "properties": {"city": {"type": "string"}, "zip": {"type": "integer"}}}
        },
        "type": "object",
        "properties": {"employee": {"type": "string"}, "address": {"$ref": "#/$defs/Address"}},
    }

    agent = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Test things",
        interface=InterfaceDefinition(outputs=schema),
    )

    output = generate_mock_output(agent, seed=123)

    assert isinstance(output["employee"], str)
    assert isinstance(output["address"], dict)
    assert isinstance(output["address"]["city"], str)
    assert isinstance(output["address"]["zip"], int)


def test_enum_constraints() -> None:
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["OPEN", "CLOSED"]},
            "priority": {"type": "integer", "enum": [1, 2, 3]},
        },
    }

    agent = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Test things",
        interface=InterfaceDefinition(outputs=schema),
    )

    # Check multiple times to ensure coverage (probabilistic but good enough with fixed seed)
    output = generate_mock_output(agent, seed=555)

    assert output["status"] in ["OPEN", "CLOSED"]
    assert output["priority"] in [1, 2, 3]


def test_special_formats() -> None:
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "created_at": {"type": "string", "format": "date-time"},
        },
    }

    agent = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="Test things",
        interface=InterfaceDefinition(outputs=schema),
    )

    output = generate_mock_output(agent, seed=101)

    # Verify UUID format (basic check)
    assert len(output["id"]) == 36
    assert "-" in output["id"]

    # Verify ISO format
    # Will throw ValueError if not ISO format
    from datetime import datetime

    dt = datetime.fromisoformat(output["created_at"])
    assert dt is not None


def test_coverage_edge_cases() -> None:
    # 1. Empty schema
    agent_empty = AgentDefinition(
        id="test-empty",
        name="Empty",
        role="Tester",
        goal="Coverage",
        interface=InterfaceDefinition(outputs={}),
    )
    assert generate_mock_output(agent_empty) == {}

    # 2. Ref not found
    schema_bad_ref = {"type": "object", "properties": {"bad": {"$ref": "#/defs/Missing"}}}
    agent_bad_ref = AgentDefinition(
        id="test-bad-ref",
        name="Bad Ref",
        role="Tester",
        goal="Coverage",
        interface=InterfaceDefinition(outputs=schema_bad_ref),
    )
    # Should resolve to {}, so bad key is {}
    output_bad_ref = generate_mock_output(agent_bad_ref)
    assert output_bad_ref["bad"] == {}

    # 3. Unknown type
    schema_unknown = {"type": "object", "properties": {"weird": {"type": "unsupported_type"}}}
    agent_unknown = AgentDefinition(
        id="test-unknown",
        name="Unknown",
        role="Tester",
        goal="Coverage",
        interface=InterfaceDefinition(outputs=schema_unknown),
    )
    output_unknown = generate_mock_output(agent_unknown)
    # The implementation returns None for unknown types
    assert output_unknown["weird"] is None

    # 4. Result not a dict
    # If top level is an array, it returns [], which fails isinstance(result, dict) check in wrapper
    schema_array = {"type": "array", "items": {"type": "string"}}
    agent_array = AgentDefinition(
        id="test-array",
        name="Array",
        role="Tester",
        goal="Coverage",
        interface=InterfaceDefinition(outputs=schema_array),
    )
    # The wrapper function forces return type dict, so it returns {} if generator returns list
    assert generate_mock_output(agent_array) == {}


def test_nullable_types() -> None:
    # Handle type: ["string", "null"]
    schema = {
        "type": "object",
        "properties": {
            "maybe_null": {"type": ["string", "null"]},
            "forced_null": {"type": "null"},
        },
    }
    agent = AgentDefinition(
        id="test-null",
        name="Null",
        role="Tester",
        goal="Test Null",
        interface=InterfaceDefinition(outputs=schema),
    )
    output = generate_mock_output(agent, seed=42)
    # With seed 42, rng.choice(["string"]) should pick "string"
    assert isinstance(output["maybe_null"], str)
    assert output["forced_null"] is None


def test_circular_ref_handling() -> None:
    schema = {
        "$defs": {
            "Node": {
                "type": "object",
                "properties": {
                    "value": {"type": "integer"},
                    "next": {"$ref": "#/$defs/Node"},
                },
            }
        },
        "type": "object",
        "properties": {"root": {"$ref": "#/$defs/Node"}},
    }
    agent = AgentDefinition(
        id="test-circular",
        name="Circular",
        role="Tester",
        goal="Test Circular",
        interface=InterfaceDefinition(outputs=schema),
    )
    # Should not crash, but stop at max depth
    output = generate_mock_output(agent)

    # Traverse to verify depth limit
    curr = output["root"]
    depth = 0
    while curr and "next" in curr:
        curr = curr["next"]
        depth += 1
        if depth > 20:
            break

    assert depth <= 12  # 10 is default max depth, +1 or 2 for root level


def test_const_value() -> None:
    schema = {
        "type": "object",
        "properties": {
            "fixed": {"const": "always_this_value"},
            "fixed_int": {"const": 42},
        },
    }
    agent = AgentDefinition(
        id="test-const",
        name="Const",
        role="Tester",
        goal="Test Const",
        interface=InterfaceDefinition(outputs=schema),
    )
    output = generate_mock_output(agent)
    assert output["fixed"] == "always_this_value"
    assert output["fixed_int"] == 42


def test_complex_nested_schema() -> None:
    schema = {
        "$defs": {
            "Item": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
            }
        },
        "type": "object",
        "properties": {
            "meta": {
                "type": "object",
                "properties": {
                    "version": {"const": "1.0"},
                    "timestamp": {"type": "string", "format": "date-time"},
                },
            },
            "data": {
                "type": "array",
                "items": {"$ref": "#/$defs/Item"},
            },
            "status": {"type": "string", "enum": ["ok", "error"]},
        },
    }
    agent = AgentDefinition(
        id="test-complex",
        name="Complex",
        role="Tester",
        goal="Test Complex",
        interface=InterfaceDefinition(outputs=schema),
    )

    output = generate_mock_output(agent, seed=999)

    assert output["meta"]["version"] == "1.0"
    assert isinstance(output["data"], list)
    if output["data"]:
        item = output["data"][0]
        assert "id" in item
        assert isinstance(item["tags"], list)
    assert output["status"] in ["ok", "error"]
