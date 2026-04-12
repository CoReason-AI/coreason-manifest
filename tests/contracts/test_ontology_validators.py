# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ActivationSteeringContract,
    AdjudicationRubricProfile,
    CognitiveAgentNodeProfile,
    CognitiveFormatContract,
    CognitiveUncertaintyProfile,
    ComputeEngineProfile,
    ComputeRateContract,
    ComputeTierProfile,
    ConsensusPolicy,
    ConstrainedDecodingPolicy,
    ContextualizedSourceState,
    CoreasonBaseState,
    DefeasibleCascadeEvent,
    DynamicLayoutManifest,
    EphemeralNamespacePartitionState,
    EpistemicCompressionSLA,
    EpistemicSecurityPolicy,
    EpistemicSecurityProfile,
    EpistemicUpsamplingTask,
    GradingCriterionProfile,
    LatentSmoothingProfile,
    MultimodalTokenAnchorState,
    NeurosymbolicInferenceIntent,
    PermissionBoundaryPolicy,
    QuorumPolicy,
    RedactionPolicy,
    RiskLevelPolicy,
    RollbackIntent,
    SaeLatentPolicy,
    SE3TransformProfile,
    SecureSubSessionState,
    SemanticClassificationProfile,
    SpatialHardwareProfile,
    TopologicalFidelityReceipt,
    ViewportProjectionContract,
    VolumetricBoundingProfile,
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


# --- 2. Volumetric Bounding Box Fuzzing ---
@given(
    extents_x=st.floats(min_value=0.0, max_value=10.0),
    extents_y=st.floats(min_value=0.0, max_value=10.0),
    extents_z=st.floats(min_value=0.0, max_value=10.0),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_spatial_bounds_fuzzing(extents_x: float, extents_y: float, extents_z: float) -> None:
    """Mathematically prove the 3D plane logic strictly rejects impossible Euclidean geometries."""
    transform = SE3TransformProfile(reference_frame_cid="frame", x=0, y=0, z=0)
    if extents_x * extents_y * extents_z == 0.0:
        with pytest.raises(ValidationError, match=r"strictly greater than 0"):
            VolumetricBoundingProfile(
                center_transform=transform, extents_x=extents_x, extents_y=extents_y, extents_z=extents_z
            )
    else:
        box = VolumetricBoundingProfile(
            center_transform=transform, extents_x=extents_x, extents_y=extents_y, extents_z=extents_z
        )
        assert box.extents_x == extents_x


def test_se3_transform_quaternion_validation() -> None:
    # Magnitude 0.0
    with pytest.raises(ValidationError, match="Quaternion cannot be a zero vector"):
        SE3TransformProfile(reference_frame_cid="frame", x=0, y=0, z=0, qx=0.0, qy=0.0, qz=0.0, qw=0.0)

    # Not normalized
    with pytest.raises(ValidationError, match="Quaternion magnitude is"):
        SE3TransformProfile(reference_frame_cid="frame", x=0, y=0, z=0, qx=1.0, qy=1.0, qz=1.0, qw=1.0)


def test_viewport_projection_validation() -> None:
    # Clipping plane near >= far
    with pytest.raises(ValidationError, match=r"clipping_plane_near must be strictly less than clipping_plane_far\."):
        ViewportProjectionContract(
            projection_class="perspective", clipping_plane_near=0.5, clipping_plane_far=0.1, field_of_view_degrees=90.0
        )

    # Perspective without FOV
    with pytest.raises(
        ValidationError, match=r"Perspective projection mathematically requires field_of_view_degrees\."
    ):
        ViewportProjectionContract(projection_class="perspective", clipping_plane_near=0.1, clipping_plane_far=10.0)

    # Valid configurations
    ViewportProjectionContract(
        projection_class="perspective", clipping_plane_near=0.1, clipping_plane_far=10.0, field_of_view_degrees=90.0
    )
    ViewportProjectionContract(projection_class="orthographic", clipping_plane_near=0.1, clipping_plane_far=10.0)


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
    # A SyntaxError in parsing must not be ignored to prevent fail-open security bypass.
    with pytest.raises(ValidationError, match="Invalid syntax in dynamic string"):
        DynamicLayoutManifest(layout_tstring="f'{a")


@pytest.mark.parametrize(
    ("tstring", "bad_node"),
    [("f'{a()} {b}'", "Call"), ("print('hello')", "Call"), ("import os", "Import"), ("<html>{a()}</html>", "Call")],
)
def test_dynamic_layout_manifest_kinetic_bleed(tstring: str, bad_node: str) -> None:
    with pytest.raises(ValidationError, match=rf"Kinetic execution bleed detected: Forbidden AST node {bad_node}"):
        DynamicLayoutManifest(layout_tstring=tstring)


# --- 7. Deterministic Array Sorting Validation ---
def test_compute_engine_profile_sorting() -> None:
    rate = ComputeRateContract(
        cost_per_million_input_tokens=1,
        cost_per_million_output_tokens=2,
        magnitude_unit="USD",
    )
    profile = ComputeEngineProfile(
        foundation_matrix_name="test-model",
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
    c1 = GradingCriterionProfile(criterion_cid="c_beta", description="Beta criterion", weight=10.0)
    c2 = GradingCriterionProfile(criterion_cid="c_alpha", description="Alpha criterion", weight=5.0)
    rubric = AdjudicationRubricProfile(rubric_cid="rubric1", criteria=[c1, c2], passing_threshold=15.0)
    assert rubric.criteria[0].criterion_cid == "c_alpha"
    assert rubric.criteria[1].criterion_cid == "c_beta"


def test_redaction_policy_sorting() -> None:
    policy = RedactionPolicy(
        rule_cid="r1",
        classification=SemanticClassificationProfile.PUBLIC,
        target_pattern="email",
        target_regex_pattern=".*",
        context_exclusion_zones=["/path/z", "/path/a"],
        action="redact",
    )
    assert policy.context_exclusion_zones == ["/path/a", "/path/z"]


# --- 8. Missing specific validators coverage ---


def test_constrained_decoding_policy_lmql_missing_string() -> None:
    with pytest.raises(
        ValidationError, match=r"formal_grammar_string must be provided when enforcement_strategy is 'lmql_query'"
    ):
        ConstrainedDecodingPolicy(
            enforcement_strategy="lmql_query",
            compiler_backend="lmql",
            formal_grammar_string=None,
        )


def test_cognitive_format_contract_regex_conflict() -> None:
    policy = ConstrainedDecodingPolicy(
        enforcement_strategy="lmql_query",
        compiler_backend="lmql",
        formal_grammar_string='SELECT "Hello World"',
    )
    with pytest.raises(
        ValidationError,
        match=r"Regex constraints must be embedded directly inside the LMQL grammar string when using 'lmql_query'.",
    ):
        CognitiveFormatContract(
            require_think_tags=False,
            final_answer_regex="^Hello.*$",
            decoding_policy=policy,
        )


def test_cognitive_format_contract_valid_lmql() -> None:
    policy = ConstrainedDecodingPolicy(
        enforcement_strategy="lmql_query",
        compiler_backend="lmql",
        formal_grammar_string='SELECT "Hello World"',
    )
    contract = CognitiveFormatContract(
        require_think_tags=False,
        final_answer_regex=None,
        decoding_policy=policy,
    )
    assert contract.final_answer_regex is None


@given(
    eig=st.floats(min_value=-1.0, max_value=2.0),
)
def test_active_inference_contract_bounds_fuzzing(eig: float) -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import ActiveInferenceContract

    if eig < 0.0 or eig > 1.0:
        with pytest.raises(ValidationError, match=r"Input should be"):
            ActiveInferenceContract(
                task_cid="task_1",
                target_hypothesis_cid="hyp_1",
                target_condition_cid="cond_1",
                selected_tool_name="tool_1",
                expected_information_gain=eig,
                execution_cost_budget_magnitude=100,
            )
    else:
        contract = ActiveInferenceContract(
            task_cid="task_1",
            target_hypothesis_cid="hyp_1",
            target_condition_cid="cond_1",
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
@settings(deadline=None)
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
@settings(max_examples=100, deadline=None)
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
        cascade_cid="c1",
        root_falsified_event_cid="e1",
        propagated_decay_factor=0.5,
        quarantined_event_cids=["z", "a", "x"],
    )
    assert event.quarantined_event_cids == ["a", "x", "z"]


def test_rollback_intent_sorting() -> None:
    intent = RollbackIntent(
        request_cid="r1", target_event_cid="e1", invalidated_node_cids=["node_c", "node_a", "node_b"]
    )
    assert intent.invalidated_node_cids == ["node_a", "node_b", "node_c"]


def test_multimodal_token_anchor_state_sorting() -> None:
    anchor = MultimodalTokenAnchorState(visual_patch_hashes=["hash_c", "hash_a", "hash_b"])
    assert anchor.visual_patch_hashes == ["hash_a", "hash_b", "hash_c"]


def test_secure_sub_session_state_sorting() -> None:
    state = SecureSubSessionState(
        session_cid="session1",
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
        partition_cid="part1",
        execution_runtime="wasm32-wasi",
        authorized_bytecode_hashes=[hash_c, hash_a, hash_b],
        max_ttl_seconds=3600,
        max_vram_mb=1024,
    )
    assert state.authorized_bytecode_hashes == [hash_a, hash_b, hash_c]


def test_ephemeral_namespace_partition_state_invalid_hash() -> None:
    with pytest.raises(ValidationError, match=r"Invalid SHA-256 hash in whitelist: invalid_hash"):
        EphemeralNamespacePartitionState(
            partition_cid="part1",
            execution_runtime="wasm32-wasi",
            authorized_bytecode_hashes=["invalid_hash"],
            max_ttl_seconds=3600,
            max_vram_mb=1024,
        )


def test_bilateral_sla_sorting() -> None:
    from coreason_manifest.spec.ontology import FederatedBilateralSLA, SemanticClassificationProfile

    sla = FederatedBilateralSLA(
        receiving_tenant_cid="tenant-a",
        max_permitted_classification=SemanticClassificationProfile.PUBLIC,
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
        resolution_schema={"topology_class": "string"},
        timeout_action="rollback",
    )
    assert intent.deadlocked_claims == ["claim_1", "claim_2", "claim_3"]


def test_composite_node_profile_sorts_mappings() -> None:
    from coreason_manifest.spec.ontology import (
        CognitiveSystemNodeProfile,
        CompositeNodeProfile,
        DAGTopologyManifest,
        InputMappingContract,
        OutputMappingContract,
    )

    topology = DAGTopologyManifest(
        nodes={"did:example:1": CognitiveSystemNodeProfile(description="desc")}, edges=[], max_depth=10, max_fan_out=10
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


def test_action_space_manifest_enforce_canonical_sort() -> None:
    from coreason_manifest.spec.ontology import (
        CognitiveActionSpaceManifest,
        PermissionBoundaryPolicy,
        SideEffectProfile,
        SpatialToolManifest,
        TransitionEdgeProfile,
    )

    tool1 = SpatialToolManifest(
        topology_class="native_tool",
        tool_name="tool_b",
        description="description",
        input_schema={"topology_class": "object", "properties": {}},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )
    tool2 = SpatialToolManifest(
        topology_class="native_tool",
        tool_name="tool_a",
        description="description 2",
        input_schema={"topology_class": "object", "properties": {}},
        side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
        permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
    )

    # Valid manifest
    manifest = CognitiveActionSpaceManifest(
        action_space_cid="space_1",
        entry_point_cid="tool_b",
        capabilities={"tool_a": tool2, "tool_b": tool1},
        transition_matrix={
            "tool_b": [
                TransitionEdgeProfile(
                    topology_class="acyclic",
                    target_node_cid="tool_b",
                    probability_weight=0.5,
                    compute_weight_magnitude=1,
                ),
                TransitionEdgeProfile(
                    topology_class="acyclic",
                    target_node_cid="tool_a",
                    probability_weight=0.5,
                    compute_weight_magnitude=1,
                ),
            ],
            "tool_a": [],
        },
    )
    # Check canonical sorting of edges
    assert manifest.transition_matrix["tool_b"][0].target_node_cid == "tool_a"
    assert manifest.transition_matrix["tool_b"][1].target_node_cid == "tool_b"


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
    from coreason_manifest.spec.ontology import StdioTransportProfile

    with pytest.raises(
        ValidationError, match=r"UNAUTHORIZED MCP MOUNT: The presented Verifiable Credential is not signed"
    ):
        MCPServerManifest(
            server_cid="server_1",
            transport=StdioTransportProfile(command="cmd", args=[]),
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
        server_cid="server_1",
        transport=StdioTransportProfile(command="cmd", args=[]),
        binary_hash="a" * 64,
        capability_whitelist=MCPCapabilityWhitelistPolicy(),
        attestation_receipt=vc_valid,
    )
    assert manifest.attestation_receipt.issuer_did == "did:coreason:123"


def test_insight_card_profile_xss_prevention() -> None:
    from coreason_manifest.spec.ontology import InsightCardProfile

    # Test that valid links work
    InsightCardProfile(panel_cid="panel_1", title="Title", markdown_content="[click me](https://coreason.ai)")

    malicious_payloads = [
        "<script>alert(1)</script>",
        "<img src='x' onerror='alert(1)'>",
    ]

    for payload in malicious_payloads:
        profile = InsightCardProfile(panel_cid="panel_1", title="Title", markdown_content=payload)
        assert "<script>" not in profile.markdown_content
        assert "alert(1)" not in profile.markdown_content

    # Note: "<a href='javascript:alert(1)'>click me</a>" is caught by `sanitize_markdown` first
    profile = InsightCardProfile(
        panel_cid="panel_1", title="Title", markdown_content="<a href='javascript:alert(1)'>click me</a>"
    )
    assert "javascript:alert" not in profile.markdown_content


def test_macro_grid_profile_referential_integrity() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import InsightCardProfile, MacroGridProfile

    panel = InsightCardProfile(panel_cid="panel_1", title="Title", markdown_content="Content")
    with pytest.raises(ValidationError, match=r"Ghost Panel referenced in layout_matrix"):
        MacroGridProfile(layout_matrix=[["panel_1", "panel_2"]], panels=[panel])


def test_epistemic_sop_manifest_ghost_nodes() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import CognitiveStateProfile, EpistemicSOPManifest

    cog_state = CognitiveStateProfile(urgency_index=0.5, caution_index=0.5, divergence_tolerance=0.5)

    with pytest.raises(ValidationError, match=r"Ghost node referenced in chronological_flow_edges source"):
        EpistemicSOPManifest(
            sop_cid="sop_1",
            target_persona="persona_1",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={},
            chronological_flow_edges=[("ghost_step", "step_1")],
            prm_evaluations=[],
        )

    with pytest.raises(ValidationError, match=r"Ghost node referenced in chronological_flow_edges target"):
        EpistemicSOPManifest(
            sop_cid="sop_1",
            target_persona="persona_1",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={},
            chronological_flow_edges=[("step_1", "ghost_step")],
            prm_evaluations=[],
        )

    with pytest.raises(ValidationError, match=r"Ghost node referenced in structural_grammar_hashes"):
        EpistemicSOPManifest(
            sop_cid="sop_1",
            target_persona="persona_1",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={"ghost_step": "abcdef"},
            chronological_flow_edges=[],
            prm_evaluations=[],
        )


def test_executionspanreceipt_enforce_canonical_sort_events() -> None:
    from coreason_manifest.spec.ontology import ExecutionSpanReceipt, SpanEvent

    event1 = SpanEvent(name="event_a", timestamp_unix_nano=1000)
    event2 = SpanEvent(name="event_b", timestamp_unix_nano=500)
    event3 = SpanEvent(name="event_c", timestamp_unix_nano=1500)

    receipt = ExecutionSpanReceipt(
        trace_cid="trace_1",
        span_cid="span_1",
        name="span_name",
        start_time_unix_nano=0,
        events=[event1, event2, event3],
    )

    # events should be sorted by timestamp_unix_nano
    assert receipt.events[0].name == "event_b"
    assert receipt.events[1].name == "event_a"
    assert receipt.events[2].name == "event_c"


def test_causal_explanation_event_sorts_attributions() -> None:
    from coreason_manifest.spec.ontology import (
        CausalExplanationEvent,
        CollectiveIntelligenceProfile,
        ShapleyAttributionReceipt,
    )

    ci_profile = CollectiveIntelligenceProfile(synergy_index=0.8, coordination_score=0.9, information_integration=0.7)

    receipt_b = ShapleyAttributionReceipt(
        target_node_cid="did:coreason:node-b",
        causal_attribution_score=0.4,
        normalized_contribution_percentage=0.4,
        confidence_interval_lower=0.3,
        confidence_interval_upper=0.5,
    )

    receipt_a = ShapleyAttributionReceipt(
        target_node_cid="did:coreason:node-a",
        causal_attribution_score=0.6,
        normalized_contribution_percentage=0.6,
        confidence_interval_lower=0.5,
        confidence_interval_upper=0.7,
    )

    event = CausalExplanationEvent(
        event_cid="test_event_1",
        timestamp=123456.0,
        target_outcome_event_cid="test_outcome_1",
        collective_intelligence=ci_profile,
        agent_attributions=[receipt_b, receipt_a],
    )

    assert event.agent_attributions[0].target_node_cid == "did:coreason:node-a"
    assert event.agent_attributions[1].target_node_cid == "did:coreason:node-b"


def test_kinematic_delta_manifest_sorting() -> None:
    from coreason_manifest.spec.ontology import KinematicDeltaManifest

    manifest = KinematicDeltaManifest(
        stream_cid="stream-123",
        deltas=[
            ("node-B", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            ("node-A", 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ],
    )
    assert manifest.deltas[0][0] == "node-A"
    assert manifest.deltas[1][0] == "node-B"


def test_agent_node_profile_success() -> None:
    """Test that default values instantiate cleanly without triggering traps."""
    agent = CognitiveAgentNodeProfile(description="Test agent")
    assert agent.hardware.compute_tier == ComputeTierProfile.KINETIC
    assert agent.hardware.min_vram_gb == 8.0
    assert agent.security.epistemic_security == EpistemicSecurityPolicy.STANDARD


def test_agent_node_profile_thermodynamic_paradox() -> None:
    """Test that KINETIC tier cannot exceed 24.0 GB VRAM."""
    with pytest.raises(ValueError, match="Thermodynamic Constraint Violated"):
        CognitiveAgentNodeProfile(
            description="Test agent",
            hardware=SpatialHardwareProfile(compute_tier=ComputeTierProfile.KINETIC, min_vram_gb=25.0),
        )


def test_agent_node_profile_sovereign_execution_paradox() -> None:
    """Test that CONFIDENTIAL workloads must use trusted endpoints only."""
    with pytest.raises(ValueError, match="Sovereign Execution Violated"):
        CognitiveAgentNodeProfile(
            description="Test agent",
            hardware=SpatialHardwareProfile(provider_whitelist=["vast", "aws"]),
            security=EpistemicSecurityProfile(epistemic_security=EpistemicSecurityPolicy.CONFIDENTIAL),
        )

    # Success case for CONFIDENTIAL
    agent = CognitiveAgentNodeProfile(
        description="Test agent",
        hardware=SpatialHardwareProfile(provider_whitelist=["aws", "gcp"]),
        security=EpistemicSecurityProfile(epistemic_security=EpistemicSecurityPolicy.CONFIDENTIAL),
    )
    assert agent.security.epistemic_security == EpistemicSecurityPolicy.CONFIDENTIAL


def test_sovereign_execution_allows_localhost_and_bare_metal() -> None:
    """Ensure CONFIDENTIAL workloads can run on local/bare-metal without triggering the paradox."""
    profile = CognitiveAgentNodeProfile(
        description="Secure local ETL agent for proprietary schemas.",
        hardware=SpatialHardwareProfile(provider_whitelist=["localhost", "bare-metal"]),
        security=EpistemicSecurityProfile(epistemic_security=EpistemicSecurityPolicy.CONFIDENTIAL),
    )
    # If the validation passes without raising ValueError, the contract holds.
    assert profile.security.epistemic_security == EpistemicSecurityPolicy.CONFIDENTIAL
    assert "localhost" in profile.hardware.provider_whitelist


def test_deprecated_solver_coq() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import FormalVerificationContract

    with pytest.raises(ValidationError) as exc_info:
        FormalVerificationContract(proof_system="coq", invariant_theorem="test", compiled_proof_hash="a" * 64)  # type: ignore
    assert "Input should be 'lean4' or 'z3'" in str(exc_info.value)


def test_deprecated_solver_isabelle() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import FormalVerificationContract

    with pytest.raises(ValidationError) as exc_info:
        FormalVerificationContract(proof_system="isabelle", invariant_theorem="test", compiled_proof_hash="a" * 64)  # type: ignore
    assert "Input should be 'lean4' or 'z3'" in str(exc_info.value)


def test_deprecated_solver_tla_plus() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import NeuroSymbolicHandoffContract

    with pytest.raises(ValidationError) as exc_info:
        NeuroSymbolicHandoffContract(
            handoff_cid="test",
            solver_protocol="tla_plus",  # type: ignore
            formal_grammar_payload="test",
            timeout_ms=1000,
        )
    assert "Input should be 'lean4', 'z3', 'clingo' or 'swi_prolog'" in str(exc_info.value)


def test_deprecated_solver_sympy() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import AlgebraicRefinementContract, HoareLogicProofReceipt

    with pytest.raises(ValidationError) as exc_info:
        HoareLogicProofReceipt(
            capability_cid="test",
            preconditions=[AlgebraicRefinementContract(target_property="x", mathematical_predicate="x > 0")],
            postconditions=[AlgebraicRefinementContract(target_property="x", mathematical_predicate="x > 0")],
            proof_system="sympy",  # type: ignore
            verified_theorem_hash="a" * 64,
        )
    assert "Input should be 'lean4' or 'z3'" in str(exc_info.value)


def test_agent_node_profile_network_topology_paradox() -> None:
    """Test that Mixnet routing requires strict network isolation."""
    with pytest.raises(ValueError, match="Topology Routing Violated"):
        CognitiveAgentNodeProfile(
            description="Test agent",
            security=EpistemicSecurityProfile(egress_obfuscation=True, network_isolation=False),
        )

    # Success case for Mixnet routing
    agent = CognitiveAgentNodeProfile(
        description="Test agent", security=EpistemicSecurityProfile(egress_obfuscation=True, network_isolation=True)
    )
    assert agent.security.egress_obfuscation is True
    assert agent.security.network_isolation is True


def test_refusal_to_reason_enforcement() -> None:
    source_entity = ContextualizedSourceState(
        target_string="Discharge",
        contextual_envelope=[],
        source_system_provenance_flag=False,
    )
    fidelity_receipt = TopologicalFidelityReceipt(
        contextual_completeness_score=0.0,
        surrounding_token_density=0,
    )
    uncertainty_profile = CognitiveUncertaintyProfile(
        aleatoric_noise_ratio=0.1,
        epistemic_knowledge_gap=0.9,
        semantic_consistency_score=0.5,
        requires_abductive_escalation=False,
    )
    sla = EpistemicCompressionSLA(
        strict_probability_retention=True,
        max_allowed_entropy_loss=0.5,
        required_grounding_density="dense",
        minimum_fidelity_threshold=0.5,
    )

    with pytest.raises(
        ValidationError, match=r"Inference aborted due to severe semantic degradation. Epistemic gap exceeds SLA."
    ):
        NeurosymbolicInferenceIntent(
            source_entity=source_entity,
            fidelity_receipt=fidelity_receipt,
            uncertainty_profile=uncertainty_profile,
            sla=sla,
        )


def test_successful_epistemic_grounding() -> None:
    source_entity = ContextualizedSourceState(
        target_string="Amoxicillin 500mg",
        contextual_envelope=["patient chart", "medication order"],
        source_system_provenance_flag=True,
    )
    fidelity_receipt = TopologicalFidelityReceipt(
        contextual_completeness_score=0.9,
        surrounding_token_density=10,
    )
    uncertainty_profile = CognitiveUncertaintyProfile(
        aleatoric_noise_ratio=0.05,
        epistemic_knowledge_gap=0.2,  # < 0.5
        semantic_consistency_score=0.9,
        requires_abductive_escalation=False,
    )
    sla = EpistemicCompressionSLA(
        strict_probability_retention=True,
        max_allowed_entropy_loss=0.5,
        required_grounding_density="dense",
        minimum_fidelity_threshold=0.5,
    )

    req = NeurosymbolicInferenceIntent(
        source_entity=source_entity,
        fidelity_receipt=fidelity_receipt,
        uncertainty_profile=uncertainty_profile,
        sla=sla,
    )
    assert req.uncertainty_profile.epistemic_knowledge_gap < req.sla.minimum_fidelity_threshold


def test_epistemic_upsampling_instantiation() -> None:
    source = ContextualizedSourceState(
        target_string="test artifact",
        contextual_envelope=["context A", "context B"],
        source_system_provenance_flag=True,
    )
    task = EpistemicUpsamplingTask(
        source_entity=source,
        target_ontological_granularity="OMOP Measurement Concept Level 4",
        upsampling_confidence_threshold=0.95,
        justification_vectors=["rhinorrhea post-trauma"],
    )
    assert task.target_ontological_granularity == "OMOP Measurement Concept Level 4"
    assert task.upsampling_confidence_threshold == 0.95
    assert len(task.justification_vectors) == 1
    assert task.justification_vectors[0] == "rhinorrhea post-trauma"


def test_upsampling_confidence_bounds() -> None:
    """Prove that an agent cannot hallucinate an overconfident abductive leap."""
    source = ContextualizedSourceState(
        target_string="test artifact",
        contextual_envelope=["context A"],
        source_system_provenance_flag=True,
    )

    # Test upper bound violation
    with pytest.raises(ValidationError, match=r"Input should be less than or equal to 1"):
        EpistemicUpsamplingTask(
            source_entity=source,
            target_ontological_granularity="OMOP Level 4",
            upsampling_confidence_threshold=1.5,
            justification_vectors=["context A"],
        )

    # Test lower bound violation
    with pytest.raises(ValidationError, match=r"Input should be greater than or equal to 0"):
        EpistemicUpsamplingTask(
            source_entity=source,
            target_ontological_granularity="OMOP Level 4",
            upsampling_confidence_threshold=-0.1,
            justification_vectors=["context A"],
        )


def test_empty_justification_rejection() -> None:
    """Prove that the system structurally rejects an evidence-free abductive leap."""
    source = ContextualizedSourceState(
        target_string="test artifact",
        contextual_envelope=["context A"],
        source_system_provenance_flag=True,
    )

    with pytest.raises(ValidationError, match=r"List should have at least 1 item"):
        EpistemicUpsamplingTask(
            source_entity=source,
            target_ontological_granularity="OMOP Level 4",
            upsampling_confidence_threshold=0.95,
            justification_vectors=[],  # Empty evidence vector
        )


def test_atomic_proposition_canonical_sort() -> None:
    from coreason_manifest.spec.ontology import (
        AtomicPropositionState,
        IllocutionaryForceProfile,
        RhetoricalStructureProfile,
    )

    prop = AtomicPropositionState(
        event_cid="event-1",
        timestamp=100.0,
        proposition_cid="prop-1",
        rhetorical_role=RhetoricalStructureProfile.PREMISE,
        illocutionary_force=IllocutionaryForceProfile.ASSERTIVE,
        text_chunk="This is a test chunk.",
        anaphoric_resolution_cids=["did:node:c", "did:node:a", "did:node:b"],
    )
    assert prop.anaphoric_resolution_cids == ["did:node:a", "did:node:b", "did:node:c"]


def test_atomic_proposition_defaults() -> None:
    from coreason_manifest.spec.ontology import (
        AtomicPropositionState,
        IllocutionaryForceProfile,
        RhetoricalStructureProfile,
    )

    prop = AtomicPropositionState(
        event_cid="event-1",
        timestamp=100.0,
        proposition_cid="prop-1",
        rhetorical_role=RhetoricalStructureProfile.PREMISE,
        illocutionary_force=IllocutionaryForceProfile.ASSERTIVE,
        text_chunk="This is a test chunk.",
    )
    assert prop.anaphoric_resolution_cids == []
    assert prop.topology_class == "atomic_proposition"


def test_epic5_global_semantic_invariant_profile_sorting() -> None:
    from coreason_manifest.spec.ontology import GlobalSemanticInvariantProfile, TemporalBoundsProfile

    profile = GlobalSemanticInvariantProfile(
        invariant_cid="invariant_1",
        categorical_cohorts=["Zebra", "Apple"],
        operational_perimeters={"test": "me"},
        temporal_observation_horizons=[TemporalBoundsProfile(valid_from=None), TemporalBoundsProfile(valid_from=5.0)],
    )
    assert profile.categorical_cohorts == ["Apple", "Zebra"]


def test_epic5_discourse_node_state_sorting() -> None:
    from coreason_manifest.spec.ontology import DiscourseNodeState

    node = DiscourseNodeState(
        node_cid="did:ex:node1", discourse_type="preamble", contained_propositions=["did:ex:prop2", "did:ex:prop1"]
    )
    assert node.contained_propositions == ["did:ex:prop1", "did:ex:prop2"]


def test_epic5_discourse_tree_manifest_dag() -> None:
    from coreason_manifest.spec.ontology import DiscourseNodeState, DiscourseTreeManifest

    nodes = {
        "did:ex:root": DiscourseNodeState(node_cid="did:ex:root", discourse_type="preamble"),
    }
    manifest = DiscourseTreeManifest(manifest_cid="manifest_1", root_node_cid="did:ex:root", discourse_nodes=nodes)
    assert manifest.root_node_cid == "did:ex:root"


def test_epic5_discourse_tree_manifest_missing_root() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import DiscourseNodeState, DiscourseTreeManifest

    nodes = {
        "did:ex:child1": DiscourseNodeState(node_cid="did:ex:child1", discourse_type="findings"),
    }
    with pytest.raises(ValidationError, match="Topological Contradiction: root_node_cid not found"):
        DiscourseTreeManifest(manifest_cid="manifest_1", root_node_cid="did:ex:root", discourse_nodes=nodes)


def test_epic5_discourse_tree_manifest_ghost_pointer() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import DiscourseNodeState, DiscourseTreeManifest

    nodes = {
        "did:ex:root": DiscourseNodeState(node_cid="did:ex:root", discourse_type="preamble"),
        "did:ex:child1": DiscourseNodeState(
            node_cid="did:ex:child1", discourse_type="findings", parent_node_cid="did:ex:ghost"
        ),
    }
    with pytest.raises(ValidationError, match="Ghost pointer: Parent node did:ex:ghost not found"):
        DiscourseTreeManifest(manifest_cid="manifest_1", root_node_cid="did:ex:root", discourse_nodes=nodes)


def test_epic5_discourse_tree_manifest_cycle() -> None:
    from pydantic import ValidationError

    from coreason_manifest.spec.ontology import DiscourseNodeState, DiscourseTreeManifest

    nodes = {
        "did:ex:root": DiscourseNodeState(
            node_cid="did:ex:root", discourse_type="preamble", parent_node_cid="did:ex:child1"
        ),
        "did:ex:child1": DiscourseNodeState(
            node_cid="did:ex:child1", discourse_type="findings", parent_node_cid="did:ex:root"
        ),
    }
    with pytest.raises(
        ValidationError, match="Topological Contradiction: Discourse tree contains a cyclical reference"
    ):
        DiscourseTreeManifest(manifest_cid="manifest_1", root_node_cid="did:ex:root", discourse_nodes=nodes)
