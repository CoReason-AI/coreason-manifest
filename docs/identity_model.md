# Identity Model

The `Identity` model serves as the canonical representation of an actor within the Coreason ecosystem. It addresses the limitation of using raw strings for identification by combining a unique identifier with human-readable context.

## Overview

In previous iterations, actors (users, agents, tools) were identified solely by ID strings (e.g., `user_id="123"`). This forced downstream systems (UIs, logs) to perform additional lookups just to display a name. The `Identity` object solves this by carrying the display name alongside the ID.

## Schema

`Identity` is a frozen Pydantic model inheriting from `CoReasonBaseModel`.

```python
class Identity(CoReasonBaseModel):
    id: str           # Unique identifier (UUID string or similar)
    name: str         # Display name for UI/Logs
    role: Optional[str] # Contextual role (e.g., "user", "assistant", "system")
```

## Usage

### Instantiation

```python
from coreason_manifest.definitions.identity import Identity

# Fully specified
agent = Identity(
    id="agent-007",
    name="Bond",
    role="assistant"
)

# Minimal
user = Identity(
    id="u-123",
    name="Alice"
)
```

### String Representation

The `__str__` method provides a consistent format for logging:

```python
print(str(agent))
# Output: "Bond (agent-007)"
```

### Anonymous Identity

For unauthenticated or public sessions, use the factory method:

```python
anon = Identity.anonymous()
# id="anonymous", name="Anonymous User", role="user"
```

## Integration

The `Identity` model is primarily used in `SessionState` to identify the `processor` (the agent) and the `user`.

```python
class SessionState(CoReasonBaseModel):
    processor: Identity
    user: Optional[Identity]
    # ...
```
