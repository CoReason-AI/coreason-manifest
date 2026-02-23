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


def test_scan_raw_dicts_fail_closed() -> None:
    """
    Test fail-closed behavior for raw dicts missing risk_level.
    """
    from typing import Any, Literal

    from pydantic import Field

    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations
    from coreason_manifest.spec.core.nodes import Node

    class RawToolNode(Node):
        type: Literal["raw_tool_node"] = "raw_tool_node"
        inline_tools: list[Any] = Field(default_factory=list)

    # Tool with NO risk level -> Should default to CRITICAL
    raw_tool_missing_risk = {
        "type": "capability",
        "name": "mystery_tool",
        # risk_level MISSING
    }

    node = RawToolNode(id="raw_1", inline_tools=[raw_tool_missing_risk])

    max_risk = RiskLevel.STANDARD

    with pytest.raises(ManifestError) as exc_info:
        _scan_for_kill_switch_violations(
            max_risk=max_risk,
            definitions=None,
            nodes=[node],  # type: ignore[list-item]
        )

    assert "Security Violation" in str(exc_info.value)
    assert "mystery_tool" in str(exc_info.value)
    assert "critical" in str(exc_info.value)


def test_scan_raw_dicts_malformed() -> None:
    """
    Test fail-closed behavior for malformed raw dicts (missing required fields)
    that cause ToolCapability validation to fail.
    """
    from typing import Any, Literal

    from pydantic import Field

    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations
    from coreason_manifest.spec.core.nodes import Node

    class RawToolNode(Node):
        type: Literal["raw_tool_node"] = "raw_tool_node"
        inline_tools: list[Any] = Field(default_factory=list)

    # Tool with MISSING name -> validation fails -> falls back to Critical
    raw_tool_malformed = {
        "type": "capability",
        # name MISSING
        "description": "Invalid tool",
    }

    node = RawToolNode(id="raw_malformed", inline_tools=[raw_tool_malformed])

    max_risk = RiskLevel.STANDARD

    with pytest.raises(ManifestError) as exc_info:
        _scan_for_kill_switch_violations(
            max_risk=max_risk,
            definitions=None,
            nodes=[node],  # type: ignore[list-item]
        )

    # Should catch the "unknown_malformed_tool" fallback
    assert "Security Violation" in str(exc_info.value)
    assert "unknown_malformed_tool" in str(exc_info.value)


def test_scan_raw_dicts_valid_with_risk() -> None:
    """
    Test scanning of a valid raw dict that explicitly includes risk_level.
    """
    from typing import Any, Literal

    from pydantic import Field

    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations
    from coreason_manifest.spec.core.nodes import Node

    class RawToolNode(Node):
        type: Literal["raw_tool_node"] = "raw_tool_node"
        inline_tools: list[Any] = Field(default_factory=list)

    # Valid tool with CRITICAL risk
    raw_tool_critical = {
        "type": "capability",
        "name": "explicit_critical_tool",
        "risk_level": "critical",
        "description": "Explicit critical tool",
    }

    node = RawToolNode(id="raw_valid", inline_tools=[raw_tool_critical])

    max_risk = RiskLevel.STANDARD

    with pytest.raises(ManifestError) as exc_info:
        _scan_for_kill_switch_violations(
            max_risk=max_risk,
            definitions=None,
            nodes=[node],  # type: ignore[list-item]
        )

    assert "Security Violation" in str(exc_info.value)
    assert "explicit_critical_tool" in str(exc_info.value)


def test_scan_raw_dicts_valid_safe() -> None:
    """
    Test scanning of a valid raw dict with safe risk (should not raise).
    Ensures the happy path for raw dict parsing is covered.
    """
    from typing import Any, Literal

    from pydantic import Field

    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations
    from coreason_manifest.spec.core.nodes import Node

    class RawToolNode(Node):
        type: Literal["raw_tool_node"] = "raw_tool_node"
        inline_tools: list[Any] = Field(default_factory=list)

    # Valid tool with SAFE risk
    raw_tool_safe = {
        "type": "capability",
        "name": "safe_tool",
        "risk_level": "safe",
        "description": "Safe tool",
    }

    node = RawToolNode(id="raw_safe", inline_tools=[raw_tool_safe])

    max_risk = RiskLevel.STANDARD

    # Should NOT raise
    _scan_for_kill_switch_violations(
        max_risk=max_risk,
        definitions=None,
        nodes=[node],  # type: ignore[list-item]
    )


def test_scan_raw_dicts_invalid_risk() -> None:
    """
    Test scanning of a raw dict with invalid risk string.
    Should fail enum conversion, pass, then fail validation, then fallback to critical.
    """
    from typing import Any, Literal

    from pydantic import Field

    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations
    from coreason_manifest.spec.core.nodes import Node

    class RawToolNode(Node):
        type: Literal["raw_tool_node"] = "raw_tool_node"
        inline_tools: list[Any] = Field(default_factory=list)

    raw_tool_invalid = {
        "type": "capability",
        "name": "invalid_risk_tool",
        "risk_level": "extreme",  # Invalid enum value
        "description": "Invalid risk tool",
    }

    node = RawToolNode(id="raw_invalid", inline_tools=[raw_tool_invalid])

    max_risk = RiskLevel.STANDARD

    # Should raise ManifestError because it falls back to CRITICAL
    with pytest.raises(ManifestError) as exc_info:
        _scan_for_kill_switch_violations(
            max_risk=max_risk,
            definitions=None,
            nodes=[node],  # type: ignore[list-item]
        )

    assert "Security Violation" in str(exc_info.value)
    assert "invalid_risk_tool" in str(exc_info.value)
    assert "critical" in str(exc_info.value)  # Fallback risk


def test_scan_skips_string_references() -> None:
    """
    Test that the scanner ignores string references in node tools,
    covering the 'else' path of the type check.
    """
    from coreason_manifest.spec.core.flow import _scan_for_kill_switch_violations
    from coreason_manifest.spec.core.nodes import AgentNode

    # AgentNode has tools: list[str]
    agent = AgentNode(id="agent1", type="agent", profile="default", tools=["some_tool_ref", "another_tool_ref"])

    # Should run without error and without checking these strings
    # (since they are references, not inline definitions)
    _scan_for_kill_switch_violations(max_risk=RiskLevel.SAFE, definitions=None, nodes=[agent])
