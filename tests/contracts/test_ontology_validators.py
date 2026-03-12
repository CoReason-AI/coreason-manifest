import math
from uuid import uuid4

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ActionSpaceManifest,
    AdversarialMarketTopologyManifest,
    BoundedJSONRPCIntent,
    BrowserDOMState,
    CognitiveStateProfile,
    ConsensusFederationTopologyManifest,
    ConsensusPolicy,
    ConstitutionalPolicy,
    CoreasonBaseState,
    DAGTopologyManifest,
    DistributionProfile,
    DynamicLayoutManifest,
    EnsembleTopologyProfile,
    EpistemicSOPManifest,
    EscrowPolicy,
    EvaluatorOptimizerTopologyManifest,
    ExecutionNodeReceipt,
    ExecutionSpanReceipt,
    ExogenousEpistemicEvent,
    GenerativeManifoldSLA,
    GlobalGovernancePolicy,
    InsightCardProfile,
    InterventionReceipt,
    LatentSmoothingProfile,
    MacroGridProfile,
    MCPCapabilityWhitelistPolicy,
    MCPServerManifest,
    NDimensionalTensorManifest,
    PermissionBoundaryPolicy,
    PredictionMarketPolicy,
    QuorumPolicy,
    RiskLevelPolicy,
    SaeLatentPolicy,
    SideEffectProfile,
    SimulationEscrowContract,
    SpatialBoundingBoxProfile,
    SwarmTopologyManifest,
    SystemNodeProfile,
    TaskAwardReceipt,
    TemporalBoundsProfile,
    TensorStructuralFormatProfile,
    ToolManifest,
    UtilityJustificationGraphReceipt,
    VerifiableCredentialPresentationReceipt,
    WetwareAttestationContract,
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


def test_tensor_structural_format_profile_bytes_per_element() -> None:
    assert TensorStructuralFormatProfile.FLOAT32.bytes_per_element == 4
    assert TensorStructuralFormatProfile.FLOAT64.bytes_per_element == 8
    assert TensorStructuralFormatProfile.INT8.bytes_per_element == 1
    assert TensorStructuralFormatProfile.UINT8.bytes_per_element == 1
    assert TensorStructuralFormatProfile.INT32.bytes_per_element == 4
    assert TensorStructuralFormatProfile.INT64.bytes_per_element == 8


def test_execution_node_receipt_hash() -> None:
    receipt = ExecutionNodeReceipt(request_id="req1", inputs={"key": "val"}, outputs=None)
    assert receipt.node_hash is not None
    assert len(receipt.node_hash) == 64

    with pytest.raises(ValidationError, match="Orphaned Lineage: parent_request_id is set but root_request_id is None"):
        ExecutionNodeReceipt(request_id="req1", parent_request_id="req2", inputs={"key": "val"}, outputs=None)


def test_distribution_profile_confidence_interval() -> None:
    # Invalid confidence interval
    with pytest.raises(ValidationError, match="confidence_interval_95 must have interval\\[0\\] < interval\\[1\\]"):
        DistributionProfile(distribution_type="gaussian", confidence_interval_95=(0.9, 0.1))

    # Valid
    d = DistributionProfile(distribution_type="gaussian", confidence_interval_95=(0.1, 0.9))
    assert d.confidence_interval_95 == (0.1, 0.9)


def test_ndimensional_tensor_manifest_physics_engine() -> None:
    with pytest.raises(ValidationError, match="Tensor shape must have at least 1 dimension"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(),
            vram_footprint_bytes=4,
            merkle_root="a" * 64,
            storage_uri="uri",
        )

    with pytest.raises(ValidationError, match="Tensor dimensions must be strictly positive integers"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(-1, 1),
            vram_footprint_bytes=4,
            merkle_root="a" * 64,
            storage_uri="uri",
        )

    with pytest.raises(ValidationError, match="Topological mismatch"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, 2),  # 4 elements * 4 bytes = 16 bytes
            vram_footprint_bytes=10,
            merkle_root="a" * 64,
            storage_uri="uri",
        )

    # Valid
    t = NDimensionalTensorManifest(
        structural_type=TensorStructuralFormatProfile.FLOAT32,
        shape=(2, 2),
        vram_footprint_bytes=16,
        merkle_root="a" * 64,
        storage_uri="uri",
    )
    assert t.shape == (2, 2)


def test_browser_dom_state_url() -> None:
    with pytest.raises(ValidationError, match="SSRF topological violation detected: file:// schema is forbidden"):
        BrowserDOMState(
            current_url="file:///etc/passwd",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )

    with pytest.raises(ValidationError, match="SSRF topological violation detected: localhost"):
        BrowserDOMState(
            current_url="http://localhost:8080",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )

    with pytest.raises(ValidationError, match="SSRF mathematical bound violation detected"):
        BrowserDOMState(
            current_url="http://10.0.0.1", viewport_size=(800, 600), dom_hash="a" * 64, accessibility_tree_hash="a" * 64
        )

    # Valid
    b = BrowserDOMState(
        current_url="https://coreason.ai", viewport_size=(800, 600), dom_hash="a" * 64, accessibility_tree_hash="a" * 64
    )
    assert b.current_url == "https://coreason.ai"


def test_execution_span_receipt_temporal_bounds() -> None:
    with pytest.raises(ValidationError, match="end_time_unix_nano cannot be before start_time_unix_nano"):
        ExecutionSpanReceipt(
            trace_id="t1", span_id="s1", name="test", start_time_unix_nano=1000, end_time_unix_nano=500
        )

    # Valid
    s = ExecutionSpanReceipt(
        trace_id="t1", span_id="s1", name="test", start_time_unix_nano=1000, end_time_unix_nano=1500
    )
    assert s.end_time_unix_nano == 1500


def test_temporal_bounds_profile() -> None:
    with pytest.raises(ValidationError, match="valid_to cannot be before valid_from"):
        TemporalBoundsProfile(valid_from=1000.0, valid_to=500.0)

    t = TemporalBoundsProfile(valid_from=500.0, valid_to=1000.0)
    assert t.valid_to == 1000.0


def test_task_award_receipt() -> None:
    with pytest.raises(ValidationError, match="Escrow locked amount cannot exceed the total cleared price"):
        TaskAwardReceipt(
            task_id="t1",
            awarded_syndicate={"did:example:agent1": 10},
            cleared_price_magnitude=10,
            escrow=EscrowPolicy(
                escrow_locked_magnitude=20, release_condition_metric="sla", refund_target_node_id="did:example:agent1"
            ),
        )

    with pytest.raises(ValidationError, match="Syndicate allocation sum must exactly equal cleared_price_magnitude"):
        TaskAwardReceipt(
            task_id="t1",
            awarded_syndicate={"did:example:agent1": 10, "did:example:agent2": 5},
            cleared_price_magnitude=20,
            escrow=None,
        )

    # Valid
    t = TaskAwardReceipt(
        task_id="t1",
        awarded_syndicate={"did:example:agent1": 10, "did:example:agent2": 10},
        cleared_price_magnitude=20,
        escrow=None,
    )
    assert t.cleared_price_magnitude == 20


def test_generative_manifold_sla() -> None:
    with pytest.raises(
        ValidationError, match="Geometric explosion risk: max_topological_depth \\* max_node_fanout must be <= 1000"
    ):
        GenerativeManifoldSLA(max_topological_depth=50, max_node_fanout=50, max_synthetic_tokens=100)

    g = GenerativeManifoldSLA(max_topological_depth=10, max_node_fanout=10, max_synthetic_tokens=100)
    assert g.max_topological_depth == 10


def test_evaluator_optimizer_topology() -> None:
    # Generator and Evaluator cannot be the same node
    with pytest.raises(ValidationError):
        EvaluatorOptimizerTopologyManifest(
            generator_node_id="did:example:node1",
            evaluator_node_id="did:example:node1",
            max_revision_loops=5,
            nodes={"did:example:node1": SystemNodeProfile(description="test")},
        )

    # Missing node
    with pytest.raises(ValidationError):
        EvaluatorOptimizerTopologyManifest(
            generator_node_id="did:example:node1",
            evaluator_node_id="did:example:node2",
            max_revision_loops=5,
            nodes={"did:example:node2": SystemNodeProfile(description="test")},
        )

    with pytest.raises(ValidationError):
        EvaluatorOptimizerTopologyManifest(
            generator_node_id="did:example:node1",
            evaluator_node_id="did:example:node2",
            max_revision_loops=5,
            nodes={"did:example:node1": SystemNodeProfile(description="test")},
        )


def test_adversarial_market_topology() -> None:
    market_rules = PredictionMarketPolicy(
        staking_function="linear", min_liquidity_magnitude=10, convergence_delta_threshold=0.5
    )

    with pytest.raises(
        ValidationError, match="Topological Contradiction: A node cannot exist in both the Blue and Red teams"
    ):
        AdversarialMarketTopologyManifest(
            blue_team_ids=["did:example:node1", "did:example:node2"],
            red_team_ids=["did:example:node2", "did:example:node3"],
            adjudicator_id="did:example:node4",
            market_rules=market_rules,
        )

    with pytest.raises(
        ValidationError, match="Topological Contradiction: The adjudicator cannot be a member of a competing team"
    ):
        AdversarialMarketTopologyManifest(
            blue_team_ids=["did:example:node1", "did:example:node2"],
            red_team_ids=["did:example:node3", "did:example:node4"],
            adjudicator_id="did:example:node1",
            market_rules=market_rules,
        )

    # Valid
    manifest = AdversarialMarketTopologyManifest(
        blue_team_ids=["did:example:node1"],
        red_team_ids=["did:example:node2"],
        adjudicator_id="did:example:node3",
        market_rules=market_rules,
    )
    assert manifest.adjudicator_id == "did:example:node3"

    # compilation
    base_top = manifest.compile_to_base_topology()
    assert base_top.type == "council"
    assert "did:example:node1" in base_top.nodes
    assert "did:example:node2" in base_top.nodes
    assert "did:example:node3" in base_top.nodes


def test_consensus_federation_topology() -> None:
    quorum_rules = QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )
    with pytest.raises(
        ValidationError, match="Topological Contradiction: Adjudicator cannot act as a voting participant"
    ):
        ConsensusFederationTopologyManifest(
            participant_ids=["did:example:node1", "did:example:node2", "did:example:node3", "did:example:node4"],
            adjudicator_id="did:example:node1",
            quorum_rules=quorum_rules,
        )

    # Valid
    manifest = ConsensusFederationTopologyManifest(
        participant_ids=["did:example:node1", "did:example:node2", "did:example:node3", "did:example:node4"],
        adjudicator_id="did:example:node5",
        quorum_rules=quorum_rules,
    )
    base_top = manifest.compile_to_base_topology()
    assert base_top.type == "council"
    assert "did:example:node1" in base_top.nodes
    assert "did:example:node5" in base_top.nodes


def test_swarm_topology() -> None:
    with pytest.raises(ValidationError, match="spawning_threshold cannot exceed max_concurrent_agents"):
        SwarmTopologyManifest(nodes={}, spawning_threshold=10, max_concurrent_agents=5)


def test_epistemic_sop_manifest() -> None:
    with pytest.raises(ValidationError, match="Ghost node referenced in chronological_flow_edges source"):
        EpistemicSOPManifest(
            sop_id="sop1",
            target_persona="default",
            cognitive_steps={
                "step1": CognitiveStateProfile(urgency_index=0.5, caution_index=0.5, divergence_tolerance=0.5)
            },
            structural_grammar_hashes={},
            chronological_flow_edges=[("ghost_step", "step1")],
            prm_evaluations=[],
        )

    with pytest.raises(ValidationError, match="Ghost node referenced in chronological_flow_edges target"):
        EpistemicSOPManifest(
            sop_id="sop1",
            target_persona="default",
            cognitive_steps={
                "step1": CognitiveStateProfile(urgency_index=0.5, caution_index=0.5, divergence_tolerance=0.5)
            },
            structural_grammar_hashes={},
            chronological_flow_edges=[("step1", "ghost_step")],
            prm_evaluations=[],
        )

    with pytest.raises(ValidationError, match="Ghost node referenced in structural_grammar_hashes"):
        EpistemicSOPManifest(
            sop_id="sop1",
            target_persona="default",
            cognitive_steps={
                "step1": CognitiveStateProfile(urgency_index=0.5, caution_index=0.5, divergence_tolerance=0.5)
            },
            structural_grammar_hashes={"ghost_step": "a" * 64},
            chronological_flow_edges=[],
            prm_evaluations=[],
        )


def test_macro_grid_profile() -> None:
    panel = InsightCardProfile(panel_id="panel1", title="test", markdown_content="test")

    with pytest.raises(ValidationError, match="Ghost Panel referenced in layout_matrix"):
        MacroGridProfile(layout_matrix=[["ghost_panel"]], panels=[panel])


def test_utility_justification_graph_receipt() -> None:
    # Test valid math
    ensemble = EnsembleTopologyProfile(
        concurrent_branch_ids=["did:example:1", "did:example:2"], fusion_function="highest_confidence"
    )
    with pytest.raises(
        ValidationError, match=r"Topological Interlock Failed: ensemble_spec defined but variance threshold is 0\.0"
    ):
        UtilityJustificationGraphReceipt(superposition_variance_threshold=0.0, ensemble_spec=ensemble)

    with pytest.raises(ValidationError, match="Tensor Poisoning Detected: Vector 'v1' contains invalid float"):
        UtilityJustificationGraphReceipt(optimizing_vectors={"v1": math.nan}, superposition_variance_threshold=0.1)

    receipt = UtilityJustificationGraphReceipt(optimizing_vectors={"v1": 1.0}, superposition_variance_threshold=0.1)
    assert receipt.optimizing_vectors["v1"] == 1.0


def test_exogenous_epistemic_event() -> None:
    with pytest.raises(ValidationError):  # Pydantic string validation fails first before custom validator
        ExogenousEpistemicEvent(
            shock_id="s1",
            target_node_hash="a" * 64,
            bayesian_surprise_score=0.5,
            synthetic_payload={"key": "val"},
            escrow=SimulationEscrowContract(locked_magnitude=0),
        )


def test_intervention_receipt() -> None:
    nonce1 = uuid4()
    nonce2 = uuid4()

    with pytest.raises(ValidationError, match="Anti-Replay Lock Triggered: Attestation nonce does not match"):
        InterventionReceipt(
            intervention_request_id=nonce1,
            target_node_id="did:example:node",
            approved=True,
            feedback=None,
            attestation=WetwareAttestationContract(
                mechanism="fido2_webauthn",
                did_subject="did:example:human",
                cryptographic_payload="payload",
                dag_node_nonce=nonce2,
            ),
        )


def test_dag_topology_manifest() -> None:
    # Test draft phase ignores edges missing from nodes
    draft_dag = DAGTopologyManifest(
        lifecycle_phase="draft",
        nodes={},
        edges=[("did:example:node1", "did:example:node2")],
        max_depth=5,
        max_fan_out=5,
    )
    assert draft_dag.lifecycle_phase == "draft"

    # Test live phase enforces edges exist
    with pytest.raises(ValidationError, match="Edge source 'did:example:node1' does not exist"):
        DAGTopologyManifest(
            lifecycle_phase="live",
            nodes={"did:example:node2": SystemNodeProfile(description="test")},
            edges=[("did:example:node1", "did:example:node2")],
            max_depth=5,
            max_fan_out=5,
        )

    with pytest.raises(ValidationError, match="Edge target 'did:example:node2' does not exist"):
        DAGTopologyManifest(
            lifecycle_phase="live",
            nodes={"did:example:node1": SystemNodeProfile(description="test")},
            edges=[("did:example:node1", "did:example:node2")],
            max_depth=5,
            max_fan_out=5,
        )

    # Test cycles detected
    with pytest.raises(ValidationError, match="Graph contains cycles but allow_cycles is False"):
        DAGTopologyManifest(
            lifecycle_phase="live",
            nodes={
                "did:example:node1": SystemNodeProfile(description="test"),
                "did:example:node2": SystemNodeProfile(description="test"),
            },
            edges=[("did:example:node1", "did:example:node2"), ("did:example:node2", "did:example:node1")],
            allow_cycles=False,
            max_depth=5,
            max_fan_out=5,
        )


def test_bounded_json_rpc_intent() -> None:
    # Test valid
    BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params={"key": "val"})

    # Test invalid nesting
    # Create a deep structure
    params: dict[str, object] = {"key": "val"}
    for _ in range(15):
        params = {"nested": params}

    with pytest.raises(ValidationError, match="JSON payload exceeds maximum depth of 10"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=params)


def test_global_governance_policy() -> None:
    rule1 = ConstitutionalPolicy(rule_id="other_rule", description="test", severity="low", forbidden_intents=["test"])

    with pytest.raises(
        ValidationError,
        match=r"CRITICAL LICENSE VIOLATION: The execution graph has been stripped of its Prosperity Public "
        r"License 3\.0",
    ):
        GlobalGovernancePolicy(
            mandatory_license_rule=rule1, max_budget_magnitude=100, max_global_tokens=100, global_timeout_seconds=100
        )

    rule2 = ConstitutionalPolicy(
        rule_id="PPL_3_0_COMPLIANCE",
        description="test",
        severity="low",  # Needs to be critical
        forbidden_intents=["test"],
    )
    with pytest.raises(ValidationError, match="CRITICAL LICENSE VIOLATION"):
        GlobalGovernancePolicy(
            mandatory_license_rule=rule2, max_budget_magnitude=100, max_global_tokens=100, global_timeout_seconds=100
        )

    # Valid
    rule3 = ConstitutionalPolicy(
        rule_id="PPL_3_0_COMPLIANCE", description="test", severity="critical", forbidden_intents=["test"]
    )
    policy = GlobalGovernancePolicy(
        mandatory_license_rule=rule3, max_budget_magnitude=100, max_global_tokens=100, global_timeout_seconds=100
    )
    assert policy.max_budget_magnitude == 100


def test_mcp_server_manifest() -> None:
    attestation = VerifiableCredentialPresentationReceipt(
        presentation_format="jwt_vc",
        issuer_did="did:other:issuer",
        cryptographic_proof_blob="proof",
        authorization_claims={},
    )
    whitelist = MCPCapabilityWhitelistPolicy()

    with pytest.raises(
        ValidationError,
        match="UNAUTHORIZED MCP MOUNT: The presented Verifiable Credential is not signed by a valid CoReason "
        "issuer DID",
    ):
        MCPServerManifest(
            server_uri="uri", transport_type="stdio", capability_whitelist=whitelist, attestation_receipt=attestation
        )


def test_action_space_manifest() -> None:
    tool1 = ToolManifest(
        tool_name="tool1",
        description="test",
        input_schema={},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    tool2 = ToolManifest(
        tool_name="tool1",  # Duplicate name
        description="test2",
        input_schema={},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    with pytest.raises(ValidationError, match="Tool names within an ActionSpaceManifest must be strictly unique"):
        ActionSpaceManifest(action_space_id="space1", native_tools=[tool1, tool2])
