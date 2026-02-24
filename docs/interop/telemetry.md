# Interoperability: Telemetry & Lineage

The `coreason-manifest` architecture strictly enforces observability standards to ensure that every cognitive action is traceable, reproducible, and compliant.

The schemas in `src/coreason_manifest/spec/interop/telemetry.py` define the **Wire Protocol** for lineage. These are not merely internal logs; they are structured data contracts that allow distributed systems (e.g., a Go backend, a Python agent runner, and a React frontend) to share a unified view of execution.

---

## The `NodeExecution` Schema

The atomic unit of observability is the `NodeExecution`. It represents the complete lifecycle of a single node's attempt to run.

```python
class NodeExecution(AntibodyBase):
    node_id: str
    state: NodeState
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    traceparent: str | None
    tracestate: str | None
    execution_hash: str | None
```

### Lifecycle States (`NodeState`)
The `NodeState` enum strictly defines the valid lifecycle phases:
*   `PENDING`: Scheduled but not yet started.
*   `RUNNING`: Actively executing (e.g., waiting for LLM token stream).
*   `COMPLETED`: Successfully finished with valid outputs.
*   `FAILED`: Terminated due to an error (see `ErrorDomain`).
*   `SKIPPED`: Bypassed due to conditional logic or circuit breaking.

### W3C Trace Context
To ensure distributed tracing across microservices, the schema natively supports the **W3C Trace Context** standard.
*   **`traceparent`**: Captures the Trace ID and Parent Span ID. This allows an agent's internal thought process to be visualized as a span within a larger distributed transaction.
*   **`tracestate`**: Propagates vendor-specific lineage data.

---

## The `ExecutionSnapshot` Schema

An agent execution is rarely a single event; it is a sequence of steps. The `ExecutionSnapshot` is the top-level container that aggregates these atomic records.

*   **`node_states`**: A map of every node ID to its final state.
*   **`active_path`**: An ordered list of node IDs representing the actual path taken through the graph (ignoring skipped branches).

This snapshot allows for **Deterministic Replay**: by feeding the captured `inputs` from a snapshot back into the `GraphFlow`, the execution can be theoretically reproduced (assuming deterministic model settings).
