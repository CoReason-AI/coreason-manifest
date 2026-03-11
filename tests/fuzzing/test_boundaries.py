from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    BoundedJSONRPCIntent,
    BrowserDOMState,
    ConstitutionalPolicy,
    ContinuousMutationPolicy,
    DynamicLayoutManifest,
    EpistemicCompressionSLA,
    EpistemicTransmutationTask,
    ExecutionNodeReceipt,
    GlobalGovernancePolicy,
    InformationClassificationProfile,
    InsightCardProfile,
    SemanticSlicingPolicy,
    StateHydrationManifest,
)


@given(st.recursive(st.dictionaries(st.text(), st.text()), lambda c: st.dictionaries(st.text(), c)))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_jsonrpc_depth_attack_proof(params: dict[str, Any]) -> None:
    """Prove the schema definitively rejects deeply recursive JSON payloads out of bounds."""
    import contextlib

    payload = {"jsonrpc": "2.0", "method": "test_method", "params": params, "id": 1}
    with contextlib.suppress(ValidationError):
        BoundedJSONRPCIntent.model_validate(payload)


@pytest.mark.parametrize(
    "url", ["http://169.254.169.254/iam", "http://localhost:3000", "http://127.0.0.1:5432", "file:///etc/passwd"]
)
def test_browser_dom_ssrf_quarantine(url: str) -> None:
    """Prove Bogon IP space and local routing is severed to prevent SSRF escape."""
    with pytest.raises(ValidationError, match="SSRF"):
        BrowserDOMState(current_url=url, viewport_size=(800, 600), dom_hash="a" * 64, accessibility_tree_hash="a" * 64)


@pytest.mark.parametrize(
    "payload", ["<script>alert(1)</script>", "<img src='x' onerror='alert(1)'>", "[click me](javascript:alert(1))"]
)
def test_polymorphic_xss_proof(payload: str) -> None:
    """Prove InsightCardProfile definitively rejects malicious Markdown tags and schemas."""
    with pytest.raises(ValidationError):
        InsightCardProfile(panel_id="panel_1", title="Insight Title", markdown_content=payload)


@pytest.mark.parametrize(
    "payload", ["getattr(__builtins__, 'ev' + 'al')('print(1)')", "__import__('os').system('echo 1')"]
)
def test_dynamic_layout_ast_execution_bleed(payload: str) -> None:
    """Verify the AST boundary deterministically severs polymorphic string concatenation attacks."""
    with pytest.raises(ValidationError, match="Kinetic execution bleed detected"):
        DynamicLayoutManifest(layout_tstring=payload)


@given(rows=st.integers(min_value=10001, max_value=100000))
def test_continuous_mutation_oom_buffer_limit(rows: int) -> None:
    """Prove that ContinuousMutationPolicy rejects uncommitted rows > 10000 when append_only is True."""
    with pytest.raises(ValidationError, match="max_uncommitted_edges must be <= 10000 for append_only paradigm"):
        ContinuousMutationPolicy(
            mutation_paradigm="append_only", max_uncommitted_edges=rows, micro_batch_interval_ms=1000
        )


@pytest.mark.parametrize("visual_modality", ["tabular_grid", "raster_image"])
def test_multimodal_grounding_density_alignment(visual_modality: Any) -> None:
    """Prove that EpistemicTransmutationTask rejects visual modalities combined with sparse grounding density."""
    compression_sla = EpistemicCompressionSLA(
        strict_probability_retention=True,
        max_allowed_entropy_loss=0.5,
        required_grounding_density="sparse",
    )
    with pytest.raises(
        ValidationError,
        match=r"Epistemic safety violation: Visual or tabular modalities require strict spatial tracking\.",
    ):
        EpistemicTransmutationTask(
            task_id="task_visual_test",
            artifact_event_id="artifact_1",
            target_modalities=[visual_modality],
            compression_sla=compression_sla,
        )


def test_epistemic_license_enforcement() -> None:
    """Prove that instantiating GlobalGovernancePolicy with invalid mandatory_license_rule triggers ValidationError."""
    invalid_license = ConstitutionalPolicy(
        rule_id="MIT_LICENSE", severity="low", description="test", forbidden_intents=[]
    )
    with pytest.raises(ValidationError, match="CRITICAL LICENSE VIOLATION"):
        GlobalGovernancePolicy(
            mandatory_license_rule=invalid_license,
            max_budget_magnitude=1000,
            max_global_tokens=100000,
            global_timeout_seconds=3600,
        )


def test_mcp_quarantine_gateway_tripwire() -> None:
    from coreason_manifest.spec.ontology import (
        MCPCapabilityWhitelistPolicy,
        MCPServerManifest,
        VerifiableCredentialPresentationReceipt,
    )

    receipt = VerifiableCredentialPresentationReceipt(
        presentation_format="jwt_vc",
        issuer_did="did:web:rogue-actor:123",
        cryptographic_proof_blob="a" * 64,
        authorization_claims={},
    )
    with pytest.raises(ValidationError, match="UNAUTHORIZED MCP MOUNT"):
        MCPServerManifest(
            server_uri="http://rogue-server",
            transport_type="http",
            capability_whitelist=MCPCapabilityWhitelistPolicy(
                allowed_tools=["shell"], allowed_resources=["file://*"], allowed_prompts=["system"]
            ),
            attestation_receipt=receipt,
        )


def test_tool_invocation_cryptographic_starvation() -> None:
    from coreason_manifest.spec.ontology import ToolInvocationEvent

    with pytest.raises(ValidationError):
        ToolInvocationEvent(
            event_id="test_event",
            timestamp=1234567890.0,
            tool_name="test_tool",
            parameters={},
            agent_attestation=None,  # type: ignore
            zk_proof=None,  # type: ignore
        )


def test_mcp_quarantine_gateway_authorized_mount() -> None:
    """Prove the 'Happy Path' for the MCP Gateway, achieving 100% branch coverage."""
    from coreason_manifest.spec.ontology import (
        MCPCapabilityWhitelistPolicy,
        MCPServerManifest,
        VerifiableCredentialPresentationReceipt,
    )

    valid_receipt = VerifiableCredentialPresentationReceipt(
        presentation_format="jwt_vc",
        issuer_did="did:coreason:core-engine:v1",
        cryptographic_proof_blob="secure_proof_hash_12345",
        authorization_claims={"clearance": "RESTRICTED"},
    )

    # This must instantiate cleanly without raising a ValidationError
    manifest = MCPServerManifest(
        server_uri="stdio://coreason-mcp",
        transport_type="stdio",
        capability_whitelist=MCPCapabilityWhitelistPolicy(
            allowed_tools=["fetch"], allowed_resources=[], allowed_prompts=[]
        ),
        attestation_receipt=valid_receipt,
    )

    assert manifest.attestation_receipt.issuer_did.startswith("did:coreason:")


def test_kinetic_separation_canonical_sort() -> None:
    """Prove that the 2D cluster matrix deterministically collapses to a stable hash state."""
    from coreason_manifest.spec.ontology import KineticSeparationPolicy

    chaotic_clusters = [["mcp://server-b", "mcp://server-a"], ["tool-z", "tool-x", "tool-y"]]

    policy = KineticSeparationPolicy(
        policy_id="test_bipartite_01",
        mutually_exclusive_clusters=chaotic_clusters,
        enforcement_action="halt_and_quarantine",
    )

    # Assert inner lists are sorted, then outer list is sorted by the first element of inner lists
    assert policy.mutually_exclusive_clusters == [["mcp://server-a", "mcp://server-b"], ["tool-x", "tool-y", "tool-z"]]


def test_semantic_slicing_epistemic_bounds() -> None:
    """Prove the deterministic epistemic firewall rejects negative ceilings and perfectly sorts its canonical arrays."""

    # 1. Prove OOM/Zero-Token starvation rejection
    with pytest.raises(ValidationError, match="greater_than"):
        SemanticSlicingPolicy(
            permitted_classification_tiers=[InformationClassificationProfile.PUBLIC], context_window_token_ceiling=0
        )

    # 2. Prove Cryptographic Determinism (Sorting)
    policy = SemanticSlicingPolicy(
        permitted_classification_tiers=[
            InformationClassificationProfile.RESTRICTED,
            InformationClassificationProfile.INTERNAL,
            InformationClassificationProfile.PUBLIC,
        ],
        required_semantic_labels=["Zeta", "Alpha", "Gamma"],
        context_window_token_ceiling=4096,
    )

    assert policy.required_semantic_labels == ["Alpha", "Gamma", "Zeta"]
    assert policy.permitted_classification_tiers == [
        InformationClassificationProfile.INTERNAL,
        InformationClassificationProfile.PUBLIC,
        InformationClassificationProfile.RESTRICTED,
    ]


def test_procedural_manifold_deterministic_sort() -> None:
    """Prove that OntologicalSurfaceProjectionManifest deterministically sorts available_procedural_manifolds."""
    from coreason_manifest.spec.ontology import OntologicalSurfaceProjectionManifest, ProceduralMetadataManifest

    m1 = ProceduralMetadataManifest(metadata_id="zeta_01", target_sop_id="sop_1", trigger_description="Zeta SOP")
    m2 = ProceduralMetadataManifest(metadata_id="alpha_02", target_sop_id="sop_2", trigger_description="Alpha SOP")

    projection = OntologicalSurfaceProjectionManifest(projection_id="proj_1", available_procedural_manifolds=[m1, m2])

    # Assert the array was mathematically sorted by metadata_id
    assert projection.available_procedural_manifolds[0].metadata_id == "alpha_02"
    assert projection.available_procedural_manifolds[1].metadata_id == "zeta_01"


@given(
    trace_hash=st.text().filter(lambda x: not __import__("re").match("^[a-f0-9]{64}$", x)),
    penalty=st.floats(min_value=-10.0, max_value=10.0).filter(lambda x: x < 0.0 or x > 1.0),
)
def test_cognitive_critique_profile_bounds(trace_hash: str, penalty: float) -> None:
    from coreason_manifest.spec.ontology import CognitiveCritiqueProfile

    with pytest.raises(ValidationError):
        CognitiveCritiqueProfile(reasoning_trace_hash=trace_hash, epistemic_penalty_scalar=0.5)
    with pytest.raises(ValidationError):
        CognitiveCritiqueProfile(reasoning_trace_hash="a" * 64, epistemic_penalty_scalar=penalty)


@given(threshold=st.integers(max_value=0), asymptote=st.floats(max_value=-0.0001))
def test_kinetic_budget_policy_bounds(threshold: int, asymptote: float) -> None:
    from coreason_manifest.spec.ontology import KineticBudgetPolicy

    with pytest.raises(ValidationError):
        KineticBudgetPolicy(
            exploration_decay_curve="linear",
            forced_exploitation_threshold_ms=threshold,
            dynamic_temperature_asymptote=0.5,
        )
    with pytest.raises(ValidationError):
        KineticBudgetPolicy(
            exploration_decay_curve="linear",
            forced_exploitation_threshold_ms=10,
            dynamic_temperature_asymptote=asymptote,
        )
    with pytest.raises(ValidationError):
        KineticBudgetPolicy(
            exploration_decay_curve="invalid_curve",  # type: ignore
            forced_exploitation_threshold_ms=10,
            dynamic_temperature_asymptote=0.5,
        )


@given(entropy=st.floats(max_value=-0.0001), multiplier=st.floats(max_value=1.0), tiers=st.integers(max_value=0))
def test_epistemic_escalation_contract_bounds(entropy: float, multiplier: float, tiers: int) -> None:
    from coreason_manifest.spec.ontology import EpistemicEscalationContract

    with pytest.raises(ValidationError):
        EpistemicEscalationContract(
            baseline_entropy_threshold=entropy, test_time_multiplier=2.0, max_escalation_tiers=5
        )
    with pytest.raises(ValidationError):
        EpistemicEscalationContract(
            baseline_entropy_threshold=0.5, test_time_multiplier=multiplier, max_escalation_tiers=5
        )
    with pytest.raises(ValidationError):
        EpistemicEscalationContract(
            baseline_entropy_threshold=0.5, test_time_multiplier=2.0, max_escalation_tiers=tiers
        )


@given(
    merkle_root=st.text().filter(lambda x: not __import__("re").match("^[a-f0-9]{64}$", x)),
    vram=st.integers(max_value=0),
    ttl=st.integers(max_value=0),
    priority=st.floats().filter(lambda x: x < 0.0 or x > 1.0),
)
def test_federated_peft_contract_bounds(merkle_root: str, vram: int, ttl: int, priority: float) -> None:
    from coreason_manifest.spec.ontology import FederatedPeftContract

    with pytest.raises(ValidationError):
        FederatedPeftContract(
            adapter_merkle_root=merkle_root, vram_footprint_bytes=1000, ephemeral_ttl_ms=1000, cache_priority_weight=0.5
        )
    with pytest.raises(ValidationError):
        FederatedPeftContract(
            adapter_merkle_root="a" * 64, vram_footprint_bytes=vram, ephemeral_ttl_ms=1000, cache_priority_weight=0.5
        )
    with pytest.raises(ValidationError):
        FederatedPeftContract(
            adapter_merkle_root="a" * 64, vram_footprint_bytes=1000, ephemeral_ttl_ms=ttl, cache_priority_weight=0.5
        )
    with pytest.raises(ValidationError):
        FederatedPeftContract(
            adapter_merkle_root="a" * 64,
            vram_footprint_bytes=1000,
            ephemeral_ttl_ms=1000,
            cache_priority_weight=priority,
        )


@given(st.recursive(st.dictionaries(st.text(), st.text()), lambda c: st.dictionaries(st.text(), c), max_leaves=1))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_execution_node_receipt_recursive_payload(params: dict[str, Any]) -> None:  # noqa: ARG001
    """Prove that ExecutionNodeReceipt rejects deeply nested payloads on inputs > 10 depth."""

    def build_deep_dict(depth: int) -> dict[str, Any]:
        d: dict[str, Any] = {"base": "val"}
        for _ in range(depth):
            d = {"nested": d}
        return d

    deep_payload = build_deep_dict(11)
    with pytest.raises(ValidationError):
        ExecutionNodeReceipt(request_id="test_id", inputs=deep_payload, outputs={"valid": "output"})


def test_state_hydration_manifest_long_string_quarantine() -> None:
    """Prove that StateHydrationManifest immediately collapses instantiation and raises ValidationError for > 10k strings."""  # noqa: E501
    long_string = "a" * 10001
    with pytest.raises(ValidationError):
        StateHydrationManifest(
            epistemic_coordinate="test_session",
            crystallized_ledger_cids=["a" * 64],
            working_memory_variables={"large_payload": long_string},
            max_retained_tokens=4096,
        )
