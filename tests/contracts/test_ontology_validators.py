import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

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
    y_max=st.floats(min_value=0.0, max_value=1.0),
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
        with pytest.raises(
            ValidationError, match=r"Byzantine Fault Tolerance requires min_quorum_size \(N\) >= 3f \+ 1"
        ):
            QuorumPolicy(
                max_tolerable_faults=f,
                min_quorum_size=n,
                state_validation_metric="ledger_hash",
                byzantine_action="quarantine",
            )
    else:
        policy = QuorumPolicy(
            max_tolerable_faults=f,
            min_quorum_size=n,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )
        assert policy.min_quorum_size == n


# --- 4. Consensus Policy Atomicity ---
def test_consensus_policy_pbft_valid() -> None:
    quorum = QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )
    ConsensusPolicy(strategy="pbft", quorum_rules=quorum)


def test_consensus_policy_pbft_missing_quorum() -> None:
    with pytest.raises(ValidationError, match=r"quorum_rules must be provided when strategy is 'pbft'"):
        ConsensusPolicy(strategy="pbft")


def test_consensus_policy_non_pbft() -> None:
    ConsensusPolicy(strategy="majority")


# --- 5. Activation Steering Atomicity ---
def test_sae_latent_policy_valid_halt() -> None:
    SaeLatentPolicy(
        target_feature_index=1,
        monitored_layers=[1],
        max_activation_threshold=1.0,
        violation_action="halt",
        sae_dictionary_hash="a" * 64,
    )


def test_sae_latent_policy_valid_smooth_decay() -> None:
    smoothing = LatentSmoothingProfile(decay_function="exponential", transition_window_tokens=10)
    SaeLatentPolicy(
        target_feature_index=1,
        monitored_layers=[1],
        max_activation_threshold=1.0,
        violation_action="smooth_decay",
        sae_dictionary_hash="a" * 64,
        smoothing_profile=smoothing,
        clamp_value=0.1,
    )


def test_sae_latent_policy_smooth_decay_missing_profile() -> None:
    with pytest.raises(ValidationError, match=r"smoothing_profile must be provided"):
        SaeLatentPolicy(
            target_feature_index=1,
            monitored_layers=[1],
            max_activation_threshold=1.0,
            violation_action="smooth_decay",
            sae_dictionary_hash="a" * 64,
            clamp_value=0.1,
        )


def test_sae_latent_policy_smooth_decay_missing_clamp() -> None:
    smoothing = LatentSmoothingProfile(decay_function="exponential", transition_window_tokens=10)
    with pytest.raises(ValidationError, match=r"clamp_value must be provided"):
        SaeLatentPolicy(
            target_feature_index=1,
            monitored_layers=[1],
            max_activation_threshold=1.0,
            violation_action="smooth_decay",
            sae_dictionary_hash="a" * 64,
            smoothing_profile=smoothing,
        )


# --- 6. Dynamic Layout AST Atomicity ---
@pytest.mark.parametrize("tstring", ["f'{a} {b}'", "'text'"])
def test_dynamic_layout_manifest_valid_ast(tstring: str) -> None:
    DynamicLayoutManifest(layout_tstring=tstring)


@pytest.mark.parametrize(
    ("tstring", "bad_node"), [("f'{a()} {b}'", "Call"), ("print('hello')", "Call"), ("import os", "Import")]
)
def test_dynamic_layout_manifest_kinetic_bleed(tstring: str, bad_node: str) -> None:
    with pytest.raises(ValidationError, match=rf"Kinetic execution bleed detected: Forbidden AST node {bad_node}"):
        DynamicLayoutManifest(layout_tstring=tstring)


# --- 7. Missing Coverage Tests ---


def test_dynamic_layout_manifest_syntax_error() -> None:
    from coreason_manifest.spec.ontology import DynamicLayoutManifest

    # AST parsing exception for SyntaxError
    with pytest.raises(ValidationError):
        DynamicLayoutManifest(layout_tstring="f'{a")


def test_compute_engine_profile_sorting() -> None:
    from coreason_manifest.spec.ontology import ComputeEngineProfile, ComputeRateContract

    rate_card = ComputeRateContract(
        cost_per_million_input_tokens=0.5, cost_per_million_output_tokens=1.5, magnitude_unit="USD"
    )
    profile = ComputeEngineProfile(
        model_name="test-model",
        provider="test-provider",
        context_window_size=1024,
        capabilities=["c", "a", "b"],
        supported_functional_experts=["z", "x", "y"],
        rate_card=rate_card,
    )

    assert profile.capabilities == ["a", "b", "c"]
    assert profile.supported_functional_experts == ["x", "y", "z"]


def test_permission_boundary_policy_sorting() -> None:
    from coreason_manifest.spec.ontology import PermissionBoundaryPolicy

    policy = PermissionBoundaryPolicy(
        network_access=True,
        allowed_domains=["z.com", "a.com", "b.com"],
        file_system_mutation_forbidden=True,
        auth_requirements=["mtls:internal", "oauth2:github"],
    )

    assert policy.allowed_domains == ["a.com", "b.com", "z.com"]
    assert policy.auth_requirements == ["mtls:internal", "oauth2:github"]


def test_activation_steering_contract_sorting() -> None:
    from coreason_manifest.spec.ontology import ActivationSteeringContract

    contract = ActivationSteeringContract(
        steering_vector_hash="a" * 64, injection_layers=[5, 1, 3], scaling_factor=1.0, vector_modality="additive"
    )

    assert contract.injection_layers == [1, 3, 5]


def test_ephemeral_namespace_partition_state_validate_hashes() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import EphemeralNamespacePartitionState

    # valid
    state = EphemeralNamespacePartitionState(
        partition_id="test",
        execution_runtime="wasm32-wasi",
        authorized_bytecode_hashes=["b" * 64, "a" * 64],
        max_ttl_seconds=60,
        max_vram_mb=1024,
    )
    assert state.authorized_bytecode_hashes == ["a" * 64, "b" * 64]

    # invalid
    with pytest.raises(ValidationError):
        EphemeralNamespacePartitionState(
            partition_id="test",
            execution_runtime="wasm32-wasi",
            authorized_bytecode_hashes=["invalid-hash"],
            max_ttl_seconds=60,
            max_vram_mb=1024,
        )


def test_bilateral_sla_sorting() -> None:
    from coreason_manifest.spec.ontology import BilateralSLA, InformationClassificationProfile

    sla = BilateralSLA(
        receiving_tenant_id="tenant-1",
        max_permitted_classification=InformationClassificationProfile.PUBLIC,
        liability_limit_magnitude=1000,
        permitted_geographic_regions=["us-west", "eu-central", "ap-east"],
    )

    assert sla.permitted_geographic_regions == ["ap-east", "eu-central", "us-west"]


def test_federated_discovery_manifest_sorting() -> None:
    from coreason_manifest.spec.ontology import FederatedDiscoveryManifest

    manifest = FederatedDiscoveryManifest(
        broadcast_endpoints=["http://c.com", "http://a.com", "http://b.com"],
        supported_ontologies=["hash-c", "hash-a", "hash-b"],
    )

    # It sorts endpoints by string representation. But note we provided strings.
    # Because of default pydantic HttpUrl casting it returns HttpUrl but they are defined
    # as strings in the model right now (list[str]).
    # Since they are defined as list[str] in model, pydantic doesn't cast to HttpUrl
    # if we just give it list[str].
    assert manifest.broadcast_endpoints == ["http://a.com", "http://b.com", "http://c.com"]
    assert manifest.supported_ontologies == ["hash-a", "hash-b", "hash-c"]
