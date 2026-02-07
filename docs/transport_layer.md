# Transport Layer

The **Transport Layer** defines the fundamental envelope for all communication within the CoReason ecosystem. It ensures that every interaction—whether a user request, an inter-agent call, or a system event—carries the necessary context for **Distributed Tracing**, **Session Management**, and **Audit Logging**.

## The Transport Envelope: `AgentRequest`

The core model is `AgentRequest`, which acts as a strictly typed, immutable envelope.

**Import:**
```python
from coreason_manifest import AgentRequest
```

### Fields

| Field | Type | Description | Required | Default |
| :--- | :--- | :--- | :--- | :--- |
| `request_id` | `UUID` | Unique ID for *this specific operation*. | Yes | `uuid4()` |
| `session_id` | `UUID` | Groups requests into a coherent user session. | **Yes** | - |
| `root_request_id` | `UUID` | The ID of the original request that started the trace. | Yes | `request_id` (Auto-rooting) |
| `parent_request_id` | `Optional[UUID]` | The ID of the immediate caller (for nested traces). | No | `None` |
| `payload` | `Dict[str, Any]` | The actual business logic arguments (e.g., `{"query": "hello"}`). | Yes | - |
| `metadata` | `Dict[str, Any]` | Contextual metadata (e.g., locale, auth scope). | No | `{}` |
| `created_at` | `datetime` | Creation timestamp (UTC). | Yes | `now()` |

### Key Features

#### 1. Auto-Rooting (Trace Initiation)
When a new request is created without a `root_request_id`, the system automatically assigns the current `request_id` as the root. This marks the start of a new trace.

```python
from uuid import uuid4
from coreason_manifest import AgentRequest

# Start a new trace
req = AgentRequest(
    session_id=uuid4(),
    payload={"query": "Start process"}
)

assert req.root_request_id == req.request_id  # Auto-rooted
assert req.parent_request_id is None
```

#### 2. Trace Continuity (Child Creation)
To propagate context, use the `create_child()` method. This ensures lineage integrity by setting the parent and root IDs correctly.

```python
# Create a child request (e.g., Agent A calls Agent B)
child_req = req.create_child(
    payload={"task": "sub-task"}
)

assert child_req.root_request_id == req.root_request_id  # Same trace
assert child_req.parent_request_id == req.request_id     # Parent link established
assert child_req.session_id == req.session_id            # Session preserved
```

#### 3. Lineage Validation
The model enforces strict validation to prevent broken traces. You cannot provide a `parent_request_id` without a `root_request_id`.

```python
# This raises ValueError: Broken Trace
try:
    AgentRequest(
        session_id=uuid4(),
        payload={},
        parent_request_id=uuid4()  # Missing root!
    )
except ValueError as e:
    print(e)
```

#### 4. Immutability
`AgentRequest` instances are frozen. To modify data (e.g., in middleware), use `model_copy`.

```python
# Middleware example: Redact PII
new_payload = req.payload.copy()
new_payload["query"] = "***"

safe_req = req.model_copy(update={"payload": new_payload})
```
