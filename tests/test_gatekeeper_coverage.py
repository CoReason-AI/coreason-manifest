from coreason_manifest.spec.core.flow import FlowDefinitions as Definitions
from coreason_manifest.spec.core.flow import FlowMetadata, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.core.nodes import CognitiveProfile as Profile
from coreason_manifest.utils.gatekeeper import validate_policy


def test_gatekeeper_capability_error_handling() -> None:
    """
    Test that an AttributeError in required_capabilities is caught and treated as empty capabilities.
    Coverage for gatekeeper.py line 96.
    """
    # Use model_construct to bypass validation.
    # We pass an empty object() as reasoning.
    # Calling object().required_capabilities() will raise AttributeError.
    profile = Profile.model_construct(
        role="broken",
        persona="broken",
        reasoning=object(),  # type: ignore[arg-type]
        fast_path=None,
    )

    flow = LinearFlow(
        kind="LinearFlow",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        definitions=Definitions(profiles={"broken": profile}),
        sequence=[AgentNode(id="a1", metadata={}, type="agent", profile="broken", tools=[])],
    )

    # Should not crash
    reports = validate_policy(flow)
    # Should be empty reports as no policies violated (empty caps due to exception)
    assert isinstance(reports, list)

def test_gatekeeper_schemeless_url() -> None:
    """Cover line 93 in gatekeeper.py: schemeless URL handling."""
    from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
    from coreason_manifest.spec.core.governance import Governance

    # Define a tool with a schemeless URL
    tool = ToolCapability(
        name="schemeless_tool",
        description="A tool without schema",
        url="evil.com/api",  # No https://
        risk_level="standard",
    )

    flow = LinearFlow(
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="Schemeless Test", version="1.0", description="desc", tags=[]),
        definitions=Definitions(
            tool_packs={
                "pack1": ToolPack(kind="ToolPack", namespace="pack1", tools=[tool], dependencies=[], env_vars=[])
            }
        ),
        sequence=[],
        governance=Governance(allowed_domains=["good.com"]),  # evil.com should fail
    )

    reports = validate_policy(flow)

    # Should find a violation for evil.com
    violation = next((r for r in reports if "blocked domain" in r.message), None)
    assert violation is not None
    assert "evil.com" in violation.message


def test_gatekeeper_port_stripping() -> None:
    """Cover port stripping logic (line 93)."""
    from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
    from coreason_manifest.spec.core.governance import Governance

    tool = ToolCapability(
        name="port_tool",
        description="Tool with port",
        url="https://evil.com:8080/api",
        risk_level="standard",
    )

    flow = LinearFlow(
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="Port Test", version="1.0", description="desc", tags=[]),
        definitions=Definitions(
            tool_packs={
                "pack1": ToolPack(kind="ToolPack", namespace="pack1", tools=[tool], dependencies=[], env_vars=[])
            }
        ),
        sequence=[],
        governance=Governance(allowed_domains=["good.com"]),
    )

    reports = validate_policy(flow)
    violation = next((r for r in reports if "blocked domain" in r.message), None)
    assert violation is not None
    assert "evil.com" in violation.message  # Should be stripped of port
