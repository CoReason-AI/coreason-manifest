# Coreason Agent Manifest (CAM)

The **Coreason Agent Manifest (CAM)** is the core standard used by the Coreason ecosystem to define, configure, and validate AI Agents. It serves as the "Source of Truth," ensuring that agents are portable, strictly typed, and secure.

**Note:** While the CAM is the "machine code" for agents, developers are encouraged to use the **[Builder SDK](builder_sdk.md)** to generate these definitions using Python classes and Pydantic models.

In this repository (`coreason-manifest`), the CAM is implemented as a set of strict **Pydantic v2 models**. These models define the schema for Agents, their relationships (Topology), and their execution requirements.

## Architecture: The Shared Kernel

The `coreason-manifest` package acts as a **Shared Kernel**. It contains *only* data structures, schemas, and validation logic. It does not contain execution engines, server logic, or database drivers.

By centralizing the definitions here, all downstream services (Builder, Engine/MACO, Simulator) interact with a single, unified language. If a field or concept does not exist in the CAM, it does not exist in the platform.

## The Agent Manifest

The root of the specification is the `AgentDefinition` class (located in `src/coreason_manifest/definitions/agent.py`). It encapsulates everything needed to instantiate and run an agent.

### Core Components

An `AgentDefinition` consists of the following sections:

1.  **Metadata (`AgentMetadata`)**:
    *   **Identity**: `id` (UUID), `name`, `author`.
    *   **Versioning**: strict semantic versioning (`version`).
    *   **Timestamps**: `created_at`.
    *   **Auth**: `requires_auth` flag for user context injection.

2.  **Capabilities (`List[AgentCapability]`)**:
    *   Defines the modes of interaction for the agent (e.g., "Atomic", "Streaming").
    *   Each capability has a unique `name`, `type`, and `description`.
    *   **Delivery Mode**: `delivery_mode` explicitly declares whether the client should expect a single `REQUEST_RESPONSE` or a stream of `SERVER_SENT_EVENTS`.
    *   `inputs` and `outputs` are defined using immutable dictionaries (representing JSON Schemas).
    *   `injected_params` lists system-injected values (e.g., `user_context`).

3.  **Configuration (`AgentRuntimeConfig`)**:
    *   The "brain" of the agent.
    *   **LLM Config**: Model selection, temperature, and system prompts.
    *   **Topology**: Defines whether the agent is Atomic (single prompt) or Graph-based (workflow).

4.  **Status (`status`)**:
    *   Lifecycle state of the agent (`draft` or `published`).
    *   Defaults to `draft`.

5.  **Dependencies (`AgentDependencies`)**:
    *   **Tools**: Supports the **Model Context Protocol (MCP)**.
    *   `ToolRequirement`: Defines external tools via URI, including `risk_level` and `scopes`.
    *   `InlineToolDefinition`: Allows embedding tool schemas directly in the manifest.
    *   **Integrity**: Tools require SHA256 hashes for security.

6.  **Policy (`PolicyConfig`)**:
    *   Internal governance controls defined *by* the agent.
    *   `budget_caps`: Limits on cost or tokens.
    *   `human_in_the_loop`: Node IDs that trigger a pause for human approval.
    *   `allowed_domains`: Whitelisting for external access.
    *   *Note: For external enforcement of organizational rules (e.g., blocking unsafe tools), see the [Governance & Policy Enforcement](governance_policy_enforcement.md) module.*

7.  **Deployment (`DeploymentConfig`)**:
    *   Specifies *how* the agent is hosted.
    *   `protocol`: The communication protocol (`HTTP_SSE`, `WEBSOCKET`, `GRPC`).
    *   `port`, `route_prefix`: Network settings.
    *   `scaling_min_instances`, `scaling_max_instances`: Horizontal autoscaling bounds.
    *   `timeout_seconds`: Request processing limits.
    *   `env_vars`: Static environment variable injection.

8.  **Observability (`ObservabilityConfig`)**:
    *   `trace_level`: Controls the granularity of logs (`FULL`, `METADATA_ONLY`, `NONE`).
    *   `retention_policy`: How long logs are kept.
    *   `encryption_key_id`: Optional ID of the key used for log encryption.

9.  **Custom Metadata (`custom_metadata`)**:
    *   Container for arbitrary metadata extensions without breaking validation.

10. **Integrity**:
    *   `integrity_hash`: SHA256 hash of the source code (top-level field). Required only when `status` is `published`.

## Agent Lifecycle: Draft vs. Published

The CAM introduces a "Draft Mode" to facilitate prototyping and visual editing.

*   **Draft Mode (`status="draft"`)**:
    *   **Relaxed Validation**: Topology integrity checks (e.g., ensuring all edges point to valid nodes) are skipped.
    *   **Optional Hash**: The `integrity_hash` field is optional.
    *   **Purpose**: Allows saving "work in progress" states where the graph might be incomplete or disconnected.

*   **Published Mode (`status="published"`)**:
    *   **Strict Validation**: Full topology integrity is enforced.
    *   **Mandatory Hash**: A valid SHA256 `integrity_hash` is required.
    *   **Purpose**: Ensures that executable agents are complete, valid, and tamper-proof.

## Agent Types: Atomic vs. Graph

The CAM supports two distinct architectural patterns via `AgentRuntimeConfig`:

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
    *   **Topology Validation**: The specification validates that all edges connect to existing nodes (preventing "dangling pointers"). *Note: This check is skipped if the agent is in `draft` status.*

## Recipes and Topology

While `AgentDefinition` defines an autonomous entity, the **Recipe Manifest** (`RecipeManifest`) defines a reusable workflow or "Standard Operating Procedure" (SOP).

Both share the `GraphTopology` structure (from `src/coreason_manifest/definitions/topology.py`), which supports:
*   **Polymorphic Nodes**: Agents, Human input, Pure Python logic, Map/Reduce operations.
*   **Conditional Edges**: Dynamic routing based on logic or router expressions.
*   **State Management**: `StateDefinition` schemas for persistent memory across steps.

## Key Value Propositions

### 1. Strict Typing & Validation
Built on Pydantic v2, the CAM enforces types at runtime. Invalid UUIDs, malformed semantic versions, or missing required fields cause immediate validation errors, preventing invalid states from entering the system.

### 2. Integrity & Security
*   **Integrity Hashing**: The `integrity_hash` field (SHA256) ensures that the agent definition has not been tampered with since creation. *Required for published agents.*
*   **Tool Safety**: MCP tools require explicit risk levels (`SAFE`, `STANDARD`, `CRITICAL`) and scope definitions.

### 3. Serialization (`CoReasonBaseModel`)
All models inherit from `CoReasonBaseModel`, which solves common serialization issues. It ensures that complex types like `UUID` and `datetime` are consistently serialized to JSON-compatible strings, making the manifest easily portable between Python and frontend (JSON/JS) environments.

## Example Usage

Here is how to programmatically define an Agent using the CAM:

```python
import uuid
from datetime import datetime, timezone
from coreason_manifest.definitions.agent import (
    AgentDefinition,
    AgentMetadata,
    AgentCapability,
    CapabilityType,
    AgentRuntimeConfig,
    ModelConfig,
    AgentDependencies,
    ToolRequirement,
    ToolRiskLevel,
    AgentStatus
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

    # 2. Capabilities
    capabilities=[
        AgentCapability(
            name="forecast",
            type=CapabilityType.ATOMIC,
            description="Get the weather forecast.",
            inputs={"location": {"type": "string"}},
            outputs={"forecast": {"type": "string"}},
            # delivery_mode defaults to REQUEST_RESPONSE
        )
    ],

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

    # 5. Integrity & Status
    status=AgentStatus.PUBLISHED,
    integrity_hash="a" * 64
)

# Dump to JSON
json_output = agent.model_dump_json(indent=2)
print(json_output)
```

## Visualization and Topology Export

Complex graph-based agents can be difficult to understand by reading JSON. The `AgentDefinition` includes a built-in method to export the topology to **Mermaid.js** format.

### `to_mermaid()`

Generates a string compatible with Mermaid's Live Editor or any Mermaid renderer.

*   **Atomic Agents**: Renders as a single node.
*   **Graph Agents**: Renders the full flow, including:
    *   **Start Node**: Synthetic entry point indicator.
    *   **Shapes**: Distinct shapes for `AgentNode` (Rectangle), `LogicNode` (Rhombus), `HumanNode` (Rounded), etc.
    *   **Styles**: Color-coded classes for visual distinction.
    *   **Edges**: Directional arrows, with labels for conditional logic.

**Example Usage:**

```python
mermaid_graph = agent.to_mermaid()
print(mermaid_graph)
# Output:
# graph TD
# classDef agent ...
# Start((Start)) --> node1
# node1["Search"]:::agent --> node2{"Check"}:::logic
```
