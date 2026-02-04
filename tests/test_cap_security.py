# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict

from coreason_manifest.spec.cap import StreamOpCode, StreamPacket


def test_deeply_nested_payload_dos_check() -> None:
    """Ensure deeply nested payloads don't crash validation (though they might hit recursion limits)."""
    # Create a nested dict 500 levels deep
    deep_payload: Dict[str, Any] = {}
    current = deep_payload
    for _ in range(500):
        current["next"] = {}
        current = current["next"]

    # This should pass validation as a Dict, or fail gracefully with RecursionError if too deep for Python.
    # 500 is usually safe for default recursion limit (1000).
    packet = StreamPacket(op=StreamOpCode.EVENT, p=deep_payload)
    assert packet.op == StreamOpCode.EVENT
    assert isinstance(packet.p, dict)
