# Builder SDK

The Builder SDK provides a fluent, Pythonic interface for creating `ManifestV2` definitions. It abstracts away the complexity of the raw JSON/YAML structure and ensures type safety using Pydantic models.

## Key Components

### `TypedCapability`

Wraps input/output Pydantic models to define a capability. It automatically generates the JSON Schema required for the Agent's interface.

```python
from pydantic import BaseModel
from coreason_manifest import TypedCapability

class SearchInput(BaseModel):
    query: str

class SearchOutput(BaseModel):
    results: list[str]

search_cap = TypedCapability(
    name="WebSearch",
    description="Search the internet.",
    input_model=SearchInput,
    output_model=SearchOutput
)
```

### `AgentBuilder`

Constructs an `AgentDefinition` and wraps it in a valid `ManifestV2`.

```python
from coreason_manifest import AgentBuilder

manifest = (
    AgentBuilder("ResearchAgent")
    .with_model("gpt-4-turbo")
    .with_system_prompt("You are a helpful researcher.")
    .with_capability(search_cap)
    .with_tool("mcp-browser")
    .build()
)

# Export to YAML
from coreason_manifest import dump
print(dump(manifest))
```

## Features

*   **Fluent Interface**: Chain methods to build up your agent.
*   **Schema Generation**: Automatically converts Pydantic models to JSON Schema.
*   **Type Safety**: Generic typing ensures inputs and outputs match your models.
*   **Defaults**: sets sensible defaults for boilerplate fields like `Workflow`.
