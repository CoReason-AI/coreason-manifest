from typing import Any

import pytest

from coreason_manifest.adapters.observability.privacy import scrub_genui_payload
from coreason_manifest.core.common.presentation import AdaptiveUIContract
from coreason_manifest.core.primitives.types import DataClassification
from coreason_manifest.core.telemetry.stream import StreamThoughtEnvelope, StreamUIEnvelope


def test_import() -> None:
    import coreason_manifest

    assert coreason_manifest is not None


@pytest.fixture
def mock_factory() -> Any:
    from coreason_manifest.toolkit.mock import MockFactory

    return MockFactory(seed=42)


def test_sota_passport_instantiation(mock_factory: Any) -> None:
    """
    Ensures the 2026+ Architectural Hardening fields are properly validated.
    Epic 6 is fully merged and models accept these kwargs.
    """
    # Test 1: Standard Multi-Dimensional Bounds
    passport = mock_factory.generate_mock_passport(classification=DataClassification.RESTRICTED)
    assert passport.delegation.max_tokens == 50_000
    assert passport.delegation.max_compute_time_ms == 120_000
    assert passport.delegation.max_data_classification == DataClassification.RESTRICTED
    assert passport.delegation.caep_stream_uri == "https://mock-ssf.local.coreason.ai/stream"
    assert passport.signature_algorithm == "ML-DSA-65"
    assert passport.parent_passport_id is None

    # Test 2: Swarm Lineage Fuzzing
    child_passport = mock_factory.generate_mock_passport(is_swarm_child=True)
    assert child_passport.parent_passport_id is not None
    assert "mock_parent_jti_" in child_passport.parent_passport_id


@pytest.mark.evals
def test_genui_multiplexer_emission() -> None:
    """
    Simulates a multiplexed stream yielding a thought and a UI component.
    Ensures that the stream does not block and the privacy scrubber
    successfully strips PII from the UI props.
    """

    def mock_stream() -> Any:
        yield StreamThoughtEnvelope(op="thought", p="Generating dashboard...", timestamp=1.0)
        yield StreamUIEnvelope(
            op="ui_mount",
            p=AdaptiveUIContract(
                layout=[{"type": "weather_widget", "props": {"location": "San Francisco", "user_id": "123-45-678"}}]
            ),
            timestamp=2.0
        )

    # Simulate multiplexer reading the stream
    stream_results = list(mock_stream())

    # Assert non-blocking generation (all items yielded)
    assert len(stream_results) == 2
    assert stream_results[0].op == "thought"
    assert stream_results[1].op == "ui_mount"

    # Simulate processing the UI envelope and passing to logger/scrubber
    raw_payload = stream_results[1].p.model_dump()
    scrubbed_payload = scrub_genui_payload(raw_payload)

    # The layout structure should be intact
    assert "layout" in scrubbed_payload
    assert scrubbed_payload["layout"][0]["type"] == "weather_widget"

    # The PII inside props should be redacted
    props = scrubbed_payload["layout"][0]["props"]
    assert props["location"] == "[REDACTED_PII]"
    assert props["user_id"] == "[REDACTED_PII]"
