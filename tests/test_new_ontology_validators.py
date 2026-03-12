import pytest
from typing import Any

from coreason_manifest.spec.ontology import (
    BoundedJSONRPCIntent,
    BrowserDOMState,
    ContinuousMutationPolicy,
)


def test_bounded_json_rpc_intent() -> None:
    # Test valid simple params
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params={"a": 1}, id="1")
    assert intent.params == {"a": 1}

    # Test invalid type for params
    with pytest.raises(ValueError, match="params must be a dictionary"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params="invalid", id="1") # type: ignore

    # Test max depth
    params: dict[str, Any] = {}
    current = params
    for _i in range(11):
        current["key"] = {}
        current = current["key"]

    with pytest.raises(ValueError, match="JSON payload exceeds maximum depth of 10"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=params, id="1")

    # Test max dict keys
    params = {str(i): 1 for i in range(101)}
    with pytest.raises(ValueError, match="Dictionary exceeds maximum of 100 keys"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=params, id="1")

    # Test dict key length
    params = {"a" * 1001: 1}
    with pytest.raises(ValueError, match="Dictionary key exceeds maximum length of 1000"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=params, id="1")

    # Test max list length
    params2: dict[str, Any] = {"a": [1] * 1001}
    with pytest.raises(ValueError, match="List exceeds maximum of 1000 elements"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=params2, id="1")

    # Test string max length
    params3: dict[str, Any] = {"a": "b" * 10001}
    with pytest.raises(ValueError, match="String exceeds maximum length of 10000 characters"):
        BoundedJSONRPCIntent(jsonrpc="2.0", method="test", params=params3, id="1")


def test_browser_dom_state_ip_parsing() -> None:
    # Test hex IP
    with pytest.raises(ValueError, match="SSRF mathematical bound violation detected"):
        BrowserDOMState(
            current_url="http://0x7f000001",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )

    # Test integer IP
    with pytest.raises(ValueError, match="SSRF mathematical bound violation detected"):
        BrowserDOMState(
            current_url="http://2130706433",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )

    # Test octal IP parts
    with pytest.raises(ValueError, match="SSRF mathematical bound violation detected"):
        BrowserDOMState(
            current_url="http://0177.0.0.1",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )


def test_continuous_mutation_policy() -> None:
    with pytest.raises(
        ValueError, match="max_uncommitted_edges must be <= 10000 for append_only paradigm to prevent OOM crashes."
    ):
        ContinuousMutationPolicy(
            mutation_paradigm="append_only", max_uncommitted_edges=10001, micro_batch_interval_ms=10
        )

    policy = ContinuousMutationPolicy(
        mutation_paradigm="append_only", max_uncommitted_edges=10000, micro_batch_interval_ms=10
    )
    assert policy.max_uncommitted_edges == 10000


from coreason_manifest.spec.ontology import (
    BaseNodeProfile,
    DistributionProfile,
    DynamicLayoutManifest,
)


def test_dynamic_layout_manifest_ast_validation() -> None:
    # Valid t-string template
    valid = DynamicLayoutManifest(layout_tstring="f'some string {var}'")
    assert valid.layout_tstring == "f'some string {var}'"

    # Invalid AST injection (exec)
    with pytest.raises(ValueError, match="Kinetic execution bleed detected"):
        DynamicLayoutManifest(layout_tstring="import os\nos.system('ls')")


def test_base_node_profile_domain_extensions() -> None:
    valid = BaseNodeProfile(description="desc", domain_extensions={"a": 1, "b": "str", "c": [1, 2, 3]})
    assert valid.domain_extensions == {"a": 1, "b": "str", "c": [1, 2, 3]}

    # Test invalid key type
    with pytest.raises(ValueError, match="domain_extensions keys must be strings"):
        BaseNodeProfile(description="desc", domain_extensions={1: "a"}) # type: ignore

    # Test max depth
    params: dict[str, Any] = {}
    current = params
    for _i in range(6):
        current["key"] = {}
        current = current["key"]

    with pytest.raises(ValueError, match="domain_extensions exceeds maximum allowed depth of 5"):
        BaseNodeProfile(description="desc", domain_extensions=params)


def test_distribution_profile() -> None:
    with pytest.raises(ValueError, match="confidence_interval_95 must have interval\\[0\\] < interval\\[1\\]"):
        DistributionProfile(distribution_type="gaussian", confidence_interval_95=(1.0, 0.0))

    valid = DistributionProfile(distribution_type="gaussian", confidence_interval_95=(0.0, 1.0))
    assert valid.confidence_interval_95 == (0.0, 1.0)


from coreason_manifest.spec.ontology import (
    DocumentLayoutManifest,
    DocumentLayoutRegionState,
    ExecutionNodeReceipt,
    InsightCardProfile,
    MultimodalTokenAnchorState,
)


def test_insight_card_profile_xss() -> None:
    with pytest.raises(ValueError, match="Forbidden HTML event handler detected"):
        InsightCardProfile(panel_id="1", title="title", markdown_content="<a onload='alert(1)'>")
    with pytest.raises(ValueError, match="HTML tags are prohibited."):
        InsightCardProfile(panel_id="1", title="title", markdown_content="<script>alert(1)</script>")
    with pytest.raises(ValueError, match="Malicious executable link scheme detected"):
        InsightCardProfile(panel_id="1", title="title", markdown_content="[click here](javascript:alert(1))")

    valid = InsightCardProfile(panel_id="1", title="title", markdown_content="x < y")
    assert valid.markdown_content == "x < y"


def test_execution_node_receipt_hash() -> None:
    receipt = ExecutionNodeReceipt(
        request_id="req1",
        inputs={"a": 1},
        outputs={"b": 2},
    )
    assert receipt.node_hash is not None


def test_document_layout_manifest_dag() -> None:
    anchor = MultimodalTokenAnchorState(token_span_start=0, token_span_end=1)
    block1 = DocumentLayoutRegionState(block_id="b1", block_type="paragraph", anchor=anchor)
    block2 = DocumentLayoutRegionState(block_id="b2", block_type="paragraph", anchor=anchor)
    DocumentLayoutRegionState(block_id="b3", block_type="paragraph", anchor=anchor)

    # Valid
    manifest = DocumentLayoutManifest(blocks={"b1": block1, "b2": block2}, chronological_flow_edges=[("b1", "b2")])
    assert manifest.chronological_flow_edges == [("b1", "b2")]

    # Cycle
    with pytest.raises(ValueError, match="Reading order contains a cyclical contradiction."):
        DocumentLayoutManifest(
            blocks={"b1": block1, "b2": block2}, chronological_flow_edges=[("b1", "b2"), ("b2", "b1")]
        )

    # Missing node
    with pytest.raises(ValueError, match="Source block 'b3' does not exist"):
        DocumentLayoutManifest(blocks={"b1": block1, "b2": block2}, chronological_flow_edges=[("b3", "b2")])
    with pytest.raises(ValueError, match="Target block 'b3' does not exist"):
        DocumentLayoutManifest(blocks={"b1": block1, "b2": block2}, chronological_flow_edges=[("b1", "b3")])


from coreason_manifest.spec.ontology import (
    DAGTopologyManifest,
    QuorumPolicy,
    SystemNodeProfile,
)


def test_dag_topology_manifest_missing_edge_nodes() -> None:
    nodes: dict[str, AnyNodeProfile] = {"did:coreason:1": SystemNodeProfile(description="desc")}

    with pytest.raises(ValueError, match="Edge source 'did:coreason:2' does not exist in nodes registry."):
        DAGTopologyManifest(nodes=nodes, edges=[("did:coreason:2", "did:coreason:1")], max_depth=10, max_fan_out=10)

    with pytest.raises(ValueError, match="Edge target 'did:coreason:2' does not exist in nodes registry."):
        DAGTopologyManifest(nodes=nodes, edges=[("did:coreason:1", "did:coreason:2")], max_depth=10, max_fan_out=10)


def test_quorum_policy_math() -> None:
    with pytest.raises(ValueError, match="Byzantine Fault Tolerance requires min_quorum_size \\(N\\) >= 3f \\+ 1"):
        QuorumPolicy(
            max_tolerable_faults=1,
            min_quorum_size=3,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )

    valid = QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )
    assert valid.min_quorum_size == 4


from coreason_manifest.spec.ontology import (
    RiskLevelPolicy,
    TensorStructuralFormatProfile,
    _validate_payload_bounds,
)


def test_risk_level_policy_weight() -> None:
    assert RiskLevelPolicy.SAFE.weight == 0
    assert RiskLevelPolicy.STANDARD.weight == 1
    assert RiskLevelPolicy.CRITICAL.weight == 2


def test_tensor_structural_format_profile() -> None:
    assert TensorStructuralFormatProfile.FLOAT32.bytes_per_element == 4
    assert TensorStructuralFormatProfile.FLOAT64.bytes_per_element == 8
    assert TensorStructuralFormatProfile.INT8.bytes_per_element == 1
    assert TensorStructuralFormatProfile.UINT8.bytes_per_element == 1
    assert TensorStructuralFormatProfile.INT32.bytes_per_element == 4
    assert TensorStructuralFormatProfile.INT64.bytes_per_element == 8


def test_validate_payload_bounds() -> None:
    # max list items
    with pytest.raises(ValueError, match="List exceeds maximum item count of 1000"):
        _validate_payload_bounds([1] * 1001)

    # string keys only in dict
    with pytest.raises(ValueError, match="Dictionary keys must be strings"):
        _validate_payload_bounds({1: 1})  # type: ignore

    # invalid primitive
    class CustomObj:
        pass

    with pytest.raises(ValueError, match="Payload value must be a valid JSON primitive, got CustomObj"):
        _validate_payload_bounds(CustomObj())  # type: ignore


from coreason_manifest.spec.ontology import (
    ExecutionSpanReceipt,
    HTTPTransportProfile,
    InterventionReceipt,
    LatentScratchpadReceipt,
    SpatialBoundingBoxProfile,
    SSETransportProfile,
    TemporalBoundsProfile,
    ThoughtBranchState,
    WetwareAttestationContract,
)


def test_spatial_bounding_box_profile() -> None:
    with pytest.raises(ValueError, match="x_min cannot be strictly greater than x_max."):
        SpatialBoundingBoxProfile(x_min=0.5, y_min=0.1, x_max=0.4, y_max=0.2)
    with pytest.raises(ValueError, match="y_min cannot be strictly greater than y_max."):
        SpatialBoundingBoxProfile(x_min=0.1, y_min=0.5, x_max=0.2, y_max=0.4)


def test_http_transport_profile_crlf() -> None:
    with pytest.raises(ValueError, match="CRLF injection detected in headers"):
        HTTPTransportProfile(uri="http://example.com", headers={"Host": "example.com\r\n"}) # type: ignore
    with pytest.raises(ValueError, match="CRLF injection detected in headers"):
        HTTPTransportProfile(uri="http://example.com", headers={"Host\n": "example.com"}) # type: ignore


def test_sse_transport_profile_crlf() -> None:
    with pytest.raises(ValueError, match="CRLF injection detected in headers"):
        SSETransportProfile(uri="http://example.com", headers={"Host": "example.com\r\n"}) # type: ignore


def test_latent_scratchpad_receipt() -> None:
    tb1 = ThoughtBranchState(branch_id="b1", latent_content_hash="a" * 64)
    tb2 = ThoughtBranchState(branch_id="b2", latent_content_hash="b" * 64)

    # valid
    LatentScratchpadReceipt(
        trace_id="t1",
        explored_branches=[tb1, tb2],
        discarded_branches=["b2"],
        resolution_branch_id="b1",
        total_latent_tokens=10,
    )

    # resolution branch missing
    with pytest.raises(ValueError, match="resolution_branch_id 'b3' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="t1",
            explored_branches=[tb1, tb2],
            discarded_branches=["b2"],
            resolution_branch_id="b3",
            total_latent_tokens=10,
        )

    # discarded branch missing
    with pytest.raises(ValueError, match="discarded branch 'b3' not found in explored_branches"):
        LatentScratchpadReceipt(
            trace_id="t1",
            explored_branches=[tb1, tb2],
            discarded_branches=["b3"],
            resolution_branch_id="b1",
            total_latent_tokens=10,
        )


import uuid


def test_intervention_receipt_nonce() -> None:
    nonce1 = uuid.uuid4()
    nonce2 = uuid.uuid4()
    attestation = WetwareAttestationContract(
        mechanism="fido2_webauthn", did_subject="did:example:1", cryptographic_payload="blob", dag_node_nonce=nonce2
    )

    with pytest.raises(ValueError, match="Anti-Replay Lock Triggered"):
        InterventionReceipt(
            intervention_request_id=nonce1,
            target_node_id="did:example:2",
            approved=True,
            attestation=attestation,
            feedback="f",
        )


def test_execution_span_receipt() -> None:
    with pytest.raises(ValueError, match="end_time_unix_nano cannot be before start_time_unix_nano"):
        ExecutionSpanReceipt(trace_id="t1", span_id="s1", name="n1", start_time_unix_nano=100, end_time_unix_nano=50)

    valid = ExecutionSpanReceipt(
        trace_id="t1", span_id="s1", name="n1", start_time_unix_nano=50, end_time_unix_nano=100
    )
    assert valid.end_time_unix_nano == 100


def test_temporal_bounds_profile() -> None:
    with pytest.raises(ValueError, match="valid_to cannot be before valid_from"):
        TemporalBoundsProfile(valid_from=100.0, valid_to=50.0)

    valid = TemporalBoundsProfile(valid_from=50.0, valid_to=100.0)
    assert valid.valid_from == 50.0


from coreason_manifest.spec.ontology import (
    AdversarialMarketTopologyManifest,
    ConsensusFederationTopologyManifest,
    EvaluatorOptimizerTopologyManifest,
    NDimensionalTensorManifest,
    TaskAwardReceipt,
    AnyNodeProfile,
)


def test_evaluator_optimizer_topology() -> None:
    nodes: dict[str, AnyNodeProfile] = {
        "did:example:1": SystemNodeProfile(description="actor"),
        "did:example:2": SystemNodeProfile(description="critic"),
    }

    with pytest.raises(ValueError, match="Generator node 'did:example:3' not found in topology nodes"):
        EvaluatorOptimizerTopologyManifest(
            generator_node_id="did:example:3", evaluator_node_id="did:example:2", max_revision_loops=5, nodes=nodes
        )
    with pytest.raises(ValueError, match="Evaluator node 'did:example:3' not found in topology nodes"):
        EvaluatorOptimizerTopologyManifest(
            generator_node_id="did:example:1", evaluator_node_id="did:example:3", max_revision_loops=5, nodes=nodes
        )
    with pytest.raises(ValueError, match="Generator and Evaluator cannot be the same node."):
        EvaluatorOptimizerTopologyManifest(
            generator_node_id="did:example:1", evaluator_node_id="did:example:1", max_revision_loops=5, nodes=nodes
        )


def test_task_award_receipt() -> None:
    from coreason_manifest.spec.ontology import EscrowPolicy

    escrow = EscrowPolicy(escrow_locked_magnitude=200, release_condition_metric="a", refund_target_node_id="b")
    with pytest.raises(ValueError, match="Escrow locked amount cannot exceed the total cleared price."):
        TaskAwardReceipt(task_id="t1", awarded_syndicate={"a": 100}, cleared_price_magnitude=100, escrow=escrow)

    with pytest.raises(ValueError, match="Syndicate allocation sum must exactly equal cleared_price_magnitude"):
        TaskAwardReceipt(task_id="t1", awarded_syndicate={"a": 50, "b": 60}, cleared_price_magnitude=100)


def test_adversarial_market_topology_manifest() -> None:
    from coreason_manifest.spec.ontology import PredictionMarketPolicy

    market_rules = PredictionMarketPolicy(
        staking_function="linear", min_liquidity_magnitude=10, convergence_delta_threshold=0.5
    )

    with pytest.raises(
        ValueError, match="Topological Contradiction: A node cannot exist in both the Blue and Red teams."
    ):
        AdversarialMarketTopologyManifest(
            blue_team_ids=["did:example:1"],
            red_team_ids=["did:example:1"],
            adjudicator_id="did:example:3",
            market_rules=market_rules,
        )
    with pytest.raises(
        ValueError, match="Topological Contradiction: The adjudicator cannot be a member of a competing team."
    ):
        AdversarialMarketTopologyManifest(
            blue_team_ids=["did:example:1"],
            red_team_ids=["did:example:2"],
            adjudicator_id="did:example:1",
            market_rules=market_rules,
        )

    valid = AdversarialMarketTopologyManifest(
        blue_team_ids=["did:example:1"],
        red_team_ids=["did:example:2"],
        adjudicator_id="did:example:3",
        market_rules=market_rules,
    )
    compiled = valid.compile_to_base_topology()
    assert compiled.adjudicator_id == "did:example:3"
    assert len(compiled.nodes) == 3


def test_consensus_federation_topology_manifest() -> None:
    from coreason_manifest.spec.ontology import QuorumPolicy

    quorum = QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )

    with pytest.raises(ValueError, match="Topological Contradiction: Adjudicator cannot act as a voting participant."):
        ConsensusFederationTopologyManifest(
            participant_ids=["did:example:1", "did:example:2", "did:example:3"],
            adjudicator_id="did:example:1",
            quorum_rules=quorum,
        )

    valid = ConsensusFederationTopologyManifest(
        participant_ids=["did:example:1", "did:example:2", "did:example:3"],
        adjudicator_id="did:example:4",
        quorum_rules=quorum,
    )
    compiled = valid.compile_to_base_topology()
    assert compiled.adjudicator_id == "did:example:4"
    assert len(compiled.nodes) == 4


def test_n_dimensional_tensor_manifest() -> None:
    with pytest.raises(ValueError, match="Tensor shape must have at least 1 dimension"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(),
            vram_footprint_bytes=10,
            merkle_root="a" * 64,
            storage_uri="uri",
        )

    with pytest.raises(ValueError, match="Tensor dimensions must be strictly positive integers"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(0,),
            vram_footprint_bytes=10,
            merkle_root="a" * 64,
            storage_uri="uri",
        )

    with pytest.raises(ValueError, match="Topological mismatch: Shape"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, 2),
            vram_footprint_bytes=10,
            merkle_root="a" * 64,
            storage_uri="uri",
        )


from coreason_manifest.spec.ontology import UtilityJustificationGraphReceipt


def test_utility_justification_graph_receipt() -> None:
    with pytest.raises(
        ValueError, match="Topological Interlock Failed: ensemble_spec defined but variance threshold is 0.0"
    ):
        UtilityJustificationGraphReceipt(
            superposition_variance_threshold=0.0,
            ensemble_spec={ # type: ignore
                "concurrent_branch_ids": ["did:example:1", "did:example:2"],
                "fusion_function": "weighted_consensus",
            },
        )
    with pytest.raises(ValueError, match="Tensor Poisoning Detected: Vector 'a' contains invalid float"):
        UtilityJustificationGraphReceipt(superposition_variance_threshold=1.0, optimizing_vectors={"a": float("inf")})
    with pytest.raises(ValueError, match="Tensor Poisoning Detected: Vector 'b' contains invalid float"):
        UtilityJustificationGraphReceipt(superposition_variance_threshold=1.0, degrading_vectors={"b": float("nan")})


from coreason_manifest.spec.ontology import (
    BypassReceipt,
    ConstitutionalPolicy,
    DynamicRoutingManifest,
    GenerativeManifoldSLA,
    GlobalGovernancePolicy,
    GlobalSemanticProfile,
)


def test_global_governance_policy() -> None:
    with pytest.raises(ValueError, match="CRITICAL LICENSE VIOLATION"):
        GlobalGovernancePolicy(
            mandatory_license_rule=ConstitutionalPolicy(
                rule_id="other", description="desc", severity="critical", forbidden_intents=["a"]
            ),
            max_budget_magnitude=100,
            max_global_tokens=1000,
            global_timeout_seconds=60,
        )
    with pytest.raises(ValueError, match="CRITICAL LICENSE VIOLATION"):
        GlobalGovernancePolicy(
            mandatory_license_rule=ConstitutionalPolicy(
                rule_id="PPL_3_0_COMPLIANCE", description="desc", severity="high", forbidden_intents=["a"]
            ),
            max_budget_magnitude=100,
            max_global_tokens=1000,
            global_timeout_seconds=60,
        )
    valid = GlobalGovernancePolicy(
        mandatory_license_rule=ConstitutionalPolicy(
            rule_id="PPL_3_0_COMPLIANCE", description="desc", severity="critical", forbidden_intents=["a"]
        ),
        max_budget_magnitude=100,
        max_global_tokens=1000,
        global_timeout_seconds=60,
    )
    assert valid.max_budget_magnitude == 100


def test_generative_manifold_sla() -> None:
    with pytest.raises(ValueError, match="Geometric explosion risk"):
        GenerativeManifoldSLA(max_topological_depth=100, max_node_fanout=11, max_synthetic_tokens=100)

    valid = GenerativeManifoldSLA(max_topological_depth=100, max_node_fanout=10, max_synthetic_tokens=100)
    assert valid.max_synthetic_tokens == 100


def test_dynamic_routing_manifest() -> None:
    profile = GlobalSemanticProfile(artifact_event_id="a1", detected_modalities=["text"], token_density=10)
    with pytest.raises(ValueError, match="Epistemic Violation: Cannot route to subgraph"):
        DynamicRoutingManifest(
            manifest_id="m1",
            artifact_profile=profile,
            active_subgraphs={"tabular_grid": []},
            branch_budgets_magnitude={},
        )

    bypass = BypassReceipt(
        artifact_event_id="a2",
        bypassed_node_id="did:example:1",
        justification="modality_mismatch",
        cryptographic_null_hash="b" * 64,
    )
    with pytest.raises(ValueError, match="Merkle Violation: BypassReceipt artifact_event_id does not match"):
        DynamicRoutingManifest(
            manifest_id="m1",
            artifact_profile=profile,
            active_subgraphs={},
            bypassed_steps=[bypass],
            branch_budgets_magnitude={},
        )


from coreason_manifest.spec.ontology import CognitiveCritiqueProfile


def test_cognitive_critique_profile() -> None:
    valid = CognitiveCritiqueProfile(reasoning_trace_hash="a" * 64, epistemic_penalty_scalar=0.5)
    assert valid.epistemic_penalty_scalar == 0.5


from coreason_manifest.spec.ontology import StateDifferentialManifest, StateMutationIntent
from coreason_manifest.utils.algebra import apply_state_differential


def test_apply_state_differential() -> None:
    manifest = StateDifferentialManifest(
        diff_id="d1",
        author_node_id="did:example:1",
        lamport_timestamp=1,
        vector_clock={},
        patches=[
            StateMutationIntent(op="add", path="/a", value=1),
            StateMutationIntent(op="add", path="/b/-", value=2),
            StateMutationIntent(op="replace", path="/c", value=3),
            StateMutationIntent(op="remove", path="/d"),
            StateMutationIntent(op="move", path="/e", **{"from": "/f"}),
            StateMutationIntent(op="copy", path="/g", **{"from": "/h"}),
            StateMutationIntent(op="test", path="/i", value=1),
        ],
    )

    current_state = {
        "b": [1],
        "c": 2,
        "d": 1,
        "f": 4,
        "h": 5,
        "i": 1,
    }

    new_state = apply_state_differential(current_state, manifest)

    assert new_state["a"] == 1
    assert new_state["b"] == [1, 2]
    assert new_state["c"] == 3
    assert "d" not in new_state
    assert new_state["e"] == 4
    assert "f" not in new_state
    assert new_state["g"] == 5
    assert new_state["h"] == 5
    assert new_state["i"] == 1


from coreason_manifest.utils.algebra import verify_ast_safety, verify_merkle_proof


def test_verify_ast_safety() -> None:
    assert verify_ast_safety("1 + 1")

    with pytest.raises(ValueError, match="Payload is not valid syntax."):
        verify_ast_safety("import os")

    with pytest.raises(ValueError, match="Payload is not valid syntax."):
        verify_ast_safety("1 +")


def test_verify_merkle_proof() -> None:
    node1 = ExecutionNodeReceipt(request_id="1", inputs=1, outputs=2)
    node1_hash = node1.generate_node_hash()

    node2 = ExecutionNodeReceipt(
        request_id="2", root_request_id="1", parent_request_id="1", inputs=2, outputs=3, parent_hashes=[node1_hash]
    )

    assert verify_merkle_proof([node1, node2])


def test_apply_state_differential_errors() -> None:
    manifest_test = StateDifferentialManifest(
        diff_id="d1",
        author_node_id="did:example:1",
        lamport_timestamp=1,
        vector_clock={},
        patches=[StateMutationIntent(op="test", path="/a", value=2)],
    )
    with pytest.raises(ValueError, match="Patch test operation failed"):
        apply_state_differential({"a": 1}, manifest_test)

    manifest_invalid_ptr = StateDifferentialManifest(
        diff_id="d1",
        author_node_id="did:example:1",
        lamport_timestamp=1,
        vector_clock={},
        patches=[StateMutationIntent(op="add", path="a", value=2)],
    )
    with pytest.raises(ValueError, match="Invalid JSON pointer"):
        apply_state_differential({"a": 1}, manifest_invalid_ptr)

    manifest_add_invalid = StateDifferentialManifest(
        diff_id="d1",
        author_node_id="did:example:1",
        lamport_timestamp=1,
        vector_clock={},
        patches=[StateMutationIntent(op="add", path="/a/b", value=2)],
    )
    with pytest.raises(ValueError, match="Cannot add to path"):
        apply_state_differential({"a": 1}, manifest_add_invalid)

    manifest_remove_invalid = StateDifferentialManifest(
        diff_id="d1",
        author_node_id="did:example:1",
        lamport_timestamp=1,
        vector_clock={},
        patches=[StateMutationIntent(op="remove", path="/b")],
    )
    with pytest.raises(ValueError, match="Cannot remove from path"):
        apply_state_differential({"a": 1}, manifest_remove_invalid)


def test_apply_state_differential_array_operations() -> None:
    manifest = StateDifferentialManifest(
        diff_id="d1",
        author_node_id="did:example:1",
        lamport_timestamp=1,
        vector_clock={},
        patches=[
            StateMutationIntent(op="add", path="/a/0", value=0),  # insert at 0
            StateMutationIntent(op="remove", path="/b/1"),
            StateMutationIntent(op="replace", path="/c/0", value=99),
            StateMutationIntent(op="move", path="/d/0", **{"from": "/e/0"}),
            StateMutationIntent(op="copy", path="/f/-", **{"from": "/g/0"}),
        ],
    )

    current_state = {"a": [1, 2], "b": [1, 2, 3], "c": [1, 2], "d": [1, 2], "e": [10, 20], "f": [1, 2], "g": [100, 200]}

    new_state = apply_state_differential(current_state, manifest)

    assert new_state["a"] == [0, 1, 2]
    assert new_state["b"] == [1, 3]
    assert new_state["c"] == [99, 2]
    assert new_state["d"] == [10, 1, 2]
    assert new_state["e"] == [20]
    assert new_state["f"] == [1, 2, 100]
    assert new_state["g"] == [100, 200]


def test_apply_state_differential_nested_errors() -> None:
    manifest_replace_invalid = StateDifferentialManifest(
        diff_id="d1",
        author_node_id="did:example:1",
        lamport_timestamp=1,
        vector_clock={},
        patches=[StateMutationIntent(op="replace", path="/a/-", value=2)],
    )
    with pytest.raises(ValueError, match="Cannot replace at path"):
        apply_state_differential({"a": [1]}, manifest_replace_invalid)

    manifest_move_invalid = StateDifferentialManifest(
        diff_id="d1",
        author_node_id="did:example:1",
        lamport_timestamp=1,
        vector_clock={},
        patches=[StateMutationIntent(op="move", path="/a", **{"from": "/b/-"})],
    )
    with pytest.raises(ValueError, match="Cannot extract from end of array"):
        apply_state_differential({"b": [1]}, manifest_move_invalid)
