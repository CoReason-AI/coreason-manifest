# Coreason Manifest: The Shared Kernel for Autonomous Agents

The definitive source of truth for CoReason-AI Asset definitions. "The Contract."

[![License: Prosperity 3.0](https://img.shields.io/badge/license-Prosperity%203.0-blue)](https://github.com/CoReason-AI/coreason-manifest)
[![Build Status](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason-manifest/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Documentation](https://img.shields.io/badge/docs-home-informational)](docs/index.md)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/coreason-manifest/)

## Overview

`coreason-manifest` serves as the **Shared Kernel** for the Coreason ecosystem. It is not just a schema library; it is the **Contract** between the Builder (UI), the Engine (Runtime), and the Analyst (Eval).

It provides the **"Blueprint"** that all other services rely on. It focuses on strict typing, schema validation, and serialization, ensuring that if it isn't in the manifest, it doesn't exist.

### Standards Clarification
*Note: The "Coreason Agent Manifest" (CAM) is a proprietary, strict governance schema designed for the CoReason Platform. It is distinct from the Oracle/Linux Foundation "Open Agent Specification," though we aim for future interoperability via adapters.*

## Architecture: The "Holy Trinity" + 1

To enable robust Enterprise Agentic Systems, this library implements four critical layers:

| Layer | Component | Description |
| :--- | :--- | :--- |
| **🧭 Orchestration** | **Recipes (`GraphTopology`)** | Directed Cyclic Graphs supporting loops, branching, and Human-in-the-Loop workflows. Replaces linear chains. |
| **📡 Transport** | **Tracing (`AgentRequest`)** | Distributed tracing envelopes compatible with OpenTelemetry. Ensures full lineage from Root -> Parent -> Child. |
| **🤖 Behavior** | **Protocols (`IAgentRuntime`)** | Hexagonal architecture interfaces for portable agents. Defines the Input/Output contract. |
| **🧪 Simulation** | **ATIF (`SimulationTrace`)** | The "Flight Recorder" schema for auditing, red-teaming, and evaluation scenarios. |

### Shared Kernel Boundaries

To avoid the "Distributed Monolith" trap, this library strictly separates **Data** from **Logic**:

*   **`coreason_manifest.spec` (The Kernel):** Contains **pure Pydantic models (DTOs)**. It has zero dependencies on business logic and is safe to import anywhere.
*   **`coreason_manifest.utils` (The Toolbelt):** Contains **optional reference implementations** for Visualization, Audit Hashing, and Governance Enforcement.

These components are co-located for developer convenience but are architecturally decoupled. The Core Spec **never** imports from Utils. See [Package Structure](docs/package_structure.md) for details.

## Installation

```bash
pip install coreason-manifest
```

## Usage

### 1. Defining a Graph Recipe (Orchestration)

Recipes are now graphs, allowing for complex orchestration logic.

```python
from coreason_manifest.spec.v2.recipe import RecipeDefinition, GraphTopology, AgentNode, HumanNode, GraphEdge
from coreason_manifest.spec.v2.definitions import ManifestMetadata, InterfaceDefinition

# Define the nodes
research_node = AgentNode(
    id="research-agent",
    agent_ref="researcher-v1",
    inputs_map={"topic": "user_input"}
)

approval_node = HumanNode(
    id="manager-approval",
    prompt="Approve the research plan?",
    timeout_seconds=3600
)

# Define the topology (The Graph)
topology = GraphTopology(
    entry_point="research-agent",
    nodes=[research_node, approval_node],
    edges=[
        GraphEdge(source="research-agent", target="manager-approval")
    ]
)

# Create the Recipe
recipe = RecipeDefinition(
    metadata=ManifestMetadata(name="Research & Approve Workflow"),
    interface=InterfaceDefinition(
        inputs={"user_input": {"type": "string"}},
        outputs={"approval_status": {"type": "string"}}
    ),
    topology=topology
)

print(f"Recipe '{recipe.metadata.name}' is valid!")
```

### 2. Distributed Tracing (Transport)

The `AgentRequest` envelope ensures that every action is traceable back to its origin.

```python
from coreason_manifest.spec.common.request import AgentRequest
from uuid import uuid4

# 1. Incoming Request (Root)
root_request = AgentRequest(
    session_id=uuid4(),
    payload={"task": "Write a poem"}
)
print(f"Root Trace ID: {root_request.root_request_id}")

# 2. Child Request (e.g., Sub-agent call)
# Automatically inherits session_id and sets parent pointers
child_request = root_request.create_child(
    payload={"subtask": "Find rhyming words"}
)

print(f"Child Parent ID: {child_request.parent_request_id} (Should match Root Request ID)")
print(f"Child Root ID:   {child_request.root_request_id}   (Should match Root Request ID)")
```

### 3. Builder SDK (Optional)

For a fluent, Pythonic API to construct manifests (especially useful for tooling), use the `ManifestBuilder`.

```python
from coreason_manifest.builder import AgentBuilder

agent = AgentBuilder("ResearchAgent") \
    .with_model("gpt-4-turbo") \
    .with_system_prompt("You are a helpful researcher.") \
    .build_definition()
```
See [Builder SDK](docs/builder_sdk.md) for details.

## CLI

The `coreason` CLI is your primary tool for managing agent manifests.

*   `init`: Scaffold a new project.
*   `run`: Simulate execution locally.
*   `viz`: Visualize workflow topology.
*   `validate`: Statically validate JSON/YAML files against the schema.
*   `inspect`: View full canonical JSON.
*   `hash`: Compute integrity hashes.

See [CLI Documentation](docs/cli.md) for full details.

## Documentation

**[Full Documentation Index](docs/index.md)**

*   [**Orchestration**](docs/graph_recipes.md): Building Graph Recipes.
*   [**Transport**](docs/transport_layer.md): Distributed Tracing & Lineage.
*   [**Inline Tools**](docs/inline_tools.md): Serverless/Local Tool Definitions.
*   [**Visualization**](docs/presentation_schemas.md): Controlling the UI Layout.
*   [**Simulation**](docs/simulation.md): ATIF and Evaluation.
