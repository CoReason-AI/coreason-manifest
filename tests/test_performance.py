from typing import Any

from coreason_manifest.state import EpisodicTraceMemory
from coreason_manifest.state.events import ObservationEvent
from coreason_manifest.telemetry.schemas import ExecutionSpan, SpanEvent


def test_epistemic_ledger_hash_o1_tripwire(benchmark: Any) -> None:
    ledger = EpisodicTraceMemory(
        trace_id="t1",
        node_id="did:web:1",
        parent_hash="p1",
        merkle_root="m1",
        events=[
            ObservationEvent(event_id=f"ev_{i}", timestamp=float(i), payload={"key": "value"}) for i in range(10000)
        ],
    )
    _ = hash(ledger)
    benchmark(lambda: [hash(ledger) for _ in range(1000)])
    assert benchmark.stats.stats.max < 0.20


def test_execution_span_sorting_o1_tripwire(benchmark: Any) -> None:
    span = ExecutionSpan(
        trace_id="t1",
        span_id="s1",
        name="span",
        start_time_unix_nano=0,
        events=[SpanEvent(name=f"ev_{i}", timestamp_unix_nano=10000 - i) for i in range(10000)],
    )
    _ = hash(span)
    benchmark(lambda: [hash(span) for _ in range(1000)])
    assert benchmark.stats.stats.max < 0.20
