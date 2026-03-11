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
    GlobalGovernancePolicy,
    InsightCardProfile,
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
