# Interface Contracts

The Coreason Agent Manifest (CAM) supports decoupling the **Interface** (Contract) from the **Implementation** (Capability). This allows for stricter governance, reusability, and polymorphism across agents.

Instead of every agent redefining `inputs` and `outputs` inline, they can reference a shared `InterfaceDefinition` by ID.

## The Interface Definition

The `InterfaceDefinition` is a top-level asset that defines a strict contract for inputs and outputs.

### Schema

An `InterfaceDefinition` consists of:

1.  **Metadata (`ContractMetadata`)**:
    *   `id`: Unique Identifier (UUID).
    *   `version`: Semantic Version.
    *   `name`: Human-readable name (e.g., "Corporate Search").
    *   `author`: The team or entity defining the contract.

2.  **Inputs (`inputs`)**:
    *   A JSON Schema defining the arguments required by the interface.

3.  **Outputs (`outputs`)**:
    *   A JSON Schema defining the expected structure of the result.

4.  **Description (`description`)**:
    *   A human-readable explanation of the contract's purpose.

### Example

```python
from uuid import uuid4
from datetime import datetime, timezone
from coreason_manifest.definitions.contracts import InterfaceDefinition, ContractMetadata

search_interface = InterfaceDefinition(
    metadata=ContractMetadata(
        id=uuid4(),
        version="1.0.0",
        name="Enterprise Search",
        author="Platform Team",
        created_at=datetime.now(timezone.utc)
    ),
    description="Standard interface for searching corporate knowledge bases.",
    inputs={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query."}
        },
        "required": ["query"]
    },
    outputs={
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string"}
                    }
                }
            }
        },
        "required": ["results"]
    }
)
```

## Using Interfaces in Agents

When defining an `AgentCapability`, you can now reference an interface instead of defining schemas inline.

### `AgentCapability` Updates

The `AgentCapability` class has been updated with:
*   `interface_id` (Optional[UUID]): References a published `InterfaceDefinition`.
*   **Validation Rule**: A capability must provide **EITHER** an `interface_id` **OR** inline `inputs`/`outputs`.

### Example Agent

```python
from coreason_manifest.definitions.agent import AgentCapability, CapabilityType

capability = AgentCapability(
    name="search",
    type=CapabilityType.ATOMIC,
    description="Implements the Enterprise Search contract.",
    # Instead of inputs/outputs, we reference the ID:
    interface_id=search_interface.metadata.id
)
```

## Benefits

1.  **Standardization**: Ensure all "Search" agents accept the same arguments.
2.  ** Governance**: Central teams can publish contracts that agents must adhere to.
3.  **Polymorphism**: Clients can program against the *Interface* (e.g., "Find an agent that implements interface X") rather than inspecting individual schemas.
