# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.observability import CloudEvent, EventContentType, ReasoningTrace


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


def test_security_datacontenttype_manipulation() -> None:
    """
    Red Team: Fuzzing datacontenttype field with dangerous strings.
    """
    now = datetime.now(timezone.utc)

    # 1. Null Byte Injection
    # Pydantic/Python should allow null bytes in strings, but JSON might escape them.
    # We want to ensure it doesn't crash.
    event_null = CloudEvent(
        id="null-test",
        source="urn:redteam",
        type="attack.null",
        time=now,
        datacontenttype="application/json\0",
    )
    dumped = event_null.dump()
    assert dumped["datacontenttype"] == "application/json\0"

    # 2. XSS Payload in Content Type
    # Should be preserved literally, relying on consumer to escape.
    xss_type = 'application/json"><script>alert(1)</script>'
    event_xss = CloudEvent(
        id="xss-test",
        source="urn:redteam",
        type="attack.xss",
        time=now,
        datacontenttype=xss_type,
    )
    dumped_xss = event_xss.dump()
    assert dumped_xss["datacontenttype"] == xss_type

    # 3. Massive Content Type String (DoS)
    # Should not crash.
    massive_type = "application/" + "a" * 1_000_000
    start = datetime.now()
    event_massive = CloudEvent(
        id="massive-type",
        source="urn:redteam",
        type="attack.massive",
        time=now,
        datacontenttype=massive_type,
    )
    dumped_massive = event_massive.dump()
    duration = (datetime.now() - start).total_seconds()

    assert len(dumped_massive["datacontenttype"]) > 1_000_000
    assert duration < 2.0  # Should be fast since it's just a string copy/ref


def test_security_enum_confusion() -> None:
    """
    Red Team: Attempt to confuse strict typing with Enum vs String.
    """
    now = datetime.now(timezone.utc)

    # 1. Using a string that looks like an Enum name but isn't the value
    # EventContentType.JSON is "application/json".
    # What if we pass "JSON"? It should be treated as a raw string "JSON".
    event_name = CloudEvent(
        id="name-test",
        source="urn:redteam",
        type="attack.confusion",
        time=now,
        datacontenttype="JSON",
    )
    assert event_name.datacontenttype == "JSON"
    assert event_name.datacontenttype != EventContentType.JSON

    # 2. Case sensitivity
    # "Application/Json" vs "application/json"
    event_case = CloudEvent(
        id="case-test",
        source="urn:redteam",
        type="attack.case",
        time=now,
        datacontenttype="Application/Json",
    )
    # It should NOT coerce to the Enum because Enums are value-based and exact string match.
    assert event_case.datacontenttype == "Application/Json"
    assert event_case.datacontenttype != EventContentType.JSON
