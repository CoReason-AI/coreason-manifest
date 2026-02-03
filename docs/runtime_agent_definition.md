# Runtime Agent Definition (V1)

The **Runtime Agent Definition** (`AgentDefinition`) is the strictly-typed, machine-optimized structure used by the Coreason Runtime to execute AI Agents.

While developers typically author agents using the [Coreason Agent Manifest (V2)](coreason_agent_manifest.md) YAML format, they are compiled down to this Python/JSON structure for execution.

## Overview

The `AgentDefinition` class (located in `src/coreason_manifest/definitions/agent.py`) encapsulates everything needed to instantiate and run an agent in the runtime environment.

It is implemented using strict **Pydantic v2 models**, ensuring type safety, validation, and serialization.

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
    *   `inputs` and `outputs` are defined using immutable dictionaries (representing JSON Schemas).
    *   `injected_params` lists system-injected values (e.g., `user_context`).

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
    *   Specifies *how* the agent is hosted.
    *   `protocol`: The communication protocol (`HTTP_SSE`, `WEBSOCKET`, `GRPC`).
    *   `port`, `route_prefix`: Network settings.
    *   `scaling_min_instances`, `scaling_max_instances`: Horizontal autoscaling bounds.
    *   `timeout_seconds`: Request processing limits.
    *   `env_vars`: Static environment variable injection.
    *   **Coreason Agent Protocol (CAP)**: All agents must expose the standard endpoints defined in the [Coreason Agent Protocol (CAP)](interface_contracts.md).

8.  **Evaluation (`EvaluationProfile`)**:
    *   **Evaluation-Ready Metadata**: Defines test contracts directly in the manifest.
    *   `expected_latency_ms`: SLA for response time.
    *   `golden_dataset_uri`: Reference to a test dataset.
    *   `grading_rubric`: List of `SuccessCriterion` for quality checks.
    *   `evaluator_model`: Model to use for evaluation.

9.  **Observability (`ObservabilityConfig`)**:
    *   `trace_level`: Controls the granularity of logs (`FULL`, `METADATA_ONLY`, `NONE`).
    *   `retention_policy`: How long logs are kept.
    *   `encryption_key_id`: Optional ID of the key used for log encryption.

10.  **Presentation (`PresentationEvent`)**:
    *   Standardized schemas for emitting UI-ready events (`THOUGHT_TRACE`, `CITATION_BLOCK`, `PROGRESS_INDICATOR`, etc.).

11. **Custom Metadata (`custom_metadata`)**:
    *   Container for arbitrary metadata extensions without breaking validation.

12. **Integrity**:
    *   `integrity_hash`: SHA256 hash of the source code (top-level field). Required only when `status` is `published`.

## Agent Lifecycle: Draft vs. Published

The definition supports a "Draft Mode" to facilitate prototyping and visual editing.

*   **Draft Mode (`status="draft"`)**:
    *   **Relaxed Validation**: Topology integrity checks (e.g., ensuring all edges point to valid nodes) are skipped.
    *   **Optional Hash**: The `integrity_hash` field is optional.
    *   **Purpose**: Allows saving "work in progress" states.

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
    *   **Topology Validation**: The specification validates that all edges connect to existing nodes.

## Example Usage

Here is how to programmatically define an Agent Runtime Object:

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
