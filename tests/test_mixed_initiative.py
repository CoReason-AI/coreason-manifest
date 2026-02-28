import pytest
from pydantic import ValidationError

from coreason_manifest.core.oversight.governance import Governance
from coreason_manifest.core.oversight.mixed_initiative import (
    AllocationRule,
    BoundedAutonomyConfig,
    MixedInitiativePolicy,
)
from coreason_manifest.toolkit.builder import NewLinearFlow


def test_allocation_rule_instantiation() -> None:
    rule = AllocationRule(condition="confidence < 0.8", target_queue="human_experts")
    assert rule.condition == "confidence < 0.8"
    assert rule.target_queue == "human_experts"


def test_bounded_autonomy_config_instantiation() -> None:
    config = BoundedAutonomyConfig(intervention_window_seconds=300, timeout_behavior="escalate")
    assert config.intervention_window_seconds == 300
    assert config.timeout_behavior == "escalate"

    # Test literal constraint
    with pytest.raises(ValidationError):
        BoundedAutonomyConfig(intervention_window_seconds=300, timeout_behavior="invalid_behavior")  # type: ignore


def test_mixed_initiative_policy_instantiation() -> None:
    policy = MixedInitiativePolicy()
    assert policy.enable_shadow_telemetry is False
    assert policy.bounded_autonomy is None
    assert policy.dynamic_allocation_rules == []

    rule = AllocationRule(condition="error == True", target_queue="fallback")
    config = BoundedAutonomyConfig(intervention_window_seconds=60, timeout_behavior="proceed")
    custom_policy = MixedInitiativePolicy(
        enable_shadow_telemetry=True, bounded_autonomy=config, dynamic_allocation_rules=[rule]
    )

    assert custom_policy.enable_shadow_telemetry is True
    assert custom_policy.bounded_autonomy == config
    assert custom_policy.dynamic_allocation_rules == [rule]


def test_governance_accepts_mixed_initiative() -> None:
    policy = MixedInitiativePolicy(enable_shadow_telemetry=True)
    gov = Governance(mixed_initiative=policy)
    assert gov.mixed_initiative is not None
    assert gov.mixed_initiative.enable_shadow_telemetry is True


def test_base_flow_builder_set_mixed_initiative() -> None:
    from coreason_manifest.core.workflow.nodes import AgentNode, CognitiveProfile

    flow_builder = NewLinearFlow(name="TestFlow", version="1.0.0", description="A test flow.")

    # We must add at least one step so the linear flow validation passes.
    flow_builder.add_step(
        AgentNode(
            id="test_agent",
            type="agent",
            profile=CognitiveProfile(role="test", persona="test"),
            tools=[],
        )
    )

    policy = MixedInitiativePolicy(
        bounded_autonomy=BoundedAutonomyConfig(intervention_window_seconds=120, timeout_behavior="fail")
    )

    # First without any existing governance
    flow_builder.set_mixed_initiative(policy)
    assert flow_builder.governance is not None
    assert flow_builder.governance.mixed_initiative == policy

    # Now test modifying existing governance
    new_policy = MixedInitiativePolicy(enable_shadow_telemetry=True)
    flow_builder.set_mixed_initiative(new_policy)
    assert flow_builder.governance is not None
    assert flow_builder.governance.mixed_initiative == new_policy

    # Ensure it's correctly applied when building
    flow = flow_builder.build()
    assert flow.governance is not None
    assert flow.governance.mixed_initiative == new_policy
