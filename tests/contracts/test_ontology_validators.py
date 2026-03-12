import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ActivationSteeringContract,
    AdjudicationRubricProfile,
    ComputeEngineProfile,
    ComputeRateContract,
    ConsensusPolicy,
    CoreasonBaseState,
    DefeasibleCascadeEvent,
    DynamicLayoutManifest,
    EphemeralNamespacePartitionState,
    GradingCriterionProfile,
    InformationClassificationProfile,
    LatentSmoothingProfile,
    MultimodalTokenAnchorState,
    PermissionBoundaryPolicy,
    QuorumPolicy,
    RedactionPolicy,
    RiskLevelPolicy,
    RollbackIntent,
    SaeLatentPolicy,
    SecureSubSessionState,
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
    # First call generates and caches the canonical hash
    h1 = hash(state)
    # Second call pulls from cache
    h2 = hash(state)

    assert h1 == h2
    assert hasattr(state, "_cached_hash")
    assert state._cached_hash == h1


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


def test_dynamic_layout_manifest_syntax_error() -> None:
    # A SyntaxError in parsing is silently ignored because it poses no execution bleed risk.
    manifest = DynamicLayoutManifest(layout_tstring="f'{a")
    assert manifest.layout_tstring == "f'{a"


@pytest.mark.parametrize(
    ("tstring", "bad_node"), [("f'{a()} {b}'", "Call"), ("print('hello')", "Call"), ("import os", "Import")]
)
def test_dynamic_layout_manifest_kinetic_bleed(tstring: str, bad_node: str) -> None:
    with pytest.raises(ValidationError, match=rf"Kinetic execution bleed detected: Forbidden AST node {bad_node}"):
        DynamicLayoutManifest(layout_tstring=tstring)


# --- 7. Deterministic Array Sorting Validation ---
def test_compute_engine_profile_sorting() -> None:
    rate = ComputeRateContract(
        cost_per_million_input_tokens=1.0,
        cost_per_million_output_tokens=2.0,
        magnitude_unit="USD",
    )
    profile = ComputeEngineProfile(
        model_name="test-model",
        provider="test-provider",
        context_window_size=8192,
        capabilities=["write", "read", "execute", "analyze"],
        supported_functional_experts=["synthesizer", "falsifier", "coder"],
        rate_card=rate,
    )
    assert profile.capabilities == ["analyze", "execute", "read", "write"]
    assert profile.supported_functional_experts == ["coder", "falsifier", "synthesizer"]


def test_permission_boundary_policy_sorting() -> None:
    policy = PermissionBoundaryPolicy(
        network_access=True,
        file_system_mutation_forbidden=True,
        allowed_domains=["z-domain.com", "a-domain.com", "m-domain.com"],
        auth_requirements=["oauth2:google", "mtls:internal", "basic:auth"],
    )
    assert policy.allowed_domains == ["a-domain.com", "m-domain.com", "z-domain.com"]
    assert policy.auth_requirements == ["basic:auth", "mtls:internal", "oauth2:google"]


def test_permission_boundary_policy_none() -> None:
    policy = PermissionBoundaryPolicy(
        network_access=False,
        file_system_mutation_forbidden=True,
        allowed_domains=None,
        auth_requirements=None,
    )
    assert policy.allowed_domains is None
    assert policy.auth_requirements is None


def test_activation_steering_contract_sorting() -> None:
    contract = ActivationSteeringContract(
        steering_vector_hash="a" * 64, injection_layers=[10, 2, 5], scaling_factor=1.5, vector_modality="additive"
    )
    assert contract.injection_layers == [2, 5, 10]


def test_adjudication_rubric_profile_sorting() -> None:
    c1 = GradingCriterionProfile(criterion_id="c_beta", description="Beta criterion", weight=10.0)
    c2 = GradingCriterionProfile(criterion_id="c_alpha", description="Alpha criterion", weight=5.0)
    rubric = AdjudicationRubricProfile(rubric_id="rubric1", criteria=[c1, c2], passing_threshold=15.0)
    assert rubric.criteria[0].criterion_id == "c_alpha"
    assert rubric.criteria[1].criterion_id == "c_beta"


def test_redaction_policy_sorting() -> None:
    policy = RedactionPolicy(
        rule_id="r1",
        classification=InformationClassificationProfile.PUBLIC,
        target_pattern="email",
        target_regex_pattern=".*",
        context_exclusion_zones=["/path/z", "/path/a"],
        action="redact",
    )
    assert policy.context_exclusion_zones == ["/path/a", "/path/z"]


# --- 8. Missing specific validators coverage ---


def test_defeasible_cascade_event_sorting() -> None:
    event = DefeasibleCascadeEvent(
        cascade_id="c1",
        root_falsified_event_id="e1",
        propagated_decay_factor=0.5,
        quarantined_event_ids=["z", "a", "x"],
    )
    assert event.quarantined_event_ids == ["a", "x", "z"]


def test_rollback_intent_sorting() -> None:
    intent = RollbackIntent(request_id="r1", target_event_id="e1", invalidated_node_ids=["node_c", "node_a", "node_b"])
    assert intent.invalidated_node_ids == ["node_a", "node_b", "node_c"]


def test_multimodal_token_anchor_state_sorting() -> None:
    anchor = MultimodalTokenAnchorState(visual_patch_hashes=["hash_c", "hash_a", "hash_b"])
    assert anchor.visual_patch_hashes == ["hash_a", "hash_b", "hash_c"]


def test_secure_sub_session_state_sorting() -> None:
    state = SecureSubSessionState(
        session_id="session1",
        allowed_vault_keys=["vault_z", "vault_a", "vault_m"],
        max_ttl_seconds=3600,
        description="test session",
    )
    assert state.allowed_vault_keys == ["vault_a", "vault_m", "vault_z"]


def test_ephemeral_namespace_partition_state_sorting() -> None:
    hash_a = "a" * 64
    hash_b = "b" * 64
    hash_c = "c" * 64
    state = EphemeralNamespacePartitionState(
        partition_id="part1",
        execution_runtime="wasm32-wasi",
        authorized_bytecode_hashes=[hash_c, hash_a, hash_b],
        max_ttl_seconds=3600,
        max_vram_mb=1024,
    )
    assert state.authorized_bytecode_hashes == [hash_a, hash_b, hash_c]


def test_ephemeral_namespace_partition_state_invalid_hash() -> None:
    with pytest.raises(ValidationError, match=r"Invalid SHA-256 hash in whitelist: invalid_hash"):
        EphemeralNamespacePartitionState(
            partition_id="part1",
            execution_runtime="wasm32-wasi",
            authorized_bytecode_hashes=["invalid_hash"],
            max_ttl_seconds=3600,
            max_vram_mb=1024,
        )


def test_bilateral_sla_sorting() -> None:
    from coreason_manifest.spec.ontology import BilateralSLA, InformationClassificationProfile

    sla = BilateralSLA(
        receiving_tenant_id="tenant-a",
        max_permitted_classification=InformationClassificationProfile.PUBLIC,
        liability_limit_magnitude=1000,
        permitted_geographic_regions=["us-west", "eu-central", "ap-south"],
    )
    assert sla.permitted_geographic_regions == ["ap-south", "eu-central", "us-west"]


def test_federated_discovery_manifest_sorting() -> None:
    from coreason_manifest.spec.ontology import FederatedDiscoveryManifest

    manifest = FederatedDiscoveryManifest(
        broadcast_endpoints=["https://c.com", "https://a.com", "https://b.com"],
        supported_ontologies=["hash_z", "hash_x", "hash_y"],
    )
    assert manifest.broadcast_endpoints == ["https://a.com", "https://b.com", "https://c.com"]
    assert manifest.supported_ontologies == ["hash_x", "hash_y", "hash_z"]


def test_adjudication_intent_sorting() -> None:
    from coreason_manifest.spec.ontology import AdjudicationIntent

    intent = AdjudicationIntent(
        deadlocked_claims=["claim_3", "claim_1", "claim_2"],
        resolution_schema={"type": "string"},
        timeout_action="rollback",
    )
    assert intent.deadlocked_claims == ["claim_1", "claim_2", "claim_3"]
def test_risk_level_policy_weight2() -> None:
    assert RiskLevelPolicy.SAFE.weight == 0

def test_federated_capability_attestation_receipt_restricted_locks() -> None:
    from coreason_manifest.spec.ontology import FederatedCapabilityAttestationReceipt, BilateralSLA, InformationClassificationProfile, SecureSubSessionState

    sla = BilateralSLA(
        receiving_tenant_id="tenant-a",
        max_permitted_classification=InformationClassificationProfile.RESTRICTED,
        liability_limit_magnitude=1000,
        permitted_geographic_regions=["us-west", "eu-central", "ap-south"],
    )

    session_with_keys = SecureSubSessionState(
        session_id="session1",
        allowed_vault_keys=["vault_z"],
        max_ttl_seconds=3600,
        description="test session",
    )

    session_without_keys = SecureSubSessionState(
        session_id="session2",
        allowed_vault_keys=[],
        max_ttl_seconds=3600,
        description="test session",
    )

    # Valid because keys are defined
    FederatedCapabilityAttestationReceipt(
        attestation_id="att1",
        target_topology_id="did:ex:1",
        authorized_session=session_with_keys,
        governing_sla=sla
    )

    # Invalid because RESTRICTED but no keys
    with pytest.raises(ValidationError, match=r"RESTRICTED federated connections MUST define allowed_vault_keys"):
        FederatedCapabilityAttestationReceipt(
            attestation_id="att2",
            target_topology_id="did:ex:2",
            authorized_session=session_without_keys,
            governing_sla=sla
        )

def test_execution_node_receipt_hash_generation() -> None:
    from coreason_manifest.spec.ontology import ExecutionNodeReceipt

    receipt = ExecutionNodeReceipt(
        request_id="req1",
        parent_request_id="req0",
        root_request_id="req0",
        inputs={"in1": "a", "in2": "b"},
        outputs={"out1": "c", "out2": "d"},
        parent_hashes=["hash1", "hash2"]
    )

    # Check that node_hash is generated automatically and deterministic
    hash_value = receipt.node_hash
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64

    # The canonicalization method should work even with empty dicts or lists
    receipt2 = ExecutionNodeReceipt(
        request_id="req1",
        inputs=[],
        outputs={},
        parent_hashes=[]
    )
    assert isinstance(receipt2.node_hash, str)
    assert len(receipt2.node_hash) == 64

def test_n_dimensional_tensor_manifest_bounds() -> None:
    from coreason_manifest.spec.ontology import NDimensionalTensorManifest, TensorStructuralFormatProfile
    import pytest
    from pydantic import ValidationError

    # Valid case
    NDimensionalTensorManifest(
        structural_type=TensorStructuralFormatProfile.FLOAT32,
        shape=(2, 2),
        vram_footprint_bytes=16,
        merkle_root="a" * 64,
        storage_uri="s3://bucket/tensor.bin"
    )

    # Empty shape
    with pytest.raises(ValidationError, match=r"Tensor shape must have at least 1 dimension"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(),
            vram_footprint_bytes=16,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor.bin"
        )

    # Negative dimension
    with pytest.raises(ValidationError, match=r"Tensor dimensions must be strictly positive integers"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(-2, 2),
            vram_footprint_bytes=16,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor.bin"
        )

    # Zero dimension
    with pytest.raises(ValidationError, match=r"Tensor dimensions must be strictly positive integers"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(0, 2),
            vram_footprint_bytes=16,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor.bin"
        )

    # Mismatch VRAM bytes
    with pytest.raises(ValidationError, match=r"Topological mismatch: Shape"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, 2),
            vram_footprint_bytes=24, # Should be 16
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor.bin"
        )

def test_multimodal_token_anchor_state_token_spans() -> None:
    from coreason_manifest.spec.ontology import MultimodalTokenAnchorState

    # Valid definitions
    MultimodalTokenAnchorState(token_span_start=0, token_span_end=10, visual_patch_hashes=[])

    # Invalid: span_start defined but span_end is None
    with pytest.raises(ValidationError, match=r"If token_span_start is defined, token_span_end MUST be defined."):
        MultimodalTokenAnchorState(token_span_start=0, visual_patch_hashes=[])

    # Invalid: span_end defined but span_start is None
    with pytest.raises(ValidationError, match=r"token_span_end cannot be defined without a token_span_start."):
        MultimodalTokenAnchorState(token_span_end=10, visual_patch_hashes=[])

    # Invalid: span_end <= span_start
    with pytest.raises(ValidationError, match=r"token_span_end MUST be strictly greater than token_span_start."):
        MultimodalTokenAnchorState(token_span_start=10, token_span_end=10, visual_patch_hashes=[])

def test_multimodal_token_anchor_state_spatial_geometry() -> None:
    from coreason_manifest.spec.ontology import MultimodalTokenAnchorState

    # Valid definitions
    MultimodalTokenAnchorState(bounding_box=(0.0, 0.0, 1.0, 1.0), visual_patch_hashes=[])

    # Invalid: x_min > x_max
    with pytest.raises(ValidationError, match=r"Spatial invariant violated: min bounds .* exceed max bounds .*"):
        MultimodalTokenAnchorState(bounding_box=(1.0, 0.0, 0.0, 1.0), visual_patch_hashes=[])

    # Invalid: y_min > y_max
    with pytest.raises(ValidationError, match=r"Spatial invariant violated: min bounds .* exceed max bounds .*"):
        MultimodalTokenAnchorState(bounding_box=(0.0, 1.0, 1.0, 0.0), visual_patch_hashes=[])

def test_epistemic_transmutation_task_validate_grounding_density_for_visuals() -> None:
    from coreason_manifest.spec.ontology import EpistemicTransmutationTask, EpistemicCompressionSLA

    # Valid
    sla = EpistemicCompressionSLA(strict_probability_retention=True, max_allowed_entropy_loss=0.0, required_grounding_density="dense")
    EpistemicTransmutationTask(
        task_id="t1",
        artifact_event_id="e1",
        target_modalities=["raster_image", "tabular_grid"],
        compression_sla=sla
    )

    # Invalid
    sla_invalid = EpistemicCompressionSLA(strict_probability_retention=True, max_allowed_entropy_loss=0.0, required_grounding_density="sparse")
    with pytest.raises(ValidationError, match=r"Epistemic safety violation: Visual or tabular modalities require strict spatial tracking."):
        EpistemicTransmutationTask(
            task_id="t2",
            artifact_event_id="e2",
            target_modalities=["raster_image"],
            compression_sla=sla_invalid
        )

def test_execution_span_receipt_temporal_bounds() -> None:
    from coreason_manifest.spec.ontology import ExecutionSpanReceipt

    # Valid
    ExecutionSpanReceipt(trace_id="t1", span_id="s1", name="n1", start_time_unix_nano=0, end_time_unix_nano=10)

    # Invalid: end < start
    with pytest.raises(ValidationError, match=r"end_time_unix_nano cannot be before start_time_unix_nano"):
        ExecutionSpanReceipt(trace_id="t1", span_id="s1", name="n1", start_time_unix_nano=10, end_time_unix_nano=0)

def test_temporal_bounds_profile_temporal_bounds() -> None:
    from coreason_manifest.spec.ontology import TemporalBoundsProfile

    # Valid
    TemporalBoundsProfile(valid_from=0.0, valid_to=10.0)

    # Invalid: valid_to < valid_from
    with pytest.raises(ValidationError, match=r"valid_to cannot be before valid_from"):
        TemporalBoundsProfile(valid_from=10.0, valid_to=0.0)

def test_task_award_receipt_validate_escrow_bounds() -> None:
    from coreason_manifest.spec.ontology import TaskAwardReceipt, EscrowPolicy

    escrow = EscrowPolicy(escrow_locked_magnitude=1000, release_condition_metric="m", refund_target_node_id="id1")

    # Valid
    TaskAwardReceipt(task_id="t1", awarded_syndicate={"node1": 1500}, cleared_price_magnitude=1500, escrow=escrow)

    # Invalid
    with pytest.raises(ValidationError, match=r"Escrow locked amount cannot exceed the total cleared price."):
        TaskAwardReceipt(task_id="t1", awarded_syndicate={"node1": 500}, cleared_price_magnitude=500, escrow=escrow)

def test_task_award_receipt_verify_syndicate_allocation() -> None:
    from coreason_manifest.spec.ontology import TaskAwardReceipt

    # Valid
    TaskAwardReceipt(task_id="t1", awarded_syndicate={"node1": 1000, "node2": 500}, cleared_price_magnitude=1500)

    # Invalid
    with pytest.raises(ValidationError, match=r"Syndicate allocation sum must exactly equal cleared_price_magnitude"):
        TaskAwardReceipt(task_id="t1", awarded_syndicate={"node1": 1000, "node2": 1000}, cleared_price_magnitude=1500)

def test_dynamic_routing_manifest_validate_modality_alignment() -> None:
    from coreason_manifest.spec.ontology import DynamicRoutingManifest, GlobalSemanticProfile

    profile = GlobalSemanticProfile(artifact_event_id="e1", detected_modalities=["text", "tabular_grid"], token_density=10)

    # Valid
    DynamicRoutingManifest(
        manifest_id="m1",
        artifact_profile=profile,
        active_subgraphs={"text": ["did:ex:1"], "tabular_grid": ["did:ex:2"]},
        branch_budgets_magnitude={"did:ex:1": 100, "did:ex:2": 200}
    )

    # Invalid: modality not detected
    with pytest.raises(ValidationError, match=r"Epistemic Violation: Cannot route to subgraph 'raster_image' because it is missing from detected_modalities."):
        DynamicRoutingManifest(
            manifest_id="m1",
            artifact_profile=profile,
            active_subgraphs={"raster_image": ["did:ex:1"]},
            branch_budgets_magnitude={"did:ex:1": 100}
        )

def test_dynamic_routing_manifest_validate_conservation_of_custody() -> None:
    from coreason_manifest.spec.ontology import DynamicRoutingManifest, GlobalSemanticProfile, BypassReceipt

    profile = GlobalSemanticProfile(artifact_event_id="e1", detected_modalities=["text"], token_density=10)
    bypass = BypassReceipt(artifact_event_id="e1", bypassed_node_id="did:ex:1", justification="modality_mismatch", cryptographic_null_hash="a" * 64)
    bypass_invalid = BypassReceipt(artifact_event_id="e2", bypassed_node_id="did:ex:1", justification="modality_mismatch", cryptographic_null_hash="a" * 64)

    # Valid
    DynamicRoutingManifest(
        manifest_id="m1",
        artifact_profile=profile,
        active_subgraphs={"text": ["did:ex:1"]},
        bypassed_steps=[bypass],
        branch_budgets_magnitude={"did:ex:1": 100}
    )

    # Invalid: bypass has wrong artifact_event_id
    with pytest.raises(ValidationError, match=r"Merkle Violation: BypassReceipt artifact_event_id does not match the root artifact_profile."):
        DynamicRoutingManifest(
            manifest_id="m1",
            artifact_profile=profile,
            active_subgraphs={"text": ["did:ex:1"]},
            bypassed_steps=[bypass_invalid],
            branch_budgets_magnitude={"did:ex:1": 100}
        )

def test_base_node_profile_validate_domain_extensions_depth() -> None:
    from coreason_manifest.spec.ontology import BaseNodeProfile

    # Depth 1
    BaseNodeProfile(description="Test Node", domain_extensions={"k1": "v1"})

    # Depth 5
    valid_ext = {"k1": {"k2": {"k3": {"k4": {"k5": "v5"}}}}}
    BaseNodeProfile(description="Test Node", domain_extensions=valid_ext)

    # Depth 6 (Invalid)
    invalid_ext = {"k1": {"k2": {"k3": {"k4": {"k5": {"k6": "v6"}}}}}}
    with pytest.raises(ValidationError, match=r"domain_extensions exceeds maximum allowed depth of 5"):
        BaseNodeProfile(description="Test Node", domain_extensions=invalid_ext)

    # Invalid keys
    with pytest.raises(ValidationError, match=r"domain_extensions keys must be strings"):
        BaseNodeProfile(description="Test Node", domain_extensions={1: "v1"}) # type: ignore

    # Invalid leaf values
    with pytest.raises(ValidationError, match=r"domain_extensions leaf values must be JSON primitives"):
        BaseNodeProfile(description="Test Node", domain_extensions={"k1": object()})

    # Valid array
    valid_array_ext = {"k1": [{"k2": "v2"}]}
    BaseNodeProfile(description="Test Node", domain_extensions=valid_array_ext)

    # Invalid array leaf
    invalid_array_ext = {"k1": [{"k2": object()}]}
    with pytest.raises(ValidationError, match=r"domain_extensions leaf values must be JSON primitives"):
        BaseNodeProfile(description="Test Node", domain_extensions=invalid_array_ext)

def test_epistemic_sop_manifest_ghost_nodes() -> None:
    from coreason_manifest.spec.ontology import EpistemicSOPManifest, CognitiveStateProfile

    step = CognitiveStateProfile(urgency_index=0.5, caution_index=0.5, divergence_tolerance=0.5)

    # Valid
    EpistemicSOPManifest(
        sop_id="sop1",
        target_persona="persona1",
        cognitive_steps={"step1": step, "step2": step},
        structural_grammar_hashes={"step1": "hash1"},
        chronological_flow_edges=[("step1", "step2")],
        prm_evaluations=[]
    )

    # Ghost node in chronological_flow_edges source
    with pytest.raises(ValidationError, match=r"Ghost node referenced in chronological_flow_edges source: ghost1"):
        EpistemicSOPManifest(
            sop_id="sop1",
            target_persona="persona1",
            cognitive_steps={"step1": step, "step2": step},
            structural_grammar_hashes={"step1": "hash1"},
            chronological_flow_edges=[("ghost1", "step2")],
            prm_evaluations=[]
        )

    # Ghost node in chronological_flow_edges target
    with pytest.raises(ValidationError, match=r"Ghost node referenced in chronological_flow_edges target: ghost2"):
        EpistemicSOPManifest(
            sop_id="sop1",
            target_persona="persona1",
            cognitive_steps={"step1": step, "step2": step},
            structural_grammar_hashes={"step1": "hash1"},
            chronological_flow_edges=[("step1", "ghost2")],
            prm_evaluations=[]
        )

    # Ghost node in structural_grammar_hashes
    with pytest.raises(ValidationError, match=r"Ghost node referenced in structural_grammar_hashes: ghost3"):
        EpistemicSOPManifest(
            sop_id="sop1",
            target_persona="persona1",
            cognitive_steps={"step1": step, "step2": step},
            structural_grammar_hashes={"ghost3": "hash3"},
            chronological_flow_edges=[("step1", "step2")],
            prm_evaluations=[]
        )

def test_execution_span_receipt_sort_events() -> None:
    from coreason_manifest.spec.ontology import ExecutionSpanReceipt, SpanEvent

    event1 = SpanEvent(name="e1", timestamp_unix_nano=10)
    event2 = SpanEvent(name="e2", timestamp_unix_nano=5)

    receipt = ExecutionSpanReceipt(
        trace_id="t1",
        span_id="s1",
        name="n1",
        start_time_unix_nano=0,
        events=[event1, event2]
    )

    assert receipt.events[0].name == "e2"
    assert receipt.events[1].name == "e1"

def test_structural_causal_graph_profile_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import StructuralCausalGraphProfile, CausalDirectedEdgeState

    edge1 = CausalDirectedEdgeState(source_variable="b", target_variable="a", edge_type="direct_cause")
    edge2 = CausalDirectedEdgeState(source_variable="a", target_variable="b", edge_type="direct_cause")

    profile = StructuralCausalGraphProfile(
        observed_variables=["v2", "v1"],
        latent_variables=["l2", "l1"],
        causal_edges=[edge1, edge2]
    )

    assert profile.observed_variables == ["v1", "v2"]
    assert profile.latent_variables == ["l1", "l2"]
    assert profile.causal_edges[0].source_variable == "a"
    assert profile.causal_edges[1].source_variable == "b"

def test_neural_audit_attestation_receipt_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import NeuralAuditAttestationReceipt, SaeFeatureActivationState

    act1 = SaeFeatureActivationState(feature_index=2, activation_magnitude=0.5)
    act2 = SaeFeatureActivationState(feature_index=1, activation_magnitude=0.8)

    receipt = NeuralAuditAttestationReceipt(
        audit_id="a1",
        layer_activations={1: [act1, act2]}
    )

    assert receipt.layer_activations[1][0].feature_index == 1
    assert receipt.layer_activations[1][1].feature_index == 2

def test_ontological_handshake_receipt_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import OntologicalHandshakeReceipt

    receipt = OntologicalHandshakeReceipt(
        handshake_id="h1",
        participant_node_ids=["did:ex:2", "did:ex:1"],
        measured_cosine_similarity=0.9,
        alignment_status="aligned"
    )

    assert receipt.participant_node_ids == ["did:ex:1", "did:ex:2"]

def test_composite_node_profile_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import CompositeNodeProfile, DAGTopologyManifest, InputMappingContract, OutputMappingContract

    topology = DAGTopologyManifest(max_depth=1, max_fan_out=1, nodes={})

    in1 = InputMappingContract(parent_key="b", child_key="c1")
    in2 = InputMappingContract(parent_key="a", child_key="c2")

    out1 = OutputMappingContract(child_key="y", parent_key="p1")
    out2 = OutputMappingContract(child_key="x", parent_key="p2")

    profile = CompositeNodeProfile(
        description="d1",
        topology=topology,
        input_mappings=[in1, in2],
        output_mappings=[out1, out2]
    )

    assert profile.input_mappings[0].parent_key == "a"
    assert profile.output_mappings[0].child_key == "x"

def test_peft_adapter_contract_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import PeftAdapterContract

    contract = PeftAdapterContract(
        adapter_id="a1",
        safetensors_hash="b"*64,
        base_model_hash="c"*64,
        adapter_rank=4,
        target_modules=["v_proj", "q_proj"]
    )

    assert contract.target_modules == ["q_proj", "v_proj"]

def test_prediction_market_state_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import PredictionMarketState, HypothesisStakeReceipt

    stake1 = HypothesisStakeReceipt(agent_id="agent2", target_hypothesis_id="h1", staked_magnitude=100, implied_probability=0.5)
    stake2 = HypothesisStakeReceipt(agent_id="agent1", target_hypothesis_id="h1", staked_magnitude=200, implied_probability=0.8)

    state = PredictionMarketState(
        market_id="m1",
        resolution_oracle_condition_id="c1",
        lmsr_b_parameter="1.0",
        order_book=[stake1, stake2],
        current_market_probabilities={}
    )

    assert state.order_book[0].agent_id == "agent1"

def test_compute_provisioning_intent_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import ComputeProvisioningIntent

    intent = ComputeProvisioningIntent(
        max_budget=100.0,
        required_capabilities=["c", "a", "b"]
    )

    assert intent.required_capabilities == ["a", "b", "c"]

def test_sse_transport_profile_crlf_injection() -> None:
    from coreason_manifest.spec.ontology import SSETransportProfile

    # Valid
    SSETransportProfile(uri="http://ex.com/", headers={"key": "val"})

    # CRLF in key
    with pytest.raises(ValidationError, match=r"CRLF injection detected in headers"):
        SSETransportProfile(uri="http://ex.com/", headers={"key\r\n": "val"})

    # CRLF in value
    with pytest.raises(ValidationError, match=r"CRLF injection detected in headers"):
        SSETransportProfile(uri="http://ex.com/", headers={"key": "val\r\n"})


def test_semantic_firewall_policy_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import SemanticFirewallPolicy

    policy = SemanticFirewallPolicy(
        max_input_tokens=100,
        forbidden_intents=["c", "a", "b"],
        action_on_violation="drop"
    )

    assert policy.forbidden_intents == ["a", "b", "c"]

def test_exogenous_epistemic_event_enforce_economic_escrow() -> None:
    from coreason_manifest.spec.ontology import ExogenousEpistemicEvent, SimulationEscrowContract

    escrow1 = SimulationEscrowContract(locked_magnitude=10)

    event = ExogenousEpistemicEvent(
        shock_id="s1",
        target_node_hash="a" * 64,
        bayesian_surprise_score=0.5,
        synthetic_payload={"a": 1},
        escrow=escrow1
    )

    # We can't really test <= 0 because SimulationEscrowContract already enforces gt=0 natively
    # But just in case

def test_exogenous_epistemic_event_invalid_escrow() -> None:
    from coreason_manifest.spec.ontology import ExogenousEpistemicEvent, SimulationEscrowContract

    with pytest.raises(ValidationError):
        # Even instantiation of SimulationEscrowContract with 0 will fail
        # but if we construct one and pass it, it triggers the event's validator
        escrow = SimulationEscrowContract.model_construct(locked_magnitude=0)
        ExogenousEpistemicEvent(
            shock_id="s1",
            target_node_hash="a" * 64,
            bayesian_surprise_score=0.5,
            synthetic_payload={"a": 1},
            escrow=escrow
        )

def test_information_flow_policy_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import InformationFlowPolicy, RedactionPolicy, SaeLatentPolicy, InformationClassificationProfile

    r1 = RedactionPolicy(rule_id="r1", classification=InformationClassificationProfile.PUBLIC, target_pattern="p1", target_regex_pattern=".*", action="redact")
    r2 = RedactionPolicy(rule_id="r0", classification=InformationClassificationProfile.PUBLIC, target_pattern="p2", target_regex_pattern=".*", action="redact")

    f1 = SaeLatentPolicy(target_feature_index=2, monitored_layers=[1], max_activation_threshold=1.0, violation_action="halt", sae_dictionary_hash="a" * 64)
    f2 = SaeLatentPolicy(target_feature_index=1, monitored_layers=[1], max_activation_threshold=1.0, violation_action="halt", sae_dictionary_hash="a" * 64)

    policy = InformationFlowPolicy(
        policy_id="p1",
        rules=[r1, r2],
        latent_firewalls=[f1, f2]
    )

    assert policy.rules[0].rule_id == "r0"
    assert policy.latent_firewalls[0].target_feature_index == 1

def test_mcp_server_binding_profile_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import MCPServerBindingProfile, StdioTransportProfile

    transport = StdioTransportProfile(command="cmd")

    profile = MCPServerBindingProfile(
        server_id="s1",
        transport=transport,
        required_capabilities=["tools", "prompts", "resources"]
    )

    assert profile.required_capabilities == ["prompts", "resources", "tools"]

def test_steady_state_hypothesis_state_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import SteadyStateHypothesisState

    state = SteadyStateHypothesisState(
        expected_max_latency=10.0,
        max_loops_allowed=5,
        required_tool_usage=["c", "a", "b"]
    )

    assert state.required_tool_usage == ["a", "b", "c"]

def test_chaos_experiment_task_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import ChaosExperimentTask, SteadyStateHypothesisState, FaultInjectionProfile, ExogenousEpistemicEvent, SimulationEscrowContract

    hypothesis = SteadyStateHypothesisState(expected_max_latency=10.0, max_loops_allowed=5)
    f1 = FaultInjectionProfile(fault_type="latency_spike", target_node_id="n2", intensity=0.5)
    f2 = FaultInjectionProfile(fault_type="latency_spike", target_node_id="n1", intensity=0.5)

    escrow = SimulationEscrowContract(locked_magnitude=10)
    s1 = ExogenousEpistemicEvent(shock_id="s2", target_node_hash="a" * 64, bayesian_surprise_score=0.5, synthetic_payload={}, escrow=escrow)
    s2 = ExogenousEpistemicEvent(shock_id="s1", target_node_hash="a" * 64, bayesian_surprise_score=0.5, synthetic_payload={}, escrow=escrow)

    task = ChaosExperimentTask(
        experiment_id="e1",
        hypothesis=hypothesis,
        faults=[f1, f2],
        shocks=[s1, s2]
    )

    assert task.faults[0].target_node_id == "n1"
    assert task.shocks[0].shock_id == "s1"

def test_hypothesis_generation_event_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import HypothesisGenerationEvent, FalsificationContract

    cond1 = FalsificationContract(condition_id="c2", description="d1", falsifying_observation_signature=".*")
    cond2 = FalsificationContract(condition_id="c1", description="d2", falsifying_observation_signature=".*")

    event = HypothesisGenerationEvent(
        event_id="e1",
        timestamp=0.0,
        hypothesis_id="h1",
        premise_text="p1",
        bayesian_prior=0.5,
        falsification_conditions=[cond1, cond2]
    )

    assert event.falsification_conditions[0].condition_id == "c1"

def test_system_1_reflex_policy_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import System1ReflexPolicy

    policy = System1ReflexPolicy(
        confidence_threshold=0.8,
        allowed_passive_tools=["t2", "t1", "t3"]
    )

    assert policy.allowed_passive_tools == ["t1", "t2", "t3"]

def test_auction_state_sort_bids() -> None:
    from coreason_manifest.spec.ontology import AuctionState, TaskAnnouncementIntent, AgentBidIntent

    announcement = TaskAnnouncementIntent(task_id="t1", max_budget_magnitude=1000)

    b1 = AgentBidIntent(agent_id="agent2", estimated_cost_magnitude=500, estimated_latency_ms=10, estimated_carbon_gco2eq=0.0, confidence_score=0.9)
    b2 = AgentBidIntent(agent_id="agent1", estimated_cost_magnitude=400, estimated_latency_ms=15, estimated_carbon_gco2eq=0.0, confidence_score=0.8)

    state = AuctionState(
        announcement=announcement,
        bids=[b1, b2],
        clearing_timeout=100,
        minimum_tick_size=1.0
    )

    assert state.bids[0].agent_id == "agent1"

def test_theory_of_mind_snapshot_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import TheoryOfMindSnapshot

    snapshot = TheoryOfMindSnapshot(
        target_agent_id="agent1",
        assumed_shared_beliefs=["b", "a", "c"],
        identified_knowledge_gaps=["y", "z", "x"],
        empathy_confidence_score=0.8
    )

    assert snapshot.assumed_shared_beliefs == ["a", "b", "c"]
    assert snapshot.identified_knowledge_gaps == ["x", "y", "z"]

def test_trace_export_manifest_sort_spans() -> None:
    from coreason_manifest.spec.ontology import TraceExportManifest, ExecutionSpanReceipt

    s1 = ExecutionSpanReceipt(trace_id="t1", span_id="s2", name="n2", start_time_unix_nano=0)
    s2 = ExecutionSpanReceipt(trace_id="t1", span_id="s1", name="n1", start_time_unix_nano=0)

    manifest = TraceExportManifest(
        batch_id="b1",
        spans=[s1, s2]
    )

    assert manifest.spans[0].span_id == "s1"

def test_utility_justification_graph_receipt_interlocks() -> None:
    from coreason_manifest.spec.ontology import UtilityJustificationGraphReceipt, EnsembleTopologyProfile

    ensemble = EnsembleTopologyProfile(concurrent_branch_ids=["did:ex:id1", "did:ex:id2"], fusion_function="weighted_consensus")

    # Valid
    UtilityJustificationGraphReceipt(
        optimizing_vectors={"v1": 1.0},
        degrading_vectors={"v2": -1.0},
        superposition_variance_threshold=0.5,
        ensemble_spec=ensemble
    )

    # Invalid: ensemble_spec defined but threshold is 0
    with pytest.raises(ValidationError, match=r"Topological Interlock Failed: ensemble_spec defined but variance threshold is 0.0."):
        UtilityJustificationGraphReceipt(
            superposition_variance_threshold=0.0,
            ensemble_spec=ensemble
        )

    # Invalid: NaN or Inf
    with pytest.raises(ValidationError, match=r"Tensor Poisoning Detected: Vector 'v1' contains invalid float"):
        UtilityJustificationGraphReceipt(
            optimizing_vectors={"v1": float("inf")},
            superposition_variance_threshold=0.5
        )

def test_system2_remediation_intent_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import System2RemediationIntent

    intent = System2RemediationIntent(
        fault_id="f1",
        target_node_id="did:ex:1",
        failing_pointers=["/c", "/a", "/b"],
        remediation_prompt="fix it"
    )

    assert intent.failing_pointers == ["/a", "/b", "/c"]
