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
import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.observability import CloudEvent, EventContentType

# --- Red Team / Security Tests ---

def test_mime_type_spoofing_vectors() -> None:
    """
    Test if `datacontenttype` accepts dangerous strings.

    Since `CloudEvent` allows arbitrary strings (Union[EventContentType, str]),
    this test confirms that the model stores them as-is without executing/interpreting them.
    It functions as a regression test to ensure we don't accidentally add unsafe validation logic later.
    """
    now = datetime.now(timezone.utc)
    vectors = [
        "application/javascript; alert(1)",
        "text/html; <script>alert(1)</script>",
        "../../etc/passwd",
        "A" * 10000,  # Buffer overflow attempt (Python handles this, but good to check perf)
    ]

    for vector in vectors:
        event = CloudEvent(
            id="sec-1",
            source="urn:sec",
            type="sec.test",
            time=now,
            datacontenttype=vector
        )
        # Should persist safely as a string
        assert event.datacontenttype == vector
        dumped = event.dump()
        assert dumped["datacontenttype"] == vector

def test_recursion_dos_protection() -> None:
    """
    Test deep nesting of CloudEvents to verify Pydantic V2's recursion limits.

    We attempt to create a deeply nested structure where `data` contains another `CloudEvent` dump.
    Pydantic V2 handles deep recursion well, but extremely deep structures should eventually
    raise a RecursionError or ValidationError, NOT segfault or hang indefinitely.
    """
    now = datetime.now(timezone.utc)

    # 1. Create a deep chain
    depth = 500
    last_payload = {"msg": "bottom"}

    for i in range(depth):
        try:
            last_payload = CloudEvent(
                id=f"nested-{i}",
                source="urn:nested",
                type="nested.event",
                time=now,
                data=last_payload if isinstance(last_payload, dict) else last_payload.dump()
            )
        except ValueError as e:
            # Pydantic V2 raises ValueError("Circular reference detected (depth exceeded)")
            if "Circular reference" in str(e) or "depth exceeded" in str(e):
                return
            raise

    # 2. Attempt serialization of the massive chain
    # This might be slow, but shouldn't crash.
    try:
        dumped = last_payload.dump()
        assert dumped["id"] == f"nested-{depth-1}"
    except (RecursionError, ValueError):
        # Accepting RecursionError is fine; crashing is not.
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception type: {type(e)}")

def test_large_payload_handling() -> None:
    """
    Test behavior with a massive `data` payload (e.g., 10MB string).
    Ensures no immediate memory exhaustion crashes during simple instantiation.
    """
    now = datetime.now(timezone.utc)
    large_data = {"blob": "x" * (10 * 1024 * 1024)}  # 10MB

    event = CloudEvent(
        id="large-1",
        source="urn:large",
        type="large.test",
        time=now,
        data=large_data
    )

    assert len(event.data["blob"]) == 10 * 1024 * 1024

def test_type_confusion_enum_injection() -> None:
    """
    Attempt to pass an invalid Enum type or object that mimics the Enum but isn't it.
    Since `datacontenttype` is Union[EventContentType, str],
    a non-matching Enum should be coerced to string or rejected if strict.
    """
    from enum import Enum
    class FakeEnum(str, Enum):
        FAKE = "application/fake"

    now = datetime.now(timezone.utc)

    # 1. Pass a different Enum member (should be treated as its value (str))
    event = CloudEvent(
        id="conf-1",
        source="urn:conf",
        type="conf.test",
        time=now,
        datacontenttype=FakeEnum.FAKE
    )

    # It matches the string value
    assert event.datacontenttype == "application/fake"

    # 2. Pass an object that str()s to a valid content type
    class SneakyStr:
        def __str__(self):
            return "application/json"

    # Pydantic V2 is strict on types; it should REJECT objects that just have __str__
    # unless we write a custom validator. This is secure behavior.
    with pytest.raises(ValidationError) as excinfo:
        CloudEvent(
            id="conf-2",
            source="urn:conf",
            type="conf.test",
            time=now,
            datacontenttype=SneakyStr() # type: ignore
        )
    assert "Input should be a valid string" in str(excinfo.value)

def test_payload_none_serialization_security() -> None:
    """
    Confirm that `data=None` is excluded from output.
    Security relevance: Prevents null-pointer-like issues in consumers
    that might blindly check `if 'data' in event:` vs `if event.get('data'):`.
    """
    now = datetime.now(timezone.utc)
    event = CloudEvent(id="null-1", source="urn:null", type="test", time=now, data=None)
    dumped = event.dump()
    assert "data" not in dumped
