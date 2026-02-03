# Memory Governance

As agents run for extended periods, their conversation history (`SessionState.history`) grows indefinitely. This leads to two critical problems:

1.  **Context Window Overflow:** LLMs have finite token limits. Infinite history eventually crashes the agent.
2.  **Unpredictable Costs:** Processing very long histories is expensive and slow.

**Memory Governance** provides a standardized, declarative way to define eviction policies in the Agent Manifest. The Runtime Kernel enforces these policies deterministically.

## Configuration

Memory policies are defined in the `AgentRuntimeConfig` via the `memory` field.

### Schema

```python
class MemoryConfig(CoReasonBaseModel):
    strategy: MemoryStrategy  # e.g., SLIDING_WINDOW
    limit: int                # The "N" parameter (e.g., 20 turns)
    summary_prompt: Optional[str] = None  # Instructions for summarization
```

### Strategies

The `MemoryStrategy` enum defines the supported eviction algorithms:

| Strategy | Description | Limit (N) |
| :--- | :--- | :--- |
| `SLIDING_WINDOW` | Keep the last `N` interactions. Older turns are dropped. | Number of Turns |
| `TOKEN_BUFFER` | Keep the last `N` tokens (approximate). | Token Count |
| `SUMMARY` | Keep a running summary + last `N` turns. | Number of Turns |
| `VECTOR_STORE` | Offload older turns to a vector database (RAG). | Number of Turns |

*Note: The Coreason Kernel currently implements the deterministic `SLIDING_WINDOW` logic directly. Complex strategies like `SUMMARY` or `VECTOR_STORE` require an Engine/LLM call but are configured here for standardization.*

## Usage Example

```python
from coreason_manifest.definitions.agent import AgentRuntimeConfig
from coreason_manifest.definitions.memory import MemoryConfig, MemoryStrategy

config = AgentRuntimeConfig(
    # ... other config ...
    memory=MemoryConfig(
        strategy=MemoryStrategy.SLIDING_WINDOW,
        limit=20  # Keep only the last 20 turns
    )
)
```

## Runtime Logic: `prune()`

The `SessionState` object includes a `prune()` method that strictly enforces these policies.

```python
# Returns a NEW SessionState instance with truncated history
pruned_session = session.prune(
    strategy=MemoryStrategy.SLIDING_WINDOW,
    limit=20
)
```

### Immutability & Determinism
*   **Immutability:** The `prune()` operation never modifies the original session in place. It returns a new copy (`copy-on-write`).
*   **Determinism:** For `SLIDING_WINDOW`, the logic is purely arithmetic (`history[-limit:]`).
