import yaml

from coreason_manifest.definitions.agent import AgentDefinition as V1AgentDefinition
from coreason_manifest.definitions.agent import ToolRequirement
from coreason_manifest.v2.adapter import v2_to_recipe
from coreason_manifest.v2.spec.definitions import (
    AgentDefinition,
    GenericDefinition,
    ManifestV2,
    ToolDefinition,
)


def test_minimal_maximal_agents() -> None:
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Edge Cases
workflow:
  start: s
  steps: {s: {type: logic, id: s, code: pass}}
definitions:
  min_agent:
    type: agent
    id: min
    name: Minimal
    role: MinRole
    goal: MinGoal

  max_agent:
    type: agent
    id: max
    name: Maximal
    role: MaxRole
    goal: MaxGoal
    backstory: "A long backstory."
    model: "claude-3-opus"
    tools: []
    knowledge: ["/docs/info.txt"]
"""
    manifest = ManifestV2(**yaml.safe_load(yaml_content))
    recipe = v2_to_recipe(manifest)

    # Check Minimal
    v1_min = recipe.parameters["min_agent"]
    assert isinstance(v1_min, V1AgentDefinition)
    assert v1_min.config.llm_config.persona is not None
    assert v1_min.config.llm_config.persona.name == "MinRole"
    assert v1_min.config.llm_config.model == "gpt-4"  # Default

    # Check Maximal
    v1_max = recipe.parameters["max_agent"]
    assert isinstance(v1_max, V1AgentDefinition)
    assert v1_max.config.llm_config.persona is not None
    assert v1_max.config.llm_config.model == "claude-3-opus"
    assert v1_max.config.system_prompt == "A long backstory."


def test_recursive_composition() -> None:
    """Test 'Agent-as-a-Tool' scenario."""
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Recursive Team
workflow:
  start: s
  steps: {s: {type: logic, id: s, code: pass}}
definitions:
  writer:
    type: agent
    id: writer-1
    name: Writer
    role: Writer
    goal: Write

  editor:
    type: agent
    id: editor-1
    name: Editor
    role: Editor
    goal: Edit
    tools: ["writer"] # Referencing another agent as a tool
"""
    manifest = ManifestV2(**yaml.safe_load(yaml_content))
    recipe = v2_to_recipe(manifest)

    v1_editor = recipe.parameters["editor"]
    assert isinstance(v1_editor, V1AgentDefinition)

    # Check dependencies
    assert len(v1_editor.dependencies.tools) == 1
    tool_req = v1_editor.dependencies.tools[0]

    # It should treat the agent ref as an MCP tool
    assert isinstance(tool_req, ToolRequirement)
    # The adapter logic falls back to mcp://<id> for non-ToolDefinition references (like AgentDefinition)
    assert str(tool_req.uri) == "mcp://writer"


def test_mixed_definitions_typo_tolerance() -> None:
    """Test mixing valid types and 'typo' types falling back to Generic."""
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Mixed Bag
workflow:
  start: s
  steps: {s: {type: logic, id: s, code: pass}}
definitions:
  valid_tool:
    type: tool
    id: t1
    name: T1
    uri: mcp://t1
    risk_level: safe

  valid_agent:
    type: agent
    id: a1
    name: A1
    role: R1
    goal: G1

  typo_thing:
    type: unknown_type # This should become GenericDefinition
    id: u1
    name: Unknown
"""
    manifest = ManifestV2(**yaml.safe_load(yaml_content))

    assert isinstance(manifest.definitions["valid_tool"], ToolDefinition)
    assert isinstance(manifest.definitions["valid_agent"], AgentDefinition)
    assert isinstance(manifest.definitions["typo_thing"], GenericDefinition)

    # Check access on generic
    generic = manifest.definitions["typo_thing"]
    # GenericDefinition stores extra fields in __pydantic_extra__ or via model_dump
    data = generic.model_dump()
    assert data["type"] == "unknown_type"


def test_self_reference_circular_tools() -> None:
    """Test an agent referencing itself in tools (Circular)."""
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Self Ref
workflow:
  start: s
  steps: {s: {type: logic, id: s, code: pass}}
definitions:
  ouroboros:
    type: agent
    id: snake
    name: Snake
    role: Eater
    goal: Eat tail
    tools: ["snake"]
"""
    manifest = ManifestV2(**yaml.safe_load(yaml_content))
    recipe = v2_to_recipe(manifest)

    v1_agent = recipe.parameters["ouroboros"]
    assert isinstance(v1_agent, V1AgentDefinition)
    # It should just have a tool ref to mcp://snake
    assert len(v1_agent.dependencies.tools) == 1

    # Explicitly check/cast to ToolRequirement to satisfy strict mypy
    tool = v1_agent.dependencies.tools[0]
    assert isinstance(tool, ToolRequirement)

    assert str(tool.uri) == "mcp://snake"
