import uuid

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import AgentDefinition


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
