from coreason_manifest.spec.core.flow import FlowDefinitions as Definitions
from coreason_manifest.spec.core.flow import FlowMetadata, LinearFlow
from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.core.nodes import AgentNode
from coreason_manifest.spec.core.nodes import CognitiveProfile as Profile
from coreason_manifest.spec.core.tools import MCPResource, MCPServerConfig
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
        metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
        definitions=Definitions(profiles={"broken": profile}),
        steps=[AgentNode(id="a1", metadata={}, type="agent", profile="broken", tools=[])],
    )

    # Should not crash
    reports = validate_policy(flow)
    # Should be empty reports as no policies violated (empty caps due to exception)
    assert isinstance(reports, list)


def test_gatekeeper_schemeless_url() -> None:
    """Cover schemeless URL handling."""
    # MCPResource uri is a string, so Pydantic won't fail validation for format unless we add a validator.
    # But validate_policy might flag it or ignore it.

    # We can test that validate_policy handles it gracefully.

    tool = MCPResource(
        name="schemeless_tool", description="A tool without schema", uri="evil.com/api", mime_type="text/plain"
    )

    flow = LinearFlow(
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="Schemeless Test", version="1.0.0", description="desc", tags=[]),
        definitions=Definitions(
            mcp_servers={
                "pack1": MCPServerConfig(
                    kind="MCPServerConfig", namespace="pack1", tools=[tool], dependencies=[], env_vars=[]
                )
            }
        ),
        steps=[],
        governance=Governance(allowed_domains=["good.com"]),
    )

    reports = validate_policy(flow)
    # Since uri doesn't have ://, extraction might fail or return empty domain.
    # validate_policy logic: if "://" in uri: domain = ...
    # So it skips domain check for schemeless.
    # We assert no crash.
    assert isinstance(reports, list)


def test_gatekeeper_port_stripping() -> None:
    """Cover port stripping logic."""
    # Use MCPResource
    tool = MCPResource(
        name="port_tool", description="Tool with port", uri="https://evil.com:8080/api", mime_type="text/plain"
    )

    flow = LinearFlow(
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="Port Test", version="1.0.0", description="desc", tags=[]),
        definitions=Definitions(
            mcp_servers={
                "pack1": MCPServerConfig(
                    kind="MCPServerConfig", namespace="pack1", tools=[tool], dependencies=[], env_vars=[]
                )
            }
        ),
        steps=[],
        governance=Governance(allowed_domains=["good.com"]),
    )

    reports = validate_policy(flow)
    violation = next((r for r in reports if "blocked domain" in r.message), None)

    # Note: validate_policy uses canonicalize_domain which strips port.
    # "https://evil.com:8080/api" -> domain "evil.com"
    # "evil.com" is not in allowed_domains ("good.com").
    # So it should be blocked.

    assert violation is not None
    assert "evil.com" in violation.message
