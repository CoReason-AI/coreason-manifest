# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import concurrent.futures
import secrets
import time
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.state.events import BeliefUpdateEvent, ObservationEvent, SystemFaultEvent
from coreason_manifest.telemetry.custody import ExecutionNode
from coreason_manifest.telemetry.schemas import LogEnvelope, SpanTrace
from coreason_manifest.workflow.topologies import SwarmTopology

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
        event: Any = ObservationEvent(event_id=f"ev_{index}", timestamp=index * 1.5, payload={})
    elif index % 3 == 1:
        event = BeliefUpdateEvent(event_id=f"ev_{index}", timestamp=index * 1.5, payload={})
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


@given(
    spawning_threshold=st.integers(min_value=1, max_value=100),
    max_concurrent_agents=st.integers(min_value=1, max_value=100),
)
def test_swarm_deadlock_proof(spawning_threshold: int, max_concurrent_agents: int) -> None:
    """The Swarm Deadlock Proof."""
    if spawning_threshold > max_concurrent_agents:
        try:
            SwarmTopology(nodes={}, spawning_threshold=spawning_threshold, max_concurrent_agents=max_concurrent_agents)
            pytest.fail("Should have raised ValidationError")
        except ValidationError:
            pass
    else:
        # Should succeed
        SwarmTopology(nodes={}, spawning_threshold=spawning_threshold, max_concurrent_agents=max_concurrent_agents)


def _writer_thread(idx: int, shared_list: list[ExecutionNode]) -> None:
    """Generate deeply nested ExecutionNode payloads."""
    # S311 compliant generator for jitter
    rng = secrets.SystemRandom()
    for j in range(200):
        time.sleep(rng.uniform(0, 0.001))

        node = ExecutionNode(
            request_id=f"req_{idx}_{j}",
            inputs={"nested": {"data": [1, 2, 3], "idx": idx, "j": j}},
            outputs={"result": f"out_{idx}", "nested": [{"a": 1}, {"b": 2}]},
            parent_hashes=[f"parent_{idx}"],
        )

        # Introduce jitter
        time.sleep(rng.uniform(0, 0.001))
        shared_list.append(node)

        # Verify post-instantiation mutation is blocked
        try:
            node.outputs = {"mutated": True}  # type: ignore
            raise AssertionError("Should have raised exception due to frozen config")
        except ValidationError:
            # Pydantic V2 raises ValidationError on frozen model mutation
            pass
        except Exception as e:
            # If any other exception besides ValidationError is raised, it's fine as long as mutation is blocked
            if isinstance(e, AssertionError):
                raise


def _reader_thread(_idx: int, shared_list: list[ExecutionNode]) -> None:
    """Read and hash ExecutionNode payloads."""
    rng = secrets.SystemRandom()
    for _ in range(200):
        time.sleep(rng.uniform(0, 0.001))

        # Wait until there are items in the list to read
        for _wait in range(10):
            if shared_list:
                break
            time.sleep(0.001)

        if not shared_list:
            continue

        # Pick a random element from the currently available nodes
        try:
            node = rng.choice(shared_list)
            # Attempt to read and canonicalize hashes
            h1 = node.node_hash
            time.sleep(rng.uniform(0, 0.001))
            h2 = node.generate_node_hash()

            assert h1 == h2, "Hash mismatch"
        except IndexError:
            pass


def test_thread_weaver_stress_test() -> None:
    """The NoGIL Thread-Weaver Stress Test."""
    num_threads = 100
    shared_nodes: list[ExecutionNode] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            if i % 2 == 0:
                # 50 writers
                futures.append(executor.submit(_writer_thread, i, shared_nodes))
            else:
                # 50 readers
                futures.append(executor.submit(_reader_thread, i, shared_nodes))

        # Wait for all futures to complete, asserting no exceptions were raised
        for future in concurrent.futures.as_completed(futures):
            future.result()  # This will re-raise any exception caught in the thread
