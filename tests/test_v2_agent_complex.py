import yaml

from coreason_manifest.v2.spec.definitions import (
    AgentDefinition,
    GenericDefinition,
    ManifestV2,
    ToolDefinition,
)


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
