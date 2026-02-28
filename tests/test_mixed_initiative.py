import pytest

from coreason_manifest.core.oversight.mixed_initiative import (
    AllocationRule,
    BoundedAutonomyConfig,
    MixedInitiativePolicy
)
from coreason_manifest.core.oversight.governance import Governance

def test_allocation_rule():
    rule = AllocationRule(condition="x > 5", target_queue="human_review")
    assert rule.condition == "x > 5"
    assert rule.target_queue == "human_review"

def test_bounded_autonomy_config():
    config = BoundedAutonomyConfig(
        intervention_window_seconds=300,
        timeout_behavior="escalate"
    )
    assert config.intervention_window_seconds == 300
    assert config.timeout_behavior == "escalate"

def test_mixed_initiative_policy():
    policy = MixedInitiativePolicy(
        enable_shadow_telemetry=True,
        dynamic_allocation_rules=[AllocationRule(condition="x > 5", target_queue="human_review")]
    )
    assert policy.enable_shadow_telemetry is True
    assert len(policy.dynamic_allocation_rules) == 1

def test_governance_integration():
    policy = MixedInitiativePolicy()
    gov = Governance(mixed_initiative=policy)
    assert gov.mixed_initiative is not None
