# Request Lineage Implementation

This document describes the request lineage enforcement mechanisms implemented in `coreason-manifest`. Lineage tracking ensures cryptographic causality and traceability across distributed agent interactions.

## Overview

Every request within the Coreason ecosystem is tracked via a strict lineage chain consisting of:

*   **`request_id`** (UUID): The unique identifier for the current operation.
*   **`root_request_id`** (UUID): The identifier of the original user request that triggered this chain. This ID is propagated unchanged throughout the entire lifecycle.
*   **`parent_request_id`** (UUID, Optional): The identifier of the immediate caller/parent step.

## Auto-Rooting Logic

To ensure data integrity, the system enforces an "Auto-Rooting" policy:

1.  **Missing Root:** If a request is initialized without a `root_request_id`, the system automatically assigns the current `request_id` as the root. This establishes the request as the origin of a new trace.
2.  **Explicit Root:** If `root_request_id` is provided, it is respected.
3.  **Parent Validation:** While not strictly enforced by the schema (to allow flexible partial updates), semantic logic implies that if a `parent_request_id` exists, a `root_request_id` must also exist (and usually differs from the current `request_id`).

## Data Models

### `AgentRequest`

The primary payload for agent services.

```python
class AgentRequest(CoReasonBaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    root_request_id: Optional[UUID] = None  # Auto-filled if None
    parent_request_id: Optional[UUID] = None
    ...
```

### `ReasoningTrace`

Structured audit logs for observability.

```python
class ReasoningTrace(CoReasonBaseModel):
    request_id: UUID
    root_request_id: Optional[UUID] = None  # Auto-filled if None
    parent_request_id: Optional[UUID] = None
    ...
```

### `AuditLog`

Immutable audit record for compliance.

```python
class AuditLog(CoReasonBaseModel):
    id: UUID
    request_id: UUID
    root_request_id: UUID
    timestamp: datetime
    actor: str
    action: str
    outcome: str
    integrity_hash: str
```

## Session Boundaries

When crossing session boundaries (e.g., persistent user sessions), lineage is tracked via metadata:

```python
class LineageMetadata(CoReasonBaseModel):
    root_request_id: str
    parent_interaction_id: Optional[str] = None
```
