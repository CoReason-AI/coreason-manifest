import pytest
from pydantic import ValidationError
from coreason_manifest.spec.core.governance import ToolAccessPolicy
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.spec.core.flow import LinearFlow, FlowMetadata, FlowDefinitions
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, HumanNode
from coreason_manifest.spec.core.resilience import EscalationStrategy

def test_governance_tool_access_policy_critical() -> None:
    # Critical requires auth=True
    with pytest.raises(ValueError, match="Critical tools must require authentication"):
        ToolAccessPolicy(risk_level=RiskLevel.CRITICAL, require_auth=False)

def test_tool_capability_critical_description() -> None:
    # Critical requires description
    with pytest.raises(ValidationError, match="Critical but lacks a description"):
        ToolCapability(
            name="nuke",
            type="capability",
            risk_level=RiskLevel.CRITICAL,
            description=""
        )

def test_gatekeeper_critical_tools() -> None:
    # Test _enforce_red_button_rule with critical tool
    tool = ToolCapability(name="nuke", risk_level=RiskLevel.CRITICAL, description="desc")
    pack = ToolPack(kind="ToolPack", namespace="p", tools=[tool], dependencies=[], env_vars=[])

    defs = FlowDefinitions(
        profiles={"p": CognitiveProfile(role="r", persona="p")},
        tool_packs={"p": pack}
    )

    agent = AgentNode(id="a1", type="agent", profile="p", tools=["nuke"])
    flow = LinearFlow.model_construct(
        kind="LinearFlow",
        metadata=FlowMetadata(name="t", version="1"),
        definitions=defs,
        steps=[agent]
    )

    reports = validate_policy(flow)
    assert any("critical tools ['nuke']" in str(r.details.get("reason", "")) for r in reports)
    assert any("requires high-risk features" in r.message for r in reports)
