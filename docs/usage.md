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

The recommended way to work with manifests is using the **Secure Recursive Loader**, which handles `$ref` resolution, path security ("Jail"), and validation.

```python
from coreason_manifest import load

# Load from file (resolves imports automatically and securely)
manifest = load("my_agent.yaml")

print(f"Loaded {manifest.kind}: {manifest.metadata.name}")
print(f"Inputs: {manifest.interface.inputs.keys()}")
```

For details on composition, security constraints, and referencing syntax, see [Secure Composition](composition.md).

### Creating a Manifest Programmatically

You can also construct the object directly using Python classes.

```python
from coreason_manifest import (
    RecipeDefinition,
    ManifestMetadata,
    RecipeInterface,
    StateDefinition,
    PolicyConfig,
    GraphTopology,
    AgentNode
)

# 1. Define Metadata
metadata = ManifestMetadata(
    name="Research Recipe",
    # Optional provenance fields
    confidence_score=0.95,
    generated_by="coreason-strategist-v1"
)

# 2. Define Topology
topology = GraphTopology(
    entry_point="step1",
    nodes=[
        AgentNode(
            id="step1",
            agent_ref="researcher-agent",
        ),
        # ... define other nodes
    ],
    edges=[]
)

# 3. Instantiate Manifest
manifest = RecipeDefinition(
    kind="Recipe",
    metadata=metadata,
    interface=RecipeInterface(
        inputs={"topic": {"type": "string"}},
        outputs={"summary": {"type": "string"}}
    ),
    state=StateDefinition(
        properties={"notes": {"type": "string"}},
        persistence="redis"
    ),
    policy=PolicyConfig(max_retries=3),
    topology=topology
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

### Visualizing Workflows

Complex workflows can be hard to understand as raw JSON/YAML. You can visualize the execution flow using the built-in Mermaid.js generator.

```python
from coreason_manifest import generate_mermaid_graph

print(generate_mermaid_graph(manifest))
```

For more details, see [Visualization Tools](visualization.md).

### Using the CLI

The `coreason` CLI allows you to inspect, visualize, and simulate agents without writing Python scripts.

```bash
# Visualize an agent defined in a Python file
coreason viz examples/my_agent.py:agent

# Run a simulation
coreason run examples/my_agent.py:agent --inputs '{"query": "hello"}' --mock
```

For full documentation, see [CLI Reference](cli.md).

## Advanced Documentation

*   [Secure Composition](composition.md): Secure Recursive Loader and `$ref` syntax.
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
