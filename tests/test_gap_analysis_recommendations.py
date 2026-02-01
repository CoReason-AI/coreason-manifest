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
