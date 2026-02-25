# Orchestration Schemas: The Polymorphic Vertices

The `coreason-manifest` architecture uses a strictly typed system of **Nodes** to construct cognitive workflows. Each node represents a specific functional block—whether it is an LLM call, a logical branch, or a human interaction point.

These nodes are **polymorphic**: they all inherit from the base `Node` schema, sharing common properties like `id`, `metadata`, and `resilience` policies, but each defines its own specialized configuration.

---

## 1. `AgentNode`
The primary workhorse of any cognitive system. An `AgentNode` represents a single cognitive profile executing a task.

*   **Role:** Performs reasoning, tool usage, and content generation.
*   **Key Property:** **`profile`**. This defines *who* is acting. It can be an inline definition or a reference to a shared `CognitiveProfile` (e.g., "Researcher", "Editor").
*   **Tools:** A list of tool names available to this agent for the specific step.

```python
AgentNode(
    id="research_step",
    profile="researcher_profile_v1",
    tools=["web_search", "calculator"]
)
```

---

## 2. `SwitchNode`
A purely logical node used for conditional routing. It evaluates the state of the Blackboard without invoking an LLM, making it fast and deterministic.

*   **Role:** Directs execution flow based on a variable's value.
*   **Key Property:** **`cases`**. A dictionary mapping potential variable values to target node IDs.
*   **Default:** A mandatory fallback route if no case matches.

```python
SwitchNode(
    id="route_by_topic",
    variable="user_topic",
    cases={
        "finance": "finance_agent",
        "tech": "tech_agent"
    },
    default="general_agent"
)
```

---

## 3. `HumanNode`
A node schema that explicitly pauses execution to await external input. This is critical for **Human-in-the-Loop (HITL)** workflows.

*   **Role:** Suspends the graph until a human provides approval, feedback, or data.
*   **Key Property:** **`interaction_mode`**.
    *   `blocking`: The graph waits indefinitely (or until timeout).
    *   `shadow`: The graph proceeds automatically after a timeout, allowing for "passive approval."
    *   `steering`: Allows mid-flight alteration of the plan.
*   **Schema:** Can enforce strict JSON Schema validation on the human's input.

---

## 4. `PlannerNode`
A specialized node configured to decompose a high-level goal into a structured plan.

*   **Role:** Generates a dynamic list of sub-tasks or a sub-graph based on the objective.
*   **Key Property:** **`output_schema`**. Defines the strict structure of the generated plan (e.g., a list of steps with dependencies).
*   **Goal:** The natural language objective guiding the decomposition.

---

## 5. `SwarmNode`
Represents a multi-agent topology where multiple cognitive profiles collaborate simultaneously.

*   **Role:** Spawns strictly parallel execution units (a "swarm") to process a workload.
*   **Key Property:** **`distribution_strategy`**.
    *   `sharded`: Splits a dataset across workers.
    *   `replicated`: Runs the same task multiple times for consensus.
*   **Aggregation:** Defines how the results from N workers are combined (e.g., `vote`, `concat`, `summarize`).

```python
SwarmNode(
    id="parallel_research",
    worker_profile="researcher",
    workload_variable="urls_to_scrape",
    distribution_strategy="sharded",
    max_concurrency=10
)
```

---

## 6. `InspectorNode` & `EmergenceInspectorNode`
Governance and supervision nodes used to evaluate the quality, safety, and integrity of the workflow.

### `InspectorNode`
*   **Role:** Evaluates a specific output variable against defined criteria.
*   **Modes:**
    *   `programmatic`: Uses regex or numeric thresholds (fast, deterministic).
    *   `semantic`: Uses an LLM Judge to evaluate complex qualities like "tone" or "accuracy."

### `EmergenceInspectorNode`
*   **Role:** Monitors the graph for complex, emergent behaviors that may arise from multi-agent interactions.
*   **Key Property:** **`detect_deception`**, **`detect_power_seeking`**. Flags specific high-risk behavioral markers.
*   **Requirement:** Always operates in `semantic` mode with a strong reasoning model.

---

## 7. `PlaceholderNode`
A structural stub used during graph development.

*   **Role:** Allows architects to define the topology and connections of a graph before the actual logic or prompts are implemented.
*   **Usage:** Useful for "sketching" the flow. The validation layer accepts it as a valid node, but the runtime will raise a clear error if execution reaches it.
