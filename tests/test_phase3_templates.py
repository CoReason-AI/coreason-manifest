import pytest

from coreason_manifest.builder import NewLinearFlow
from coreason_manifest.spec.core.flow import FlowDefinitions
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.resilience import RetryStrategy, SupervisionPolicy


def test_global_supervision_template() -> None:
    # Define a shared policy
    shared_policy = SupervisionPolicy(
        handlers=[], default_strategy=RetryStrategy(max_attempts=5, backoff_factor=1.5), max_cumulative_actions=10
    )

    # Create flow with definitions
    lf = NewLinearFlow(name="Template Flow")

    # Register the template using the builder method
    lf.define_supervision_template("standard-retry", shared_policy)

    # Add node referencing the template
    node = AgentNode(
        id="node1",
        metadata={},
        resilience="ref:standard-retry",
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    lf.add_step(node)

    # Build should pass validation
    flow = lf.build()
    assert flow.sequence[0].resilience == "ref:standard-retry"
    assert isinstance(flow.definitions, FlowDefinitions)
    assert flow.definitions.supervision_templates is not None
    assert flow.definitions.supervision_templates["standard-retry"] == shared_policy


def test_missing_supervision_template() -> None:
    lf = NewLinearFlow(name="Broken Template Flow")

    # No templates defined

    node = AgentNode(
        id="node1",
        metadata={},
        resilience="ref:missing-policy",
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    lf.add_step(node)

    # Build as draft should succeed (reference validation is strict)
    # Actually reference validation is also semantic check
    flow = lf.build()

    # Manually validate as published
    flow = flow.model_copy(update={"status": "published"})
    from coreason_manifest.utils.validator import validate_flow
    errors = validate_flow(flow)
    assert any("references undefined supervision template ID 'missing-policy'" in e for e in errors)


def test_malformed_supervision_reference() -> None:
    lf = NewLinearFlow(name="Malformed Ref Flow")

    node = AgentNode(
        id="node1",
        metadata={},
        resilience="invalid-string",
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    lf.add_step(node)

    flow_draft = lf.build()
    flow = flow_draft.model_copy(update={"status": "published"})
    from coreason_manifest.utils.validator import validate_flow
    errors = validate_flow(flow)
    assert any("invalid resilience reference" in e for e in errors)
