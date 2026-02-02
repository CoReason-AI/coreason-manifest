import uuid

from coreason_manifest.definitions.agent import AgentDefinition


def test_atomic_agent_mermaid() -> None:
    """Test Mermaid export for an atomic agent."""
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "My Atomic Agent",
            "author": "Me",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "capabilities": [{"name": "default", "type": "atomic", "description": "Default", "inputs": {}, "outputs": {}}],
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": None,
            "model_config": {"model": "gpt-4", "temperature": 0.7},
            "system_prompt": "You are an atomic agent.",
        },
        "dependencies": {},
    }

    agent = AgentDefinition(**data)
    mermaid = agent.to_mermaid()

    assert "graph TD" in mermaid
    assert 'Start((Start)) --> Agent["My Atomic Agent (Atomic)"]' in mermaid


def test_graph_agent_mermaid() -> None:
    """Test Mermaid export for a graph agent."""
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "My Graph Agent",
            "author": "Me",
            "created_at": "2023-10-27T10:00:00Z",
        },
        "capabilities": [{"name": "default", "type": "atomic", "description": "Default", "inputs": {}, "outputs": {}}],
        "config": {
            "nodes": [
                {"id": "node1", "type": "agent", "agent_name": "search_agent", "visual": {"label": "Search Web"}},
                {"id": "node2", "type": "logic", "code": "pass", "visual": {"label": "Process"}},
                {"id": "node3", "type": "human", "visual": {"label": "Approve"}},
            ],
            "edges": [
                {"source_node_id": "node1", "target_node_id": "node2", "condition": "success"},
                {"source_node_id": "node2", "target_node_id": "node3"},
            ],
            "entry_point": "node1",
            "model_config": {"model": "gpt-4", "temperature": 0.7},
        },
        "dependencies": {},
    }

    agent = AgentDefinition(**data)
    mermaid = agent.to_mermaid()

    assert "graph TD" in mermaid

    # Check Styling Definitions
    assert "classDef agent" in mermaid
    assert "classDef logic" in mermaid
    assert "classDef human" in mermaid

    # Check Nodes
    assert 'node1["Search Web"]:::agent' in mermaid
    assert 'node2{"Process"}:::logic' in mermaid
    assert 'node3("Approve"):::human' in mermaid

    # Check Edges
    assert 'node1 -- "success" --> node2' in mermaid
    assert "node2 --> node3" in mermaid

    # Check Entry Point
    assert "Start((Start)) --> node1" in mermaid
