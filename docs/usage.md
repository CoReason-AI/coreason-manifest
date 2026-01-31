# Usage Guide

The `coreason-manifest` package serves as the **Shared Kernel** for the Coreason ecosystem. It provides the canonical Pydantic definitions and schemas for Agents, Workflows (Recipes), and Auditing.

It is designed to be a pure data library, meaning it contains **no execution logic** (no servers, no engines, no policy enforcement engines). Its sole purpose is to define the *structure* and *validation rules* for data.

## Core Concepts

### 1. Agent Definition
The `AgentDefinition` is the source of truth for an AI Agent. It includes:
- **Metadata**: Identity, versioning (Strict SemVer), and authorship.
- **Interface**: Strictly typed inputs and outputs (JSON Schema).
- **Topology**: A graph-based execution flow (`GraphTopology`) supporting cyclic loops (e.g., for reflection).
- **Dependencies**: MCP Tooling requirements (`ToolRequirement`) and Python libraries.
- **Policy**: Governance rules for budget and human-in-the-loop triggers (`PolicyConfig`).
- **Observability**: Telemetry configurations (`ObservabilityConfig`).

### 2. Strict Constraints
To ensure reliability and auditability, the library enforces three strict constraints:

#### A. Immutability
All dictionary and list fields in the interface are converted to immutable types (`MappingProxyType`, `tuple`) upon validation. You cannot modify them in place.

**Incorrect:**
```python
agent.interface.inputs["new_param"] = "value"  # Raises TypeError
```

**Correct:**
```python
# Construct the full dictionary first
inputs = {
    "query": {"type": "string"},
    "max_results": {"type": "integer"}
}
# Pass it to the constructor
```

#### B. Strict SemVer
Versions must strictly follow the `X.Y.Z` format (e.g., `1.0.0`). While `v1.0.0` is normalized to `1.0.0`, loose formats like `1.0` or `beta` are rejected.

#### C. Integrity Hash
The `integrity_hash` field is mandatory. It must be a valid 64-character SHA256 hex string representing the hash of the agent's source code.

## Examples

### Creating an Agent Definition

```python
import uuid
from coreason_manifest.definitions.agent import (
    AgentDefinition,
    ToolRequirement,
    ToolRiskLevel,
    TraceLevel
)

# 1. Define Metadata
metadata = {
    "id": uuid.uuid4(),
    "version": "1.0.0",  # Strict SemVer
    "name": "Research Agent",
    "author": "Coreason AI",
    "created_at": "2023-10-27T10:00:00Z"
}

# 2. Define Topology (Graph)
# Using logic nodes for demonstration
nodes = [
    {"id": "start", "type": "logic", "code": "print('Starting')"},
    {"id": "process", "type": "logic", "code": "process_data()"},
    {"id": "end", "type": "logic", "code": "return result"}
]

edges = [
    {"source_node_id": "start", "target_node_id": "process"},
    {"source_node_id": "process", "target_node_id": "end"}
]

# 3. Instantiate Agent
agent = AgentDefinition(
    metadata=metadata,
    interface={
        "inputs": {"topic": {"type": "string"}},
        "outputs": {"summary": {"type": "string"}}
    },
    topology={
        "nodes": nodes,
        "edges": edges,
        "entry_point": "start",
        "model_config": {"model": "gpt-4", "temperature": 0.0}
    },
    dependencies={
        "tools": [
            ToolRequirement(
                uri="mcp://search-service/google",
                hash="a" * 64,  # Valid SHA256
                scopes=["search:read"],
                risk_level=ToolRiskLevel.STANDARD
            )
        ],
        "libraries": ["pandas==2.0.0"]
    },
    policy={
        "budget_caps": {"total_cost": 5.0},
        "human_in_the_loop": ["process"]
    },
    observability={
        "trace_level": TraceLevel.FULL,
        "retention_policy": "90_days"
    },
    # Mandatory Integrity Hash
    integrity_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)

print(f"Agent '{agent.metadata.name}' created successfully.")
```

### Accessing Immutable Fields

```python
# Reading is allowed
print(agent.interface.inputs["topic"])

# Writing raises TypeError
try:
    agent.interface.inputs["topic"] = "int"
except TypeError as e:
    print("Caught expected error:", e)
```
