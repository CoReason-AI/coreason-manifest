# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict

import jsonschema
import pytest

from coreason_manifest.builder.agent import AgentBuilder
from coreason_manifest.definitions.agent import AgentCapability, CapabilityType, DeliveryMode


# Helper class to bypass strict Pydantic model requirement of TypedCapability
class RawCapability:
    def __init__(self, name: str, input_schema: Dict[str, Any]):
        self.name = name
        self.input_schema = input_schema
        self.output_schema = {"type": "object"}  # Dummy output schema

    def to_definition(self) -> AgentCapability:
        return AgentCapability(
            name=self.name,
            type=CapabilityType.ATOMIC,
            description="Test capability",
            inputs=self.input_schema,
            outputs=self.output_schema,
            delivery_mode=DeliveryMode.REQUEST_RESPONSE,
        )


def test_dry_run_validation() -> None:
    # 1. Test Setup
    # Create an AgentDefinition using AgentBuilder.
    builder = AgentBuilder(name="TestAgent")

    # Add a capability named "search" with inputs:
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1}},
        "required": ["query"],
    }

    # Use RawCapability to inject the raw schema
    # We ignore the type hint error because we are intentionally mocking TypedCapability
    builder.with_capability(RawCapability("search", schema))

    agent = builder.build()

    # 2. Test Cases

    # test_valid_input: Pass {"query": "hello", "limit": 5}. Assert validate_input returns True.
    assert agent.validate_input("search", {"query": "hello", "limit": 5}) is True

    # test_invalid_type: Pass {"query": 123}. Assert it raises jsonschema.ValidationError.
    with pytest.raises(jsonschema.ValidationError):
        agent.validate_input("search", {"query": 123})

    # test_missing_required: Pass {"limit": 5}. Assert it raises jsonschema.ValidationError.
    with pytest.raises(jsonschema.ValidationError):
        agent.validate_input("search", {"limit": 5})

    # test_unknown_capability: Call with capability_name="flight_booker". Assert it raises ValueError.
    with pytest.raises(ValueError, match="Capability 'flight_booker' not found"):
        agent.validate_input("flight_booker", {"query": "foo"})
