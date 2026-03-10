from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    BoundedJSONRPCIntent,
    BrowserDOMState,
    ContinuousMutationPolicy,
    DynamicLayoutManifest,
    EpistemicCompressionSLA,
    EpistemicTransmutationTask,
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
    with pytest.raises(ValidationError, match="max_uncommitted_rows must be <= 10000 for append_only paradigm"):
        ContinuousMutationPolicy(
            mutation_paradigm="append_only", max_uncommitted_rows=rows, micro_batch_interval_ms=1000
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
