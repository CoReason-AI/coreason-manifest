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

    # Use status=PUBLISHED to ensure integrity_hash is generated
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


def test_builder_set_status() -> None:
    """Test that set_status correctly updates the builder status."""
    builder = AgentBuilder(name="StatusAgent")
    assert builder._status == AgentStatus.DRAFT

    builder.set_status(AgentStatus.PUBLISHED)
    assert builder._status == AgentStatus.PUBLISHED  # type: ignore[comparison-overlap]

    builder.set_status(AgentStatus.DRAFT)
    assert builder._status == AgentStatus.DRAFT


def test_integrity_hash_sensitivity() -> None:
    """Test that integrity hash changes when content changes."""
    cap = TypedCapability(
        name="search",
        description="Search",
        input_model=SearchInput,
        output_model=SearchOutput,
    )

    # Base Agent
    builder1 = AgentBuilder(name="Agent", status=AgentStatus.PUBLISHED)
    builder1.with_capability(cap).with_system_prompt("Prompt A")
    agent1 = builder1.build()

    # Modified Agent (different prompt)
    builder2 = AgentBuilder(name="Agent", status=AgentStatus.PUBLISHED)
    builder2.with_capability(cap).with_system_prompt("Prompt B")
    agent2 = builder2.build()

    assert agent1.integrity_hash != agent2.integrity_hash

    # Identical Agent
    builder3 = AgentBuilder(name="Agent", status=AgentStatus.PUBLISHED)
    builder3.with_capability(cap).with_system_prompt("Prompt A")
    agent3 = builder3.build()

    assert agent1.integrity_hash == agent3.integrity_hash


def test_builder_with_auth_requirement() -> None:
    """Test setting auth requirement."""
    cap = TypedCapability(
        name="search",
        description="Search",
        input_model=SearchInput,
        output_model=SearchOutput,
        injected_params=["user_context"],
    )
    builder = AgentBuilder(name="AuthAgent")
    builder.with_capability(cap).with_auth_requirement(True)
    agent = builder.build()

    assert agent.metadata.requires_auth is True
