from coreason_manifest.state import EpistemicLedger
from coreason_manifest.state.events import ObservationEvent
from coreason_manifest.telemetry.schemas import ExecutionSpan, SpanEvent


def test_epistemic_ledger_hash_o1_tripwire(benchmark):
    ledger = EpistemicLedger(
        history=[
            ObservationEvent(event_id=f"ev_{i}", timestamp=float(i), payload={"key": "value"}) for i in range(10000)
        ]
    )
    _ = hash(ledger)
    benchmark(lambda: [hash(ledger) for _ in range(1000)])
    assert benchmark.stats.stats.max < 0.05


def test_execution_span_sorting_o1_tripwire(benchmark):
    span = ExecutionSpan(
        trace_id="t1",
        span_id="s1",
        name="span",
        start_time_unix_nano=0,
        events=[SpanEvent(name=f"ev_{i}", timestamp_unix_nano=10000 - i) for i in range(10000)],
    )
    _ = hash(span)
    benchmark(lambda: [hash(span) for _ in range(1000)])
    assert benchmark.stats.stats.max < 0.05
