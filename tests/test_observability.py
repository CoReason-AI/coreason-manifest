import json
from typing import Any

from coreason_manifest.spec.interop.otel import to_otel_attributes
from coreason_manifest.spec.interop.telemetry import NodeState
from coreason_manifest.utils.privacy import PrivacySentinel
from coreason_manifest.utils.recorder import BlackBoxRecorder


def test_privacy_sentinel_secrets() -> None:
    sentinel = PrivacySentinel(redact_secrets=True, hashing_salt="salty")

    # Test secret key redaction
    data = {"password": "supersecret", "api_key": "12345", "public": "visible"}
    sanitized = sentinel.sanitize(data)

    assert sanitized["password"] != "supersecret"
    assert sanitized["password"].startswith("<REDACTED:SECRET:")
    assert sanitized["api_key"] != "12345"
    assert sanitized["public"] == "visible"

    # Verify hashing consistency
    sanitized2 = sentinel.sanitize(data)
    assert sanitized["password"] == sanitized2["password"]


def test_privacy_sentinel_heuristics() -> None:
    sentinel = PrivacySentinel(redact_secrets=True)

    # Cases that SHOULD be redacted
    should_redact = {
        "auth_token": "secret",
        "access_token": "secret",
        "my_password": "secret",
        "client_secret": "secret",
        "api_key": "secret",
        "x-api-key": "secret",  # key part of split
    }

    # Cases that SHOULD NOT be redacted (metrics, safe words)
    should_keep = {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "author": "Gowtham",
        "authenticated": True,  # "authenticated" splits to ["authenticated"] which is not "auth"
        "key_id": "123",  # "key" is not in SENSITIVE_WORDS anymore (api_key is substring)
        "public_key_id": "pk_123",
    }

    for key, val in should_redact.items():
        res = sentinel.sanitize({key: val})
        assert res[key] != val, f"Expected redaction for {key}"
        assert str(res[key]).startswith("<REDACTED:SECRET:"), f"Expected redaction for {key}"

    for k_keep, v_keep in should_keep.items():
        res = sentinel.sanitize({k_keep: v_keep})
        assert res[k_keep] == v_keep, f"Expected NO redaction for {k_keep}"


def test_privacy_sentinel_pii() -> None:
    sentinel = PrivacySentinel(redact_pii=True, hashing_salt="salty")

    # Test PII redaction in strings
    email = "contact me at test@example.com please"
    sanitized_email = sentinel.sanitize(email)
    assert sanitized_email != email
    assert sanitized_email.startswith("<REDACTED:SECRET:")

    # Test PII inside list
    data = ["safe", "my ssn is 123-45-6789"]
    sanitized_list = sentinel.sanitize(data)
    assert sanitized_list[0] == "safe"
    assert sanitized_list[1] != "my ssn is 123-45-6789"


def test_privacy_sentinel_recursion() -> None:
    sentinel = PrivacySentinel(redact_secrets=True, redact_pii=True)

    data = {"user": {"profile": {"email": "user@example.com", "id": 123}, "auth": {"token": "secret_token"}}}

    sanitized = sentinel.sanitize(data)

    # Check deep PII redaction
    assert sanitized["user"]["profile"]["email"] != "user@example.com"
    assert sanitized["user"]["profile"]["email"].startswith("<REDACTED:SECRET:")

    # Check deep secret key redaction
    # "auth" is in SENSITIVE_WORDS. The whole value `{"token": ...}` is redacted.
    assert isinstance(sanitized["user"]["auth"], str)
    assert sanitized["user"]["auth"].startswith("<REDACTED:SECRET:")

    # If we had a non-sensitive key with sensitive inner key
    data2 = {"config": {"password": "123"}}
    sanitized2 = sentinel.sanitize(data2)
    assert sanitized2["config"]["password"].startswith("<REDACTED:SECRET:")


def test_recorder_chaining() -> None:
    recorder = BlackBoxRecorder(initial_hash="GENESIS_HASH")

    # Record 1
    rec1 = recorder.record(
        node_id="node1", state=NodeState.COMPLETED, inputs={"a": 1}, outputs={"b": 2}, duration_ms=10.0
    )

    assert rec1.previous_hash == "GENESIS_HASH"
    assert rec1.execution_hash is not None

    # Record 2
    rec2 = recorder.record(
        node_id="node2", state=NodeState.COMPLETED, inputs={"prev": 2}, outputs={"curr": 3}, duration_ms=15.0
    )

    assert rec2.previous_hash == rec1.execution_hash
    assert rec2.execution_hash != rec1.execution_hash

    # Verify internal state updated
    assert recorder.previous_hash == rec2.execution_hash


def test_recorder_sanitization_integration() -> None:
    # Recorder should use PrivacySentinel
    recorder = BlackBoxRecorder()

    rec = recorder.record(
        node_id="node_secret",
        state=NodeState.COMPLETED,
        inputs={"password": "secret"},
        outputs={"result": "ok"},
        duration_ms=5.0,
    )

    assert rec.inputs["password"] != "secret"
    assert str(rec.inputs["password"]).startswith("<REDACTED:SECRET:")


def test_otel_bridge() -> None:
    recorder = BlackBoxRecorder()
    rec = recorder.record(
        node_id="my_agent",
        state=NodeState.FAILED,
        inputs={"prompt": "hello"},
        outputs={"response": "world"},
        duration_ms=100.0,
        error="Something went wrong",
        attributes={"custom.tag": "value"},
    )

    otel_attrs = to_otel_attributes(rec)

    assert otel_attrs["gen_ai.system"] == "my_agent"
    assert otel_attrs["duration"] == 100.0
    assert otel_attrs["error.message"] == "Something went wrong"
    assert otel_attrs["custom.tag"] == "value"

    # Check input/output serialization
    inputs_json = json.loads(otel_attrs["gen_ai.request.content"])
    assert inputs_json["prompt"] == "hello"


def test_privacy_sentinel_no_pii_redaction() -> None:
    """
    Verify that if redact_pii is False, PII strings are returned as-is.
    """
    sentinel = PrivacySentinel(redact_pii=False)
    email = "test@example.com"
    sanitized = sentinel.sanitize(email)
    assert sanitized == email


def test_recorder_handles_non_dict_sanitized_data() -> None:
    """
    Verify that BlackBoxRecorder handles cases where PrivacySentinel returns
    non-dict data for inputs/outputs (e.g. if a custom sanitizer is used).
    """

    class MockSentinel(PrivacySentinel):
        def sanitize(self, data: Any) -> Any:
            # Force return a string even if input is dict
            return "sanitized_string"

    recorder = BlackBoxRecorder(privacy_sentinel=MockSentinel())

    rec = recorder.record(
        node_id="test_node", state=NodeState.COMPLETED, inputs={"a": 1}, outputs={"b": 2}, duration_ms=10.0
    )

    # The recorder should have wrapped the string result in a dict
    assert rec.inputs == {"_sanitized_value": "sanitized_string"}
    assert rec.outputs == {"_sanitized_value": "sanitized_string"}
