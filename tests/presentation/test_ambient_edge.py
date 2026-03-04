import pytest
from pydantic import ValidationError

from coreason_manifest.presentation.ambient import AmbientListenerConfig, AmbientTriggerRule
from coreason_manifest.presentation.ambient_edge import (
    AutonomousPrecomputeIntent,
    EdgeNativeAmbientListener,
    EdgeSLMProcessor,
)
from coreason_manifest.telemetry.ambient_schemas import MultimodalTelemetryStream


def test_edge_slm_processor_valid() -> None:
    """Test valid instantiation of EdgeSLMProcessor."""
    processor = EdgeSLMProcessor(
        model_quantization="int8",
        max_latency_ms=150,
        local_feature_extraction_only=True,
    )
    assert processor.model_quantization == "int8"
    assert processor.max_latency_ms == 150
    assert processor.local_feature_extraction_only is True


def test_edge_slm_processor_invalid_latency() -> None:
    """Test that max_latency_ms >= 250 raises a ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        EdgeSLMProcessor(
            model_quantization="int4",
            max_latency_ms=300,
            local_feature_extraction_only=False,
        )

    assert "max_latency_ms must be < 250ms" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo2:
        EdgeSLMProcessor(
            model_quantization="int4",
            max_latency_ms=250,
            local_feature_extraction_only=False,
        )

    assert "max_latency_ms must be < 250ms" in str(excinfo2.value)


def test_autonomous_precompute_intent_valid() -> None:
    """Test valid instantiation of AutonomousPrecomputeIntent."""
    intent = AutonomousPrecomputeIntent(
        predicted_query_hash="1234abcd",
        confidence_score=0.85,
        background_resource_allocation_mb=512,
        auto_inject_ui_target="$local.search_results",
    )
    assert intent.predicted_query_hash == "1234abcd"
    assert intent.confidence_score == 0.85
    assert intent.background_resource_allocation_mb == 512
    assert intent.auto_inject_ui_target == "$local.search_results"


def test_autonomous_precompute_intent_invalid_confidence() -> None:
    """Test that confidence_score < 0.0 or > 1.0 raises a ValidationError."""
    with pytest.raises(ValidationError) as excinfo_low:
        AutonomousPrecomputeIntent(
            predicted_query_hash="1234abcd",
            confidence_score=-0.1,
            background_resource_allocation_mb=512,
        )
    assert "confidence_score must be between 0.0 and 1.0" in str(excinfo_low.value)

    with pytest.raises(ValidationError) as excinfo_high:
        AutonomousPrecomputeIntent(
            predicted_query_hash="1234abcd",
            confidence_score=1.1,
            background_resource_allocation_mb=512,
        )
    assert "confidence_score must be between 0.0 and 1.0" in str(excinfo_high.value)


def test_edge_native_ambient_listener_valid() -> None:
    """Test valid instantiation of EdgeNativeAmbientListener."""
    trigger_rule = AmbientTriggerRule(
        trigger_events=["CANVAS_ADD_CONNECTION"],
        debounce_ms=800,
        extract_triplets=True,
    )
    base_config = AmbientListenerConfig(
        listener_id="listener_001",
        target_canvas_id="canvas_001",
        trigger_rules=[trigger_rule],
        action_route="node_001",
        ui_target_pointer="$local.results",
    )
    telemetry_stream = MultimodalTelemetryStream(
        audio_exhaust_enabled=False,
        screen_capture_framerate=1.0,
        privacy_masking_zones=[],
    )
    processor = EdgeSLMProcessor(
        model_quantization="int4",
        max_latency_ms=200,
        local_feature_extraction_only=True,
    )

    listener = EdgeNativeAmbientListener(
        base_config=base_config,
        telemetry_stream=telemetry_stream,
        edge_processor=processor,
        precompute_threshold=0.9,
    )

    assert listener.precompute_threshold == 0.9
    assert listener.base_config.listener_id == "listener_001"
    assert listener.telemetry_stream.screen_capture_framerate == 1.0
    assert listener.edge_processor.max_latency_ms == 200
