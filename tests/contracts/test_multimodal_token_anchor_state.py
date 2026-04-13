import pytest
from pydantic import ValidationError
from coreason_manifest.spec.ontology import MultimodalTokenAnchorState

def test_temporal_frame_start_without_end():
    with pytest.raises(ValidationError, match="If temporal_frame_start_ms is defined, temporal_frame_end_ms MUST be defined."):
        MultimodalTokenAnchorState.model_validate({"temporal_frame_start_ms": 100})

def test_temporal_frame_end_without_start():
    with pytest.raises(ValidationError, match="temporal_frame_end_ms cannot be defined without a temporal_frame_start_ms."):
        MultimodalTokenAnchorState.model_validate({"temporal_frame_end_ms": 100})

def test_temporal_frame_start_greater_than_end():
    with pytest.raises(ValidationError, match="temporal_frame_end_ms MUST be strictly greater than temporal_frame_start_ms."):
        MultimodalTokenAnchorState.model_validate({"temporal_frame_start_ms": 200, "temporal_frame_end_ms": 100})

def test_temporal_frame_start_equal_to_end():
    with pytest.raises(ValidationError, match="temporal_frame_end_ms MUST be strictly greater than temporal_frame_start_ms."):
        MultimodalTokenAnchorState.model_validate({"temporal_frame_start_ms": 100, "temporal_frame_end_ms": 100})

def test_token_span_start_without_end():
    with pytest.raises(ValidationError, match="If token_span_start is defined, token_span_end MUST be defined."):
        MultimodalTokenAnchorState.model_validate({"token_span_start": 100})

def test_token_span_end_without_start():
    with pytest.raises(ValidationError, match="token_span_end cannot be defined without a token_span_start."):
        MultimodalTokenAnchorState.model_validate({"token_span_end": 100})

def test_token_span_start_greater_than_end():
    with pytest.raises(ValidationError, match="token_span_end MUST be strictly greater than token_span_start."):
        MultimodalTokenAnchorState.model_validate({"token_span_start": 200, "token_span_end": 100})

def test_token_span_start_equal_to_end():
    with pytest.raises(ValidationError, match="token_span_end MUST be strictly greater than token_span_start."):
        MultimodalTokenAnchorState.model_validate({"token_span_start": 100, "token_span_end": 100})

def test_valid_temporal_frames():
    anchor = MultimodalTokenAnchorState.model_validate({"temporal_frame_start_ms": 100, "temporal_frame_end_ms": 200})
    assert anchor.temporal_frame_start_ms == 100
    assert anchor.temporal_frame_end_ms == 200

def test_valid_token_spans():
    anchor = MultimodalTokenAnchorState.model_validate({"token_span_start": 100, "token_span_end": 200})
    assert anchor.token_span_start == 100
    assert anchor.token_span_end == 200
