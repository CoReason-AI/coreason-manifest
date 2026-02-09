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
import yaml
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2, ToolDefinition
from tests.factories import create_agent_definition


def test_factory_usage() -> None:
    """Demonstrate using the factory to create an agent."""
    agent = create_agent_definition(
        id="factory-agent",
        name="Factory Agent",
        # defaults handle type, role, goal
    )
    assert agent.id == "factory-agent"
    assert agent.name == "Factory Agent"
    assert agent.role == "Tester"
    assert agent.type == "agent"


def test_polymorphic_parsing() -> None:
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: My Mixed Manifest
workflow:
  start: step1
  steps:
    step1:
      id: step1
      type: logic
      code: "print('hello')"
definitions:
  my_tool:
    type: tool
    id: tool-1
    name: Search
    uri: mcp://search
    risk_level: safe
  my_agent:
    type: agent
    id: agent-1
    name: Researcher
    role: Research Specialist
    goal: Find data
    tools:
      - type: remote
        uri: my_tool
"""
    manifest_data = yaml.safe_load(yaml_content)
    manifest = ManifestV2(**manifest_data)

    assert "my_tool" in manifest.definitions
    assert isinstance(manifest.definitions["my_tool"], ToolDefinition)
    assert manifest.definitions["my_tool"].type == "tool"

    assert "my_agent" in manifest.definitions
    assert isinstance(manifest.definitions["my_agent"], AgentDefinition)
    assert manifest.definitions["my_agent"].type == "agent"
    assert manifest.definitions["my_agent"].role == "Research Specialist"


def test_validation_failure() -> None:
    # Missing 'role' for agent. Should raise ValidationError now.
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Invalid Manifest
workflow:
  start: step1
  steps:
    step1:
      id: step1
      type: logic
      code: "pass"
definitions:
  bad_agent:
    type: agent
    id: agent-1
    name: Researcher
    # role is missing
    goal: Find data
"""
    manifest_data = yaml.safe_load(yaml_content)
    with pytest.raises(ValidationError):
        ManifestV2(**manifest_data)
