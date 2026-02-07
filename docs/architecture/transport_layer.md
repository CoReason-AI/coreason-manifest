# Transport Layer: The AgentRequest Envelope

The **Transport Layer** in the CoReason ecosystem ensures that all interactions between agents, nodes, and services are encapsulated in a standardized, immutable envelope called `AgentRequest`.

This envelope is responsible for:
1.  **Distributed Tracing**: enforcing strict lineage (Root -> Parent -> Child).
2.  **Context Propagation**: carrying session IDs and metadata across boundaries.
3.  **Immutability**: preventing modification of requests once they enter the graph.

## The AgentRequest Model

The `AgentRequest` model is the fundamental unit of work. It is defined in `coreason_manifest.spec.common.request`.

```python
class AgentRequest(CoReasonBaseModel):
    request_id: UUID          # Unique ID for this specific operation
    session_id: UUID          # Mandatory user session ID
    root_request_id: UUID     # The start of the trace
    parent_request_id: UUID?  # The immediate caller (optional)
    payload: Dict[str, Any]   # The actual business logic arguments
    metadata: Dict[str, Any]  # Context (e.g., auth, locale)
    created_at: datetime      # Timestamp
```

### Trace Lineage Rules

To maintain a coherent distributed trace, the Transport Layer enforces the following rules at runtime:

1.  **Auto-Rooting**: If a request is created without a `root_request_id`, it is considered a new trace. The `root_request_id` is automatically set to the `request_id`.
2.  **Broken Trace Prevention**: You cannot specify a `parent_request_id` without also specifying a `root_request_id`. This prevents "orphaned" branches that cannot be traced back to their origin.
    *   *Violation*: `ValueError("Broken Trace: parent_request_id provided without root_request_id.")`
3.  **Immutability**: Fields cannot be modified after instantiation. To modify a request (e.g., to add middleware headers), you must create a new instance (copy-on-write).

### Usage Pattern

#### Starting a New Trace
When a request enters the system (e.g., from an API Gateway), a new trace is started.

```python
# A new user request
req = AgentRequest(
    session_id=user_session_id,
    payload={"query": "Hello world"}
)
# req.root_request_id == req.request_id
```

#### Propagating Context (Child Requests)
When an agent calls another agent or tool, it must create a **child request**. This preserves the `root_request_id` and links the new request to the current one.

```python
# Inside an agent, calling a sub-agent
child_req = current_req.create_child(
    payload={"task": "analyze_data"},
    metadata={"priority": "high"}
)
# child_req.root_request_id == current_req.root_request_id
# child_req.parent_request_id == current_req.request_id
```

## JSON Serialization

The envelope serializes to a standard JSON structure, ensuring interoperability across languages and transport mechanisms (HTTP, Queues).

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "7136511c-2c93-4556-9609-f643f3287611",
  "root_request_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_request_id": null,
  "payload": {
    "query": "Hello world"
  },
  "metadata": {},
  "created_at": "2023-10-27T10:00:00Z"
}
```
