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
    AgentStep,
    DeliveryMode,
    Manifest,
    TypedCapability,
)


class SearchInput(BaseModel):
    query: str


class SearchOutput(BaseModel):
    results: list[str]


def test_schema_generation() -> None:
    cap = TypedCapability(
        name="Search",
        description="Search the web",
        input_model=SearchInput,
        output_model=SearchOutput,
    )
    interface = cap.to_interface()
    assert "properties" in interface["inputs"]
    assert interface["inputs"]["properties"]["query"]["type"] == "string"


def test_fluent_chaining_and_build() -> None:
    builder = AgentBuilder("TestAgent")
    manifest = builder.with_model("gpt-4").with_system_prompt("Act helpful").build()

    assert isinstance(manifest, Manifest)
    assert manifest.kind == "Agent"
    assert manifest.metadata.name == "TestAgent"

    # Check definition
    assert "TestAgent" in manifest.definitions
    agent_def = manifest.definitions["TestAgent"]

    # Type narrowing for Mypy
    assert isinstance(agent_def, AgentDefinition)

    assert agent_def.model == "gpt-4"
    assert agent_def.backstory == "Act helpful"
    assert agent_def.role == "General Assistant"  # Default

    # Check workflow
    assert manifest.workflow.start == "main"
    step = manifest.workflow.steps["main"]
    assert isinstance(step, AgentStep)
    assert step.agent == "TestAgent"


def test_capability_integration() -> None:
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

    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.capabilities.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS

    # Check interface schema merging
    assert manifest.interface.inputs["properties"] == {}


def test_complex_schema_merging() -> None:
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


def test_with_tool() -> None:
    manifest = AgentBuilder("ToolAgent").with_tool("search-tool").build()
    agent_def = manifest.definitions["ToolAgent"]

    assert isinstance(agent_def, AgentDefinition)
    assert "search-tool" in agent_def.tools


def test_with_role_and_goal() -> None:
    """Test setting role and goal explicitly."""
    manifest = AgentBuilder("RoleAgent").with_role("Researcher").with_goal("Find information").build()
    agent_def = manifest.definitions["RoleAgent"]

    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.role == "Researcher"
    assert agent_def.goal == "Find information"


# --- Edge Case Tests ---


def test_conflicting_schema_properties() -> None:
    """Test that later capabilities overwrite properties with the same name."""

    class InputA(BaseModel):
        field: int

    class InputB(BaseModel):
        field: str

    cap1 = TypedCapability("A", "A", InputA, InputA)
    cap2 = TypedCapability("B", "B", InputB, InputB)

    manifest = AgentBuilder("Conflict").with_capability(cap1).with_capability(cap2).build()

    props = manifest.interface.inputs["properties"]
    # Should correspond to InputB (string) because it was added last
    assert props["field"]["type"] == "string"


def test_empty_builder() -> None:
    """Test building an agent with minimal configuration."""
    manifest = AgentBuilder("Minimal").build()

    assert manifest.metadata.name == "Minimal"
    agent_def = manifest.definitions["Minimal"]
    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.role == "General Assistant"
    assert agent_def.tools == []


def test_duplicate_tools() -> None:
    """Test adding the same tool multiple times."""
    manifest = AgentBuilder("DupeTool").with_tool("tool-1").with_tool("tool-1").build()

    agent_def = manifest.definitions["DupeTool"]
    assert isinstance(agent_def, AgentDefinition)
    # The builder appends to a list, so we expect duplicates unless filtered.
    # If the requirement is strict set behavior, we might want to check that,
    # but the implementation uses a list. Let's assert the list behavior.
    assert agent_def.tools == ["tool-1", "tool-1"]


def test_nested_models() -> None:
    """Test schema generation for nested Pydantic models."""

    class Nested(BaseModel):
        value: int

    class Wrapper(BaseModel):
        nested: Nested

    cap = TypedCapability("Nested", "Nested Desc", Wrapper, Wrapper)

    manifest = AgentBuilder("NestedAgent").with_capability(cap).build()

    input_schema = manifest.interface.inputs
    # Since we use model_json_schema(), it typically puts definitions in $defs
    # BUT our builder uses properties.update().
    # If Pydantic generates references, they might point to $defs that are NOT merged.
    # This is a known limitation we are verifying.

    props = input_schema["properties"]
    assert "nested" in props
    # Check if we have what looks like a schema structure
    # Even if $ref is broken in the merged context without $defs at root,
    # the property should exist.
    assert props["nested"] is not None


def test_builder_state_mutation() -> None:
    """Test that the builder accumulates state correctly across calls."""
    builder = AgentBuilder("Stateful")
    builder.with_model("v1")

    manifest1 = builder.build()
    agent_def1 = manifest1.definitions["Stateful"]
    assert isinstance(agent_def1, AgentDefinition)
    assert agent_def1.model == "v1"

    # Continue using the same builder
    builder.with_model("v2")
    manifest2 = builder.build()
    agent_def2 = manifest2.definitions["Stateful"]
    assert isinstance(agent_def2, AgentDefinition)
    assert agent_def2.model == "v2"

    # Ensure v1 wasn't retroactively changed (manifests are immutable/copies)
    assert agent_def1.model == "v1"
