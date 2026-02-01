import uuid

import pytest
from coreason_manifest.definitions.agent import AgentDefinition
from pydantic import ValidationError


def test_atomic_agent_without_topology_succeeds() -> None:
    """
    Demonstrate that creating an Atomic Agent (System Prompt only)
    now succeeds because 'nodes', 'edges', and 'entry_point' are optional.
    """
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Atomic Agent",
            "author": "Me",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "config": {
            # No nodes, edges, entry_point
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "You are an atomic agent.",
        },
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }

    agent = AgentDefinition(**data)
    assert agent.config.nodes == []
    assert agent.config.edges == []
    assert agent.config.entry_point is None
    assert agent.config.system_prompt == "You are an atomic agent."


def test_atomic_agent_with_skeleton_topology_succeeds() -> None:
    """
    Demonstrate that Skeleton Topology still works.
    """
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Atomic Agent",
            "author": "Me",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "config": {
            # Skeleton Topology
            "nodes": [{"id": "main", "type": "agent", "agent_name": "self"}],  # minimal node
            "edges": [],
            "entry_point": "main",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "You are an atomic agent.",
        },
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }

    agent = AgentDefinition(**data)
    assert len(agent.config.nodes) == 1
    assert agent.config.entry_point == "main"


def test_nodes_without_entry_point_fails() -> None:
    """
    Test that if nodes are provided, entry_point is mandatory.
    """
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Invalid Agent",
            "author": "Me",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "config": {
            "nodes": [{"id": "main", "type": "agent", "agent_name": "self"}],
            "edges": [],
            # entry_point missing
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }

    with pytest.raises(ValidationError) as exc:
        AgentDefinition(**data)
    assert "Graph execution requires an 'entry_point'" in str(exc.value)


def test_atomic_agent_with_explicit_empty_nodes() -> None:
    """
    Test that explicit empty nodes list is treated as atomic agent (valid).
    """
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Explicit Empty",
            "author": "Me",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "config": {
            "nodes": [],  # Explicit empty
            "edges": [],
            "entry_point": None,
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "Atomic",
        },
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }

    agent = AgentDefinition(**data)
    assert agent.config.nodes == []
    assert agent.config.entry_point is None


def test_edges_without_nodes_integrity() -> None:
    """
    Test that edges cannot reference non-existent nodes (Graph Integrity).
    Although AgentRuntimeConfig allows empty nodes, GraphTopology logic (if used elsewhere)
    or just common sense dictates edges shouldn't exist without nodes.
    However, AgentRuntimeConfig defines edges as List[Edge].
    Does it have a validator for graph integrity like GraphTopology?

    Looking at AgentRuntimeConfig, it has `validate_unique_node_ids` but NOT `validate_graph_integrity`
    like `GraphTopology` does.

    Let's check if we can define edges without nodes.
    """
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Broken Graph",
            "author": "Me",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "config": {
            "nodes": [],
            "edges": [{"source_node_id": "a", "target_node_id": "b"}],
            "entry_point": None,
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "Dummy prompt",
        },
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }

    # Currently, AgentRuntimeConfig DOES have the integrity check (added in Shared Kernel Review).

    with pytest.raises(ValidationError) as exc:
        AgentDefinition(**data)

    assert "Edge source node 'a' not found in nodes" in str(exc.value)


def test_atomic_agent_serialization_excludes_defaults() -> None:
    """
    Test serialization behavior. Pydantic usually includes defaults unless exclude_defaults=True.
    """
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Atomic",
            "author": "Me",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "config": {
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "Atomic",
        },
        "dependencies": {},
        "integrity_hash": "a" * 64,
    }

    agent = AgentDefinition(**data)
    dump = agent.model_dump(exclude_unset=True)

    # config should NOT have nodes, edges, entry_point if they weren't set
    assert "nodes" not in dump["config"]
    assert "edges" not in dump["config"]
    assert "entry_point" not in dump["config"]
    assert dump["config"]["system_prompt"] == "Atomic"
