# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from pydantic import BaseModel

from coreason_manifest import (
    AgentBuilder,
    AgentDefinition,
    DeliveryMode,
    Manifest,
    TypedCapability,
)


class SearchInput(BaseModel):
    query: str


class SearchOutput(BaseModel):
    results: list[str]


def test_schema_generation():
    cap = TypedCapability(
        name="Search", description="Search the web", input_model=SearchInput, output_model=SearchOutput
    )
    interface = cap.to_interface()
    assert "properties" in interface["inputs"]
    assert interface["inputs"]["properties"]["query"]["type"] == "string"


def test_fluent_chaining_and_build():
    builder = AgentBuilder("TestAgent")
    manifest = builder.with_model("gpt-4").with_system_prompt("Act helpful").build()

    assert isinstance(manifest, Manifest)
    assert manifest.kind == "Agent"
    assert manifest.metadata.name == "TestAgent"

    # Check definition
    assert "TestAgent" in manifest.definitions
    agent_def = manifest.definitions["TestAgent"]
    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.model == "gpt-4"
    assert agent_def.backstory == "Act helpful"
    assert agent_def.role == "General Assistant"  # Default

    # Check workflow
    assert manifest.workflow.start == "main"
    assert manifest.workflow.steps["main"].agent == "TestAgent"


def test_capability_integration():
    class Empty(BaseModel):
        pass

    cap = TypedCapability(
        name="Stream",
        description="Stream stuff",
        input_model=Empty,
        output_model=Empty,
        delivery_mode=DeliveryMode.SERVER_SENT_EVENTS,
    )

    manifest = AgentBuilder("StreamAgent").with_capability(cap).build()
    agent_def = manifest.definitions["StreamAgent"]

    assert agent_def.capabilities.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS

    # Check interface schema merging
    assert manifest.interface.inputs["properties"] == {}


def test_complex_schema_merging():
    class InputA(BaseModel):
        a: int

    class InputB(BaseModel):
        b: str

    cap1 = TypedCapability("A", "A", InputA, InputA)
    cap2 = TypedCapability("B", "B", InputB, InputB)

    manifest = AgentBuilder("Complex").with_capability(cap1).with_capability(cap2).build()

    props = manifest.interface.inputs["properties"]
    assert "a" in props
    assert "b" in props
    assert props["a"]["type"] == "integer"
    assert props["b"]["type"] == "string"


def test_with_tool():
    manifest = AgentBuilder("ToolAgent").with_tool("search-tool").build()
    agent_def = manifest.definitions["ToolAgent"]
    assert "search-tool" in agent_def.tools
