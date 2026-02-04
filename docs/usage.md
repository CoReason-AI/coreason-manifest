# Usage Guide

The `coreason-manifest` package serves as the **Shared Kernel** for the Coreason ecosystem. It provides the canonical Pydantic definitions and schemas for Agents and Workflows (Recipes).

It is designed to be a pure data library, meaning it contains **no execution logic** (no servers, no engines, no policy enforcement engines). Its sole purpose is to define the *structure* and *validation rules* for data.

## Core Concepts

### 1. Agent & Recipe Definition
The `Manifest` is the source of truth for an AI Agent or Recipe. It includes:
- **Metadata**: Identity, versioning (Strict SemVer), and authorship.
- **Interface**: Strictly typed modes of interaction (`inputs`, `outputs` as JSON Schema).
- **Topology**: A graph-based execution flow (`Workflow`) supporting cyclic loops (e.g., for reflection).
- **Definitions**: Reusable components like Tools (`ToolDefinition`) and sub-agents.
- **Policy**: Governance rules for budget and human-in-the-loop triggers (`PolicyDefinition`).
- **State**: Shared memory schema (`StateDefinition`).

### 2. Constraints
To ensure reliability and auditability, the library enforces:

#### Strict SemVer
Versions must strictly follow the `X.Y.Z` format (e.g., `1.0.0`). While `v1.0.0` is normalized to `1.0.0`, loose formats like `1.0` or `beta` are rejected.

## Examples

### Loading a Manifest

The recommended way to work with manifests is using the YAML loader, which handles recursive imports and validation.

```python
from coreason_manifest import load

# Load from file (resolves imports automatically)
manifest = load("my_agent.yaml")

print(f"Loaded {manifest.kind}: {manifest.metadata.name}")
print(f"Inputs: {manifest.interface.inputs.keys()}")
```

### Creating a Manifest Programmatically

You can also construct the object directly using Python classes.

```python
from coreason_manifest import (
    Recipe,
    ManifestMetadata,
    InterfaceDefinition,
    StateDefinition,
    PolicyDefinition,
    Workflow,
    AgentStep
)

# 1. Define Metadata
metadata = ManifestMetadata(
    name="Research Agent",
    version="1.0.0"
)

# 2. Define Workflow
workflow = Workflow(
    start="step1",
    steps={
        "step1": AgentStep(
            id="step1",
            agent="gpt-4-researcher",
            next="step2"
        ),
        # ... define other steps
    }
)

# 3. Instantiate Manifest
manifest = Recipe(
    metadata=metadata,
    interface=InterfaceDefinition(
        inputs={"topic": {"type": "string"}},
        outputs={"summary": {"type": "string"}}
    ),
    state=StateDefinition(),
    policy=PolicyDefinition(max_retries=3),
    workflow=workflow
)

print(f"Manifest '{manifest.metadata.name}' created successfully.")
```

### Modifying Fields

Manifests are mutable to facilitate authoring and builder tools.

```python
# Reading
print(manifest.interface.inputs["topic"])

# Writing
manifest.interface.inputs["topic"] = {"type": "integer"}
```

## Advanced Documentation

*   [Coreason Agent Manifest](cap/specification.md): The Canonical YAML Authoring Format.

## Shared Primitives

### Identity
The `Identity` class is a standardized, immutable representation of any actor in the system (User, Agent, or System). It replaces raw string IDs to provide context-aware identification.

```python
from coreason_manifest import Identity

# Creating an identity
user = Identity(id="user-123", name="Alice", role="admin")
print(user)  # Output: Alice (user-123)

# Anonymous identity
anon = Identity.anonymous()
print(anon.id)  # "anonymous"

# Immutability
# user.name = "Bob"  # Raises ValidationError
```
