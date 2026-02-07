# Orchestration: Graph Recipes

Coreason V2 introduces **Graph Recipes**, replacing linear workflows with a robust **Directed Cyclic Graph (DCG)** architecture. This allows for complex orchestration patterns including loops, conditional branching, and human-in-the-loop interactions.

## Concept: Graphs, Not Lists

In V1, workflows were simple lists of steps. In V2, a `RecipeDefinition` contains a `GraphTopology`.
A Topology is a collection of **Nodes** connected by **Edges**.

*   **Nodes**: The "Workers" (Agents, Humans, Routers).
*   **Edges**: The "Control Flow" (Next Step).
*   **Entry Point**: Where execution begins.

This structure allows for **Cycles** (loops), enabling agents to self-correct or retry tasks until a condition is met.

## Recipe Components

A `RecipeDefinition` is composed of four key layers:

1.  **Interface (Contract)**: Defines inputs and outputs.
2.  **State (Memory)**: Defines shared variables.
3.  **Policy (Governance)**: Defines execution limits.
4.  **Topology (Logic)**: Defines the graph structure.

### 1. The Interface Layer
Defines the input/output contract for the Recipe using JSON Schema.

```python
interface=InterfaceDefinition(
    inputs={"user_input": {"type": "string"}},
    outputs={"final_report": {"type": "string"}}
)
```

### 2. The State Layer (Blackboard)
Defines the shared memory structure and persistence strategy.

```python
state=StateDefinition(
    properties={"draft": {"type": "string"}},
    persistence="ephemeral" # or "redis", "postgres"
)
```

### 3. The Policy Layer
Sets execution limits and error handling strategies.

```python
policy=PolicyConfig(
    max_retries=3,
    timeout_seconds=3600,
    execution_mode="sequential"
)
```

## The Graph Topology Schema

The `GraphTopology` enforces structural integrity. It requires a list of `nodes`, a list of `edges`, and a valid `entry_point`.

### JSON Example: Agent -> Human Handover

Here is a raw JSON example of a topology where an AI Agent performs a task, and then a Human Manager must approve it.

```json
{
  "entry_point": "research-task",
  "nodes": [
    {
      "type": "agent",
      "id": "research-task",
      "agent_ref": "researcher-v1",
      "inputs_map": {
        "topic": "user_query"
      }
    },
    {
      "type": "human",
      "id": "manager-approval",
      "prompt": "Review the research report. Approve to proceed?",
      "timeout_seconds": 86400,
      "required_role": "manager"
    }
  ],
  "edges": [
    {
      "source": "research-task",
      "target": "manager-approval",
      "condition": "on_success"
    }
  ]
}
```

### Node Types

1.  **`AgentNode`**: Executes an AI Agent.
2.  **`HumanNode`**: Suspends execution until a human provides input or approval.
3.  **`RouterNode`**: Evaluates a variable and branches execution to different target nodes.

## Integrity Validation

The `coreason-manifest` library performs strict validation on the graph topology to prevent runtime errors.

### 1. Dangling Edge Check
Every `source` and `target` in the `edges` list must correspond to a valid Node ID. If you try to connect to a node that doesn't exist, the validator will raise a `ValueError`.

### 2. Entry Point Check
The `entry_point` ID must exist in the `nodes` list. You cannot start a graph at a non-existent node.

### 3. Duplicate ID Check
All Node IDs must be unique within the topology.

```python
from coreason_manifest.spec.v2.recipe import GraphTopology, AgentNode, GraphEdge

try:
    # This will fail because 'phantom-node' does not exist
    topology = GraphTopology(
        entry_point="node-1",
        nodes=[AgentNode(id="node-1", agent_ref="agent-a")],
        edges=[GraphEdge(source="node-1", target="phantom-node")]
    )
except ValueError as e:
    print(f"Validation Error: {e}")
    # Output: Dangling edge target: node-1 -> phantom-node
```

## Runtime Execution

The `GraphExecutor` is responsible for traversing the `RecipeDefinition` and executing nodes.

### The Blackboard Architecture

Execution state is maintained in a shared **Blackboard** (`context`).
*   **Inputs Mapping**: When entering a node, data is mapped from the Blackboard to the Node's inputs using `inputs_map`.
*   **Output Merging**: When a node completes, its output is merged back into the Blackboard.

### Routing Logic

*   **Standard Edges**: If a node has a single outgoing edge matching its ID, execution proceeds to the target.
*   **Router Nodes**: `RouterNode` explicitly inspects a variable in the Blackboard (`input_key`) and selects the next node based on the `routes` map. If no match is found, it uses the `default_route`.

### Execution Limits

To prevent infinite loops in malformed graphs, the executor enforces a `max_steps` limit (default: 50). If the limit is reached, execution halts to protect resources.

### Trace Generation

The executor generates a `SimulationTrace` containing a list of `SimulationStep` objects, providing a full audit trail of the execution path, including inputs, outputs, and routing decisions.
