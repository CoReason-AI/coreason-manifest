# Coreason Manifest

The definitive source of truth for CoReason-AI Asset definitions. "The Blueprint."

[![License: Prosperity 3.0](https://img.shields.io/badge/license-Prosperity%203.0-blue)](https://github.com/CoReason-AI/coreason-manifest)
[![Build Status](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason-manifest/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Documentation](https://img.shields.io/badge/docs-product_requirements-informational)](docs/product_requirements.md)

## Overview

`coreason-manifest` serves as the **Shared Kernel** for the Coreason ecosystem. It contains the canonical Pydantic definitions, schemas, and data structures for Agents, Workflows (Recipes), and Auditing.

It provides the **"Blueprint"** that all other services (Builder, Engine, Simulator) rely on. It focuses on strict typing, schema validation, and serialization, ensuring that if it isn't in the manifest, it doesn't exist.

### Standards Clarification
*Note: The "Coreason Agent Manifest" (CAM) is a proprietary, strict governance schema designed for the CoReason Platform. It is distinct from the Oracle/Linux Foundation "Open Agent Specification," though we aim for future interoperability via adapters.*

*   CAM is for **configuration**.
*   CAP is for **communication**.

## Features

*   **Coreason Agent Manifest (CAM):** Strict Pydantic models for Agent definitions (`AgentDefinition`).
*   **Coreason Agent Protocol (CAP):** Standardized HTTP/SSE runtime contract for invoking agents and streaming results, strictly typed via `ServiceRequest` and `StreamPacket`.
*   **Behavioral Protocols:** Standard `AgentInterface` and `LifecycleInterface` protocols for runtime interoperability.
*   **Strict Typing:** Enforces type safety and immutable structures for critical interfaces.
*   **Enhanced Serialization:** Includes `CoReasonBaseModel` to ensure consistent JSON serialization of complex types like `UUID` and `datetime`.
*   **Event Protocol:** Defines the `GraphEvent` and `CloudEvent` structures for real-time communication.
*   **Simulation Schemas:** Provides standard models for `SimulationScenario`, `AdversaryProfile`, and `SimulationTrace`.
*   **Audit & Compliance:** Defines the `AuditLog` structure for tamper-evident record keeping.
*   **Governance & Policy:** Enforce organizational rules (domains, risk levels) on agents via `GovernanceConfig`.
*   **Ergonomic Factory Methods:** Simplified construction of `ChatMessage` and `GenAIOperation`.
*   **Token Arithmetic:** Support for `+` and `+=` operators on `GenAITokenUsage`.
*   **Flexible Tooling:** `ToolCallRequestPart` accepts JSON strings with automatic parsing.
*   **Enhanced Tracing:** `ReasoningTrace` includes flexible metadata for execution state.
*   **Builder SDK:** A fluent, strictly-typed Python SDK for defining Agents using Pydantic models.
*   **Topology Visualization:** Export agent execution flows to Mermaid.js graph syntax (`.to_mermaid()`).

## Serialization & Base Model

All core definitions (`AgentDefinition`, `RecipeManifest`, `GraphTopology`, `AuditLog`) inherit from `CoReasonBaseModel`. This provides a consistent interface for serialization, solving common Pydantic v2 issues with `UUID` and `datetime`.

*   Use `.dump()` to get a JSON-compatible dictionary (where UUIDs/datetimes are strings).
*   Use `.to_json()` to get a JSON string.

For a detailed rationale, see [docs/coreason_base_model_rationale.md](docs/coreason_base_model_rationale.md).

## Installation

```bash
pip install coreason-manifest
```

## Usage

This library is used to define and validate Agent configurations programmatically.

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
    PolicyConfig,
    ObservabilityConfig,
    TraceLevel
)

# 1. Define Metadata
metadata = AgentMetadata(
    id=uuid.uuid4(),
    version="1.0.0",  # Strict SemVer
    name="Research Agent",
    author="Coreason AI",
    created_at=datetime.now(timezone.utc)
)

# 2. Instantiate Agent
agent = AgentDefinition(
    metadata=metadata,
    capabilities=[
        AgentCapability(
            name="research",
            type=CapabilityType.ATOMIC,
            description="Deep research on a topic.",
            inputs={"topic": {"type": "string"}},
            outputs={"summary": {"type": "string"}}
        )
    ],
    config=AgentRuntimeConfig(
        model_config=ModelConfig(
            model="gpt-4",
            temperature=0.0,
            system_prompt="You are a helpful assistant."
        )
    ),
    dependencies=AgentDependencies(
        tools=[
            ToolRequirement(
                uri="mcp://search-service/google",
                hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # Valid SHA256
                scopes=["search:read"],
                risk_level=ToolRiskLevel.STANDARD
            )
        ],
        libraries=("pandas==2.0.0",)
    ),
    policy=PolicyConfig(
        budget_caps={"total_cost": 5.0}
    ),
    observability=ObservabilityConfig(
        trace_level=TraceLevel.FULL,
        retention_policy="90_days"
    ),
    # Mandatory Integrity Hash
    integrity_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)

print(f"Agent '{agent.metadata.name}' definition created and validated.")
```

For full details, see the [Usage Documentation](docs/usage.md).

## Builder SDK

The **Builder SDK** offers a developer-friendly way to define agents using standard Python classes instead of raw schemas.

```python
from coreason_manifest.builder import AgentBuilder, TypedCapability
from pydantic import BaseModel

class MyInput(BaseModel):
    query: str

class MyOutput(BaseModel):
    answer: str

cap = TypedCapability("search", "Search tool", MyInput, MyOutput)

agent = AgentBuilder("MyAgent").with_capability(cap).build()
```

The Builder also supports **Graph Topologies** (`with_node`, `with_edge`) and **External Tools** (`with_tool_requirement`).

See [docs/builder_sdk.md](docs/builder_sdk.md) for details.

## Documentation

*   [Builder SDK](docs/builder_sdk.md): Fluent Python API for defining Agents.
*   [Agent Behavior Protocols](docs/agent_behavior_protocols.md): The standard interfaces for agent implementation.
*   [Transport-Layer Specification](docs/transport_layer_specification.md): The HTTP/SSE contract for serving agents.
*   [Frontend Integration](docs/frontend_integration.md): Communicating with the Coreason Engine.
*   [Simulation Architecture](docs/simulation_architecture.md): Details on ATIF compatibility and GAIA scenarios.
*   [Audit & Compliance](docs/audit_compliance.md): Details on EU AI Act compliance, Chain of Custody, and Integrity Hashing.
*   [Governance & Policy Enforcement](docs/governance_policy_enforcement.md): Validating agents against organizational rules.

## Roadmap

*   **RFC 001: Canonical YAML (v2)**: We have implemented the "Human-Centric" YAML format for manifests. See [docs/rfcs/001-v2-canonical-yaml.md](docs/rfcs/001-v2-canonical-yaml.md) for the specification and [docs/v2_bridge.md](docs/v2_bridge.md) for usage of the Loader Bridge.
