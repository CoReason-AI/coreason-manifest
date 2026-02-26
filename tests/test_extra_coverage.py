import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import FlowDefinitions, FlowMetadata, LinearFlow
from coreason_manifest.spec.core.governance import ToolAccessPolicy
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, InspectorNode
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.utils.validator import _validate_data_flow


def test_governance_tool_access_policy_critical() -> None:
    # Critical requires auth=True
    with pytest.raises(ValueError, match="Critical tools must require authentication"):
        ToolAccessPolicy(risk_level=RiskLevel.CRITICAL, require_auth=False)


def test_tool_capability_critical_description() -> None:
    # Critical requires description
    with pytest.raises(ValidationError, match="Critical but lacks a description"):
        ToolCapability(name="nuke", type="capability", risk_level=RiskLevel.CRITICAL, description="")


def test_gatekeeper_critical_tools() -> None:
    # Test _enforce_red_button_rule with critical tool
    tool = ToolCapability(name="nuke", risk_level=RiskLevel.CRITICAL, description="desc")
    pack = ToolPack(kind="ToolPack", namespace="p", tools=[tool], dependencies=[], env_vars=[])

    defs = FlowDefinitions(profiles={"p": CognitiveProfile(role="r", persona="p")}, tool_packs={"p": pack})

    agent = AgentNode(id="a1", type="agent", profile="p", tools=["nuke"])
    flow = LinearFlow.model_construct(
        kind="LinearFlow", metadata=FlowMetadata(name="t", version="1"), definitions=defs, steps=[agent]
    )

    reports = validate_policy(flow)
    assert any("critical tools ['nuke']" in str(r.details.get("reason", "")) for r in reports)
    assert any("requires high-risk features" in r.message for r in reports)


def test_governance_critical_defaults() -> None:
    # Test set_defaults logic for critical tools

    # Case 1: Critical enum, auth=None -> auth=True
    pol2 = ToolAccessPolicy(risk_level=RiskLevel.CRITICAL)
    assert pol2.require_auth is True

    # Case 2: Critical, auth=False -> ValueError (Covers line 66)
    with pytest.raises(ValueError, match="Critical tools must require authentication"):
        ToolAccessPolicy(risk_level=RiskLevel.CRITICAL, require_auth=False)

    # Case 3: Critical string, auth=False -> ValueError (Covers string logic branch)
    # The validator raises ValueError before Pydantic checks types.
    with pytest.raises(ValueError, match="Critical tools must require authentication"):
        ToolAccessPolicy(risk_level="critical", require_auth=False)  # type: ignore

    # Case 3b: Critical string, auth=None -> ValidationError
    # Here validator sets auth=True, but then Pydantic fails on "critical" string not being Enum.
    with pytest.raises(ValidationError):
        ToolAccessPolicy(risk_level="critical")  # type: ignore

    # Case 4: Non-critical, auth=None -> auth=False (Covers lines 67-68)
    pol3 = ToolAccessPolicy(risk_level=RiskLevel.STANDARD)
    assert pol3.require_auth is False


def test_validator_inspector_type_warning_direct() -> None:
    # Direct test of _validate_data_flow to ensure coverage of the warning logic
    node = InspectorNode(
        id="i1",
        type="inspector",
        target_variable="target",
        output_variable="out",
        mode="programmatic",
        criteria="regex:.*",
    )
    st = {"target": "object", "out": "string"}

    reports = _validate_data_flow([node], st, None)
    assert any(r.severity == "warning" and "Type Warning" in r.message for r in reports)
