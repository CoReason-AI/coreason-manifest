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
*   **Compliance Enforcement:** Uses Open Policy Agent (OPA) / Rego to enforce complex business rules and allowlists.
*   **Integrity Verification:** Calculates and verifies SHA256 hashes of the agent's source code to prevent tampering.
*   **Automatic Schema Generation:** Inspects Python functions to generate Agent Interfaces, automatically handling `UserContext` injection.
*   **Dependency Pinning:** Enforces strict version pinning for all library dependencies.
*   **Trusted Bill of Materials (TBOM):** Validates libraries against an approved list.
*   **Compliance Microservice:** Can be run as a standalone API server (Service C) for centralized validation.

## Installation

```bash
pip install coreason-manifest
```

## Usage

`coreason-manifest` supports two modes: **Library (CLI)** and **Server (Microservice)**.

### 1. Library Usage

Use the python library to validate local agent files and verify source integrity.

```python
from coreason_manifest import ManifestEngine, ManifestConfig

# Initialize and Validate
config = ManifestConfig(policy_path="./policies/compliance.rego")
engine = ManifestEngine(config)
agent_def = engine.load_and_validate("agent.yaml", "./src")
```

### 2. Server Mode

Run the package as a FastAPI server to provide a centralized compliance API.

```bash
uvicorn coreason_manifest.server:app --host 0.0.0.0 --port 8000
```

For full details, see the [Usage Documentation](docs/usage.md).

For detailed requirements and architecture, please refer to the [Product Requirements](docs/product_requirements.md) or [Requirements](docs/requirements.md).
