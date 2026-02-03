# Runtime Agent Definition (V1)

The **Runtime Agent Definition** (often referred to as the V1 Manifest) is the strict, machine-optimized Pydantic model used by the Coreason Engine to execute agents. Unlike the [Coreason Agent Manifest (CAM V2)](coreason_agent_manifest.md), which is designed for human authoring, this format is designed for runtime validation, integrity, and performance.

> **Note:** V1 components have been moved to the `coreason_manifest.v1` namespace. This document describes the internal runtime format which is typically generated from V2 manifests via the V2 Bridge.

The root of the runtime specification is the `AgentDefinition` class. The **V2 Loader Bridge** automatically converts the V2 YAML format into this runtime object.

## Core Components

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
    *   **Interface Contracts**: Can reference a reusable `InterfaceDefinition` via `interface_id`.
    *   `inputs` and `outputs` are defined using immutable dictionaries (representing JSON Schemas). *Note: These are optional if `interface_id` is provided.*
    *   `injected_params` lists system-injected values (e.g., `user_context`).
    *   See [Interface Contracts](interface_contracts.md) for details.

3.  **Configuration (`AgentRuntimeConfig`)**:
    *   The "brain" of the agent.
    *   **LLM Config**: Model selection, temperature, and system prompts.
    *   **Topology**: Defines whether the agent is Atomic (single prompt) or Graph-based (workflow).
    *   **Interoperability**: `adapter_hints` allow embedding "Rosetta Stone" metadata for external frameworks (e.g., LangGraph, AutoGen).

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
    *   Specifies *how* the agent is hosted ("Zero-Surprise Deployment").
    *   `env_vars`: List of `SecretReference`s (key, description, provider hint) required for the agent.
    *   `resources`: Hardware limits (`cpu_cores`, `memory_mb`, `timeout_seconds`).
    *   `scaling_strategy`: `serverless` or `dedicated`.
    *   `concurrency_limit`: Max simultaneous requests.
    *   See [Runtime Deployment Configuration](runtime_deployment_configuration.md) for details.

8.  **Evaluation (`EvaluationProfile`)**:
    *   **Evaluation-Ready Metadata**: Defines test contracts directly in the manifest.
    *   `expected_latency_ms`: SLA for response time.
    *   `golden_dataset_uri`: Reference to a test dataset.
    *   `grading_rubric`: List of `SuccessCriterion` for quality checks.
    *   `evaluator_model`: Model to use for evaluation.
    *   See [Evaluation-Ready Metadata](evaluation.md) for details.

9.  **Observability (`ObservabilityConfig`)**:
    *   `trace_level`: Controls the granularity of logs (`FULL`, `METADATA_ONLY`, `NONE`).
    *   `retention_policy`: How long logs are kept.
    *   `encryption_key_id`: Optional ID of the key used for log encryption.

10. **Presentation (`PresentationEvent`)**:
    *   Standardized schemas for emitting UI-ready events (`THOUGHT_TRACE`, `CITATION_BLOCK`, `PROGRESS_INDICATOR`, etc.).
    *   See the **[Presentation Schemas](presentation_schemas.md)** documentation for details.

11. **Custom Metadata (`custom_metadata`)**:
    *   Container for arbitrary metadata extensions without breaking validation.

12. **Integrity**:
    *   `integrity_hash`: SHA256 hash of the source code (top-level field). Required only when `status` is `published`.

## Agent Lifecycle: Draft vs. Published

The `AgentDefinition` supports a "Draft Mode" to facilitate prototyping and visual editing.

*   **Draft Mode (`status="draft"`)**:
    *   **Relaxed Validation**: Topology integrity checks (e.g., ensuring all edges point to valid nodes) are skipped.
    *   **Optional Hash**: The `integrity_hash` field is optional.
    *   **Purpose**: Allows saving "work in progress" states where the graph might be incomplete or disconnected.

*   **Published Mode (`status="published"`)**:
    *   **Strict Validation**: Full topology integrity is enforced.
    *   **Mandatory Hash**: A valid SHA256 `integrity_hash` is required.
    *   **Purpose**: Ensures that executable agents are complete, valid, and tamper-proof.

## Agent Types: Atomic vs. Graph

The runtime supports two distinct architectural patterns via `AgentRuntimeConfig`:

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

## Visualization & Export

To assist with debugging and documentation, the `AgentDefinition` class includes a `to_mermaid()` method. This generates a [Mermaid.js](https://mermaid.js.org/) graph definition string representing the agent's topology.

*   **Atomic Agents**: Rendered as a simple flow from Start to the Agent.
*   **Graph Agents**: Rendered as a `graph TD` flow diagram, including:
    *   Visual distinction between Node Types (Agents, Logic, Human).
    *   Conditional Edges.
    *   Entry Point indication.

```python
mermaid_graph = agent.to_mermaid()
print(mermaid_graph)
# Output:
# graph TD
# Start((Start)) --> node1
# node1["Search"]:::agent
# ...
```

## Key Value Propositions

### 1. Strict Typing & Validation
Built on Pydantic v2, the model enforces types at runtime. Invalid UUIDs, malformed semantic versions, or missing required fields cause immediate validation errors, preventing invalid states from entering the system.

### 2. Integrity & Security
*   **Integrity Hashing**: The `integrity_hash` field (SHA256) ensures that the agent definition has not been tampered with since creation. *Required for published agents.*
*   **Tool Safety**: MCP tools require explicit risk levels (`SAFE`, `STANDARD`, `CRITICAL`) and scope definitions.

### 3. Serialization (`CoReasonBaseModel`)
All models inherit from `CoReasonBaseModel`, which solves common serialization issues. It ensures that complex types like `UUID` and `datetime` are consistently serialized to JSON-compatible strings, making the manifest easily portable between Python and frontend (JSON/JS) environments.

## Example Usage

Here is how to programmatically define an Agent using the Runtime SDK:

```python
import uuid
from datetime import datetime, timezone
# Import from V1 namespace
from coreason_manifest.v1 import AgentDefinition
from coreason_manifest.definitions.agent import (
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
