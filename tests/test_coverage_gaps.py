from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ActionSpaceManifest,
    AdjudicationRubricProfile,
    AdversarialMarketTopologyManifest,
    AnyNodeProfile,
    BeliefMutationEvent,
    BilateralSLA,
    BoundedJSONRPCIntent,
    CognitiveStateProfile,
    ConsensusFederationTopologyManifest,
    ConsensusPolicy,
    ConstitutionalPolicy,
    CrossoverPolicy,
    DAGTopologyManifest,
    DefeasibleCascadeEvent,
    DelegatedCapabilityManifest,
    DistributionProfile,
    DynamicLayoutManifest,
    EpistemicLedgerState,
    EpistemicQuarantineSnapshot,
    EpistemicSOPManifest,
    EvaluatorOptimizerTopologyManifest,
    EvolutionaryTopologyManifest,
    ExecutionNodeReceipt,
    ExecutionSpanReceipt,
    FederatedCapabilityAttestationReceipt,
    FederatedDiscoveryManifest,
    FitnessObjectiveProfile,
    GradingCriterionProfile,
    InformationClassificationProfile,
    InsightCardProfile,
    LatentScratchpadReceipt,
    MacroGridProfile,
    MarketContract,
    MCPCapabilityWhitelistPolicy,
    MCPServerManifest,
    MigrationContract,
    MultimodalTokenAnchorState,
    MutationPolicy,
    NDimensionalTensorManifest,
    NeuralAuditAttestationReceipt,
    PeftAdapterContract,
    PermissionBoundaryPolicy,
    PredictionMarketPolicy,
    QuorumPolicy,
    RollbackIntent,
    SaeFeatureActivationState,
    SecureSubSessionState,
    SemanticDiscoveryIntent,
    SemanticFirewallPolicy,
    SemanticSlicingPolicy,
    SideEffectProfile,
    SpatialBoundingBoxProfile,
    SwarmTopologyManifest,
    System1ReflexPolicy,
    System2RemediationIntent,
    SystemNodeProfile,
    TaskAwardReceipt,
    TemporalBoundsProfile,
    TensorStructuralFormatProfile,
    TheoryOfMindSnapshot,
    ThoughtBranchState,
    ToolManifest,
    VectorEmbeddingState,
    VerifiableCredentialPresentationReceipt,
)


def test_bounded_json_rpc_intent_params_validation() -> None:
    # Valid params
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params={"a": 1, "b": "string", "c": [1, 2, 3]}, id=1)
    assert intent.params == {"a": 1, "b": "string", "c": [1, 2, 3]}

    # None params
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=None, id=1)
    assert intent.params == {}

    # Invalid params type
    with pytest.raises(ValidationError, match="params must be a dictionary"):
        BoundedJSONRPCIntent(
            jsonrpc="2.0",
            method="test",
            params=[1, 2, 3],  # type: ignore
            id=1,
        )

    # Exceed max depth
    deep_dict: dict[str, Any] = {}
    current: dict[str, Any] = deep_dict
    for _ in range(11):
        current["k"] = {}
        current = current["k"]

    with pytest.raises(ValidationError, match="JSON payload exceeds maximum depth of 10"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=deep_dict, id=1)

    # Exceed max dict keys
    wide_dict = {f"k{i}": i for i in range(101)}
    with pytest.raises(ValidationError, match="Dictionary exceeds maximum of 100 keys"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=wide_dict, id=1)

    # Exceed max dict key length
    long_key_dict = {"a" * 1001: 1}
    with pytest.raises(ValidationError, match="Dictionary key exceeds maximum length of 1000"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=long_key_dict, id=1)

    # Exceed list size
    long_list = list(range(1001))
    with pytest.raises(ValidationError, match="List exceeds maximum of 1000 elements"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params={"list": long_list}, id=1)

    # Exceed string length
    long_str = "a" * 10001
    with pytest.raises(ValidationError, match="String exceeds maximum length of 10000 characters"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params={"str": long_str}, id=1)


def _create_tool(name: str) -> ToolManifest:
    return ToolManifest(
        tool_name=name,
        description="A strictly bounded tool.",
        input_schema={"type": "object"},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )


def test_action_space_manifest_duplicate_tools() -> None:
    tool1 = _create_tool("tool_a")
    tool2 = _create_tool("tool_a")

    with pytest.raises(ValidationError, match="Tool names within an ActionSpaceManifest must be strictly unique"):
        ActionSpaceManifest(action_space_id="space_1", native_tools=[tool1, tool2])

    # Test sorting
    tool_b = _create_tool("tool_b")
    space = ActionSpaceManifest(action_space_id="space_1", native_tools=[tool_b, tool1])
    assert space.native_tools[0].tool_name == "tool_a"
    assert space.native_tools[1].tool_name == "tool_b"


def test_epistemic_sop_manifest_ghost_nodes() -> None:
    cog_state = CognitiveStateProfile(
        urgency_index=0.5,
        caution_index=0.5,
        divergence_tolerance=0.5,
    )

    # Valid setup
    sop = EpistemicSOPManifest(
        sop_id="sop_1",
        target_persona="default_assistant",
        cognitive_steps={"step_1": cog_state, "step_2": cog_state},
        structural_grammar_hashes={"step_1": "a" * 64},
        chronological_flow_edges=[("step_1", "step_2")],
        prm_evaluations=[],
    )
    assert sop.sop_id == "sop_1"

    # Ghost source in flow edge
    with pytest.raises(ValidationError, match="Ghost node referenced in chronological_flow_edges source"):
        EpistemicSOPManifest(
            sop_id="sop_1",
            target_persona="default_assistant",
            cognitive_steps={"step_2": cog_state},
            structural_grammar_hashes={},
            chronological_flow_edges=[("step_1", "step_2")],
            prm_evaluations=[],
        )

    # Ghost target in flow edge
    with pytest.raises(ValidationError, match="Ghost node referenced in chronological_flow_edges target"):
        EpistemicSOPManifest(
            sop_id="sop_1",
            target_persona="default_assistant",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={},
            chronological_flow_edges=[("step_1", "step_2")],
            prm_evaluations=[],
        )

    # Ghost node in structural grammar
    with pytest.raises(ValidationError, match="Ghost node referenced in structural_grammar_hashes"):
        EpistemicSOPManifest(
            sop_id="sop_1",
            target_persona="default_assistant",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={"step_2": "a" * 64},
            chronological_flow_edges=[],
            prm_evaluations=[],
        )


def test_adversarial_market_topology_manifest_validation() -> None:
    rules = PredictionMarketPolicy(
        staking_function="linear", min_liquidity_magnitude=100, convergence_delta_threshold=0.05
    )

    blue_id = "did:coreason:blue"
    red_id = "did:coreason:red"
    adj_id = "did:coreason:adj"

    # Valid
    manifest = AdversarialMarketTopologyManifest(
        blue_team_ids=[blue_id], red_team_ids=[red_id], adjudicator_id=adj_id, market_rules=rules
    )

    base = manifest.compile_to_base_topology()
    assert base.type == "council"
    assert base.adjudicator_id == adj_id
    assert blue_id in base.nodes
    assert red_id in base.nodes

    # Intersection between teams
    with pytest.raises(
        ValidationError, match=r"Topological Contradiction: A node cannot exist in both the Blue and Red teams\."
    ):
        AdversarialMarketTopologyManifest(
            blue_team_ids=[blue_id], red_team_ids=[blue_id], adjudicator_id=adj_id, market_rules=rules
        )

    # Adjudicator in teams
    with pytest.raises(
        ValidationError, match=r"Topological Contradiction: The adjudicator cannot be a member of a competing team\."
    ):
        AdversarialMarketTopologyManifest(
            blue_team_ids=[blue_id, adj_id], red_team_ids=[red_id], adjudicator_id=adj_id, market_rules=rules
        )


def test_n_dimensional_tensor_manifest_validation() -> None:
    # Valid
    NDimensionalTensorManifest(
        structural_type=TensorStructuralFormatProfile.FLOAT32,
        shape=(10, 10),
        vram_footprint_bytes=10 * 10 * 4,
        merkle_root="a" * 64,
        storage_uri="s3://bucket/tensor",
    )

    # Empty shape
    with pytest.raises(ValidationError, match="Tensor shape must have at least 1 dimension"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(),
            vram_footprint_bytes=0,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor",
        )

    # Negative shape
    with pytest.raises(ValidationError, match="Tensor dimensions must be strictly positive integers"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(-1, 10),
            vram_footprint_bytes=100,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor",
        )

    # Wrong vram calculation
    with pytest.raises(ValidationError, match="Topological mismatch: Shape"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(10, 10),
            vram_footprint_bytes=100,
            merkle_root="a" * 64,
            storage_uri="s3://bucket/tensor",
        )


def test_evolutionary_topology_manifest_sorting() -> None:
    obj1 = FitnessObjectiveProfile(target_metric="latency", direction="minimize")
    obj2 = FitnessObjectiveProfile(target_metric="accuracy", direction="maximize")

    mutation = MutationPolicy(mutation_rate=0.1, temperature_shift_variance=0.2)
    crossover = CrossoverPolicy(strategy_type="uniform_blend", blending_factor=0.5)

    manifest = EvolutionaryTopologyManifest(
        generations=10,
        population_size=100,
        mutation=mutation,
        crossover=crossover,
        fitness_objectives=[obj1, obj2],
        nodes={},
    )

    assert manifest.fitness_objectives[0].target_metric == "accuracy"
    assert manifest.fitness_objectives[1].target_metric == "latency"


def test_consensus_federation_topology_manifest() -> None:
    adj_id = "did:coreason:adj"
    part_id1 = "did:coreason:p1"
    part_id2 = "did:coreason:p2"
    part_id3 = "did:coreason:p3"

    quorum = QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="ignore"
    )

    # Valid
    manifest = ConsensusFederationTopologyManifest(
        participant_ids=[part_id1, part_id2, part_id3], adjudicator_id=adj_id, quorum_rules=quorum
    )

    base = manifest.compile_to_base_topology()
    assert base.type == "council"
    assert base.adjudicator_id == adj_id
    assert part_id1 in base.nodes

    # Adjudicator in participants
    with pytest.raises(
        ValidationError, match=r"Topological Contradiction: Adjudicator cannot act as a voting participant\."
    ):
        ConsensusFederationTopologyManifest(
            participant_ids=[part_id1, adj_id, part_id3], adjudicator_id=adj_id, quorum_rules=quorum
        )


def test_evaluator_optimizer_topology_manifest() -> None:
    gen_id = "did:coreason:gen"
    eval_id = "did:coreason:eval"

    # Valid
    nodes: dict[str, AnyNodeProfile] = {
        gen_id: SystemNodeProfile(description="gen"),
        eval_id: SystemNodeProfile(description="eval"),
    }

    EvaluatorOptimizerTopologyManifest(
        generator_node_id=gen_id, evaluator_node_id=eval_id, max_revision_loops=10, nodes=nodes
    )

    # Missing generator
    with pytest.raises(ValidationError, match=r"Generator node .* not found in topology nodes"):
        EvaluatorOptimizerTopologyManifest(
            generator_node_id=gen_id,
            evaluator_node_id=eval_id,
            max_revision_loops=10,
            nodes={eval_id: SystemNodeProfile(description="eval")},  # type: ignore[arg-type]
        )

    # Missing evaluator
    with pytest.raises(ValidationError, match=r"Evaluator node .* not found in topology nodes"):
        EvaluatorOptimizerTopologyManifest(
            generator_node_id=gen_id,
            evaluator_node_id=eval_id,
            max_revision_loops=10,
            nodes={gen_id: SystemNodeProfile(description="gen")},  # type: ignore[arg-type]
        )

    # Same nodes
    with pytest.raises(ValidationError, match="Generator and Evaluator cannot be the same node"):
        EvaluatorOptimizerTopologyManifest(
            generator_node_id=gen_id, evaluator_node_id=gen_id, max_revision_loops=10, nodes=nodes
        )


def test_quorum_policy_validation() -> None:
    # Valid
    QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="ignore"
    )

    # Invalid PBFT constraint
    with pytest.raises(ValidationError, match=r"Byzantine Fault Tolerance requires min_quorum_size .* >= 3f \+ 1"):
        QuorumPolicy(
            max_tolerable_faults=1, min_quorum_size=3, state_validation_metric="ledger_hash", byzantine_action="ignore"
        )


@given(st.integers(min_value=1, max_value=100), st.integers(min_value=1, max_value=100))
def test_hypothesis_n_dimensional_tensor(dim1: int, dim2: int) -> None:
    tensor_format = TensorStructuralFormatProfile.FLOAT32
    vram = dim1 * dim2 * 4

    NDimensionalTensorManifest(
        structural_type=tensor_format,
        shape=(dim1, dim2),
        vram_footprint_bytes=vram,
        merkle_root="a" * 64,
        storage_uri="s3://bucket/tensor",
    )


@given(st.text(min_size=11, max_size=1000))
def test_hypothesis_bounded_json_rpc(long_string: str) -> None:
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params={"str": long_string}, id=1)
    assert intent.params == {"str": long_string}


def test_dag_topology_manifest_cycle_validation() -> None:
    node1 = SystemNodeProfile(description="node1")
    node2 = SystemNodeProfile(description="node2")

    # Valid
    DAGTopologyManifest(
        nodes={"did:test:n1": node1, "did:test:n2": node2},
        edges=[("did:test:n1", "did:test:n2")],
        allow_cycles=False,
        max_depth=10,
        max_fan_out=10,
    )

    # Invalid cycle
    with pytest.raises(ValidationError, match="Graph contains cycles but allow_cycles is False"):
        DAGTopologyManifest(
            nodes={"did:test:n1": node1, "did:test:n2": node2},
            edges=[("did:test:n1", "did:test:n2"), ("did:test:n2", "did:test:n1")],
            allow_cycles=False,
            max_depth=10,
            max_fan_out=10,
        )


def test_semantic_firewall_policy_sorting() -> None:
    firewall = SemanticFirewallPolicy(
        max_input_tokens=1000, forbidden_intents=["b", "a", "c"], action_on_violation="drop"
    )
    assert firewall.forbidden_intents == ["a", "b", "c"]


def test_market_contract_validation() -> None:
    MarketContract(minimum_collateral=100.0, slashing_penalty=50.0)

    with pytest.raises(ValidationError, match="ECONOMIC INVARIANT VIOLATION"):
        MarketContract(minimum_collateral=50.0, slashing_penalty=100.0)


def test_temporal_bounds_profile_validation() -> None:
    TemporalBoundsProfile(valid_from=100.0, valid_to=200.0)

    with pytest.raises(ValidationError, match="valid_to cannot be before valid_from"):
        TemporalBoundsProfile(valid_from=200.0, valid_to=100.0)


def test_macro_grid_profile_ghost_panel() -> None:
    panel = InsightCardProfile(panel_id="p1", title="test", markdown_content="content")

    with pytest.raises(ValidationError, match="Ghost Panel referenced in layout_matrix"):
        MacroGridProfile(layout_matrix=[["p1", "p2"]], panels=[panel])


def test_span_trace_temporal_bounds() -> None:
    ExecutionSpanReceipt(trace_id="t1", span_id="s1", name="test", start_time_unix_nano=100, end_time_unix_nano=200)

    with pytest.raises(ValidationError, match="end_time_unix_nano cannot be before start_time_unix_nano"):
        ExecutionSpanReceipt(trace_id="t1", span_id="s1", name="test", start_time_unix_nano=200, end_time_unix_nano=100)


def test_latent_scratchpad_receipt() -> None:
    branch1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64, prm_score=0.9)
    branch2 = ThoughtBranchState(branch_id="b2", latent_content_hash="b" * 64, prm_score=0.1)

    # Valid
    receipt = LatentScratchpadReceipt(
        trace_id="t1",
        explored_branches=[branch2, branch1],
        discarded_branches=["b2"],
        resolution_branch_id="b1",
        total_latent_tokens=100,
    )

    assert receipt.explored_branches[0].branch_id == "b1"
    assert receipt.explored_branches[1].branch_id == "b2"

    # Invalid discarded branch
    with pytest.raises(ValidationError, match="discarded branch 'b3' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="t1",
            explored_branches=[branch1, branch2],
            discarded_branches=["b3"],
            resolution_branch_id="b1",
            total_latent_tokens=100,
        )

    # Invalid resolution branch
    with pytest.raises(ValidationError, match="resolution_branch_id 'b3' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="t1",
            explored_branches=[branch1, branch2],
            discarded_branches=["b2"],
            resolution_branch_id="b3",
            total_latent_tokens=100,
        )


def test_semantic_slicing_policy_sorting() -> None:
    policy = SemanticSlicingPolicy(
        permitted_classification_tiers=[
            InformationClassificationProfile.RESTRICTED,
            InformationClassificationProfile.PUBLIC,
        ],
        required_semantic_labels=["b", "a"],
        context_window_token_ceiling=1000,
    )

    assert policy.permitted_classification_tiers == [
        InformationClassificationProfile.PUBLIC,
        InformationClassificationProfile.RESTRICTED,
    ]
    assert policy.required_semantic_labels == ["a", "b"]


def test_execution_node_receipt_hashing() -> None:
    receipt = ExecutionNodeReceipt(request_id="req1", inputs={"a": 1}, outputs={"b": 2}, parent_hashes=["a" * 64])

    # Hash generated deterministically
    assert receipt.node_hash is not None
    assert len(receipt.node_hash) == 64

    # Orphaned lineage
    with pytest.raises(ValidationError, match="Orphaned Lineage: parent_request_id is set but root_request_id is None"):
        ExecutionNodeReceipt(
            request_id="req1", parent_request_id="parent1", root_request_id=None, inputs={"a": 1}, outputs={"b": 2}
        )


def test_dynamic_layout_manifest_tstring_validation() -> None:
    # Valid
    manifest = DynamicLayoutManifest(layout_tstring="f'hello {name}'")
    assert manifest.layout_tstring == "f'hello {name}'"

    # Invalid AST
    with pytest.raises(ValidationError, match="Kinetic execution bleed detected: Forbidden AST node Call"):
        DynamicLayoutManifest(layout_tstring='f\'hello {__import__("os").system("ls")}\'')


def test_spatial_bounding_box_profile() -> None:
    # Valid
    SpatialBoundingBoxProfile(x_min=0.1, y_min=0.1, x_max=0.9, y_max=0.9)

    # Invalid X
    with pytest.raises(ValidationError, match="x_min cannot be strictly greater than x_max"):
        SpatialBoundingBoxProfile(x_min=0.9, y_min=0.1, x_max=0.1, y_max=0.9)

    # Invalid Y
    with pytest.raises(ValidationError, match="y_min cannot be strictly greater than y_max"):
        SpatialBoundingBoxProfile(x_min=0.1, y_min=0.9, x_max=0.9, y_max=0.1)


def test_multimodal_token_anchor_state_validation() -> None:
    # Valid span
    MultimodalTokenAnchorState(token_span_start=10, token_span_end=20)

    # Missing end span
    with pytest.raises(ValidationError, match="If token_span_start is defined, token_span_end MUST be defined"):
        MultimodalTokenAnchorState(token_span_start=10)

    # Missing start span
    with pytest.raises(ValidationError, match="token_span_end cannot be defined without a token_span_start"):
        MultimodalTokenAnchorState(token_span_end=20)

    # End before start
    with pytest.raises(ValidationError, match="token_span_end MUST be strictly greater than token_span_start"):
        MultimodalTokenAnchorState(token_span_start=20, token_span_end=10)

    # Valid bounding box
    MultimodalTokenAnchorState(bounding_box=(0.1, 0.1, 0.9, 0.9))

    # Invalid bounding box X
    with pytest.raises(ValidationError, match="Spatial invariant violated"):
        MultimodalTokenAnchorState(bounding_box=(0.9, 0.1, 0.1, 0.9))

    # Invalid bounding box Y
    with pytest.raises(ValidationError, match="Spatial invariant violated"):
        MultimodalTokenAnchorState(bounding_box=(0.1, 0.9, 0.9, 0.1))


def test_mcp_server_manifest_validation() -> None:
    # Valid
    MCPServerManifest(
        server_uri="http://localhost:8000",
        transport_type="http",
        capability_whitelist=MCPCapabilityWhitelistPolicy(
            allowed_tools=[], allowed_resources=[], allowed_prompts=[], required_licenses=[]
        ),
        attestation_receipt=VerifiableCredentialPresentationReceipt(
            presentation_format="jwt_vc",
            issuer_did="did:coreason:auth",
            cryptographic_proof_blob="a" * 64,
            authorization_claims={},
        ),
    )

    # Invalid DID
    with pytest.raises(
        ValidationError,
        match=r"UNAUTHORIZED MCP MOUNT",
    ):
        MCPServerManifest(
            server_uri="http://localhost:8000",
            transport_type="http",
            capability_whitelist=MCPCapabilityWhitelistPolicy(
                allowed_tools=[], allowed_resources=[], allowed_prompts=[], required_licenses=[]
            ),
            attestation_receipt=VerifiableCredentialPresentationReceipt(
                presentation_format="jwt_vc",
                issuer_did="did:other:auth",
                cryptographic_proof_blob="a" * 64,
                authorization_claims={},
            ),
        )


def test_swarm_topology_manifest_validation() -> None:
    SwarmTopologyManifest(
        nodes={},
        spawning_threshold=3,
        max_concurrent_agents=10,
    )

    with pytest.raises(ValidationError, match="spawning_threshold cannot exceed max_concurrent_agents"):
        SwarmTopologyManifest(
            nodes={},
            spawning_threshold=11,
            max_concurrent_agents=10,
        )


def test_task_award_receipt_validation() -> None:
    TaskAwardReceipt(task_id="t1", awarded_syndicate={"agent_a": 50, "agent_b": 50}, cleared_price_magnitude=100)

    with pytest.raises(ValidationError, match="Syndicate allocation sum must exactly equal cleared_price_magnitude"):
        TaskAwardReceipt(task_id="t1", awarded_syndicate={"agent_a": 50, "agent_b": 40}, cleared_price_magnitude=100)


def test_distribution_profile_validation() -> None:
    # Valid
    DistributionProfile(distribution_type="gaussian", confidence_interval_95=(0.1, 0.9))

    # Invalid CI
    with pytest.raises(ValidationError, match=r"confidence_interval_95 must have interval\[0\] < interval\[1\]"):
        DistributionProfile(distribution_type="gaussian", confidence_interval_95=(0.9, 0.1))


def test_peft_adapter_contract_validation() -> None:
    adapter = PeftAdapterContract(
        adapter_id="a1",
        safetensors_hash="a" * 64,
        base_model_hash="b" * 64,
        adapter_rank=8,
        target_modules=["v_proj", "q_proj"],
    )
    # Check sorting
    assert adapter.target_modules == ["q_proj", "v_proj"]


def test_bilateral_sla_validation() -> None:
    sla = BilateralSLA(
        receiving_tenant_id="did:tenant:1",
        max_permitted_classification=InformationClassificationProfile.PUBLIC,
        liability_limit_magnitude=1000,
        permitted_geographic_regions=["us-east-1", "eu-west-1"],
    )
    assert sla.permitted_geographic_regions == ["eu-west-1", "us-east-1"]


def test_federated_discovery_manifest_validation() -> None:
    manifest = FederatedDiscoveryManifest(
        broadcast_endpoints=["http://b", "http://a"], supported_ontologies=["hash_b", "hash_a"]
    )
    assert manifest.broadcast_endpoints == ["http://a", "http://b"]
    assert manifest.supported_ontologies == ["hash_a", "hash_b"]


def test_delegated_capability_manifest_validation() -> None:
    manifest = DelegatedCapabilityManifest(
        capability_id="c1",
        principal_did="did:coreason:p1",
        delegate_agent_did="did:coreason:d1",
        allowed_tool_ids=["t2", "t1"],
        expiration_timestamp=100.0,
        cryptographic_signature="sig",
    )
    assert manifest.allowed_tool_ids == ["t1", "t2"]


def test_theory_of_mind_snapshot_sorting() -> None:
    snapshot = TheoryOfMindSnapshot(
        target_agent_id="a1",
        assumed_shared_beliefs=["b", "a"],
        identified_knowledge_gaps=["d", "c"],
        empathy_confidence_score=0.9,
    )
    assert snapshot.assumed_shared_beliefs == ["a", "b"]
    assert snapshot.identified_knowledge_gaps == ["c", "d"]


def test_epistemic_ledger_state_sorting() -> None:
    # Simple history setup to verify it sorts correctly
    b1 = BeliefMutationEvent(event_id="e1", timestamp=200.0, payload={"a": 1})
    b2 = BeliefMutationEvent(event_id="e2", timestamp=100.0, payload={"b": 2})

    r1 = RollbackIntent(request_id="r2", target_event_id="e1")
    r2 = RollbackIntent(request_id="r1", target_event_id="e2")

    m1 = MigrationContract(contract_id="m2", source_version="1.0.0", target_version="2.0.0")
    m2 = MigrationContract(contract_id="m1", source_version="2.0.0", target_version="3.0.0")

    c1 = DefeasibleCascadeEvent(
        cascade_id="c2", root_falsified_event_id="e1", propagated_decay_factor=0.5, quarantined_event_ids=["e2"]
    )
    c2 = DefeasibleCascadeEvent(
        cascade_id="c1", root_falsified_event_id="e2", propagated_decay_factor=0.5, quarantined_event_ids=["e1"]
    )

    ledger = EpistemicLedgerState(
        history=[b1, b2], active_rollbacks=[r1, r2], migration_contracts=[m1, m2], active_cascades=[c1, c2]
    )

    # Asserting sorted order based on validators
    assert ledger.history[0].event_id == "e2"
    assert ledger.history[1].event_id == "e1"

    assert ledger.active_rollbacks[0].request_id == "r1"
    assert ledger.active_rollbacks[1].request_id == "r2"

    assert ledger.migration_contracts[0].contract_id == "m1"
    assert ledger.migration_contracts[1].contract_id == "m2"

    assert ledger.active_cascades[0].cascade_id == "c1"
    assert ledger.active_cascades[1].cascade_id == "c2"


def test_neural_audit_attestation_receipt_sorting() -> None:
    sae_feature1 = SaeFeatureActivationState(feature_index=2, activation_magnitude=0.5)
    sae_feature2 = SaeFeatureActivationState(feature_index=1, activation_magnitude=0.9)

    receipt = NeuralAuditAttestationReceipt(audit_id="a1", layer_activations={0: [sae_feature1, sae_feature2]})

    assert receipt.layer_activations[0][0].feature_index == 1
    assert receipt.layer_activations[0][1].feature_index == 2


def test_consensus_policy_pbft() -> None:
    # Valid pbft
    quorum = QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="ignore"
    )
    ConsensusPolicy(strategy="pbft", quorum_rules=quorum)

    # Invalid pbft
    with pytest.raises(ValidationError, match="quorum_rules must be provided when strategy is 'pbft'"):
        ConsensusPolicy(strategy="pbft", quorum_rules=None)


def test_system2_remediation_intent_sorting() -> None:
    intent = System2RemediationIntent(
        fault_id="f1",
        target_node_id="did:coreason:n1",
        failing_pointers=["/c", "/a", "/b"],
        remediation_prompt="Fix it",
    )
    assert intent.failing_pointers == ["/a", "/b", "/c"]


def test_adjudication_rubric_profile_sorting() -> None:
    crit1 = GradingCriterionProfile(criterion_id="c2", description="test2", weight=1.0)
    crit2 = GradingCriterionProfile(criterion_id="c1", description="test1", weight=2.0)

    rubric = AdjudicationRubricProfile(rubric_id="r1", criteria=[crit1, crit2], passing_threshold=50.0)
    assert rubric.criteria[0].criterion_id == "c1"


def test_constitutional_policy_sorting() -> None:
    policy = ConstitutionalPolicy(rule_id="r1", description="test", severity="low", forbidden_intents=["b", "a"])
    assert policy.forbidden_intents == ["a", "b"]


def test_epistemic_quarantine_snapshot_sorting() -> None:
    t1 = TheoryOfMindSnapshot(
        target_agent_id="a2", assumed_shared_beliefs=[], identified_knowledge_gaps=[], empathy_confidence_score=1.0
    )
    t2 = TheoryOfMindSnapshot(
        target_agent_id="a1", assumed_shared_beliefs=[], identified_knowledge_gaps=[], empathy_confidence_score=1.0
    )

    c1 = FederatedCapabilityAttestationReceipt(
        attestation_id="c2",
        target_topology_id="did:coreason:t1",
        authorized_session=SecureSubSessionState(
            session_id="s1", allowed_vault_keys=[], max_ttl_seconds=10, description=""
        ),
        governing_sla=BilateralSLA(
            receiving_tenant_id="did:t:1",
            max_permitted_classification=InformationClassificationProfile.PUBLIC,
            liability_limit_magnitude=10,
            permitted_geographic_regions=[],
        ),
    )
    c2 = FederatedCapabilityAttestationReceipt(
        attestation_id="c1",
        target_topology_id="did:coreason:t1",
        authorized_session=SecureSubSessionState(
            session_id="s1", allowed_vault_keys=[], max_ttl_seconds=10, description=""
        ),
        governing_sla=BilateralSLA(
            receiving_tenant_id="did:t:1",
            max_permitted_classification=InformationClassificationProfile.PUBLIC,
            liability_limit_magnitude=10,
            permitted_geographic_regions=[],
        ),
    )

    snapshot = EpistemicQuarantineSnapshot(
        system_prompt="sys", active_context={}, theory_of_mind_models=[t1, t2], capability_attestations=[c1, c2]
    )

    assert snapshot.theory_of_mind_models[0].target_agent_id == "a1"
    assert snapshot.capability_attestations[0].attestation_id == "c1"


def test_semantic_discovery_intent_sorting() -> None:
    intent = SemanticDiscoveryIntent(
        query_vector=VectorEmbeddingState(vector_base64="", dimensionality=1, model_name="m"),
        min_isometry_score=0.9,
        required_structural_types=["b", "a"],
    )
    assert intent.required_structural_types == ["a", "b"]


def test_system1_reflex_policy_sorting() -> None:
    policy = System1ReflexPolicy(confidence_threshold=0.9, allowed_passive_tools=["b", "a"])
    assert policy.allowed_passive_tools == ["a", "b"]
