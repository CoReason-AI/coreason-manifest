# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime
from uuid import uuid4

from coreason_manifest.utils.mock import MockGenerator


def test_mock_recursion_dos_fix() -> None:
    """
    Verifies that nested allOf structures with cyclic references do not cause
    Infinite Recursion / Stack Overflow.
    """
    # Schema with allOf loop: A -> B -> A
    definitions = {
        "A": {"allOf": [{"$ref": "#/$defs/B"}, {"properties": {"a": {"type": "string"}}}]},
        "B": {"allOf": [{"$ref": "#/$defs/A"}, {"properties": {"b": {"type": "integer"}}}]},
    }

    schema = {"$ref": "#/$defs/A"}

    gen = MockGenerator(definitions=definitions)

    # This call should not crash.
    # It should hit max depth and return a safe default (likely {})
    val = gen._generate_value(schema)

    assert isinstance(val, dict)
    # We don't strictly assert the content because it's truncated by recursion limit,
    # but it should return a valid python object.


def test_mock_safe_defaults() -> None:
    """
    Verifies that MockGenerator returns safe defaults when recursion limit is reached,
    instead of None (which might violate schema).
    """
    # Force max_depth to -1 to trigger limit immediately
    gen = MockGenerator()
    gen.max_depth = -1

    assert gen._generate_value({"type": "string"}) == ""
    assert gen._generate_value({"type": "integer"}) == 0
    assert gen._generate_value({"type": "number"}) == 0.0
    assert gen._generate_value({"type": "boolean"}) is False
    assert gen._generate_value({"type": "array"}) == []
    assert gen._generate_value({"type": "object"}) == {}

    # Union types
    assert gen._generate_value({"type": ["string", "null"]}) == ""
    assert gen._generate_value({"type": ["integer", "null"]}) == 0
    # Union with all nulls or empty (fallback to object -> {})
    assert gen._generate_value({"type": ["null"]}) == {}
