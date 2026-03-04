# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import concurrent.futures
from typing import Any

from pydantic import TypeAdapter

from coreason_manifest.state.events import BeliefUpdateEvent, ObservationEvent, SystemFaultEvent
from coreason_manifest.telemetry.schemas import LogEnvelope, SpanTrace

log_adapter = TypeAdapter(LogEnvelope)
span_adapter = TypeAdapter(SpanTrace)
obs_adapter = TypeAdapter(ObservationEvent)
belief_adapter = TypeAdapter(BeliefUpdateEvent)
fault_adapter = TypeAdapter(SystemFaultEvent)


def instantiate_and_hash(index: int) -> tuple[int, int, int]:
    # LogEnvelope
    log = LogEnvelope(
        timestamp=index * 1.5,
        level="INFO" if index % 2 == 0 else "WARNING",
        message=f"Log message {index}",
        metadata={"idx": index},
    )
    h_log = hash(log)

    # SpanTrace
    span = SpanTrace(
        span_id=f"span_{index}",
        start_time=index * 1.5,
        status="OK" if index % 3 != 0 else "ERROR",
        metadata={"idx": index},
    )
    h_span = hash(span)

    # StateEvent
    if index % 3 == 0:
        event: Any = ObservationEvent(event_id=f"ev_{index}", timestamp=index * 1.5)
    elif index % 3 == 1:
        event = BeliefUpdateEvent(event_id=f"ev_{index}", timestamp=index * 1.5)
    else:
        event = SystemFaultEvent(event_id=f"ev_{index}", timestamp=index * 1.5)

    h_event = hash(event)

    return h_log, h_span, h_event


def test_massive_concurrency() -> None:
    num_tasks = 10000
    max_workers = 32

    results: list[tuple[int, int, int]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(instantiate_and_hash, i): i for i in range(num_tasks)}

        results.extend(future.result() for future in concurrent.futures.as_completed(futures))

    assert len(results) == num_tasks
    # If it completed without exceptions/deadlocks, the test passes
