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
