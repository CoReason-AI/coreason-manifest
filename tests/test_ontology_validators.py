import pytest
from coreason_manifest.spec.ontology import (
    ActionSpaceManifest,
    ToolManifest,
    MCPServerManifest,
    EphemeralNamespacePartitionState,
    SideEffectProfile,
    PermissionBoundaryPolicy,
    VerifiableCredentialPresentationReceipt,
    NodeIdentifierState,
    MacroGridProfile,
    InsightCardProfile,
    EpistemicSOPManifest,
    ProfileIdentifierState,
    CognitiveStateProfile,
    CompositeNodeProfile,
    SystemNodeProfile,
    DAGTopologyManifest,
    InputMappingContract,
    OutputMappingContract,
    MCPCapabilityWhitelistPolicy,
)

def test_action_space_manifest_unique_tool_names():
    tool1 = ToolManifest(
        tool_name="tool_a",
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
    with pytest.raises(ValueError, match="Tool names within an ActionSpaceManifest must be strictly unique"):
        ActionSpaceManifest(
            action_space_id="space_1",
            native_tools=[tool1, tool2]
        )

def test_macro_grid_profile_referential_integrity():
    panel = InsightCardProfile(panel_id="panel_1", title="Title", markdown_content="Content")
    with pytest.raises(ValueError, match="Ghost Panel referenced in layout_matrix"):
        MacroGridProfile(
            layout_matrix=[["panel_1", "panel_2"]],
            panels=[panel]
        )

def test_epistemic_sop_manifest_ghost_nodes():
    cog_state = CognitiveStateProfile(
        urgency_index=0.5,
        caution_index=0.5,
        divergence_tolerance=0.5
    )
    with pytest.raises(ValueError, match="Ghost node referenced in chronological_flow_edges source"):
        EpistemicSOPManifest(
            sop_id="sop_1",
            target_persona="persona_1",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={},
            chronological_flow_edges=[("ghost_step", "step_1")],
            prm_evaluations=[]
        )

def test_epistemic_sop_manifest_ghost_nodes_target():
    cog_state = CognitiveStateProfile(
        urgency_index=0.5,
        caution_index=0.5,
        divergence_tolerance=0.5
    )
    with pytest.raises(ValueError, match="Ghost node referenced in chronological_flow_edges target"):
        EpistemicSOPManifest(
            sop_id="sop_1",
            target_persona="persona_1",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={},
            chronological_flow_edges=[("step_1", "ghost_step")],
            prm_evaluations=[]
        )

def test_epistemic_sop_manifest_ghost_nodes_structural_hash():
    cog_state = CognitiveStateProfile(
        urgency_index=0.5,
        caution_index=0.5,
        divergence_tolerance=0.5
    )
    with pytest.raises(ValueError, match="Ghost node referenced in structural_grammar_hashes"):
        EpistemicSOPManifest(
            sop_id="sop_1",
            target_persona="persona_1",
            cognitive_steps={"step_1": cog_state},
            structural_grammar_hashes={"ghost_step": "abcdef"},
            chronological_flow_edges=[],
            prm_evaluations=[]
        )

def test_composite_node_profile_sorts_mappings():
    topology = DAGTopologyManifest(
        nodes={"did:example:1": SystemNodeProfile(description="desc")},
        edges=[],
        max_depth=10,
        max_fan_out=10
    )
    in_map1 = InputMappingContract(parent_key="b", child_key="c1")
    in_map2 = InputMappingContract(parent_key="a", child_key="c2")
    out_map1 = OutputMappingContract(child_key="y", parent_key="p1")
    out_map2 = OutputMappingContract(child_key="x", parent_key="p2")

    node = CompositeNodeProfile(
        description="composite",
        topology=topology,
        input_mappings=[in_map1, in_map2],
        output_mappings=[out_map1, out_map2]
    )

    assert node.input_mappings[0].parent_key == "a"
    assert node.input_mappings[1].parent_key == "b"
    assert node.output_mappings[0].child_key == "x"
    assert node.output_mappings[1].child_key == "y"

def test_action_space_manifest_sort_arrays():
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
    manifest = ActionSpaceManifest(
        action_space_id="space_1",
        native_tools=[tool1, tool2]
    )
    assert manifest.native_tools[0].tool_name == "tool_a"
    assert manifest.native_tools[1].tool_name == "tool_b"

def test_mcpservermanifest_enforce_did():
    vc = VerifiableCredentialPresentationReceipt(
        presentation_format="jwt_vc",
        issuer_did="did:example:123",
        cryptographic_proof_blob="blob",
        authorization_claims={}
    )
    with pytest.raises(ValueError, match="UNAUTHORIZED MCP MOUNT: The presented Verifiable Credential is not signed by a valid"):
        MCPServerManifest(
            server_uri="uri",
            transport_type="stdio",
            capability_whitelist=MCPCapabilityWhitelistPolicy(),
            attestation_receipt=vc
        )

def test_mcpservermanifest_enforce_did_valid():
    vc = VerifiableCredentialPresentationReceipt(
        presentation_format="jwt_vc",
        issuer_did="did:coreason:123",
        cryptographic_proof_blob="blob",
        authorization_claims={}
    )
    manifest = MCPServerManifest(
        server_uri="uri",
        transport_type="stdio",
        capability_whitelist=MCPCapabilityWhitelistPolicy(),
        attestation_receipt=vc
    )
    assert manifest.attestation_receipt.issuer_did == "did:coreason:123"

def test_browser_dom_state_safety_valid():
    from coreason_manifest.spec.ontology import BrowserDOMState

    state = BrowserDOMState(
        current_url="https://example.com",
        viewport_size=(800, 600),
        dom_hash="a"*64,
        accessibility_tree_hash="b"*64
    )
    assert state.current_url == "https://example.com"

    with pytest.raises(ValueError, match="SSRF topological violation detected"):
        BrowserDOMState(
            current_url="file:///etc/passwd",
            viewport_size=(800, 600),
            dom_hash="a"*64,
            accessibility_tree_hash="b"*64
        )

    with pytest.raises(ValueError, match="SSRF topological violation detected"):
        BrowserDOMState(
            current_url="http://localhost:8080",
            viewport_size=(800, 600),
            dom_hash="a"*64,
            accessibility_tree_hash="b"*64
        )

def test_mcpserverbindingprofile_sort_arrays():
    from coreason_manifest.spec.ontology import MCPServerBindingProfile, StdioTransportProfile

    profile = MCPServerBindingProfile(
        server_id="server_1",
        transport=StdioTransportProfile(command="python", args=[]),
        required_capabilities=["tools", "prompts", "resources"]
    )
    assert profile.required_capabilities == ["prompts", "resources", "tools"]

def test_active_inference_contract_bounds():
    from coreason_manifest.spec.ontology import ActiveInferenceContract

    contract = ActiveInferenceContract(
        task_id="task_1",
        target_hypothesis_id="hyp_1",
        target_condition_id="cond_1",
        selected_tool_name="tool_1",
        expected_information_gain=0.5,
        execution_cost_budget_magnitude=100
    )
    assert contract.expected_information_gain == 0.5

    with pytest.raises(ValueError):
        ActiveInferenceContract(
            task_id="task_1",
            target_hypothesis_id="hyp_1",
            target_condition_id="cond_1",
            selected_tool_name="tool_1",
            expected_information_gain=1.5, # Out of bounds
            execution_cost_budget_magnitude=100
        )

def test_ephemeral_namespace_partition_state():
    from coreason_manifest.spec.ontology import EphemeralNamespacePartitionState
    with pytest.raises(ValueError):
        EphemeralNamespacePartitionState(
            partition_id="part1",
            execution_runtime="wasm32-wasi",
            authorized_bytecode_hashes=["invalid_hash"],
            max_ttl_seconds=10,
            max_vram_mb=100
        )

    state = EphemeralNamespacePartitionState(
        partition_id="part1",
        execution_runtime="wasm32-wasi",
        authorized_bytecode_hashes=["a"*64, "b"*64],
        max_ttl_seconds=10,
        max_vram_mb=100
    )
    assert state.authorized_bytecode_hashes == ["a"*64, "b"*64]

def test_federated_capability_attestation_receipt():
    from coreason_manifest.spec.ontology import FederatedCapabilityAttestationReceipt, InformationClassificationProfile, SecureSubSessionState, BilateralSLA

    session = SecureSubSessionState(
        session_id="session_1",
        allowed_vault_keys=[],
        max_ttl_seconds=10,
        description="desc"
    )
    sla = BilateralSLA(
        receiving_tenant_id="tenant_1",
        max_permitted_classification=InformationClassificationProfile("restricted"),
        liability_limit_magnitude=100,
        permitted_geographic_regions=["US"]
    )
    with pytest.raises(ValueError, match="RESTRICTED federated connections MUST define allowed_vault_keys"):
        FederatedCapabilityAttestationReceipt(
            attestation_id="att_1",
            target_topology_id="did:example:123",
            authorized_session=session,
            governing_sla=sla
        )
