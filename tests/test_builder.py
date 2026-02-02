# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import List

from pydantic import BaseModel

from coreason_manifest.builder import AgentBuilder, TypedCapability
from coreason_manifest.definitions.agent import AgentDefinition, AgentStatus


class SearchInput(BaseModel):
    query: str


class SearchOutput(BaseModel):
    results: List[str]


def test_capability_compilation() -> None:
    """Test that TypedCapability correctly compiles Pydantic models to JSON Schema."""
    cap = TypedCapability(
        name="search",
        description="Search the web",
        input_model=SearchInput,
        output_model=SearchOutput,
    )

    definition = cap.to_definition()

    assert definition.name == "search"
    assert definition.description == "Search the web"

    # Check inputs schema
    assert "properties" in definition.inputs
    assert "query" in definition.inputs["properties"]
    assert definition.inputs["properties"]["query"]["type"] == "string"

    # Check outputs schema
    assert "properties" in definition.outputs
    assert "results" in definition.outputs["properties"]
    assert definition.outputs["properties"]["results"]["type"] == "array"


def test_full_agent_build() -> None:
    """Test that AgentBuilder constructs a valid AgentDefinition."""
    cap = TypedCapability(
        name="search",
        description="Search the web",
        input_model=SearchInput,
        output_model=SearchOutput,
    )

    builder = AgentBuilder(name="SearchAgent", author="Tester", status=AgentStatus.PUBLISHED)
    agent = builder.with_capability(cap).with_system_prompt("You are a search agent.").with_model("gpt-4-turbo").build()

    assert isinstance(agent, AgentDefinition)
    assert agent.metadata.name == "SearchAgent"
    assert agent.metadata.author == "Tester"
    assert len(agent.capabilities) == 1

    # Verify capability is compiled
    compiled_cap = agent.capabilities[0]
    assert compiled_cap.name == "search"
    assert compiled_cap.inputs["properties"]["query"]["type"] == "string"

    # Verify config
    assert agent.config.system_prompt == "You are a search agent."
    assert agent.config.llm_config.model == "gpt-4-turbo"
    assert agent.config.llm_config.system_prompt == "You are a search agent."
    assert agent.integrity_hash is not None
