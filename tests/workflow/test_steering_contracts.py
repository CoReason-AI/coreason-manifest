import pytest
from pydantic import ValidationError

from coreason_manifest.core.oversight.resilience import EscalationStrategy
from coreason_manifest.core.workflow.nodes.agent import (
    AgentNode,
    CognitiveProfile,
    InspectionConfig,
    InterventionTrigger,
    TransparencyLevel,
)
from coreason_manifest.core.workflow.nodes.human import (
    HumanNode,
    SteeringConfig,
    TimeoutBehavior,
)


def test_inspection_config_valid():
    config = InspectionConfig(
        transparency=TransparencyLevel.interactive,
        triggers=[InterventionTrigger.on_start, InterventionTrigger.on_failure],
        editable_pointers=["/foo/bar", "/baz"],
    )
    assert config.transparency == TransparencyLevel.interactive
    assert config.triggers == [InterventionTrigger.on_start, InterventionTrigger.on_failure]
    assert config.editable_pointers == ["/foo/bar", "/baz"]


def test_inspection_config_invalid_pointer():
    with pytest.raises(ValidationError, match="Invalid JSON Pointer"):
        InspectionConfig(
            transparency=TransparencyLevel.opaque,
            triggers=[],
            editable_pointers=["foo/bar"],
        )


def test_inspection_config_invalid_trigger():
    with pytest.raises(ValidationError):
        InspectionConfig(
            transparency=TransparencyLevel.observable,
            triggers=["invalid_trigger"],  # type: ignore
            editable_pointers=["/foo"],
        )


def test_agent_node_with_inspection():
    profile = CognitiveProfile(role="Tester", persona="A tester bot.")
    config = InspectionConfig(
        transparency=TransparencyLevel.observable,
        triggers=[InterventionTrigger.on_completion],
        editable_pointers=["/memory/latest"],
    )
    agent = AgentNode(
        id="agent_1",
        profile=profile,
        inspection=config,
    )
    assert agent.inspection is not None
    assert agent.inspection.transparency == TransparencyLevel.observable


def test_steering_config_timeout():
    config = SteeringConfig(
        allow_variable_mutation=True,
        allowed_targets=None,
        timeout_seconds=300,
        timeout_behavior=TimeoutBehavior.proceed_with_default,
        default_fallback_payload={"status": "approved"},
    )
    assert config.timeout_seconds == 300
    assert config.timeout_behavior == TimeoutBehavior.proceed_with_default
    assert config.default_fallback_payload == {"status": "approved"}


def test_human_node_with_steering():
    escalation = EscalationStrategy(queue_name="test", notification_level="critical", timeout_seconds=10)
    config = SteeringConfig(
        allow_variable_mutation=True,
        timeout_seconds=60,
        timeout_behavior=TimeoutBehavior.fail,
    )
    human = HumanNode(
        id="human_1",
        prompt="Please verify.",
        escalation=escalation,
        steering_config=config,

    )
    assert human.steering_config is not None
    assert human.steering_config.timeout_seconds == 60
    assert human.steering_config.timeout_behavior == TimeoutBehavior.fail
