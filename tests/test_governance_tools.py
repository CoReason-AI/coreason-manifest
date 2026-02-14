import pytest
from coreason_manifest.spec.core.tools import ToolPack, ToolCapability
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode, CognitiveProfile
from coreason_manifest.spec.core.flow import LinearFlow, FlowMetadata, FlowDefinitions
from coreason_manifest.utils.gatekeeper import validate_policy

def test_critical_tool_requires_guard():
    # Define a critical tool
    critical_tool = ToolCapability(name="delete_db", risk_level="critical")
    safe_tool = ToolCapability(name="read_db", risk_level="safe")

    pack = ToolPack(
        kind="ToolPack",
        namespace="db_tools",
        tools=[critical_tool, safe_tool],
        dependencies=[],
        env_vars=[]
    )

    # Need a profile for integrity check
    profile = CognitiveProfile(
        role="tester",
        persona="tester",
        reasoning=None,
        fast_path=None
    )

    definitions = FlowDefinitions(
        profiles={"default_profile": profile},
        tool_packs={"db_tools": pack},
        supervision_templates={}
    )

    # Define Agent using critical tool
    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        profile="default_profile",
        tools=["delete_db"]
    )

    # Unguarded Flow
    flow_unguarded = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="test", version="1", description="test", tags=[]),
        definitions=definitions,
        sequence=[agent]
    )

    errors = validate_policy(flow_unguarded)
    # Check for specific error message
    assert any("critical tools ['delete_db']" in e for e in errors)
    assert any("not guarded by a HumanNode" in e for e in errors)

    # Guarded Flow
    human = HumanNode(
        id="human-1",
        metadata={},
        supervision=None,
        type="human",
        prompt="Approve?",
        timeout_seconds=60,
        interaction_mode="blocking"
    )

    flow_guarded = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="test", version="1", description="test", tags=[]),
        definitions=definitions,
        sequence=[human, agent]
    )

    errors = validate_policy(flow_guarded)
    # Filter for tool policy errors
    tool_errors = [e for e in errors if "critical tools" in e]
    assert not tool_errors

def test_safe_tool_allowed():
    # Define tools
    safe_tool = ToolCapability(name="read_db", risk_level="safe")

    pack = ToolPack(
        kind="ToolPack",
        namespace="db_tools",
        tools=[safe_tool],
        dependencies=[],
        env_vars=[]
    )

    profile = CognitiveProfile(
        role="tester",
        persona="tester",
        reasoning=None,
        fast_path=None
    )

    definitions = FlowDefinitions(
        profiles={"default_profile": profile},
        tool_packs={"db_tools": pack},
        supervision_templates={}
    )

    agent = AgentNode(
        id="agent-1",
        metadata={},
        supervision=None,
        type="agent",
        profile="default_profile",
        tools=["read_db"]
    )

    flow = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="test", version="1", description="test", tags=[]),
        definitions=definitions,
        sequence=[agent]
    )

    errors = validate_policy(flow)
    assert not errors
