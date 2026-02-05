# Memory Governance

Coreason Manifest provides a declarative way to define memory eviction policies for Agents. This allows developers to control how conversation history is managed, ensuring that agents stay within context window limits while retaining relevant information.

## Configuration Model

The memory configuration is defined via the `MemoryConfig` model, which is embedded within the `AgentRuntimeConfig` of an `AgentDefinition`.

### Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `strategy` | `MemoryStrategy` | The eviction strategy to use. Default: `sliding_window`. |
| `limit` | `int` | The parameter 'N' governing the strategy (e.g., number of turns or tokens). Must be > 0. |
| `summary_prompt` | `str \| None` | Instructions for summarization. Required/Used only if strategy is `summary`. |

## Strategies

The `MemoryStrategy` enum defines the available eviction policies:

*   **`sliding_window`**: Retains the last `N` messages/turns. Oldest messages are dropped.
*   **`token_buffer`**: Retains messages fitting within the last `N` tokens.
*   **`summary`**: Summarizes older conversation history when the limit `N` is reached.
*   **`vector_store`**: Offloads memory to a vector database for semantic retrieval.

## Usage Example

Memory configuration is applied to an Agent via its `runtime` property.

```python
from coreason_manifest import (
    AgentDefinition,
    AgentRuntimeConfig,
    MemoryConfig,
    MemoryStrategy,
)

# Define memory configuration
memory_policy = MemoryConfig(
    strategy=MemoryStrategy.SUMMARY,
    limit=10,  # Summarize after 10 turns
    summary_prompt="Summarize the conversation focusing on user preferences."
)

# Apply to Agent
agent = AgentDefinition(
    id="agent-1",
    name="Personal Assistant",
    role="Assistant",
    goal="Help the user",
    runtime=AgentRuntimeConfig(
        memory=memory_policy
    )
)

print(agent.model_dump_json(indent=2))
```

### JSON Representation

```json
{
  "type": "agent",
  "id": "agent-1",
  "name": "Personal Assistant",
  "role": "Assistant",
  "goal": "Help the user",
  "runtime": {
    "memory": {
      "strategy": "summary",
      "limit": 10,
      "summary_prompt": "Summarize the conversation focusing on user preferences."
    }
  }
}
```
