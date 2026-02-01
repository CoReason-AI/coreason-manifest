# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from coreason_manifest.definitions.events import GraphEventNodeStart
from coreason_manifest.definitions.topology import AgentNode, Edge, GraphTopology, LogicNode


def test_agent_overrides_edge_cases() -> None:
    """Test edge cases for AgentNode overrides."""
    # Empty overrides should be valid
    node_empty = AgentNode(id="a1", agent_name="test", overrides={})
    assert node_empty.overrides == {}

    # None overrides should be valid (default)
    node_none = AgentNode(id="a2", agent_name="test", overrides=None)
    assert node_none.overrides is None

    # Deeply nested overrides (serialization check)
    deep_dict = {"level1": {"level2": {"level3": "value"}}}
    node_deep = AgentNode(id="a3", agent_name="test", overrides=deep_dict)
    assert node_deep.overrides == deep_dict


def test_topology_self_reference() -> None:
    """Test that self-referencing edges are valid and validated correctly."""
    n1 = LogicNode(id="n1", code="pass")
    # Edge from n1 to n1 (loop)
    edge = Edge(source_node_id="n1", target_node_id="n1")

    topo = GraphTopology(nodes=[n1], edges=[edge])
    assert len(topo.edges) == 1
    assert topo.edges[0].source_node_id == "n1"
    assert topo.edges[0].target_node_id == "n1"


def test_topology_disconnected_node() -> None:
    """Test that disconnected nodes (islands) are valid."""
    n1 = LogicNode(id="n1", code="pass")
    n2 = LogicNode(id="n2", code="pass")
    # Edge only connects n1 -> n1, n2 is isolated
    edge = Edge(source_node_id="n1", target_node_id="n1")

    topo = GraphTopology(nodes=[n1, n2], edges=[edge])
    assert len(topo.nodes) == 2
    # This confirms the validator doesn't enforce connectivity, only referential integrity


def test_event_payload_strictness_extra_fields() -> None:
    """Test that extra fields in payload are forbidden/ignored based on config."""
    # BaseNodePayload has extra='ignore' usually, let's verify specific behavior for GraphEvent
    # If we pass extra fields to the Pydantic model constructor, they should be ignored/dropped
    # if extra='ignore', or raise if extra='forbid'.

    # Current definition: BaseNodePayload has config dict with extra="ignore"

    # Using explicit model
    payload_data = {"status": "RUNNING", "node_id": "n1", "timestamp": 123.0, "extra_junk": "should_be_ignored"}

    # Should NOT raise, but field should be stripped
    event = GraphEventNodeStart(
        event_type="NODE_START",
        run_id="r1",
        node_id="n1",
        timestamp=123.0,
        payload=payload_data,  # type: ignore [arg-type] # Mypy sees the mismatch, runtime handles it
        visual_metadata={},
    )

    # Check if extra_junk is in the payload model dump
    dump = event.payload.model_dump()
    assert "extra_junk" not in dump


def test_metadata_boundaries() -> None:
    """Test metadata boundaries."""
    # Empty metadata
    n1 = LogicNode(id="n1", code="pass", metadata={})
    assert n1.metadata == {}

    # Large metadata
    large_meta = {f"k{i}": i for i in range(1000)}
    n2 = LogicNode(id="n2", code="pass", metadata=large_meta)
    assert len(n2.metadata) == 1000

    # Mixed types
    mixed_meta = {"int": 1, "bool": True, "list": [1, 2], "dict": {"a": "b"}}
    n3 = LogicNode(id="n3", code="pass", metadata=mixed_meta)
    assert n3.metadata["list"] == [1, 2]
