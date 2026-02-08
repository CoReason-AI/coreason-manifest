# Reference Graph Executor

The `GraphExecutor` class (located in `coreason_manifest.utils.simulation_executor`) is a **reference implementation** of the Coreason Runtime architecture. It is designed primarily for **simulation, testing, and graph validation**, providing a working baseline for the "Passive Definition, Active Execution" principle.

> **Note:** For the complete set of architectural mandates for production runtimes (including Middleware, Multiplexed Streams, and Provenance), please refer to the [Runtime Principles](runtime_principles.md).

## Overview

The executor implements a **Blackboard Architecture** where all nodes read from and write to a shared state (`context`). It traverses the `RecipeDefinition` topology, executing nodes sequentially until a terminal state is reached or a safety limit is exceeded.

### Key Responsibilities

1.  **Graph Traversal**: Navigates the Directed Cyclic Graph (DCG) using explicit edges and `RouterNode` logic.
2.  **State Management**: Manages the Blackboard (`dict[str, Any]`), handling `inputs_map` variable resolution.
3.  **Simulation & Tracing**: Produces a standardized `SimulationTrace` containing `SimulationStep` objects with full state snapshots (implementing [Principle 8](runtime_principles.md)).

## The Blackboard Model

The `context` is a dictionary that accumulates state throughout the lifecycle.

*   **Initialization**: Populated from the `initial_state` provided at runtime.
*   **Input Mapping**: `AgentNode.inputs_map` defines how to extract specific variables for an agent.
    *   *Example:* `{"query": "user_input"}` maps `context["user_input"]` to the agent's `query` argument.
*   **Output Merging**: When a node completes, its output is merged back into the Blackboard.
    *   *Example:* `context.update(agent_output)`

## Supported Node Types

The reference implementation currently supports the following nodes:

### AgentNode
*   **Behavior**: Simulates an AI Agent execution. In this reference implementation, it mocks the output rather than calling an LLM.
*   **Step Type**: `TOOL_EXECUTION`.

### HumanNode
*   **Behavior**: Pauses execution to request input from the user (via CLI `input()` in this implementation).
*   **Step Type**: `INTERACTION`.

### RouterNode
*   **Behavior**: Evaluates a blackboard variable (`input_key`) against a map of `routes`.
*   **Logic**:
    1.  Resolve `value = context[node.input_key]`.
    2.  Match `value` against keys in `node.routes`.
    3.  Transition to the matching node ID, or `default_route` if no match.
*   **Step Type**: `REASONING`.

> **Implementation Gap:** The `EvaluatorNode` (for self-correction loops) is defined in the specification but not yet implemented in this reference executor.

## Safety & Limits

### Infinite Loop Protection
To prevent runaway execution in cyclic graphs, the executor enforces a hard `max_steps` limit (default: 50).

> **Production Note:** A production-grade runtime must strictly enforce the `PolicyConfig` defined in the recipe (e.g., `timeout_seconds`, `max_retries`) and perform "Pre-Flight" feasibility checks (`RecipeDefinition.check_feasibility`) before execution.

## Usage Example

```python
from coreason_manifest.utils.simulation_executor import GraphExecutor
from coreason_manifest.spec.v2.recipe import RecipeDefinition

# 1. Load a Recipe
recipe = RecipeDefinition.model_validate(...)

# 2. Define Initial State
initial_state = {"user_input": "Hello World"}

# 3. Initialize Executor
executor = GraphExecutor(recipe, initial_state)

# 4. Run Simulation
trace = await executor.run()

# 5. Inspect Trace
for step in trace.steps:
    print(f"[{step.node_id}] {step.thought or ''}")
```
