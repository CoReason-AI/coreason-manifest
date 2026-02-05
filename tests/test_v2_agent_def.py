import yaml

from coreason_manifest.spec.v2.definitions import AgentDefinition, GenericDefinition, ManifestV2, ToolDefinition


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
    tools: [my_tool]
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
    # Missing 'role' for agent. Should fall back to GenericDefinition.
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
    manifest = ManifestV2(**manifest_data)

    assert "bad_agent" in manifest.definitions
    # Should fallback to GenericDefinition because validation failed for AgentDefinition
    assert isinstance(manifest.definitions["bad_agent"], GenericDefinition)
    # Ensure it is NOT AgentDefinition
    assert not isinstance(manifest.definitions["bad_agent"], AgentDefinition)
