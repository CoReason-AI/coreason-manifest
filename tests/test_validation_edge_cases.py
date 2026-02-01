# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import (
    AgentMetadata,
    AgentRuntimeConfig,
)
from coreason_manifest.definitions.topology import AgentNode


def test_unique_node_ids_validation() -> None:
    """Test that duplicate node IDs raise a ValidationError."""
    nodes = [
        AgentNode(id="node1", agent_name="A"),
        AgentNode(id="node1", agent_name="B"),  # Duplicate
    ]

    with pytest.raises(ValidationError) as e:
        AgentRuntimeConfig(
            nodes=nodes, edges=[], entry_point="node1", llm_config={"model": "gpt-4", "temperature": 0.5}
        )
    assert "Duplicate node IDs found: node1" in str(e.value)


def test_unique_node_ids_valid() -> None:
    """Test that unique node IDs are accepted."""
    nodes = [
        AgentNode(id="node1", agent_name="A"),
        AgentNode(id="node2", agent_name="B"),
    ]
    topo = AgentRuntimeConfig(
        nodes=nodes, edges=[], entry_point="node1", model_config={"model": "gpt-4", "temperature": 0.5}
    )
    assert len(topo.nodes) == 2


def test_empty_name_author_rejected() -> None:
    """Test that empty name and author are rejected."""
    # Test Name
    with pytest.raises(ValidationError) as e:
        AgentMetadata(
            id=uuid4(),
            version="1.0.0",
            name="",
            author="Valid",
            created_at=datetime.now(timezone.utc),
        )
    assert "String should have at least 1 character" in str(e.value)

    # Test Author
    with pytest.raises(ValidationError) as e:
        AgentMetadata(
            id=uuid4(),
            version="1.0.0",
            name="Valid",
            author="",
            created_at=datetime.now(timezone.utc),
        )
    assert "String should have at least 1 character" in str(e.value)


def test_created_at_validation() -> None:
    """Test created_at datetime parsing."""
    # Valid ISO string
    meta = AgentMetadata(
        id=uuid4(),
        version="1.0.0",
        name="Valid",
        author="Valid",
        created_at="2023-01-01T12:00:00Z",
    )
    assert isinstance(meta.created_at, datetime)
    assert meta.created_at.year == 2023

    # Invalid string
    with pytest.raises(ValidationError) as e:
        AgentMetadata(
            id=uuid4(),
            version="1.0.0",
            name="Valid",
            author="Valid",
            created_at="not-a-date",
        )
    assert "Input should be a valid datetime" in str(e.value)
