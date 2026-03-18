# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CoreasonBaseState,
    QuorumPolicy,
    RiskLevelPolicy,
    SpatialBoundingBoxProfile,
    SaeLatentPolicy,
    LatentSmoothingProfile
)


def test_risk_level_policy_weight() -> None:
    assert RiskLevelPolicy.SAFE.weight == 0
    assert RiskLevelPolicy.STANDARD.weight == 1
    assert RiskLevelPolicy.CRITICAL.weight == 2

    assert RiskLevelPolicy.SAFE < RiskLevelPolicy.STANDARD
    assert RiskLevelPolicy.STANDARD <= RiskLevelPolicy.CRITICAL
    assert RiskLevelPolicy.CRITICAL > RiskLevelPolicy.STANDARD
    assert RiskLevelPolicy.STANDARD >= RiskLevelPolicy.SAFE

    assert not (RiskLevelPolicy.SAFE < "not a policy")


class DummyState(CoreasonBaseState):
    val: int


@given(st.integers())
def test_coreason_base_state_cached_hash(val: int) -> None:
    state = DummyState(val=val)

    # Trigger first calculation
    h1 = hash(state)

    # It should now be cached
    assert hasattr(state, "_cached_hash")

    # Trigger cached path
    h2 = hash(state)

    assert h1 == h2


@given(
    st.floats(min_value=0.5, max_value=1.0),
    st.floats(min_value=0.0, max_value=0.4),
)
def test_spatial_bounding_box_invalid_x(x_min: float, x_max: float) -> None:
    with pytest.raises(ValidationError, match="x_min cannot be strictly greater than x_max"):
        SpatialBoundingBoxProfile(x_min=x_min, y_min=0.0, x_max=x_max, y_max=1.0)


@given(
    st.floats(min_value=0.5, max_value=1.0),
    st.floats(min_value=0.0, max_value=0.4),
)
def test_spatial_bounding_box_invalid_y(y_min: float, y_max: float) -> None:
    with pytest.raises(ValidationError, match="y_min cannot be strictly greater than y_max"):
        SpatialBoundingBoxProfile(x_min=0.0, y_min=y_min, x_max=1.0, y_max=y_max)


@given(
    st.integers(min_value=0, max_value=100000),
    st.integers(min_value=1, max_value=100000),
)
def test_quorum_policy_validity(max_faults: int, quorum_size: int) -> None:
    if quorum_size < (3 * max_faults + 1):
        with pytest.raises(ValidationError, match=r"requires min_quorum_size \(N\) >= 3f \+ 1"):
            QuorumPolicy(max_tolerable_faults=max_faults, min_quorum_size=quorum_size, state_validation_metric="ledger_hash", byzantine_action="quarantine")
    else:
        QuorumPolicy(max_tolerable_faults=max_faults, min_quorum_size=quorum_size, state_validation_metric="ledger_hash", byzantine_action="quarantine")


def test_sae_latent_policy_smooth_decay() -> None:
    # Missing smoothing profile
    with pytest.raises(ValidationError, match="smoothing_profile must be provided when violation_action is 'smooth_decay'"):
        SaeLatentPolicy(
            target_feature_index=1,
            max_activation_threshold=1.0,
            violation_action="smooth_decay",
            sae_dictionary_hash="a"*64,
            clamp_value=1.0,
            monitored_layers=[1]
        )

    # Missing clamp value
    with pytest.raises(ValidationError, match="clamp_value must be provided as the target asymptote when violation_action is 'smooth_decay'"):
        SaeLatentPolicy(
            target_feature_index=1,
            max_activation_threshold=1.0,
            violation_action="smooth_decay",
            sae_dictionary_hash="a"*64,
            monitored_layers=[1],
            smoothing_profile=LatentSmoothingProfile(decay_function="exponential", transition_window_tokens=100)
        )

    # Valid smooth_decay
    SaeLatentPolicy(
        target_feature_index=1,
        max_activation_threshold=1.0,
        violation_action="smooth_decay",
        sae_dictionary_hash="a"*64,
        clamp_value=1.0,
        monitored_layers=[1],
        smoothing_profile=LatentSmoothingProfile(decay_function="exponential", transition_window_tokens=100)
    )
