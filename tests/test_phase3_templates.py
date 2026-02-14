import pytest

from coreason_manifest.builder import NewLinearFlow
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
        supervision="ref:standard-retry",
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    lf.add_step(node)

    # Build should pass validation
    flow = lf.build()
    assert flow.sequence[0].supervision == "ref:standard-retry"
    assert flow.definitions is not None
    assert flow.definitions.supervision_templates["standard-retry"] == shared_policy


def test_missing_supervision_template() -> None:
    lf = NewLinearFlow(name="Broken Template Flow")

    # No templates defined

    node = AgentNode(
        id="node1",
        metadata={},
        supervision="ref:missing-policy",
        profile=CognitiveProfile(role="dummy", persona="dummy", reasoning=None, fast_path=None),
        tools=[],
    )
    lf.add_step(node)

    with pytest.raises(ValueError, match="references undefined supervision template ID 'missing-policy'"):
        lf.build()
