import yaml

from coreason_manifest.definitions.agent import AgentDefinition as V1AgentDefinition
from coreason_manifest.definitions.agent import ToolRequirement
from coreason_manifest.v2.adapter import v2_to_recipe
from coreason_manifest.v2.spec.definitions import AgentDefinition, GenericDefinition, ManifestV2, ToolDefinition


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


def test_adapter_conversion() -> None:
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Conversion Test
workflow:
  start: step1
  steps:
    step1:
      id: step1
      type: logic
      code: "pass"
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
    goal: Find comprehensive data
    backstory: You are an expert researcher.
    tools: [my_tool]
"""
    manifest_data = yaml.safe_load(yaml_content)
    manifest = ManifestV2(**manifest_data)

    recipe = v2_to_recipe(manifest)

    # Check parameters
    assert "my_agent" in recipe.parameters
    v1_agent = recipe.parameters["my_agent"]

    # Assert it is a V1 AgentDefinition
    assert isinstance(v1_agent, V1AgentDefinition)

    # Check Mappings
    # Role -> Persona.name
    assert v1_agent.config.llm_config.persona is not None
    assert v1_agent.config.llm_config.persona.name == "Research Specialist"
    # Goal -> Persona.description
    assert v1_agent.config.llm_config.persona.description == "Find comprehensive data"
    # Backstory -> Persona.directives
    assert "You are an expert researcher." in v1_agent.config.llm_config.persona.directives

    # Check Tools
    assert len(v1_agent.dependencies.tools) == 1
    tool_req = v1_agent.dependencies.tools[0]

    # Ensure it is a ToolRequirement (not InlineToolDefinition) to satisfy Mypy
    assert isinstance(tool_req, ToolRequirement)

    assert str(tool_req.uri) == "mcp://search"
    assert tool_req.risk_level == "safe"
    # Hash should be present (SHA256 hex)
    assert len(tool_req.hash) == 64
