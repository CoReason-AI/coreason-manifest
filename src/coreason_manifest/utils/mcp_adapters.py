# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any, cast

import msgspec

from coreason_manifest.spec.ontology import ExecutionEnvelopeState

_ENCODER = msgspec.json.Encoder(order="deterministic")


def _canonicalize_payload(payload: Any) -> Any:
    """
    Recursively strips all `None` values from dictionaries and lists to mathematically prevent Null Contagion.
    """
    if isinstance(payload, dict):
        return {k: _canonicalize_payload(v) for k, v in payload.items() if v is not None}
    if isinstance(payload, list):
        return [_canonicalize_payload(v) for v in payload if v is not None]
    return payload


class DeterministicTransportAdapter:
    """
    AGENT INSTRUCTION: Strictly serializes execution envelopes into deterministic JSON-RPC 2.0 bytes.

    CAUSAL AFFORDANCE: Operates as an impassable one-way serialization border. It physically strips mutable connection attributes to mathematically guarantee that all execution records are identical byte-for-byte across varying host environments.

    EPISTEMIC BOUNDS: It is natively forbidden from invoking socket writes, stdout, or async TCP loops. Pure structural projection relying entirely on `msgspec.json.Encoder(sort_keys=True)`.

    MCP ROUTING TRIGGERS: JSON-RPC 2.0, Byte Serialization, Zero-Trust Execution, msgspec, Deterministic Network Transport
    """

    @staticmethod
    def serialize_envelope(envelope: ExecutionEnvelopeState[Any]) -> bytes:
        payload_dict = envelope.model_dump(mode="json", exclude_none=True, by_alias=True)
        canonical_dict = _canonicalize_payload(payload_dict)
        trace_context = payload_dict.get("trace_context", {})
        request_cid = trace_context.get("trace_cid", "unknown")

        wrapped_payload = {
            "jsonrpc": "2.0",
            "method": "coreason_execute",
            "params": canonical_dict,
            "id": request_cid,  # Note: External Protocol Exemption.
        }
        return cast("bytes", _ENCODER.encode(wrapped_payload))
