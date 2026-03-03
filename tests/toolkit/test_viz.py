# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.core.workflow.flow import Edge, FlowInterface, FlowMetadata, Graph, GraphFlow, LinearFlow
from coreason_manifest.core.workflow.nodes.agent import AgentNode, CognitiveProfile
from coreason_manifest.core.workflow.nodes.human import HumanNode
from coreason_manifest.core.workflow.nodes.oversight import InspectorNode
from coreason_manifest.core.workflow.nodes.routing import SwitchNode
from coreason_manifest.core.workflow.nodes.swarm import SwarmNode
from coreason_manifest.core.workflow.nodes.system import PlaceholderNode
from coreason_manifest.toolkit.viz import flow_to_mermaid


def test_flow_to_mermaid_deterministic_and_shapes() -> None:
    """Test deterministic output sorting and correct polymorphic shape mapping."""
    profile = CognitiveProfile(role="assistant", persona="helpful")

    agent = AgentNode(id="node_b_agent", profile=profile, operational_policy=None)
    from coreason_manifest.core.oversight.resilience import EscalationStrategy

    human = HumanNode(
        id="node_a_human",
        prompt="Review this.",
        escalation=EscalationStrategy(
            type="escalate", queue_name="review", notification_level="info", timeout_seconds=3600
        ),
    )
    swarm = SwarmNode(
        id="node_c_swarm",
        worker_profile="assistant",
        workload_variable="items",
        distribution_strategy="sharded",
        max_concurrency=5,
        reducer_function="concat",
        output_variable="results",
        operational_policy=None,
    )
    switch = SwitchNode(id="node_d_switch", variable="state", cases={"true": "node_b_agent"}, default="node_a_human")
    inspector = InspectorNode(
        id="node_e_inspector", target_variable="results", criteria="Is it good?", output_variable="inspection_result"
    )

    flow = GraphFlow(
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph(
            nodes={
                "node_b_agent": agent,
                "node_a_human": human,
                "node_c_swarm": swarm,
                "node_d_switch": switch,
                "node_e_inspector": inspector,
            },
            entry_point="node_a_human",
            edges=[
                Edge(from_node="node_b_agent", to_node="node_c_swarm"),
                Edge(from_node="node_a_human", to_node="node_b_agent"),
            ],
        ),
    )

    mermaid_str = flow_to_mermaid(flow)

    expected = [
        "graph TD",
        "    node_a_human{{node_a_human}}",
        "    node_b_agent[node_b_agent]",
        "    node_c_swarm[[node_c_swarm]]",
        "    node_d_switch{node_d_switch}",
        "    node_e_inspector([node_e_inspector])",
        "    node_a_human --> node_b_agent",
        "    node_b_agent --> node_c_swarm",
    ]

    actual_lines = mermaid_str.split("\n")
    assert actual_lines == expected


def test_flow_to_mermaid_sanitization() -> None:
    """Test that malicious labels are sanitized."""
    # Using construct to bypass extra validation
    node = PlaceholderNode.model_construct(
        id='malicious"<[id]>;&', type="placeholder", required_capabilities=[], metadata={"label": "bad<[label]>;&"}
    )

    flow = GraphFlow.model_construct(
        type="graph",
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0"),
        interface=FlowInterface(),
        graph=Graph.model_construct(nodes={'malicious"<[id]>;&': node}, entry_point='malicious"<[id]>;&', edges=[]),
    )

    mermaid_str = flow_to_mermaid(flow)

    # Check that it has been safely sanitized
    assert "maliciousid" in mermaid_str
    assert '"' not in mermaid_str
    assert "<" not in mermaid_str
    assert "[" not in mermaid_str.replace("[maliciousid]", "")  # Only the shape brackets
    assert "]" not in mermaid_str.replace("[maliciousid]", "")
    assert ">" not in mermaid_str
    assert ";" not in mermaid_str
    assert "&" not in mermaid_str


def test_flow_to_mermaid_linear_flow_and_default_shape() -> None:
    """Test linear flow processing and default shape mapping."""
    # LinearFlow and a generic node type
    # Construct using dict to bypass frozen checks on modification
    node1 = PlaceholderNode.model_construct(**{"id": "step_1", "type": "unknown_type_for_default_shape", "required_capabilities": []})
    node2 = PlaceholderNode.model_construct(id="step_2", type="placeholder", required_capabilities=[])

    flow = LinearFlow.model_construct(
        type="linear",
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0"),
        steps=[node1, node2],
    )

    mermaid_str = flow_to_mermaid(flow)
    assert "step_1(step_1)" in mermaid_str  # default is round rect ( )
    assert "step_1 --> step_2" in mermaid_str
