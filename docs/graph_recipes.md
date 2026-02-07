# Orchestration: Graph Recipes

Coreason V2 introduces **Graph Recipes**, replacing linear workflows with a robust **Directed Cyclic Graph (DCG)** architecture. This allows for complex orchestration patterns including loops, conditional branching, and human-in-the-loop interactions.

## Concept: Graphs, Not Lists

In V1 (and `ManifestV2`), workflows were simple lists of steps. In V2 Graph Recipes, a `RecipeDefinition` contains a `GraphTopology`.
A Topology is a collection of **Nodes** connected by **Edges**.

*   **Nodes**: The "Workers" (Agents, Humans, Routers).
*   **Edges**: The "Control Flow" (Next Step).
*   **Entry Point**: Where execution begins.

This structure allows for **Cycles** (loops), enabling agents to self-correct or retry tasks until a condition is met.

## Syntactic Sugar: Task Sequences (New in 0.22.0)

While Graphs are powerful, they can be verbose for simple linear workflows. To simplify this, `RecipeDefinition` supports **Task Sequences**.

You can pass a simple list of nodes (or a dictionary with a `"steps"` key) to the `topology` field, and the library will automatically:
1.  Set the first node as the `entry_point`.
2.  Create linear edges connecting each node to the next (A -> B -> C).
3.  Compile it into a full `GraphTopology` object.

### Example: Linear Sequence

```python
from coreason_manifest.spec.v2.recipe import RecipeDefinition, AgentNode, HumanNode

# Define nodes linearly
step1 = AgentNode(id="research", agent_ref="researcher")
step2 = HumanNode(id="approve", prompt="Approve?")
step3 = AgentNode(id="publish", agent_ref="publisher")

# Pass as a list
recipe = RecipeDefinition(
    ...
    topology=[step1, step2, step3]  # Automatically converts to GraphTopology
)

# Resulting Topology:
# Nodes: [research, approve, publish]
# Edges: research -> approve, approve -> publish
# Entry Point: research
```

## Recipe Components

A `RecipeDefinition` is composed of four key layers:

1.  **Interface (Contract)**: Defines inputs and outputs.
2.  **State (Memory)**: Defines shared variables.
3.  **Policy (Governance)**: Defines execution limits.
4.  **Topology (Logic)**: Defines the graph structure.

### 1. The Interface Layer (`RecipeInterface`)
Defines the input/output contract for the Recipe using JSON Schema.

```python
interface=RecipeInterface(
    inputs={"user_input": {"type": "string"}},
    outputs={"final_report": {"type": "string"}}
)
```

### 2. The State Layer (`StateDefinition`)
Defines the shared memory structure (Blackboard) and persistence strategy.

```python
state=StateDefinition(
    properties={"draft": {"type": "string"}},
    persistence="ephemeral" # or "redis", "postgres"
)
```

### 3. The Policy Layer (`PolicyConfig`)
Sets execution limits and error handling strategies.

```python
policy=PolicyConfig(
    max_retries=3,
    timeout_seconds=3600,
    execution_mode="sequential" # or "parallel"
)
```

## The Graph Topology Schema (`GraphTopology`)

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

All nodes inherit from `RecipeNode`, which includes `id`, `metadata`, and `presentation` (UI layout).

1.  **`AgentNode`** (`type: agent`): Executes an AI Agent.
    - `agent_ref`: The ID or URI of the Agent Definition to execute.
    - `system_prompt_override`: Context-specific instructions (optional).
    - `inputs_map`: Mapping parent outputs to agent inputs (dict[str, str]).

2.  **`HumanNode`** (`type: human`): Suspends execution until a human provides input or approval.
    - `prompt`: Instruction for the human user.
    - `timeout_seconds`: SLA for approval (optional).
    - `required_role`: Role required to approve (e.g., manager) (optional).

3.  **`RouterNode`** (`type: router`): Evaluates a variable and branches execution to different target nodes.
    - `input_key`: The variable to evaluate (e.g., 'classification').
    - `routes`: Map of value -> target_node_id.
    - `default_route`: Fallback target_node_id.

4.  **`EvaluatorNode`** (`type: evaluator`): Executes an LLM-as-a-Judge evaluation loop, providing scores and critiques to optimize content.
    - `target_variable`: The key in the shared state/blackboard containing the content to evaluate.
    - `evaluator_agent_ref`: Reference to the Agent Definition ID that will act as the judge.
    - `evaluation_profile`: Inline criteria definition or a reference to a preset profile.
    - `pass_threshold`: The score (0.0-1.0) required to proceed.
    - `max_refinements`: Maximum number of loops allowed before forcing a generic fail/fallback.
    - `pass_route`: Node ID to go to if score >= threshold.
    - `fail_route`: Node ID to go to if score < threshold.
    - `feedback_variable`: The key in the state where the critique/reasoning will be written.

## Evaluator-Optimizer Workflow

Coreason V2 natively supports the **Evaluator-Optimizer** pattern (popularized by Anthropic's Claude Cookbook). This pattern uses a dedicated `EvaluatorNode` to critique the output of a Generator agent and loop back for refinements until a quality threshold is met.

### Example: Writer + Editor Loop

```yaml
topology:
  nodes:
    # 1. The Generator
    - type: agent
      id: "writer"
      agent_ref: "copywriter-v1"
      inputs_map:
        topic: "user_topic"
        critique: "critique_history"  # Receives feedback from the Evaluator

    # 2. The Evaluator-Optimizer
    - type: evaluator
      id: "editor-check"
      target_variable: "writer_output" # The content to grade
      evaluator_agent_ref: "editor-llm" # The judge
      evaluation_profile: "standard-critique" # The criteria

      # Logic
      pass_threshold: 0.9
      max_refinements: 3

      # Feedback Output
      feedback_variable: "critique_history"

      # Control Flow
      pass_route: "publish"
      fail_route: "writer" # Loops back to Generator for refinement

    # 3. Success State
    - type: agent
      id: "publish"
      agent_ref: "publisher-v1"
```

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
