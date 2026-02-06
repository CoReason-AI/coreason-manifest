# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import yaml

from coreason_manifest import dump, simple_agent
from coreason_manifest.spec.v2.definitions import AgentDefinition, AgentStep, ManifestV2


def test_simple_agent_defaults() -> None:
    manifest = simple_agent("TestAgent")

    assert manifest.metadata.name == "TestAgent"
    assert manifest.kind == "Agent"

    # Check defaults
    agent_def = manifest.definitions["TestAgent"]
    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.role == "Assistant"
    assert agent_def.goal == "Help the user"
    assert agent_def.backstory is None

    # Check workflow
    assert "main" in manifest.workflow.steps
    step = manifest.workflow.steps["main"]
    assert isinstance(step, AgentStep)
    assert step.agent == "TestAgent"


def test_simple_agent_full() -> None:
    manifest = simple_agent(
        name="ResearchAgent",
        prompt="You research stuff.",
        model="gpt-4",
        tools=["web-search"],
        role="Researcher",
        goal="Find info",
    )

    agent_def = manifest.definitions["ResearchAgent"]
    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.backstory == "You research stuff."
    assert agent_def.model == "gpt-4"
    assert agent_def.tools == ["web-search"]
    assert agent_def.role == "Researcher"
    assert agent_def.goal == "Find info"

    # Check interface defaults
    assert manifest.interface.inputs == {"type": "object", "additionalProperties": True}


def test_simple_agent_edge_cases() -> None:
    """Test edge cases: empty strings, None values, empty lists."""
    manifest = simple_agent(
        name="EdgeCaseAgent",
        prompt="",  # Empty string prompt
        model=None,  # Explicit None model
        tools=[],  # Explicit empty list
    )

    agent_def = manifest.definitions["EdgeCaseAgent"]
    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.backstory == ""  # Should preserve empty string
    assert agent_def.model is None
    assert agent_def.tools == []


def test_simple_agent_complex_modification() -> None:
    """Test creating a simple agent and then manually extending the workflow."""
    manifest = simple_agent("BaseAgent")

    # Manually add a second step to the workflow
    second_step = AgentStep(id="step2", agent="BaseAgent")
    manifest.workflow.steps["step2"] = second_step

    # Update the first step to point to the second
    first_step = manifest.workflow.steps["main"]
    assert isinstance(first_step, AgentStep)  # for mypy
    # Note: Pydantic models are frozen by default in this repo, so we can't mutate directly.
    # We must use model_copy with update.
    updated_first_step = first_step.model_copy(update={"next": "step2"})
    manifest.workflow.steps["main"] = updated_first_step

    final_first_step = manifest.workflow.steps["main"]
    assert isinstance(final_first_step, AgentStep)
    assert final_first_step.next == "step2"
    assert "step2" in manifest.workflow.steps
    assert manifest.workflow.steps["step2"].id == "step2"


def test_simple_agent_round_trip() -> None:
    """Test that the generated manifest can be serialized and deserialized correctly."""
    original = simple_agent(name="RoundTripAgent", prompt="Testing serialization", tools=["tool1", "tool2"])

    # 1. Dump to YAML string
    yaml_str = dump(original)

    # 2. Load back from YAML string (manually, as load() requires a file)
    data = yaml.safe_load(yaml_str)
    loaded = ManifestV2.model_validate(data)

    # 3. Verify equality
    # Note: We rely on Pydantic equality, but we might need to be careful about strict types.
    # The 'load' function typically returns a validated model.

    assert loaded.metadata.name == original.metadata.name
    assert loaded.kind == original.kind

    loaded_def = loaded.definitions["RoundTripAgent"]
    original_def = original.definitions["RoundTripAgent"]

    # Need to cast to AgentDefinition for type checking access, as definitions values are unions
    assert isinstance(loaded_def, AgentDefinition)
    assert isinstance(original_def, AgentDefinition)

    assert loaded_def.backstory == original_def.backstory
    assert loaded_def.tools == original_def.tools

    # Deep equality check
    assert loaded.model_dump() == original.model_dump()
