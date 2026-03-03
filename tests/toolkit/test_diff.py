# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.core.oversight.resilience import RetryStrategy
from coreason_manifest.core.workflow.flow import Edge, FlowInterface, FlowMetadata, Graph, GraphFlow, LinearFlow
from coreason_manifest.core.workflow.nodes.agent import AgentNode, CognitiveProfile
from coreason_manifest.toolkit.diff import ChangeCategory, ChangeType, compare_flows


def test_compare_flows_add_tool() -> None:
    """Test that adding a tool is categorized as a FEATURE change."""
    profile = CognitiveProfile(role="assistant", persona="helpful")

    old_node = AgentNode(id="agent_1", profile=profile, tools=["tool_a"], operational_policy=None)
    new_node = AgentNode(id="agent_1", profile=profile, tools=["tool_a", "tool_b"], operational_policy=None)

    old_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": old_node}, entry_point="agent_1", edges=[]),
    )

    new_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": new_node}, entry_point="agent_1", edges=[]),
    )

    report = compare_flows(old_flow, new_flow)

    # We should find an addition to the tools list
    tool_changes = [c for c in report.changes if "tools" in c.path]
    assert len(tool_changes) > 0
    assert any(c.category == ChangeCategory.FEATURE for c in tool_changes)
    assert any(c.change_type == ChangeType.ADD and c.new_value == "tool_b" for c in tool_changes)


def test_compare_flows_change_governance() -> None:
    """Test that changing a governance aspect yields a GOVERNANCE change."""
    profile = CognitiveProfile(role="assistant", persona="helpful")

    old_node = AgentNode(
        id="agent_1", profile=profile, resilience=RetryStrategy(max_attempts=1), operational_policy=None
    )
    new_node = AgentNode(
        id="agent_1", profile=profile, resilience=RetryStrategy(max_attempts=3), operational_policy=None
    )

    old_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": old_node}, entry_point="agent_1", edges=[]),
    )

    new_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": new_node}, entry_point="agent_1", edges=[]),
    )

    report = compare_flows(old_flow, new_flow)

    # We should find a modification to the resilience/retry_strategy
    gov_changes = [c for c in report.changes if "resilience" in c.path]
    assert len(gov_changes) > 0
    assert any(c.category == ChangeCategory.GOVERNANCE for c in gov_changes)


def test_compare_flows_remove_edge() -> None:
    """Test that removing an edge yields a BREAKING change."""
    profile = CognitiveProfile(role="assistant", persona="helpful")

    node_1 = AgentNode(id="agent_1", profile=profile, operational_policy=None)
    node_2 = AgentNode(id="agent_2", profile=profile, operational_policy=None)

    old_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(
            nodes={"agent_1": node_1, "agent_2": node_2},
            entry_point="agent_1",
            edges=[Edge(from_node="agent_1", to_node="agent_2")],
        ),
    )

    new_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": node_1, "agent_2": node_2}, entry_point="agent_1", edges=[]),
    )

    report = compare_flows(old_flow, new_flow)

    # We should find a removal from the edges list
    edge_changes = [c for c in report.changes if "edges" in c.path]
    assert len(edge_changes) > 0
    assert any(c.category == ChangeCategory.BREAKING for c in edge_changes)
    assert any(c.change_type == ChangeType.REMOVE for c in edge_changes)


def test_compare_flows_change_description() -> None:
    """Test that changing a description yields a PATCH change."""
    profile = CognitiveProfile(role="assistant", persona="helpful")

    # We will use metadata to test a simple dict change, because AgentNode does not have a "description" field.
    old_node = AgentNode(id="agent_1", profile=profile, metadata={"description": "Old desc"}, operational_policy=None)
    new_node = AgentNode(id="agent_1", profile=profile, metadata={"description": "New desc"}, operational_policy=None)

    old_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": old_node}, entry_point="agent_1", edges=[]),
    )

    new_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": new_node}, entry_point="agent_1", edges=[]),
    )

    report = compare_flows(old_flow, new_flow)

    patch_changes = [c for c in report.changes if "description" in c.path]
    assert len(patch_changes) > 0
    assert any(c.category == ChangeCategory.PATCH for c in patch_changes)


def test_compare_flows_change_id_breaking() -> None:
    """Test that changing a node ID yields a BREAKING change."""
    profile = CognitiveProfile(role="assistant", persona="helpful")

    old_node = AgentNode(id="agent_1", profile=profile, operational_policy=None)
    new_node = AgentNode(id="agent_1_new", profile=profile, operational_policy=None)

    old_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": old_node}, entry_point="agent_1", edges=[]),
    )

    new_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1_new": new_node}, entry_point="agent_1_new", edges=[]),
    )

    report = compare_flows(old_flow, new_flow)

    id_changes = [c for c in report.changes if "agent_1_new" in c.path or "entry_point" in c.path or "id" in c.path]
    assert len(id_changes) > 0
    assert any(c.category == ChangeCategory.BREAKING for c in id_changes)


def test_compare_flows_list_different_lengths() -> None:
    """Test comparing lists of different lengths to hit insert/delete logic directly."""
    # Build two sets of tools with different lengths
    profile = CognitiveProfile(role="assistant", persona="helpful")

    old_node = AgentNode(id="agent_1", profile=profile, tools=["tool_1", "tool_2"], operational_policy=None)
    new_node = AgentNode(
        id="agent_1", profile=profile, tools=["tool_1", "tool_2", "tool_3", "tool_4"], operational_policy=None
    )

    old_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": old_node}, entry_point="agent_1", edges=[]),
    )

    new_flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={"agent_1": new_node}, entry_point="agent_1", edges=[]),
    )

    report = compare_flows(old_flow, new_flow)

    tool_changes = [c for c in report.changes if "tools" in c.path and c.change_type == ChangeType.ADD]
    assert len(tool_changes) == 2  # Added tool_3 and tool_4


def test_compare_flows_list_replace() -> None:
    """Test comparing lists with replacements to hit replace logic."""
    profile = CognitiveProfile(role="assistant", persona="helpful")

    # We use linear flows to easily test replacing steps
    node1 = AgentNode(id="step_1", profile=profile, operational_policy=None)
    node2_old = AgentNode(id="step_2_old", profile=profile, operational_policy=None)
    node2_new = AgentNode(id="step_2_new", profile=profile, operational_policy=None)

    old_flow = LinearFlow.model_construct(
        type="linear",
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0"),
        steps=[node1, node2_old],
    )

    new_flow = LinearFlow.model_construct(
        type="linear",
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0"),
        steps=[node1, node2_new],
    )

    report = compare_flows(old_flow, new_flow)

    step_changes = [c for c in report.changes if "steps" in c.path]
    assert len(step_changes) > 0


def test_compare_flows_linear_list_complex() -> None:
    """Test complex list changes to hit length difference branches."""
    profile = CognitiveProfile(role="assistant", persona="helpful")

    # Make a linear flow with 3 steps, change to 1 step
    node1 = AgentNode(id="step_1", profile=profile, operational_policy=None)
    node2 = AgentNode(id="step_2", profile=profile, operational_policy=None)
    node3 = AgentNode(id="step_3", profile=profile, operational_policy=None)

    old_flow = LinearFlow.model_construct(
        type="linear",
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0"),
        steps=[node1, node2, node3],
    )

    new_flow = LinearFlow.model_construct(
        type="linear",
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0"),
        steps=[node1],
    )

    report = compare_flows(old_flow, new_flow)

    # Check that steps were removed
    step_removals = [c for c in report.changes if "steps" in c.path and c.change_type == ChangeType.REMOVE]
    assert len(step_removals) == 2

    # Now test the reverse (1 step -> 3 steps)
    report2 = compare_flows(new_flow, old_flow)
    step_additions = [c for c in report2.changes if "steps" in c.path and c.change_type == ChangeType.ADD]
    assert len(step_additions) == 2
