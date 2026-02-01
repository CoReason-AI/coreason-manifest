# Coreason Manifest

The definitive source of truth for CoReason-AI Asset definitions. "The Blueprint."

[![License: Prosperity 3.0](https://img.shields.io/badge/license-Prosperity%203.0-blue)](https://github.com/CoReason-AI/coreason-manifest)
[![Build Status](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason-manifest/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Documentation](https://img.shields.io/badge/docs-product_requirements-informational)](docs/product_requirements.md)

## Overview

`coreason-manifest` serves as the **Shared Kernel** for the Coreason ecosystem. It contains the canonical Pydantic definitions, schemas, and data structures for Agents, Workflows (Recipes), and Auditing.

It provides the **"Blueprint"** that all other services (Builder, Engine, Simulator) rely on. It focuses on strict typing, schema validation, and serialization, ensuring that if it isn't in the manifest, it doesn't exist.

## Features

*   **Open Agent Specification (OAS):** Strict Pydantic models for Agent definitions (`AgentDefinition`).
*   **Strict Typing:** Enforces type safety and immutable structures for critical interfaces.
*   **Enhanced Serialization:** Includes `CoReasonBaseModel` to ensure consistent JSON serialization of complex types like `UUID` and `datetime`.
*   **Event Protocol:** Defines the `GraphEvent` and `CloudEvent` structures for real-time communication.
*   **Simulation Schemas:** Provides standard models for `SimulationScenario`, `AdversaryProfile`, and `SimulationTrace`.
*   **Audit & Compliance:** Defines the `AuditLog` structure for tamper-evident record keeping.
*   **Ergonomic Factory Methods:** Simplified construction of `ChatMessage` and `GenAIOperation`.
*   **Token Arithmetic:** Support for `+` and `+=` operators on `GenAITokenUsage`.
*   **Flexible Tooling:** `ToolCallRequestPart` accepts JSON strings with automatic parsing.
*   **Enhanced Tracing:** `ReasoningTrace` includes flexible metadata for execution state.

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

# 2. Instantiate Agent
agent = AgentDefinition(
    metadata=metadata,
    interface={
        "inputs": {"topic": {"type": "string"}},
        "outputs": {"summary": {"type": "string"}}
    },
    config={
        "nodes": [],
        "edges": [],
        "entry_point": None,
        "model_config": {"model": "gpt-4", "temperature": 0.0},
        "system_prompt": "You are a helpful assistant."
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
        "budget_caps": {"total_cost": 5.0}
    },
    observability={
        "trace_level": TraceLevel.FULL,
        "retention_policy": "90_days"
    },
    # Mandatory Integrity Hash
    integrity_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)

print(f"Agent '{agent.metadata.name}' definition created and validated.")
```

For full details, see the [Usage Documentation](docs/usage.md).

## Documentation

*   [Frontend Integration](docs/frontend_integration.md): Communicating with the Coreason Engine.
*   [Simulation Architecture](docs/simulation_architecture.md): Details on ATIF compatibility and GAIA scenarios.
*   [Audit & Compliance](docs/audit_compliance.md): Details on EU AI Act compliance, Chain of Custody, and Integrity Hashing.
