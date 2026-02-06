# Coreason Manifest

The definitive source of truth for CoReason-AI Asset definitions. "The Blueprint."

[![License: Prosperity 3.0](https://img.shields.io/badge/license-Prosperity%203.0-blue)](https://github.com/CoReason-AI/coreason-manifest)
[![Build Status](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason-manifest/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Documentation](https://img.shields.io/badge/docs-home-informational)](docs/index.md)

## Overview

`coreason-manifest` serves as the **Shared Kernel** for the Coreason ecosystem. It contains the canonical Pydantic definitions, schemas, and data structures for Agents and Workflows (Recipes).

It provides the **"Blueprint"** that all other services (Builder, Engine, Simulator) rely on. It focuses on strict typing, schema validation, and serialization, ensuring that if it isn't in the manifest, it doesn't exist.

### Standards Clarification
*Note: The "Coreason Agent Manifest" (CAM) is a proprietary, strict governance schema designed for the CoReason Platform. It is distinct from the Oracle/Linux Foundation "Open Agent Specification," though we aim for future interoperability via adapters.*

## Features

*   **Coreason Agent Manifest (CAM):** Strict Pydantic models for Agent definitions (`AgentDefinition`) and Recipes (`Recipe`).
*   **Strict Typing:** Enforces type safety for critical interfaces.
*   **Governance & Policy:** Enforce organizational rules (domains, risk levels) on agents via `GovernanceConfig`.
*   **Ergonomic Factory Methods:** Simplified construction of manifests.
*   **Flexible Tooling:** Support for external tool definitions (`ToolDefinition`) and risk levels (`ToolRiskLevel`).
*   **Topology Visualization:** Workflows are defined as graph topologies (`Workflow`).

## Serialization & Base Model

Core definitions (e.g., `Manifest`, `Workflow`, `AgentDefinition`) inherit from Pydantic's `BaseModel`. Shared configuration models like `GovernanceConfig` inherit from `CoReasonBaseModel` for enhanced serialization capabilities.

## Installation

```bash
pip install coreason-manifest
```

## Usage

This library is used to define and validate Agent configurations programmatically.

```python
from coreason_manifest import (
    Recipe,
    ManifestMetadata,
    AgentStep,
    Workflow,
    InterfaceDefinition,
    StateDefinition,
    PolicyDefinition
)

# 1. Define Metadata
metadata = ManifestMetadata(
    name="Research Agent",
    version="1.0.0"
)

# 2. Define Workflow
workflow = Workflow(
    start="step1",
    steps={
        "step1": AgentStep(
            id="step1",
            agent="gpt-4-researcher",
            next="step2"
        ),
        # ... define other steps
    }
)

# 3. Instantiate Manifest
manifest = Recipe(
    apiVersion="coreason.ai/v2",
    kind="Recipe",
    metadata=metadata,
    interface=InterfaceDefinition(
        inputs={"topic": {"type": "string"}},
        outputs={"summary": {"type": "string"}}
    ),
    state=StateDefinition(),
    policy=PolicyDefinition(max_retries=3),
    workflow=workflow
)

print(f"Manifest '{manifest.metadata.name}' created successfully.")
```

For full details, see the [Usage Documentation](docs/usage.md).

## Documentation

**[Full Documentation Index](docs/index.md)**

*   [Usage Guide](docs/usage.md): How to load and create manifests.
*   [Governance & Policy Enforcement](docs/governance_policy_enforcement.md): Validating agents against organizational rules.
*   [Coreason Agent Manifest (CAM)](docs/cap/specification.md): The Canonical YAML Authoring Format.
