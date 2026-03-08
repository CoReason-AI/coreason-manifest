import pytest
from pydantic import ValidationError

from coreason_manifest.state.differentials import DefeasibleCascade, TruthMaintenancePolicy


def test_truth_maintenance_policy_valid() -> None:
    policy = TruthMaintenancePolicy(
        decay_propagation_rate=0.5,
        epistemic_quarantine_threshold=0.8,
        max_cascade_depth=10,
        max_quarantine_blast_radius=100,
    )
    assert policy.decay_propagation_rate == 0.5
    assert policy.epistemic_quarantine_threshold == 0.8
    assert policy.enforce_cross_agent_quarantine is False


def test_truth_maintenance_policy_invalid_decay() -> None:
    with pytest.raises(ValidationError):
        TruthMaintenancePolicy(
            decay_propagation_rate=-0.1,
            epistemic_quarantine_threshold=0.8,
            max_cascade_depth=10,
            max_quarantine_blast_radius=100,
        )

    with pytest.raises(ValidationError):
        TruthMaintenancePolicy(
            decay_propagation_rate=1.1,
            epistemic_quarantine_threshold=0.8,
            max_cascade_depth=10,
            max_quarantine_blast_radius=100,
        )


def test_truth_maintenance_policy_invalid_quarantine_threshold() -> None:
    with pytest.raises(ValidationError):
        TruthMaintenancePolicy(
            decay_propagation_rate=0.5,
            epistemic_quarantine_threshold=-0.1,
            max_cascade_depth=10,
            max_quarantine_blast_radius=100,
        )

    with pytest.raises(ValidationError):
        TruthMaintenancePolicy(
            decay_propagation_rate=0.5,
            epistemic_quarantine_threshold=1.1,
            max_cascade_depth=10,
            max_quarantine_blast_radius=100,
        )


def test_defeasible_cascade_valid() -> None:
    cascade = DefeasibleCascade(
        cascade_id="cas-1",
        root_falsified_event_id="evt-1",
        propagated_decay_factor=0.5,
        quarantined_event_ids=["evt-2"],
    )
    assert cascade.cascade_id == "cas-1"
    assert cascade.root_falsified_event_id == "evt-1"
    assert cascade.propagated_decay_factor == 0.5
    assert cascade.quarantined_event_ids == ["evt-2"]
    assert cascade.cross_boundary_quarantine_issued is False


def test_defeasible_cascade_invalid_cascade_id() -> None:
    with pytest.raises(ValidationError):
        DefeasibleCascade(
            cascade_id="",
            root_falsified_event_id="evt-1",
            propagated_decay_factor=0.5,
            quarantined_event_ids=["evt-2"],
        )


def test_defeasible_cascade_invalid_decay_factor() -> None:
    with pytest.raises(ValidationError):
        DefeasibleCascade(
            cascade_id="cas-1",
            root_falsified_event_id="evt-1",
            propagated_decay_factor=-0.1,
            quarantined_event_ids=["evt-2"],
        )

    with pytest.raises(ValidationError):
        DefeasibleCascade(
            cascade_id="cas-1",
            root_falsified_event_id="evt-1",
            propagated_decay_factor=1.1,
            quarantined_event_ids=["evt-2"],
        )


def test_defeasible_cascade_invalid_quarantine_ids() -> None:
    with pytest.raises(ValidationError):
        DefeasibleCascade(
            cascade_id="cas-1",
            root_falsified_event_id="evt-1",
            propagated_decay_factor=0.5,
            quarantined_event_ids=[],
        )
