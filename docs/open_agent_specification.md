# Open Agent Specification (OAS)

The **Open Agent Specification (OAS)** is the core standard used by the Coreason ecosystem to define, configure, and validate AI Agents. It serves as the "Source of Truth," ensuring that agents are portable, strictly typed, and secure.

In this repository (`coreason-manifest`), the OAS is implemented as a set of strict **Pydantic v2 models**. These models define the schema for Agents, their relationships (Topology), and their execution requirements.

## Architecture: The Shared Kernel

The `coreason-manifest` package acts as a **Shared Kernel**. It contains *only* data structures, schemas, and validation logic. It does not contain execution engines, server logic, or database drivers.

By centralizing the definitions here, all downstream services (Builder, Engine/MACO, Simulator) interact with a single, unified language. If a field or concept does not exist in the OAS, it does not exist in the platform.

## The Agent Manifest

The root of the specification is the `AgentDefinition` class (located in `src/coreason_manifest/definitions/agent.py`). It encapsulates everything needed to instantiate and run an agent.

### Core Components

An `AgentDefinition` consists of the following sections:

1.  **Metadata (`AgentMetadata`)**:
    *   **Identity**: `id` (UUID), `name`, `author`.
    *   **Versioning**: strict semantic versioning (`version`).
    *   **Timestamps**: `created_at`.
    *   **Auth**: `requires_auth` flag for user context injection.

2.  **Interface (`AgentInterface`)**:
    *   Defines the "contract" of the agent.
    *   `inputs` and `outputs` are defined using immutable dictionaries (representing JSON Schemas).
    *   `injected_params` lists system-injected values (e.g., `user_context`).

3.  **Configuration (`AgentRuntimeConfig`)**:
    *   The "brain" of the agent.
    *   **LLM Config**: Model selection, temperature, and system prompts.
    *   **Topology**: Defines whether the agent is Atomic (single prompt) or Graph-based (workflow).

4.  **Dependencies (`AgentDependencies`)**:
    *   **Tools**: Supports the **Model Context Protocol (MCP)**.
    *   `ToolRequirement`: Defines external tools via URI, including `risk_level` and `scopes`.
    *   `InlineToolDefinition`: Allows embedding tool schemas directly in the manifest.
    *   **Integrity**: Tools require SHA256 hashes for security.

5.  **Policy (`PolicyConfig`)**:
    *   Governance controls.
    *   `budget_caps`: Limits on cost or tokens.
    *   `human_in_the_loop`: Node IDs that trigger a pause for human approval.
    *   `allowed_domains`: Whitelisting for external access.

6.  **Observability (`ObservabilityConfig`)**:
    *   `trace_level`: Controls the granularity of logs (`FULL`, `METADATA_ONLY`, `NONE`).
    *   `retention_policy`: How long logs are kept.
    *   `encryption_key_id`: Optional ID of the key used for log encryption.

7.  **Integrity**:
    *   `integrity_hash`: SHA256 hash of the source code (top-level field).

## Agent Types: Atomic vs. Graph

The OAS supports two distinct architectural patterns via `AgentRuntimeConfig`:

### 1. Atomic Agents
An Atomic Agent is a single-step execution unit. It relies on a System Prompt and an LLM to process inputs and generate outputs.

*   **Requirements**:
    *   `nodes` and `edges` lists must be empty.
    *   Must have a `system_prompt` (either global or within `llm_config`).

### 2. Graph-Based Agents
A Graph Agent orchestrates a complex workflow involving multiple steps, loops, or sub-agents.

*   **Requirements**:
    *   `nodes`: A list of execution units (`AgentNode`, `LogicNode`, `RecipeNode`, etc.).
    *   `edges`: Directed connections defining control flow.
    *   `entry_point`: The ID of the starting node.
    *   **Topology Validation**: The specification strictly validates that all edges connect to existing nodes (preventing "dangling pointers").

## Recipes and Topology

While `AgentDefinition` defines an autonomous entity, the **Recipe Manifest** (`RecipeManifest`) defines a reusable workflow or "Standard Operating Procedure" (SOP).

Both share the `GraphTopology` structure (from `src/coreason_manifest/definitions/topology.py`), which supports:
*   **Polymorphic Nodes**: Agents, Human input, Pure Python logic, Map/Reduce operations.
*   **Conditional Edges**: Dynamic routing based on logic or router expressions.
*   **State Management**: `StateDefinition` schemas for persistent memory across steps.

## Key Value Propositions

### 1. Strict Typing & Validation
Built on Pydantic v2, the OAS enforces types at runtime. Invalid UUIDs, malformed semantic versions, or missing required fields cause immediate validation errors, preventing invalid states from entering the system.

### 2. Integrity & Security
*   **Integrity Hashing**: The `integrity_hash` field (SHA256) ensures that the agent definition has not been tampered with since creation.
*   **Tool Safety**: MCP tools require explicit risk levels (`SAFE`, `STANDARD`, `CRITICAL`) and scope definitions.

### 3. Serialization (`CoReasonBaseModel`)
All models inherit from `CoReasonBaseModel`, which solves common serialization issues. It ensures that complex types like `UUID` and `datetime` are consistently serialized to JSON-compatible strings, making the manifest easily portable between Python and frontend (JSON/JS) environments.

## Example Usage

Here is how to programmatically define an Agent using the OAS:

```python
import uuid
from datetime import datetime, timezone
from coreason_manifest.definitions.agent import (
    AgentDefinition,
    AgentMetadata,
    AgentInterface,
    AgentRuntimeConfig,
    ModelConfig,
    AgentDependencies,
    ToolRequirement,
    ToolRiskLevel
)

# Define the Agent
agent = AgentDefinition(
    # 1. Metadata
    metadata=AgentMetadata(
        id=uuid.uuid4(),
        version="1.0.0",
        name="Weather Researcher",
        author="Coreason AI",
        created_at=datetime.now(timezone.utc)
    ),

    # 2. Interface
    interface=AgentInterface(
        inputs={"location": {"type": "string"}},
        outputs={"forecast": {"type": "string"}}
    ),

    # 3. Configuration (Atomic)
    config=AgentRuntimeConfig(
        model_config=ModelConfig(
            model="gpt-4-turbo",
            temperature=0.7,
            system_prompt="You are a weather expert."
        )
    ),

    # 4. Dependencies
    dependencies=AgentDependencies(
        tools=[
            ToolRequirement(
                uri="mcp://weather-service/api",
                hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                scopes=["weather:read"],
                risk_level=ToolRiskLevel.SAFE
            )
        ]
    ),

    # 5. Integrity
    integrity_hash="a" * 64
)

# Dump to JSON
json_output = agent.model_dump_json(indent=2)
print(json_output)
```
