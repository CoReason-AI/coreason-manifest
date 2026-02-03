# Interface Contracts

The "Interface Contracts" feature elevates schema definitions from implementation details to first-class citizens. It allows agents to implement shared interfaces rather than redefining arguments and return types for every capability.

## Problem: Duplication and Drift

Traditionally, every `AgentCapability` defined its `inputs` and `outputs` schemas inline:

```python
AgentCapability(
    name="search",
    description="Search the corpus",
    inputs={"query": {"type": "string"}},
    outputs={"results": {"type": "array"}}
)
```

If multiple agents (e.g., `CorporateSearchAgent` and `LegalSearchAgent`) perform the same conceptual task, they often duplicate these schemas. Over time, these definitions drift, making it difficult to swap agents or enforce standards.

## Solution: The InterfaceDefinition

The `InterfaceDefinition` (in `src/coreason_manifest/definitions/contracts.py`) is a reusable, top-level asset that defines a contract:

```python
from coreason_manifest.definitions.contracts import InterfaceDefinition, ContractMetadata

search_interface = InterfaceDefinition(
    metadata=ContractMetadata(
        id=uuid.uuid4(),
        version="1.0.0",
        name="Standard Search",
        author="Platform Team",
        created_at=now
    ),
    inputs={"type": "object", "properties": {"query": {"type": "string"}}},
    outputs={"type": "object", "properties": {"results": {"type": "array"}}},
    description="A standard interface for search operations."
)
```

## Implementing Interfaces in Agents

Agents can now reference this interface by its ID using the `interface_id` field in `AgentCapability`:

```python
AgentCapability(
    name="legal_search",
    type=CapabilityType.ATOMIC,
    description="Search legal docs.",
    interface_id=search_interface.metadata.id
    # inputs and outputs are omitted here!
)
```

### Validation Rules

The `AgentCapability` model enforces the following validation logic:

1.  **Reference OR Inline**: You must provide either an `interface_id` **OR** both `inputs` and `outputs`.
2.  **Overriding**: You *can* provide both. In this case, the inline `inputs`/`outputs` act as an override or specific implementation detail of the interface (though strictly adhering to the interface contract is best practice).
3.  **Runtime Integrity**: The `AgentDefinition.validate_input()` method will check if `inputs` are present. If an agent uses an `interface_id` without inline schemas, the runtime (e.g., the Engine) is responsible for resolving the `interface_id` to the actual schema before validation. The manifest library itself acts as a data container and will raise a `ValueError` if you try to validate against a missing schema locally.

## Benefits

*   **Standardization**: Enforce a "Search" or "Reasoning" standard across the organization.
*   **Interoperability**: Clients can code against the Interface ID, knowing any agent implementing it will accept the same payload.
*   **Maintainability**: Update the interface once, and the "contract" propagates (versioning applies).
