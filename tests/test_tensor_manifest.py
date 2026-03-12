import pytest

from coreason_manifest.spec.ontology import (
    ExecutionSpanReceipt,
    MCPServerBindingProfile,
    NDimensionalTensorManifest,
    NeuralAuditAttestationReceipt,
    PeftAdapterContract,
    SaeFeatureActivationState,
    SpanEvent,
    StdioTransportProfile,
    SteadyStateHypothesisState,
    TensorStructuralFormatProfile,
)


def test_tensor_manifest_valid() -> None:
    manifest = NDimensionalTensorManifest(
        structural_type=TensorStructuralFormatProfile.FLOAT32,
        shape=(2, 3),
        vram_footprint_bytes=24,  # 2*3*4
        merkle_root="0" * 64,
        storage_uri="s3://bucket/tensor",
    )
    assert manifest.vram_footprint_bytes == 24


def test_tensor_manifest_invalid_shape_len() -> None:
    with pytest.raises(ValueError, match="Tensor shape must have at least 1 dimension"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(),
            vram_footprint_bytes=0,
            merkle_root="0" * 64,
            storage_uri="s3://bucket/tensor",
        )


def test_tensor_manifest_invalid_dim() -> None:
    with pytest.raises(ValueError, match="Tensor dimensions must be strictly positive integers"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, 0),
            vram_footprint_bytes=0,
            merkle_root="0" * 64,
            storage_uri="s3://bucket/tensor",
        )


def test_tensor_manifest_mismatch_bytes() -> None:
    with pytest.raises(ValueError, match="Topological mismatch: Shape"):
        NDimensionalTensorManifest(
            structural_type=TensorStructuralFormatProfile.FLOAT32,
            shape=(2, 3),
            vram_footprint_bytes=100,
            merkle_root="0" * 64,
            storage_uri="s3://bucket/tensor",
        )


def test_tensor_manifest_from_str_enum() -> None:
    manifest = NDimensionalTensorManifest(
        structural_type=TensorStructuralFormatProfile("float32"),
        shape=(2, 3),
        vram_footprint_bytes=24,
        merkle_root="0" * 64,
        storage_uri="s3://bucket/tensor",
    )
    assert manifest.vram_footprint_bytes == 24


def test_neural_audit_attestation_receipt() -> None:
    activation1 = SaeFeatureActivationState(feature_index=2, activation_magnitude=0.5)
    activation2 = SaeFeatureActivationState(feature_index=1, activation_magnitude=0.8)
    receipt = NeuralAuditAttestationReceipt(audit_id="audit_123", layer_activations={0: [activation1, activation2]})
    assert receipt.layer_activations[0][0].feature_index == 1
    assert receipt.layer_activations[0][1].feature_index == 2


def test_peft_adapter_manifest() -> None:
    manifest = PeftAdapterContract(
        adapter_id="adapter_1",
        safetensors_hash="0" * 64,
        base_model_hash="0" * 64,
        adapter_rank=8,
        target_modules=["module_b", "module_a"],
    )
    assert manifest.target_modules == ["module_a", "module_b"]


def test_execution_span_receipt() -> None:
    event1 = SpanEvent(name="event1", timestamp_unix_nano=2000, attributes={})
    event2 = SpanEvent(name="event2", timestamp_unix_nano=1000, attributes={})
    receipt = ExecutionSpanReceipt(
        trace_id="trace1",
        span_id="span1",
        parent_span_id="parent1",
        name="test_span",
        start_time_unix_nano=100,
        end_time_unix_nano=1000,
        events=[event1, event2],
    )
    assert receipt.events[0].name == "event1"
    assert receipt.events[1].name == "event2"


def test_execution_span_receipt_invalid_time() -> None:
    with pytest.raises(ValueError, match="end_time_unix_nano cannot be before start_time_unix_nano"):
        ExecutionSpanReceipt(
            trace_id="trace1", span_id="span1", name="test_span", start_time_unix_nano=1000, end_time_unix_nano=100
        )


def test_mcp_server_binding_profile() -> None:
    profile = MCPServerBindingProfile(
        server_id="server1",
        transport=StdioTransportProfile(command="cmd", args=[]),
        required_capabilities=["tools", "prompts", "resources"],
    )
    assert profile.required_capabilities == ["prompts", "resources", "tools"]


def test_steady_state_hypothesis_state() -> None:
    state = SteadyStateHypothesisState(
        expected_max_latency=10.0, max_loops_allowed=5, required_tool_usage=["tool_b", "tool_a"]
    )
    assert state.required_tool_usage == ["tool_a", "tool_b"]
