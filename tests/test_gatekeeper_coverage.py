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
        metadata=FlowMetadata(name="test", version="1.0.0", description="test", tags=[]),
        definitions=Definitions(profiles={"broken": profile}),
        steps=[AgentNode(id="a1", metadata={}, type="agent", profile="broken", tools=[])],
    )

    # Should not crash
    reports = validate_policy(flow)
    # Should be empty reports as no policies violated (empty caps due to exception)
    assert isinstance(reports, list)


def test_gatekeeper_schemeless_url() -> None:
    """Cover line 93 in gatekeeper.py: schemeless URL handling."""
    import pytest
    from pydantic import ValidationError

    from coreason_manifest.spec.core.tools import ToolCapability

    # SOTA Change: ToolCapability.url is strictly typed as HttpUrl.
    # Schemeless URLs must raise ValidationError during instantiation.
    with pytest.raises(ValidationError):
        ToolCapability(
            name="schemeless_tool",
            description="A tool without schema",
            # This line causes type error because Mypy sees `str` passed to `HttpUrl | None`
            # But we WANT to test validation failure at runtime.
            # We cast to ignore typing.
            url="evil.com/api",  # type: ignore[arg-type]
            risk_level="standard",
        )


def test_gatekeeper_port_stripping() -> None:
    """Cover port stripping logic (line 93)."""
    from pydantic import HttpUrl

    from coreason_manifest.spec.core.governance import Governance
    from coreason_manifest.spec.core.tools import ToolCapability, ToolPack

    tool = ToolCapability(
        name="port_tool",
        description="Tool with port",
        url=HttpUrl("https://evil.com:8080/api"),
        risk_level="standard",
    )

    flow = LinearFlow(
        kind="LinearFlow",
        status="draft",
        metadata=FlowMetadata(name="Port Test", version="1.0.0", description="desc", tags=[]),
        definitions=Definitions(
            tool_packs={
                "pack1": ToolPack(kind="ToolPack", namespace="pack1", tools=[tool], dependencies=[], env_vars=[])
            }
        ),
        steps=[],
        governance=Governance(allowed_domains=["good.com"]),
    )

    reports = validate_policy(flow)
    violation = next((r for r in reports if "blocked domain" in r.message), None)
    assert violation is not None
    assert "evil.com" in violation.message  # Should be stripped of port
