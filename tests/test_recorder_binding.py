from coreason_manifest.spec.core.governance import Audit, Governance, Safety
from coreason_manifest.spec.interop.telemetry import NodeState
from coreason_manifest.utils.recorder import create_recorder


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
        parent_hashes=[],
    )

    # Assert email is redacted (via omission due to secure default)
    assert record.inputs == {"_omitted": "policy_log_payloads_false"}


# Test 2: Explicit Opt-In (Redaction Enabled)
def test_recorder_explicit_opt_in() -> None:
    """
    Test that if governance explicitly enables PII redaction, it is respected.
    We must also enable log_payloads to verify the redaction.
    """
    gov = Governance(
        safety=Safety(input_filtering=True, pii_redaction=True, content_safety="high"),
        audit=Audit(trace_retention_days=7, log_payloads=True),
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
        parent_hashes=[],
    )

    sanitized_email = record.inputs["email"]
    assert "secure@example.com" not in sanitized_email
    assert isinstance(sanitized_email, str)
    assert sanitized_email.startswith("<REDACTED:SECRET:")


# Test 3: Explicit Opt-Out (Redaction Disabled)
def test_recorder_explicit_opt_out() -> None:
    """
    Test that if governance explicitly disables PII redaction, PII passes through.
    We must enable log_payloads.
    """
    gov = Governance(
        safety=Safety(input_filtering=True, pii_redaction=False, content_safety="medium"),
        audit=Audit(trace_retention_days=7, log_payloads=True),
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
        parent_hashes=[],
    )

    # Assert email is NOT redacted
    assert record.inputs["email"] == "internal@example.com"


# Test 4: Omit Payloads
def test_recorder_omits_payloads() -> None:
    """
    Assert that if log_payloads=False, inputs/outputs are replaced with marker.
    """
    gov = Governance(
        safety=Safety(input_filtering=True, pii_redaction=True, content_safety="high"),
        audit=Audit(log_payloads=False, trace_retention_days=7),
    )
    recorder = create_recorder(gov)

    record = recorder.record(
        node_id="test_omit",
        state=NodeState.COMPLETED,
        inputs={"sensitive": "data"},
        outputs={"also": "sensitive"},
        duration_ms=10.0,
        parent_hashes=[],
    )

    expected = {"_omitted": "policy_log_payloads_false"}
    assert record.inputs == expected
    assert record.outputs == expected


# Test 5: Salting Hashes (Dynamic)
def test_recorder_salts_hashes() -> None:
    """
    Call create_recorder twice with same Governance config but *no* explicit salt.
    Assert that redacted hashes are different (proving random fallback).
    """
    gov = Governance(
        safety=Safety(input_filtering=True, pii_redaction=True, content_safety="high"),
        audit=Audit(log_payloads=True, trace_retention_days=7),
    )

    # Instance 1
    r1 = create_recorder(gov)
    rec1 = r1.record(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={"secret": "my_secret_value"},
        outputs={},
        duration_ms=1.0,
        parent_hashes=[],
    )

    # Instance 2
    r2 = create_recorder(gov)
    rec2 = r2.record(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={"secret": "my_secret_value"},
        outputs={},
        duration_ms=1.0,
        parent_hashes=[],
    )

    hash1 = rec1.inputs["secret"]
    hash2 = rec2.inputs["secret"]

    assert hash1 != hash2
    assert hash1.startswith("<REDACTED:SECRET:")
    assert hash2.startswith("<REDACTED:SECRET:")


# Test 6: Deterministic Salt
def test_recorder_deterministic_salt() -> None:
    """
    Call create_recorder with a fixed system_salt.
    Assert that redacted hashes are deterministic.
    """
    gov = Governance(
        safety=Safety(input_filtering=True, pii_redaction=True, content_safety="high"),
        audit=Audit(log_payloads=True, trace_retention_days=7),
    )
    salt = "my_fixed_salt"

    r1 = create_recorder(gov, system_salt=salt)
    rec1 = r1.record(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={"secret": "same_value"},
        outputs={},
        duration_ms=1.0,
        parent_hashes=[],
    )

    r2 = create_recorder(gov, system_salt=salt)
    rec2 = r2.record(
        node_id="n1",
        state=NodeState.COMPLETED,
        inputs={"secret": "same_value"},
        outputs={},
        duration_ms=1.0,
        parent_hashes=[],
    )

    assert rec1.inputs["secret"] == rec2.inputs["secret"]
