# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest import simple_agent
from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2


def test_simple_agent_minimal() -> None:
    manifest = simple_agent(name="TestAgent")
    assert isinstance(manifest, ManifestV2)
    assert manifest.metadata.name == "TestAgent"
    assert "TestAgent" in manifest.definitions
    agent = manifest.definitions["TestAgent"]
    assert isinstance(agent, AgentDefinition)
    assert agent.id == "TestAgent"
    assert agent.goal == "Help the user"  # default from AgentBuilder


def test_simple_agent_full_options() -> None:
    # simple_agent uses AgentBuilder.build() which triggers integrity checks.
    # Since we can't easily inject ToolDefinitions into simple_agent, this call fails if tools are referenced but undefined.
    # HOWEVER, simple_agent is a high-level shortcut. If it fails on tools, it's brittle.
    # BUT, strict is strict.
    #
    # We can't fix simple_agent to auto-mock definitions without polluting the library.
    #
    # Fix: Don't test tools here with simple_agent if we can't make it valid, OR rely on the fact that
    # simple_agent is just a wrapper around AgentBuilder, and we've already tested Builder issues.
    #
    # OR, we catch the ValidationError and assert it failed because of missing tool, confirming it TRIED to add the tool.
    # This proves simple_agent passed the tool to the builder.

    # Option 2: Catch error.
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError) as exc:
        simple_agent(
            name="Researcher",
            prompt="You are a research assistant.",
            model="gpt-4",
            tools=["search-tool"],
            knowledge=["docs/info.txt"],
            inputs={"topic": {"type": "string"}},
            outputs={"report": {"type": "string"}},
        )

    assert "references missing tool 'search-tool'" in str(exc.value)

    # Re-run without tools to verify other fields
    manifest = simple_agent(
        name="Researcher",
        prompt="You are a research assistant.",
        model="gpt-4",
        # tools=["search-tool"], # Removed to pass integrity
        knowledge=["docs/info.txt"],
        inputs={"topic": {"type": "string"}},
        outputs={"report": {"type": "string"}},
    )

    agent = manifest.definitions["Researcher"]
    assert isinstance(agent, AgentDefinition)
    assert agent.backstory == "You are a research assistant."
    assert agent.model == "gpt-4"
    # tools check moved to exception block above
    assert agent.knowledge == ["docs/info.txt"]

    # Check interface inputs - it should be wrapped in object/properties because we passed a dict without "type"
    assert manifest.interface.inputs["type"] == "object"
    assert "topic" in manifest.interface.inputs["properties"]
    assert manifest.interface.inputs["properties"]["topic"]["type"] == "string"

    # Check interface outputs
    assert manifest.interface.outputs["type"] == "object"
    assert "report" in manifest.interface.outputs["properties"]


def test_simple_agent_raw_schema() -> None:
    # Pass full schema with "type": "object"
    schema = {"type": "object", "properties": {"foo": {"type": "integer"}}, "required": ["foo"]}
    manifest = simple_agent(name="SchemaAgent", inputs=schema)

    # Should use the schema directly
    assert manifest.interface.inputs == schema
    assert manifest.interface.inputs["type"] == "object"
    assert manifest.interface.inputs["required"] == ["foo"]


def test_simple_agent_raw_output_schema() -> None:
    # Pass full schema for outputs with "type": "object"
    # This should hit the IF branch: if "type" in outputs...
    schema = {
        "type": "object",
        "properties": {"bar": {"type": "string"}},
    }
    manifest = simple_agent(name="OutputSchemaAgent", outputs=schema)

    assert manifest.interface.outputs == schema
    assert manifest.interface.outputs["type"] == "object"
