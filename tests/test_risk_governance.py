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
    # Expect ManifestError (ValidationError wrapping ManifestError in model_validator?
    # Or strict ManifestError depending on how it's raised.
    # Validators raise ValueError/AssertionError/PydanticCustomError normally.
    # We raised ManifestError directly. Pydantic might wrap it if it's not a PydanticKnownError.)

    # Since we raise ManifestError inside the validator, and it inherits from Exception (likely),
    # Pydantic usually wraps exceptions in ValidationError unless we use specific Pydantic patterns.
    # However, for now let's catch ValidationError and check the cause or message.

    with pytest.raises(ManifestError) as exc_info:
        GraphFlow(
            metadata=FlowMetadata(name="DangerousFlowBlocked", version="1.0.0"),
            interface=FlowInterface(),
            graph=Graph(nodes={}, edges=[]),
            definitions=definitions,
            governance=Governance(max_risk_level=RiskLevel.STANDARD),
        )

    # Check that it contains our security message
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

    # Case 4: Tool with MISSING risk level with max_risk_level='standard' (should FAIL)
    # Note: With strong typing `AnyTool`, raw dicts are parsed into ToolCapability.
    # ToolCapability defaults risk_level to "standard".
    # So "missing risk level" in a dict passed to `AnyTool` field becomes "standard".
    # To test fail-closed for "missing/unknown", we need to simulate a tool that somehow bypasses default
    # or explicitly sets an invalid one (which enum prevents).
    #
    # However, if we pass a dict that DOES NOT match ToolCapability schema (e.g. invalid type),
    # Pydantic validation will fail before our validator runs.
    #
    # To test the `_scan_for_kill_switch_violations` logic for raw dicts, we need a place where raw dicts are allowed.
    # `FlowDefinitions.tools` is now `dict[str, AnyTool]`, so raw dicts get parsed.
    #
    # The only place raw dicts might exist unparsed is if we inject them into a Node's `inline_tools`
    # (if that field existed and was `Any`) or if we mock the object.
    #
    # But wait, `_scan_for_kill_switch_violations` iterates over `nodes` and checks `tools`/`inline_tools`.
    # AgentNode.tools is list[str].
    # Let's create a FakeNode with inline tools to test the scanner's raw dict handling
    # (if we can't instantiate it via Pydantic).


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

    # Define a custom node that supports inline tools
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

    # Flow with standard governance limit
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

    # Set limit to STANDARD. If mystery_tool defaults to CRITICAL, this should raise.
    max_risk = RiskLevel.STANDARD

    with pytest.raises(ManifestError) as exc_info:
        _scan_for_kill_switch_violations(
            max_risk=max_risk,
            definitions=None,
            nodes=[node],  # type: ignore[list-item]
        )

    assert "Security Violation" in str(exc_info.value)
    assert "mystery_tool" in str(exc_info.value)
    assert "critical" in str(exc_info.value)  # Defaulted value


def test_scan_raw_dicts_malformed() -> None:
    """
    Test fail-closed behavior for malformed raw dicts (missing required fields like name/type)
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
