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
    manifest = simple_agent(
        name="Researcher",
        prompt="You are a research assistant.",
        model="gpt-4",
        tools=["search-tool"],
        knowledge=["docs/info.txt"],
        inputs={"topic": {"type": "string"}},
        outputs={"report": {"type": "string"}},
    )

    agent = manifest.definitions["Researcher"]
    assert isinstance(agent, AgentDefinition)
    assert agent.backstory == "You are a research assistant."
    assert agent.model == "gpt-4"
    # tools is now list[ToolRequirement | InlineToolDefinition]
    assert len(agent.tools) == 1
    assert hasattr(agent.tools[0], "uri")
    assert agent.tools[0].uri == "search-tool"
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
