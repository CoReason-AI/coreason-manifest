# Flow Governance & Resilience

Coreason V2 introduces **Flow Governance** capabilities to `RecipeNode`, transforming the Recipe from a static DAG into a resilient State Machine. This allows nodes to define specific behaviors for failure scenarios, enabling the Runtime Engine to perform Self-Correction (e.g., retries, fallbacks) without crashing the entire workflow.

## Concepts

Flow Governance is configured via the `recovery` field on any `RecipeNode`. It dictates what happens when a node fails to execute or crashes.

### Key Primitives

1.  **`RecoveryConfig`**: The configuration object attached to a node.
2.  **`FailureBehavior`**: The strategy to employ when retries are exhausted.

## Configuration (`RecoveryConfig`)

```python
from coreason_manifest.spec.v2.recipe import (
    RecoveryConfig,
    FailureBehavior,
    AgentNode
)

# Define recovery settings
recovery = RecoveryConfig(
    max_retries=3,                  # Retry up to 3 times
    retry_delay_seconds=2.0,        # Wait 2s between retries (exponential backoff may be applied by runtime)
    behavior=FailureBehavior.ROUTE_TO_FALLBACK, # Strategy on final failure
    fallback_node_id="human-escalation"         # Target for fallback
)

# Attach to a node
node = AgentNode(
    id="risky-task",
    agent_ref="experimental-agent",
    recovery=recovery
)
```

### Failure Behaviors

The `behavior` field controls the final action after all `max_retries` have failed.

| Behavior | Value | Description |
| :--- | :--- | :--- |
| **Fail Workflow** | `fail_workflow` | **Default**. The entire recipe stops with an error. |
| **Continue with Default** | `continue_with_default` | The node "succeeds" but returns a static `default_output` payload. Useful for optional steps (e.g., enrichment). |
| **Route to Fallback** | `route_to_fallback` | Execution jumps to a specific `fallback_node_id`. This effectively adds a dynamic edge to the graph. |
| **Ignore** | `ignore` | The node returns `None` and execution proceeds to the next step (if inputs allow). |

## Patterns

### 1. The "Try-Catch" Pattern (Fallback)

Use `route_to_fallback` to implement a "Try-Catch" block where a failure routes to a different handler.

```python
primary = AgentNode(
    id="fetch-data",
    recovery=RecoveryConfig(
        behavior=FailureBehavior.ROUTE_TO_FALLBACK,
        fallback_node_id="fetch-data-backup"
    )
)

backup = AgentNode(
    id="fetch-data-backup",
    ...
)
```

### 2. The "Optional Step" Pattern (Default Value)

Use `continue_with_default` for steps that are nice-to-have but shouldn't block the workflow.

```python
enrichment = AgentNode(
    id="enrich-user-profile",
    recovery=RecoveryConfig(
        behavior=FailureBehavior.CONTINUE_WITH_DEFAULT,
        default_output={"enriched": False, "reason": "service_down"}
    )
)
```

### 3. The "Transient Failure" Pattern (Retries)

Simply set `max_retries` to handle transient network issues or LLM hiccups.

```python
robust_node = AgentNode(
    id="call-llm",
    recovery=RecoveryConfig(max_retries=5)
)
```

## Validation

The `RecipeDefinition` validates Flow Governance configurations:
*   `max_retries`: Defines the retry limit. Negative values are permitted for flexible runtime interpretations (e.g., infinite retries).
*   `retry_delay_seconds`: Defines the backoff delay. Negative values are permitted for custom runtime scheduling.
*   If `behavior` is `route_to_fallback`, `fallback_node_id` MUST be provided and MUST exist in the graph.
*   If `behavior` is `continue_with_default`, `default_output` generally should be provided (though `None` is valid).
