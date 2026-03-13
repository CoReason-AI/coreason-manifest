import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError
from typing import Any

from coreason_manifest.spec.ontology import (
    RiskLevelPolicy,
    CoreasonBaseState,
    SpatialBoundingBoxProfile,
    QuorumPolicy,
    ConsensusPolicy,
    SaeLatentPolicy,
    LatentSmoothingProfile,
)


@given(st.sampled_from(RiskLevelPolicy))
def test_risk_level_policy_weight(risk_level: RiskLevelPolicy) -> None:
    if risk_level == RiskLevelPolicy.SAFE:
        assert risk_level.weight == 0
    elif risk_level == RiskLevelPolicy.STANDARD:
        assert risk_level.weight == 1
    elif risk_level == RiskLevelPolicy.CRITICAL:
        assert risk_level.weight == 2


class DummyState(CoreasonBaseState):
    value: str
    count: int

@given(st.builds(DummyState, value=st.text(), count=st.integers()))
def test_coreason_base_state_cached_hash(state: DummyState) -> None:
    # Hash is calculated and cached on first call
    first_hash = hash(state)
    assert hasattr(state, "_cached_hash")

    # Hash uses the cached value on second call
    second_hash = hash(state)
    assert first_hash == second_hash


@given(
    x_min=st.floats(0.0, 1.0),
    x_max=st.floats(0.0, 1.0),
    y_min=st.floats(0.0, 1.0),
    y_max=st.floats(0.0, 1.0),
)
def test_spatial_bounding_box_geometry_validation(
    x_min: float, x_max: float, y_min: float, y_max: float
) -> None:
    if x_min > x_max or y_min > y_max:
        with pytest.raises(ValidationError):
            SpatialBoundingBoxProfile(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
    else:
        profile = SpatialBoundingBoxProfile(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
        assert profile.x_min == x_min
        assert profile.y_min == y_min
        assert profile.x_max == x_max
        assert profile.y_max == y_max


@given(
    max_tolerable_faults=st.integers(0, 100),
    min_quorum_size=st.integers(1, 400),
    state_validation_metric=st.sampled_from(["ledger_hash", "zk_proof", "semantic_embedding"]),
    byzantine_action=st.sampled_from(["quarantine", "slash_escrow", "ignore"])
)
def test_quorum_policy_enforce_bft_math(
    max_tolerable_faults: int,
    min_quorum_size: int,
    state_validation_metric: str,
    byzantine_action: str
) -> None:
    if min_quorum_size < 3 * max_tolerable_faults + 1:
        with pytest.raises(ValidationError):
            QuorumPolicy(
                max_tolerable_faults=max_tolerable_faults,
                min_quorum_size=min_quorum_size,
                state_validation_metric=state_validation_metric,
                byzantine_action=byzantine_action
            )
    else:
        policy = QuorumPolicy(
            max_tolerable_faults=max_tolerable_faults,
            min_quorum_size=min_quorum_size,
            state_validation_metric=state_validation_metric,
            byzantine_action=byzantine_action
        )
        assert policy.min_quorum_size == min_quorum_size


@given(
    strategy=st.sampled_from(["unanimous", "majority", "debate_rounds", "prediction_market"]),
    quorum_rules=st.one_of(
        st.none(),
        st.builds(QuorumPolicy,
            max_tolerable_faults=st.integers(0, 10),
            min_quorum_size=st.integers(32, 100),
            state_validation_metric=st.sampled_from(["ledger_hash", "zk_proof", "semantic_embedding"]),
            byzantine_action=st.sampled_from(["quarantine", "slash_escrow", "ignore"])
        )
    )
)
def test_consensus_policy_validate_pbft_requirements_non_pbft(strategy: str, quorum_rules: QuorumPolicy | None) -> None:
    # Test valid non-pbft configurations
    policy = ConsensusPolicy(strategy=strategy, quorum_rules=quorum_rules)
    assert policy.strategy == strategy

@given(
    quorum_rules=st.builds(QuorumPolicy,
        max_tolerable_faults=st.integers(0, 10),
        min_quorum_size=st.integers(32, 100),
        state_validation_metric=st.sampled_from(["ledger_hash", "zk_proof", "semantic_embedding"]),
        byzantine_action=st.sampled_from(["quarantine", "slash_escrow", "ignore"])
    )
)
def test_consensus_policy_validate_pbft_requirements_valid_pbft(quorum_rules: QuorumPolicy) -> None:
    # Test valid pbft configuration (with quorum_rules)
    policy = ConsensusPolicy(strategy="pbft", quorum_rules=quorum_rules)
    assert policy.strategy == "pbft"
    assert policy.quorum_rules is not None

def test_consensus_policy_validate_pbft_requirements_invalid_pbft() -> None:
    # Test invalid pbft configuration (missing quorum_rules)
    with pytest.raises(ValidationError):
        ConsensusPolicy(strategy="pbft", quorum_rules=None)


@given(
    target_feature_index=st.integers(0, 100),
    monitored_layers=st.lists(st.integers(), min_size=1),
    max_activation_threshold=st.floats(0.0, 100.0),
    clamp_value=st.floats(-10.0, 10.0),
    sae_dictionary_hash=st.from_regex("^[a-f0-9]{64}$", fullmatch=True),
    smoothing_profile=st.builds(LatentSmoothingProfile,
        decay_function=st.sampled_from(["linear", "exponential", "cosine_annealing"]),
        transition_window_tokens=st.integers(1, 100),
        decay_rate_param=st.one_of(st.none(), st.floats())
    )
)
def test_sae_latent_policy_validate_smooth_decay_valid(
    target_feature_index: int,
    monitored_layers: list[int],
    max_activation_threshold: float,
    clamp_value: float,
    sae_dictionary_hash: str,
    smoothing_profile: LatentSmoothingProfile
) -> None:
    # Test valid configuration
    policy = SaeLatentPolicy(
        target_feature_index=target_feature_index,
        monitored_layers=monitored_layers,
        max_activation_threshold=max_activation_threshold,
        violation_action="smooth_decay",
        clamp_value=clamp_value,
        sae_dictionary_hash=sae_dictionary_hash,
        smoothing_profile=smoothing_profile
    )
    assert policy.violation_action == "smooth_decay"


@given(
    target_feature_index=st.integers(0, 100),
    monitored_layers=st.lists(st.integers(), min_size=1),
    max_activation_threshold=st.floats(0.0, 100.0),
    clamp_value=st.floats(-10.0, 10.0),
    sae_dictionary_hash=st.from_regex("^[a-f0-9]{64}$", fullmatch=True)
)
def test_sae_latent_policy_validate_smooth_decay_missing_profile(
    target_feature_index: int,
    monitored_layers: list[int],
    max_activation_threshold: float,
    clamp_value: float,
    sae_dictionary_hash: str
) -> None:
    # Test invalid configuration: missing smoothing_profile
    with pytest.raises(ValidationError):
        SaeLatentPolicy(
            target_feature_index=target_feature_index,
            monitored_layers=monitored_layers,
            max_activation_threshold=max_activation_threshold,
            violation_action="smooth_decay",
            clamp_value=clamp_value,
            sae_dictionary_hash=sae_dictionary_hash,
            smoothing_profile=None
        )


@given(
    target_feature_index=st.integers(0, 100),
    monitored_layers=st.lists(st.integers(), min_size=1),
    max_activation_threshold=st.floats(0.0, 100.0),
    sae_dictionary_hash=st.from_regex("^[a-f0-9]{64}$", fullmatch=True),
    smoothing_profile=st.builds(LatentSmoothingProfile,
        decay_function=st.sampled_from(["linear", "exponential", "cosine_annealing"]),
        transition_window_tokens=st.integers(1, 100),
        decay_rate_param=st.one_of(st.none(), st.floats())
    )
)
def test_sae_latent_policy_validate_smooth_decay_missing_clamp(
    target_feature_index: int,
    monitored_layers: list[int],
    max_activation_threshold: float,
    sae_dictionary_hash: str,
    smoothing_profile: LatentSmoothingProfile
) -> None:
    # Test invalid configuration: missing clamp_value
    with pytest.raises(ValidationError):
        SaeLatentPolicy(
            target_feature_index=target_feature_index,
            monitored_layers=monitored_layers,
            max_activation_threshold=max_activation_threshold,
            violation_action="smooth_decay",
            clamp_value=None,
            sae_dictionary_hash=sae_dictionary_hash,
            smoothing_profile=smoothing_profile
        )

from hypothesis import given, strategies as st
from pydantic import ValidationError
from typing import Any

from coreason_manifest.spec.ontology import (
    RiskLevelPolicy,
    CoreasonBaseState,
    SpatialBoundingBoxProfile,
    QuorumPolicy,
    ConsensusPolicy,
    SaeLatentPolicy,
    LatentSmoothingProfile,
)


@given(st.sampled_from(RiskLevelPolicy))
def test_risk_level_policy_weight(risk_level: RiskLevelPolicy) -> None:
    if risk_level == RiskLevelPolicy.SAFE:
        assert risk_level.weight == 0
    elif risk_level == RiskLevelPolicy.STANDARD:
        assert risk_level.weight == 1
    elif risk_level == RiskLevelPolicy.CRITICAL:
        assert risk_level.weight == 2


class DummyState(CoreasonBaseState):
    value: str
    count: int

@given(st.builds(DummyState, value=st.text(), count=st.integers()))
def test_coreason_base_state_cached_hash(state: DummyState) -> None:
    # Hash is calculated and cached on first call
    first_hash = hash(state)
    assert hasattr(state, "_cached_hash")

    # Hash uses the cached value on second call
    second_hash = hash(state)
    assert first_hash == second_hash


@given(
    x_min=st.floats(0.0, 1.0),
    x_max=st.floats(0.0, 1.0),
    y_min=st.floats(0.0, 1.0),
    y_max=st.floats(0.0, 1.0),
)
def test_spatial_bounding_box_geometry_validation(
    x_min: float, x_max: float, y_min: float, y_max: float
) -> None:
    if x_min > x_max or y_min > y_max:
        with pytest.raises(ValidationError):
            SpatialBoundingBoxProfile(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
    else:
        profile = SpatialBoundingBoxProfile(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
        assert profile.x_min == x_min
        assert profile.y_min == y_min
        assert profile.x_max == x_max
        assert profile.y_max == y_max


@given(
    max_tolerable_faults=st.integers(0, 100),
    min_quorum_size=st.integers(1, 400),
    state_validation_metric=st.sampled_from(["ledger_hash", "zk_proof", "semantic_embedding"]),
    byzantine_action=st.sampled_from(["quarantine", "slash_escrow", "ignore"])
)
def test_quorum_policy_enforce_bft_math(
    max_tolerable_faults: int,
    min_quorum_size: int,
    state_validation_metric: str,
    byzantine_action: str
) -> None:
    if min_quorum_size < 3 * max_tolerable_faults + 1:
        with pytest.raises(ValidationError):
            QuorumPolicy(
                max_tolerable_faults=max_tolerable_faults,
                min_quorum_size=min_quorum_size,
                state_validation_metric=state_validation_metric,
                byzantine_action=byzantine_action
            )
    else:
        policy = QuorumPolicy(
            max_tolerable_faults=max_tolerable_faults,
            min_quorum_size=min_quorum_size,
            state_validation_metric=state_validation_metric,
            byzantine_action=byzantine_action
        )
        assert policy.min_quorum_size == min_quorum_size


@given(
    strategy=st.sampled_from(["unanimous", "majority", "debate_rounds", "prediction_market"]),
    quorum_rules=st.one_of(
        st.none(),
        st.builds(QuorumPolicy,
            max_tolerable_faults=st.integers(0, 10),
            min_quorum_size=st.integers(32, 100),
            state_validation_metric=st.sampled_from(["ledger_hash", "zk_proof", "semantic_embedding"]),
            byzantine_action=st.sampled_from(["quarantine", "slash_escrow", "ignore"])
        )
    )
)
def test_consensus_policy_validate_pbft_requirements_non_pbft(strategy: str, quorum_rules: QuorumPolicy | None) -> None:
    # Test valid non-pbft configurations
    policy = ConsensusPolicy(strategy=strategy, quorum_rules=quorum_rules)
    assert policy.strategy == strategy

@given(
    quorum_rules=st.builds(QuorumPolicy,
        max_tolerable_faults=st.integers(0, 10),
        min_quorum_size=st.integers(32, 100),
        state_validation_metric=st.sampled_from(["ledger_hash", "zk_proof", "semantic_embedding"]),
        byzantine_action=st.sampled_from(["quarantine", "slash_escrow", "ignore"])
    )
)
def test_consensus_policy_validate_pbft_requirements_valid_pbft(quorum_rules: QuorumPolicy) -> None:
    # Test valid pbft configuration (with quorum_rules)
    policy = ConsensusPolicy(strategy="pbft", quorum_rules=quorum_rules)
    assert policy.strategy == "pbft"
    assert policy.quorum_rules is not None

def test_consensus_policy_validate_pbft_requirements_invalid_pbft() -> None:
    # Test invalid pbft configuration (missing quorum_rules)
    with pytest.raises(ValidationError):
        ConsensusPolicy(strategy="pbft", quorum_rules=None)


@given(
    target_feature_index=st.integers(0, 100),
    monitored_layers=st.lists(st.integers(), min_size=1),
    max_activation_threshold=st.floats(0.0, 100.0),
    clamp_value=st.floats(-10.0, 10.0),
    sae_dictionary_hash=st.from_regex("^[a-f0-9]{64}$", fullmatch=True),
    smoothing_profile=st.builds(LatentSmoothingProfile,
        decay_function=st.sampled_from(["linear", "exponential", "cosine_annealing"]),
        transition_window_tokens=st.integers(1, 100),
        decay_rate_param=st.one_of(st.none(), st.floats())
    )
)
def test_sae_latent_policy_validate_smooth_decay_valid(
    target_feature_index: int,
    monitored_layers: list[int],
    max_activation_threshold: float,
    clamp_value: float,
    sae_dictionary_hash: str,
    smoothing_profile: LatentSmoothingProfile
) -> None:
    # Test valid configuration
    policy = SaeLatentPolicy(
        target_feature_index=target_feature_index,
        monitored_layers=monitored_layers,
        max_activation_threshold=max_activation_threshold,
        violation_action="smooth_decay",
        clamp_value=clamp_value,
        sae_dictionary_hash=sae_dictionary_hash,
        smoothing_profile=smoothing_profile
    )
    assert policy.violation_action == "smooth_decay"


@given(
    target_feature_index=st.integers(0, 100),
    monitored_layers=st.lists(st.integers(), min_size=1),
    max_activation_threshold=st.floats(0.0, 100.0),
    clamp_value=st.floats(-10.0, 10.0),
    sae_dictionary_hash=st.from_regex("^[a-f0-9]{64}$", fullmatch=True)
)
def test_sae_latent_policy_validate_smooth_decay_missing_profile(
    target_feature_index: int,
    monitored_layers: list[int],
    max_activation_threshold: float,
    clamp_value: float,
    sae_dictionary_hash: str
) -> None:
    # Test invalid configuration: missing smoothing_profile
    with pytest.raises(ValidationError):
        SaeLatentPolicy(
            target_feature_index=target_feature_index,
            monitored_layers=monitored_layers,
            max_activation_threshold=max_activation_threshold,
            violation_action="smooth_decay",
            clamp_value=clamp_value,
            sae_dictionary_hash=sae_dictionary_hash,
            smoothing_profile=None
        )


@given(
    target_feature_index=st.integers(0, 100),
    monitored_layers=st.lists(st.integers(), min_size=1),
    max_activation_threshold=st.floats(0.0, 100.0),
    sae_dictionary_hash=st.from_regex("^[a-f0-9]{64}$", fullmatch=True),
    smoothing_profile=st.builds(LatentSmoothingProfile,
        decay_function=st.sampled_from(["linear", "exponential", "cosine_annealing"]),
        transition_window_tokens=st.integers(1, 100),
        decay_rate_param=st.one_of(st.none(), st.floats())
    )
)
def test_sae_latent_policy_validate_smooth_decay_missing_clamp(
    target_feature_index: int,
    monitored_layers: list[int],
    max_activation_threshold: float,
    sae_dictionary_hash: str,
    smoothing_profile: LatentSmoothingProfile
) -> None:
    # Test invalid configuration: missing clamp_value
    with pytest.raises(ValidationError):
        SaeLatentPolicy(
            target_feature_index=target_feature_index,
            monitored_layers=monitored_layers,
            max_activation_threshold=max_activation_threshold,
            violation_action="smooth_decay",
            clamp_value=None,
            sae_dictionary_hash=sae_dictionary_hash,
            smoothing_profile=smoothing_profile
        )

