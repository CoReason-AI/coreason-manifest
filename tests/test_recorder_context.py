import uuid
from datetime import datetime

from coreason_manifest.spec.core.governance import Audit, Governance, Safety
from coreason_manifest.spec.interop.telemetry import NodeState
from coreason_manifest.utils.recorder import create_recorder

# Helper for tests that require payload logging to verify hash sensitivity
ALLOW_LOGS_GOV = Governance(
    safety=Safety(input_filtering=True, pii_redaction=True, content_safety="medium"),
    audit=Audit(trace_retention_days=7, log_payloads=True),
)


def test_explicit_context() -> None:
    recorder = create_recorder(None)
    req_id = str(uuid.uuid4())
    root_id = str(uuid.uuid4())
    parent_id = str(uuid.uuid4())
    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    tracestate = "rojo=00f067aa0ba902b7"

    exec1 = recorder.record(
        node_id="test_node_1",
        state=NodeState.COMPLETED,
        inputs={"a": 1},
        outputs={"b": 2},
        duration_ms=100.0,
        parent_hashes=[],
        request_id=req_id,
        root_request_id=root_id,
        parent_request_id=parent_id,
        traceparent=traceparent,
        tracestate=tracestate,
    )

    assert exec1.request_id == req_id
    assert exec1.root_request_id == root_id
    assert exec1.parent_request_id == parent_id
    assert exec1.traceparent == traceparent
    assert exec1.tracestate == tracestate


def test_default_behavior() -> None:
    recorder = create_recorder(None)
    exec2 = recorder.record(
        node_id="test_node_2",
        state=NodeState.COMPLETED,
        inputs={"a": 1},
        outputs={"b": 2},
        duration_ms=100.0,
        parent_hashes=[],
    )

    assert exec2.request_id is not None
    assert exec2.root_request_id is not None
    assert exec2.request_id == exec2.root_request_id


def test_hash_sensitivity() -> None:
    # Use governance that enables logging, otherwise inputs are replaced with omission marker
    # and hashes collide because the payloads become identical.
    recorder = create_recorder(ALLOW_LOGS_GOV)
    req_id = str(uuid.uuid4())
    root_id = str(uuid.uuid4())
    ts = datetime.now()

    exec3a = recorder.record(
        node_id="test_node_3",
        state=NodeState.COMPLETED,
        inputs={"a": 1},
        outputs={"b": 2},
        duration_ms=100.0,
        parent_hashes=[],
        timestamp=ts,
        request_id=req_id,
        root_request_id=root_id,
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    )

    exec3b = recorder.record(
        node_id="test_node_3",
        state=NodeState.COMPLETED,
        inputs={"a": 1},  # Same inputs
        outputs={"b": 2},
        duration_ms=100.0,
        parent_hashes=[],
        timestamp=ts,
        request_id=req_id,
        root_request_id=root_id,
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-02",  # Different trace context
    )

    # Hash should be different because traceparent is part of the hashed payload
    assert exec3a.execution_hash != exec3b.execution_hash


def test_hash_stability() -> None:
    recorder = create_recorder(ALLOW_LOGS_GOV)
    req_id = str(uuid.uuid4())
    root_id = str(uuid.uuid4())
    ts = datetime.now()

    exec3a = recorder.record(
        node_id="test_node_3",
        state=NodeState.COMPLETED,
        inputs={"a": 1},
        outputs={"b": 2},
        duration_ms=100.0,
        parent_hashes=[],
        timestamp=ts,
        request_id=req_id,
        root_request_id=root_id,
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    )

    exec3c = recorder.record(
        node_id="test_node_3",
        state=NodeState.COMPLETED,
        inputs={"a": 1},
        outputs={"b": 2},
        duration_ms=100.0,
        parent_hashes=[],
        timestamp=ts,
        request_id=req_id,
        root_request_id=root_id,
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    )
    assert exec3a.execution_hash == exec3c.execution_hash
