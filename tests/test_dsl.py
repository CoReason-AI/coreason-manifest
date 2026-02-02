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
from coreason_manifest.dsl import load_from_yaml
from coreason_manifest.definitions.agent import AgentStatus, CapabilityType

def test_load_basic_agent() -> None:
    yaml_content = """
name: "WeatherBot"
version: "0.1.0"
status: "draft"
system_prompt: "You are a weather bot."
model:
  name: "gpt-4o"
  temperature: 0.2
capabilities:
  - name: "get_weather"
    description: "Fetches weather."
    inputs:
      city: string
      days: int
    outputs:
      report: string
"""
    agent = load_from_yaml(yaml_content)

    # Metadata assertions
    assert agent.metadata.name == "WeatherBot"
    assert agent.metadata.version == "0.1.0"
    assert agent.status == AgentStatus.DRAFT

    # Config assertions
    assert agent.config.system_prompt == "You are a weather bot."
    assert agent.config.llm_config.model == "gpt-4o"
    assert agent.config.llm_config.temperature == 0.2

    # Capability assertions
    assert len(agent.capabilities) == 1
    cap = agent.capabilities[0]
    assert cap.name == "get_weather"
    assert cap.description == "Fetches weather."
    assert cap.type == CapabilityType.ATOMIC

    # Schema assertions
    # Inputs
    assert cap.inputs["type"] == "object"
    assert cap.inputs["required"] == ["city", "days"]
    assert cap.inputs["properties"]["city"] == {"type": "string"}
    assert cap.inputs["properties"]["days"] == {"type": "integer"}

    # Outputs
    assert cap.outputs["type"] == "object"
    assert cap.outputs["properties"]["report"] == {"type": "string"}

def test_load_complex_types() -> None:
    yaml_content = """
name: "ComplexBot"
capabilities:
  - name: "process_data"
    inputs:
      tags: list[string]
      scores: array[float]
    outputs:
      summary: any
"""
    agent = load_from_yaml(yaml_content)
    cap = agent.capabilities[0]

    # List[string] -> {"type": "array", "items": {"type": "string"}}
    tags_schema = cap.inputs["properties"]["tags"]
    assert tags_schema["type"] == "array"
    assert tags_schema["items"] == {"type": "string"}

    # Array[float] -> {"type": "array", "items": {"type": "number"}}
    scores_schema = cap.inputs["properties"]["scores"]
    assert scores_schema["type"] == "array"
    assert scores_schema["items"] == {"type": "number"}

    # Any -> {}
    summary_schema = cap.outputs["properties"]["summary"]
    assert summary_schema == {}

def test_load_published_status() -> None:
    # Note: Published status requires integrity_hash usually, but AgentBuilder generates a dummy one if published.
    yaml_content = """
name: "PublishedBot"
status: "published"
capabilities:
  - name: "test"
    inputs: {}
    outputs: {}
"""
    # Just checking if it parses status correctly.
    # However, AgentDefinition validation might fail if integrity_hash is missing?
    # AgentBuilder.build() handles generating integrity_hash if status is published.
    # But wait, AgentBuilder.build() says:
    # if self._status == AgentStatus.PUBLISHED:
    #     integrity_hash = hashlib.sha256(self.name.encode("utf-8")).hexdigest()
    # So it should pass.

    # Also need system prompt for atomic agent if published?
    # validate_config_completeness_if_published: Atomic Agents require a system_prompt when published.
    # So I need to add system_prompt.

    yaml_content = """
name: "PublishedBot"
status: "published"
system_prompt: "Sys prompt"
capabilities:
  - name: "test"
    inputs: {}
    outputs: {}
"""
    agent = load_from_yaml(yaml_content)
    assert agent.status == AgentStatus.PUBLISHED
    assert agent.integrity_hash is not None

def test_load_error_cases() -> None:
    # Test unknown shorthand
    with pytest.raises(ValueError, match="Unknown shorthand type"):
        load_from_yaml("""
name: "ErrorBot"
capabilities:
  - name: "test"
    inputs:
      x: invalid_type
""")

    # Test boolean shorthand (missing coverage)
    agent = load_from_yaml("""
name: "BoolBot"
capabilities:
  - name: "test"
    inputs:
      flag: bool
""")
    assert agent.capabilities[0].inputs["properties"]["flag"]["type"] == "boolean"

    # Test invalid YAML structure (list instead of dict)
    with pytest.raises(ValueError, match="must resolve to a dictionary"):
        load_from_yaml("- item")

    # Test missing name
    with pytest.raises(ValueError, match="Field 'name' is required"):
        load_from_yaml("version: '1.0'")

    # Test missing capability name
    with pytest.raises(ValueError, match="Capability must have a 'name'"):
        load_from_yaml("""
name: "NoCapName"
capabilities:
  - description: "missing name"
""")
