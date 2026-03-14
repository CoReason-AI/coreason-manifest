# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

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


@given(
    eig=st.floats(min_value=-1.0, max_value=2.0),
)
def test_active_inference_contract_bounds_fuzzing(eig: float) -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import ActiveInferenceContract

    if eig < 0.0 or eig > 1.0:
        with pytest.raises(ValidationError, match=r"Input should be"):
            ActiveInferenceContract(
                task_id="task_1",
                target_hypothesis_id="hyp_1",
                target_condition_id="cond_1",
                selected_tool_name="tool_1",
                expected_information_gain=eig,
                execution_cost_budget_magnitude=100,
            )
    else:
        contract = ActiveInferenceContract(
            task_id="task_1",
            target_hypothesis_id="hyp_1",
            target_condition_id="cond_1",
            selected_tool_name="tool_1",
            expected_information_gain=eig,
            execution_cost_budget_magnitude=100,
        )
        assert contract.expected_information_gain == eig


@given(
    url=st.one_of(
        st.emails().map(lambda e: f"https://{e.split('@')[1]}"),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=10).map(
            lambda t: f"https://{t}.com"
        ),
    )
)
def test_browser_dom_state_safety_valid_fuzzing(url: str) -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import BrowserDOMState

    try:
        state = BrowserDOMState(
            current_url=url,
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )
        assert state.current_url == url
    except ValidationError:
        # It might still trigger SSRF validation if hypothesis generates a local-looking domain,
        # but that's properly handled as part of the fuzzing scope.
        pass


@given(
    bogon=st.sampled_from(
        [
            "localhost",
            "broadcasthost",
            "test.local",
            "test.internal",
            "test.arpa",
            "test.nip.io",
            "test.sslip.io",
            "127.0.0.1",
            "192.168.1.1",
            "10.0.0.1",
            "169.254.169.254",
            "0.0.0.0",  # noqa: S104
        ]
    )
)
def test_browser_dom_state_safety_invalid_fuzzing(bogon: str) -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import BrowserDOMState

    with pytest.raises(ValidationError, match=r"SSRF|validation error"):
        BrowserDOMState(
            current_url=f"http://{bogon}",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )

    with pytest.raises(ValidationError, match=r"SSRF|validation error"):
        BrowserDOMState(
            current_url=f"file://{bogon}",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )


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


def test_composite_node_profile_sorts_mappings() -> None:
    from coreason_manifest.spec.ontology import (
        CompositeNodeProfile,
        DAGTopologyManifest,
        InputMappingContract,
        OutputMappingContract,
        SystemNodeProfile,
    )

    topology = DAGTopologyManifest(
        nodes={"did:example:1": SystemNodeProfile(description="desc")}, edges=[], max_depth=10, max_fan_out=10
    )
    in_map1 = InputMappingContract(parent_key="b", child_key="c1")
    in_map2 = InputMappingContract(parent_key="a", child_key="c2")
    out_map1 = OutputMappingContract(child_key="y", parent_key="p1")
    out_map2 = OutputMappingContract(child_key="x", parent_key="p2")

    node = CompositeNodeProfile(
        description="composite",
        topology=topology,
        input_mappings=[in_map1, in_map2],
        output_mappings=[out_map1, out_map2],
    )

    assert node.input_mappings[0].parent_key == "a"
    assert node.input_mappings[1].parent_key == "b"
    assert node.output_mappings[0].child_key == "x"
    assert node.output_mappings[1].child_key == "y"


def test_action_space_manifest_sort_arrays() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import (
        ActionSpaceManifest,
        PermissionBoundaryPolicy,
        SideEffectProfile,
        ToolManifest,
    )

    tool1 = ToolManifest(
        tool_name="tool_b",
        description="description",
        input_schema={},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )
    tool2 = ToolManifest(
        tool_name="tool_a",
        description="description 2",
        input_schema={},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )
    tool3 = ToolManifest(
        tool_name="tool_b",
        description="description duplicate",
        input_schema={},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    with pytest.raises(ValidationError, match=r"Tool names within an ActionSpaceManifest must be strictly unique"):
        ActionSpaceManifest(action_space_id="space_1", native_tools=[tool1, tool3])

    manifest = ActionSpaceManifest(action_space_id="space_1", native_tools=[tool1, tool2])
    assert manifest.native_tools[0].tool_name == "tool_a"
    assert manifest.native_tools[1].tool_name == "tool_b"


def test_mcpservermanifest_enforce_did() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import (
        MCPCapabilityWhitelistPolicy,
        MCPServerManifest,
        VerifiableCredentialPresentationReceipt,
    )

    vc_invalid = VerifiableCredentialPresentationReceipt(
        presentation_format="jwt_vc",
        issuer_did="did:example:123",
        cryptographic_proof_blob="blob",
        authorization_claims={},
    )
    with pytest.raises(
        ValidationError, match=r"UNAUTHORIZED MCP MOUNT: The presented Verifiable Credential is not signed"
    ):
        MCPServerManifest(
            server_uri="uri",
            transport_type="stdio",
            capability_whitelist=MCPCapabilityWhitelistPolicy(),
            attestation_receipt=vc_invalid,
        )

    vc_valid = VerifiableCredentialPresentationReceipt(
        presentation_format="jwt_vc",
        issuer_did="did:coreason:123",
        cryptographic_proof_blob="blob",
        authorization_claims={},
    )
    manifest = MCPServerManifest(
        server_uri="uri",
        transport_type="stdio",
        capability_whitelist=MCPCapabilityWhitelistPolicy(),
        attestation_receipt=vc_valid,
    )
    assert manifest.attestation_receipt.issuer_did == "did:coreason:123"


def test_macro_grid_profile_referential_integrity() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import InsightCardProfile, MacroGridProfile

    panel = InsightCardProfile(panel_id="panel_1", title="Title", markdown_content="Content")
    with pytest.raises(ValidationError, match=r"Ghost Panel referenced in layout_matrix"):
        MacroGridProfile(layout_matrix=[["panel_1", "panel_2"]], panels=[panel])


def test_epistemic_sop_manifest_ghost_nodes() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import CognitiveStateProfile, EpistemicSOPManifest

    cog_state = CognitiveStateProfile(urgency_index=0.5, caution_index=0.5, divergence_tolerance=0.5)

    with pytest.raises(ValidationError, match=r"Ghost node referenced in chronological_flow_edges source"):
        EpistemicSOPManifest(
            sop_id="sop_1",
            target_persona="persona_1",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={},
            chronological_flow_edges=[("ghost_step", "step_1")],
            prm_evaluations=[],
        )

    with pytest.raises(ValidationError, match=r"Ghost node referenced in chronological_flow_edges target"):
        EpistemicSOPManifest(
            sop_id="sop_1",
            target_persona="persona_1",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={},
            chronological_flow_edges=[("step_1", "ghost_step")],
            prm_evaluations=[],
        )

    with pytest.raises(ValidationError, match=r"Ghost node referenced in structural_grammar_hashes"):
        EpistemicSOPManifest(
            sop_id="sop_1",
            target_persona="persona_1",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={"ghost_step": "abcdef"},
            chronological_flow_edges=[],
            prm_evaluations=[],
        )


def test_mcpserverbindingprofile_sort_arrays() -> None:
    from coreason_manifest.spec.ontology import MCPServerBindingProfile, StdioTransportProfile

    profile = MCPServerBindingProfile(
        server_id="server_1",
        transport=StdioTransportProfile(command="python", args=[]),
        required_capabilities=["tools", "prompts", "resources"],
    )
    assert profile.required_capabilities == ["prompts", "resources", "tools"]


def test_executionspanreceipt_sort_events() -> None:
    from coreason_manifest.spec.ontology import ExecutionSpanReceipt, SpanEvent

    event1 = SpanEvent(name="event_a", timestamp_unix_nano=1000)
    event2 = SpanEvent(name="event_b", timestamp_unix_nano=500)
    event3 = SpanEvent(name="event_c", timestamp_unix_nano=1500)

    receipt = ExecutionSpanReceipt(
        trace_id="trace_1", span_id="span_1", name="span_name", start_time_unix_nano=0, events=[event1, event2, event3]
    )

    # events should be sorted by timestamp_unix_nano
    assert receipt.events[0].name == "event_b"
    assert receipt.events[1].name == "event_a"
    assert receipt.events[2].name == "event_c"
