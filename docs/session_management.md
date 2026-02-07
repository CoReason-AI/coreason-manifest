# Session Management

The Coreason Manifest Runtime Engine employs a strict, stateless, and immutable approach to session management. This ensures predictable state transitions, simplifies debugging, and enables functional memory management strategies.

## Core Concepts

### 1. Immutable Session State
The `SessionState` model is the container for all conversational context. It is strictly immutable (`frozen=True`), meaning any change to the session (e.g., adding a message, pruning history) results in a **new** instance of the `SessionState` object.

```python
class SessionState(CoReasonBaseModel):
    model_config = ConfigDict(frozen=True)

    id: str                 # Unique Session ID
    agent_id: str          # Owner Agent
    user_id: str           # Owner User
    history: list[Interaction]  # Conversation History
    variables: dict[str, Any]   # Arbitrary State Variables
```

### 2. Functional Memory Pruning
Memory management is handled via the `.prune()` method, which implements the **Functional Pattern**. Instead of modifying the existing list of interactions in place, it returns a new `SessionState` with the applied eviction strategy.

#### Strategies (`MemoryStrategy`)

| Strategy | Description |
| :--- | :--- |
| `ALL` | Retains the entire history. No pruning. |
| `SLIDING_WINDOW` | Retains the last `N` interactions defined by the `limit`. |
| `TOKEN_BUFFER` | Retains the last `N` tokens (Requires external tokenizer implementation). |
| `SUMMARY` | (Legacy/External) Replaces older history with a summary. |
| `VECTOR_STORE` | (Legacy/External) Offloads history to a vector database. |

#### Usage Example

```python
# Initial State with 10 items
state = load_session(session_id)

# Prune to last 5 items
new_state = state.prune(strategy=MemoryStrategy.SLIDING_WINDOW, limit=5)

# Original 'state' remains untouched (length 10)
# 'new_state' has length 5 and a newer 'updated_at' timestamp
save_session(new_state)
```

## Integration

### Agent Request
The `AgentRequest` envelope includes a mandatory `session_id` field to correlate stateless requests with their persistent session context.

```python
class AgentRequest(CoReasonBaseModel):
    session_id: UUID
    payload: Dict[str, Any]
    # ...
```

### Runtime Behavior
1.  **Load:** The runtime fetches the latest `SessionState` by ID.
2.  **Execute:** The agent processes the request, potentially generating new `Interaction` items.
3.  **Update:** A new `SessionState` is created with the appended history.
4.  **Prune:** If a memory policy is active, `.prune()` is called on the new state.
5.  **Save:** The final `SessionState` is persisted.

## Active Memory Interface

While `SessionState` manages the passive context passed to the agent, the **Active Memory Interface** allows agents to proactively interact with the storage layer during their execution.

See **[Active Memory Interface](active_memory_interface.md)** for details on the `SessionHandle` protocol, which provides methods for:

*   **Recall:** Semantic search over knowledge base.
*   **Store/Get:** Persistent variable storage across sessions.
*   **History:** Fetching raw conversation logs.
