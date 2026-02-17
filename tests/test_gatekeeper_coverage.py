from coreason_manifest.spec.core.flow import AgentNode, LinearFlow
from coreason_manifest.spec.core.flow import FlowDefinitions as Definitions
from coreason_manifest.spec.core.nodes import CognitiveProfile as Profile
from coreason_manifest.utils.gatekeeper import validate_policy


def test_gatekeeper_capability_error_handling():
    """
    Test that an AttributeError in required_capabilities is caught and treated as empty capabilities.
    Coverage for gatekeeper.py line 96.
    """
    # Use model_construct to bypass validation.
    # We pass an empty object() as reasoning.
    # Calling object().required_capabilities() will raise AttributeError.
    profile = Profile.model_construct(role="broken", persona="broken", reasoning=object(), fast_path=None)

    flow = LinearFlow(
        kind="LinearFlow",
        metadata={"name": "test", "version": "1.0", "description": "test", "tags": []},
        definitions=Definitions(profiles={"broken": profile}),
        sequence=[AgentNode(id="a1", metadata={}, type="agent", profile="broken", tools=[])],
    )

    # Should not crash
    reports = validate_policy(flow)
    # Should be empty reports as no policies violated (empty caps due to exception)
    assert isinstance(reports, list)
