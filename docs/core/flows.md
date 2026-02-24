# Core Primitives: Flows

The `coreason-manifest` architecture is built around the concept of **Topological Determinism**. An orchestration is strictly defined by its shape, which dictates the flow of execution.

This document details the high-level containers that organize cognitive nodes into executable workflows.

## FlowInterface

The `FlowInterface` is the universal contract for all flow types. It is a discriminated union that allows a manifest to be either a `LinearFlow` (sequential) or a `GraphFlow` (DAG/cyclic).

This polymorphism allows runtimes to treat all flows uniformly, inspecting the `type` field to determine the execution strategy.

## FlowMetadata

Every flow is wrapped in a standard metadata envelope. This ensures that every cognitive artifact is versioned, attributable, and searchable.

```json
{
  "name": "ResearchAssistant",
  "version": "1.0.0",
  "description": "A multi-step agent for web research.",
  "tags": ["research", "web", "production"],
  "created_at": "2023-10-27T10:00:00Z",
  "updated_at": "2023-10-27T12:00:00Z"
}
```

## The Blackboard

The `Blackboard` is the abstract shared memory space for a flow. It serves as the type-safe contract for inputs and outputs.

*   **Variables**: A dictionary of variable names to their values.
*   **Schemas**: A list of `DataSchema` objects that define the strict structure (JSON Schema) of the variables.

Nodes in the flow read from the Blackboard at the start of their execution and write back to it upon completion. This strictly decouples nodes from each other; they communicate only through the shared state.

## LinearFlow

`LinearFlow` represents the simplest possible topology: a sequential list of steps.

*   **Type**: `linear`
*   **Structure**: A list of `AnyNode` objects.
*   **Execution**: Step 1 -> Step 2 -> Step 3.
*   **Use Case**: Deterministic pipelines, data preprocessing, simple Q&A chains.

```json
{
  "type": "linear",
  "metadata": { ... },
  "sequence": [
    { "type": "agent", "id": "step1", ... },
    { "type": "agent", "id": "step2", ... }
  ]
}
```

## GraphFlow

`GraphFlow` represents the full power of the architecture: a Directed Acyclic Graph (DAG) or a cyclic graph with controlled loops.

*   **Type**: `graph`
*   **Structure**:
    *   `nodes`: A dictionary of `NodeID` to `AnyNode` objects.
    *   `edges`: A list of `Edge` objects defining the connections.
    *   `entry_point`: The `NodeID` where execution begins.
*   **Edges**:
    *   `from`: Source node ID.
    *   `to`: Target node ID.
    *   `condition`: An optional Python expression (strictly AST-validated) that determines if the edge should be traversed.

```json
{
  "type": "graph",
  "metadata": { ... },
  "graph": {
    "nodes": {
      "start": { "type": "agent", ... },
      "decide": { "type": "switch", ... },
      "end": { "type": "agent", ... }
    },
    "edges": [
      { "from": "start", "to": "decide" },
      { "from": "decide", "to": "end", "condition": "result == 'success'" }
    ],
    "entry_point": "start"
  }
}
```
