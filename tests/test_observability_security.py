from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.observability import CloudEvent, ReasoningTrace


def test_security_massive_payload_dos() -> None:
    """
    Red Team: Attempt to cause DoS/Memory exhaustion with a massive payload.
    Pydantic should handle this, but we check for crashes or extreme latency.
    """
    massive_string = "a" * 1_000_000  # 1MB string
    massive_dict = {f"key_{i}": massive_string for i in range(10)}  # 10MB payload

    start = datetime.now()
    event = CloudEvent(
        id="dos-test", source="urn:redteam", type="attack.dos", time=datetime.now(timezone.utc), data=massive_dict
    )
    dumped = event.dump()
    duration = (datetime.now() - start).total_seconds()

    assert dumped["data"]["key_0"] == massive_string
    # Ensure serialization is reasonably fast (< 1s for 10MB is expected on modern CPUs)
    # This is a soft check; main goal is no crash.
    assert duration < 5.0


def test_security_deep_nesting_recursion() -> None:
    """
    Red Team: Attempt stack overflow via deep recursion in `data`.
    Standard JSON parsers have recursion limits; Pydantic might too.
    """
    deep_dict: Dict[str, Any] = {}
    current = deep_dict
    for _ in range(1000):
        current["next"] = {}
        current = current["next"]

    event = CloudEvent(
        id="recursion-test",
        source="urn:redteam",
        type="attack.recursion",
        time=datetime.now(timezone.utc),
        data=deep_dict,
    )

    # Dump should fail with RecursionError or ValueError due to depth
    # Pydantic serializer raises ValueError: Circular reference detected (depth exceeded)
    # Python raises RecursionError if stack limit hit.
    with pytest.raises((ValueError, RecursionError)):
        event.dump()


def test_security_injection_strings() -> None:
    """
    Red Team: Verify that injection strings (SQLi, XSS) are preserved literally
    and not executed or interpreted during serialization.
    """
    malicious_payload = {
        "sqli": "'; DROP TABLE users; --",
        "xss": "<script>alert('xss')</script>",
        "cmd": "$(rm -rf /)",
    }

    event = CloudEvent(
        id="injection-test",
        source="urn:redteam",
        type="attack.injection",
        time=datetime.now(timezone.utc),
        data=malicious_payload,
    )

    dumped = event.dump()
    # Pydantic/JSON serialization must escape these, preventing execution if blindly rendered.
    # We verify the content remains preserved as data.
    assert dumped["data"]["sqli"] == "'; DROP TABLE users; --"
    assert dumped["data"]["xss"] == "<script>alert('xss')</script>"


def test_security_pii_leakage_warning() -> None:
    """
    Red Team: ReasoningTrace `inputs` and `outputs` might contain PII/Secrets.
    There is no automatic redaction, so we just verify they accept any dict.
    (This is a finding for the documentation, not a code failure per se).
    """
    secret_payload = {"api_key": "sk-1234567890", "password": "super_secret"}

    trace = ReasoningTrace(
        request_id=uuid4(),
        root_request_id=uuid4(),
        node_id="auth-service",
        status="success",
        inputs=secret_payload,
        latency_ms=1.0,
        timestamp=datetime.now(timezone.utc),
    )

    dumped = trace.dump()
    # Confirm secrets are present (i.e., NOT redacted).
    # This confirms the risk: The consumer is responsible for scrubbing.
    assert dumped["inputs"]["api_key"] == "sk-1234567890"


def test_security_type_spoofing() -> None:
    """
    Red Team: Declare datacontenttype='application/json' but provide non-dict data?
    CloudEvent model enforces `data: Optional[Dict[str, Any]]`.
    So we cannot pass a string or bytes if we want to be valid Pydantic.
    """
    with pytest.raises(ValidationError):
        CloudEvent(
            id="spoof-test",
            source="urn:redteam",
            type="attack.spoof",
            time=datetime.now(timezone.utc),
            datacontenttype="application/json",
            data="<xml>not json</xml>",
        )
