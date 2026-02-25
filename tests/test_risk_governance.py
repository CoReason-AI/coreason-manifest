import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import (
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.governance import Governance, ToolAccessPolicy
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.utils.validator import validate_flow


def test_risk_governance_graph_flow() -> None:
    # Construct a flow with a critical tool
    critical_tool = ToolCapability(
        name="nuke_database", type="capability", risk_level=RiskLevel.CRITICAL, description="Deletes all data."
    )

    pack = ToolPack(namespace="danger_ops", tools=[critical_tool])

    definitions = FlowDefinitions(tool_packs={"danger": pack})

    # Case 1: No kill switch
    flow = GraphFlow(
        metadata=FlowMetadata(name="DangerousFlow", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=definitions,
        governance=Governance(),  # No max_risk_level
    )
    assert flow.governance is not None
    assert flow.governance.max_risk_level is None
    errors = validate_flow(flow)
    # Assuming no other errors (empty graph is error? Yes "Graph must contain at least one node")
    # But we check specific error.
    assert not any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" for e in errors)

    # Case 2: Kill switch set to 'standard'
    flow_blocked = GraphFlow(
        metadata=FlowMetadata(name="DangerousFlowBlocked", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=definitions,
        governance=Governance(max_risk_level=RiskLevel.STANDARD),
    )
    errors = validate_flow(flow_blocked)
    assert any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" and e.details.get("tool_name") == "nuke_database" for e in errors)

    # Case 3: Kill switch set to 'critical' (should PASS)
    flow_allowed = GraphFlow(
        metadata=FlowMetadata(name="DangerousFlowAllowed", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=definitions,
        governance=Governance(max_risk_level=RiskLevel.CRITICAL),
    )
    errors = validate_flow(flow_allowed)
    assert not any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" for e in errors)


def test_risk_governance_linear_flow() -> None:
    # Construct a flow with a critical tool
    critical_tool = ToolCapability(
        name="nuke_database", type="capability", risk_level=RiskLevel.CRITICAL, description="Deletes all data."
    )

    pack = ToolPack(namespace="danger_ops", tools=[critical_tool])

    definitions = FlowDefinitions(tool_packs={"danger": pack})

    # Case 1: No kill switch
    flow = LinearFlow(
        metadata=FlowMetadata(name="DangerousFlow", version="1.0.0"),
        steps=[],
        definitions=definitions,
        governance=Governance(),  # No max_risk_level
    )
    errors = validate_flow(flow)
    assert not any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" for e in errors)

    # Case 2: Kill switch set to 'standard'
    flow_blocked = LinearFlow(
        metadata=FlowMetadata(name="DangerousFlowBlocked", version="1.0.0"),
        steps=[],
        definitions=definitions,
        governance=Governance(max_risk_level=RiskLevel.STANDARD),
    )
    errors = validate_flow(flow_blocked)
    assert any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" for e in errors)

    # Case 3: Kill switch set to 'critical' (should PASS)
    flow_allowed = LinearFlow(
        metadata=FlowMetadata(name="DangerousFlowAllowed", version="1.0.0"),
        steps=[],
        definitions=definitions,
        governance=Governance(max_risk_level=RiskLevel.CRITICAL),
    )
    errors = validate_flow(flow_allowed)
    assert not any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" for e in errors)


def test_risk_enum_update() -> None:
    # Test valid values
    ToolAccessPolicy(risk_level=RiskLevel.SAFE)
    ToolAccessPolicy(risk_level=RiskLevel.STANDARD)
    ToolAccessPolicy(risk_level=RiskLevel.CRITICAL, require_auth=True)

    # Test invalid value 'minimal'
    with pytest.raises(ValidationError):
        ToolAccessPolicy(risk_level="minimal")  # type: ignore[arg-type]


def test_inline_tool_bypass_prevention() -> None:
    """
    Test that the scanner detects a critical tool hidden inside a node's inline_tools attribute
    (simulating a node type that allows inline tool definitions).
    """
    from typing import Literal

    from pydantic import Field

    from coreason_manifest.spec.core.nodes import Node

    class HackerNode(Node):
        type: Literal["hacker"] = "hacker"
        inline_tools: list[ToolCapability] = Field(default_factory=list)

    critical_tool = ToolCapability(
        name="inline_nuke", type="capability", risk_level=RiskLevel.CRITICAL, description="Hidden inline tool"
    )

    hacker_node = HackerNode(id="hacker_1", inline_tools=[critical_tool])

    # Construct a LinearFlow with this node
    # Since LinearFlow.steps expects AnyNode (which doesn't include HackerNode), we use model_construct or similar to bypass typing if possible,
    # or just rely on runtime inspection.
    # LinearFlow steps is list[AnyNode]. AnyNode is a Union.
    # Pydantic validation of LinearFlow might fail if we pass HackerNode.
    # So we use model_construct.

    flow = LinearFlow.model_construct(
        kind="LinearFlow",
        metadata=FlowMetadata(name="HackerFlow", version="1.0.0"),
        steps=[hacker_node],
        definitions=None,
        governance=Governance(max_risk_level=RiskLevel.STANDARD),
    )

    errors = validate_flow(flow)
    assert any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" and e.details.get("tool_name") == "inline_nuke" for e in errors)


def test_scan_remote_uri_fail_closed() -> None:
    """
    Test that the scanner enforces fail-closed logic for remote URIs (://).
    These should be treated as CRITICAL risk.
    """
    from coreason_manifest.spec.core.nodes import AgentNode

    # AgentNode with a remote tool reference
    agent = AgentNode(id="agent_remote", type="agent", profile="default", tools=["mcp://remote-server/tools/dangerous"])

    # If max_risk is STANDARD, CRITICAL (remote) should raise
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="RemoteFlow", version="1.0.0"),
        steps=[agent],
        governance=Governance(max_risk_level=RiskLevel.STANDARD),
    )

    errors = validate_flow(flow)
    assert any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" and e.details.get("assumed_risk") == "critical" for e in errors)


def test_scan_remote_uri_allowed_if_critical() -> None:
    """
    Test that remote URIs are allowed if the global policy allows CRITICAL risk.
    """
    from coreason_manifest.spec.core.nodes import AgentNode

    agent = AgentNode(
        id="agent_remote_allowed", type="agent", profile="default", tools=["https://trusted-but-remote.com/api"]
    )

    flow = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="RemoteFlow", version="1.0.0"),
        steps=[agent],
        governance=Governance(max_risk_level=RiskLevel.CRITICAL),
    )

    errors = validate_flow(flow)
    assert not any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" for e in errors)


def test_scan_skips_local_string_references() -> None:
    """
    Test that the scanner ignores local string references (no ://) in node tools.
    """
    from coreason_manifest.spec.core.nodes import AgentNode

    # AgentNode has tools: list[str]
    agent = AgentNode(id="agent1", type="agent", profile="default", tools=["some_tool_ref", "another_tool_ref"])

    # Should run without error and without checking these strings
    flow = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="LocalFlow", version="1.0.0"),
        steps=[agent],
        governance=Governance(max_risk_level=RiskLevel.SAFE),
    )

    errors = validate_flow(flow)
    assert not any(e.code == "ERR_SEC_KILL_SWITCH_VIOLATION" for e in errors)
