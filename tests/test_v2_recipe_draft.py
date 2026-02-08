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

from coreason_manifest.spec.v2.recipe import GraphTopology


def test_draft_status_allows_missing_entry_point() -> None:
    """Test that setting status='draft' allows missing entry point."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
        ],
        "edges": [],
        "entry_point": "Z",  # Missing
        "status": "draft",
    }
    # Should not raise
    topology = GraphTopology.model_validate(data)
    assert topology.status == "draft"

    # Verify completeness check
    assert topology.verify_completeness() is False


def test_draft_status_allows_dangling_edges() -> None:
    """Test that setting status='draft' allows dangling edges."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
        ],
        "edges": [{"source": "A", "target": "B"}],  # B missing
        "entry_point": "A",
        "status": "draft",
    }
    # Should not raise
    topology = GraphTopology.model_validate(data)
    assert topology.status == "draft"

    assert topology.verify_completeness() is False


def test_valid_status_enforces_integrity() -> None:
    """Test that setting status='valid' enforces strict integrity checks."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
        ],
        "edges": [{"source": "A", "target": "B"}],
        "entry_point": "A",
        "status": "valid",
    }
    with pytest.raises(ValidationError) as excinfo:
        GraphTopology.model_validate(data)

    assert "Dangling edge" in str(excinfo.value)


def test_default_status_is_valid() -> None:
    """Test that default status is 'valid' and enforces integrity."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
        ],
        "edges": [{"source": "A", "target": "B"}],
        "entry_point": "A",
    }
    # Default is valid, so it should raise
    with pytest.raises(ValidationError) as excinfo:
        GraphTopology.model_validate(data)

    assert "Dangling edge" in str(excinfo.value)


def test_duplicate_ids_forbidden_in_draft() -> None:
    """Test that duplicate IDs are forbidden even in draft mode."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
            {"type": "agent", "id": "A", "agent_ref": "ref-b"},
        ],
        "edges": [],
        "entry_point": "A",
        "status": "draft",
    }
    with pytest.raises(ValidationError) as excinfo:
        GraphTopology.model_validate(data)
    assert "Duplicate node IDs found" in str(excinfo.value)


def test_verify_completeness_true() -> None:
    """Test verify_completeness returns True for a valid graph."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
            {"type": "agent", "id": "B", "agent_ref": "ref-b"},
        ],
        "edges": [{"source": "A", "target": "B"}],
        "entry_point": "A",
        "status": "draft",
    }
    topology = GraphTopology.model_validate(data)
    assert topology.verify_completeness() is True


def test_verify_completeness_missing_entry_point() -> None:
    """Test verify_completeness returns False for missing entry point."""
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
        ],
        "edges": [],
        "entry_point": "Z",
        "status": "draft",
    }
    topology = GraphTopology.model_validate(data)
    assert topology.verify_completeness() is False


# --- New Edge Case & Complex Tests ---


def test_draft_allows_empty_graph() -> None:
    """Test that a draft graph can have no nodes (if list is allowed to be empty)."""
    data = {
        "nodes": [],
        "edges": [],
        "entry_point": "start",  # Missing, but allowed in draft
        "status": "draft",
    }
    topology = GraphTopology.model_validate(data)
    assert len(topology.nodes) == 0
    assert topology.status == "draft"
    assert topology.verify_completeness() is False


def test_draft_allows_disconnected_components() -> None:
    """Test behavior with disconnected islands."""
    # A -> B   C -> D
    data = {
        "nodes": [
            {"type": "agent", "id": "A", "agent_ref": "ref-a"},
            {"type": "agent", "id": "B", "agent_ref": "ref-b"},
            {"type": "agent", "id": "C", "agent_ref": "ref-c"},
            {"type": "agent", "id": "D", "agent_ref": "ref-d"},
        ],
        "edges": [
            {"source": "A", "target": "B"},
            {"source": "C", "target": "D"},
        ],
        "entry_point": "A",
        "status": "draft",
    }
    # This is actually valid in strict mode too (unreachable nodes are allowed),
    # but we verify verify_completeness() passes.
    topology = GraphTopology.model_validate(data)
    assert topology.verify_completeness() is True


def test_complex_incomplete_graph() -> None:
    """Test a large graph with multiple missing connections."""
    data = {
        "nodes": [
            {"type": "agent", "id": "Start", "agent_ref": "ref-1"},
            {"type": "router", "id": "Router", "input_key": "x", "routes": {"yes": "PathA"}, "default_route": "PathB"},
            # PathA exists
            {"type": "agent", "id": "PathA", "agent_ref": "ref-2"},
            # PathB MISSING
        ],
        "edges": [
            {"source": "Start", "target": "Router"},
            # Router -> PathA implied by logic (not edge list), but let's say explicit edge
            {"source": "Router", "target": "PathA"},
            {"source": "Router", "target": "PathB"},  # Dangling edge
            {"source": "PathA", "target": "End"},  # Dangling edge
        ],
        "entry_point": "Start",
        "status": "draft",
    }
    topology = GraphTopology.model_validate(data)
    assert topology.status == "draft"
    assert topology.verify_completeness() is False

    # Check that it fails validation if we tried to make it valid
    data["status"] = "valid"
    with pytest.raises(ValidationError) as excinfo:
        GraphTopology.model_validate(data)
    assert "Dangling edge" in str(excinfo.value)


def test_typo_in_entry_point() -> None:
    """Test a common user error: typo in entry point ID."""
    data = {
        "nodes": [
            {"type": "agent", "id": "research_agent", "agent_ref": "ref-1"},
        ],
        "edges": [],
        "entry_point": "research_agnte",  # Typo
        "status": "draft",
    }
    topology = GraphTopology.model_validate(data)
    assert topology.status == "draft"
    assert topology.verify_completeness() is False


def test_upgrade_draft_to_valid() -> None:
    """Test the workflow of 'upgrading' a draft to valid by correcting data."""
    # 1. Start with invalid draft
    draft_data = {
        "nodes": [{"type": "agent", "id": "A", "agent_ref": "ref-1"}],
        "edges": [{"source": "A", "target": "B"}],  # Missing B
        "entry_point": "A",
        "status": "draft",
    }
    draft = GraphTopology.model_validate(draft_data)
    assert draft.verify_completeness() is False

    # 2. Correct the data
    valid_data = draft.model_dump()
    valid_data["nodes"].append({"type": "agent", "id": "B", "agent_ref": "ref-2"})
    valid_data["status"] = "valid"

    # 3. Create new valid topology
    valid_topology = GraphTopology.model_validate(valid_data)
    assert valid_topology.status == "valid"
    # Should not raise
