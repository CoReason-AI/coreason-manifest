import time
from unittest.mock import MagicMock

import pytest

from coreason_manifest.adapters.observability.privacy import scrub_genui_payload


@pytest.mark.evals
def test_schema_import() -> None:
    """Verify that the coreason_manifest schema can be imported."""
    import coreason_manifest

    assert coreason_manifest is not None


@pytest.mark.evals
def test_genui_multiplexer_emission() -> None:
    """Mock the emission of a Thought and UI Envelope, ensuring non-blocking and proper PII scrubbing."""
    # Mocking future stream contracts from parallel epics
    StreamThoughtEnvelope = MagicMock()
    StreamThoughtEnvelope.type = "thought"
    StreamThoughtEnvelope.content = "Reasoning about user request..."

    StreamUIEnvelope = MagicMock()
    StreamUIEnvelope.type = "ui"
    StreamUIEnvelope.payload = {
        "layout": {
            "type": "widget",
            "props": {
                "user_name": "Alice PII",
                "email": "alice@example.com",
            },
        }
    }

    # Simulate a multiplexer yielding these envelopes
    def mock_stream():
        yield StreamThoughtEnvelope
        yield StreamUIEnvelope

    emissions = []
    start_time = time.time()
    for envelope in mock_stream():
        if getattr(envelope, "type", None) == "ui":
            # Scrub before logging
            scrubbed_payload = scrub_genui_payload(envelope.payload)
            emissions.append(scrubbed_payload)
        else:
            emissions.append(envelope)
    end_time = time.time()

    # Assert non-blocking (the mock stream should complete instantly)
    assert (end_time - start_time) < 0.1

    # Ensure we got two envelopes
    assert len(emissions) == 2

    # Verify that the scrubber successfully stripped out the 'props' PII
    ui_emission = emissions[1]
    props = ui_emission["layout"]["props"]
    assert props["user_name"] == "[REDACTED_PII]"
    assert props["email"] == "[REDACTED_PII]"
    # Verify the structure remains intact
    assert ui_emission["layout"]["type"] == "widget"
