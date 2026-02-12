import json
from typing import Any, cast

from coreason_manifest.spec.interop.otel import to_otel_attributes
from coreason_manifest.spec.interop.telemetry import NodeState
from coreason_manifest.utils.integrity import verify_merkle_proof
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


def test_privacy_sentinel_custom_keys() -> None:
    # Test extensibility
    sentinel = PrivacySentinel(redact_secrets=True, custom_sensitive_keys={"mrn", "dob", "patient_id"})

    data = {"patient_id": "12345", "mrn": "A-999", "dob": "2000-01-01", "other": "safe"}
    sanitized = sentinel.sanitize(data)

    assert sanitized["patient_id"] != "12345"
    assert str(sanitized["patient_id"]).startswith("<REDACTED:SECRET:")
    assert sanitized["mrn"] != "A-999"
    assert sanitized["dob"] != "2000-01-01"
    assert sanitized["other"] == "safe"


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


def test_recorder_stateless_dag() -> None:
    # Recorder is now stateless
    recorder = BlackBoxRecorder()

    # Step 1: Genesis Node
    rec1 = recorder.record(
        node_id="genesis",
        state=NodeState.COMPLETED,
        inputs={"a": 1},
        outputs={"b": 2},
        duration_ms=10.0,
        previous_hashes=[],  # Genesis
    )
    assert rec1.execution_hash is not None
    assert rec1.previous_hashes == []

    # Step 2: Parallel Node A (links to Genesis)
    rec2a = recorder.record(
        node_id="worker_a",
        state=NodeState.COMPLETED,
        inputs={"in": "a"},
        outputs={"out": "a"},
        duration_ms=5.0,
        previous_hashes=[rec1.execution_hash],  # Link to rec1
    )
    assert rec2a.previous_hashes == [rec1.execution_hash]

    # Step 3: Parallel Node B (links to Genesis)
    rec2b = recorder.record(
        node_id="worker_b",
        state=NodeState.COMPLETED,
        inputs={"in": "b"},
        outputs={"out": "b"},
        duration_ms=5.0,
        previous_hashes=[rec1.execution_hash],  # Link to rec1
    )
    assert rec2b.previous_hashes == [rec1.execution_hash]

    # Step 4: Aggregator Node (links to A and B) - The DAG Merge
    rec3 = recorder.record(
        node_id="aggregator",
        state=NodeState.COMPLETED,
        inputs={"results": ["a", "b"]},
        outputs={"final": "done"},
        duration_ms=20.0,
        previous_hashes=[cast("str", rec2a.execution_hash), cast("str", rec2b.execution_hash)],  # Merge
    )

    assert len(rec3.previous_hashes) == 2
    assert rec2a.execution_hash in rec3.previous_hashes
    assert rec2b.execution_hash in rec3.previous_hashes


def test_dag_integrity() -> None:
    # Re-use the DAG construction from above logic (simplified) to test verify_merkle_proof
    recorder = BlackBoxRecorder()

    # 1. Genesis
    n1 = recorder.record("n1", NodeState.COMPLETED, {}, {}, 1.0, previous_hashes=[])
    # 2. Branch A
    n2a = recorder.record("n2a", NodeState.COMPLETED, {}, {}, 1.0, previous_hashes=[cast("str", n1.execution_hash)])
    # 3. Branch B
    n2b = recorder.record("n2b", NodeState.COMPLETED, {}, {}, 1.0, previous_hashes=[cast("str", n1.execution_hash)])
    # 4. Merge
    n3 = recorder.record(
        "n3",
        NodeState.COMPLETED,
        {},
        {},
        1.0,
        previous_hashes=[cast("str", n2a.execution_hash), cast("str", n2b.execution_hash)],
    )

    trace = [n1, n2a, n2b, n3]

    # Verify valid DAG
    assert verify_merkle_proof(trace) is True

    # Verify Broken Link
    n3_bad = n3.model_copy(update={"previous_hashes": ["bad_hash", n2b.execution_hash]})
    trace_bad = [n1, n2a, n2b, n3_bad]
    assert verify_merkle_proof(trace_bad) is False

    # Verify Missing Parent in History
    trace_incomplete = [n1, n2a, n3]  # n3 depends on n2b which is missing
    assert verify_merkle_proof(trace_incomplete) is False

    # Verify Genesis Trusted Root
    assert verify_merkle_proof([n1], trusted_root_hash=cast("str", n1.execution_hash)) is True
    assert verify_merkle_proof([n1], trusted_root_hash="bad_root") is False


def test_recorder_sanitization_integration() -> None:
    # Recorder should use PrivacySentinel
    recorder = BlackBoxRecorder()

    rec = recorder.record(
        node_id="node_secret",
        state=NodeState.COMPLETED,
        inputs={"password": "secret"},
        outputs={"result": "ok"},
        duration_ms=5.0,
        previous_hashes=[],
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
        previous_hashes=[],
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
        def sanitize(self, _: Any) -> Any:
            # Force return a string even if input is dict
            return "sanitized_string"

    recorder = BlackBoxRecorder(privacy_sentinel=MockSentinel())

    rec = recorder.record(
        node_id="test_node",
        state=NodeState.COMPLETED,
        inputs={"a": 1},
        outputs={"b": 2},
        duration_ms=10.0,
        previous_hashes=[],
    )

    # The recorder should have wrapped the string result in a dict
    assert rec.inputs == {"_sanitized_value": "sanitized_string"}
    assert rec.outputs == {"_sanitized_value": "sanitized_string"}
