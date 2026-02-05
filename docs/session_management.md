# Session Management

The `coreason-manifest` library provides strict, immutable data structures for managing conversational session state. This ensures that the runtime can manage memory statelessly and predictably.

## Core Concepts

### SessionState

`SessionState` is a frozen Pydantic model representing the state of a conversation at a specific point in time. Because it is immutable (`frozen=True`), any modification to the state results in a **new** instance. This implements a Functional Pattern.

**Fields:**

*   `id` (str): Unique UUID for the session state version.
*   `agent_id` (str): The ID of the agent definition.
*   `user_id` (str): The ID of the user/owner.
*   `created_at` (datetime): When the session started.
*   `updated_at` (datetime): When this specific state version was created.
*   `history` (List[Interaction]): An ordered list of interactions (messages/exchanges).
*   `variables` (Dict[str, Any]): Arbitrary key-value store for session variables.

### MemoryStrategy

The `MemoryStrategy` enum defines how the session history should be managed (pruned) to fit within context windows.

*   `ALL` ("all"): Retain all history. No pruning.
*   `SLIDING_WINDOW` ("sliding_window"): Retain only the last `N` interactions.
*   `TOKEN_BUFFER` ("token_buffer"): (Reserved) Retain items fitting within a token budget. Currently behaves like `ALL`.

## Usage

### Creating a Session

```python
from datetime import datetime
from coreason_manifest import SessionState

state = SessionState(
    agent_id="agent-1",
    user_id="user-123",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)
```

### Pruning History

The `prune` method allows you to apply a memory strategy. It returns a **new** `SessionState` instance; the original instance is left untouched.

```python
from coreason_manifest import MemoryStrategy

# Assume state.history has 10 items
new_state = state.prune(MemoryStrategy.SLIDING_WINDOW, limit=5)

# state.history has 10 items
# new_state.history has 5 items (the most recent ones)
```

### Managing Variables

Since `SessionState` is frozen, updating variables also requires creating a new instance. Pydantic's `model_copy` is useful here.

```python
current_vars = state.variables.copy()
current_vars["topic"] = "physics"

updated_state = state.model_copy(update={
    "variables": current_vars,
    "updated_at": datetime.now()
})
```

## Immutability Guarantee

The design strictly enforces immutability to prevent side effects in concurrent or distributed runtime environments.

*   **Thread Safety:** Instances can be safely shared across threads.
*   **Time Travel:** Keeping references to older state objects allows for "undo" or lineage inspection.
*   **Statelessness:** The runtime does not need to lock state; it simply transforms input state to output state.
