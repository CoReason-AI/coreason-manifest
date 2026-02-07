# Orchestration: Graph Recipes

Coreason V2 introduces **Graph Recipes**, replacing linear workflows with a robust **Directed Cyclic Graph (DCG)** architecture. This allows for complex orchestration patterns including loops, conditional branching, and human-in-the-loop interactions.

## Concept: Graphs, Not Lists

In V1, workflows were simple lists of steps. In V2, a `RecipeDefinition` contains a `GraphTopology`.
A Topology is a collection of **Nodes** connected by **Edges**.

*   **Nodes**: The "Workers" (Agents, Humans, Routers).
*   **Edges**: The "Control Flow" (Next Step).
*   **Entry Point**: Where execution begins.

This structure allows for **Cycles** (loops), enabling agents to self-correct or retry tasks until a condition is met.

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
