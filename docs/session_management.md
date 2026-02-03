# Session Management

The `coreason-manifest` library defines a standardized protocol for managing agent sessions and state. This approach decouples the *execution* of an agent (the runtime logic) from its *memory* (the session state), enabling scalable, stateless execution patterns.

## Core Concepts

### AgentRequest

The entry point for any interaction is the [AgentRequest](agent_request_envelope.md). This envelope carries the `session_id` and the input `payload` that triggers the runtime. The runtime uses this ID to hydrate the correct `SessionState` before execution begins.

### Interaction

An `Interaction` represents a single "turn" or request/response cycle in a conversation or workflow. It captures:

*   **Input/Output:** The raw payloads passed to and from the agent.
*   **Events:** A strictly typed log of `GraphEvent`s emitted during execution (e.g., node start, stream, completion).
*   **Metadata:** Operational data like latency, cost, and model details.
*   **Lineage:** Chain of Custody metadata linking this interaction to its trigger.

The `Interaction` model is immutable (`frozen=True`) to ensure history integrity.

```python
from coreason_manifest.definitions.session import Interaction, LineageMetadata
from coreason_manifest.definitions.message import MultiModalInput, ContentPart
from coreason_manifest.definitions.events import GraphEventNodeInit, NodeInit

# Example: Creating an interaction with strictly typed input
input_payload = MultiModalInput(
    parts=[ContentPart(text="Hello, world!")]
)

interaction = Interaction(
    input=input_payload,
    output={"role": "assistant", "content": "Hi there!"},
    events=[
        GraphEventNodeInit(
            run_id="run-1",
            node_id="node-a",
            timestamp=1700000000.0,
            payload=NodeInit(node_id="node-a"),
            visual_metadata={"color": "blue"}
        )
    ],
    meta={"latency_ms": 150},
    lineage=LineageMetadata(
        root_request_id="req-123",
        parent_interaction_id="int-456"
    )
)
```

### SessionState

`SessionState` is the portable container for the entire conversation history and user context. It is designed to be serialized, stored in a database, and rehydrated on any server.

Key features:

*   **Immutable Updates:** State changes via functional updates (e.g., `add_interaction` returns a *new* instance), preventing side effects.
*   **Context Variables:** A "scratchpad" dictionary (`context_variables`) for long-term memory that persists across turns, separate from the message history.
*   **Identification:** Strictly typed UUIDs for sessions and `Identity` objects for processor/user (carrying both ID and display name).

```python
from uuid import uuid4
from datetime import datetime, timezone
from coreason_manifest.definitions.session import SessionState
from coreason_manifest.definitions.identity import Identity

# 1. Create a new session
session = SessionState(
    session_id=uuid4(),
    processor=Identity(id="agent-v1", name="Support Agent", role="assistant"),
    user=Identity(id="user-123", name="Alice Smith", role="user"),
    created_at=datetime.now(timezone.utc),
    last_updated_at=datetime.now(timezone.utc),
)

# 2. Add an interaction (returns a NEW session object)
new_session = session.add_interaction(interaction)

assert len(session.history) == 0      # Original is unchanged
assert len(new_session.history) == 1  # New instance has the update
```

## Why this Architecture?

By formalizing `SessionState` separate from the raw Agent logic, we achieve:

1.  **Stateless Runtime:** The execution engine doesn't need to hold state in memory between turns. It just needs the `SessionState` object.
2.  **Portability:** Sessions can be moved between different workers or regions easily.
3.  **Auditability:** The history of `Interaction`s provides a complete, immutable audit trail of the conversation.
