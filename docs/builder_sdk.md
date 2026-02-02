# Builder SDK

The **Builder SDK** (`coreason_manifest.builder`) provides a fluent, Pythonic interface for defining Agents. Instead of manually constructing complex dictionary schemas and strictly typed `AgentDefinition` objects, developers can use Pydantic models and a builder pattern to "compile" their agents into the standard Coreason Manifest format.

## Overview

The Builder SDK bridges the gap between Python's strong typing system and Coreason's language-agnostic "Schema-as-Data" architecture.

*   **Typed Capabilities:** Define Inputs/Outputs using standard Pydantic models.
*   **Fluent Interface:** Chainable methods for configuring the agent.
*   **Auto-Compilation:** Automatically converts Pydantic models into the required JSON Schemas (`ImmutableDict`).
*   **Validation:** Ensures the final object satisfies all `AgentDefinition` invariants.

## Usage

### 1. Define Input/Output Models

Use Pydantic `BaseModel` to define the structure of your capability's data.

```python
from pydantic import BaseModel, Field
from typing import List

class SearchInput(BaseModel):
    query: str = Field(..., description="The search query.")
    max_results: int = Field(5, description="Maximum number of results to return.")

class SearchOutput(BaseModel):
    results: List[str] = Field(..., description="List of URLs found.")
```

### 2. Create a Typed Capability

Wrap your models in a `TypedCapability`.

```python
from coreason_manifest.builder import TypedCapability
from coreason_manifest.definitions.agent import CapabilityType

search_capability = TypedCapability(
    name="search",
    description="Executes a web search.",
    input_model=SearchInput,
    output_model=SearchOutput,
    type=CapabilityType.ATOMIC
)
```

### 3. Build the Agent

Use `AgentBuilder` to assemble the agent and compile it into an `AgentDefinition`.

```python
from coreason_manifest.builder import AgentBuilder

builder = AgentBuilder(
    name="ResearchAssistant",
    version="1.0.0",
    author="Coreason Team"
)

agent_definition = (
    builder
    .with_capability(search_capability)
    .with_system_prompt("You are a helpful research assistant.")
    .with_model("gpt-4-turbo")
    .build()
)

# agent_definition is now a valid, immutable AgentDefinition object
# ready for serialization or usage by the Engine.
print(agent_definition.to_json(indent=2))
```

### 4. Define Graph Topology (Optional)

You can define complex workflows using Nodes and Edges.

```python
from coreason_manifest.definitions.topology import LogicNode

node_a = LogicNode(id="start", type="logic", code="print('Start')")
node_b = LogicNode(id="end", type="logic", code="print('End')")

builder.with_node(node_a)
builder.with_node(node_b)
builder.with_edge("start", "end")
builder.set_entry_point("start")
```

### 5. Add External Tools (Optional)

You can declare dependencies on external MCP tools.

```python
from coreason_manifest.definitions.agent import ToolRiskLevel

builder.with_tool_requirement(
    uri="mcp://google/search",
    hash="a" * 64,  # Valid SHA256
    scopes=["read"],
    risk_level=ToolRiskLevel.STANDARD
)
```

## Key Components

### `TypedCapability[InputT, OutputT]`

A generic wrapper that takes two Pydantic model types (`input_model`, `output_model`).

*   **`to_definition()`**: Converts the Pydantic models into JSON Schemas and returns a standard `AgentCapability` object.

### `AgentBuilder`

The main entry point for creating agents.

*   **`with_capability(cap)`**: Adds a capability.
*   **`with_system_prompt(prompt)`**: Sets the global system instruction.
*   **`with_model(model, temperature)`**: Configures the LLM settings.
*   **`with_node(node)`**: Adds a processing node to the graph.
*   **`with_edge(source, target, condition)`**: Adds a control flow edge.
*   **`set_entry_point(node_id)`**: Sets the starting node for graph execution.
*   **`with_tool_requirement(...)`**: Adds a dependency on an external MCP tool.
*   **`build()`**: Validates configuration, generates integrity hashes, and returns the `AgentDefinition`.

## Why use the Builder?

Directly instantiating `AgentDefinition` requires manually writing JSON Schemas in dictionaries:

```python
# The HARD way (Manual Schema)
AgentCapability(
    inputs={
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    },
    ...
)
```

The Builder allows you to use idiomatic Python:

```python
# The EASY way (Builder SDK)
class SearchInput(BaseModel):
    query: str
```
