import pytest
from pydantic import ValidationError
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st

from coreason_manifest.spec.ontology import (
    ConsensusPolicy,
    CoreasonBaseState,
    DynamicLayoutManifest,
    LatentSmoothingProfile,
    QuorumPolicy,
    RiskLevelPolicy,
    SaeLatentPolicy,
    SpatialBoundingBoxProfile,
)

# --- 1. Static Mappings ---
def test_risk_level_policy_weight() -> None:
    assert RiskLevelPolicy.SAFE.weight == 0
    assert RiskLevelPolicy.STANDARD.weight == 1
    assert RiskLevelPolicy.CRITICAL.weight == 2

def test_coreason_base_state_hash() -> None:
    class TestState(CoreasonBaseState):
        name: str
    state = TestState(name="test")
    assert hash(state) == hash(state)

# --- 2. Spatial Bounding Box Fuzzing ---
@given(
    x_min=st.floats(min_value=0.0, max_value=1.0),
    x_max=st.floats(min_value=0.0, max_value=1.0),
    y_min=st.floats(min_value=0.0, max_value=1.0),
    y_max=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_spatial_bounds_fuzzing(x_min: float, x_max: float, y_min: float, y_max: float) -> None:
    """Mathematically prove the 2D plane logic strictly rejects impossible Euclidean geometries."""
    if x_min > x_max:
        with pytest.raises(ValidationError, match=r"x_min cannot be strictly greater than x_max"):
            SpatialBoundingBoxProfile(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
    elif y_min > y_max:
        with pytest.raises(ValidationError, match=r"y_min cannot be strictly greater than y_max"):
            SpatialBoundingBoxProfile(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
    else:
        box = SpatialBoundingBoxProfile(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
        assert box.x_min == x_min

# --- 3. Byzantine Fault Tolerance Fuzzing ---
@given(f=st.integers(min_value=0, max_value=1000), n=st.integers(min_value=1, max_value=4000))
@settings(max_examples=100)
def test_quorum_policy_bft_math_fuzzing(f: int, n: int) -> None:
    """Mathematically prove the deterministic quarantine of impossible PBFT geometries."""
    if n < 3 * f + 1:
        with pytest.raises(ValidationError, match=r"Byzantine Fault Tolerance requires min_quorum_size \(N\) >= 3f \+ 1"):
            QuorumPolicy(max_tolerable_faults=f, min_quorum_size=n, state_validation_metric="ledger_hash", byzantine_action="quarantine")
    else:
        policy = QuorumPolicy(max_tolerable_faults=f, min_quorum_size=n, state_validation_metric="ledger_hash", byzantine_action="quarantine")
        assert policy.min_quorum_size == n

# --- 4. Consensus Policy Atomicity ---
def test_consensus_policy_pbft_valid() -> None:
    quorum = QuorumPolicy(max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="quarantine")
    ConsensusPolicy(strategy="pbft", quorum_rules=quorum)

def test_consensus_policy_pbft_missing_quorum() -> None:
    with pytest.raises(ValidationError, match=r"quorum_rules must be provided when strategy is 'pbft'"):
        ConsensusPolicy(strategy="pbft")

def test_consensus_policy_non_pbft() -> None:
    ConsensusPolicy(strategy="majority")

# --- 5. Activation Steering Atomicity ---
def test_sae_latent_policy_valid_halt() -> None:
    SaeLatentPolicy(target_feature_index=1, monitored_layers=[1], max_activation_threshold=1.0, violation_action="halt", sae_dictionary_hash="a"*64)

def test_sae_latent_policy_valid_smooth_decay() -> None:
    smoothing = LatentSmoothingProfile(decay_function="exponential", transition_window_tokens=10)
    SaeLatentPolicy(target_feature_index=1, monitored_layers=[1], max_activation_threshold=1.0, violation_action="smooth_decay", sae_dictionary_hash="a"*64, smoothing_profile=smoothing, clamp_value=0.1)

def test_sae_latent_policy_smooth_decay_missing_profile() -> None:
    with pytest.raises(ValidationError, match=r"smoothing_profile must be provided"):
        SaeLatentPolicy(target_feature_index=1, monitored_layers=[1], max_activation_threshold=1.0, violation_action="smooth_decay", sae_dictionary_hash="a"*64, clamp_value=0.1)

def test_sae_latent_policy_smooth_decay_missing_clamp() -> None:
    smoothing = LatentSmoothingProfile(decay_function="exponential", transition_window_tokens=10)
    with pytest.raises(ValidationError, match=r"clamp_value must be provided"):
        SaeLatentPolicy(target_feature_index=1, monitored_layers=[1], max_activation_threshold=1.0, violation_action="smooth_decay", sae_dictionary_hash="a"*64, smoothing_profile=smoothing)

# --- 6. Dynamic Layout AST Atomicity ---
@pytest.mark.parametrize("tstring", ["f'{a} {b}'", "1 + 1", "'text'"])
def test_dynamic_layout_manifest_valid_ast(tstring: str) -> None:
    DynamicLayoutManifest(layout_tstring=tstring)

@pytest.mark.parametrize("tstring, bad_node", [
    ("f'{a()} {b}'", "Call"),
    ("print('hello')", "Call"),
    ("import os", "Import")
])
def test_dynamic_layout_manifest_kinetic_bleed(tstring: str, bad_node: str) -> None:
    with pytest.raises(ValidationError, match=rf"Kinetic execution bleed detected: Forbidden AST node {bad_node}"):
        DynamicLayoutManifest(layout_tstring=tstring)
