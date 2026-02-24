# Orchestration Schemas: Defining Flows

In the `coreason-manifest` architecture, a **Flow** is the top-level container that defines a complete cognitive workflow. It encapsulates the topology, the data contracts, and the governance policies required to execute a complex task.

The manifest provides two primary flow schemas:
1.  **`GraphFlow`**: For complex, non-linear Directed Acyclic Graphs (DAGs).
2.  **`LinearFlow`**: For strictly sequential, step-by-step execution.

All flow definitions are strict Pydantic models (`CoreasonModel`), ensuring that every blueprint is valid, immutable, and serializable before execution begins.

---

## `FlowInterface` & `Blackboard`

Every flow is grounded in a strict data contract. Data does not float abstractly; it must be explicitly defined in the `FlowInterface` and stored in the `Blackboard`.

### `FlowInterface`
The `FlowInterface` defines the boundary of the system—what goes in and what comes out. It serves as the API signature for the agent.

*   **`inputs`**: A dictionary or JSON Schema defining the required arguments to start the flow.
*   **`outputs`**: A dictionary or JSON Schema defining the structure of the final result returned to the caller.

### `Blackboard`
The `Blackboard` represents the shared state memory of the flow. During execution, nodes read from and write to this central repository.

*   **`variables`**: A dictionary mapping variable names to their initial values or definitions.
*   **`schemas`**: A list of `DataSchema` objects that enforce strict typing on blackboard variables, ensuring that nodes do not corrupt shared state with malformed data.

---

## `LinearFlow`

The `LinearFlow` schema is optimized for simplicity. It represents a pipeline where execution proceeds strictly from one step to the next, without branching or conditional logic.

**Key Structure:**
*   **`steps`** (alias `sequence`): An ordered list of `AnyNode` objects.
*   **Execution Model:** The output of Step N is automatically available to Step N+1. If any step fails, the entire linear flow halts unless resilience policies are active.

```python
# Conceptual Example
flow = LinearFlow(
    metadata=FlowMetadata(name="Simple Chain", version="1.0.0"),
    steps=[
        AgentNode(id="step_1", ...),
        AgentNode(id="step_2", ...),
    ]
)
```

---

## `GraphFlow`

The `GraphFlow` is the primary schema for defining sophisticated cognitive agents. It allows for arbitrary topologies, including parallel execution, conditional branching, and complex routing paths (within the constraints of a DAG).

The topology is defined within the **`graph`** attribute.

### 1. `nodes`
A dictionary mapping unique string **Node IDs** to their corresponding **Node** configurations.
*   **Type Safety:** The dictionary values are polymorphic (`AnyNode`), allowing any valid node type (`AgentNode`, `SwitchNode`, etc.) to be placed in the graph.
*   **Uniqueness:** Node IDs must be unique within the flow scope.

### 2. `edges`
A list of **Edge** objects defining the routing logic between nodes.

*   **`from_node`**: The ID of the source node.
*   **`to_node`**: The ID of the target node.
*   **`condition`**: An optional string containing a Python expression.

#### AST Condition Validation
To ensure safety and determinism, edge conditions are **strictly validated** using Python's Abstract Syntax Tree (AST).
*   **Allowed Operations:** The schema permits only safe operations: comparisons (`==`, `>`, `in`), boolean logic (`and`, `or`, `not`), and variable access.
*   **Forbidden:** Function calls, imports, loop constructs, and assignments are strictly rejected at the schema level.
*   **Mechanism:** When an edge has a condition, the runtime evaluates it against the current `Blackboard` state. If the condition evaluates to `True`, the edge is traversed.

### 3. `entry_point`
A strict requirement defining the starting `Node ID` of the graph. Execution always begins here. The validator ensures that the `entry_point` references a valid, existing node in the `nodes` dictionary.

```python
# Conceptual Example
graph = Graph(
    nodes={
        "start": AgentNode(...),
        "router": SwitchNode(...),
        "worker_a": AgentNode(...),
        "worker_b": AgentNode(...)
    },
    edges=[
        Edge(from_node="start", to_node="router"),
        Edge(from_node="router", to_node="worker_a", condition="topic == 'tech'"),
        Edge(from_node="router", to_node="worker_b", condition="topic == 'finance'")
    ],
    entry_point="start"
)
```
