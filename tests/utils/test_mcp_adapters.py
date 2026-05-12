# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import json

from coreason_manifest.spec.ontology import (
    ExecutionEnvelopeState,
    FYIIntent,
    StateVectorProfile,
    TraceContextState,
)
from coreason_manifest.utils.mcp_adapters import DeterministicTransportAdapter, _canonicalize_payload


def test_canonicalize_payload_primitives() -> None:
    assert _canonicalize_payload(1) == 1
    assert _canonicalize_payload("string") == "string"
    assert _canonicalize_payload(None) is None
    assert _canonicalize_payload(True) is True


def test_canonicalize_payload_dict() -> None:
    payload = {"a": 1, "b": None, "c": {"d": None, "e": 2}}
    assert _canonicalize_payload(payload) == {"a": 1, "c": {"e": 2}}


def test_canonicalize_payload_list() -> None:
    payload = [1, None, 2, [3, None, 4]]
    assert _canonicalize_payload(payload) == [1, 2, [3, 4]]


def test_canonicalize_payload_mixed() -> None:
    payload = {"a": [1, None], "b": {"c": None}, "d": None}
    assert _canonicalize_payload(payload) == {"a": [1], "b": {}}


def test_canonicalize_payload_tuple() -> None:
    # Tuples are not modified by current implementation
    payload = (1, None, 2)
    assert _canonicalize_payload(payload) == (1, None, 2)


def test_serialize_envelope_with_trace_context() -> None:
    intent = FYIIntent()
    envelope = ExecutionEnvelopeState[FYIIntent].model_construct(
        state_vector=StateVectorProfile.model_construct(immutable_matrix={}, mutable_matrix={}, is_delta=False),
        payload=intent,
        trace_context=TraceContextState.model_construct(trace_cid="a" * 64, span_cid="b" * 64),
    )

    result_bytes = DeterministicTransportAdapter.serialize_envelope(envelope)
    result_dict = json.loads(result_bytes.decode("utf-8"))

    assert result_dict["jsonrpc"] == "2.0"
    assert result_dict["method"] == "coreason_execute"
    assert result_dict["id"] == "a" * 64
    assert "params" in result_dict
    assert "trace_context" in result_dict["params"]
    assert result_dict["params"]["trace_context"]["trace_cid"] == "a" * 64


def test_serialize_envelope_missing_trace_cid() -> None:
    intent = FYIIntent()
    envelope = ExecutionEnvelopeState[FYIIntent].model_construct(
        state_vector=StateVectorProfile.model_construct(immutable_matrix={}, mutable_matrix={}, is_delta=False),
        payload=intent,
        trace_context=TraceContextState.model_construct(  # type: ignore[call-arg]
            span_cid="c" * 64
        ),  # No trace_cid
    )

    result_bytes = DeterministicTransportAdapter.serialize_envelope(envelope)
    result_dict = json.loads(result_bytes.decode("utf-8"))

    assert result_dict["id"] == "unknown"


def test_serialize_envelope_missing_trace_context() -> None:
    intent = FYIIntent()
    envelope = ExecutionEnvelopeState[FYIIntent].model_construct(  # type: ignore[call-arg]
        state_vector=StateVectorProfile.model_construct(immutable_matrix={}, mutable_matrix={}, is_delta=False),
        payload=intent,
        # No trace_context provided
    )

    result_bytes = DeterministicTransportAdapter.serialize_envelope(envelope)
    result_dict = json.loads(result_bytes.decode("utf-8"))

    assert result_dict["id"] == "unknown"
    assert "trace_context" not in result_dict["params"]
