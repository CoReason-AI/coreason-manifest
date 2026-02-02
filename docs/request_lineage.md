# Request Lineage & Traceability

The Coreason Manifest enforces **Explicit Request Lineage** to ensure that every AI action, reasoning trace, and audit log can be inextricably linked back to the originating user request. This creates a complete, reconstructible "Trace Tree" of causality, crucial for debugging, compliance, and safety.

## The Trace Tree Concept

In a complex multi-agent system, a single user request (the "Root") can trigger a cascade of sub-requests (child agents, tool calls, internal reasoning).

To maintain order, we enforce a strict lineage hierarchy across three core data structures:
1.  **`AgentRequest`**: The envelope for execution.
2.  **`ReasoningTrace`**: The record of thought.
3.  **`AuditLog`**: The legal record of outcome.

## 1. AgentRequest Lineage

The `AgentRequest` serves as the carrier of lineage during execution.

-   **`request_id`** (UUID): The unique ID of the current operation.
-   **`root_request_id`** (UUID): The ID of the original user request. **Must always be present.**
-   **`parent_request_id`** (UUID, Optional): The ID of the immediate caller.

### Validation Rules
*   **Auto-Rooting**: If `root_request_id` is missing, the system assumes it is a root request and sets `root_request_id = request_id`.
*   **Broken Chain Prevention**: If `parent_request_id` is provided, `root_request_id` **must** also be explicitly provided. It cannot be inferred.

## 2. ReasoningTrace Lineage

The `ReasoningTrace` captures the internal thought process of an agent. It mirrors the `AgentRequest` lineage to allow direct correlation.

### Fields
-   `request_id`: The ID of the request being processed.
-   `root_request_id`: The ID of the root conversation trigger.
-   `parent_request_id`: The ID of the caller.

### Enforcement
The `ReasoningTrace` model validates its own integrity:
```python
if self.root_request_id is None:
    if self.parent_request_id is None:
        # I am the root
        self.root_request_id = self.request_id
    else:
        # I have a parent but no root -> IMPOSSIBLE
        raise ValueError("Root ID missing while Parent ID is present.")
```

## 3. AuditLog Lineage

The `AuditLog` provides a tamper-evident record. To ensure that an audit entry can always be traced to its source, the lineage fields are **mandatory** and included in the integrity hash.

### Fields
-   `request_id`: The specific request that generated this log.
-   `root_request_id`: The root cause.

By including these UUIDs in the `integrity_hash`, we ensure that the causal link cannot be altered without breaking the cryptographic chain of custody.

## 4. Interaction Lineage

The `Interaction` model captures a single turn in a session. While `AgentRequest` drives the execution, the `Interaction` stores the *persistent history* of that execution in the `SessionState`.

### Fields
The `Interaction` uses a dedicated `LineageMetadata` object:
-   `root_request_id`: The ID of the original request that started the entire chain.
-   `parent_interaction_id`: The ID of the specific interaction that triggered this one.

**Note:** Unlike `AgentRequest` which strictly enforces `UUID`s, the `Interaction` lineage uses `str` to ensure interoperability with external systems (e.g., AWS Request IDs, Sentient ULIDs) that may not conform to the UUID standard.

## Summary

| Model | Role | Lineage Enforcement |
| :--- | :--- | :--- |
| `AgentRequest` | **Input** Envelope | Auto-roots; Forbids Parent without Root. |
| `ReasoningTrace` | **Process** Record | Auto-roots; Forbids Parent without Root. |
| `AuditLog` | **Output** Record | Mandatory fields; Hashed for integrity. |
| `Interaction` | **Session** History | Optional `LineageMetadata`; Uses `str` for compatibility. |
