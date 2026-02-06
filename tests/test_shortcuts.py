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
from coreason_manifest.spec.v2.definitions import AgentDefinition, AgentStep


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
