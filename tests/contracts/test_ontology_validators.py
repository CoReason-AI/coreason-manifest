import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ConsensusPolicy,
    CoreasonBaseState,
    LatentSmoothingProfile,
    QuorumPolicy,
    RiskLevelPolicy,
    SaeLatentPolicy,
    SpatialBoundingBoxProfile,
)


def test_risk_level_policy_weight() -> None:
    assert RiskLevelPolicy.SAFE.weight == 0
    assert RiskLevelPolicy.STANDARD.weight == 1
    assert RiskLevelPolicy.CRITICAL.weight == 2


def test_coreason_base_state_hash() -> None:
    class TestState(CoreasonBaseState):
        name: str

    state = TestState(name="test")
    # first call caches
    h1 = hash(state)
    # second call retrieves
    h2 = hash(state)
    assert h1 == h2


def test_spatial_coordinate_state_validation() -> None:
    # Valid
    SpatialBoundingBoxProfile(x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0)

    # Invalid x
    with pytest.raises(ValidationError, match=r"x_min cannot be strictly greater than x_max\."):
        SpatialBoundingBoxProfile(x_min=1.0, x_max=0.0, y_min=0.0, y_max=1.0)

    # Invalid y
    with pytest.raises(ValidationError, match=r"y_min cannot be strictly greater than y_max\."):
        SpatialBoundingBoxProfile(x_min=0.0, x_max=1.0, y_min=1.0, y_max=0.0)


def test_byzantine_fault_tolerance_policy_math() -> None:
    # Valid: N >= 3f + 1
    QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )

    # Invalid
    with pytest.raises(ValidationError, match=r"Byzantine Fault Tolerance requires min_quorum_size \(N\) >= 3f \+ 1\."):
        QuorumPolicy(
            max_tolerable_faults=1,
            min_quorum_size=3,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )


def test_consensus_policy_pbft_requirements() -> None:
    # Valid non-pbft
    ConsensusPolicy(strategy="majority")

    # Valid pbft
    ConsensusPolicy(
        strategy="pbft",
        quorum_rules=QuorumPolicy(
            max_tolerable_faults=1,
            min_quorum_size=4,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        ),
    )

    # Invalid pbft
    with pytest.raises(ValidationError, match=r"quorum_rules must be provided when strategy is 'pbft'\."):
        ConsensusPolicy(strategy="pbft")


def test_activation_steering_contract_smooth_decay() -> None:
    # Valid non-smooth decay
    SaeLatentPolicy(
        target_feature_index=1,
        monitored_layers=[1],
        max_activation_threshold=1.0,
        violation_action="halt",
        sae_dictionary_hash="a" * 64,
    )

    # Valid smooth decay
    SaeLatentPolicy(
        target_feature_index=1,
        monitored_layers=[1],
        max_activation_threshold=1.0,
        violation_action="smooth_decay",
        sae_dictionary_hash="a" * 64,
        smoothing_profile=LatentSmoothingProfile(decay_function="exponential", transition_window_tokens=10),
        clamp_value=0.1,
    )

    # Invalid smooth decay missing smoothing_profile
    with pytest.raises(
        ValidationError, match=r"smoothing_profile must be provided when violation_action is 'smooth_decay'\."
    ):
        SaeLatentPolicy(
            target_feature_index=1,
            monitored_layers=[1],
            max_activation_threshold=1.0,
            violation_action="smooth_decay",
            sae_dictionary_hash="a" * 64,
            clamp_value=0.1,
        )

    # Invalid smooth decay missing clamp_value
    with pytest.raises(
        ValidationError, match=r"clamp_value must be provided .* when violation_action is 'smooth_decay'\."
    ):
        SaeLatentPolicy(
            target_feature_index=1,
            monitored_layers=[1],
            max_activation_threshold=1.0,
            violation_action="smooth_decay",
            sae_dictionary_hash="a" * 64,
            smoothing_profile=LatentSmoothingProfile(decay_function="exponential", transition_window_tokens=10),
        )
