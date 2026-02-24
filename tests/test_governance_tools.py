from coreason_manifest.spec.core.co_intelligence import CoIntelligencePolicy
from coreason_manifest.spec.core.flow import FlowDefinitions, FlowMetadata, LinearFlow
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.utils.gatekeeper import validate_policy


def test_critical_tool_requires_guard() -> None:
    # Define a critical tool
    critical_tool = ToolCapability(name="delete_db", risk_level=RiskLevel.CRITICAL, description="Deletes the database")
    safe_tool = ToolCapability(name="read_db", risk_level=RiskLevel.SAFE)

    pack = ToolPack(
        kind="ToolPack", namespace="db_tools", tools=[critical_tool, safe_tool], dependencies=[], env_vars=[]
    )

    # Need a profile for integrity check
    profile = CognitiveProfile(role="tester", persona="tester", reasoning=None, fast_path=None)

    definitions = FlowDefinitions(
        profiles={"default_profile": profile}, tool_packs={"db_tools": pack}, supervision_templates={}
    )

    # Define Agent using critical tool
    agent = AgentNode(id="agent-1", metadata={}, type="agent", profile="default_profile", tools=["delete_db"])

    # Unguarded Flow
    flow_unguarded = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
        definitions=definitions,
        steps=[agent],
    )

    errors = validate_policy(flow_unguarded)
    # Check for specific error message
    assert any("critical tools ['delete_db']" in e.message for e in errors)
    assert any("no Co-Intelligence Policy" in e.message for e in errors)

    # Guarded Flow
    gov = Governance(co_intelligence=CoIntelligencePolicy())
    flow_guarded = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
        definitions=definitions,
        steps=[agent],
        governance=gov,
    )

    errors = validate_policy(flow_guarded)
    # Filter for tool policy errors
    tool_errors = [e for e in errors if "critical tools" in e.message]
    assert not tool_errors


def test_safe_tool_allowed() -> None:
    # Define tools
    safe_tool = ToolCapability(name="read_db", risk_level=RiskLevel.SAFE)

    pack = ToolPack(kind="ToolPack", namespace="db_tools", tools=[safe_tool], dependencies=[], env_vars=[])

    profile = CognitiveProfile(role="tester", persona="tester", reasoning=None, fast_path=None)

    definitions = FlowDefinitions(
        profiles={"default_profile": profile}, tool_packs={"db_tools": pack}, supervision_templates={}
    )

    agent = AgentNode(id="agent-1", metadata={}, type="agent", profile="default_profile", tools=["read_db"])

    flow = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
        definitions=definitions,
        steps=[agent],
    )

    errors = validate_policy(flow)
    assert not errors
