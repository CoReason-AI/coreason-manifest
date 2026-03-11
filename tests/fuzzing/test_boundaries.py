import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    BrowserDOMState,
    ConstitutionalPolicy,
    GlobalGovernancePolicy,
    InformationClassificationProfile,
    InsightCardProfile,
    SemanticSlicingPolicy,
)


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
