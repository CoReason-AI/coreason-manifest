# Atomic Agents and Graph Topologies

## Overview

The `coreason-manifest` supports two primary modes of agent definition:

1.  **Graph-Based Agents**: Agents defined by a topology of nodes and edges, orchestrating complex workflows.
2.  **Atomic Agents**: Agents defined primarily by a System Prompt and a Model Configuration, without an internal graph topology. These are often used as "foundry" agents or simple personas.

## AgentRuntimeConfig

The `AgentRuntimeConfig` model controls the execution strategy.

### Graph-Based Configuration

For graph-based agents, you must provide:

-   `nodes`: A list of execution units (`Node`).
-   `edges`: A list of connections (`Edge`).
-   `entry_point`: The ID of the starting node.

```python
config = AgentRuntimeConfig(
    nodes=[...],
    edges=[...],
    entry_point="start_node",
    model_config=ModelConfig(...)
)
```

### Atomic Agent Configuration

For atomic agents, `nodes`, `edges`, and `entry_point` are optional. You define the behavior via `system_prompt`.

-   `nodes`: Defaults to `[]`.
-   `edges`: Defaults to `[]`.
-   `entry_point`: Defaults to `None`.
-   `system_prompt`: The instruction for the agent.

```python
config = AgentRuntimeConfig(
    model_config=ModelConfig(...),
    system_prompt="You are a helpful assistant."
)
```

### Validation

The `AgentRuntimeConfig` includes a validator `validate_topology_or_atomic` that enforces:

-   If `nodes` are present (graph-based), `entry_point` MUST be provided.
-   If `nodes` are empty (atomic), `entry_point` is optional (and typically `None`).

## Inline Tool Definitions

To support self-contained agents (e.g., from `coreason-foundry`), `AgentDependencies.tools` supports **Inline Tool Definitions**.

Instead of requiring a remote URI and hash (via `ToolRequirement`), you can define the tool directly in the manifest:

```python
class InlineToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    type: Literal["function"] = "function"
```

This allows agents to be fully portable without external deployment dependencies during the drafting phase.
