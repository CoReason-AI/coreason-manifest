# Graph Executor Architecture

The `GraphExecutor` is the runtime engine responsible for traversing the `RecipeDefinition` graph and managing the execution state. It implements a **Blackboard Architecture** where all nodes share a common context.

## Overview

The executor operates by maintaining an execution pointer (`current_node_id`) and a state dictionary (`context`). It loops until a terminal node is reached or a safety limit (`max_steps`) is exceeded.

### Key Responsibilities

1.  **Graph Traversal**: Navigating nodes based on topology and routing logic.
2.  **State Management**: Mapping inputs from the Blackboard to nodes, and merging outputs back.
3.  **Execution Simulation**: Invoking (or mocking) the logic for each node type.
4.  **Tracing**: Recording every step in a `SimulationTrace`.

## The Blackboard Model

The `context` (Blackboard) is a dictionary `dict[str, Any]` that accumulates state throughout the execution.

*   **Initial State**: Populated from `recipe.interface.inputs`.
*   **Input Mapping**: `AgentNode.inputs_map` defines how to extract data from the Blackboard for a specific agent.
    *   Example: `{"query": "user_input"}` maps `context["user_input"]` to the agent's `query` argument.
*   **Output Merging**: When a node completes, its entire output dictionary is updated into the Blackboard.
    *   Example: `context.update(agent_output)`

## Node Execution

### AgentNode
*   **Action**: Executes an AI Agent (simulated in the reference implementation).
*   **Input**: Derived from Blackboard via `inputs_map`.
*   **Output**: Merged into Blackboard.
*   **Step Type**: `TOOL_EXECUTION`.

### HumanNode
*   **Action**: Pauses for human input (CLI prompt in reference implementation).
*   **Input**: `prompt` string.
*   **Output**: User response, merged into Blackboard.
*   **Step Type**: `INTERACTION`.

### RouterNode
*   **Action**: Evaluates a variable for branching.
*   **Input**: `input_key` from Blackboard.
*   **Output**: Routing decision (target node ID).
*   **Logic**:
    1.  Read `value = context[node.input_key]`.
    2.  Check `node.routes` for `value`.
    3.  If match, return target ID.
    4.  Else, return `node.default_route`.
*   **Step Type**: `REASONING`.

## Safety Mechanisms

### Infinite Loop Protection
To prevent runaway execution in cyclic graphs (loops), the executor enforces a strict `max_steps` limit (default: 50). This ensures that even if a loop condition is never met, the process will terminate.

### Validation
The executor validates the initial state against the `RecipeInterface` (if strict validation is enabled) and ensures that traversed nodes exist in the topology.

## Usage

```python
from coreason_manifest.runtime.executor import GraphExecutor
from coreason_manifest.spec.v2.recipe import RecipeDefinition

# Load Recipe
recipe = ...

# Initialize State
initial_state = {"user_input": "Hello World"}

# Execute
executor = GraphExecutor(recipe, initial_state)
trace = await executor.run()

# Inspect Result
print(trace.steps)
print(executor.context)
```
