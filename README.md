# Coreason Manifest

The definitive source of truth for CoReason-AI Asset definitions. "The Blueprint."

[![License: Prosperity 3.0](https://img.shields.io/badge/license-Prosperity%203.0-blue)](https://github.com/CoReason-AI/coreason-manifest)
[![Build Status](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason-manifest/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Documentation](https://img.shields.io/badge/docs-product_requirements-informational)](docs/product_requirements.md)

## Overview

`coreason-manifest` serves as the **Shared Kernel** for the Coreason ecosystem. It contains the canonical definitions, schemas, and data structures for Agents, Workflows (Recipes), and Auditing.

It provides the **"Blueprint"** that all other services (Builder, Engine, Simulator) rely on. It consists of:

1.  **Coreason Agent Manifest (CAM)**: A Human-Centric Canonical YAML format (V2) for authoring Agents and Recipes.
2.  **Runtime Definitions**: Strict Pydantic models (`AgentDefinition`, `RecipeManifest`) optimized for machine execution.

### Standards Clarification
*Note: The "Coreason Agent Manifest" (CAM) is a proprietary, strict governance schema designed for the CoReason Platform. It is distinct from the Oracle/Linux Foundation "Open Agent Specification," though we aim for future interoperability via adapters.*

*   CAM is for **configuration**.
*   CAP is for **communication**.

## Features

*   **Coreason Agent Manifest (CAM):** The primary V2 YAML authoring format for Agents and Recipes.
*   **Runtime Definitions:** Strict Pydantic models (`AgentDefinition`, `RecipeManifest`) for the execution engine.
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

This library is used to define and validate Agent configurations.

### 1. Loading from V2 YAML (Recommended)

```python
from coreason_manifest.v2.io import load_from_yaml
from coreason_manifest.v2.adapter import v2_to_recipe

# Load a human-friendly V2 manifest
v2_manifest = load_from_yaml("my_workflow.v2.yaml")

# Compile to Runtime Recipe
recipe = v2_to_recipe(v2_manifest)

print(f"Loaded Recipe: {recipe.name}")
```

### 2. Programmatic Definition (Runtime Objects)

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

# ... (See docs/usage.md for full example)
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

*   [Coreason Agent Manifest (CAM)](docs/coreason_agent_manifest.md): The V2 YAML Authoring Format.
*   [Runtime Agent Definition](docs/runtime_agent_definition.md): The Machine-Optimized Agent Definition.
*   [Builder SDK](docs/builder_sdk.md): Fluent Python API for defining Agents.
*   [Agent Behavior Protocols](docs/agent_behavior_protocols.md): The standard interfaces for agent implementation.
*   [Transport-Layer Specification](docs/transport_layer_specification.md): The HTTP/SSE contract for serving agents.
*   [Frontend Integration](docs/frontend_integration.md): Communicating with the Coreason Engine.
*   [Simulation Architecture](docs/simulation_architecture.md): Details on ATIF compatibility and GAIA scenarios.
*   [Audit & Compliance](docs/audit_compliance.md): Details on EU AI Act compliance, Chain of Custody, and Integrity Hashing.
*   [Governance & Policy Enforcement](docs/governance_policy_enforcement.md): Validating agents against organizational rules.
