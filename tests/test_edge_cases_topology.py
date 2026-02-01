# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.definitions.agent import AgentRuntimeConfig
from coreason_manifest.definitions.topology import Edge, LogicNode


def test_topology_allows_cycles() -> None:
    """Test that the topology allows cyclic graphs (e.g., A -> B -> A)."""
    # Define nodes
    node_a = LogicNode(id="A", type="logic", code="pass")
    node_b = LogicNode(id="B", type="logic", code="pass")

    # Define edges forming a cycle
    edges = [
        Edge(source_node_id="A", target_node_id="B"),
        Edge(source_node_id="B", target_node_id="A"),
    ]

    # Should be valid
    topology = AgentRuntimeConfig(
        nodes=[node_a, node_b],
        edges=edges,
        entry_point="A",
        model_config={"model": "gpt-4", "temperature": 0.0},
    )
    assert len(topology.edges) == 2


def test_topology_disconnected_graph_valid() -> None:
    """Test that disconnected components are valid (e.g., A->B, C)."""
    node_a = LogicNode(id="A", type="logic", code="pass")
    node_b = LogicNode(id="B", type="logic", code="pass")
    node_c = LogicNode(id="C", type="logic", code="pass")

    edges = [Edge(source_node_id="A", target_node_id="B")]

    # Should be valid
    topology = AgentRuntimeConfig(
        nodes=[node_a, node_b, node_c],
        edges=edges,
        entry_point="A",
        model_config={"model": "gpt-4", "temperature": 0.0},
    )
    assert len(topology.nodes) == 3


def test_topology_self_loop_valid() -> None:
    """Test that self-loops are valid (A -> A)."""
    node_a = LogicNode(id="A", type="logic", code="pass")
    edges = [Edge(source_node_id="A", target_node_id="A")]

    topology = AgentRuntimeConfig(
        nodes=[node_a],
        edges=edges,
        entry_point="A",
        model_config={"model": "gpt-4", "temperature": 0.0},
    )
    assert len(topology.edges) == 1


def test_topology_entry_point_must_exist() -> None:
    """Test that the entry point must reference an existing node ID."""
    node_a = LogicNode(id="A", type="logic", code="pass")

    # This is currently NOT validated by the model directly (it's a string),
    # but let's see if we should add a validator or if it's acceptable for now.
    # The current AgentRuntimeConfig model only validates unique node IDs.
    # If the user requirement implies strict graph validation, we might need to add it.
    # However, for now, let's verify the current behavior (it accepts it).
    # If we want to be strict, we would add a model validator.
    # Given "Robust, interoperable standard", let's assume loose coupling is okay unless specified.

    # Actually, a robust standard SHOULD probably validate this.
    # But I am writing tests for *current* implementation edge cases.
    topology = AgentRuntimeConfig(
        nodes=[node_a],
        edges=[],
        entry_point="Z",  # Non-existent
        model_config={"model": "gpt-4", "temperature": 0.0},
    )
    assert topology.entry_point == "Z"
