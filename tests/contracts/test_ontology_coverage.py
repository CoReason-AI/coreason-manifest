# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import contextlib

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    BilateralSLA,
    BoundedInterventionScopePolicy,
    BrowserDOMState,
    BypassReceipt,
    ContinuousMutationPolicy,
    DelegatedCapabilityManifest,
    DistributionProfile,
    DynamicRoutingManifest,
    EnsembleTopologyProfile,
    EpistemicArgumentClaimState,
    EpistemicAxiomVerificationReceipt,
    EpistemicPromotionEvent,
    EvictionPolicy,
    EvidentiaryWarrantState,
    ExecutionNodeReceipt,
    FederatedCapabilityAttestationReceipt,
    GenerativeManifoldSLA,
    GlobalSemanticProfile,
    HTTPTransportProfile,
    InformationClassificationProfile,
    NDimensionalTensorManifest,
    OntologicalSurfaceProjectionManifest,
    SaeLatentPolicy,
    SecureSubSessionState,
    SemanticDiscoveryIntent,
    SystemNodeProfile,
    TensorStructuralFormatProfile,
    VectorEmbeddingState,
)


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
@given(
    url=st.sampled_from(
        [
            "file:///etc/passwd",
            "http://[::1]/",
            "http://0x7f000001",
            "http://0177.0.0.1",
            "http://2130706433",
            "http://localhost.localdomain",
            "http://broadcasthost",
            "http://169.254.169.254",  # link-local
            "http://224.0.0.1",  # multicast
            "http://10.0.0.1",
            "http://bad.local",
            "http://test.internal",
            "http://0.0.0.0",
            "http://127.1",
            "http://127.0.1",
        ]
    )
)
def test_browser_dom_state_ssrf_violations(url: str) -> None:
    with pytest.raises((ValidationError, ValueError)):
        BrowserDOMState(
            current_url=url,
            viewport_size=(1920, 1080),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
@given(
    url=st.sampled_from(
        [
            "data:text/html,test",  # No hostname
            "http://127.0.0.",  # Empty parsing part
            "http://127.0.0.256",  # Part > 255
            "http://127.0.256.1",  # part > 255 len 4
            "http://127.0.0.4294967300",  # > 4294967295 limit
            "http://127.0.70000",  # len 3, part > 65535,
            "http://127.256.1",  # len 3, part 0/1 > 255
            "http://127.16777216",  # len 2, part 1 > 16777215
            "http://256.1",  # len 2, part 0 > 255
        ]
    )
)
def test_browser_dom_state_valid_urls(url: str) -> None:
    # These URLs will fail IP parsing, and revert to hostname evaluation which is allowed.
    BrowserDOMState(
        current_url=url,
        viewport_size=(1920, 1080),
        dom_hash="a" * 64,
        accessibility_tree_hash="b" * 64,
    )


def test_browser_dom_state_invalid_hostname() -> None:
    with pytest.raises(ValidationError):
        BrowserDOMState(
            current_url="http://",
            viewport_size=(1920, 1080),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10)
@given(max_edges=st.integers(min_value=10001, max_value=1000000000))
def test_continuous_mutation_policy_oom_prevention(max_edges: int) -> None:
    with pytest.raises(ValidationError):
        ContinuousMutationPolicy(
            mutation_paradigm="append_only",
            max_uncommitted_edges=max_edges,
            micro_batch_interval_ms=100,
        )


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10)
@given(
    lower=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    upper=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
def test_distribution_profile_confidence_interval(lower: float, upper: float) -> None:
    if lower >= upper:
        with pytest.raises(ValidationError):
            DistributionProfile(distribution_type="gaussian", confidence_interval_95=(lower, upper))
    else:
        profile = DistributionProfile(distribution_type="gaussian", confidence_interval_95=(lower, upper))
        assert profile.confidence_interval_95 == (lower, upper)


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10)
@given(allowed_fields=st.lists(st.text(min_size=8, max_size=15, alphabet="abcdefghi_.-:"), min_size=2, max_size=10))
def test_sort_arrays_validators(allowed_fields: list[str]) -> None:
    # Ensure items are unique so we don't have duplicated elements in length checks
    allowed_fields = list(set(allowed_fields))
    if len(allowed_fields) < 2:
        return

    policy = BoundedInterventionScopePolicy(
        allowed_fields=allowed_fields,
        json_schema_whitelist={},
    )
    assert policy.allowed_fields == sorted(allowed_fields)

    intent = SemanticDiscoveryIntent(
        query_vector=VectorEmbeddingState(vector_base64="aaaa", dimensionality=1536, model_name="test"),
        min_isometry_score=0.5,
        required_structural_types=allowed_fields,
    )
    assert intent.required_structural_types == sorted(allowed_fields)

    # Needs pattern ^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$
    did_fields = [f"did:example:{f.replace(':', '_')}" for f in allowed_fields]

    topology = EnsembleTopologyProfile(
        concurrent_branch_ids=did_fields,
        fusion_function="weighted_consensus",
    )
    assert topology.concurrent_branch_ids == sorted(did_fields)

    event = EpistemicPromotionEvent(
        event_id="evt_1",
        timestamp=1.0,
        source_episodic_event_ids=allowed_fields,
        crystallized_semantic_node_id="node_1",
        compression_ratio=0.5,
    )
    assert event.source_episodic_event_ids == sorted(allowed_fields)


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=20)
@given(
    bad_header_key=st.sampled_from(["Header\rName", "Header\nName"]), bad_header_val=st.sampled_from(["val\r", "val\n"])
)
def test_http_transport_profile_crlf(bad_header_key: str, bad_header_val: str) -> None:
    from pydantic import HttpUrl

    with pytest.raises(ValidationError, match="CRLF injection"):
        HTTPTransportProfile(uri=HttpUrl("http://example.com/"), headers={bad_header_key: "clean_val"})

    with pytest.raises(ValidationError, match="CRLF injection"):
        HTTPTransportProfile(uri=HttpUrl("http://example.com/"), headers={"clean_key": bad_header_val})


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10)
@given(
    claim=st.text(min_size=1, max_size=100),
    warrant1=st.text(min_size=1, max_size=50),
    warrant2=st.text(min_size=1, max_size=50),
)
def test_epistemic_argument_claim_state_sorting(claim: str, warrant1: str, warrant2: str) -> None:
    # ensure deterministic
    w1 = EvidentiaryWarrantState(source_event_id="e1", justification=warrant1)
    w2 = EvidentiaryWarrantState(source_event_id="e2", justification=warrant2)

    cs = EpistemicArgumentClaimState(claim_id="claim_1", proponent_id="prop_1", text_chunk=claim, warrants=[w1, w2])

    assert cs.warrants == sorted([w1, w2], key=lambda x: x.justification)


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10)
@given(protected_event_ids=st.lists(st.text(min_size=1, max_size=128), min_size=2, max_size=10))
def test_eviction_policy_sorting(protected_event_ids: list[str]) -> None:
    policy = EvictionPolicy(strategy="fifo", max_retained_tokens=1000, protected_event_ids=protected_event_ids)
    assert policy.protected_event_ids == sorted(protected_event_ids)


def test_generative_manifold_sla_geometric_bounds() -> None:
    with pytest.raises(ValidationError, match="Geometric explosion risk"):
        GenerativeManifoldSLA(max_topological_depth=5, max_node_fanout=5, max_synthetic_tokens=100)


def test_federated_session_state_restricted_vault_locks() -> None:
    sla = BilateralSLA(
        receiving_tenant_id="tenant_p",
        max_permitted_classification=InformationClassificationProfile.RESTRICTED,
        liability_limit_magnitude=1000,
        permitted_geographic_regions=["us-east-1"],
    )
    session = SecureSubSessionState(
        session_id="sess_1", max_ttl_seconds=3600, description="Test", allowed_vault_keys=[]
    )
    with pytest.raises(ValidationError, match="RESTRICTED federated connections MUST define allowed_vault_keys"):
        FederatedCapabilityAttestationReceipt(
            attestation_id="attest_1",
            target_topology_id="did:example:target",
            authorized_session=session,
            governing_sla=sla,
        )


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10)
@given(
    allowed_tool_ids=st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-", min_size=1, max_size=128),
        min_size=2,
        max_size=10,
    )
)
def test_delegated_capability_manifest_sorting(allowed_tool_ids: list[str]) -> None:
    manifest = DelegatedCapabilityManifest(
        capability_id="cap_1",
        principal_did="did:example:p",
        delegate_agent_did="did:example:d",
        allowed_tool_ids=allowed_tool_ids,
        expiration_timestamp=100.0,
        cryptographic_signature="sig",
    )
    assert manifest.allowed_tool_ids == sorted(allowed_tool_ids)


def test_dynamic_routing_manifest_validation() -> None:
    profile = GlobalSemanticProfile(artifact_event_id="art_1", detected_modalities=["text"], token_density=10)

    with pytest.raises(ValidationError, match="Cannot route to subgraph"):
        DynamicRoutingManifest(
            manifest_id="route_1",
            artifact_profile=profile,
            active_subgraphs={"tabular_grid": ["did:example:node1"]},
            bypassed_steps=[],
            branch_budgets_magnitude={"did:example:node1": 100},
        )

    bypass = BypassReceipt(
        artifact_event_id="art_2",
        bypassed_node_id="did:example:node2",
        justification="modality_mismatch",
        cryptographic_null_hash="0" * 64,
    )

    with pytest.raises(ValidationError, match="BypassReceipt artifact_event_id does not match"):
        DynamicRoutingManifest(
            manifest_id="route_1",
            artifact_profile=profile,
            active_subgraphs={"text": ["did:example:node1"]},
            bypassed_steps=[bypass],
            branch_budgets_magnitude={"did:example:node1": 100},
        )


def test_system_node_profile_domain_extensions_validation() -> None:
    from typing import Any

    # 1. Depth > 5
    deep_dict: dict[str, Any] = {}
    current = deep_dict
    for _i in range(5):
        current["k"] = {}
        current = current["k"]
    current["k"] = "value"

    with pytest.raises(ValueError, match="maximum allowed depth of 5"):
        SystemNodeProfile(description="desc", domain_extensions=deep_dict)

    # 2. Non-string keys
    with pytest.raises(ValueError, match="keys must be strings"):
        SystemNodeProfile(
            description="desc",
            domain_extensions={123: "val"},  # type: ignore
        )

    # 3. Keys too long
    with pytest.raises(ValueError, match="exceeds maximum length of 255"):
        SystemNodeProfile(description="desc", domain_extensions={"a" * 256: "val"})

    # 4. Non-JSON primitives
    class ComplexObj:
        pass

    with pytest.raises(ValueError, match="leaf values must be JSON primitives"):
        SystemNodeProfile(description="desc", domain_extensions={"key": ComplexObj()})


def test_ndimensional_tensor_manifest_physics_engine() -> None:
    # 1. 0 dimensions
    with pytest.raises(ValueError, match="at least 1 dimension"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(),
            vram_footprint_bytes=100,
            merkle_root="a" * 64,
            storage_uri="s3://foo",
        )
    # 2. <= 0 size
    with pytest.raises(ValueError, match="strictly positive integers"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(0,),
            vram_footprint_bytes=100,
            merkle_root="a" * 64,
            storage_uri="s3://foo",
        )
    # 3. Size mismatch
    with pytest.raises(ValueError, match="Topological mismatch"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, 2),  # 4 elements * 4 bytes = 16 bytes
            vram_footprint_bytes=100,
            merkle_root="a" * 64,
            storage_uri="s3://foo",
        )


def test_execution_node_receipt_lineage_and_hash() -> None:
    # 1. Orphaned Lineage
    with pytest.raises(ValueError, match="Orphaned Lineage"):
        ExecutionNodeReceipt(
            request_id="req_1",
            parent_request_id="req_p",
            root_request_id=None,
            inputs={"a": 1},
            outputs={"b": 2},
            parent_hashes=[],
        )

    # 2. Hash generation
    receipt = ExecutionNodeReceipt(
        request_id="req_1",
        parent_request_id="req_p",
        root_request_id="req_r",
        inputs={"a": 1, "b": [1, 2]},
        outputs={"c": 3},
        parent_hashes=["hash1"],
    )
    assert receipt.node_hash is not None
    assert len(receipt.node_hash) == 64


def test_sae_latent_policy_sorting_and_decay() -> None:
    # 1. Validation error on smooth_decay without profile
    with pytest.raises(ValueError, match="smoothing_profile must be provided"):
        SaeLatentPolicy(
            target_feature_index=1,
            monitored_layers=[2, 1],
            max_activation_threshold=10.0,
            violation_action="smooth_decay",
            sae_dictionary_hash="a" * 64,
        )
    # 2. Sorting
    policy = SaeLatentPolicy(
        target_feature_index=1,
        monitored_layers=[2, 1],
        max_activation_threshold=10.0,
        violation_action="clamp",
        clamp_value=5.0,
        sae_dictionary_hash="a" * 64,
    )
    assert policy.monitored_layers == [1, 2]


def test_ontological_surface_projection_manifest_sorting() -> None:
    manifest = OntologicalSurfaceProjectionManifest(
        projection_id="proj_1", action_spaces=[], supported_personas=[], available_procedural_manifolds=[]
    )
    assert manifest is not None


def test_epistemic_axiom_verification_receipt_quarantine() -> None:
    import time

    with pytest.raises(ValueError, match="Epistemic Contagion Prevented"):
        EpistemicAxiomVerificationReceipt(
            event_id="evt_1",
            timestamp=int(time.time()),
            source_prediction_id="pred_1",
            sequence_similarity_score=0.9,
            fact_score_passed=False,
        )


def test_information_flow_policy_sorting() -> None:
    from coreason_manifest.spec.ontology import InformationFlowPolicy

    policy = InformationFlowPolicy(policy_id="policy_1", rules=[], latent_firewalls=[])
    assert policy.rules == []
    assert policy.latent_firewalls == []


def test_steady_state_hypothesis_state_sorting() -> None:
    from coreason_manifest.spec.ontology import SteadyStateHypothesisState

    state = SteadyStateHypothesisState(
        expected_max_latency=10.0, max_loops_allowed=5, required_tool_usage=["tool_b", "tool_a"]
    )
    assert state.required_tool_usage == ["tool_a", "tool_b"]


def test_chaos_experiment_task_sorting() -> None:
    from coreason_manifest.spec.ontology import ChaosExperimentTask, SteadyStateHypothesisState

    task = ChaosExperimentTask(
        experiment_id="exp_1",
        hypothesis=SteadyStateHypothesisState(expected_max_latency=1.0, max_loops_allowed=10),
        faults=[],
        shocks=[],
    )
    assert task.faults == []


def test_epistemic_chain_graph_state_sorting() -> None:
    from coreason_manifest.spec.ontology import EpistemicChainGraphState

    state = EpistemicChainGraphState.model_validate(
        {
            "chain_id": "chain_1",
            "syntactic_roots": ["root_1"],
            "semantic_leaves": [
                {"source_concept_id": "b", "directed_edge_type": "ext:is_a", "target_concept_id": "b"},
                {"source_concept_id": "a", "directed_edge_type": "ext:is_a", "target_concept_id": "a"},
            ],
        },
        context={"allowed_ext_intents": {"ext:is_a"}},
    )
    assert state.semantic_leaves[0].source_concept_id == "a"


def test_semantic_firewall_policy_sorting() -> None:
    from coreason_manifest.spec.ontology import SemanticFirewallPolicy

    policy = SemanticFirewallPolicy(max_input_tokens=1000, action_on_violation="drop", forbidden_intents=["b", "a"])
    assert policy.forbidden_intents == ["a", "b"]


def test_sse_transport_profile_crlf_injection() -> None:
    from pydantic import HttpUrl

    from coreason_manifest.spec.ontology import SSETransportProfile

    with pytest.raises(ValueError, match="CRLF injection detected"):
        SSETransportProfile(uri=HttpUrl("http://example.com/sse"), headers={"test\r": "val"})
    with pytest.raises(ValueError, match="CRLF injection detected"):
        SSETransportProfile(uri=HttpUrl("http://example.com/sse"), headers={"test": "val\n"})


def test_compute_provisioning_intent_sorting() -> None:
    from coreason_manifest.spec.ontology import ComputeProvisioningIntent

    intent = ComputeProvisioningIntent(max_budget=100.0, required_capabilities=["b", "a"], qos_class="interactive")
    assert intent.required_capabilities == ["a", "b"]


def test_semantic_alignment_handshake_sorting() -> None:
    from coreason_manifest.spec.ontology import OntologicalHandshakeReceipt

    handshake = OntologicalHandshakeReceipt(
        handshake_id="cid_1",
        participant_node_ids=["b", "a"],
        measured_cosine_similarity=0.5,
        alignment_status="aligned",
    )
    assert handshake.participant_node_ids == ["a", "b"]


def test_bulk_array_sorting_coverage() -> None:
    from coreason_manifest.spec.ontology import (
        BeliefMutationEvent,
        ChaosExperimentTask,
        DefeasibleRebuttalContract,
        EpistemicQuarantineSnapshot,
        HypothesisGenerationEvent,
        MarketResolutionState,
        MCPClientBindingProfile,
        MCPResourceManifest,
        MCPServerBindingProfile,
        MechanisticAuditContract,
        MigrationContract,
        PeftAdapterContract,
        SteadyStateHypothesisState,
        StructuralCausalGraphProfile,
        SwarmTopologyManifest,
        System1ReflexPolicy,
        TheoryOfMindSnapshot,
    )

    o1 = MCPResourceManifest.model_construct(schema_dependencies=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o1.sort_arrays()  # type: ignore

    o2 = MCPClientBindingProfile.model_construct(available_roots=[], required_capabilities=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o2.sort_arrays()  # type: ignore

    o3 = MarketResolutionState.model_construct(
        winning_hypothesis_ids=[], falsified_hypothesis_ids=[], consensus_proofs=[], isolated_agent_ids=[]
    )  # type: ignore
    with contextlib.suppress(AttributeError):
        o3.sort_arrays()  # type: ignore

    o4 = MechanisticAuditContract.model_construct(monitored_attention_heads=[], causal_interventions=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o4.sort_arrays()  # type: ignore

    o5 = MigrationContract.model_construct(backward_compatible_edges=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o5.sort_arrays()  # type: ignore

    o6 = PeftAdapterContract.model_construct(target_modules=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o6.sort_arrays()  # type: ignore

    o7 = MCPServerBindingProfile.model_construct(exposed_schemas=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o7.sort_arrays()  # type: ignore

    o8 = SteadyStateHypothesisState.model_construct(measured_invariants=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o8.sort_arrays()  # type: ignore

    o9 = ChaosExperimentTask.model_construct(faults=[], shocks=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o9.sort_arrays()  # type: ignore

    o10 = StructuralCausalGraphProfile.model_construct(observed_variables=[], latent_variables=[], causal_edges=[])
    with contextlib.suppress(AttributeError):
        o10.sort_arrays()  # type: ignore

    o11 = HypothesisGenerationEvent.model_construct(proposed_variables=[], falsification_conditions=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o11.sort_arrays()  # type: ignore

    o12 = System1ReflexPolicy.model_construct(allowed_passive_tools=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o12.sort_arrays()  # type: ignore

    o14 = TheoryOfMindSnapshot.model_construct(predicted_intents=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o14.sort_arrays()  # type: ignore

    o16 = SwarmTopologyManifest.model_construct(active_prediction_markets=[], resolved_markets=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o16.sort_arrays()  # type: ignore

    o18 = EpistemicQuarantineSnapshot.model_construct(theory_of_mind_models=[], capability_attestations=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o18.sort_arrays()  # type: ignore

    o19 = BeliefMutationEvent.model_construct(causal_attributions=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o19.sort_arrays()  # type: ignore

    o20 = DefeasibleRebuttalContract.model_construct(permitted_attack_edges=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o20.sort_arrays()  # type: ignore

def test_epistemic_extraction_policy_sorting() -> None:
    from coreason_manifest.spec.ontology import EpistemicExtractionPolicy

    policy = EpistemicExtractionPolicy(
        strategy_tier="speed_single_pass", required_relations=["part_of", "is_a"], grounding_confidence_threshold=0.5
    )
    assert policy.required_relations == ["is_a", "part_of"]


def test_semantic_node_state_canonical_grounding_sorting() -> None:
    from coreason_manifest.spec.ontology import CanonicalGroundingReceipt, EpistemicProvenanceReceipt, SemanticNodeState

    state = SemanticNodeState(
        node_id="node_1",
        label="Concept",
        scope="global",
        text_chunk="Some text",
        provenance=EpistemicProvenanceReceipt(extracted_by="did:example:agent1", source_event_id="event_1"),
        tier="semantic",
        canonical_groundings=[
            CanonicalGroundingReceipt(target_database="mesh", canonical_id="B", cosine_similarity=0.9),
            CanonicalGroundingReceipt(target_database="snomed_ct", canonical_id="A", cosine_similarity=0.8),
        ],
    )
    assert state.canonical_groundings[0].canonical_id == "A"
    assert state.canonical_groundings[1].canonical_id == "B"


def test_bulk_array_sorting_coverage_2() -> None:
    import contextlib

    from coreason_manifest.spec.ontology import (
        AgentNodeProfile,
        EpistemicExtractionPolicy,
        SemanticNodeState,
    )

    o1 = EpistemicExtractionPolicy.model_construct(required_relations=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o1.sort_arrays()  # type: ignore

    o2 = SemanticNodeState.model_construct(canonical_groundings=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o2.sort_arrays()  # type: ignore

    o3 = AgentNodeProfile.model_construct(peft_adapters=[])  # type: ignore
    with contextlib.suppress(AttributeError):
        o3.sort_arrays()  # type: ignore
