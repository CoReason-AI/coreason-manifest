# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Any

from coreason_manifest import EpistemicLedger, ExecutionSpan, ObservationEvent, SpanEvent


def test_epistemic_ledger_hash_o1_tripwire(benchmark: Any) -> None:
    ledger = EpistemicLedger(
        history=[
            ObservationEvent(event_id=f"ev_{i}", timestamp=float(i), payload={"key": "value"}) for i in range(10000)
        ]
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
