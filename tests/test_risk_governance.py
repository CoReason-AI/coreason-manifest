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
from coreason_manifest.spec.core.governance import Governance, OperationalPolicy, ToolAccessPolicy
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.spec.interop.exceptions import ManifestError


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

    # Case 2: Kill switch set to 'standard'
    with pytest.raises(ManifestError) as exc_info:
        GraphFlow(
            metadata=FlowMetadata(name="DangerousFlowBlocked", version="1.0.0"),
            interface=FlowInterface(),
            graph=Graph(nodes={}, edges=[]),
            definitions=definitions,
            governance=Governance(max_risk_level=RiskLevel.STANDARD),
        )

    assert "Security Violation" in str(exc_info.value)
    assert "nuke_database" in str(exc_info.value)

    # Case 3: Kill switch set to 'critical' (should PASS)
    GraphFlow(
        metadata=FlowMetadata(name="DangerousFlowAllowed", version="1.0.0"),
        interface=FlowInterface(),
        graph=Graph(nodes={}, edges=[]),
        definitions=definitions,
        governance=Governance(max_risk_level=RiskLevel.CRITICAL),
    )


def test_risk_governance_linear_flow() -> None:
    # Construct a flow with a critical tool
    critical_tool = ToolCapability(
        name="nuke_database", type="capability", risk_level=RiskLevel.CRITICAL, description="Deletes all data."
    )

    pack = ToolPack(namespace="danger_ops", tools=[critical_tool])

    definitions = FlowDefinitions(tool_packs={"danger": pack})

    # Case 1: No kill switch
    LinearFlow(
        metadata=FlowMetadata(name="DangerousFlow", version="1.0.0"),
        steps=[],
        definitions=definitions,
        governance=Governance(),  # No max_risk_level
    )

    # Case 2: Kill switch set to 'standard'
    with pytest.raises(ManifestError) as exc_info:
        LinearFlow(
            metadata=FlowMetadata(name="DangerousFlowBlocked", version="1.0.0"),
            steps=[],
            definitions=definitions,
            governance=Governance(max_risk_level=RiskLevel.STANDARD),
        )
    assert "Security Violation" in str(exc_info.value)

    # Case 3: Kill switch set to 'critical' (should PASS)
    LinearFlow(
        metadata=FlowMetadata(name="DangerousFlowAllowed", version="1.0.0"),
        steps=[],
        definitions=definitions,
        governance=Governance(max_risk_level=RiskLevel.CRITICAL),
    )


def test_risk_enum_update() -> None:
    # Test valid values
    ToolAccessPolicy(risk_level=RiskLevel.SAFE)
    ToolAccessPolicy(risk_level=RiskLevel.STANDARD)
    ToolAccessPolicy(risk_level=RiskLevel.CRITICAL, require_auth=True)

    # Test invalid value 'minimal'
    with pytest.raises(ValidationError):
        ToolAccessPolicy(risk_level="minimal")  # type: ignore[arg-type]


def test_operational_policy() -> None:
    # Instantiate an OperationalPolicy with mock data
    policy = OperationalPolicy(
        retry_counts={"default": 3},
        row_limits={"max": 1000},
        search_limits={"default": 10},
        timeout_durations={"default": 60},
        cost_multipliers={"gpt-4": 1.5},
        model_switching={"confidence": 0.8},
        custom_thresholds={"threshold1": 0.5},
        custom_limits={"limit1": 100},
    )

    # Assign it to a Governance object
    gov = Governance(operational_policy=policy)

    # Assert the values match
    assert gov.operational_policy is not None
    assert gov.operational_policy.retry_counts["default"] == 3
    assert gov.operational_policy.row_limits["max"] == 1000
    assert gov.operational_policy.search_limits["default"] == 10
    assert gov.operational_policy.timeout_durations["default"] == 60
    assert gov.operational_policy.cost_multipliers["gpt-4"] == 1.5
    assert gov.operational_policy.model_switching["confidence"] == 0.8
    assert gov.operational_policy.custom_thresholds["threshold1"] == 0.5
    assert gov.operational_policy.custom_limits["limit1"] == 100


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

    # Bypass GraphFlow validation (which strictly checks AnyNode types)
    # and test the scanner directly.
    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations

    max_risk = RiskLevel.STANDARD

    with pytest.raises(ManifestError) as exc_info:
        _scan_for_kill_switch_violations(
            max_risk=max_risk,
            definitions=None,
            nodes=[hacker_node],  # type: ignore[list-item]
        )

    assert "Security Violation" in str(exc_info.value)
    assert "inline_nuke" in str(exc_info.value)


def test_scan_remote_uri_fail_closed() -> None:
    """
    Test that the scanner enforces fail-closed logic for remote URIs (://).
    These should be treated as CRITICAL risk.
    """

    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations
    from coreason_manifest.spec.core.nodes import AgentNode

    # AgentNode with a remote tool reference
    agent = AgentNode(id="agent_remote", type="agent", profile="default", tools=["mcp://remote-server/tools/dangerous"])

    # If max_risk is STANDARD, CRITICAL (remote) should raise
    max_risk = RiskLevel.STANDARD

    with pytest.raises(ManifestError) as exc_info:
        _scan_for_kill_switch_violations(max_risk=max_risk, definitions=None, nodes=[agent])

    assert "Security Violation" in str(exc_info.value)
    assert "Unresolved remote tool URIs default to CRITICAL" in str(exc_info.value)
    # Check the structured fault context for the specific URI
    assert exc_info.value.fault.context["tool_uri"] == "mcp://remote-server/tools/dangerous"
    assert exc_info.value.fault.context["assumed_risk"] == "critical"


def test_scan_remote_uri_allowed_if_critical() -> None:
    """
    Test that remote URIs are allowed if the global policy allows CRITICAL risk.
    """
    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations
    from coreason_manifest.spec.core.nodes import AgentNode

    agent = AgentNode(
        id="agent_remote_allowed", type="agent", profile="default", tools=["https://trusted-but-remote.com/api"]
    )

    max_risk = RiskLevel.CRITICAL

    # Should NOT raise because max_risk >= CRITICAL
    _scan_for_kill_switch_violations(max_risk=max_risk, definitions=None, nodes=[agent])


def test_scan_skips_local_string_references() -> None:
    """
    Test that the scanner ignores local string references (no ://) in node tools.
    """
    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations
    from coreason_manifest.spec.core.nodes import AgentNode

    # AgentNode has tools: list[str]
    agent = AgentNode(id="agent1", type="agent", profile="default", tools=["some_tool_ref", "another_tool_ref"])

    # Should run without error and without checking these strings
    # (since they are references, not inline definitions, and not remote URIs)
    _scan_for_kill_switch_violations(max_risk=RiskLevel.SAFE, definitions=None, nodes=[agent])
