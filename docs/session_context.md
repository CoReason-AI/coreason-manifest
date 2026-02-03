# Session Context

In the Coreason Framework, every agent execution is accompanied by a **Session Context**. This context answers the fundamental questions of *who* initiated the request, *where* it came from, and *what* permissions are granted.

Unlike the conversation history (which grows and changes), the **Session Context** is **immutable** for the duration of a request. It acts as the "source of truth" for security and observability.

## The Model

The `SessionContext` is a composite object containing three key pillars:

1.  **User Context**: Who is the user?
2.  **Trace Context**: Where is this request in the distributed system?
3.  **Permissions**: What is this agent allowed to do?

### Schema

All context models are immutable (`frozen=True`) Pydantic models.

```python
class SessionContext(CoReasonBaseModel):
    session_id: UUID          # Unique identifier for the session
    agent_id: UUID            # The specific agent instance being invoked
    user: UserContext         # Identity details of the caller
    trace: TraceContext       # Distributed tracing headers
    permissions: List[str]    # Scopes granted for this run (e.g., ["search:read"])
    created_at: datetime      # When this context was minted
```

### User Context

The `UserContext` provides stable identity details about the user. This is distinct from the `Identity` object used in the conversation history (which is for display). `UserContext` is for logic and enforcement.

```python
class UserContext(CoReasonBaseModel):
    user_id: str              # Stable, unique ID (e.g., "auth0|12345")
    email: Optional[str]      # Contact email
    tier: str                 # Entitlement tier (e.g., "free", "pro", "enterprise")
    locale: str               # I18n locale (e.g., "en-US")
```

### Trace Context

The `TraceContext` carries standard distributed tracing identifiers, allowing the agent's execution to be correlated with upstream API calls and downstream service requests.

```python
class TraceContext(CoReasonBaseModel):
    trace_id: UUID            # Global trace ID (W3C standard)
    span_id: UUID             # Current span ID
    parent_id: Optional[UUID] # Parent span ID (if any)
```

## Usage

### In SessionState

The `SessionContext` is a required field in `SessionState`. This ensures that no agent can execute without a valid, defined context.

```python
session = SessionState(
    # ...
    context=SessionContext(
        # ...
    )
)
```

### In Agents

Agents can access the context to make decisions. For example, a tool might check the user's tier before performing an expensive operation.

```python
def generate_report(session: SessionState, ...):
    if session.context.user.tier == "free":
        raise PermissionError("Reports are a Pro feature.")

    # ...
```

## Design Principles

1.  **Strict Separation:** We strictly separate **Context** (immutable facts about the request) from **State** (mutable history of the conversation). This prevents "context drift" where a long-running session might accidentally rely on outdated user info.
2.  **Security First:** By baking permissions and user identity into an immutable object, we prevent tampering. The `SessionContext` should ideally be signed or verified by the platform before reaching the agent.
3.  **Observability:** Mandatory `TraceContext` ensures that every agent execution is observable by default, preventing "black hole" processes that are hard to debug.
