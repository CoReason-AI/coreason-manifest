import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ActivationSteeringContract,
    AdjudicationRubricProfile,
    BaseNodeProfile,
    BoundedJSONRPCIntent,
    BypassReceipt,
    ComputeEngineProfile,
    ComputeRateContract,
    ConsensusPolicy,
    CoreasonBaseState,
    DefeasibleCascadeEvent,
    DistributionProfile,
    DynamicLayoutManifest,
    DynamicRoutingManifest,
    EphemeralNamespacePartitionState,
    EpistemicCompressionSLA,
    EpistemicTransmutationTask,
    EscrowPolicy,
    ExecutionNodeReceipt,
    ExecutionSpanReceipt,
    GlobalSemanticProfile,
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
    TaskAwardReceipt,
    TemporalBoundsProfile,
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


def test_multimodal_token_anchor_state_validate_token_spans() -> None:
    with pytest.raises(ValidationError, match="If token_span_start is defined, token_span_end MUST be defined."):
        MultimodalTokenAnchorState(token_span_start=10)

    with pytest.raises(ValidationError, match="token_span_end MUST be strictly greater than token_span_start."):
        MultimodalTokenAnchorState(token_span_start=10, token_span_end=10)

    with pytest.raises(ValidationError, match="token_span_end cannot be defined without a token_span_start."):
        MultimodalTokenAnchorState(token_span_end=20)


def test_multimodal_token_anchor_state_validate_spatial_geometry() -> None:
    with pytest.raises(ValidationError, match="Spatial invariant violated"):
        MultimodalTokenAnchorState(bounding_box=(0.5, 0.5, 0.4, 0.6))

    with pytest.raises(ValidationError, match="Spatial invariant violated"):
        MultimodalTokenAnchorState(bounding_box=(0.5, 0.5, 0.6, 0.4))


def test_distribution_profile_validate_confidence_interval() -> None:
    with pytest.raises(ValidationError, match=r"confidence_interval_95 must have interval\[0\] < interval\[1\]"):
        DistributionProfile(distribution_type="gaussian", confidence_interval_95=(0.8, 0.5))

    with pytest.raises(ValidationError, match=r"confidence_interval_95 must have interval\[0\] < interval\[1\]"):
        DistributionProfile(distribution_type="gaussian", confidence_interval_95=(0.5, 0.5))

    # Valid
    DistributionProfile(distribution_type="gaussian", confidence_interval_95=(0.1, 0.9))


def test_epistemic_transmutation_task_validate_grounding_density_for_visuals() -> None:
    sla_sparse = EpistemicCompressionSLA(
        max_allowed_entropy_loss=0.1, required_grounding_density="sparse"
    )

    with pytest.raises(ValidationError, match="'required_grounding_density' cannot be 'sparse'"):
        EpistemicTransmutationTask(
            task_id="t1",
            artifact_event_id="a1",
            target_modalities=["tabular_grid"],
            compression_sla=sla_sparse
        )

    with pytest.raises(ValidationError, match="'required_grounding_density' cannot be 'sparse'"):
        EpistemicTransmutationTask(
            task_id="t1",
            artifact_event_id="a1",
            target_modalities=["raster_image"],
            compression_sla=sla_sparse
        )

    sla_dense = EpistemicCompressionSLA(
        max_allowed_entropy_loss=0.1, required_grounding_density="dense"
    )

    # Valid
    EpistemicTransmutationTask(
        task_id="t1",
        artifact_event_id="a1",
        target_modalities=["raster_image"],
        compression_sla=sla_dense
    )


def test_dynamic_routing_manifest_validate_modality_alignment() -> None:
    artifact = GlobalSemanticProfile(
        artifact_event_id="a1", detected_modalities=["text"], token_density=100
    )
    with pytest.raises(ValidationError, match="Epistemic Violation: Cannot route to subgraph 'tabular_grid' because it is missing from detected_modalities."):
        DynamicRoutingManifest(
            manifest_id="m1",
            artifact_profile=artifact,
            active_subgraphs={"tabular_grid": ["did:coreason:node1"]},
            branch_budgets_magnitude={"did:coreason:node1": 10},
        )

    # Valid
    DynamicRoutingManifest(
        manifest_id="m1",
        artifact_profile=artifact,
        active_subgraphs={"text": ["did:coreason:node1"]},
        branch_budgets_magnitude={"did:coreason:node1": 10},
    )


def test_dynamic_routing_manifest_validate_conservation_of_custody() -> None:
    artifact = GlobalSemanticProfile(
        artifact_event_id="a1", detected_modalities=["text"], token_density=100
    )

    bypass = BypassReceipt(
        artifact_event_id="a2",
        bypassed_node_id="did:coreason:node2",
        justification="modality_mismatch",
        cryptographic_null_hash="a" * 64
    )

    with pytest.raises(ValidationError, match="Merkle Violation: BypassReceipt artifact_event_id does not match the root artifact_profile."):
        DynamicRoutingManifest(
            manifest_id="m1",
            artifact_profile=artifact,
            active_subgraphs={"text": ["did:coreason:node1"]},
            branch_budgets_magnitude={"did:coreason:node1": 10},
            bypassed_steps=[bypass]
        )


def test_execution_span_receipt_validate_temporal_bounds() -> None:
    with pytest.raises(ValidationError, match="end_time_unix_nano cannot be before start_time_unix_nano"):
        ExecutionSpanReceipt(
            trace_id="trace1",
            span_id="span1",
            name="test",
            start_time_unix_nano=1000,
            end_time_unix_nano=999
        )

    # Valid
    ExecutionSpanReceipt(
        trace_id="trace1",
        span_id="span1",
        name="test",
        start_time_unix_nano=1000,
        end_time_unix_nano=1000
    )


def test_task_award_receipt_validate_escrow_bounds() -> None:
    escrow = EscrowPolicy(
        escrow_locked_magnitude=20,
        release_condition_metric="metric",
        refund_target_node_id="node1"
    )
    with pytest.raises(ValidationError, match="Escrow locked amount cannot exceed the total cleared price."):
        TaskAwardReceipt(
            task_id="task1",
            awarded_syndicate={"node1": 10},
            cleared_price_magnitude=10,
            escrow=escrow
        )

    valid_escrow = EscrowPolicy(
        escrow_locked_magnitude=10,
        release_condition_metric="metric",
        refund_target_node_id="node1"
    )
    # Valid
    TaskAwardReceipt(
        task_id="task1",
        awarded_syndicate={"node1": 10},
        cleared_price_magnitude=10,
        escrow=valid_escrow
    )


def test_temporal_bounds_profile_validate_temporal_bounds() -> None:
    with pytest.raises(ValidationError, match="valid_to cannot be before valid_from"):
        TemporalBoundsProfile(valid_from=10.0, valid_to=9.9)

    # Valid
    TemporalBoundsProfile(valid_from=10.0, valid_to=10.0)


def test_base_node_profile_validate_domain_extensions_depth() -> None:
    with pytest.raises(ValidationError, match="domain_extensions must be a dictionary"):
        BaseNodeProfile(description="test", domain_extensions=[1, 2, 3])

    deep_dict: dict[str, Any] = {}
    current = deep_dict
    for _ in range(6):
        current["a"] = {}
        current = current["a"]
    with pytest.raises(ValidationError, match="domain_extensions exceeds maximum allowed depth of 5"):
        BaseNodeProfile(description="test", domain_extensions=deep_dict)

    with pytest.raises(ValidationError, match="domain_extensions keys must be strings"):
        BaseNodeProfile(description="test", domain_extensions={1: "a"})

    long_key_dict = {"k" * 256: 1}
    with pytest.raises(ValidationError, match="domain_extensions key exceeds maximum length of 255 characters"):
        BaseNodeProfile(description="test", domain_extensions=long_key_dict)

    with pytest.raises(ValidationError, match="domain_extensions leaf values must be JSON primitives"):
        class Obj:
            pass
        BaseNodeProfile(description="test", domain_extensions={"a": Obj()})

    # Valid
    BaseNodeProfile(description="test", domain_extensions={"a": 1, "b": {"c": 2}, "d": [3, 4]})


def test_execution_node_receipt_validate_lineage() -> None:
    with pytest.raises(ValidationError, match="Orphaned Lineage: parent_request_id is set but root_request_id is None"):
        ExecutionNodeReceipt(
            request_id="req1",
            parent_request_id="parent1",
            root_request_id=None,
            inputs={"in": 1},
            outputs={"out": 2},
        )

    # Valid
    ExecutionNodeReceipt(
        request_id="req1",
        parent_request_id="parent1",
        root_request_id="root1",
        inputs={"in": 1},
        outputs={"out": 2},
    )


def test_bounded_jsonrpc_intent_validate_params_depth_and_size() -> None:
    with pytest.raises(ValidationError, match="params must be a dictionary"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=[1, 2, 3])

    deep_dict: dict[str, Any] = {}
    current = deep_dict
    for _ in range(11):
        current["a"] = {}
        current = current["a"]
    with pytest.raises(ValidationError, match="JSON payload exceeds maximum depth of 10"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=deep_dict)

    wide_dict = {f"k{i}": i for i in range(101)}
    with pytest.raises(ValidationError, match="Dictionary exceeds maximum of 100 keys"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=wide_dict)

    long_key_dict = {"k" * 1001: 1}
    with pytest.raises(ValidationError, match="Dictionary key exceeds maximum length of 1000"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=long_key_dict)

    long_list_dict = {"list": [1] * 1001}
    with pytest.raises(ValidationError, match="List exceeds maximum of 1000 elements"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=long_list_dict)

    long_str_dict = {"str": "s" * 10001}
    with pytest.raises(ValidationError, match="String exceeds maximum length of 10000 characters"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=long_str_dict)

    # Valid
    BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params={"a": 1})
    BoundedJSONRPCIntent(jsonrpc="2.0", method="test")


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
