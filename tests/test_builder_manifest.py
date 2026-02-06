# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import BaseModel
from coreason_manifest.builder import AgentBuilder, ManifestBuilder
from coreason_manifest.spec.v2.definitions import (
    AgentStep,
    LogicStep,
    SwitchStep,
    ToolDefinition,
    GenericDefinition,
)
from coreason_manifest.spec.v2.contracts import PolicyDefinition, StateDefinition, InterfaceDefinition
from coreason_manifest.spec.common_base import StrictUri

def test_manifest_builder_simple() -> None:
    # Build a simple agent definition using AgentBuilder
    agent_def = AgentBuilder("Agent1").with_system_prompt("Hello").build_definition()

    # Use ManifestBuilder
    manifest = (
        ManifestBuilder("SimpleManifest")
        .add_agent(agent_def)
        .add_step(AgentStep(id="step1", agent="Agent1"))
        .set_start_step("step1")
        .build()
    )

    assert manifest.metadata.name == "SimpleManifest"
    assert "Agent1" in manifest.definitions
    assert manifest.workflow.start == "step1"
    assert "step1" in manifest.workflow.steps

def test_manifest_builder_complex_workflow() -> None:
    agent1 = AgentBuilder("Agent1").build_definition()
    agent2 = AgentBuilder("Agent2").build_definition()

    manifest = (
        ManifestBuilder("ComplexWorkflow", kind="Recipe")
        .add_agent(agent1)
        .add_agent(agent2)
        .add_step(AgentStep(id="step1", agent="Agent1", next="step2"))
        .add_step(AgentStep(id="step2", agent="Agent2", next="step3"))
        .add_step(LogicStep(id="step3", code="print('done')", next=None))
        .set_start_step("step1")
        .build()
    )

    assert len(manifest.definitions) == 2
    assert len(manifest.workflow.steps) == 3
    assert manifest.workflow.steps["step1"].next == "step2"

def test_manifest_builder_policy_state() -> None:
    policy = PolicyDefinition(max_steps=10, human_in_the_loop=True)
    state = StateDefinition(backend="redis")

    manifest = (
        ManifestBuilder("PolicyManifest")
        .add_step(LogicStep(id="start", code="pass"))
        .set_policy(policy)
        .set_state(state)
        .build()
    )

    assert manifest.policy.max_steps == 10
    assert manifest.policy.human_in_the_loop is True
    assert manifest.state.backend == "redis"

def test_manifest_builder_tools() -> None:
    tool = ToolDefinition(
        id="tool1",
        name="Search",
        uri=StrictUri("https://example.com/mcp"),
        risk_level="safe",
        description="Search tool"
    )

    manifest = (
        ManifestBuilder("ToolManifest")
        .add_tool(tool)
        .add_step(LogicStep(id="main", code="pass"))
        .build()
    )

    assert "tool1" in manifest.definitions
    assert manifest.definitions["tool1"].uri == StrictUri("https://example.com/mcp")

def test_manifest_builder_generic_def() -> None:
    generic = GenericDefinition(some_field="value")

    manifest = (
        ManifestBuilder("GenericManifest")
        .add_generic_definition("my_generic", generic)
        .add_step(LogicStep(id="main", code="pass"))
        .build()
    )

    assert "my_generic" in manifest.definitions
    # Accessing dynamic fields on Pydantic models usually works if configured properly,
    # but GenericDefinition has model_config(extra="allow").
    # Pydantic v2 access for extra fields:
    assert manifest.definitions["my_generic"].some_field == "value" # type: ignore

def test_manifest_builder_implicit_start_step() -> None:
    # If only one step, it should be auto-selected as start
    manifest = (
        ManifestBuilder("ImplicitStart")
        .add_step(LogicStep(id="only_step", code="pass"))
        .build()
    )

    assert manifest.workflow.start == "only_step"

def test_manifest_builder_interface_metadata_error() -> None:
    # Test set_interface
    interface = InterfaceDefinition(inputs={"type": "object"})
    builder = ManifestBuilder("TestInterface")
    builder.set_interface(interface)

    # Test set_metadata
    builder.set_metadata("extra_field", "extra_value")

    # Test ValueError for missing start step
    builder.add_step(LogicStep(id="s1", code="pass"))
    builder.add_step(LogicStep(id="s2", code="pass"))

    with pytest.raises(ValueError, match="Start step must be specified"):
        builder.build()

    # Now set start step and build should succeed
    builder.set_start_step("s1")
    manifest = builder.build()

    assert manifest.interface.inputs["type"] == "object"
    # Pydantic V2 allows accessing extra fields as attributes if not colliding
    assert getattr(manifest.metadata, "extra_field", None) == "extra_value"
