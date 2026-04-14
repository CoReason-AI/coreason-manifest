"""Tests for the DeterministicTransportAdapter msgspec serialization boundary."""

import json

from coreason_manifest.spec.ontology import (
    ExecutionEnvelopeState,
    StateVectorProfile,
    TraceContextState,
)
from coreason_manifest.utils.mcp_adapters import DeterministicTransportAdapter


def _make_minimal_envelope() -> ExecutionEnvelopeState:  # type: ignore[type-arg]
    """Build a minimal valid ExecutionEnvelopeState for serialization tests."""
    return ExecutionEnvelopeState(
        trace_context=TraceContextState(
            trace_cid="01JRWX5V6E8K3M2N4P7Q9R1S0T",
            span_cid="01JRWX5V6E8K3M2N4P7Q9R1S0W",
        ),
        state_vector=StateVectorProfile(),
        payload={},
    )


def test_serialize_envelope_returns_bytes() -> None:
    envelope = _make_minimal_envelope()
    result = DeterministicTransportAdapter.serialize_envelope(envelope)
    assert isinstance(result, bytes)


def test_serialize_envelope_is_valid_json_rpc() -> None:
    envelope = _make_minimal_envelope()
    raw = DeterministicTransportAdapter.serialize_envelope(envelope)
    parsed = json.loads(raw)
    assert parsed["jsonrpc"] == "2.0"
    assert parsed["method"] == "coreason_execute"
    assert "params" in parsed
    assert "id" in parsed


def test_serialize_envelope_deterministic() -> None:
    """Two identical envelopes must produce byte-identical output."""
    envelope_a = _make_minimal_envelope()
    envelope_b = _make_minimal_envelope()
    assert (
        DeterministicTransportAdapter.serialize_envelope(envelope_a)
        == DeterministicTransportAdapter.serialize_envelope(envelope_b)
    )


def test_serialize_envelope_excludes_none_values() -> None:
    """None values must be stripped to prevent Null Contagion."""
    envelope = _make_minimal_envelope()
    raw = DeterministicTransportAdapter.serialize_envelope(envelope)
    parsed = json.loads(raw)
    params = parsed["params"]

    def _assert_no_nones(obj: object) -> None:
        if isinstance(obj, dict):
            for v in obj.values():
                assert v is not None
                _assert_no_nones(v)
        elif isinstance(obj, list):
            for v in obj:
                assert v is not None
                _assert_no_nones(v)

    _assert_no_nones(params)


def test_serialize_envelope_sorted_keys() -> None:
    """Output keys must be lexicographically sorted for determinism."""
    envelope = _make_minimal_envelope()
    raw = DeterministicTransportAdapter.serialize_envelope(envelope)
    parsed = json.loads(raw)
    top_keys = list(parsed.keys())
    assert top_keys == sorted(top_keys)


def test_serialize_envelope_trace_cid_as_request_id() -> None:
    """The JSON-RPC 'id' field must be derived from the trace_context.trace_cid."""
    envelope = _make_minimal_envelope()
    raw = DeterministicTransportAdapter.serialize_envelope(envelope)
    parsed = json.loads(raw)
    assert parsed["id"] == "01JRWX5V6E8K3M2N4P7Q9R1S0T"
