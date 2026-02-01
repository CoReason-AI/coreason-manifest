# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.definitions.topology import AgentNode, GraphTopology
from coreason_manifest.recipes import RecipeInterface, RecipeManifest, StateDefinition


def test_agent_node_enhancements() -> None:
    """Test that AgentNode accepts system_prompt and config as per v0.10.0 spec."""
    agent_node = AgentNode(
        id="agent-1",
        agent_name="optimizer-agent",
        system_prompt="You are an optimized agent.",
        config={"temperature": 0.7},
    )
    assert agent_node.system_prompt == "You are an optimized agent."
    assert agent_node.config == {"temperature": 0.7}


def test_graph_topology_state_schema_optional() -> None:
    """Test that GraphTopology state_schema is optional."""
    # We need a dummy node to validate topology
    agent_node = AgentNode(id="agent-1", agent_name="test-agent")

    topology = GraphTopology(nodes=[agent_node], edges=[])
    assert topology.state_schema is None


def test_recipe_manifest_integrity_and_metadata() -> None:
    """Test that RecipeManifest accepts integrity_hash and metadata."""
    agent_node = AgentNode(id="agent-1", agent_name="test-agent")
    topology = GraphTopology(nodes=[agent_node], edges=[])

    manifest = RecipeManifest(
        id="recipe-1",
        version="1.0.0",
        name="Test Recipe",
        description="A test recipe",
        interface=RecipeInterface(inputs={}, outputs={}),
        state=StateDefinition(schema_={}, persistence="ephemeral"),
        parameters={},
        topology=topology,
        integrity_hash="a" * 64,  # Mock SHA256
        metadata={"ui_layout": {"agent-1": [10, 20]}},
    )

    assert manifest.integrity_hash == "a" * 64
    assert manifest.metadata["ui_layout"]["agent-1"] == [10, 20]


def test_adversary_profile_accepts_persona() -> None:
    """Test that AdversaryProfile accepts a Persona object."""
    from coreason_manifest.definitions.agent import Persona
    from coreason_manifest.definitions.simulation_config import AdversaryProfile

    persona = Persona(
        name="Hacker",
        description="A skilled hacker.",
        directives=["Be stealthy.", "Exfiltrate data."],
    )
    profile = AdversaryProfile(
        name="APT28",
        goal="Steal credentials",
        strategy_model="gpt-4",
        attack_model="llama-3",
        persona=persona,
    )
    assert profile.persona is not None
    assert profile.persona.name == "Hacker"
    assert profile.persona.directives[0] == "Be stealthy."


def test_model_config_accepts_persona() -> None:
    """Test that ModelConfig accepts a Persona object."""
    from coreason_manifest.definitions.agent import ModelConfig, Persona

    persona = Persona(
        name="Assistant",
        description="A helpful assistant.",
        directives=["Be polite.", "Be concise."],
    )
    config = ModelConfig(model="gpt-4", temperature=0.7, persona=persona)
    assert config.persona is not None
    assert config.persona.name == "Assistant"
    assert config.persona.directives[1] == "Be concise."
