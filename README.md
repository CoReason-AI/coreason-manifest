# Coreason Manifest

The definitive source of truth for CoReason-AI Asset definitions. "The Blueprint."

[![License: Prosperity 3.0](https://img.shields.io/badge/license-Prosperity%203.0-blue)](https://github.com/CoReason-AI/coreason-manifest)
[![Build Status](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason-manifest/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Documentation](https://img.shields.io/badge/docs-product_requirements-informational)](docs/product_requirements.md)

## Overview

`coreason-manifest` acts as the validator for the "Agent Development Lifecycle" (ADLC). It ensures that every Agent produced meets strict GxP and security standards. If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run.

## Features

*   **Open Agent Specification (OAS) Validation:** Parses and validates agent definitions against a strict schema.
*   **Shared Kernel (Definitions):** Provides the definitive Pydantic models (`AgentManifest`, `ToolCall`, `TopologyGraph`, etc.) used across the entire CoReason platform.

## Installation

```bash
pip install coreason-manifest
```

## Usage

The package provides strict Pydantic models for Agents, Recipes, and Simulations.

```python
from coreason_manifest.definitions import AgentManifest
from coreason_manifest.recipes import RecipeManifest

# Example: Validating a manifest
# agent = AgentManifest.model_validate(data)
```

For full details, see the [Usage Documentation](docs/usage.md).

For detailed requirements and architecture, please refer to the [Product Requirements](docs/product_requirements.md) or [Requirements](docs/requirements.md).
