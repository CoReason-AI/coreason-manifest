# Core Primitives: Nodes

Nodes are the fundamental processing units of a cognitive flow. They represent the *intent* and *configuration* of a task, leaving the runtime execution details entirely abstract.

## NodeBase

All nodes inherit from `NodeBase`, which establishes the minimum required metadata for any node in the graph.

*   **`id`**: Unique identifier (alphanumeric, URL-safe).
*   **`type`**: The node type discriminator (e.g., `agent`, `switch`).
*   **`description`**: Human-readable explanation of the node's purpose.
*   **`metadata`**: Arbitrary dictionary for runtime-specific configuration.
*   **`resilience`**: Reference to a `ResilienceConfig` (retries, fallbacks).

## Node Types

The architecture supports a polymorphic set of node types through the `AnyNode` discriminated union.

### AgentNode

The primary workhorse of the system. An `AgentNode` executes a cognitive task using a specific **Cognitive Profile** (persona + reasoning engine).

*   **Type**: `agent`
*   **Profile**: A `CognitiveProfile` object defining the role and persona.
*   **Tools**: A list of tool names available to this agent.

### SwitchNode

A deterministic routing node. It inspects a variable on the Blackboard and directs execution to one of several output paths based on strict value matching.

*   **Type**: `switch`
*   **Variable**: The Blackboard variable ID to evaluate.
*   **Cases**: A map of `value -> next_node_id`.
*   **Default**: The fallback node ID if no case matches.

### PlannerNode

A node dedicated to high-level goal decomposition. It generates a structured plan (list of steps) based on a goal description.

*   **Type**: `planner`
*   **Goal**: The natural language goal to decompose.
*   **Output Schema**: The JSON Schema defining the structure of the generated plan.

### SwarmNode

A powerful primitive for parallel processing. A `SwarmNode` spawns multiple ephemeral worker agents to process a dataset or workload concurrently.

*   **Type**: `swarm`
*   **Worker Profile**: The `CognitiveProfile` ID for the ephemeral workers.
*   **Workload Variable**: The Blackboard variable (list) to distribute.
*   **Distribution Strategy**: `sharded` (split data) or `replicated` (same data, many attempts).
*   **Reducer Function**: How to aggregate results (`concat`, `vote`, `summarize`).

### HumanNode

An explicit pause for human-in-the-loop interaction. The flow halts execution at this node until a human provides input or approval.

*   **Type**: `human`
*   **Prompt**: The question or instruction for the human.
*   **Input Schema**: The JSON Schema for the expected response.
*   **Timeout**: Optional duration before proceeding automatically (if configured).

### InspectorNode & EmergenceInspectorNode

Specialized nodes for verification and systemic observation. They evaluate the output of other nodes against specific criteria.

*   **Type**: `inspector` / `emergence_inspector`
*   **Target Variable**: The variable to inspect.
*   **Criteria**: The evaluation rubric.
*   **Mode**: `programmatic` (regex/code) or `semantic` (LLM judge).
*   **EmergenceInspector**: Specifically configured to detect novel, high-risk behaviors (sycophancy, deception).

---

**Important Note**: These schemas define *what* the node is intended to do. They contain **zero** execution logic. The runtime engine is responsible for interpreting these configurations and performing the actual work (LLM calls, tool execution, etc.).
