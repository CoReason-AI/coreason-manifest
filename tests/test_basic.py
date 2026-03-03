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
    stream_thought_envelope = MagicMock()
    stream_thought_envelope.type = "thought"
    stream_thought_envelope.content = "Reasoning about user request..."

    stream_ui_envelope = MagicMock()
    stream_ui_envelope.type = "ui"
    stream_ui_envelope.payload = {
        "layout": {
            "type": "widget",
            "props": {
                "user_name": "Alice PII",
                "email": "alice@example.com",
                "variant": "danger",
                "disabled": True,
            },
        }
    }

    # Simulate a multiplexer yielding these envelopes
    def mock_stream():
        yield stream_thought_envelope
        yield stream_ui_envelope

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
    # Verify safe UI properties are preserved
    assert props["variant"] == "danger"
    assert props["disabled"] is True
    # Verify the structure remains intact
    assert ui_emission["layout"]["type"] == "widget"
