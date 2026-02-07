# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RecipeInterface,
)


def test_topology_coercion_from_list() -> None:
    """Test initializing RecipeDefinition with a list of nodes (implicit TaskSequence)."""
    step1 = AgentNode(id="step1", agent_ref="agent-1")
    step2 = HumanNode(id="step2", prompt="Approve?")
    step3 = AgentNode(id="step3", agent_ref="agent-2")

    steps = [step1, step2, step3]

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="test-recipe", version="1.0.0"),
        interface=RecipeInterface(),
        topology=steps,  # type: ignore[arg-type] # Explicitly testing coercion
    )

    assert isinstance(recipe.topology, GraphTopology)
    assert recipe.topology.entry_point == "step1"
    assert len(recipe.topology.nodes) == 3
    assert len(recipe.topology.edges) == 2

    # Verify edges
    edge1 = recipe.topology.edges[0]
    assert edge1.source == "step1"
    assert edge1.target == "step2"

    edge2 = recipe.topology.edges[1]
    assert edge2.source == "step2"
    assert edge2.target == "step3"


def test_topology_coercion_from_dict_steps() -> None:
    """Test initializing RecipeDefinition with a dict containing 'steps'."""
    step1 = AgentNode(id="step1", agent_ref="agent-1")
    step2 = AgentNode(id="step2", agent_ref="agent-2")

    topology_dict = {"steps": [step1, step2]}

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="test-recipe", version="1.0.0"),
        interface=RecipeInterface(),
        topology=topology_dict,  # type: ignore[arg-type]
    )

    assert isinstance(recipe.topology, GraphTopology)
    assert recipe.topology.entry_point == "step1"
    assert len(recipe.topology.edges) == 1
    assert recipe.topology.edges[0].source == "step1"
    assert recipe.topology.edges[0].target == "step2"


def test_topology_direct_graph_topology() -> None:
    """Test initializing RecipeDefinition with an explicit GraphTopology (fallback)."""
    step1 = AgentNode(id="step1", agent_ref="agent-1")

    # Manual graph construction
    graph = GraphTopology(
        nodes=[step1],
        edges=[],
        entry_point="step1"
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="test-recipe", version="1.0.0"),
        interface=RecipeInterface(),
        topology=graph,
    )

    assert recipe.topology == graph


def test_topology_dict_passthrough() -> None:
    """Test initializing RecipeDefinition with a dict that is already a valid GraphTopology structure."""
    topo_data = {
        "nodes": [{"type": "agent", "id": "step1", "agent_ref": "agent-1"}],
        "edges": [],
        "entry_point": "step1"
    }

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="test-recipe", version="1.0.0"),
        interface=RecipeInterface(),
        topology=topo_data,  # type: ignore[arg-type]
    )

    assert isinstance(recipe.topology, GraphTopology)
    assert recipe.topology.entry_point == "step1"
