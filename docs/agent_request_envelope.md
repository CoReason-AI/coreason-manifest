# AgentRequest Envelope

The `AgentRequest` model is the standardized envelope for all agent invocations within the Coreason Framework. It ensures that every request—whether originating from a user, another agent, or an external system—carries the necessary context for **Distributed Tracing**, **Session Management**, and **Causal Tracking**.

## Purpose

By wrapping every invocation in an `AgentRequest`, the Engine automatically propagates trace context across complex multi-agent workflows. This enables:

1.  **Distributed Tracing:** Visualization of request chains (Root -> Parent -> Child) in tools like Jaeger or Arize.
2.  **Causal Integrity:** Strict validation ensures that no child request exists without a clear lineage back to a root cause.
3.  **Standardization:** A uniform interface for all agents, regardless of their internal logic (Atomic vs. Graph-based).

## Structure

The `AgentRequest` model is defined in `src/coreason_manifest/definitions/request.py`.

```python
from coreason_manifest.definitions import AgentRequest

request = AgentRequest(
    request_id=uuid4(),      # Unique ID for this specific invocation
    session_id=uuid4(),      # The conversation/session ID
    root_request_id=uuid4(), # The ID of the very first request in the chain
    parent_request_id=uuid4(),# The ID of the request that triggered this one
    payload={"input": "Hello"}, # The actual arguments for the agent
    metadata={"user_locale": "en-US"} # Contextual headers
)
```

### Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `request_id` | `UUID` | Unique identifier for this specific request. Defaults to `uuid4()`. |
| `session_id` | `UUID` | The conversation/session ID this request belongs to. **Required.** |
| `root_request_id` | `UUID` | The ID of the first request in the causal chain. |
| `parent_request_id` | `UUID` | The ID of the request that triggered this one (optional). |
| `timestamp` | `datetime` | Creation time (UTC). Defaults to `now()`. |
| `payload` | `Dict[str, Any]` | The actual input arguments for the agent. **Required.** |
| `metadata` | `Dict[str, Any]` | Arbitrary headers or context. Defaults to `{}`. |

## Tracing Logic & Validation

The `AgentRequest` model enforces strict validation rules to maintain trace integrity.

### 1. Auto-Rooting (New Traces)
If `root_request_id` is not provided, the system assumes this is a **new trace**.
*   **Logic:** `root_request_id` defaults to the current `request_id`.

```python
# A new external request
req = AgentRequest(
    session_id=session_id,
    payload={"query": "Start task"}
)
# Result:
# req.request_id = <UUID-A>
# req.root_request_id = <UUID-A> (Self-rooted)
# req.parent_request_id = None
```

### 2. Trace Continuity (Child Requests)
If you provide a `parent_request_id`, you **must** also provide a `root_request_id`. The system raises a `ValueError` if lineage is broken.

*   **Rule:** If `parent_request_id` is set, `root_request_id` cannot be inferred; it must be explicit.

```python
# VALID Child Request
child = AgentRequest(
    session_id=session_id,
    root_request_id=root_req.request_id,
    parent_request_id=parent_req.request_id,
    payload=...
)

# INVALID (Raises ValueError)
invalid = AgentRequest(
    session_id=session_id,
    parent_request_id=parent_req.request_id,
    # Missing root_request_id!
    payload=...
)
```

## Integration

The `AgentRequest` is the primary input for the `AgentRuntime` and is expected to be passed into the `Interaction` model.

### Serialization
Inheriting from `CoReasonBaseModel`, it supports standardized JSON serialization:

```python
json_payload = request.to_json()
```
