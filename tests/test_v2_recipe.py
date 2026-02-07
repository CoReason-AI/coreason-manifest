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
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RouterNode,
)


def test_polymorphic_deserialization() -> None:
    """Test that nodes are correctly deserialized into their specific types."""
    data = {
        "nodes": [
            {
                "type": "agent",
                "id": "agent-1",
                "agent_ref": "agent-a",
                "metadata": {"x": 10, "y": 20},
            },
            {
                "type": "human",
                "id": "human-1",
                "prompt": "Approve?",
                "metadata": {"x": 100, "y": 20},
            },
            {
                "type": "router",
                "id": "router-1",
                "input_key": "score",
                "routes": {"high": "agent-1"},
                "default_route": "human-1",
                "metadata": {"x": 50, "y": 50},
            },
        ],
        "edges": [],
        "entry_point": "agent-1",
    }

    topology = GraphTopology.model_validate(data)

    assert len(topology.nodes) == 3
    assert isinstance(topology.nodes[0], AgentNode)
    assert topology.nodes[0].id == "agent-1"
    assert topology.nodes[0].agent_ref == "agent-a"

    assert isinstance(topology.nodes[1], HumanNode)
    assert topology.nodes[1].id == "human-1"
    assert topology.nodes[1].prompt == "Approve?"

    assert isinstance(topology.nodes[2], RouterNode)
    assert topology.nodes[2].id == "router-1"
    assert topology.nodes[2].input_key == "score"


def test_integrity_validation_success() -> None:
    """Test valid graph structure."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
            {"type": "agent", "id": "B", "agent_ref": "ref-b"},
        ],
        "edges": [{"source": "A", "target": "B"}],
        "entry_point": "A",
    }
    topology = GraphTopology.model_validate(data)
    assert topology.entry_point == "A"
    assert len(topology.edges) == 1


def test_integrity_validation_failure_dangling_edge() -> None:
    """Test validation failure for dangling edges."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
        ],
        "edges": [{"source": "A", "target": "B"}],  # B missing
        "entry_point": "A",
    }
    with pytest.raises(ValidationError) as excinfo:
        GraphTopology.model_validate(data)

    assert "Dangling edge" in str(excinfo.value)
    assert "A -> B" in str(excinfo.value)

    # Test dangling source
    data2 = {
        "nodes": [
            {"type": "agent", "id": "B", "agent_ref": "ref-b"},
        ],
        "edges": [{"source": "A", "target": "B"}],  # A missing
        "entry_point": "B",
    }
    with pytest.raises(ValidationError) as excinfo:
        GraphTopology.model_validate(data2)

    assert "Dangling edge" in str(excinfo.value)
    assert "A -> B" in str(excinfo.value)


def test_integrity_validation_failure_bad_entry_point() -> None:
    """Test validation failure for invalid entry point."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
        ],
        "edges": [],
        "entry_point": "Z",
    }
    with pytest.raises(ValidationError) as excinfo:
        GraphTopology.model_validate(data)

    assert "Entry point 'Z' not found" in str(excinfo.value)


def test_full_manifest_roundtrip() -> None:
    """Test serialization and deserialization of the full RecipeDefinition."""
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(
            name="Test Recipe",
            x_design=None,
        ),
        topology=GraphTopology(
            nodes=[
                AgentNode(id="start", agent_ref="agent-1"),
                HumanNode(id="approval", prompt="Is this ok?"),
            ],
            edges=[
                {"source": "start", "target": "approval", "condition": None},
            ],
            entry_point="start",
        ),
    )

    json_str = recipe.to_json()
    loaded = RecipeDefinition.model_validate_json(json_str)

    assert loaded.metadata.name == "Test Recipe"
    assert len(loaded.topology.nodes) == 2
    assert loaded.topology.entry_point == "start"
    assert loaded.topology.edges[0].source == "start"
    assert loaded.topology.edges[0].target == "approval"

    # Check dumping
    dumped = loaded.dump()
    assert dumped["kind"] == "Recipe"
    assert dumped["apiVersion"] == "coreason.ai/v2"
