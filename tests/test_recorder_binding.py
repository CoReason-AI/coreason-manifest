import pytest
from coreason_manifest.spec.core.governance import Governance, Safety
from coreason_manifest.utils.recorder import create_recorder
from coreason_manifest.spec.interop.telemetry import NodeState

# Test 1: Fail-Safe Default
def test_recorder_fail_safe_default() -> None:
    """
    Test that if no governance config is provided, the recorder defaults
    to redacting PII (fail-safe).
    """
    recorder = create_recorder(None)

    # Check internal state of the sentinel
    assert recorder.privacy.redact_pii is True
    # redact_secrets defaults to True in PrivacySentinel and create_recorder
    assert recorder.privacy.redact_secrets is True

    # Functional test
    pii_input = {"email": "test@example.com"}
    record = recorder.record(
        node_id="test_node",
        state=NodeState.COMPLETED,
        inputs=pii_input,
        outputs={},
        duration_ms=10.0,
        parent_hashes=[]
    )

    # Assert email is redacted
    sanitized_email = record.inputs["email"]
    # Verify it is not the original email
    assert "test@example.com" not in sanitized_email
    # Verify it has the redaction marker
    assert isinstance(sanitized_email, str)
    assert sanitized_email.startswith("<REDACTED:SECRET:")

# Test 2: Explicit Opt-In (Redaction Enabled)
def test_recorder_explicit_opt_in() -> None:
    """
    Test that if governance explicitly enables PII redaction, it is respected.
    """
    gov = Governance(
        safety=Safety(
            input_filtering=True,
            pii_redaction=True,
            content_safety="high"
        )
    )
    recorder = create_recorder(gov)

    assert recorder.privacy.redact_pii is True

    pii_input = {"email": "secure@example.com"}
    record = recorder.record(
        node_id="test_node",
        state=NodeState.COMPLETED,
        inputs=pii_input,
        outputs={},
        duration_ms=10.0,
        parent_hashes=[]
    )

    sanitized_email = record.inputs["email"]
    assert "secure@example.com" not in sanitized_email
    assert isinstance(sanitized_email, str)
    assert sanitized_email.startswith("<REDACTED:SECRET:")

# Test 3: Explicit Opt-Out (Redaction Disabled)
def test_recorder_explicit_opt_out() -> None:
    """
    Test that if governance explicitly disables PII redaction, PII passes through.
    """
    gov = Governance(
        safety=Safety(
            input_filtering=True,
            pii_redaction=False,
            content_safety="medium"
        )
    )
    recorder = create_recorder(gov)

    assert recorder.privacy.redact_pii is False

    pii_input = {"email": "internal@example.com"}
    record = recorder.record(
        node_id="test_node",
        state=NodeState.COMPLETED,
        inputs=pii_input,
        outputs={},
        duration_ms=10.0,
        parent_hashes=[]
    )

    # Assert email is NOT redacted
    assert record.inputs["email"] == "internal@example.com"
