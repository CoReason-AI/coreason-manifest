from typing import Any

from pytest_benchmark.fixture import BenchmarkFixture

from coreason_manifest.spec.ontology import ExecutionNodeReceipt


def test_benchmark_merkle_trace_hashing(benchmark: BenchmarkFixture) -> None:
    """
    AGENT INSTRUCTION: Mathematically prove that canonical hashing of execution
    nodes does not exceed bounded latency thresholds.
    """
    # Setup a heavy payload to stress the dictionary recursion bounds
    # using 100 to avoid dictionary size bounds limits.
    payload: dict[str, Any] = {"k" + str(i): "v" * 100 for i in range(100)}
    node = ExecutionNodeReceipt(
        request_id="req_bench_1",
        inputs=payload,
        outputs=payload,
        parent_hashes=["a" * 64, "b" * 64],
    )

    # Benchmark the canonical JSON dump and SHA-256 generation
    result = benchmark(node.generate_node_hash)

    assert len(result) == 64
